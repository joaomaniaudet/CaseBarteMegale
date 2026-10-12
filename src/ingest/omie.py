"""
Adapter Omie — contas a receber da unidade Norte (empresa adquirida).

Formato: ',' como separador, datas ISO, valor com ponto decimal, CNPJ sem
máscara, nome em CAIXA ALTA e com abreviações diferentes do Protheus
('GRAO NOBRE COM LTDA' vs 'Grao Nobre Comercio Ltda').

Sem nosso_numero: a unidade Norte não emite boleto registrado pelo mesmo
banco, então aqui não existe o identificador fácil. É estrutural, não um
defeito do export — e é por isso que a unidade adquirida concentra os casos
difíceis.
"""

from __future__ import annotations

from pathlib import Path

from ..canonico import Titulo
from ..normalizacao import (
    normalizar_cnpj,
    normalizar_documento,
    parse_data,
    parse_valor,
)
from .base import ler_csv, primeiro_campo

FONTE = "omie"

FLAGS_PAGO = {"s", "sim", "y", "yes", "true", "1", "pago", "liquidado"}


class IngestorOmie:
    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)

    def carregar(self) -> tuple[list[Titulo], list[str]]:
        linhas, avisos = ler_csv(self.caminho)
        titulos: list[Titulo] = []

        for linha in linhas:
            flag = (primeiro_campo(linha, "paid_flag", "pago", "liquidado") or "").strip().lower()
            if flag in FLAGS_PAGO:
                continue

            valor = parse_valor(primeiro_campo(linha, "amount", "valor", "value"))
            if valor <= 0:
                avisos.append(
                    f"{self.caminho.name} linha {linha.get('_linha_origem')}: "
                    f"valor inválido/zerado, título ignorado"
                )
                continue

            documento = primeiro_campo(linha, "invoice_ref", "documento", "ref") or ""
            cnpj = normalizar_cnpj(primeiro_campo(linha, "tax_id", "cnpj", "cpf_cnpj"))
            nome = primeiro_campo(linha, "customer_name", "cliente", "nome") or ""

            titulos.append(
                Titulo(
                    id=f"{FONTE}:{documento or linha.get('_linha_origem')}",
                    fonte=FONTE,
                    entidade_id="",
                    nome_original=nome,
                    cnpj=cnpj,
                    documento=documento,
                    documento_normalizado=normalizar_documento(documento),
                    id_bancario=None,       # Omie não traz nosso_numero neste export
                    tipo=(primeiro_campo(linha, "tipo", "type") or "Indefinido").strip(),
                    unidade=primeiro_campo(linha, "unidade", "branch") or "NORTE",
                    emissao=parse_data(primeiro_campo(linha, "issue_date", "emissao")),
                    vencimento=parse_data(primeiro_campo(linha, "due_date", "vencimento")),
                    valor=valor,
                    saldo=valor,
                    bruto=dict(linha),
                )
            )

        return titulos, avisos
