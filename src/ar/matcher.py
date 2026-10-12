"""
Motor de conciliação de contas a receber.

EIXO IDENTIDADE (aqui) x EIXO VALOR (src/ar/valor.py).

A ordem dos passes é a decisão mais importante do arquivo. Não processo os
créditos por data: processo por FORÇA DE EVIDÊNCIA. Primeiro todos os créditos
que têm identificador bancário, depois os que têm CNPJ no texto, depois nome,
depois IA, e só por último os que casam apenas por valor.

Por quê: o motor é guloso — quem casa primeiro consome o saldo do título. Se eu
deixasse o "casou só por valor" rodar antes do "nosso_numero", um depósito não
identificado de R$ 31.250 poderia consumir o título do Grão Nobre antes de o
boleto correto aparecer. Processar por evidência garante que a decisão fraca só
vê o que a decisão forte não quis.

Cada passe declara se aceita encostar em título já marcado como fantasma.
Evidência forte pode; evidência fraca não — porque casar um título duplicado
conhecido por heurística de valor é exatamente como se esconde o problema de
cadastro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ..canonico import (
    Conciliacao,
    Decisao,
    Evidencia,
    MovimentoBancario,
    MovimentoOrfao,
    Severidade,
    TierIdentidade,
    Titulo,
    TituloEmAberto,
    ClasseValor,
)
from ..ia.cliente import ClienteIA
from ..identidade.resolver import ResolvedorEntidades, evidencia_identidade
from ..normalizacao import (
    NormalizadorNome,
    extrair_documentos_fiscais,
    fmt_brl,
    fmt_data,
)
from .valor import AnaliseValor, achar_combinacao, classificar_valor


@dataclass
class ResultadoAR:
    conciliacoes: list[Conciliacao] = field(default_factory=list)
    orfaos: list[MovimentoOrfao] = field(default_factory=list)
    em_aberto: list[TituloEmAberto] = field(default_factory=list)
    trilha_passes: dict[str, int] = field(default_factory=dict)


class MotorConciliacaoAR:
    def __init__(
        self,
        cfg: dict,
        resolvedor: ResolvedorEntidades,
        normalizador: NormalizadorNome,
        ia: ClienteIA | None = None,
    ):
        self.cfg = cfg
        self.resolvedor = resolvedor
        self.norm = normalizador
        self.ia = ia
        self.conf_id = cfg["confianca_identidade"]
        self.ajuste_valor = cfg["ajuste_valor"]
        self.travas = cfg["travas_auto_aplicar"]
        self.dec = cfg["decisao"]

    # ==================================================================
    def conciliar(
        self,
        movimentos: list[MovimentoBancario],
        titulos: list[Titulo],
        ids_fantasma: set[str] | None = None,
    ) -> ResultadoAR:
        ids_fantasma = ids_fantasma or set()
        res = ResultadoAR()

        creditos = [m for m in movimentos if m.is_credito]
        por_id = {t.id: t for t in titulos}
        pendentes = list(creditos)

        passes = [
            ("1_id_bancario", self._passe_id_bancario, True),
            ("2_cnpj_texto", self._passe_cnpj_texto, True),
            ("3_nome", self._passe_nome, True),
            ("4_ia", self._passe_ia, False),
            ("5_so_valor", self._passe_so_valor, False),
        ]

        for nome_passe, fn, permite_fantasma in passes:
            restantes: list[MovimentoBancario] = []
            casados = 0
            for mov in pendentes:
                conc = fn(mov, titulos, ids_fantasma, permite_fantasma)
                if conc is None:
                    restantes.append(mov)
                    continue
                self._aplicar(conc)
                res.conciliacoes.append(conc)
                casados += 1
            res.trilha_passes[nome_passe] = casados
            pendentes = restantes

        # Créditos que sobraram: caixa não aplicado
        for mov in pendentes:
            res.orfaos.append(self._orfao(mov, titulos))

        # Títulos que sobraram em aberto
        res.em_aberto = self._classificar_em_aberto(titulos, ids_fantasma, por_id)
        return res

    # ==================================================================
    # Helpers de candidatura
    # ------------------------------------------------------------------
    def _na_janela(self, mov: MovimentoBancario, titulo: Titulo) -> bool:
        if titulo.vencimento is None:
            return True
        j = self.cfg["janela_credito"]
        atraso = (mov.data - titulo.vencimento).days
        return -int(j["dias_antes"]) <= atraso <= int(j["dias_depois"])

    def _candidatos_da_entidade(
        self,
        mov: MovimentoBancario,
        titulos: list[Titulo],
        entidade_id: str,
        ids_fantasma: set[str],
        permite_fantasma: bool,
    ) -> list[Titulo]:
        saida = []
        for t in titulos:
            if t.entidade_id != entidade_id or t.saldo <= 0:
                continue
            if not permite_fantasma and t.id in ids_fantasma:
                continue
            if not self._na_janela(mov, t):
                continue
            saida.append(t)
        # Vencimento mais antigo primeiro: em cobrança, o padrão é quitar o
        # título mais velho (FIFO). Não é lei, mas é o comportamento esperado
        # pela controladoria e evita escolha arbitrária entre empates.
        saida.sort(key=lambda t: (t.vencimento or date.max, t.documento))
        return saida

    def _escolher_por_valor(
        self,
        mov: MovimentoBancario,
        candidatos: list[Titulo],
        aceitar_inexplicado: bool = False,
    ) -> tuple[list[Titulo], AnaliseValor] | None:
        """
        Dado o pagador já identificado, escolhe QUAIS títulos aquele crédito
        quita. Ordem de preferência, da hipótese mais simples para a mais
        elaborada — porque a explicação mais simples que fecha a conta é a que
        a analista aceita sem desconfiar.

        `aceitar_inexplicado` existe por uma lição do data pack de estresse.
        Um crédito de R$ 21.000,00 com o nome completo do franqueado no
        histórico, contra um título de R$ 20.000,00 vencido no dia anterior, não
        casa com a fórmula de mora (5% de excesso contra 2,03% esperados). Minha
        primeira versão devolvia None e o crédito virava "caixa não aplicado".

        Isso é pior para a operação: o pagador ESTÁ identificado, e a analista
        recebia um órfão em vez de "crédito de 21.000 contra o título X,
        diferença de 1.000 sem explicação". Então: identidade forte linka mesmo
        sem explicar o valor, e a trava rebaixa para confirmação humana.
        Identidade fraca continua não linkando — vínculo ruim com evidência
        ruim é pior que nenhum vínculo.
        """
        if not candidatos:
            return None

        # (a) um título com saldo exato
        for t in candidatos:
            if abs(t.saldo - mov.valor) <= Decimal(str(self.cfg["tolerancia_centavos"])):
                return [t], classificar_valor(mov.valor, [t], mov.data, self.cfg)

        # (b) combinação de títulos que soma o crédito
        combo = achar_combinacao(mov.valor, candidatos, self.cfg)
        if combo:
            return combo, classificar_valor(mov.valor, combo, mov.data, self.cfg)

        # (c) diferença explicável: retenção ou mora, título a título
        for t in candidatos:
            analise = classificar_valor(mov.valor, [t], mov.data, self.cfg)
            if analise.classe in (ClasseValor.RETENCAO, ClasseValor.MORA):
                return [t], analise

        # (d) pagamento parcial: o crédito cabe dentro de um título
        parciais = [t for t in candidatos if mov.valor < t.saldo]
        if parciais:
            # maior título primeiro: um crédito pequeno contra um título grande
            # é mais plausivelmente parcial dele do que de um título de valor
            # próximo que ficaria com saldo residual esquisito.
            t = max(parciais, key=lambda x: x.saldo)
            return [t], classificar_valor(mov.valor, [t], mov.data, self.cfg)

        # (e) sobra inexplicada contra o título mais próximo
        t = min(candidatos, key=lambda x: abs(x.saldo - mov.valor))
        analise = classificar_valor(mov.valor, [t], mov.data, self.cfg)
        if analise.classe == ClasseValor.INEXPLICADO and not aceitar_inexplicado:
            return None          # identidade fraca: melhor órfão que vínculo ruim
        return [t], analise

    # ==================================================================
    # Passes
    # ------------------------------------------------------------------
    def _passe_id_bancario(
        self, mov, titulos, ids_fantasma, permite_fantasma
    ) -> Conciliacao | None:
        """nosso_numero do boleto no campo documento do extrato. Evidência máxima."""
        if not mov.documento:
            return None
        alvos = [t for t in titulos if t.id_bancario and t.id_bancario == mov.documento]
        alvos = [t for t in alvos if t.saldo > 0]
        if not permite_fantasma:
            alvos = [t for t in alvos if t.id not in ids_fantasma]
        if not alvos:
            return None

        titulo = alvos[0]
        analise = classificar_valor(mov.valor, [titulo], mov.data, self.cfg)
        ev = [
            Evidencia(
                regra="identidade/nosso_numero",
                detalhe=(
                    f"Campo documento do extrato ({mov.bruto.get('documento', mov.documento)}) "
                    f"é o nosso_numero do título {titulo.documento}"
                ),
                campos={"nosso_numero": mov.documento},
            ),
            *analise.evidencias,
        ]
        extra = []
        if len(alvos) > 1:
            extra.append(f"{len(alvos)} títulos com o mesmo nosso_numero — revisar cadastro")
        return self._montar(
            mov, [titulo], TierIdentidade.ID_BANCARIO, analise, ev,
            candidatos_descartados=len(alvos) - 1,
            observacao="; ".join(extra),
        )

    # ------------------------------------------------------------------
    def _passe_cnpj_texto(
        self, mov, titulos, ids_fantasma, permite_fantasma
    ) -> Conciliacao | None:
        """CNPJ cru enterrado no histórico: 'PIX RECEBIDO 11222333000166'."""
        docs = extrair_documentos_fiscais(mov.historico)
        if not docs:
            return None
        cand_ent = self.resolvedor.identificar_por_cnpj(docs)
        if not cand_ent:
            return None

        candidatos = self._candidatos_da_entidade(
            mov, titulos, cand_ent.entidade.id, ids_fantasma, permite_fantasma
        )
        escolha = self._escolher_por_valor(mov, candidatos, aceitar_inexplicado=True)
        if not escolha:
            return None
        alvos, analise = escolha
        ev = [evidencia_identidade(cand_ent, mov.historico), *analise.evidencias]
        return self._montar(
            mov, alvos, TierIdentidade.CNPJ_TEXTO, analise, ev,
            candidatos_descartados=max(0, len(candidatos) - len(alvos)),
        )

    # ------------------------------------------------------------------
    def _passe_nome(
        self, mov, titulos, ids_fantasma, permite_fantasma
    ) -> Conciliacao | None:
        """
        Nome truncado no histórico. O passe que mais trabalha neste data pack.

        Trata empate explicitamente: se dois candidatos têm a mesma cobertura e
        ambos conseguem explicar o valor, não escolhe — manda para a IA ou para
        o humano. Escolher no empate é como se produz baixa errada silenciosa.
        """
        candidatos_ent = self.resolvedor.identificar_por_nome(mov.historico)
        if not candidatos_ent:
            return None

        viaveis: list[tuple] = []
        for ce in candidatos_ent:
            if ce.cobertura < 1.0 and ce.tokens_casados < 2:
                continue
            cands = self._candidatos_da_entidade(
                mov, titulos, ce.entidade.id, ids_fantasma, permite_fantasma
            )
            ident_forte = ce.cobertura >= 1.0 and ce.tokens_casados >= int(
                self.cfg["nome"]["min_tokens_nome_forte"]
            )
            escolha = self._escolher_por_valor(
                mov, cands, aceitar_inexplicado=ident_forte
            )
            if escolha:
                viaveis.append((ce, escolha, len(cands)))

        if not viaveis:
            return None

        melhor_cob = max(v[0].cobertura for v in viaveis)
        topo = [v for v in viaveis if v[0].cobertura >= melhor_cob - 1e-9]
        if len(topo) > 1:
            # Empate real entre entidades distintas: não decide aqui.
            return None

        ce, (alvos, analise), n_cands = topo[0]
        forte = ce.cobertura >= 1.0 and ce.tokens_casados >= int(
            self.cfg["nome"]["min_tokens_nome_forte"]
        )
        tier = TierIdentidade.NOME_FORTE if forte else TierIdentidade.NOME_PARCIAL
        ev = [evidencia_identidade(ce, mov.historico), *analise.evidencias]
        obs = ""
        if not forte:
            obs = (
                f"Identificação por nome fraca ({ce.tokens_casados} token útil no "
                f"histórico) — confirmar o pagador antes de baixar"
            )
        return self._montar(
            mov, alvos, tier, analise, ev,
            candidatos_descartados=max(0, n_cands - len(alvos)),
            observacao=obs,
        )

    # ------------------------------------------------------------------
    def _passe_ia(self, mov, titulos, ids_fantasma, permite_fantasma) -> Conciliacao | None:
        """
        Rede de segurança: nome muito distorcido ou empate entre entidades.

        Monta uma lista FECHADA de candidatos plausíveis e pede ao modelo para
        escolher ou se abster. O modelo não vê a base inteira e não pode
        responder nada fora da lista.
        """
        if not self.ia or not self.ia.ativa:
            return None

        # Candidatos: qualquer título em aberto, na janela, com valor compatível
        # (exato, ou diferença de até 10% que poderia ser retenção/mora).
        plausiveis: list[Titulo] = []
        for t in titulos:
            if t.saldo <= 0 or (not permite_fantasma and t.id in ids_fantasma):
                continue
            if not self._na_janela(mov, t):
                continue
            if t.saldo == 0:
                continue
            desvio = abs(t.saldo - mov.valor) / t.saldo
            if desvio <= Decimal("0.10"):
                plausiveis.append(t)
        if not plausiveis:
            return None

        max_cands = int(self.cfg.get("ia", {}).get("max_candidatos_no_prompt", 8))
        if len(plausiveis) > max_cands:
            plausiveis.sort(key=lambda t: abs(t.saldo - mov.valor))
            plausiveis = plausiveis[:max_cands]

        payload = [
            {
                "titulo_id": t.id,
                "cliente": t.nome_original,
                "cnpj": t.cnpj,
                "documento": t.documento,
                "tipo": t.tipo,
                "vencimento": fmt_data(t.vencimento),
                "valor_face": fmt_brl(t.valor),
                "saldo": fmt_brl(t.saldo),
                "sistema_origem": t.fonte,
            }
            for t in plausiveis
        ]
        decisao = self.ia.escolher_titulo(
            historico=mov.historico,
            valor_credito=fmt_brl(mov.valor),
            data_credito=fmt_data(mov.data),
            candidatos=payload,
        )
        if decisao.absteve or not decisao.escolha:
            return None

        titulo = next((t for t in plausiveis if t.id == decisao.escolha), None)
        if titulo is None:
            return None

        analise = classificar_valor(mov.valor, [titulo], mov.data, self.cfg)
        ev = [
            Evidencia(
                regra="identidade/ia_desempate",
                detalhe=(
                    f"IA escolheu entre {len(plausiveis)} candidatos de lista fechada "
                    f"(confiança {decisao.confianca:.2f}): {decisao.justificativa}"
                ),
                campos={
                    "confianca_ia": decisao.confianca,
                    "candidatos_oferecidos": len(plausiveis),
                    "modelo": self.ia.modelo,
                },
            ),
            *analise.evidencias,
        ]
        return self._montar(
            mov, [titulo], TierIdentidade.IA, analise, ev,
            candidatos_descartados=len(plausiveis) - 1,
            observacao="Proposto por IA — exige confirmação humana por política",
            confianca_base=min(decisao.confianca, float(self.conf_id["IA"])),
        )

    # ------------------------------------------------------------------
    def _passe_so_valor(
        self, mov, titulos, ids_fantasma, permite_fantasma
    ) -> Conciliacao | None:
        """
        Último recurso: 'DEPOSITO NAO IDENTIFICADO'. Zero pista de pagador.

        Nunca é automático (trava em config). Com 1.900 títulos/mês a colisão
        de valor cresce, então a unicidade do valor na base é parte do score e
        a falta dela derruba o caso para investigação.
        """
        elegiveis = [
            t for t in titulos
            if t.saldo > 0
            and (permite_fantasma or t.id not in ids_fantasma)
            and self._na_janela(mov, t)
        ]
        tol = Decimal(str(self.cfg["tolerancia_centavos"]))
        exatos = [t for t in elegiveis if abs(t.saldo - mov.valor) <= tol]
        if not exatos:
            return None

        unico = len(exatos) == 1
        titulo = exatos[0]
        analise = classificar_valor(mov.valor, [titulo], mov.data, self.cfg)
        bonus = float(self.dec["bonus_unicidade"]) if unico else 0.0

        detalhe = (
            f"Histórico sem pagador identificável. "
            + (
                f"Único título em aberto com saldo exatamente igual a "
                f"{fmt_brl(mov.valor)} na janela."
                if unico else
                f"{len(exatos)} títulos em aberto com o mesmo valor — vínculo ambíguo."
            )
        )
        obs = (
            "Casou apenas por valor. Confirmar com o franqueado ou pelo "
            "comprovante antes de baixar."
            if unico else
            f"AMBÍGUO: {len(exatos)} títulos com valor idêntico "
            f"({', '.join(t.documento for t in exatos)}). Não baixar."
        )
        return self._montar(
            mov, [titulo], TierIdentidade.SO_VALOR, analise,
            [Evidencia(regra="identidade/apenas_valor", detalhe=detalhe,
                       campos={"candidatos_mesmo_valor": len(exatos)}),
             *analise.evidencias],
            candidatos_descartados=len(exatos) - 1,
            observacao=obs,
            bonus=bonus,
            empate=not unico,
        )

    # ==================================================================
    # Montagem, confiança e decisão
    # ------------------------------------------------------------------
    def _montar(
        self,
        mov: MovimentoBancario,
        titulos: list[Titulo],
        tier: TierIdentidade,
        analise: AnaliseValor,
        evidencias: list[Evidencia],
        candidatos_descartados: int = 0,
        observacao: str = "",
        confianca_base: float | None = None,
        bonus: float = 0.0,
        empate: bool = False,
    ) -> Conciliacao:
        base = confianca_base if confianca_base is not None else float(self.conf_id[tier.value])
        confianca = base + float(self.ajuste_valor[analise.classe.value]) + bonus
        confianca = max(0.0, min(1.0, confianca))

        decisao, motivo_trava = self._decidir(confianca, tier, analise, empate, titulos)
        if motivo_trava:
            evidencias.append(
                Evidencia(
                    regra="governanca/trava_de_automacao",
                    detalhe=motivo_trava,
                    campos={"confianca_calculada": round(confianca, 3)},
                )
            )

        return Conciliacao(
            movimento=mov,
            titulos=titulos,
            tier=tier,
            classe_valor=analise.classe,
            confianca=round(confianca, 3),
            decisao=decisao,
            valor_aplicado=(analise.valor_aplicado if decisao != Decisao.INVESTIGAR
                            else Decimal("0")),
            diferenca=analise.diferenca,
            evidencias=evidencias,
            candidatos_descartados=candidatos_descartados,
            acao_sugerida=self._acao(decisao, analise, titulos),
            observacao_analista=observacao,
        )

    def _decidir(
        self, confianca: float, tier: TierIdentidade, analise: AnaliseValor,
        empate: bool, titulos: list[Titulo],
    ) -> tuple[Decisao, str]:
        """
        Faixa de confiança decide o caminho; as travas podem só REBAIXAR.

        Nenhuma trava eleva um caso para automático. É assimétrico de
        propósito: o custo de uma baixa errada (cobrança indevida a franqueado,
        exatamente a dor que o Head de Franquias relatou) é muito maior que o
        custo de uma confirmação humana a mais.
        """
        if confianca >= float(self.dec["auto_aplicar_min"]):
            alvo = Decisao.AUTO_APLICAR
        elif confianca >= float(self.dec["revisar_min"]):
            alvo = Decisao.CONFIRMAR
        else:
            return Decisao.INVESTIGAR, ""

        if alvo != Decisao.AUTO_APLICAR:
            if empate:
                return Decisao.INVESTIGAR, "Candidatos empatados: vínculo ambíguo"
            return alvo, ""

        t = self.travas
        if t.get("bloquear_se_valor_inexplicado") and analise.classe == ClasseValor.INEXPLICADO:
            return Decisao.CONFIRMAR, "Trava: diferença de valor sem explicação financeira"
        if t.get("bloquear_se_empate_de_candidatos") and empate:
            return Decisao.INVESTIGAR, "Trava: candidatos empatados"
        if t.get("bloquear_tier_so_valor") and tier == TierIdentidade.SO_VALOR:
            return Decisao.CONFIRMAR, "Trava: identificação apenas por valor nunca é automática"
        if t.get("bloquear_se_decidido_por_ia") and tier == TierIdentidade.IA:
            return Decisao.CONFIRMAR, "Trava: decisão de IA exige confirmação humana"
        classes_confirmacao = set(t.get("classes_que_exigem_confirmacao", []))
        if analise.classe.value in classes_confirmacao:
            return Decisao.CONFIRMAR, (
                f"Trava: {analise.classe.value} é hipótese financeira; validar contrato "
                "e documento de suporte antes da baixa"
            )
        teto = Decimal(str(t.get("valor_maximo_automatico", 0) or 0))
        soma = sum((x.saldo for x in titulos), Decimal("0"))
        if teto > 0 and soma > teto:
            return Decisao.CONFIRMAR, (
                f"Trava: valor {fmt_brl(soma)} acima do teto automático de {fmt_brl(teto)}"
            )
        return Decisao.AUTO_APLICAR, ""

    @staticmethod
    def _acao(decisao: Decisao, analise: AnaliseValor, titulos: list[Titulo]) -> str:
        docs = ", ".join(t.documento for t in titulos)
        if decisao == Decisao.INVESTIGAR:
            return f"INVESTIGAR vínculo com {docs} — nada aplicado"
        verbo = "Baixar" if decisao == Decisao.AUTO_APLICAR else "Conferir e baixar"
        if analise.classe == ClasseValor.PARCIAL:
            return f"{verbo} PARCIALMENTE {docs} ({fmt_brl(analise.valor_aplicado)})"
        if analise.classe == ClasseValor.RETENCAO:
            return f"{verbo} TOTAL {docs} + lançar retenção de {fmt_brl(-analise.diferenca)}"
        if analise.classe == ClasseValor.MORA:
            return f"{verbo} TOTAL {docs} + receita financeira de {fmt_brl(analise.diferenca)}"
        return f"{verbo} TOTAL {docs}"

    @staticmethod
    def _aplicar(conc: Conciliacao) -> None:
        """
        Consome saldo dos títulos. Só para casos que seguem adiante — INVESTIGAR
        não consome nada, porque um vínculo duvidoso que consome saldo faz o
        título desaparecer da cobrança sem ninguém ter decidido.
        """
        if conc.decisao == Decisao.INVESTIGAR:
            return
        restante = conc.valor_aplicado
        for t in conc.titulos:
            if restante <= 0:
                break
            usa = min(t.saldo, restante)
            t.saldo = (t.saldo - usa).quantize(Decimal("0.01"))
            restante -= usa

    # ==================================================================
    def _orfao(self, mov: MovimentoBancario, titulos: list[Titulo]) -> MovimentoOrfao:
        """
        Crédito sem título. Em finanças: caixa não aplicado.

        Mesmo sem casar, tento identificar o PAGADOR — porque 'R$ 1.850,00 da
        Padaria Vila Nova sem título correspondente' é uma pergunta que a
        analista resolve com um telefonema, enquanto 'crédito não identificado'
        é um item que fica na planilha para sempre.
        """
        entidade = None
        docs = extrair_documentos_fiscais(mov.historico)
        cand = self.resolvedor.identificar_por_cnpj(docs) if docs else None
        if not cand:
            por_nome = self.resolvedor.identificar_por_nome(mov.historico)
            cand = por_nome[0] if por_nome and por_nome[0].cobertura >= 1.0 else None
        if cand:
            entidade = self.resolvedor.descrever(cand.entidade.id)

        proximos = sorted(
            (t for t in titulos if t.saldo > 0),
            key=lambda t: abs(t.saldo - mov.valor),
        )[:3]

        if entidade:
            motivo = (
                f"Pagador identificado ({entidade}), mas nenhum título em aberto "
                f"de {fmt_brl(mov.valor)} nem combinação que some esse valor. "
                f"Provável adiantamento, acerto de saldo antigo ou pagamento de "
                f"título fora desta base. Vai para conta transitória até ser aplicado."
            )
        else:
            motivo = (
                f"Nem pagador nem título identificados para {fmt_brl(mov.valor)}. "
                f"Histórico do banco não traz nome nem CNPJ."
            )

        return MovimentoOrfao(
            movimento=mov,
            motivo=motivo,
            entidade_provavel=entidade,
            candidatos_proximos=[
                f"{t.documento} ({t.nome_original}, saldo {fmt_brl(t.saldo)})"
                for t in proximos
            ],
        )

    # ------------------------------------------------------------------
    def _classificar_em_aberto(
        self, titulos: list[Titulo], ids_fantasma: set[str], por_id: dict[str, Titulo]
    ) -> list[TituloEmAberto]:
        """
        Fecha a conta: todo título que sobrou precisa de um motivo e de uma
        resposta sobre se pode ser cobrado.

        A distinção `e_cobravel` é o entregável mais valioso desta função. É o
        que impede o time de cobrança de ligar para quem já pagou — que é
        literalmente o que o Head de Operações de Franquias descreveu.
        """
        saida: list[TituloEmAberto] = []
        for t in titulos:
            if t.saldo <= Decimal("0.01"):
                continue

            if t.id in ids_fantasma:
                saida.append(TituloEmAberto(
                    titulo=t,
                    motivo=(
                        "Possível duplicidade entre ERPs (ver alerta CAD-001). "
                        "SUSPENDER COBRANÇA por até 48h e validar documento de origem, "
                        "pedido/contrato e histórico do cadastro antes de concluir se "
                        "a dívida é duplicada ou legítima."
                    ),
                    severidade=Severidade.CRITICO,
                    e_cobravel=False,
                ))
                continue

            parcial = t.saldo < t.valor
            if parcial:
                saida.append(TituloEmAberto(
                    titulo=t,
                    motivo=(
                        f"Saldo residual de pagamento parcial: recebido "
                        f"{fmt_brl(t.valor - t.saldo)} de {fmt_brl(t.valor)}. "
                        f"Cobrar apenas o saldo."
                    ),
                    severidade=Severidade.ALTO,
                    e_cobravel=True,
                ))
                continue

            saida.append(TituloEmAberto(
                titulo=t,
                motivo=(
                    f"Nenhum crédito identificado para este título "
                    f"(venc. {fmt_data(t.vencimento)}) no extrato analisado. Validar "
                    f"as demais contas bancárias e eventos de baixa antes de cobrar."
                ),
                severidade=Severidade.MEDIO,
                e_cobravel=True,
            ))

        saida.sort(key=lambda x: (x.e_cobravel, -float(x.titulo.saldo)))
        return saida
