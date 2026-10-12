"""
Observabilidade.

Responde à pergunta do case: "onde a sua solução falha, e como a operação
descobre antes do cliente?".

Três mecanismos, em ordem de importância:

1. IDENTIDADE DE FECHAMENTO (`conferencia`). Uma equação que TEM que fechar ao
   centavo:

       títulos iniciais = valor aplicado + saldo em aberto
       créditos no banco = aplicado - retenções + mora + excedente inexplicado
                           + caixa não aplicado + créditos em investigação

   Se não fechar, o motor perdeu ou duplicou dinheiro, e o pipeline sai com
   código de erro. Não é teste unitário: é verificação em TODA execução, sobre
   os dados reais daquele dia. É o que impede a solução de errar em silêncio —
   o modo de falha que faz um time financeiro abandonar uma ferramenta.

2. DRIFT DE COBERTURA. A taxa de automatização é comparada a um baseline em
   config. Queda acima do tolerado vira alerta operacional. É assim que a
   Barte descobre que o Protheus mudou um layout antes de a Vantara ligar
   reclamando.

3. DECOMPOSIÇÃO DO SALDO EM ABERTO. Separa o que está sob validação, o que é
   saldo parcial e o que não encontrou recebimento no extrato analisado. Não
   transforma ausência de evidência em inadimplência comprovada.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from .canonico import (
    ClasseValor,
    Conciliacao,
    Decisao,
    MovimentoBancario,
    MovimentoOrfao,
    Severidade,
    TierIdentidade,
    Titulo,
    TituloEmAberto,
)

CENTAVO = Decimal("0.01")


@dataclass
class Conferencia:
    """Resultado das invariantes. `ok=False` deve fazer o pipeline falhar."""
    ok: bool
    checagens: list[dict[str, Any]] = field(default_factory=list)

    def registrar(self, nome: str, esperado: Decimal, obtido: Decimal, descricao: str) -> None:
        diff = (obtido - esperado).quantize(CENTAVO)
        passou = abs(diff) <= CENTAVO
        if not passou:
            self.ok = False
        self.checagens.append({
            "nome": nome,
            "descricao": descricao,
            "esperado": str(esperado.quantize(CENTAVO)),
            "obtido": str(obtido.quantize(CENTAVO)),
            "diferenca": str(diff),
            "passou": passou,
        })


def _soma(valores) -> Decimal:
    return sum(valores, Decimal("0")).quantize(CENTAVO)


def conferir_fechamento(
    titulos_valor_inicial: Decimal,
    conciliacoes: list[Conciliacao],
    em_aberto: list[TituloEmAberto],
    orfaos: list[MovimentoOrfao],
    creditos: list[MovimentoBancario],
) -> Conferencia:
    """
    As duas equações que não podem falhar.

    Tratamento dos casos INVESTIGAR: não consomem saldo (valor_aplicado = 0) e
    o título continua contado em aberto, então entram naturalmente nos dois
    lados. O crédito correspondente, porém, não foi aplicado — logo precisa ser
    contabilizado como pendente na segunda equação. É o detalhe que faz a conta
    fechar e que eu só descobri rodando a verificação.
    """
    conf = Conferencia(ok=True)

    aplicado = _soma(c.valor_aplicado for c in conciliacoes)
    saldo_aberto = _soma(e.titulo.saldo for e in em_aberto)

    conf.registrar(
        "titulos_conservados",
        titulos_valor_inicial,
        aplicado + saldo_aberto,
        "Soma dos títulos iniciais = valor vinculado na simulação + saldo em aberto. "
        "Falha aqui significa título perdido ou baixado duas vezes.",
    )

    # Ajustes de valor só entram quando algum saldo foi efetivamente vinculado.
    # INVESTIGAR preserva valor_aplicado=0 e entra abaixo pelo crédito integral.
    vinculadas = [c for c in conciliacoes if c.valor_aplicado > 0]
    retencoes = _soma(
        -c.diferenca for c in vinculadas if c.classe_valor == ClasseValor.RETENCAO
    )
    mora = _soma(c.diferenca for c in vinculadas if c.classe_valor == ClasseValor.MORA)
    # Quando o pagador foi identificado, mas chegou mais dinheiro do que o
    # título e a diferença não é mora, o título pode ficar vinculado para
    # revisão. O excesso continua sendo caixa pendente e não pode desaparecer
    # da conferência.
    excedente_inexplicado = _soma(
        c.diferenca
        for c in vinculadas
        if c.classe_valor == ClasseValor.INEXPLICADO and c.diferenca > 0
    )
    nao_aplicados = _soma(o.movimento.valor for o in orfaos)
    # Créditos vinculados mas com nada aplicado (decisão INVESTIGAR)
    em_investigacao = _soma(
        c.movimento.valor for c in conciliacoes if c.decisao == Decisao.INVESTIGAR
    )
    total_creditos = _soma(m.valor for m in creditos)

    conf.registrar(
        "caixa_conciliado",
        total_creditos,
        aplicado - retencoes + mora + excedente_inexplicado
        + nao_aplicados + em_investigacao,
        "Créditos do extrato = valor vinculado na simulação - retenções candidatas + mora candidata "
        "+ excedente inexplicado + caixa não aplicado + créditos em investigação. "
        "Falha aqui significa dinheiro do banco sem destino explicado.",
    )
    return conf


def _agregar_risco(alertas: list) -> dict[str, Any]:
    """
    Soma exposição sem contar o mesmo dinheiro duas vezes.

    Dois alertas podem descrever a MESMA exposição por ângulos diferentes:
    AP-001 é o boleto de R$ 19.278,00 reemitido de uma nota já paga; AP-004 é a
    conferência que deixou esse boleto passar. Somar os dois daria R$ 38.556,00
    de "risco" que não existe.

    Por isso cada alerta carrega `grupo_risco`, e o total é o MÁXIMO por grupo —
    não a soma. E `tipo_risco` separa perda com evidência concreta de exposição
    que simplesmente não dá para verificar. Juntar as duas num número só é o
    tipo de inflação que um CTO desmonta em trinta segundos de reunião.
    """
    grupos: dict[str, tuple[str, Decimal]] = {}
    for a in alertas:
        chave = a.chave_risco
        tipo = getattr(a, "tipo_risco", "potencial")
        atual = grupos.get(chave)
        if atual is None or a.valor_em_risco > atual[1]:
            grupos[chave] = (tipo, a.valor_em_risco)

    confirmado = _soma(v for t, v in grupos.values() if t == "confirmado")
    potencial = _soma(v for t, v in grupos.values() if t == "potencial")
    sem_controle = _soma(v for t, v in grupos.values() if t == "sem_controle")
    return {
        "valor_em_risco_confirmado": str(confirmado),
        "valor_exposicao_potencial": str(potencial),
        "valor_sem_controle": str(sem_controle),
        "valor_em_risco": str(confirmado + potencial),
        "grupos_de_exposicao": len(grupos),
        "nota": (
            "valor_em_risco_confirmado = perda já materializada e comprovada. "
            "valor_exposicao_potencial = valor que pode ficar exposto se o alerta "
            "não for tratado. valor_sem_controle = valor que não é possível "
            "verificar com os dados disponíveis. Alertas sobre o mesmo dinheiro "
            "são contados uma vez por grupo."
        ),
    }


def montar_metricas(
    titulos: list[Titulo],
    titulos_valor_inicial: Decimal,
    movimentos: list[MovimentoBancario],
    conciliacoes: list[Conciliacao],
    orfaos: list[MovimentoOrfao],
    em_aberto: list[TituloEmAberto],
    alertas: list,
    trilha_passes: dict[str, int],
    conferencia: Conferencia,
    resumo_ia: dict,
    cfg: dict,
) -> dict[str, Any]:
    creditos = [m for m in movimentos if m.is_credito]
    total_creditos = _soma(m.valor for m in creditos)
    aplicado = _soma(c.valor_aplicado for c in conciliacoes)

    por_tier: dict[str, dict[str, Any]] = {}
    for t in TierIdentidade:
        grupo = [c for c in conciliacoes if c.tier == t]
        if not grupo:
            continue
        por_tier[t.value] = {
            "quantidade": len(grupo),
            "valor": str(_soma(c.movimento.valor for c in grupo)),
            "confianca_media": round(sum(c.confianca for c in grupo) / len(grupo), 3),
        }

    por_decisao: dict[str, dict[str, Any]] = {}
    for d in Decisao:
        grupo = [c for c in conciliacoes if c.decisao == d]
        por_decisao[d.value] = {
            "quantidade": len(grupo),
            "valor": str(_soma(c.movimento.valor for c in grupo)),
        }

    por_classe = {
        cl.value: len([c for c in conciliacoes if c.classe_valor == cl])
        for cl in ClasseValor
        if any(c.classe_valor == cl for c in conciliacoes)
    }
    excedente_inexplicado = _soma(
        c.diferenca
        for c in conciliacoes
        if c.valor_aplicado > 0
        and c.classe_valor == ClasseValor.INEXPLICADO
        and c.diferenca > 0
    )

    auto = [c for c in conciliacoes if c.decisao == Decisao.AUTO_APLICAR]
    valor_auto = _soma(c.movimento.valor for c in auto)
    confirmar = [c for c in conciliacoes if c.decisao == Decisao.CONFIRMAR]
    investigar = [c for c in conciliacoes if c.decisao == Decisao.INVESTIGAR]
    valor_em_analise = _soma(
        [c.movimento.valor for c in confirmar + investigar]
        + [o.movimento.valor for o in orfaos]
    )

    cobertura_valor = float(aplicado / titulos_valor_inicial) if titulos_valor_inicial else 0.0
    cobertura_credito = float(
        (total_creditos - _soma(o.movimento.valor for o in orfaos)) / total_creditos
    ) if total_creditos else 0.0
    taxa_auto = float(valor_auto / total_creditos) if total_creditos else 0.0

    # ----- decomposição do saldo em aberto, sem promover hipótese a fato
    em_validacao = _soma(e.titulo.saldo for e in em_aberto if not e.e_cobravel)
    parcial = _soma(
        e.titulo.saldo for e in em_aberto
        if e.e_cobravel and e.titulo.saldo < e.titulo.valor
    )
    sem_recebimento_identificado = _soma(
        e.titulo.saldo for e in em_aberto
        if e.e_cobravel and e.titulo.saldo >= e.titulo.valor
    )
    gap_aparente = (titulos_valor_inicial - total_creditos).quantize(CENTAVO)
    total_aberto = (
        em_validacao + parcial + sem_recebimento_identificado
    ).quantize(CENTAVO)

    # ----- drift
    obs = cfg["observabilidade"]
    base_cob = float(obs["baseline_cobertura_valor"])
    base_auto = float(obs["baseline_auto_aplicavel"])
    tol_pp = float(obs["drift_tolerado_pp"])
    drift_cob = (cobertura_credito - base_cob) * 100
    drift_auto = (taxa_auto - base_auto) * 100
    alertas_drift = []
    if drift_cob < -tol_pp:
        alertas_drift.append(
            f"Cobertura de créditos em {cobertura_credito:.1%}, "
            f"{abs(drift_cob):.1f} p.p. abaixo do baseline de {base_cob:.0%} "
            f"(tolerância {tol_pp:.0f} p.p.) — investigar mudança de layout, "
            f"novo meio de pagamento ou degradação de cadastro"
        )
    if drift_auto < -tol_pp:
        alertas_drift.append(
            f"Automatização em {taxa_auto:.1%}, {abs(drift_auto):.1f} p.p. abaixo do "
            f"baseline de {base_auto:.0%} — a fila humana vai crescer neste ciclo"
        )

    sev = {s.value: len([a for a in alertas if a.severidade == s]) for s in Severidade}
    risco = _agregar_risco(alertas)

    return {
        "volumetria": {
            "titulos_em_aberto_entrada": len(titulos),
            "valor_titulos_entrada": str(titulos_valor_inicial),
            "movimentos_bancarios": len(movimentos),
            "creditos": len(creditos),
            "valor_creditos": str(total_creditos),
        },
        "conciliacao": {
            "creditos_conciliados": len(conciliacoes),
            "creditos_nao_aplicados": len(orfaos),
            "valor_aplicado": str(aplicado),
            "valor_excedente_inexplicado_em_analise": str(excedente_inexplicado),
            "cobertura_de_creditos": round(cobertura_credito, 4),
            "cobertura_de_titulos": round(cobertura_valor, 4),
            "taxa_automatizavel_valor": round(taxa_auto, 4),
            "por_tier_de_identidade": por_tier,
            "por_decisao": por_decisao,
            "por_classe_de_valor": por_classe,
            "trilha_de_passes": trilha_passes,
        },
        "fechamento_caixa": {
            # "Validado" aqui significa que passou pelas travas do motor e
            # está pronto para uma proposta. Ainda não é baixa efetivada:
            # o piloto permanece sem escrita no ERP.
            "valor_caixa_validado_para_proposta": str(valor_auto),
            "valor_caixa_em_analise_humana": str(valor_em_analise),
            "valor_caixa_total": str(total_creditos),
            "percentual_validado_para_proposta": round(
                float(valor_auto / total_creditos), 4
            ) if total_creditos else 0.0,
            "percentual_em_analise_humana": round(
                float(valor_em_analise / total_creditos), 4
            ) if total_creditos else 0.0,
            "creditos_validados_para_proposta": len(auto),
            "creditos_em_analise_humana": len(confirmar) + len(investigar) + len(orfaos),
            "nota": (
                "Caixa validado para proposta passou pelas travas de alta confiança; "
                "não representa baixa efetivada. Caixa em análise humana inclui "
                "CONFIRMAR, INVESTIGAR e créditos sem título."
            ),
        },
        "decomposicao_do_gap": {
            "gap_aparente": str(gap_aparente),
            "total_em_aberto_ao_final": str(total_aberto),
            "em_validacao_possivel_duplicidade": str(em_validacao),
            "saldo_de_pagamento_parcial": str(parcial),
            "sem_recebimento_identificado_no_extrato": str(sem_recebimento_identificado),
            "percentual_sem_recebimento_identificado": (
                round(float(sem_recebimento_identificado / total_aberto), 4)
                if total_aberto else 0.0
            ),
            "leitura": (
                f"Do total de {total_aberto!s} em aberto ao final, "
                f"{sem_recebimento_identificado!s} não encontrou recebimento no "
                "extrato analisado. Isso não prova inadimplência: a Vantara opera "
                "quatro bancos e o data pack contém apenas uma conta."
            ),
        },
        "alertas": {
            "total": len(alertas),
            "por_severidade": sev,
            **risco,
        },
        "ia": resumo_ia,
        "saude": {
            "conferencia_de_fechamento_ok": conferencia.ok,
            "checagens": conferencia.checagens,
            "drift": {
                "cobertura_pp_vs_baseline": round(drift_cob, 2),
                "automatizacao_pp_vs_baseline": round(drift_auto, 2),
                "alertas": alertas_drift,
            },
        },
    }
