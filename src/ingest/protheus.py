"""
Adapter TOTVS Protheus — contas a receber da operação principal.

Formato: ';' como separador, datas dd/mm/aaaa, valor pt-BR com vírgula
decimal, CNPJ com máscara, nome em caixa mista e sem acento.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ..canonico import Titulo
from ..normalizacao import (
    normalizar_cnpj,
    normalizar_documento,
    normalizar_id_bancario,
    parse_data,
    parse_valor,
)
from .base import ler_csv, primeiro_campo

FONTE = "protheus"

# Status que indicam título já liquidado no próprio ERP. O data pack traz tudo
# como 'Aberto', mas em produção vem de tudo — e consumir um título já baixado
# como se estivesse aberto gera cobrança indevida.
STATUS_FECHADOS = {"baixado", "liquidado", "pago", "quitado", "cancelado", "estornado"}


class IngestorProtheus:
    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)

    def carregar(self) -> tuple[list[Titulo], list[str]]:
        linhas, avisos = ler_csv(self.caminho)
        titulos: list[Titulo] = []

        for linha in linhas:
            status = (primeiro_campo(linha, "status", "situacao") or "").strip().lower()
            if status in STATUS_FECHADOS:
                continue

            valor = parse_valor(primeiro_campo(linha, "valor", "valor_titulo", "vl_titulo"))
            if valor <= 0:
                avisos.append(
                    f"{self.caminho.name} linha {linha.get('_linha_origem')}: "
                    f"valor inválido/zerado, título ignorado"
                )
                continue

            documento = primeiro_campo(linha, "documento", "num_titulo", "nf") or ""
            cnpj = normalizar_cnpj(primeiro_campo(linha, "cnpj", "cpf_cnpj", "tax_id"))
            nome = primeiro_campo(linha, "cliente", "nome_cliente", "razao_social") or ""

            titulos.append(
                Titulo(
                    id=f"{FONTE}:{normalizar_documento(documento) or linha.get('_linha_origem')}",
                    fonte=FONTE,
                    entidade_id="",            # preenchido pelo resolvedor de identidade
                    nome_original=nome,
                    cnpj=cnpj,
                    documento=documento,
                    documento_normalizado=normalizar_documento(documento),
                    id_bancario=normalizar_id_bancario(
                        primeiro_campo(linha, "nosso_numero", "nossonumero", "id_boleto")
                    ),
                    tipo=(primeiro_campo(linha, "tipo", "natureza") or "Indefinido").strip(),
                    unidade=primeiro_campo(linha, "unidade", "filial", "cod_filial"),
                    emissao=parse_data(primeiro_campo(linha, "emissao", "dt_emissao")),
                    vencimento=parse_data(primeiro_campo(linha, "vencimento", "dt_vencimento")),
                    valor=valor,
                    saldo=valor,
                    bruto=dict(linha),
                )
            )

        # Duplicidade de documento DENTRO da mesma fonte também existe (relançamento
        # manual). Avisar, não silenciar.
        vistos: dict[str, int] = {}
        for t in titulos:
            vistos[t.id] = vistos.get(t.id, 0) + 1
        for tid, n in vistos.items():
            if n > 1:
                avisos.append(f"{FONTE}: documento repetido na mesma fonte ({tid}), {n} ocorrências")

        return titulos, avisos
