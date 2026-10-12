"""
Adapter extrato Itaú.

Formato: ';', datas dd/mm/aaaa, valor pt-BR, histórico em texto livre
TRUNCADO em ~32 caracteres, campo documento preenchido só quando a liquidação
veio por boleto registrado.

O histórico é a única pista de pagador em 11 das 16 entradas de crédito deste
extrato. É aí que mora o problema.
"""

from __future__ import annotations

from pathlib import Path

from ..canonico import MovimentoBancario
from ..normalizacao import normalizar_id_bancario, parse_data, parse_valor
from .base import ler_csv, primeiro_campo

FONTE = "itau"


class IngestorExtratoItau:
    def __init__(self, caminho: str | Path, conta: str = "ITAU-COBRANCA-PRINCIPAL"):
        self.caminho = Path(caminho)
        self.conta = conta

    def carregar(self) -> tuple[list[MovimentoBancario], list[str]]:
        linhas, avisos = ler_csv(self.caminho)
        movimentos: list[MovimentoBancario] = []

        for i, linha in enumerate(linhas, start=1):
            valor = parse_valor(primeiro_campo(linha, "valor", "vl_lancamento"))
            data = parse_data(primeiro_campo(linha, "data", "dt_lancamento", "data_mov"))
            if data is None:
                avisos.append(
                    f"{self.caminho.name} linha {linha.get('_linha_origem')}: "
                    f"data ilegível, movimento ignorado"
                )
                continue

            tipo = (primeiro_campo(linha, "tipo", "d_c", "natureza") or "").strip().upper()
            if tipo not in ("C", "D"):
                # Alguns extratos usam sinal no valor em vez de coluna de tipo.
                tipo = "D" if valor < 0 else "C"

            movimentos.append(
                MovimentoBancario(
                    id=f"{self.conta}:{data.isoformat()}:{i:03d}",
                    data=data,
                    historico=primeiro_campo(linha, "historico", "descricao", "memo") or "",
                    documento=normalizar_id_bancario(
                        primeiro_campo(linha, "documento", "doc", "nosso_numero")
                    ),
                    valor=abs(valor),
                    tipo=tipo,
                    conta=self.conta,
                    bruto=dict(linha),
                )
            )

        return movimentos, avisos
