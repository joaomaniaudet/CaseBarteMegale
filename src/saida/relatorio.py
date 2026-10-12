"""
Relatório HTML de uma execução.

Público: a controladoria e o CTO. É a página que abre no fim do pipeline e
responde, sem ninguém abrir CSV, três perguntas:

  1. A execução conservou todos os valores? (conferência, no topo)
  2. Qual é o estado do saldo em aberto? (fato, hipótese e pendência)
  3. O que exige ação humana agora? (alertas críticos, com valor e dono)

Gerado a partir dos dados, não desenhado à mão: o arquivo é produto do código,
e roda de novo em cima do data pack de qualquer mês.
"""

from __future__ import annotations

import html
import json
import base64
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from ..canonico import Decisao, ResultadoExecucao, Severidade
from ..normalizacao import fmt_brl, fmt_data

# Paleta categórica validada (slots 1-3) — ver config e README.
# node scripts/validate_palette.js "#2a78d6,#eb6834,#1baf7a" --mode light --pairs all
CSS = """
:root{
  color-scheme: light;
  --surface-1:#ffffff; --plane:#f5f8fb;
  --ink-1:#18283f; --ink-2:#52657d; --ink-muted:#718096;
  --grid:#dbe4ee; --baseline:#b9c8d8; --ring:rgba(12,40,82,.12);
  --s1:#174579; --s2:#d9a514; --s3:#13a6a6;
  --good:#0d8f83; --warning:#c58a00; --serious:#d46b37; --critical:#c9344b;
}
@media (prefers-color-scheme: dark){
  :root:where(:not([data-theme="light"])){
    color-scheme: dark;
    --surface-1:#1a1a19; --plane:#0d0d0d;
    --ink-1:#f0efec; --ink-2:#c3c2b7; --ink-muted:#898781;
    --grid:#2c2c2a; --baseline:#383835; --ring:rgba(255,255,255,.10);
    --s1:#3987e5; --s2:#d95926; --s3:#199e70;
  }
}
*{box-sizing:border-box}
body{
  margin:0; padding:32px 16px 72px;
  background:var(--plane); color:var(--ink-1);
  font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
}
.wrap{max-width:1080px;margin:0 auto}
.brand{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:14px 18px;
  background:var(--surface-1);border:1px solid var(--ring);border-radius:14px;margin-bottom:22px;
  box-shadow:0 8px 24px rgba(12,40,82,.06)}
.brand img{width:270px;height:54px;object-fit:contain}.brand-copy{text-align:right}
.brand-copy strong{display:block;color:#0c2852;font-size:17px}.brand-copy span{color:var(--ink-muted);font-size:13px}
h1{font-size:25px;margin:0 0 4px;letter-spacing:-.02em}
h2{font-size:15px;margin:36px 0 12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-muted);font-weight:600}
.sub{color:var(--ink-2);margin:0 0 4px}
.card{background:var(--surface-1);border:1px solid var(--ring);border-radius:12px;padding:20px}
.banner{display:flex;gap:12px;align-items:flex-start;padding:14px 18px;border-radius:12px;margin:20px 0 0;
  border:1px solid var(--ring);background:var(--surface-1)}
.banner .dot{width:10px;height:10px;border-radius:50%;flex:0 0 auto;margin-top:6px}
.ok .dot{background:var(--good)} .bad .dot{background:var(--critical)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:16px}
.tile{background:var(--surface-1);border:1px solid var(--ring);border-radius:12px;padding:16px 18px}
.tile .lbl{font-size:12px;color:var(--ink-muted);text-transform:uppercase;letter-spacing:.06em}
.tile .val{font-size:26px;font-weight:650;letter-spacing:-.02em;margin-top:6px}
.tile .note{font-size:12.5px;color:var(--ink-2);margin-top:4px}
.lead{font-size:17px;line-height:1.5;margin:0 0 18px}
.lead strong{font-weight:650}
.bar{display:flex;width:100%;height:46px;gap:2px;margin:10px 0 6px}
.seg{position:relative;border-radius:3px;display:flex;align-items:center;justify-content:center;min-width:2px}
.seg:first-child{border-radius:4px 3px 3px 4px}
.seg:last-child{border-radius:3px 4px 4px 3px}
.seg .tip{position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%);
  background:var(--ink-1);color:var(--surface-1);font-size:12px;line-height:1.35;white-space:nowrap;
  padding:6px 9px;border-radius:7px;opacity:0;pointer-events:none;transition:opacity .12s;z-index:5}
.seg:hover .tip{opacity:1}
.seg .inlbl{font-size:12.5px;font-weight:650;color:#fff;padding:0 8px;text-shadow:0 1px 2px rgba(0,0,0,.35)}
.legend{display:flex;flex-wrap:wrap;gap:16px;margin:12px 0 0;font-size:13px;color:var(--ink-2)}
.legend span.k{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:10px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--grid);vertical-align:top}
th{color:var(--ink-muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
tfoot td{font-weight:650;border-top:1px solid var(--baseline)}
.rank{display:grid;grid-template-columns:150px 1fr 110px;gap:10px;align-items:center;margin:7px 0;font-size:13.5px}
.rank .track{background:var(--grid);border-radius:4px;height:16px;overflow:hidden}
.rank .fill{height:100%;border-radius:4px;background:var(--s1)}
.rank .v{text-align:right;font-variant-numeric:tabular-nums;color:var(--ink-2)}
.alert{border:1px solid var(--ring);border-left:3px solid var(--ink-muted);border-radius:10px;
  background:var(--surface-1);padding:14px 16px;margin:10px 0}
.alert.CRITICO{border-left-color:var(--critical)}
.alert.ALTO{border-left-color:var(--serious)}
.alert.MEDIO{border-left-color:var(--warning)}
.alert .hd{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;margin-bottom:5px}
.alert .cod{font-size:12px;font-weight:700;letter-spacing:.04em}
.alert .nm{font-weight:650}
.alert .risk{margin-left:auto;font-variant-numeric:tabular-nums;font-weight:650}
.alert .who{font-size:12.5px;color:var(--ink-muted);margin-top:7px}
.alert p{margin:0;color:var(--ink-2);font-size:13.5px}
.pill{display:inline-block;font-size:11.5px;font-weight:650;padding:2px 8px;border-radius:999px;
  border:1px solid var(--ring);color:var(--ink-2)}
.ico{font-weight:700;margin-right:4px}
details{margin-top:10px}
summary{cursor:pointer;font-size:13px;color:var(--ink-2)}
pre{overflow-x:auto;font-size:12px;background:var(--plane);padding:12px;border-radius:8px;
  border:1px solid var(--ring);color:var(--ink-2)}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--grid);
  font-size:12.5px;color:var(--ink-muted)}
@media (max-width:620px){
  .rank{grid-template-columns:1fr;gap:3px}
  .rank .v{text-align:left}
  .seg .inlbl{display:none}
}
"""

# Ícone + rótulo (a pill de severidade) para que a cor nunca carregue o
# significado sozinha — requisito de acessibilidade e de impressão em P&B.
# Glifos geométricos em vez de "!!"/"~", que num título longo parecem erro
# de digitação em vez de sinal de severidade.
ICONE_SEV = {
    Severidade.CRITICO: "\u25c6",   # losango cheio
    Severidade.ALTO: "\u25b2",      # triângulo
    Severidade.MEDIO: "\u25a0",     # quadrado
    Severidade.INFO: "\u25cf",      # círculo
}


def _e(x: Any) -> str:
    return html.escape(str(x), quote=True)


def _d(valor: str | Decimal) -> Decimal:
    return Decimal(str(valor))


def _logo_data_uri() -> str:
    logo = Path(__file__).resolve().parents[2] / "assets" / "vantara-concilia-logo.png"
    if not logo.exists():
        return ""
    dados = base64.b64encode(logo.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{dados}"


def gerar_relatorio(
    res: ResultadoExecucao,
    destino: Path,
    titulo_execucao: str = "Vantara — fila auditável de recebíveis",
) -> Path:
    m = res.metricas
    vol, conc = m["volumetria"], m["conciliacao"]
    dec, saude = m["decomposicao_do_gap"], m["saude"]
    alr, ia = m["alertas"], m["ia"]
    fechamento = m["fechamento_caixa"]

    ok = bool(saude["conferencia_de_fechamento_ok"])
    logo_uri = _logo_data_uri()
    brand = (
        f'<div class="brand"><img src="{logo_uri}" alt="Vantara Concilia">'
        f'<div class="brand-copy"><strong>Conciliação inteligente de recebíveis</strong>'
        f'<span>Relatório operacional auditável · sem escrita no ERP</span></div></div>'
        if logo_uri else ""
    )
    partes = [
        ("Possível duplicidade — em validação",
         _d(dec["em_validacao_possivel_duplicidade"]), "var(--s2)",
         "Coincidência forte entre ERPs. Suspender cobrança e validar documentos."),
        ("Saldo de pagamento parcial", _d(dec["saldo_de_pagamento_parcial"]), "var(--s1)",
         "Recebimento parcial legítimo. Cobrar apenas o saldo."),
        ("Sem recebimento no extrato analisado",
         _d(dec["sem_recebimento_identificado_no_extrato"]), "var(--s3)",
         "Validar as outras contas e baixas antes de concluir inadimplência."),
    ]
    total_aberto = _d(dec["total_em_aberto_ao_final"])
    pct_sem_recebimento = float(dec["percentual_sem_recebimento_identificado"])

    # ---- banner de confiança
    banner = f"""
    <div class="banner {'ok' if ok else 'bad'}">
      <div class="dot"></div>
      <div>
        <strong>{'Conferência de fechamento: OK' if ok else 'FALHA NA CONFERÊNCIA DE FECHAMENTO'}</strong><br>
        <span class="sub">{
          'As duas invariantes fecharam ao centavo: todos os valores foram conservados. '
          'Isso não valida a correção semântica de cada vínculo; casos frágeis continuam '
          'dependendo de confirmação humana.'
          if ok else
          'O motor perdeu ou duplicou valor nesta execução. NÃO usar as saídas: '
          'investigar antes. Detalhe na seção de conferência.'
        }</span>
      </div>
    </div>"""

    # ---- tiles
    tiles = [
        ("Créditos conciliados",
         f"{conc['creditos_conciliados']}/{vol['creditos']}",
         f"{fmt_brl(_d(conc['valor_aplicado']))} vinculados/propostos"),
        ("Cobertura dos créditos",
         f"{conc['cobertura_de_creditos']*100:.0f}%",
         f"{conc['creditos_nao_aplicados']} crédito(s) em caixa não aplicado"),
        ("Propostas de alta confiança",
         f"{conc['taxa_automatizavel_valor']*100:.0f}%",
         f"{conc['por_decisao'].get('AUTO_APLICAR',{}).get('quantidade',0)} propostas; zero escrita"),
        ("Exposição potencial",
         fmt_brl(_d(alr["valor_exposicao_potencial"])),
         f"{fmt_brl(_d(alr['valor_em_risco_confirmado']))} de perda confirmada · "
         f"{fmt_brl(_d(alr['valor_sem_controle']))} sem controle · "
         f"{alr['por_severidade'].get('CRITICO',0)} alerta(s) crítico(s)"),
    ]
    html_tiles = "".join(
        f'<div class="tile"><div class="lbl">{_e(l)}</div>'
        f'<div class="val">{_e(v)}</div><div class="note">{_e(n)}</div></div>'
        for l, v, n in tiles
    )

    # ---- barra de composição (stacked, com rótulos diretos + tabela)
    segs, leg, rows = [], [], []
    for nome, valor, cor, nota in partes:
        pct = float(valor / total_aberto * 100) if total_aberto else 0.0
        # 7%: o menor segmento do data pack fica em ~8% e o rótulo cabe.
        # Acima disso ele sumiria justamente no número que mais importa.
        mostra = pct >= 7
        segs.append(
            f'<div class="seg" style="flex:{max(pct,0.6)} 1 0;background:{cor}">'
            f'{f"<span class=inlbl>{fmt_brl(valor)}</span>" if mostra else ""}'
            f'<span class="tip">{_e(nome)}<br>{fmt_brl(valor)} · {pct:.1f}%</span></div>'
        )
        leg.append(f'<div><span class="k" style="background:{cor}"></span>{_e(nome)}</div>')
        rows.append(
            f"<tr><td><span class=\"k\" style=\"display:inline-block;width:10px;height:10px;"
            f"border-radius:3px;background:{cor};margin-right:7px\"></span>{_e(nome)}</td>"
            f"<td class=num>{fmt_brl(valor)}</td><td class=num>{pct:.1f}%</td>"
            f"<td>{_e(nota)}</td></tr>"
        )

    # ---- cobertura por tier (barras ranqueadas, hue único = magnitude)
    tiers = conc["por_tier_de_identidade"]
    maior = max((_d(v["valor"]) for v in tiers.values()), default=Decimal("1")) or Decimal("1")
    nomes_tier = {
        "ID_BANCARIO": "nosso número",
        "CNPJ_TEXTO": "CNPJ no texto",
        "NOME_FORTE": "nome completo",
        "NOME_PARCIAL": "nome parcial",
        "IA": "IA (desempate)",
        "SO_VALOR": "só por valor",
    }
    html_tiers = "".join(
        f'<div class="rank"><div>{_e(nomes_tier.get(k,k))} '
        f'<span class="pill">{v["quantidade"]}</span></div>'
        f'<div class="track"><div class="fill" style="width:{float(_d(v["valor"])/maior*100):.1f}%"></div></div>'
        f'<div class="v">{fmt_brl(_d(v["valor"]))}</div></div>'
        for k, v in sorted(tiers.items(), key=lambda kv: -float(_d(kv[1]["valor"])))
    )

    # ---- alertas
    html_alertas = "".join(
        f'<div class="alert {a.severidade.value}">'
        f'<div class="hd"><span class="cod">{_e(a.codigo)}</span>'
        f'<span class="nm"><span class="ico">{ICONE_SEV[a.severidade]}</span>{_e(a.titulo_curto)}</span>'
        f'<span class="pill">{a.severidade.value}</span>'
        f'<span class="pill">{_e(a.tipo_risco)}</span>'
        f'{f"<span class=risk>{fmt_brl(a.valor_em_risco)}</span>" if a.valor_em_risco else ""}</div>'
        f'<p>{_e(a.descricao)}</p>'
        f'<div class="who">Responsável: {_e(a.destinatario)}</div>'
        f'<details><summary>Evidência ({len(a.evidencias)})</summary>'
        + "".join(f'<p style="margin-top:7px"><code>{_e(ev.regra)}</code> — {_e(ev.detalhe)}</p>'
                  for ev in a.evidencias)
        + '</details></div>'
        for a in res.alertas
    )

    # ---- conferência
    html_conf = "".join(
        f'<tr><td>{"OK" if c["passou"] else "FALHOU"}</td><td>{_e(c["nome"])}</td>'
        f'<td class=num>{fmt_brl(_d(c["esperado"]))}</td>'
        f'<td class=num>{fmt_brl(_d(c["obtido"]))}</td>'
        f'<td class=num>{fmt_brl(_d(c["diferenca"]))}</td>'
        f'<td>{_e(c["descricao"])}</td></tr>'
        for c in saude["checagens"]
    )
    drift = saude["drift"]
    html_drift = (
        "".join(f'<li>{_e(x)}</li>' for x in drift["alertas"])
        if drift["alertas"] else
        "<li>Nenhum desvio acima da tolerância em relação ao baseline.</li>"
    )

    # ---- decisões
    pd_ = conc["por_decisao"]
    html_dec = "".join(
        f'<tr><td>{_e(d)}</td><td class=num>{pd_[d]["quantidade"]}</td>'
        f'<td class=num>{fmt_brl(_d(pd_[d]["valor"]))}</td><td>{_e(desc)}</td></tr>'
        for d, desc in [
            ("AUTO_APLICAR", "Alta confiança. Vai para o arquivo de propostas; não escreve no ERP."),
            ("CONFIRMAR", "Analista confere a evidência e aplica. Nada roda sozinho."),
            ("INVESTIGAR", "Vínculo duvidoso. Nada é aplicado e o título não vai para cobrança."),
        ] if d in pd_
    )

    ia_txt = (
        f"IA ativa ({_e(ia.get('modelo'))}): {ia.get('chamadas',0)} chamada(s), "
        f"{ia.get('acertos_cache',0)} de cache, {ia.get('abstencoes',0)} abstenção(ões), "
        f"{ia.get('falhas',0)} falha(s)."
        if ia.get("ativa") else
        f"IA desligada nesta execução ({_e(ia.get('motivo_desligada') or 'sem motivo registrado')}). "
        f"Os tiers determinísticos rodaram normalmente e os casos ambíguos foram para "
        f"a fila humana com o motivo registrado."
    )
    if ia.get("erros"):
        ia_txt += " Diagnóstico: " + " | ".join(
            f"{e.get('categoria', 'erro')} — {e.get('mensagem', '')}"
            for e in ia["erros"][-5:]
        )

    doc = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(titulo_execucao)}</title><style>{CSS}</style></head><body><div class="wrap">

{brand}

<h1>{_e(titulo_execucao)}</h1>
<p class="sub">Execução de {datetime.now().strftime('%d/%m/%Y %H:%M')} ·
{vol['titulos_em_aberto_entrada']} títulos ({fmt_brl(_d(vol['valor_titulos_entrada']))}) ·
{vol['creditos']} créditos ({fmt_brl(_d(vol['valor_creditos']))})</p>
{banner}
<div class="tiles">{html_tiles}</div>

<h2>Fechamento do caixa</h2>
<div class="tiles">
  <div class="tile"><div class="lbl">Caixa validado para proposta</div>
    <div class="val">{fmt_brl(_d(fechamento['valor_caixa_validado_para_proposta']))}</div>
    <div class="note">{fechamento['percentual_validado_para_proposta']*100:.1f}% ·
      {fechamento['creditos_validados_para_proposta']} crédito(s)</div></div>
  <div class="tile"><div class="lbl">Caixa em análise humana</div>
    <div class="val">{fmt_brl(_d(fechamento['valor_caixa_em_analise_humana']))}</div>
    <div class="note">{fechamento['percentual_em_analise_humana']*100:.1f}% ·
      {fechamento['creditos_em_analise_humana']} crédito(s)</div></div>
  <div class="tile"><div class="lbl">Total de créditos</div>
    <div class="val">{fmt_brl(_d(fechamento['valor_caixa_total']))}</div>
    <div class="note">100% classificado · sem escrita no ERP</div></div>
</div>
<p class="sub">“Validado para proposta” significa que passou pelas travas de alta confiança;
não significa baixa efetivada. O caixa em análise humana inclui confirmações,
investigações e créditos sem título.</p>

<h2>O número que muda a decisão</h2>
<div class="card">
  <p class="lead">Do total de <strong>{fmt_brl(total_aberto)}</strong> em aberto ao final do mês,
  <strong>{fmt_brl(_d(dec['sem_recebimento_identificado_no_extrato']))}
  ({pct_sem_recebimento*100:.0f}%)</strong> não encontrou recebimento no extrato analisado.
  Isso não prova inadimplência: o data pack contém apenas uma das quatro contas bancárias.</p>
  <div class="bar">{''.join(segs)}</div>
  <div class="legend">{''.join(leg)}</div>
  <table>
    <thead><tr><th>Componente</th><th class="num">Valor</th><th class="num">Share</th>
    <th>O que é</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
    <tfoot><tr><td>Total em aberto</td><td class="num">{fmt_brl(total_aberto)}</td>
    <td class="num">100%</td><td></td></tr></tfoot>
  </table>
</div>

<h2>Alertas — exigem ação humana</h2>
<p class="sub" style="margin:0 0 10px;font-size:13px">
{alr['grupos_de_exposicao']} grupo(s) de risco/controle em {alr['total']} alertas.
Alertas que descrevem o mesmo dinheiro — como o boleto reemitido e a conferência
que o deixou passar — contam uma vez só no total.</p>
{html_alertas or '<div class="card">Nenhum alerta nesta execução.</div>'}

<h2>Como cada crédito foi identificado</h2>
<div class="card">
  {html_tiers}
  <p class="sub" style="margin-top:14px;font-size:13px">
  Da evidência mais forte para a mais fraca. Os passes rodam nessa ordem para que
  uma heurística fraca só veja o que a evidência forte não quis — processar por data
  deixaria um depósito não identificado consumir o título errado.</p>
</div>

<h2>O que roda sozinho e o que não roda</h2>
<div class="card">
  <table><thead><tr><th>Decisão</th><th class="num">Qtd</th><th class="num">Valor</th>
  <th>Significado</th></tr></thead><tbody>{html_dec}</tbody></table>
</div>

<h2>Conferência de fechamento</h2>
<div class="card">
  <table><thead><tr><th>Status</th><th>Invariante</th><th class="num">Esperado</th>
  <th class="num">Obtido</th><th class="num">Diferença</th><th>Por quê</th></tr></thead>
  <tbody>{html_conf}</tbody></table>
  <p class="sub" style="margin-top:14px;font-size:13px"><strong>Drift vs baseline:</strong>
  cobertura {drift['cobertura_pp_vs_baseline']:+.1f} p.p. ·
  automatização {drift['automatizacao_pp_vs_baseline']:+.1f} p.p.</p>
  <ul class="sub" style="font-size:13px;margin:6px 0 0">{html_drift}</ul>
  <p class="sub" style="margin-top:14px;font-size:13px"><strong>Limite:</strong>
  a conferência prova conservação aritmética, não que cada pagador foi associado ao
  título correto. Precisão por tier e auditoria amostral são controles adicionais.</p>
</div>

<h2>Onde a IA atuou</h2>
<div class="card"><p class="sub" style="margin:0">{ia_txt}</p>
<details><summary>Métricas completas da execução (JSON)</summary>
<pre>{_e(json.dumps(m, ensure_ascii=False, indent=2))}</pre></details></div>

<footer>
Gerado pelo pipeline a partir do data pack, sem edição manual.
Fontes: TOTVS Protheus, Omie, extrato Itaú e caixa de entrada de contas a pagar.
Nenhuma escrita foi feita em sistema de origem — as baixas saem como arquivo de
proposta para a Vantara aplicar.
</footer>
</div></body></html>"""

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(doc, encoding="utf-8")
    return destino
