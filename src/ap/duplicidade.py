"""
Contas a pagar: detecção de risco de pagamento em duplicidade.

Este módulo é a razão pela qual eu não comecei pela conciliação de recebíveis
que o cliente pediu.

O que está no arquivo 04, reconstruído em ordem:

  06/07  São Jorge envia NF 88231, R$ 18.900,00, venc 20/07, ref. PC 4471.
  06/07  WhatsApp: Bia pergunta "entrou o material completo?".
         Rafael responde "acho que sim, o Joao confirmou". Aprovado.
  18/07  São Jorge diz que não identificou o pagamento e REEMITE o boleto:
         R$ 19.278,00, venc 25/07, linha digitável nova.
         No mesmo e-mail, revela: "PC 4471 foi entregue parcialmente
         (12 de 15 volumes)".
  19/07  WhatsApp: Camila pergunta se já pagaram. Olha o sistema, vê o
         pagamento AGENDADO para o dia 20 e lê como já pago:
         "achei, pagou dia 20. era outra nota entao?"
         Bia: "nao sei, alguem confere?" — ninguém responde.
  20/07  Extrato: PAGAMENTO FORNECEDOR NF 88231, R$ 18.900,00 (débito).

Resultado: há evidência de liquidação da NF 88231 e uma cobrança posterior,
com outra grafia e outro valor, ainda pagável. O pagamento deve ser bloqueado
até que fornecedor e documentos de origem confirmem se é reemissão do mesmo
título ou uma obrigação legítima diferente.

E ainda: houve pagamento integral apesar de o e-mail declarar entrega parcial.
Sem pedido, recebimento e preço por item, isso prova uma falha de controle de
three-way match — não permite calcular perda proporcional.

Por que REGRA não resolve isso sozinho: o fornecedor reemitiu com outro
número ('088231' contra 'NF 88231'), outro valor e outro vencimento. A
normalização de documento pega a grafia; mas "entregue parcialmente (12 de 15
volumes)" está num 'Obs:' no fim de um e-mail de cobrança, e isso não tem
campo. São ~340 e-mails/mês. É aqui que a IA ganha de regra, e é por isso que
esta frente é mais defensável diante do CTO: não toca no Protheus.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from ..canonico import (
    Alerta,
    CobrancaRecebida,
    Evidencia,
    MensagemAprovacao,
    MovimentoBancario,
    Severidade,
)
from ..normalizacao import (
    fmt_brl,
    fmt_data,
    limpar_texto,
    normalizar_documento,
    parse_valor,
)

_RE_DOC_HIST = re.compile(
    r"\b(?:NFS?-?e?|NOTA\s+FISCAL|NOTA|FATURA|FAT|DOC)\b[\s:nº°.]*(\d{3,})",
    re.IGNORECASE,
)
_RE_PROPORCAO = re.compile(r"(\d{1,4})\s*(?:de|/)\s*(\d{1,4})\s*(volumes?|pe[cç]as?|unidades?|itens?)?",
                           re.IGNORECASE)
_RE_DOC_SOLTO = re.compile(r"\b(\d{5,8})\b")

PALAVRAS_CONFIRMACAO_FRACA = (
    "acho que", "acredito que", "parece que", "deve ter", "imagino",
    "se nao me engano", "não me engano", "provavelmente", "creio",
)
PALAVRAS_DUVIDA_ABERTA = (
    "alguem confere", "alguém confere", "nao sei", "não sei",
    "era outra nota", "ja pagamos", "já pagamos", "confirma",
)


@dataclass
class PagamentoIdentificado:
    movimento: MovimentoBancario
    documento_normalizado: str

    @property
    def quando(self) -> date:
        return self.movimento.data


@dataclass
class ResultadoAP:
    alertas: list[Alerta] = field(default_factory=list)
    pagamentos: list[PagamentoIdentificado] = field(default_factory=list)
    cobrancas_por_documento: dict[str, list[CobrancaRecebida]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
def identificar_pagamentos(movimentos: list[MovimentoBancario]) -> list[PagamentoIdentificado]:
    """
    Extrai, dos débitos do extrato, quais documentos fiscais foram pagos.

    'PAGAMENTO FORNECEDOR NF 88231' -> documento 88231.

    Limitação declarada: o histórico de débito não traz o nome do fornecedor,
    só o número da nota. Com 4 contas bancárias e vários fornecedores, dois
    documentos de mesmo número em fornecedores diferentes colidiriam. Em
    produção eu cruzaria com o arquivo de remessa de pagamento (CNAB 240),
    que carrega o favorecido. Aqui, caso a caso, confiro número + valor.
    """
    achados: list[PagamentoIdentificado] = []
    for mov in movimentos:
        if mov.is_credito:
            continue
        hist = mov.historico or ""
        m = _RE_DOC_HIST.search(hist)
        doc = m.group(1) if m else None
        if not doc:
            # tarifas e impostos não têm documento: ignora em silêncio
            if any(p in limpar_texto(hist) for p in ("TARIFA", "IOF", "IMPOSTO", "JUROS")):
                continue
            m2 = _RE_DOC_SOLTO.search(hist)
            doc = m2.group(1) if m2 else None
        if not doc:
            continue
        achados.append(
            PagamentoIdentificado(movimento=mov, documento_normalizado=normalizar_documento(doc))
        )
    return achados


# ---------------------------------------------------------------------------
def analisar_contas_a_pagar(
    cobrancas: list[CobrancaRecebida],
    movimentos: list[MovimentoBancario],
    aprovacoes: list[MensagemAprovacao],
    cfg: dict,
) -> ResultadoAP:
    res = ResultadoAP()
    res.pagamentos = identificar_pagamentos(movimentos)
    ap_cfg = cfg["contas_a_pagar"]
    tol = Decimal(str(ap_cfg["tolerancia_debito_relativa"]))
    acrescimo_max = Decimal(str(ap_cfg["acrescimo_maximo_reemissao"]))
    janela_reemissao = timedelta(days=int(ap_cfg.get("janela_reemissao_dias", 45)))

    # Agrupa por (fornecedor, documento). Chave do fornecedor = DOMÍNIO do
    # e-mail, não o nome: os dois e-mails da São Jorge vêm de remetentes
    # diferentes (financeiro@ e marcia.rocha@) do mesmo domínio.
    grupos: dict[tuple[str, str], list[CobrancaRecebida]] = {}
    for c in cobrancas:
        if not c.documento_normalizado:
            continue
        grupos.setdefault((c.dominio, c.documento_normalizado), []).append(c)
    res.cobrancas_por_documento = {f"{d}/{doc}": v for (d, doc), v in grupos.items()}

    for (dominio, doc), grupo in grupos.items():
        grupo = sorted(grupo, key=lambda c: c.recebido_em or date.min)
        datas_conhecidas = [c for c in grupo if c.recebido_em is not None]
        if len(datas_conhecidas) >= 2:
            primeira = datas_conhecidas[0].recebido_em
            grupo = [
                c for c in grupo
                if c.recebido_em is None or (c.recebido_em - primeira) <= janela_reemissao
            ]
        pagos = [
            p for p in res.pagamentos
            if p.documento_normalizado == doc
        ]

        # ---- AP-001: reemissão de cobrança de documento já pago
        if len(grupo) > 1 and pagos:
            res.alertas.extend(
                _alertas_reemissao(grupo, pagos, dominio, doc, tol, acrescimo_max)
            )
        elif len(grupo) > 1:
            res.alertas.append(_alerta_reemissao_sem_pagamento(grupo, dominio, doc))

        # ---- AP-002: gap de three-way match
        res.alertas.extend(_alertas_three_way(grupo, pagos))

    # ---- AP-003/004: qualidade da trilha de aprovação
    res.alertas.extend(_alertas_trilha(aprovacoes, res.pagamentos, cobrancas))

    # ---- AP-005: cobrança sem documento identificável
    for c in cobrancas:
        if c.documento_normalizado:
            continue
        res.alertas.append(
            Alerta(
                codigo="AP-005",
                severidade=Severidade.MEDIO,
                titulo_curto="Cobrança sem documento identificável",
                descricao=(
                    f"{c.fornecedor} ({c.dominio}) cobra {fmt_brl(c.valor_efetivo or 0)} "
                    f"sem número de documento no corpo do e-mail. "
                    + " ".join(c.notas_extracao)
                    + " Sem identificador, não é possível checar se já foi pago — é "
                    "exatamente a condição que permite pagamento em duplicidade."
                ),
                valor_em_risco=c.valor_efetivo or Decimal("0"),
                destinatario="Contas a pagar",
                grupo_risco=f"sem_controle:{c.id}",
                # Não é perda comprovada: é pagamento que NÃO é possível
                # verificar contra duplicidade com os dados disponíveis.
                tipo_risco="sem_controle",
                evidencias=[
                    Evidencia(
                        regra="ap/cobranca_sem_documento",
                        detalhe=f"Assunto: {c.assunto!r}; anexos: {c.anexos}",
                        campos={"notas": c.notas_extracao},
                    )
                ],
                referencias=[c.id, c.assunto],
            )
        )

    ordem = {Severidade.CRITICO: 0, Severidade.ALTO: 1, Severidade.MEDIO: 2, Severidade.INFO: 3}
    res.alertas.sort(key=lambda a: (ordem[a.severidade], -float(a.valor_em_risco)))
    return res


# ---------------------------------------------------------------------------
def _alertas_reemissao(
    grupo: list[CobrancaRecebida],
    pagos: list[PagamentoIdentificado],
    dominio: str,
    doc: str,
    tol: Decimal,
    acrescimo_max: Decimal,
) -> list[Alerta]:
    """
    O caso São Jorge. Documento já pago + cobrança viva na caixa de entrada.

    A trava para não gritar falso positivo: a cobrança posterior só é tratada
    como reemissão do MESMO documento se o acréscimo sobre o valor pago for
    compatível com atualização de boleto (multa + juros, até o teto de
    config). Acréscimo muito acima disso provavelmente é outra nota com número
    parecido, e aí o alerta sai como severidade menor.
    """
    alertas: list[Alerta] = []
    primeiro = grupo[0]
    base = primeiro.valor_efetivo or Decimal("0")

    for pago in pagos:
        valor_pago = pago.movimento.valor
        for cobranca in grupo:
            valor_cob = cobranca.valor_efetivo
            if valor_cob is None:
                continue
            # É a própria cobrança que foi paga? então não é risco.
            if base and abs(valor_cob - valor_pago) / max(valor_pago, Decimal("1")) <= tol:
                continue

            acrescimo = (valor_cob - valor_pago) / valor_pago if valor_pago else Decimal("0")
            if acrescimo <= 0:
                continue

            plausivel = acrescimo <= acrescimo_max
            severidade = Severidade.CRITICO if plausivel else Severidade.ALTO
            tipo = (
                "reemissão do mesmo documento com atualização de multa/juros"
                if plausivel else
                "cobrança de valor muito acima do pago — confirmar se é o mesmo documento"
            )

            evid = [
                Evidencia(
                    regra="ap/documento_normalizado",
                    detalhe=(
                        f"'{primeiro.documento}' e '{cobranca.documento}' normalizam "
                        f"para o mesmo documento ({doc}). Para o sistema são dois; "
                        f"para o fornecedor é um."
                    ),
                    campos={
                        "grafias": [c.documento for c in grupo],
                        "normalizado": doc,
                    },
                ),
                Evidencia(
                    regra="ap/pagamento_localizado_no_extrato",
                    detalhe=(
                        f"Débito de {fmt_brl(valor_pago)} em "
                        f"{fmt_data(pago.quando)}: '{pago.movimento.historico}'"
                    ),
                    campos={"movimento": pago.movimento.id},
                ),
                Evidencia(
                    regra="ap/acrescimo_compativel_com_atualizacao",
                    detalhe=(
                        f"Cobrança de {fmt_brl(valor_cob)} é {acrescimo:.2%} acima do "
                        f"valor pago — {tipo}"
                    ),
                    campos={"acrescimo_relativo": str(acrescimo.quantize(Decimal('0.0001')))},
                ),
            ]
            if cobranca.linha_digitavel:
                evid.append(
                    Evidencia(
                        regra="ap/boleto_vivo",
                        detalhe=(
                            "A cobrança traz linha digitável própria e vencimento "
                            f"{fmt_data(cobranca.vencimento)} — é pagável agora, por "
                            "qualquer pessoa da equipe, sem nenhum travamento."
                        ),
                        campos={"linha_digitavel": cobranca.linha_digitavel},
                    )
                )

            alertas.append(
                Alerta(
                    codigo="AP-001",
                    severidade=severidade,
                    titulo_curto="RISCO DE PAGAMENTO EM DUPLICIDADE",
                    descricao=(
                        f"Há um débito de {fmt_brl(valor_pago)} em {fmt_data(pago.quando)} "
                        f"referenciado ao documento {primeiro.documento} de {dominio}, mas existe "
                        f"cobrança em aberto na caixa de entrada de {fmt_brl(valor_cob)} "
                        f"com vencimento {fmt_data(cobranca.vencimento)}. "
                        f"O e-mail de {fmt_data(cobranca.recebido_em)} indica uma possível "
                        f"reemissão por pagamento não identificado. BLOQUEAR PAGAMENTO E "
                        f"VALIDAR. Ação: confirmar a liquidação, o documento de origem e a "
                        f"natureza da nova cobrança com o fornecedor antes de pagar ou baixar."
                    ),
                    valor_em_risco=valor_cob,
                    destinatario="Contas a pagar + Controladoria",
                    # Mesmo dinheiro do AP-004: a exposição é o boleto vivo.
                    grupo_risco=f"duplicidade:{dominio}:{doc}",
                    tipo_risco="potencial",
                    evidencias=evid,
                    referencias=[
                        f"{c.id} — {c.assunto} ({fmt_brl(c.valor_efetivo or 0)}, "
                        f"recebido {fmt_data(c.recebido_em)})"
                        for c in grupo
                    ],
                )
            )
    return alertas


def _alerta_reemissao_sem_pagamento(
    grupo: list[CobrancaRecebida], dominio: str, doc: str
) -> Alerta:
    valores = [c.valor_efetivo for c in grupo if c.valor_efetivo is not None]
    maior = max(valores) if valores else Decimal("0")
    return Alerta(
        codigo="AP-006",
        severidade=Severidade.ALTO,
        titulo_curto="Documento cobrado mais de uma vez, sem pagamento localizado",
        descricao=(
            f"O documento {doc} de {dominio} aparece em {len(grupo)} cobranças com "
            f"valores {', '.join(fmt_brl(v) for v in valores)}. Nenhum pagamento "
            f"correspondente foi encontrado no extrato. Pagar sem consolidar qual é a "
            f"cobrança válida arrisca pagar duas vezes. Consolidar antes de liberar."
        ),
        valor_em_risco=maior,
        destinatario="Contas a pagar",
        grupo_risco=f"duplicidade:{dominio}:{doc}",
        tipo_risco="potencial",
        evidencias=[
            Evidencia(
                regra="ap/documento_normalizado",
                detalhe=f"Grafias: {[c.documento for c in grupo]} -> {doc}",
                campos={},
            )
        ],
        referencias=[c.id for c in grupo],
    )


# ---------------------------------------------------------------------------
def _alertas_three_way(
    grupo: list[CobrancaRecebida], pagos: list[PagamentoIdentificado]
) -> list[Alerta]:
    """
    Gap de three-way match: pagou-se o cheio de uma entrega parcial.

    O controle existia e a pessoa certa fez a pergunta certa ('entrou o
    material completo?'). Falhou na resposta ('acho que sim'). Não é falta de
    processo, é falta de evidência amarrada à aprovação — e é por isso que a
    solução não automatiza a aprovação, e sim exige o documento de recebimento.
    """
    alertas: list[Alerta] = []
    for c in grupo:
        if not c.entrega_parcial:
            continue
        m = _RE_PROPORCAO.search(c.entrega_parcial)
        valor_ref = c.valor_original or c.valor_efetivo or Decimal("0")
        pago = pagos[0].movimento.valor if pagos else None
        base = pago if pago is not None else valor_ref

        if m:
            entregue, total = Decimal(m.group(1)), Decimal(m.group(2))
            unidade = m.group(3) or "itens"
            detalhe_valor = (
                f"Entrega declarada: {entregue} de {total} {unidade}. O data pack não "
                "informa o valor de cada volume nem a condição comercial; portanto não "
                "é possível calcular perda ou valor devido por proporção."
            )
        else:
            detalhe_valor = "Entrega incompleta declarada, sem proporção numérica no texto."

        alertas.append(
            Alerta(
                codigo="AP-002",
                severidade=Severidade.ALTO,
                titulo_curto="Gap de three-way match: pagamento integral de entrega parcial",
                descricao=(
                    f"O próprio fornecedor declarou entrega incompleta do "
                    f"{('PC ' + c.pedido_compra) if c.pedido_compra else 'pedido'}: "
                    f"\"{c.entrega_parcial}\". "
                    + (f"O pagamento de {fmt_brl(base)} saiu integral. " if pagos else
                       f"A cobrança é de {fmt_brl(base)}, valor integral. ")
                    + detalhe_valor
                    + " Ação: bloquear nova liberação até conferir pedido, nota, "
                    "recebimento físico e condição comercial."
                ),
                valor_em_risco=Decimal("0"),
                destinatario="Compras + Contas a pagar",
                grupo_risco=f"three_way:{c.dominio}:{c.pedido_compra or c.documento_normalizado}",
                tipo_risco="indeterminado",
                evidencias=[
                    Evidencia(
                        regra="ap/entrega_parcial_declarada",
                        detalhe=(
                            f"Trecho extraído do e-mail de {fmt_data(c.recebido_em)} "
                            f"({'IA' if c.extraido_por == 'ia' else 'palavra-chave'}): "
                            f"{c.entrega_parcial!r}"
                        ),
                        campos={"pedido_compra": c.pedido_compra},
                    ),
                    Evidencia(
                        regra="ap/aritmetica_do_devido",
                        detalhe=detalhe_valor,
                        campos={"valor_monetario": "indeterminado"},
                    ),
                ],
                referencias=[c.id, c.assunto],
            )
        )
    return alertas


# ---------------------------------------------------------------------------
def _alertas_trilha(
    aprovacoes: list[MensagemAprovacao],
    pagamentos: list[PagamentoIdentificado],
    cobrancas: list[CobrancaRecebida],
) -> list[Alerta]:
    """
    Qualidade da trilha de aprovação.

    Dois achados distintos na thread do WhatsApp:

    AP-003 — aprovação sustentada em confirmação vaga. 'entrou o material
    completo?' respondida com 'acho que sim, o Joao confirmou', e aprovada em
    seguida. Sem documento de recebimento, a aprovação não tem lastro.

    AP-004 — verificação de pagamento feita contra data futura. Em 19/07 a
    Camila escreve 'achei, pagou dia 20'. O débito só ocorre em 20/07: ela leu
    um pagamento AGENDADO como liquidado e concluiu que a cobrança era de outra
    nota. A dúvida seguinte ('alguem confere?') não foi respondida por ninguém.
    Essa é uma condição concreta de risco de duplicidade, detectável comparando
    a data da mensagem com a data do débito.
    """
    alertas: list[Alerta] = []
    if not aprovacoes:
        return alertas

    docs_citados = {
        normalizar_documento(m.group(1))
        for msg in aprovacoes
        for m in [_RE_DOC_HIST.search(msg.texto) or _RE_DOC_SOLTO.search(msg.texto)]
        if m
    }

    # --- AP-003: aprovação com confirmação vaga
    for i, msg in enumerate(aprovacoes):
        baixo = limpar_texto(msg.texto)
        if not any(limpar_texto(p) in baixo for p in PALAVRAS_CONFIRMACAO_FRACA):
            continue
        aprovacao_seguinte = next(
            (m for m in aprovacoes[i + 1: i + 4] if "aprovad" in limpar_texto(m.texto).lower()
             or "APROVAD" in limpar_texto(m.texto)),
            None,
        )
        if not aprovacao_seguinte:
            continue
        alertas.append(
            Alerta(
                codigo="AP-003",
                severidade=Severidade.ALTO,
                titulo_curto="Aprovação de pagamento sem evidência de recebimento",
                descricao=(
                    f"A controladoria pediu a confirmação de recebimento e recebeu uma "
                    f"resposta vaga: \"{msg.texto}\" ({msg.area}/{msg.autor}, "
                    f"{msg.quando}). A aprovação saiu em seguida "
                    f"(\"{aprovacao_seguinte.texto}\", {aprovacao_seguinte.quando}) sem "
                    f"nenhum documento de recebimento anexado. "
                    f"O controle existe e a pergunta certa foi feita — o que falta é "
                    f"amarrar a aprovação à evidência. Ação: exigir nota de entrada ou "
                    f"conferência de recebimento como anexo obrigatório da aprovação."
                ),
                valor_em_risco=Decimal("0"),
                destinatario="Controladoria",
                grupo_risco="trilha_aprovacao",
                tipo_risco="indeterminado",
                evidencias=[
                    Evidencia(
                        regra="ap/confirmacao_vaga_antes_de_aprovar",
                        detalhe=(
                            f"Sequência: pergunta de conferência -> resposta com hedge "
                            f"-> aprovação, em {msg.quando}-{aprovacao_seguinte.quando}, "
                            f"sem anexo de recebimento"
                        ),
                        campos={
                            "documentos_na_thread": sorted(d for d in docs_citados if d),
                            "canal": "WhatsApp (sem trilha auditável)",
                        },
                    )
                ],
                referencias=[f"[{m.quando}] {m.area} - {m.autor}: {m.texto}"
                             for m in aprovacoes],
            )
        )
        break

    # --- AP-004: verificação contra pagamento futuro
    for msg in aprovacoes:
        m_dia = re.search(r"pagou\s+dia\s+(\d{1,2})", msg.texto, re.IGNORECASE)
        if not m_dia:
            continue
        dia_citado = int(m_dia.group(1))
        partes_quando = msg.quando.split("/")
        if len(partes_quando) < 2:
            continue
        dia_msg = int(partes_quando[0])
        mes_msg = int(re.match(r"\d+", partes_quando[1]).group())
        ano_ref = pagamentos[0].quando.year if pagamentos else date.today().year
        try:
            data_msg = date(ano_ref, mes_msg, dia_msg)
        except ValueError:
            continue
        data_citada = None
        for delta in (0, 1):
            m = mes_msg + delta
            a = ano_ref + (1 if m > 12 else 0)
            if m > 12:
                m -= 12
            try:
                d = date(a, m, dia_citado)
                if d > data_msg:
                    data_citada = d
                    break
            except ValueError:
                pass
        if data_citada is None:
            continue

        debito = next((p for p in pagamentos if p.quando == data_citada), None)
        detalhe_debito = (
            f"O débito de fato ocorre em {fmt_data(debito.quando)} "
            f"({fmt_brl(debito.movimento.valor)}, '{debito.movimento.historico}')."
            if debito else
            "Nenhum débito correspondente encontrado até a data da mensagem."
        )
        pendente = next(
            (m for m in aprovacoes if any(limpar_texto(p) in limpar_texto(m.texto)
                                          for p in ("alguem confere", "alguém confere", "nao sei"))),
            None,
        )
        cobranca_viva = next(
            (c for c in cobrancas if c.e_reemissao and c.valor_efetivo), None
        )
        risco = cobranca_viva.valor_efetivo if cobranca_viva else Decimal("0")

        alertas.append(
            Alerta(
                codigo="AP-004",
                severidade=Severidade.CRITICO,
                titulo_curto="Conferência de pagamento baseada em agendamento, não em liquidação",
                descricao=(
                    f"Em {msg.quando}, {msg.autor} ({msg.area}) verifica a cobrança e "
                    f"conclui \"{msg.texto}\" — citando o dia {dia_citado}, que ainda não "
                    f"havia chegado. {detalhe_debito} "
                    f"Ou seja: um pagamento AGENDADO foi lido como liquidado, e a "
                    f"conclusão tirada foi que a cobrança do fornecedor era de outra "
                    f"nota. "
                    + (f"A dúvida levantada em seguida (\"{pendente.texto}\", "
                       f"{pendente.quando}) não foi respondida por ninguém na thread. "
                       if pendente else "")
                    + "Esta é uma condição concreta de risco de pagamento em duplicidade. "
                    "Ação: a conferência precisa ser contra extrato liquidado, nunca "
                    "contra agendamento — e nenhuma dúvida de duplicidade pode ficar "
                    "sem dono."
                ),
                valor_em_risco=risco,
                destinatario="Contas a pagar + Controladoria",
                # MESMO grupo do AP-001: é o mesmo boleto de R$ 19.278,00.
                # AP-001 descreve a exposição; AP-004 descreve a falha de
                # controle que a deixou passar. Um valor, dois alertas.
                grupo_risco=(
                    f"duplicidade:{cobranca_viva.dominio}:"
                    f"{cobranca_viva.documento_normalizado}"
                    if cobranca_viva else "verificacao_agendamento"
                ),
                tipo_risco="potencial",
                evidencias=[
                    Evidencia(
                        regra="ap/verificacao_contra_data_futura",
                        detalhe=(
                            f"Mensagem em dia {dia_msg} afirma pagamento no dia "
                            f"{dia_citado}: na data da mensagem, o extrato não podia "
                            f"confirmar liquidação"
                        ),
                        campos={"dia_mensagem": dia_msg, "dia_citado": dia_citado},
                    ),
                    Evidencia(
                        regra="ap/duvida_sem_dono",
                        detalhe=(pendente.texto if pendente else
                                 "nenhuma dúvida explícita registrada"),
                        campos={"thread_encerrada_sem_resolucao": bool(pendente)},
                    ),
                ],
                referencias=[f"[{m.quando}] {m.area} - {m.autor}: {m.texto}"
                             for m in aprovacoes],
            )
        )
        break

    return alertas
