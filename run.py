#!/usr/bin/env python3
"""
CLI do pipeline.

    python run.py                          # roda em data_pack/, grava em out/
    python run.py --sem-ia                 # só camadas determinísticas
    python run.py --dados ./agosto --saida ./out_ago
    python run.py --resumo                 # imprime o resumo e não grava nada

Código de saída 1 quando a conferência de fechamento falha. Isso é
deliberado: em um agendador (cron, Airflow), uma execução que perdeu dinheiro
precisa falhar RUIDOSAMENTE. Ferramenta financeira que erra em silêncio é
abandonada no primeiro mês — e é provavelmente parte do motivo pelo qual a
ferramenta de IA comprada no ano passado está parada.
"""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from src.canonico import Decisao, Severidade
from src.normalizacao import fmt_brl
from src.pipeline import carregar_config, executar

RAIZ = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env", override=True)
except ImportError:
    pass


def main() -> int:
    p = argparse.ArgumentParser(
        description="Conciliação de recebíveis e controles de contas a pagar — Vantara",
    )
    p.add_argument("--dados", default=str(RAIZ / "data_pack"),
                   help="pasta com os arquivos de entrada (default: data_pack/)")
    p.add_argument("--saida", default=str(RAIZ / "out"),
                   help="pasta onde as saídas são gravadas (default: out/)")
    p.add_argument("--config", default=str(RAIZ / "config" / "regras.yaml"),
                   help="arquivo de regras e calibração")
    p.add_argument("--sem-ia", action="store_true",
                   help="desliga a camada de IA; só regras determinísticas")
    p.add_argument("--resumo", action="store_true",
                   help="imprime o resumo no terminal sem gravar arquivos")
    args = p.parse_args()

    cfg = carregar_config(args.config)
    dir_saida = Path(args.saida)

    res, saidas = executar(
        dir_dados=args.dados,
        dir_saida=dir_saida,
        cfg=cfg,
        usar_ia=not args.sem_ia,
    )

    _imprimir(res, saidas, mostrar_arquivos=not args.resumo)

    if not res.metricas["saude"]["conferencia_de_fechamento_ok"]:
        print("\n[ERRO] A conferência de fechamento FALHOU. Não use estas saídas.",
              file=sys.stderr)
        for c in res.metricas["saude"]["checagens"]:
            if not c["passou"]:
                print(f"  - {c['nome']}: esperado {c['esperado']}, obtido {c['obtido']} "
                      f"(diferença {c['diferenca']})", file=sys.stderr)
        return 1
    return 0


def _imprimir(res, saidas, mostrar_arquivos: bool) -> None:
    m = res.metricas
    vol, conc, dec = m["volumetria"], m["conciliacao"], m["decomposicao_do_gap"]
    fechamento = m["fechamento_caixa"]
    L = "─" * 74

    print(f"\n{L}\n  CONCILIAÇÃO VANTARA — execução\n{L}")
    print(f"  Entrada   {vol['titulos_em_aberto_entrada']:>3} títulos  "
          f"{fmt_brl(Decimal(vol['valor_titulos_entrada'])):>14}")
    print(f"            {vol['creditos']:>3} créditos "
          f"{fmt_brl(Decimal(vol['valor_creditos'])):>14}")

    print(f"\n  Conciliados      {conc['creditos_conciliados']:>3}/{vol['creditos']}   "
          f"cobertura {conc['cobertura_de_creditos']*100:5.1f}%   "
          f"vinculado/proposto {fmt_brl(Decimal(conc['valor_aplicado']))}")
    print(f"  Alta confiança   {conc['taxa_automatizavel_valor']*100:5.1f}% do valor "
          f"({conc['por_decisao'].get('AUTO_APLICAR',{}).get('quantidade',0)} propostas; "
          "zero escrita no ERP)")

    print("\n  Identificação do pagador:")
    for tier, d in sorted(conc["por_tier_de_identidade"].items(),
                          key=lambda kv: -float(Decimal(kv[1]["valor"]))):
        print(f"    {tier:<14} {d['quantidade']:>2}  {fmt_brl(Decimal(d['valor'])):>14}  "
              f"conf. média {d['confianca_media']:.2f}")

    print("\n  Decisão:")
    for d in (Decisao.AUTO_APLICAR, Decisao.CONFIRMAR, Decisao.INVESTIGAR):
        info = conc["por_decisao"].get(d.value)
        if info:
            print(f"    {d.value:<14} {info['quantidade']:>2}  "
                  f"{fmt_brl(Decimal(info['valor'])):>14}")

    print(f"\n  Fechamento do caixa:")
    print(f"    Validado para proposta     "
          f"{fmt_brl(Decimal(fechamento['valor_caixa_validado_para_proposta'])):>14} "
          f"({fechamento['percentual_validado_para_proposta']*100:.1f}%)")
    print(f"    Em análise humana          "
          f"{fmt_brl(Decimal(fechamento['valor_caixa_em_analise_humana'])):>14} "
          f"({fechamento['percentual_em_analise_humana']*100:.1f}%)")
    print(f"    Total de créditos          "
          f"{fmt_brl(Decimal(fechamento['valor_caixa_total'])):>14} (100.0%)")
    print("    * Validado para proposta não significa baixa efetivada; o ERP não é escrito.")

    print(f"\n{L}\n  DECOMPOSIÇÃO DO SALDO EM ABERTO\n{L}")
    print(f"    Possível duplicidade em validação "
          f"{fmt_brl(Decimal(dec['em_validacao_possivel_duplicidade'])):>14}")
    print(f"    Saldo de pagamento parcial   "
          f"{fmt_brl(Decimal(dec['saldo_de_pagamento_parcial'])):>14}")
    print(f"    Sem recebimento neste extrato "
          f"{fmt_brl(Decimal(dec['sem_recebimento_identificado_no_extrato'])):>14}")
    print(f"    {'':<28} {'─'*14}")
    print(f"    Total em aberto              "
          f"{fmt_brl(Decimal(dec['total_em_aberto_ao_final'])):>14}")
    print(
        f"\n    → {dec['percentual_sem_recebimento_identificado']*100:.1f}% do saldo aberto "
        "não encontrou recebimento no extrato analisado; isso não prova inadimplência."
    )

    print(f"\n{L}\n  ALERTAS\n{L}")
    for a in res.alertas:
        marca = {Severidade.CRITICO: "\u25c6", Severidade.ALTO: "\u25b2",
                 Severidade.MEDIO: "\u25a0", Severidade.INFO: "\u25cf"}[a.severidade]
        risco = f"  {fmt_brl(a.valor_em_risco)}" if a.valor_em_risco else ""
        print(f"  {marca} [{a.codigo}] {a.titulo_curto}{risco}")
        print(f"       → {a.destinatario}")
    alr = m["alertas"]
    print(f"\n  Perda confirmada e materializada: "
          f"{fmt_brl(Decimal(alr['valor_em_risco_confirmado']))}")
    print(f"  Exposição potencial sob validação: "
          f"{fmt_brl(Decimal(alr['valor_exposicao_potencial']))}")
    print(f"  Exposição sem controle (não verificável com estes dados): "
          f"{fmt_brl(Decimal(alr['valor_sem_controle']))}")
    print(f"  {alr['grupos_de_exposicao']} grupo(s) de risco/controle distintos "
          f"em {alr['total']} alertas — alertas sobre o mesmo dinheiro não são somados.")

    saude = m["saude"]
    print(f"\n{L}\n  SAÚDE DA EXECUÇÃO\n{L}")
    for c in saude["checagens"]:
        print(f"  [{'OK  ' if c['passou'] else 'FALHA'}] {c['nome']}  "
              f"(diferença {c['diferenca']})")
    for alerta in saude["drift"]["alertas"]:
        print(f"  [DRIFT] {alerta}")
    if not saude["drift"]["alertas"]:
        print("  [OK  ] nenhum drift acima da tolerância")

    ia = m["ia"]
    print(f"\n  IA: {'ativa — ' + str(ia['modelo']) if ia['ativa'] else 'desligada (' + str(ia['motivo_desligada']) + ')'}"
          f"  chamadas={ia['chamadas']} cache={ia['acertos_cache']} "
          f"abstenções={ia['abstencoes']} falhas={ia['falhas']}")

    if res.avisos_ingestao:
        print(f"\n  Avisos de ingestão ({len(res.avisos_ingestao)}):")
        for a in res.avisos_ingestao[:8]:
            print(f"    · {a}")

    if mostrar_arquivos:
        print(f"\n{L}\n  SAÍDAS\n{L}")
        for nome, caminho in saidas.items():
            print(f"  {nome:<20} {caminho}")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
