"""
Detector de título fantasma.

O achado mais importante do data pack, e o que nenhum motor de conciliação
encontra:

    Protheus  NF 104580      Grao Nobre Comercio Ltda  31.250,00  venc 20/07
    Omie      FAT-2026-0331  GRAO NOBRE COM LTDA       31.250,00  venc 20/07
    Extrato   21/07          LIQUIDACAO 000012345740   31.250,00

Mesma entidade, mesmo valor e vencimento, dois ERPs, UM pagamento. É um forte
indício de duplicidade, mas os dados não provam que os documentos têm a mesma
causa. O comportamento seguro é suspender a cobrança e validar.

Por que isso roda ANTES do matching: se eu conciliar primeiro, o motor acha o
pagamento, quita um dos títulos e manda o outro para "inadimplência". A
exceção vira silenciosa, o DSO sobe e ninguém descobre. Rodar antes transforma
um falso inadimplente em um alerta de cadastro com dono.

E o destinatário é diferente de propósito: isso NÃO vai para a fila da
analista de conciliação, vai para cadastro/TI. Tratar tudo como "exceção de
conciliação" é o que enterra esse caso hoje.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from ..canonico import Alerta, Evidencia, Severidade, Titulo
from ..identidade.resolver import ResolvedorEntidades
from ..normalizacao import fmt_brl, fmt_data


def _dias(a: date | None, b: date | None) -> int | None:
    if a is None or b is None:
        return None
    return abs((a - b).days)


def detectar_titulos_fantasma(
    titulos: list[Titulo],
    resolvedor: ResolvedorEntidades,
    folga_vencimento_dias: int = 3,
    exigir_fontes_distintas: bool = True,
) -> tuple[list[Alerta], set[str]]:
    """
    Devolve (alertas, ids de títulos marcados como fantasma).

    Chave de colisão: mesma entidade + mesmo valor + vencimento dentro da
    folga. Deliberadamente NÃO uso o número do documento, porque é justamente
    ele que difere entre os sistemas ('NF 104580' vs 'FAT-2026-0331') — usar o
    documento como chave é o que faz o ERP não ver a duplicidade.

    Risco assumido: dois títulos legítimos de mesmo valor e vencimento para o
    mesmo franqueado (ex. duas parcelas iguais) seriam marcados. Por isso o
    alerta é SUSPEITA com evidência, não baixa automática — e por isso exijo
    fontes distintas por padrão, o que elimina o caso de parcelas do mesmo ERP.
    """
    alertas: list[Alerta] = []
    marcados: set[str] = set()

    grupos: dict[tuple[str, Decimal], list[Titulo]] = defaultdict(list)
    for t in titulos:
        grupos[(t.entidade_id, t.valor)].append(t)

    for (entidade_id, valor), grupo in grupos.items():
        if len(grupo) < 2:
            continue

        # Dentro do grupo, agrupa por vencimento próximo
        grupo = sorted(grupo, key=lambda t: (t.vencimento or date.min, t.fonte))
        usados: set[int] = set()
        for i, base in enumerate(grupo):
            if i in usados:
                continue
            cluster = [base]
            for j in range(i + 1, len(grupo)):
                if j in usados:
                    continue
                d = _dias(base.vencimento, grupo[j].vencimento)
                if d is not None and d <= folga_vencimento_dias:
                    cluster.append(grupo[j])
                    usados.add(j)
            if len(cluster) < 2:
                continue

            fontes = {t.fonte for t in cluster}
            if exigir_fontes_distintas and len(fontes) < 2:
                continue

            usados.add(i)
            for t in cluster:
                marcados.add(t.id)

            refs = [f"{t.fonte}/{t.documento} ({fmt_brl(t.valor)}, venc {fmt_data(t.vencimento)})"
                    for t in cluster]
            valor_em_risco = valor * (len(cluster) - 1)

            alertas.append(
                Alerta(
                    codigo="CAD-001",
                    severidade=Severidade.CRITICO,
                    titulo_curto="Possível duplicidade de título entre ERPs",
                    descricao=(
                        f"{resolvedor.descrever(entidade_id)} tem {len(cluster)} títulos "
                        f"de {fmt_brl(valor)} com o mesmo vencimento em sistemas diferentes "
                        f"({', '.join(sorted(fontes))}). Isso é um forte indício de "
                        f"duplicidade, não prova de que os documentos tenham a mesma causa. "
                        f"Há {fmt_brl(valor_em_risco)} sob validação. SUSPENDER COBRANÇA "
                        f"por até 48h e confirmar documento de origem, pedido/contrato e "
                        f"histórico do cadastro antes de baixar ou cobrar."
                    ),
                    valor_em_risco=valor_em_risco,
                    destinatario="Cadastro / TI (integração de empresas adquiridas)",
                    grupo_risco=f"fantasma:{entidade_id}:{valor}",
                    tipo_risco="potencial",
                    evidencias=[
                        Evidencia(
                            regra="fantasma/colisao_entidade_valor_vencimento",
                            detalhe=(
                                "Coincidência de entidade + valor + vencimento na folga de "
                                f"{folga_vencimento_dias} dia(s), em fontes distintas. "
                                "Número de documento difere entre os sistemas, que é "
                                "exatamente por isso que o ERP não enxerga a duplicidade."
                            ),
                            campos={
                                "entidade": entidade_id,
                                "valor": str(valor),
                                "fontes": sorted(fontes),
                                "documentos": [t.documento for t in cluster],
                            },
                        )
                    ],
                    referencias=refs,
                )
            )

    return alertas, marcados


def detectar_entidades_divergentes(resolvedor: ResolvedorEntidades) -> list[Alerta]:
    """
    Mesmo CNPJ, razão social escrita de formas diferentes entre sistemas.

    Severidade menor que o fantasma porque não gera cobrança indevida — mas
    gera cegueira: ninguém consegue somar a exposição do franqueado.
    """
    alertas: list[Alerta] = []
    for ent, variantes in resolvedor.entidades_com_nomes_divergentes():
        alertas.append(
            Alerta(
                codigo="CAD-002",
                severidade=Severidade.MEDIO,
                titulo_curto=(
                    f"Mesma entidade com razões sociais divergentes: "
                    f"{ent.nome_canonico}"
                ),
                descricao=(
                    f"O CNPJ {ent.cnpj} aparece com {len(variantes)} grafias diferentes "
                    f"({' | '.join(variantes)}) nas fontes {', '.join(ent.fontes)}. "
                    f"Nenhum relatório atual consegue somar a exposição total deste "
                    f"franqueado, porque para os sistemas são dois clientes."
                ),
                valor_em_risco=Decimal("0"),
                destinatario="Cadastro / TI",
                grupo_risco=f"divergencia:{ent.id}",
                tipo_risco="indeterminado",
                evidencias=[
                    Evidencia(
                        regra="identidade/divergencia_de_nome_mesmo_cnpj",
                        detalhe="CNPJ normalizado idêntico, chave canônica de nome distinta",
                        campos={"cnpj": ent.cnpj, "variantes": variantes},
                    )
                ],
                referencias=list(variantes),
            )
        )
    return alertas
