"""Fixtures compartilhadas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.pipeline import carregar_config, executar  # noqa: E402


@pytest.fixture(scope="session")
def cfg() -> dict:
    return carregar_config(RAIZ / "config" / "regras.yaml")


@pytest.fixture(scope="session")
def execucao(cfg, tmp_path_factory):
    """Pipeline completo sobre o data pack real, sem IA (determinístico)."""
    saida = tmp_path_factory.mktemp("out_real")
    res, arquivos = executar(RAIZ / "data_pack", saida, cfg, usar_ia=False)
    return res, arquivos


@pytest.fixture(scope="session")
def execucao_estresse(cfg, tmp_path_factory):
    """Pipeline sobre o data pack adversarial."""
    saida = tmp_path_factory.mktemp("out_estresse")
    res, arquivos = executar(
        RAIZ / "data_pack_estresse",
        saida,
        cfg,
        usar_ia=False,
        arquivos={
            "protheus": "01_contas_a_receber_protheus_estresse.csv",
            "omie": "02_titulos_unidade_norte_omie_estresse.csv",
            "extrato": "03_extrato_bancario_estresse.csv",
            "inbox_ap": "04_caixa_de_entrada_contas_a_pagar_estresse.txt",
        },
    )
    return res, arquivos


def conc_por_valor(res, valor: str):
    """Acha a conciliação de um crédito pelo valor, para asserção caso a caso."""
    from decimal import Decimal
    alvo = Decimal(valor)
    achados = [c for c in res.conciliacoes if c.movimento.valor == alvo]
    assert achados, f"nenhuma conciliação para crédito de {valor}"
    return achados[0]
