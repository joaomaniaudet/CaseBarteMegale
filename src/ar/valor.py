"""
Eixo VALOR: por que o dinheiro que entrou não é igual ao valor de face.

O motor tem dois eixos independentes, e separá-los é a decisão de arquitetura
mais importante do projeto:

    EIXO IDENTIDADE  ->  de quem é esse dinheiro?   (src/ar/matcher.py)
    EIXO VALOR       ->  por que o valor difere?    (este arquivo)

Por que separar: a maioria das soluções de conciliação trata "valor diferente"
como "não casou". Mas no data pack de julho, 4 dos 13 créditos conciliáveis
têm valor diferente do título — e todos os 4 têm explicação financeira legítima:

    125.000,00 -> 62.500,00   pagamento parcial
     15.600,00 -> 14.820,00   candidato a retenção de 5% (confirmar documento)
     22.900,00 -> 23.358,00   candidato a multa de 2% (confirmar contrato)
     47.630,50 <- 2 títulos   um TED quitando produto + royalty juntos

Se o motor exige valor exato, esses 4 caem na exceção e a analista continua
fazendo o trabalho na mão. Pior: o caso da retenção geraria cobrança de R$ 780
de imposto que o franqueado já pagou à prefeitura.

Cada classificação carrega a conta que a justifica. A analista não precisa
confiar no motor: ela lê a aritmética.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from itertools import combinations

from ..canonico import ClasseValor, Evidencia, Titulo
from ..normalizacao import fmt_brl, fmt_data

CENTAVO = Decimal("0.01")


@dataclass
class AnaliseValor:
    classe: ClasseValor
    valor_aplicado: Decimal
    diferenca: Decimal                  # crédito - soma(saldos dos títulos)
    explicacao: str
    evidencias: list[Evidencia] = field(default_factory=list)
    quita_titulos: bool = True          # False quando sobra saldo


def _frac(parte: Decimal, total: Decimal) -> Decimal:
    return (parte / total) if total else Decimal("0")


# ---------------------------------------------------------------------------
# Retenção na fonte
# ---------------------------------------------------------------------------

def _tentar_retencao(
    credito: Decimal, titulos: list[Titulo], cfg: dict
) -> AnaliseValor | None:
    """
    Chegou MENOS porque o tomador retinha imposto na fonte.

    Só se aplica a título de serviço: em nota de produto não há retenção de
    ISS. Essa checagem de tipo é o que impede o motor de "explicar" qualquer
    pagamento parcial de 5% como retenção.

    Quando bate, há uma hipótese forte de retenção. O data pack não contém a
    nota fiscal nem a guia/regras tributárias aplicáveis; por isso a governança
    rebaixa a decisão para confirmação humana antes de tratar o título como
    quitado operacionalmente.
    """
    if len(titulos) != 1:
        return None
    titulo = titulos[0]
    base = titulo.valor
    falta = base - credito
    if falta <= 0:
        return None

    fracao = _frac(falta, base)
    tol = Decimal(str(cfg["retencoes"]["tolerancia_relativa"]))

    for faixa in cfg["retencoes"]["faixas"]:
        tipos = [t.lower() for t in faixa.get("tipos", [])]
        if tipos and titulo.tipo.strip().lower() not in tipos:
            continue
        esperada = Decimal(str(faixa["fracao"]))
        if abs(fracao - esperada) <= tol:
            return AnaliseValor(
                classe=ClasseValor.RETENCAO,
                valor_aplicado=base,            # quita o saldo inteiro
                diferenca=-falta,
                explicacao=(
                    f"Candidato a {faixa['nome']} retido na fonte. A aritmética fecha: "
                    f"{fmt_brl(credito)} recebidos + {fmt_brl(falta)} de diferença = "
                    f"{fmt_brl(base)}. Confirmar nota, regra fiscal e comprovante antes "
                    "de quitar o título ou lançar crédito tributário."
                ),
                evidencias=[
                    Evidencia(
                        regra="valor/retencao_na_fonte",
                        detalhe=(
                            f"Título tipo '{titulo.tipo}'; diferença de {fmt_brl(falta)} "
                            f"equivale a {fracao:.4%} do valor de face, compatível com "
                            f"{faixa['nome']} (tolerância {tol:.2%})"
                        ),
                        campos={
                            "faixa": faixa["nome"],
                            "fracao_observada": str(fracao.quantize(Decimal('0.0001'))),
                            "valor_retido": str(falta),
                        },
                    )
                ],
            )
    return None


# ---------------------------------------------------------------------------
# Mora
# ---------------------------------------------------------------------------

def _tentar_mora(
    credito: Decimal, titulos: list[Titulo], data_credito: date, cfg: dict
) -> AnaliseValor | None:
    """
    Chegou MAIS e a diferença é compatível com multa/juros configurados.

    Confere a aritmética contratual (multa 2% + juros 1%/mês pro rata die) em
    vez de aceitar qualquer excesso. Se o excesso não fecha com a conta, não é
    mora — é exceção, e vai para a analista.
    """
    if len(titulos) != 1:
        return None
    titulo = titulos[0]
    base = titulo.valor
    excesso = credito - base
    if excesso <= 0 or titulo.vencimento is None:
        return None

    dias_atraso = (data_credito - titulo.vencimento).days
    if dias_atraso <= 0:
        return None

    m = cfg["mora"]
    frac_excesso = _frac(excesso, base)
    if frac_excesso > Decimal(str(m["excesso_maximo"])):
        return None

    multa = base * Decimal(str(m["multa_percentual"]))
    juros = base * Decimal(str(m["juros_mes_percentual"])) * Decimal(dias_atraso) / Decimal(30)
    tol = Decimal(str(m["tolerancia_relativa"]))

    cenarios = {
        "multa + juros pro rata": multa + juros,
        "apenas multa contratual": multa,
    }
    for nome, esperado in cenarios.items():
        if base == 0:
            continue
        if abs(excesso - esperado) / base <= tol:
            return AnaliseValor(
                classe=ClasseValor.MORA,
                valor_aplicado=base,
                diferenca=excesso,
                explicacao=(
                    f"Pago com {dias_atraso} dia(s) de atraso "
                    f"(venc. {fmt_data(titulo.vencimento)}, crédito {fmt_data(data_credito)}). "
                    f"A diferença de {fmt_brl(excesso)} é compatível com {nome}. "
                    "Confirmar a regra contratual antes de quitar o título e classificar "
                    "o excedente como receita financeira."
                ),
                evidencias=[
                    Evidencia(
                        regra="valor/mora_por_atraso",
                        detalhe=(
                            f"Excesso de {fmt_brl(excesso)} = {frac_excesso:.4%} do face. "
                            f"Esperado por contrato ({nome}): {fmt_brl(esperado)}. "
                            f"Desvio dentro da tolerância de {tol:.2%}."
                        ),
                        campos={
                            "dias_atraso": dias_atraso,
                            "cenario": nome,
                            "excesso": str(excesso),
                            "esperado": str(esperado.quantize(CENTAVO)),
                        },
                    )
                ],
            )
    return None


# ---------------------------------------------------------------------------
# Classificação principal
# ---------------------------------------------------------------------------

def classificar_valor(
    credito: Decimal,
    titulos: list[Titulo],
    data_credito: date,
    cfg: dict,
) -> AnaliseValor:
    """Classifica a diferença entre o crédito e o conjunto de títulos escolhido."""
    tol = Decimal(str(cfg["tolerancia_centavos"]))
    soma = sum((t.saldo for t in titulos), Decimal("0"))
    diferenca = credito - soma

    # --- bate exatamente
    if abs(diferenca) <= tol:
        if len(titulos) > 1:
            partes = " + ".join(f"{t.documento} {fmt_brl(t.saldo)}" for t in titulos)
            return AnaliseValor(
                classe=ClasseValor.AGREGADO,
                valor_aplicado=soma,
                diferenca=Decimal("0"),
                explicacao=(
                    f"Um crédito quitando {len(titulos)} títulos: {partes} = "
                    f"{fmt_brl(soma)}. Comum quando o franqueado junta produto e "
                    f"royalty num Pix/TED só."
                ),
                evidencias=[
                    Evidencia(
                        regra="valor/agregacao_exata",
                        detalhe=f"Soma dos saldos confere com o crédito ({fmt_brl(credito)})",
                        campos={"titulos": [t.documento for t in titulos]},
                    )
                ],
            )
        titulo = titulos[0]
        parcial_anterior = titulo.saldo < titulo.valor
        return AnaliseValor(
            classe=ClasseValor.EXATO,
            valor_aplicado=soma,
            diferenca=Decimal("0"),
            explicacao=(
                f"Valor confere com o saldo do título"
                + (f" (face {fmt_brl(titulo.valor)}, já havia baixa parcial)"
                   if parcial_anterior else "")
                + "."
            ),
            evidencias=[
                Evidencia(
                    regra="valor/exato",
                    detalhe=f"{fmt_brl(credito)} = {fmt_brl(soma)}",
                    campos={},
                )
            ],
        )

    # --- chegou menos
    if diferenca < 0:
        ret = _tentar_retencao(credito, titulos, cfg)
        if ret:
            return ret

        falta = -diferenca
        titulo = titulos[0] if len(titulos) == 1 else None
        alvo = f"do título {titulo.documento}" if titulo else f"dos {len(titulos)} títulos"
        return AnaliseValor(
            classe=ClasseValor.PARCIAL,
            valor_aplicado=credito,
            diferenca=diferenca,
            quita_titulos=False,
            explicacao=(
                f"Pagamento parcial: {fmt_brl(credito)} de {fmt_brl(soma)} {alvo}. "
                f"Saldo de {fmt_brl(falta)} ({_frac(falta, soma):.1%}) permanece em "
                f"aberto e segue cobrável. Dar baixa total aqui perderia esse saldo."
            ),
            evidencias=[
                Evidencia(
                    regra="valor/pagamento_parcial",
                    detalhe=(
                        f"Crédito cobre {_frac(credito, soma):.1%} do saldo. "
                        f"Nenhuma faixa de retenção explica a diferença"
                        + (f" (título tipo '{titulo.tipo}')" if titulo else "")
                        + "."
                    ),
                    campos={"saldo_remanescente": str(falta)},
                )
            ],
        )

    # --- chegou mais
    mora = _tentar_mora(credito, titulos, data_credito, cfg)
    if mora:
        return mora

    return AnaliseValor(
        classe=ClasseValor.INEXPLICADO,
        valor_aplicado=soma,
        diferenca=diferenca,
        explicacao=(
            f"Crédito de {fmt_brl(credito)} excede o saldo de {fmt_brl(soma)} em "
            f"{fmt_brl(diferenca)} e nenhuma regra (mora, retenção, agregação) "
            f"explica a diferença. Pode ser adiantamento, pagamento de título fora "
            f"desta base ou erro do pagador. Exige decisão humana."
        ),
        evidencias=[
            Evidencia(
                regra="valor/inexplicado",
                detalhe=(
                    f"Excesso de {_frac(diferenca, soma):.2%} não compatível com "
                    f"multa/juros contratuais"
                ),
                campos={"excesso": str(diferenca)},
            )
        ],
    )


# ---------------------------------------------------------------------------
# Agregação: achar o subconjunto de títulos que soma o crédito
# ---------------------------------------------------------------------------

def achar_combinacao(
    credito: Decimal, candidatos: list[Titulo], cfg: dict
) -> list[Titulo] | None:
    """
    Busca o subconjunto de títulos cuja soma bate com o crédito.

    Limitado por configuração (máx. 4 títulos, máx. 14 candidatos) porque isso
    é combinatório. Com 1.900 títulos/mês não dá para ser ingênuo: os
    candidatos já vêm restritos ao MESMO PAGADOR e a uma janela de data, o que
    derruba o espaço de busca de milhares para unidades.

    Preferência: menos títulos primeiro. Um crédito que casa com 2 títulos e
    também com 4 é mais provavelmente os 2.
    """
    tol = Decimal(str(cfg["tolerancia_centavos"]))
    agg = cfg["agregacao"]
    pool = [t for t in candidatos if t.saldo > 0][: int(agg["max_candidatos_avaliados"])]
    if not pool:
        return None

    maximo = min(int(agg["max_titulos_por_credito"]), len(pool))
    for n in range(2, maximo + 1):
        melhor: list[Titulo] | None = None
        for combo in combinations(pool, n):
            soma = sum((t.saldo for t in combo), Decimal("0"))
            if abs(soma - credito) <= tol:
                # Entre combinações do mesmo tamanho, prefere a de vencimentos
                # mais próximos entre si (mais provável de ser um pagamento só).
                if melhor is None:
                    melhor = list(combo)
                else:
                    def espalhamento(ts: list[Titulo]) -> int:
                        ds = [t.vencimento for t in ts if t.vencimento]
                        return (max(ds) - min(ds)).days if len(ds) > 1 else 0
                    if espalhamento(list(combo)) < espalhamento(melhor):
                        melhor = list(combo)
        if melhor:
            return melhor
    return None
