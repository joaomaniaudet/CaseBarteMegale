"""
Saídas operacionais em CSV.

Critério de desenho: a analista da Vantara abre isso no Excel na segunda de
manhã e trabalha de cima para baixo, sem precisar de treinamento e sem
precisar confiar no motor — cada linha carrega a evidência da própria
conclusão.

Escolhas deliberadas:

  * CSV com ';' e vírgula decimal. É pt-BR e abre no Excel com dois cliques.
    A analista não vai converter encoding na segunda de manhã.
  * Coluna 1 é a AÇÃO, não o id. O que ela precisa saber primeiro é o que
    fazer.
  * A fila vem ordenada por decisão e valor: o que exige julgamento primeiro,
    o que já está resolvido por último.
  * O arquivo de propostas é SEPARADO da fila e contém só o que passou nas
    travas. Isso permite operar com Protheus em modo leitura: a Vantara valida
    e aplica manualmente, ou homologa depois um adapter para o importador real.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from ..canonico import (
    Alerta,
    Conciliacao,
    Decisao,
    MovimentoOrfao,
    ResultadoExecucao,
    TituloEmAberto,
)
from ..normalizacao import fmt_brl, fmt_data, formatar_cnpj

ORDEM_DECISAO = {Decisao.INVESTIGAR: 0, Decisao.CONFIRMAR: 1, Decisao.AUTO_APLICAR: 2}


def _escrever(caminho: Path, cabecalho: list[str], linhas: list[list]) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(cabecalho)
        w.writerows(linhas)
    return caminho


def _evidencias(conc: Conciliacao) -> str:
    return " | ".join(str(e) for e in conc.evidencias)


# ---------------------------------------------------------------------------
def gravar_fila_conciliacao(res: ResultadoExecucao, destino: Path) -> Path:
    """A fila de trabalho. O entregável principal para a operação."""
    linhas = []
    for c in sorted(
        res.conciliacoes,
        key=lambda x: (ORDEM_DECISAO[x.decisao], -float(x.movimento.valor)),
    ):
        titulo = c.titulos[0] if c.titulos else None
        linhas.append([
            c.acao_sugerida,
            c.decisao.value,
            f"{c.confianca:.2f}",
            fmt_data(c.movimento.data),
            c.movimento.historico,
            fmt_brl(c.movimento.valor),
            " + ".join(t.documento for t in c.titulos),
            " + ".join(t.fonte for t in c.titulos),
            titulo.nome_original if titulo else "",
            formatar_cnpj(titulo.cnpj) if titulo and titulo.cnpj else "",
            fmt_brl(c.valor_titulos),
            fmt_brl(c.valor_aplicado),
            fmt_brl(c.diferenca) if c.diferenca else "",
            c.classe_valor.value,
            c.tier.value,
            c.observacao_analista,
            _evidencias(c),
            c.movimento.id,
        ])
    return _escrever(
        destino,
        [
            "acao_sugerida", "decisao", "confianca", "data_credito", "historico_banco",
            "valor_credito", "titulos", "sistema_origem", "cliente", "cnpj",
            "valor_titulos", "valor_a_aplicar", "diferenca", "classe_da_diferenca",
            "como_foi_identificado", "atencao", "evidencia", "id_movimento",
        ],
        linhas,
    )


# ---------------------------------------------------------------------------
def gravar_baixas_propostas(res: ResultadoExecucao, destino: Path) -> Path:
    """
    Arquivo genérico de propostas de baixa.

    Só entra o que passou em TODAS as travas de automação. Com o Protheus em
    modo leitura nos primeiros 90 dias, este arquivo é a fronteira: a Barte
    propõe, a Vantara valida e aplica. Nenhuma escrita parte daqui e o layout
    ainda precisa ser adaptado e homologado antes de uma importação no Protheus.

    O layout é genérico de propósito (um campo por informação, sem posicional)
    para ser adaptado ao importador do Protheus na implantação — e para servir
    a um ERP diferente na próxima conta.
    """
    linhas = []
    for c in res.conciliacoes:
        if c.decisao != Decisao.AUTO_APLICAR:
            continue
        for t in c.titulos:
            valor = min(t.valor, c.valor_aplicado) if len(c.titulos) == 1 else t.valor
            linhas.append([
                t.fonte,
                t.documento,
                t.bruto.get("nosso_numero", t.id_bancario or ""),
                formatar_cnpj(t.cnpj) if t.cnpj else "",
                t.nome_original,
                fmt_data(t.vencimento),
                fmt_brl(t.valor),
                fmt_brl(valor),
                "PARCIAL" if valor < t.valor else "TOTAL",
                fmt_data(c.movimento.data),
                c.movimento.conta,
                c.movimento.bruto.get("documento", c.movimento.documento or ""),
                fmt_brl(c.movimento.valor),
                c.classe_valor.value,
                fmt_brl(-c.diferenca) if c.diferenca < 0 else "",
                fmt_brl(c.diferenca) if c.diferenca > 0 else "",
                f"{c.confianca:.2f}",
                c.tier.value,
                _evidencias(c),
            ])
    return _escrever(
        destino,
        [
            "sistema_origem", "documento", "nosso_numero", "cnpj", "cliente",
            "vencimento", "valor_titulo", "valor_baixa", "tipo_baixa",
            "data_credito", "conta_bancaria", "doc_bancario", "valor_credito",
            "classe_diferenca", "valor_retencao", "valor_mora",
            "confianca", "tier_identidade", "evidencia",
        ],
        linhas,
    )


# ---------------------------------------------------------------------------
def gravar_titulos_em_aberto(res: ResultadoExecucao, destino: Path) -> Path:
    """
    Títulos que sobraram, com a coluna que mais importa: `pode_cobrar`.

    É esta coluna que impede o time de cobrança de ligar para um franqueado em
    dia — o problema que o Head de Operações de Franquias levou para a reunião.
    """
    linhas = []
    for e in res.em_aberto:
        t = e.titulo
        linhas.append([
            "SIM" if e.e_cobravel else "NAO",
            e.severidade.value,
            t.fonte,
            t.documento,
            t.nome_original,
            formatar_cnpj(t.cnpj) if t.cnpj else "",
            t.unidade or "",
            t.tipo,
            fmt_data(t.vencimento),
            fmt_brl(t.valor),
            fmt_brl(t.saldo),
            fmt_brl(t.valor - t.saldo) if t.saldo < t.valor else "",
            e.motivo,
        ])
    return _escrever(
        destino,
        [
            "pode_cobrar", "severidade", "sistema_origem", "documento", "cliente",
            "cnpj", "unidade", "tipo", "vencimento", "valor_face", "saldo_em_aberto",
            "ja_recebido", "motivo",
        ],
        linhas,
    )


# ---------------------------------------------------------------------------
def gravar_caixa_nao_aplicado(res: ResultadoExecucao, destino: Path) -> Path:
    """Créditos que entraram e não acharam título."""
    linhas = []
    for o in res.orfaos:
        linhas.append([
            fmt_data(o.movimento.data),
            o.movimento.historico,
            fmt_brl(o.movimento.valor),
            o.entidade_provavel or "não identificado",
            o.motivo,
            " | ".join(o.candidatos_proximos),
            o.movimento.conta,
            o.movimento.id,
        ])
    return _escrever(
        destino,
        [
            "data", "historico_banco", "valor", "pagador_provavel", "motivo",
            "titulos_de_valor_proximo", "conta", "id_movimento",
        ],
        linhas,
    )


# ---------------------------------------------------------------------------
def gravar_alertas(alertas: list[Alerta], destino: Path) -> Path:
    """
    Alertas vão para destinatários DIFERENTES da fila de conciliação.

    Possível duplicidade é problema de cadastro/TI. Risco de pagamento duplicado é contas a
    pagar. Mandar tudo para a mesma fila de "exceções de conciliação" é
    exatamente o que enterra esses casos hoje: eles ficam na planilha de quem
    não tem mandato para resolvê-los.
    """
    linhas = []
    for a in alertas:
        linhas.append([
            a.codigo,
            a.severidade.value,
            a.titulo_curto,
            a.tipo_risco,
            fmt_brl(a.valor_em_risco) if a.valor_em_risco else "",
            a.destinatario,
            a.descricao,
            " | ".join(str(e) for e in a.evidencias),
            " || ".join(a.referencias),
        ])
    return _escrever(
        destino,
        [
            "codigo", "severidade", "achado", "natureza_do_risco",
            "valor_em_risco", "responsavel", "descricao", "evidencia", "referencias",
        ],
        linhas,
    )
