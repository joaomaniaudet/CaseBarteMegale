"""
Demo interativa — Vantara Concilia.

Apresentação socrática: cada aba faz uma pergunta, mostra o problema,
e revela como a solução resolve — sempre com o argumento de escala.

    streamlit run demo.py
"""

import base64
import sys
import tempfile
import time
from decimal import Decimal
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=True)
except ImportError:
    pass

st.set_page_config(
    page_title="Vantara Concilia — Demo",
    page_icon=str(ROOT / "assets" / "vantara-concilia-logo.png"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Identidade visual Vantara Concilia
st.markdown("""
<style>
    :root {
        --vantara-navy: #0c2852;
        --vantara-blue: #174579;
        --vantara-teal: #13a6a6;
        --vantara-ink: #18283f;
        --vantara-muted: #64748b;
        --vantara-line: #dbe4ee;
        --vantara-bg: #f5f8fb;
    }
    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    [data-testid="stAppViewContainer"] { background: var(--vantara-bg); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1480px; padding-top: 2rem; padding-bottom: 3rem; }
    .brand-header {
        display: flex; align-items: center; justify-content: space-between; gap: 24px;
        background: #ffffff; border: 1px solid var(--vantara-line); border-radius: 18px;
        padding: 16px 24px; margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(12, 40, 82, .06);
    }
    .brand-header img { width: 278px; height: 54px; object-fit: contain; object-position: center; }
    .brand-copy { text-align: right; }
    .brand-name { color: var(--vantara-navy); font-size: 1.15rem; font-weight: 750; letter-spacing: -.02em; }
    .brand-subtitle { color: var(--vantara-muted); font-size: .86rem; margin-top: 4px; }
    .environment-badge {
        display: inline-block; margin-top: 8px; padding: 4px 10px; border-radius: 999px;
        color: #087f7f; background: #e3f7f6; font-size: .72rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: .06em;
    }
    .workflow {
        display: flex; align-items: center; gap: 10px; margin: 0 0 24px;
        color: var(--vantara-muted); font-size: .86rem; font-weight: 650;
    }
    .workflow-step {
        display: flex; align-items: center; gap: 8px; padding: 9px 13px;
        border: 1px solid var(--vantara-line); border-radius: 999px; background: #fff;
    }
    .workflow-step.active { color: var(--vantara-navy); border-color: #8ccfce; background: #ebfaf7; }
    .workflow-step.done { color: #087f7f; border-color: #b8e4dd; background: #f2fbf9; }
    .workflow-number {
        display: inline-grid; place-items: center; width: 22px; height: 22px;
        border-radius: 50%; background: #e8eef5; color: var(--vantara-blue); font-size: .75rem;
    }
    .workflow-step.active .workflow-number { background: var(--vantara-teal); color: #fff; }
    .workflow-step.done .workflow-number { background: #80cfc4; color: #fff; }
    .workflow-arrow { color: #9aaabd; font-size: 1.1rem; }
    h1, h2, h3 { color: var(--vantara-ink); letter-spacing: -.025em; }
    h1 { font-weight: 780; }
    h2, h3 { font-weight: 720; }
    .stCaption, [data-testid="stCaptionContainer"] { color: var(--vantara-muted); }
    .stMetric > div {
        background: #ffffff; padding: 16px; border-radius: 14px;
        border: 1px solid var(--vantara-line); box-shadow: 0 3px 12px rgba(12, 40, 82, .04);
    }
    [data-testid="stMetricLabel"] { color: var(--vantara-muted); font-weight: 650; }
    [data-testid="stMetricValue"] { color: var(--vantara-navy); font-weight: 780; }
    div[data-testid="stTabs"] { border-bottom: 1px solid var(--vantara-line); }
    div[data-testid="stTabs"] button { color: var(--vantara-muted); font-size: .92rem; font-weight: 650; }
    div[data-testid="stTabs"] button[aria-selected="true"] { color: var(--vantara-navy); }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--vantara-teal); height: 3px; }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: var(--vantara-navy); border-color: var(--vantara-navy); border-radius: 9px;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover { background: var(--vantara-blue); border-color: var(--vantara-blue); }
    div[data-testid="stFileUploader"] section { background: #ffffff; border: 1px dashed #9fb3c8; border-radius: 12px; }
    div[data-testid="stExpander"] { background: #ffffff; border: 1px solid var(--vantara-line); border-radius: 12px; }
    [data-testid="stDataFrame"] { border: 1px solid var(--vantara-line); border-radius: 12px; overflow: hidden; }
    hr { border-color: var(--vantara-line); }
    .highlight-box {
        background: #fff8df; padding: 16px; border-radius: 12px;
        border: 1px solid #f0d47a; border-left: 4px solid #d9a514; margin: 10px 0;
    }
    .danger-box {
        background: #fff1f2; padding: 16px; border-radius: 12px;
        border: 1px solid #f4b8bf; border-left: 4px solid #c9344b; margin: 10px 0;
    }
    .success-box {
        background: #ebfaf7; padding: 16px; border-radius: 12px;
        border: 1px solid #a9e0d5; border-left: 4px solid var(--vantara-teal); margin: 10px 0;
    }
    .scale-box {
        background: #edf5ff; padding: 16px; border-radius: 12px;
        border: 1px solid #b9d5f4; border-left: 4px solid var(--vantara-blue); margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar_pipeline():
    import yaml
    from src.pipeline import executar
    cfg = yaml.safe_load((ROOT / "config" / "regras.yaml").read_text("utf-8"))
    inicio = time.perf_counter()
    res, _ = executar(
        ROOT / "data_pack", ROOT / "out_demo", cfg, usar_ia=False,
        arquivos={
            "protheus": "01_contas_a_receber_protheus_jul2026.csv",
            "omie": "02_titulos_unidade_norte_omie_jul2026.csv",
            "extrato": "03_extrato_bancario_jul2026.csv",
            "inbox_ap": "04_caixa_de_entrada_contas_a_pagar.txt",
        },
    )
    tempo = time.perf_counter() - inicio
    # Usa exatamente as métricas da mesma execução que alimenta a demo.
    # Ler out/metricas.json separadamente permitia que uma execução antiga
    # ficasse em cache e quebrasse a interface quando o schema evoluía.
    return res, tempo, res.metricas


def fmt(v):
    """Formata Decimal como BRL."""
    d = Decimal(str(v)).quantize(Decimal("0.01"))
    inteiro, _, dec = f"{abs(d):.2f}".partition(".")
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    sinal = "-" if d < 0 else ""
    return f"R$ {sinal}{'.'.join(grupos)},{dec}"


def calcular_fechamento_interativo(res, decisoes_usuario):
    """Calcula o fechamento atual incluindo as decisões da analista."""
    auto = [c for c in res.conciliacoes if c.decisao.value == "AUTO_APLICAR"]
    confirmar = [c for c in res.conciliacoes if c.decisao.value == "CONFIRMAR"]
    investigar = [c for c in res.conciliacoes if c.decisao.value == "INVESTIGAR"]

    aprovados = [
        c for i, c in enumerate(confirmar)
        if decisoes_usuario.get(f"conc_{i}") == "aprovado"
    ]
    rejeitados = [
        c for i, c in enumerate(confirmar)
        if decisoes_usuario.get(f"conc_{i}") == "rejeitado"
    ]
    pendentes = [
        c for i, c in enumerate(confirmar)
        if f"conc_{i}" not in decisoes_usuario
    ]

    valor_validado = sum(
        (c.movimento.valor for c in auto + aprovados), Decimal("0")
    )
    valor_erro = sum(
        (c.movimento.valor for c in rejeitados), Decimal("0")
    )
    valor_analise = (
        sum((c.movimento.valor for c in pendentes + investigar), Decimal("0"))
        + sum((o.movimento.valor for o in res.orfaos), Decimal("0"))
    )
    total = sum(
        (m.valor for m in res.movimentos if m.is_credito), Decimal("0")
    )

    def percentual(valor):
        return float(valor / total) if total else 0.0

    return {
        "valor_validado": valor_validado,
        "valor_analise": valor_analise,
        "valor_erro": valor_erro,
        "valor_total": total,
        "percentual_validado": percentual(valor_validado),
        "percentual_analise": percentual(valor_analise),
        "percentual_erro": percentual(valor_erro),
        "qtd_validado": len(auto) + len(aprovados),
        "qtd_analise": len(pendentes) + len(investigar) + len(res.orfaos),
        "qtd_erro": len(rejeitados),
        "qtd_total": sum(1 for m in res.movimentos if m.is_credito),
    }


def construir_linhas_financeiras(res, decisoes_usuario):
    """Monta a visão linha a linha do extrato, sem misturar risco com caixa."""
    conciliacoes_por_movimento = {c.movimento.id: c for c in res.conciliacoes}
    orfaos_por_movimento = {o.movimento.id: o for o in res.orfaos}
    confirmar = [c for c in res.conciliacoes if c.decisao.value == "CONFIRMAR"]
    indice_confirmar = {c.movimento.id: i for i, c in enumerate(confirmar)}

    def alertas_da_linha(conciliacao):
        if not conciliacao:
            return []
        documentos = [t.documento for t in conciliacao.titulos]
        return [
            a for a in res.alertas
            if any(doc and any(doc in ref for ref in a.referencias) for doc in documentos)
        ]

    linhas = []
    for movimento in sorted(res.movimentos, key=lambda item: (item.data, item.id)):
        conciliacao = conciliacoes_por_movimento.get(movimento.id)
        orfao = orfaos_por_movimento.get(movimento.id)
        alertas = alertas_da_linha(conciliacao)
        valor = movimento.valor

        if not movimento.is_credito:
            if "TARIFA" in movimento.historico.upper():
                categoria = "Despesa bancária"
                acao = "Registrar como despesa e conferir tarifa contratada."
            elif "FORNECEDOR" in movimento.historico.upper():
                categoria = "Pagamento a fornecedor"
                acao = "Conferir NF, recebimento e aprovação antes de considerar encerrado."
            else:
                categoria = "Saída de caixa"
                acao = "Classificar no plano de contas."
            linhas.append({
                "Data": str(movimento.data),
                "Tipo": "🔻 Saída",
                "Histórico": movimento.historico,
                "Valor": f"- {fmt(valor)}",
                "Status caixa": "Saída registrada",
                "Categoria / vínculo": categoria,
                "Alerta / problema": "—",
                "Ação recomendada": acao,
            })
            continue

        if conciliacao:
            decisao_usuario = None
            if conciliacao.movimento.id in indice_confirmar:
                decisao_usuario = decisoes_usuario.get(
                    f"conc_{indice_confirmar[conciliacao.movimento.id]}"
                )
            if conciliacao.decisao.value == "AUTO_APLICAR":
                status = "✅ Validado pelo motor"
                acao = conciliacao.acao_sugerida or "Proposta pronta para revisão final."
            elif decisao_usuario == "aprovado":
                status = "✅ Validado pela analista"
                acao = "Linha aprovada; manter evidência da decisão."
            elif decisao_usuario == "rejeitado":
                status = "❌ Marcado como erro"
                acao = "Corrigir vínculo e investigar antes de qualquer baixa."
            else:
                status = "🟡 Em análise humana"
                acao = conciliacao.acao_sugerida or "Analista deve validar ou marcar como erro."

            vinculo = ", ".join(t.documento for t in conciliacao.titulos) or "Sem título"
            problemas = ", ".join(
                f"{a.codigo}: {a.titulo_curto}" for a in alertas
            ) or "Nenhum alerta vinculado à linha"
            if alertas:
                acao = f"⚠️ Revisar {', '.join(a.codigo for a in alertas)}. {acao}"
            linhas.append({
                "Data": str(movimento.data),
                "Tipo": "🔺 Entrada",
                "Histórico": movimento.historico,
                "Valor": f"+ {fmt(valor)}",
                "Status caixa": status,
                "Categoria / vínculo": f"Recebimento → {vinculo}",
                "Alerta / problema": problemas,
                "Ação recomendada": acao,
            })
            continue

        if orfao:
            linhas.append({
                "Data": str(movimento.data),
                "Tipo": "🔺 Entrada",
                "Histórico": movimento.historico,
                "Valor": f"+ {fmt(valor)}",
                "Status caixa": "🟡 Caixa não aplicado",
                "Categoria / vínculo": (
                    f"Conta transitória"
                    + (f" → {orfao.entidade_provavel}" if orfao.entidade_provavel else "")
                ),
                "Alerta / problema": "Sem título correspondente no data pack",
                "Ação recomendada": "Identificar a origem e aplicar ao título correto.",
            })

    return linhas


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------

try:
    res, tempo_exec, metricas = carregar_pipeline()
except Exception as e:
    st.error(f"Erro ao carregar pipeline: {e}")
    st.info("Execute `python run.py --sem-ia` primeiro para gerar os dados.")
    st.stop()

if "execucao_ativa" not in st.session_state:
    st.session_state.execucao_ativa = {
        "res": res,
        "metricas": metricas,
        "tempo": tempo_exec,
        "fonte": "data_pack do case",
    }
if "decisoes_usuario" not in st.session_state:
    st.session_state.decisoes_usuario = {}
if "alertas_tratados" not in st.session_state:
    st.session_state.alertas_tratados = {}
if "etapa_atual" not in st.session_state:
    st.session_state.etapa_atual = "preparar"

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

logo_path = ROOT / "assets" / "vantara-concilia-logo.png"
if logo_path.exists():
    logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    st.markdown(
        f"""
        <div class="brand-header">
            <img src="data:image/png;base64,{logo_data}" alt="Vantara Concilia">
            <div class="brand-copy">
                <div class="brand-name">Conciliação inteligente de recebíveis</div>
                <div class="brand-subtitle">Controle operacional · Contas a receber e a pagar</div>
                <span class="environment-badge">Ambiente de demonstração</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.title("Vantara Concilia")
    st.caption("Motor de identidade para conciliação de recebíveis e controle de contas a pagar")

# ---------------------------------------------------------------------------
# Fluxo em duas etapas
# ---------------------------------------------------------------------------

etapa_atual = st.session_state.etapa_atual
classe_preparar = "active" if etapa_atual == "preparar" else "done"
classe_validar = "active" if etapa_atual == "validar" else ""
icone_validar = "✓" if etapa_atual == "validar" else "2"
st.markdown(
    f"""
    <div class="workflow" aria-label="Fluxo da aplicação">
        <div class="workflow-step {classe_preparar}">
            <span class="workflow-number">{'1' if etapa_atual == 'preparar' else '✓'}</span>
            <span>Preparar dados</span>
        </div>
        <span class="workflow-arrow">→</span>
        <div class="workflow-step {classe_validar}">
            <span class="workflow-number">{icone_validar}</span>
            <span>Validar e fechar caixa</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ===== ETAPA 1: PREPARAR DADOS =============================================
if etapa_atual == "preparar":
    st.header("Etapa 1 · Preparar dados")
    st.markdown("""
    Envie os arquivos financeiros e execute a análise. O Vantara Concilia lê cada
    fonte como ela vem do sistema de origem, normaliza os dados e prepara a fila
    de validação. Ao concluir, você será direcionado automaticamente para a
    próxima etapa.
    """)

    st.divider()

    # ---------- Upload dos 4 arquivos ----------
    st.subheader("1. Fontes de dados")
    st.caption("Adicione os quatro arquivos exportados dos sistemas atuais. Nenhuma alteração é feita nas fontes originais.")

    def campo_upload(titulo, descricao, label, tipos, chave, ajuda):
        st.markdown(f"**{titulo}**")
        st.caption(descricao)
        return st.file_uploader(
            label,
            type=tipos,
            key=chave,
            label_visibility="collapsed",
            help=ajuda,
        )

    # Uma fonte por cartão/coluna evita o desalinhamento causado por dois
    # uploaders empilhados em colunas com descrições de alturas diferentes.
    fontes_linha1 = st.columns(2, gap="large")
    with fontes_linha1[0]:
        up_protheus = campo_upload(
            "Contas a receber — Protheus",
            "Exportação CSV · separador ; · UTF-8",
            "Protheus CSV",
            ["csv"],
            "up_protheus",
            "Colunas esperadas: PREFIXO; NUM; PARCELA; TIPO; EMISSAO; VENCTO; VLRTITULO; SALDO; CLIENTE; LOJA; A1_NOME; A1_CGC.",
        )
    with fontes_linha1[1]:
        up_omie = campo_upload(
            "Contas a receber — Omie",
            "Exportação CSV · separador ; · UTF-8",
            "Omie CSV",
            ["csv"],
            "up_omie",
            "Colunas esperadas: Numero NF; Codigo cliente; Razao social; CNPJ/CPF; Dt emissao; Dt vencimento; Valor documento; Valor em aberto; Status.",
        )

    fontes_linha2 = st.columns(2, gap="large")
    with fontes_linha2[0]:
        up_extrato = campo_upload(
            "Extrato bancário — Itaú",
            "Extrato CSV · valores com vírgula decimal",
            "Extrato CSV",
            ["csv"],
            "up_extrato",
            "Colunas esperadas: data; historico; valor; documento; agencia_origem; saldo.",
        )
    with fontes_linha2[1]:
        up_inbox = campo_upload(
            "Caixa de entrada — Contas a pagar",
            "Arquivo TXT · e-mails separados por ---",
            "Inbox AP TXT",
            ["txt"],
            "up_inbox",
            "Cada bloco deve conter De:, Data:, Assunto: e o corpo do e-mail.",
        )

    st.divider()

    # ---------- Opções ----------
    st.subheader("2. Configuração do processamento")
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        usar_ia_upload = st.toggle(
            "Ativar camada de IA (Gemini)",
            value=False,
            help="Requer GOOGLE_API_KEY no .env. Sem IA, o pipeline roda só com regras determinísticas.",
        )
    with col_cfg2:
        st.caption(
            "Os dados de exemplo do case (`data_pack/`) podem ser usados "
            "se você não tiver arquivos próprios — basta não enviar nenhum arquivo acima."
        )

    st.divider()

    # ---------- Executar ----------
    st.subheader("3. Iniciar análise")

    arquivos_enviados = sum(1 for f in [up_protheus, up_omie, up_extrato, up_inbox] if f)
    usar_exemplo = arquivos_enviados == 0

    if usar_exemplo:
        st.info(
            "Nenhum arquivo enviado — o pipeline usará os dados de exemplo "
            "(`data_pack/`) para demonstração."
        )

    botao = st.button(
        "Processar e continuar" if not usar_exemplo else "Processar dados de exemplo e continuar",
        type="primary",
        use_container_width=True,
    )

    if botao:
        import yaml
        cfg = yaml.safe_load((ROOT / "config" / "regras.yaml").read_text("utf-8"))

        if usar_exemplo:
            dir_dados = ROOT / "data_pack"
        else:
            tmpdir = tempfile.mkdtemp(prefix="vantara_")
            dir_dados = Path(tmpdir)
            nomes_arquivo = {}
            for chave, upfile, prefixo in [
                ("protheus", up_protheus, "01_contas_a_receber_protheus.csv"),
                ("omie", up_omie, "02_titulos_unidade_norte_omie.csv"),
                ("extrato", up_extrato, "03_extrato_bancario.csv"),
                ("inbox_ap", up_inbox, "04_caixa_de_entrada_contas_a_pagar.txt"),
            ]:
                if upfile is not None:
                    dest = dir_dados / prefixo
                    dest.write_bytes(upfile.getvalue())
                    nomes_arquivo[chave] = prefixo

        dir_saida_upload = ROOT / "out_upload"

        with st.spinner("Processando..."):
            inicio = time.perf_counter()
            try:
                from src.pipeline import executar
                res_up, saidas_up = executar(
                    dir_dados=dir_dados,
                    dir_saida=dir_saida_upload,
                    cfg=cfg,
                    usar_ia=usar_ia_upload,
                )
                tempo_up = time.perf_counter() - inicio
                metricas_up = res_up.metricas
                st.session_state.execucao_ativa = {
                    "res": res_up,
                    "metricas": metricas_up,
                    "tempo": tempo_up,
                    "fonte": "arquivos enviados" if not usar_exemplo else "data_pack do case",
                }
                # Uma nova execução começa uma nova revisão humana.
                st.session_state.decisoes_usuario = {}
                st.session_state.alertas_tratados = {}
                erro_exec = None
            except Exception as e:
                erro_exec = str(e)
                tempo_up = time.perf_counter() - inicio

        if erro_exec:
            st.error(f"Erro na execução: {erro_exec}")
        else:
            st.success(f"Dados processados em {tempo_up:.2f}s. Abrindo a central de validação...")
            st.session_state.etapa_atual = "validar"
            time.sleep(0.35)
            st.rerun()

            # ========== PAINEL DE RESULTADOS ==========
            st.divider()
            st.header("Resultado da análise")

            # --- KPIs rápidos ---
            k1, k2, k3, k4 = st.columns(4)
            conc_up = metricas_up["conciliacao"]
            vol_up = metricas_up["volumetria"]
            with k1:
                st.metric("Títulos", vol_up["titulos_em_aberto_entrada"])
            with k2:
                st.metric("Créditos", vol_up["creditos"])
            with k3:
                st.metric("Cobertura", f"{conc_up['cobertura_de_creditos']:.1%}")
            with k4:
                st.metric("Tempo", f"{tempo_up:.2f}s")

            st.divider()

            # ========== CHECKLIST DE AÇÕES ==========
            st.subheader("Checklist de verificação")
            st.markdown(
                "Cada etapa mostra o que foi processado com sucesso e o que precisa "
                "de atenção. Revise de cima para baixo."
            )

            # --- 1. Ingestão ---
            with st.expander(
                "✅ **Ingestão de dados** — arquivos carregados"
                if not res_up.avisos_ingestao
                else f"⚠️ **Ingestão de dados** — {len(res_up.avisos_ingestao)} aviso(s)",
                expanded=bool(res_up.avisos_ingestao),
            ):
                if res_up.avisos_ingestao:
                    for av in res_up.avisos_ingestao:
                        st.caption(f"  {av}")
                else:
                    st.markdown("Todos os arquivos foram lidos sem avisos.")
                st.markdown(
                    f"**{len(res_up.titulos)} títulos** de "
                    f"{len(set(t.fonte for t in res_up.titulos))} fonte(s) | "
                    f"**{len(res_up.movimentos)} movimentos** no extrato"
                )

            # --- 2. Identidade ---
            ent_multi = [e for e in res_up.entidades.values() if len(e.fontes) >= 2]
            fantasmas = [t for t in res_up.em_aberto if not t.e_cobravel]
            if fantasmas:
                label_ident = f"🔴 **Identidade** — {len(fantasmas)} possível(eis) duplicidade(s)"
            elif ent_multi:
                label_ident = f"🟡 **Identidade** — {len(ent_multi)} entidade(s) unificada(s) cross-ERP"
            else:
                label_ident = "✅ **Identidade** — entidades resolvidas"

            with st.expander(label_ident, expanded=bool(fantasmas)):
                st.markdown(f"**{len(res_up.entidades)} entidades** resolvidas")
                if ent_multi:
                    st.markdown("**Unificações cross-ERP:**")
                    for ent in ent_multi:
                        nomes = " / ".join(f"`{n}`" for n in ent.nomes_vistos)
                        st.markdown(f"- **{ent.nome_canonico}** ({', '.join(ent.fontes)}): {nomes}")
                if fantasmas:
                    st.markdown('<div class="danger-box">', unsafe_allow_html=True)
                    st.markdown("**Possíveis duplicidades — cobrança suspensa:**")
                    for g in fantasmas:
                        st.markdown(
                            f"- **{g.titulo.documento}** — {g.titulo.nome_original} — "
                            f"{fmt(g.titulo.valor)} — *{g.motivo}*"
                        )
                    st.markdown("**Ação:** validar documentos de origem antes de cobrar.")
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- 3. Conciliação AR ---
            auto_up = [c for c in res_up.conciliacoes if c.decisao.value == "AUTO_APLICAR"]
            confirmar_up = [c for c in res_up.conciliacoes if c.decisao.value == "CONFIRMAR"]
            investigar_up = [c for c in res_up.conciliacoes if c.decisao.value == "INVESTIGAR"]

            if confirmar_up or investigar_up:
                label_conc = (
                    f"🟡 **Conciliação** — {len(auto_up)} automática(s), "
                    f"{len(confirmar_up)} para revisão, {len(investigar_up)} para investigação"
                )
            else:
                label_conc = f"✅ **Conciliação** — {len(auto_up)} baixa(s) automática(s)"

            with st.expander(label_conc, expanded=bool(confirmar_up)):
                # Sucesso: automáticas
                if auto_up:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    valor_auto_up = sum(c.valor_aplicado for c in auto_up)
                    st.markdown(
                        f"**{len(auto_up)} baixa(s) automática(s)** — {fmt(valor_auto_up)}\n\n"
                        "Alta confiança; arquivo de importação pronto para o ERP."
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                # Atenção: para revisão humana
                if confirmar_up:
                    st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
                    st.markdown(
                        f"**{len(confirmar_up)} item(ns) para revisão humana:**"
                    )
                    for c in confirmar_up:
                        titulo_info = c.titulos[0] if c.titulos else None
                        cliente = titulo_info.nome_original[:30] if titulo_info else "?"
                        doc = titulo_info.documento if titulo_info else "?"
                        st.markdown(
                            f"- **{fmt(c.movimento.valor)}** — `{c.movimento.historico[:40]}` "
                            f"→ {doc} ({cliente}) — tier: {c.tier.value}, "
                            f"confiança: {c.confianca:.0%}"
                        )
                    st.markdown(
                        "\n**Ação:** revisar na central de validação > Fila de revisão. "
                        "Aprovar ou rejeitar cada vínculo."
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

                # Investigação
                if investigar_up:
                    st.markdown('<div class="danger-box">', unsafe_allow_html=True)
                    st.markdown(
                        f"**{len(investigar_up)} caso(s) para investigação** — "
                        "evidência insuficiente para propor vínculo."
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- 4. Caixa não aplicado ---
            if res_up.orfaos:
                with st.expander(
                    f"🟡 **Caixa não aplicado** — {len(res_up.orfaos)} crédito(s) sem título",
                    expanded=True,
                ):
                    st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
                    st.markdown("Créditos que entraram no banco e não encontraram título:")
                    for o in res_up.orfaos:
                        prov = f" (pagador provável: {o.entidade_provavel})" if o.entidade_provavel else ""
                        st.markdown(
                            f"- **{fmt(o.movimento.valor)}** em {o.movimento.data} — "
                            f"`{o.movimento.historico}`{prov}"
                        )
                    st.markdown(
                        "\n**Ação:** verificar se o crédito pertence a outra conta, "
                        "a um mês diferente, ou a um título não exportado."
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- 5. Alertas ---
            alertas_crit = [a for a in res_up.alertas if a.severidade.value == "CRITICO"]
            alertas_alto = [a for a in res_up.alertas if a.severidade.value == "ALTO"]
            alertas_outros = [a for a in res_up.alertas
                              if a.severidade.value not in ("CRITICO", "ALTO")]

            total_alertas = len(res_up.alertas)
            if alertas_crit:
                label_alertas = f"🔴 **Alertas** — {len(alertas_crit)} crítico(s), {total_alertas} total"
            elif alertas_alto:
                label_alertas = f"🟠 **Alertas** — {len(alertas_alto)} alto(s), {total_alertas} total"
            elif total_alertas:
                label_alertas = f"🟡 **Alertas** — {total_alertas} alerta(s)"
            else:
                label_alertas = "✅ **Alertas** — nenhum alerta"

            with st.expander(label_alertas, expanded=bool(alertas_crit)):
                sev_ordem = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "INFO": 3}
                sev_icons = {"CRITICO": "🔴", "ALTO": "🟠", "MEDIO": "🟡", "INFO": "🔵"}

                for a in sorted(res_up.alertas,
                                key=lambda x: sev_ordem.get(x.severidade.value, 9)):
                    ic = sev_icons.get(a.severidade.value, "⚪")
                    risco = f" — **{fmt(a.valor_em_risco)}**" if a.valor_em_risco else ""
                    st.markdown(
                        f"{ic} **[{a.codigo}]** {a.titulo_curto}{risco}\n"
                        f"  - Destinatário: {a.destinatario}"
                    )

                alr = metricas_up["alertas"]
                st.markdown("---")
                st.markdown(
                    f"Perda confirmada: **{fmt(Decimal(alr['valor_em_risco_confirmado']))}** | "
                    f"Exposição potencial: **{fmt(Decimal(alr['valor_exposicao_potencial']))}** | "
                    f"Sem controle: **{fmt(Decimal(alr['valor_sem_controle']))}**"
                )

            # --- 6. Conferência de fechamento ---
            saude = metricas_up["saude"]
            conf_ok = saude["conferencia_de_fechamento_ok"]

            with st.expander(
                "✅ **Conferência de fechamento** — invariantes OK"
                if conf_ok
                else "🔴 **Conferência de fechamento** — FALHOU",
                expanded=not conf_ok,
            ):
                for check in saude["checagens"]:
                    icone = "✅" if check["passou"] else "❌"
                    st.markdown(
                        f"{icone} **{check['nome']}** — {check['descricao']}\n"
                        f"  - Esperado: {fmt(Decimal(check['esperado']))} | "
                        f"Obtido: {fmt(Decimal(check['obtido']))} | "
                        f"Diferença: {fmt(Decimal(check['diferenca']))}"
                    )
                if conf_ok:
                    st.markdown('<div class="success-box">', unsafe_allow_html=True)
                    st.markdown(
                        "Conservação aritmética comprovada ao centavo. "
                        "A correção semântica dos vínculos exige auditoria do piloto."
                    )
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- 7. IA ---
            ia_up = metricas_up["ia"]
            if ia_up["ativa"] and ia_up["falhas"]:
                label_ia = (
                    f"⚠️ **IA ativa com fallback ({ia_up['modelo']})** — "
                    f"{ia_up['chamadas']} chamadas, {ia_up['falhas']} falha(s)"
                )
            elif ia_up["ativa"]:
                label_ia = (
                    f"✅ **IA ({ia_up['modelo']})** — "
                    f"{ia_up['chamadas']} chamadas, {ia_up['falhas']} falha(s)"
                )
            else:
                label_ia = f"ℹ️ **IA desligada** — {ia_up['motivo_desligada']}"

            with st.expander(label_ia, expanded=False):
                st.markdown(
                    f"- Provedor: **{ia_up['provedor'] or 'nenhum'}**\n"
                    f"- Modelo: **{ia_up['modelo'] or '-'}**\n"
                    f"- Chamadas: {ia_up['chamadas']} | Cache: {ia_up['acertos_cache']} | "
                    f"Abstenções: {ia_up['abstencoes']} | Falhas: {ia_up['falhas']}"
                )
                if ia_up.get("erros"):
                    st.markdown("**Diagnóstico das falhas:**")
                    for erro_ia in ia_up["erros"]:
                        st.error(
                            f"**{erro_ia['categoria']}** · {erro_ia['etapa']}\n\n"
                            f"{erro_ia['mensagem']}"
                        )
                    st.caption(
                        "A execução continuou com fallback determinístico e/ou fila humana. "
                        "Nenhuma baixa foi aplicada automaticamente pela IA."
                    )

            # --- Resumo final visual ---
            st.divider()

            etapas = [
                ("Ingestão", not bool(res_up.avisos_ingestao)),
                ("Identidade", not bool(fantasmas)),
                ("Conciliação", not bool(confirmar_up) and not bool(investigar_up)),
                ("Caixa não aplicado", not bool(res_up.orfaos)),
                ("Alertas", not bool(alertas_crit) and not bool(alertas_alto)),
                ("Conferência", conf_ok),
            ]

            sucesso = sum(1 for _, ok in etapas if ok)
            total_etapas = len(etapas)

            st.subheader(f"Resumo: {sucesso}/{total_etapas} etapas sem pendências")
            cols_res = st.columns(total_etapas)
            for i, (nome, ok) in enumerate(etapas):
                with cols_res[i]:
                    if ok:
                        st.markdown(
                            f'<div style="text-align:center; padding:12px; '
                            f'background:#d4edda; border-radius:8px; border:2px solid #28a745">'
                            f'<span style="font-size:1.5rem">✅</span><br>'
                            f'<small><b>{nome}</b></small></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="text-align:center; padding:12px; '
                            f'background:#fff3cd; border-radius:8px; border:2px solid #ffc107">'
                            f'<span style="font-size:1.5rem">⚠️</span><br>'
                            f'<small><b>{nome}</b></small></div>',
                            unsafe_allow_html=True,
                        )

# A execução selecionada na etapa de preparação alimenta a central de validação.
res = st.session_state.execucao_ativa["res"]
metricas = st.session_state.execucao_ativa["metricas"]
tempo_exec = st.session_state.execucao_ativa["tempo"]
fechamento_atual = calcular_fechamento_interativo(res, st.session_state.decisoes_usuario)

# ===== ETAPA 2: VALIDAR E FECHAR CAIXA =====================================
if etapa_atual == "validar":
    voltar_col, titulo_col = st.columns([1, 4])
    with voltar_col:
        if st.button("← Preparar novamente", use_container_width=True):
            st.session_state.etapa_atual = "preparar"
            st.rerun()
    st.header("Etapa 2 · Validar e fechar caixa")
    st.markdown("""
    > *Aqui a analista revisa as propostas, trata os alertas e acompanha o caixa
    > validado em tempo real. Cada decisão fica refletida no fechamento operacional.*
    """)

    # ---------- Painel de resumo do dia ----------
    st.subheader("📊 Resumo da execução — Julho/2026")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Créditos processados", f"{metricas['volumetria']['creditos']}")
    with kpi2:
        st.metric("Conciliados", f"{metricas['conciliacao']['creditos_conciliados']}")
    with kpi3:
        st.metric("Automáticos", f"{metricas['conciliacao']['por_decisao']['AUTO_APLICAR']['quantidade']}")
    with kpi4:
        st.metric("Para revisão", f"{metricas['conciliacao']['por_decisao']['CONFIRMAR']['quantidade']}")
    with kpi5:
        total_alertas_crit = metricas["alertas"]["por_severidade"].get("CRITICO", 0)
        st.metric("Alertas críticos", f"{total_alertas_crit}", delta="ação urgente" if total_alertas_crit > 0 else None, delta_color="inverse")

    st.divider()

    # ---------- Fechamento vivo do caixa ----------
    fechamento_atual = calcular_fechamento_interativo(
        res, st.session_state.decisoes_usuario
    )
    st.subheader("💰 Fechamento vivo do caixa")
    st.caption(
        "A decisão da analista altera esta apuração na hora: OK entra em validado; "
        "Erro sai do validado e fica registrado como erro."
    )
    caixa1, caixa2, caixa3, caixa4 = st.columns(4)
    with caixa1:
        st.metric(
            "Caixa validado",
            fmt(fechamento_atual["valor_validado"]),
            f"{fechamento_atual['percentual_validado']:.1%} · "
            f"{fechamento_atual['qtd_validado']} linha(s)",
        )
    with caixa2:
        st.metric(
            "Em análise humana",
            fmt(fechamento_atual["valor_analise"]),
            f"{fechamento_atual['percentual_analise']:.1%} · "
            f"{fechamento_atual['qtd_analise']} linha(s)",
        )
    with caixa3:
        st.metric(
            "Marcado como erro",
            fmt(fechamento_atual["valor_erro"]),
            f"{fechamento_atual['percentual_erro']:.1%} · "
            f"{fechamento_atual['qtd_erro']} linha(s)",
        )
    with caixa4:
        st.metric(
            "Total de créditos",
            fmt(fechamento_atual["valor_total"]),
            "100% classificado",
        )
    st.progress(
        min(fechamento_atual["percentual_validado"], 1.0),
        text=f"{fechamento_atual['percentual_validado']:.1%} do caixa validado até agora",
    )
    st.info(
        "Este fechamento é operacional: ‘validado’ significa pronto para a proposta "
        "de baixa. O piloto continua sem escrita automática no ERP."
    )

    # ---------- Estado de sessão para interações ----------
    if "decisoes_usuario" not in st.session_state:
        st.session_state.decisoes_usuario = {}
    if "alertas_tratados" not in st.session_state:
        st.session_state.alertas_tratados = {}

    # ---------- Sub-tabs dentro do sistema ----------
    sub1, sub2, sub3, sub4, sub5 = st.tabs([
        "Fila de revisão",
        "Baixas automáticas",
        "Alertas e riscos",
        "Painel executivo",
        "Caixa linha a linha",
    ])

    # --- Sub1: Fila de conciliação (itens para revisão) ---
    with sub1:
        st.markdown("### Itens que precisam da sua decisão")
        st.caption(
            "Validar linha coloca o valor no caixa validado. Marcar como erro "
            "retira o valor do validado e o mantém rastreado como erro."
        )

        confirmar = [c for c in res.conciliacoes if c.decisao.value == "CONFIRMAR"]

        if not confirmar:
            st.success("Nenhum item pendente de revisão.")
        else:
            for i, c in enumerate(confirmar):
                chave = f"conc_{i}"
                decisao_atual = st.session_state.decisoes_usuario.get(chave)

                with st.container():
                    # Cabeçalho do card
                    status_icon = {"aprovado": "✅", "rejeitado": "❌"}.get(decisao_atual, "⏳")
                    col_head, col_valor = st.columns([3, 1])
                    with col_head:
                        st.markdown(
                            f"#### {status_icon} {c.movimento.historico[:50]}"
                        )
                    with col_valor:
                        st.markdown(f"### {fmt(c.movimento.valor)}")

                    # Detalhes em duas colunas
                    col_banco, col_titulo = st.columns(2)
                    with col_banco:
                        st.markdown("**Crédito no banco**")
                        st.markdown(f"""
                        - **Data:** {c.movimento.data}
                        - **Histórico:** `{c.movimento.historico}`
                        - **Valor:** {fmt(c.movimento.valor)}
                        """)
                    with col_titulo:
                        st.markdown("**Título(s) vinculado(s)**")
                        for t in c.titulos:
                            st.markdown(f"""
                            - **{t.documento}** — {t.nome_original}
                            - Valor face: {fmt(t.valor)} | Saldo: {fmt(t.saldo)}
                            - Venc: {t.vencimento} | Tipo: {t.tipo} | Fonte: {t.fonte}
                            """)

                    # Evidências e confiança
                    col_ev, col_conf = st.columns([3, 1])
                    with col_ev:
                        with st.expander("📋 Evidências do motor", expanded=False):
                            for ev in c.evidencias:
                                st.markdown(f"- **{ev.regra}:** {ev.detalhe}")
                    with col_conf:
                        cor = "#28a745" if c.confianca >= 0.85 else "#ffc107" if c.confianca >= 0.70 else "#dc3545"
                        st.markdown(
                            f'<div style="text-align:center; padding:8px; background:{cor}22; '
                            f'border-radius:8px; border:2px solid {cor}">'
                            f'<small>Confiança</small><br>'
                            f'<span style="font-size:1.8rem; font-weight:bold; color:{cor}">'
                            f'{c.confianca:.0%}</span><br>'
                            f'<small>{c.tier.value}</small></div>',
                            unsafe_allow_html=True,
                        )

                    # Botões de ação
                    col_apr, col_rej, col_obs = st.columns([1, 1, 2])
                    with col_apr:
                        if st.button("✅ Validar linha", key=f"apr_{i}",
                                      type="primary", disabled=(decisao_atual is not None)):
                            st.session_state.decisoes_usuario[chave] = "aprovado"
                            st.rerun()
                    with col_rej:
                        if st.button("❌ Marcar como erro", key=f"rej_{i}",
                                      disabled=(decisao_atual is not None)):
                            st.session_state.decisoes_usuario[chave] = "rejeitado"
                            st.rerun()
                    with col_obs:
                        if decisao_atual:
                            st.markdown(
                                f'<div class="{"success-box" if decisao_atual == "aprovado" else "danger-box"}">'
                                f'{"Linha validada — valor entrou no caixa OK" if decisao_atual == "aprovado" else "Erro marcado — valor saiu do caixa validado"}'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    st.divider()

            # Resumo das decisões
            total_dec = len(st.session_state.decisoes_usuario)
            if total_dec > 0:
                aprovados = sum(1 for v in st.session_state.decisoes_usuario.values() if v == "aprovado")
                rejeitados = total_dec - aprovados
                st.markdown(f"""
                **Progresso da revisão:** {total_dec}/{len(confirmar)} itens revisados
                — {aprovados} aprovado(s), {rejeitados} rejeitado(s)
                """)
                if total_dec == len(confirmar):
                    st.balloons()
                    st.success("Revisão completa! Todos os itens foram processados.")

    # --- Sub2: Baixas automáticas ---
    with sub2:
        st.markdown("### Baixas propostas — já aprovadas pelo motor")
        st.caption(
            "Estes créditos passaram em TODAS as travas de automação. "
            "São propostas prontas para revisão final; o piloto não escreve no ERP."
        )

        auto = [c for c in res.conciliacoes if c.decisao.value == "AUTO_APLICAR"]
        if auto:
            dados_auto = []
            for c in auto:
                for t in c.titulos:
                    dados_auto.append({
                        "Status": "✅ Automático",
                        "Crédito": fmt(c.movimento.valor),
                        "Data": str(c.movimento.data),
                        "Histórico": c.movimento.historico[:35],
                        "Título": t.documento,
                        "Cliente": t.nome_original[:25],
                        "Tier": c.tier.value,
                        "Confiança": f"{c.confianca:.0%}",
                        "Classe Valor": c.classe_valor.value,
                    })
            st.dataframe(dados_auto, width="stretch", hide_index=True)

            valor_auto = sum(c.valor_aplicado for c in auto)
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(
                f"**{len(auto)} baixas automáticas** totalizando **{fmt(valor_auto)}** "
                f"— propostas validadas pelo motor, sem escrita automática no ERP."
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhuma baixa automática nesta execução.")

    # --- Sub3: Central de alertas ---
    with sub3:
        st.markdown("### Alertas que exigem ação")
        st.caption("Cada alerta tem um dono e uma ação recomendada. Trate pelo nível de severidade.")

        # Filtro de severidade
        sev_filtro = st.multiselect(
            "Filtrar por severidade",
            ["CRITICO", "ALTO", "MEDIO", "INFO"],
            default=["CRITICO", "ALTO"],
        )

        alertas_filtrados = [a for a in res.alertas if a.severidade.value in sev_filtro]

        for j, alerta in enumerate(sorted(alertas_filtrados,
                                           key=lambda a: ["CRITICO", "ALTO", "MEDIO", "INFO"].index(a.severidade.value))):
            chave_al = f"alerta_{j}"
            tratado = st.session_state.alertas_tratados.get(chave_al, False)

            sev_cores = {"CRITICO": "#dc3545", "ALTO": "#fd7e14", "MEDIO": "#ffc107", "INFO": "#17a2b8"}
            sev_icons = {"CRITICO": "🔴", "ALTO": "🟠", "MEDIO": "🟡", "INFO": "🔵"}
            cor = sev_cores.get(alerta.severidade.value, "#666")
            icon = sev_icons.get(alerta.severidade.value, "⚪")

            with st.container():
                col_sev, col_desc, col_valor, col_acao = st.columns([0.5, 3, 1, 1.5])

                with col_sev:
                    st.markdown(
                        f'<div style="text-align:center; padding:12px; background:{cor}22; '
                        f'border-radius:8px; border:2px solid {cor}">'
                        f'<span style="font-size:1.5rem">{icon}</span><br>'
                        f'<small><b>{alerta.severidade.value}</b></small></div>',
                        unsafe_allow_html=True,
                    )

                with col_desc:
                    st.markdown(f"**{alerta.codigo}** — {alerta.titulo_curto}")
                    with st.expander("Ver detalhes", expanded=False):
                        st.markdown(alerta.descricao)
                        if alerta.evidencias:
                            for ev in alerta.evidencias:
                                st.caption(f"📋 {ev.regra}: {ev.detalhe}")
                        if alerta.referencias:
                            st.markdown("**Referências:**")
                            for ref in alerta.referencias[:3]:
                                st.caption(ref)

                with col_valor:
                    st.markdown(f"**{fmt(alerta.valor_em_risco)}**")
                    st.caption(f"→ {alerta.destinatario}")

                with col_acao:
                    if tratado:
                        st.markdown(
                            '<div class="success-box" style="text-align:center">'
                            '<b>✅ Tratado</b></div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        if st.button(
                            f"Marcar como tratado",
                            key=f"tratar_{j}",
                        ):
                            st.session_state.alertas_tratados[chave_al] = True
                            st.rerun()

            st.divider()

        # Progresso
        total_alertas_vis = len(alertas_filtrados)
        tratados = sum(1 for k, v in st.session_state.alertas_tratados.items() if v)
        if total_alertas_vis > 0:
            st.progress(
                min(tratados / total_alertas_vis, 1.0),
                text=f"{tratados}/{total_alertas_vis} alertas tratados"
            )

    # --- Sub4: Painel de controle ---
    with sub4:
        st.markdown("### Visão consolidada")

        # Títulos em aberto com classificação
        st.subheader("📄 Títulos em aberto — classificados")
        st.caption(
            "A coluna **pode_cobrar** distingue cobrança liberada de caso suspenso para validação."
        )

        if res.em_aberto:
            dados_aberto = []
            for ta in res.em_aberto:
                dados_aberto.append({
                    "Pode cobrar?": "✅ Sim" if ta.e_cobravel else "❌ Não",
                    "Documento": ta.titulo.documento,
                    "Cliente": ta.titulo.nome_original[:25],
                    "Valor": fmt(ta.titulo.valor),
                    "Saldo": fmt(ta.titulo.saldo),
                    "Motivo": ta.motivo[:40],
                    "Severidade": ta.severidade.value,
                })
            st.dataframe(dados_aberto, width="stretch", hide_index=True)

        # Créditos órfãos
        if res.orfaos:
            st.subheader("💸 Caixa não aplicado")
            st.caption("Créditos que entraram no banco e não acharam título.")
            for o in res.orfaos:
                st.markdown(
                    f"- **{fmt(o.movimento.valor)}** em {o.movimento.data} — "
                    f"`{o.movimento.historico}` — {o.motivo}"
                )
                if o.entidade_provavel:
                    st.caption(f"  Pagador provável: {o.entidade_provavel}")

        # Conferência
        st.subheader("🔒 Conferência de fechamento")
        conf_ok = metricas["saude"]["conferencia_de_fechamento_ok"]
        if conf_ok:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown(
                "**✅ As duas invariantes fecham ao centavo.** A conservação aritmética foi "
                "comprovada; a correção semântica dos vínculos ainda exige auditoria do piloto."
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="danger-box">', unsafe_allow_html=True)
            st.markdown("**❌ Conferência FALHOU.** As saídas NÃO devem ser usadas.")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- Sub5: Caixa / DRE operacional linha a linha ---
    with sub5:
        st.markdown("### 🧾 Caixa / DRE operacional — linha a linha")
        st.caption(
            "Esta é uma visão gerencial do extrato, não uma DRE contábil fechada. "
            "Ela mostra exatamente o que entrou, saiu, foi validado e ainda está errado."
        )

        entradas = sum(
            (m.valor for m in res.movimentos if m.is_credito), Decimal("0")
        )
        saidas = sum(
            (m.valor for m in res.movimentos if not m.is_credito), Decimal("0")
        )
        saldo_liquido = entradas - saidas
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas no extrato", fmt(entradas))
        c2.metric("Saídas no extrato", fmt(saidas))
        c3.metric("Movimento líquido", fmt(saldo_liquido))

        st.markdown(
            "**Como ler:** ✅ validado = vínculo aceito; 🟡 análise = ainda não decidido; "
            "❌ erro = vínculo rejeitado; 🔻 saída = débito bancário. Alertas críticos "
            "aparecem na coluna de problema, mas não são somados novamente ao caixa."
        )

        linhas_financeiras = construir_linhas_financeiras(
            res, st.session_state.decisoes_usuario
        )
        st.dataframe(
            linhas_financeiras,
            width="stretch",
            hide_index=True,
            column_config={
                "Valor": st.column_config.TextColumn("Valor", width="small"),
                "Status caixa": st.column_config.TextColumn("Status do caixa", width="medium"),
                "Alerta / problema": st.column_config.TextColumn("O que está errado", width="large"),
                "Ação recomendada": st.column_config.TextColumn("Próxima ação", width="large"),
            },
        )

        st.divider()
        st.subheader("Leitura executiva do fechamento")
        fechamento_dre = calcular_fechamento_interativo(
            res, st.session_state.decisoes_usuario
        )
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Caixa validado", fmt(fechamento_dre["valor_validado"]))
        d2.metric("Em análise", fmt(fechamento_dre["valor_analise"]))
        d3.metric("Marcado como erro", fmt(fechamento_dre["valor_erro"]))
        d4.metric("Total de entradas", fmt(fechamento_dre["valor_total"]))
        st.info(
            "Para alterar uma linha, use a Fila de Conciliação. Ao validar ou marcar "
            "como erro, esta tabela e o fechamento são atualizados juntos."
        )

# A narrativa técnica foi movida para a página "Visão guiada".
st.divider()
st.caption(
    f"Pipeline executado em {tempo_exec:.2f}s — foco operacional: upload, revisão humana "
    f"e fechamento do caixa — conferência "
    f"{'✅ OK' if metricas['saude']['conferencia_de_fechamento_ok'] else '❌ FALHOU'}"
)

