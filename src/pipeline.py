"""
Orquestração.

A ordem aqui não é arbitrária. Cada etapa só pode rodar depois da anterior:

  1. INGESTÃO           — tudo vira schema canônico; a bagunça morre aqui.
  2. IDENTIDADE         — entidades unificadas entre ERPs.
  3. FANTASMA           — antes do matching, para que um título duplicado não
                          seja silenciosamente "resolvido" e o gêmeo vá para
                          inadimplência sem ninguém saber.
  4. CONCILIAÇÃO AR     — cascata de evidência forte para fraca.
  5. CONTAS A PAGAR     — independente de AR; usa os débitos do mesmo extrato.
  6. CONFERÊNCIA        — invariantes. Falha aqui aborta a execução.
  7. SAÍDAS             — CSVs operacionais + relatório.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml

from .ap.duplicidade import analisar_contas_a_pagar
from .ar.matcher import MotorConciliacaoAR
from .canonico import ResultadoExecucao
from .ia.cliente import ClienteIA
from .identidade.fantasma import detectar_entidades_divergentes, detectar_titulos_fantasma
from .identidade.resolver import ResolvedorEntidades
from .ingest import (
    IngestorExtratoItau,
    IngestorInboxAP,
    IngestorOmie,
    IngestorProtheus,
)
from .normalizacao import NormalizadorNome
from .observabilidade import conferir_fechamento, montar_metricas
from .saida.planilhas import (
    gravar_alertas,
    gravar_baixas_propostas,
    gravar_caixa_nao_aplicado,
    gravar_fila_conciliacao,
    gravar_titulos_em_aberto,
)
from .saida.relatorio import gerar_relatorio

ARQUIVOS_PADRAO = {
    "protheus": "01_contas_a_receber_protheus_jul2026.csv",
    "omie": "02_titulos_unidade_norte_omie_jul2026.csv",
    "extrato": "03_extrato_bancario_jul2026.csv",
    "inbox_ap": "04_caixa_de_entrada_contas_a_pagar.txt",
}


def carregar_config(caminho: str | Path) -> dict:
    return yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))


def _resolver_arquivos(dir_dados: Path, mapa: dict[str, str]) -> dict[str, Path | None]:
    """
    Resolve cada fonte por nome exato ou por prefixo numérico.

    Aceitar prefixo importa: na implantação, os arquivos chegam com o mês no
    nome (`01_contas_a_receber_protheus_ago2026.csv`) e ninguém deveria ter que
    renomear nada para o pipeline rodar.
    """
    saida: dict[str, Path | None] = {}
    for chave, nome in mapa.items():
        exato = dir_dados / nome
        if exato.exists():
            saida[chave] = exato
            continue
        prefixo = nome.split("_")[0]
        candidatos = sorted(dir_dados.glob(f"{prefixo}_*"))
        saida[chave] = candidatos[0] if candidatos else None
    return saida


def executar(
    dir_dados: str | Path,
    dir_saida: str | Path,
    cfg: dict,
    usar_ia: bool = True,
    arquivos: dict[str, str] | None = None,
) -> tuple[ResultadoExecucao, dict[str, Path]]:
    dir_dados, dir_saida = Path(dir_dados), Path(dir_saida)
    res = ResultadoExecucao()
    fontes = _resolver_arquivos(dir_dados, arquivos or ARQUIVOS_PADRAO)

    # ---------------------------------------------------------------- 1
    titulos = []
    for chave, Ingestor in (("protheus", IngestorProtheus), ("omie", IngestorOmie)):
        caminho = fontes.get(chave)
        if not caminho:
            res.avisos_ingestao.append(f"fonte '{chave}' não encontrada em {dir_dados}")
            continue
        novos, avisos = Ingestor(caminho).carregar()
        titulos.extend(novos)
        res.avisos_ingestao.extend(avisos)

    movimentos = []
    if fontes.get("extrato"):
        movimentos, avisos = IngestorExtratoItau(fontes["extrato"]).carregar()
        res.avisos_ingestao.extend(avisos)
    else:
        res.avisos_ingestao.append("extrato bancário não encontrado — sem conciliação")

    cobrancas, aprovacoes = [], []
    if fontes.get("inbox_ap"):
        cobrancas, aprovacoes, avisos = IngestorInboxAP(fontes["inbox_ap"]).carregar()
        res.avisos_ingestao.extend(avisos)

    res.titulos, res.movimentos = titulos, movimentos
    valor_inicial = sum((t.valor for t in titulos), Decimal("0"))

    # ---------------------------------------------------------------- 2
    norm = NormalizadorNome(
        stopwords=cfg["nome"]["stopwords"],
        ruido_historico=cfg["nome"]["ruido_historico"],
        ultimo_token_prefixo=cfg["nome"]["ultimo_token_casa_por_prefixo"],
        prefixo_minimo=int(cfg["nome"]["prefixo_minimo"]),
    )
    resolvedor = ResolvedorEntidades(norm)
    res.entidades = resolvedor.construir(titulos)

    # ---------------------------------------------------------------- 3
    alertas_fantasma, ids_fantasma = detectar_titulos_fantasma(
        titulos, resolvedor,
        folga_vencimento_dias=int(cfg["fantasma"]["folga_vencimento_dias"]),
        exigir_fontes_distintas=bool(cfg["fantasma"]["exigir_fontes_distintas"]),
    )
    res.alertas.extend(alertas_fantasma)
    res.alertas.extend(detectar_entidades_divergentes(resolvedor))

    # ---------------------------------------------------------------- 4
    ia = ClienteIA(cfg, habilitada=usar_ia, dir_cache=dir_saida / ".cache_ia")
    if cobrancas and ia.ativa:
        _enriquecer_com_ia(cobrancas, ia)

    motor = MotorConciliacaoAR(cfg, resolvedor, norm, ia)
    ar = motor.conciliar(movimentos, titulos, ids_fantasma)
    res.conciliacoes, res.orfaos, res.em_aberto = ar.conciliacoes, ar.orfaos, ar.em_aberto

    # ---------------------------------------------------------------- 5
    ap = analisar_contas_a_pagar(cobrancas, movimentos, aprovacoes, cfg)
    res.alertas.extend(ap.alertas)

    # ---------------------------------------------------------------- 6
    creditos = [m for m in movimentos if m.is_credito]
    conferencia = conferir_fechamento(
        valor_inicial, res.conciliacoes, res.em_aberto, res.orfaos, creditos
    )
    res.metricas = montar_metricas(
        titulos=titulos,
        titulos_valor_inicial=valor_inicial,
        movimentos=movimentos,
        conciliacoes=res.conciliacoes,
        orfaos=res.orfaos,
        em_aberto=res.em_aberto,
        alertas=res.alertas,
        trilha_passes=ar.trilha_passes,
        conferencia=conferencia,
        resumo_ia=ia.resumo(),
        cfg=cfg,
    )
    res.metricas["avisos_de_ingestao"] = res.avisos_ingestao

    # ---------------------------------------------------------------- 7
    dir_saida.mkdir(parents=True, exist_ok=True)
    saidas = {
        "fila_conciliacao": gravar_fila_conciliacao(res, dir_saida / "01_fila_conciliacao.csv"),
        "baixas_propostas": gravar_baixas_propostas(res, dir_saida / "02_baixas_propostas.csv"),
        "titulos_em_aberto": gravar_titulos_em_aberto(res, dir_saida / "03_titulos_em_aberto.csv"),
        "caixa_nao_aplicado": gravar_caixa_nao_aplicado(
            res, dir_saida / "04_caixa_nao_aplicado.csv"),
        "alertas": gravar_alertas(res.alertas, dir_saida / "05_alertas.csv"),
        "relatorio": gerar_relatorio(res, dir_saida / "relatorio.html"),
    }
    import json
    (dir_saida / "metricas.json").write_text(
        json.dumps(res.metricas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    saidas["metricas"] = dir_saida / "metricas.json"
    return res, saidas


def _enriquecer_com_ia(cobrancas, ia: ClienteIA) -> None:
    """
    Camada 2 da extração de contas a pagar.

    A IA sobrescreve o que a regra achou APENAS quando acha algo que a regra
    não achou. Nunca o contrário: valor e número de documento extraídos por
    regex são mais confiáveis que os de um modelo, e um valor alucinado aqui
    vira pagamento errado.
    """
    for c in cobrancas:
        dados = ia.enriquecer_cobranca_ap({
            "remetente": c.remetente,
            "recebido_em": str(c.recebido_em),
            "assunto": c.assunto,
            "corpo": c.corpo,
        })
        if not dados:
            continue
        usou = False
        if not c.entrega_parcial and dados.get("entrega_parcial"):
            c.entrega_parcial = str(dados["entrega_parcial"])
            usou = True
        if dados.get("e_reemissao_de_cobranca_anterior") and not c.e_reemissao:
            c.e_reemissao = True
            usou = True
        nome = dados.get("fornecedor")
        if nome and isinstance(nome, str) and len(nome) > 2:
            c.fornecedor = nome.strip()
            usou = True
        risco = dados.get("observacoes_de_risco")
        if risco:
            c.notas_extracao.append(f"IA: {risco}")
            usou = True
        if usou:
            c.extraido_por = "ia"
