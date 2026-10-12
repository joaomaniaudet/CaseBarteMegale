const pptxgen = require("pptxgenjs");
const path = require("path");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Barte AI Services";
pptx.company = "Barte";
pptx.subject = "Vantara Concilia — solução de negócio, técnica e arquitetura";
pptx.title = "Vantara Concilia — da identidade financeira à escala";
pptx.lang = "pt-BR";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "pt-BR",
};

const W = 13.333;
const H = 7.5;
const S = pptx.ShapeType;
const C = {
  dark: "111522",
  dark2: "1C2435",
  ink: "172033",
  muted: "667085",
  paper: "F7F8FC",
  white: "FFFFFF",
  purple: "6D4AFF",
  purpleSoft: "EEEAFE",
  mint: "20C7A8",
  mintSoft: "DDF8F1",
  blue: "4285F4",
  blueSoft: "E7F0FF",
  coral: "FF6B6B",
  coralSoft: "FFE8E8",
  amber: "F4B740",
  amberSoft: "FFF3D6",
  line: "DDE3EE",
  slate: "AAB5C8",
};

const logoPath = path.join(__dirname, "..", "assets", "vantara-concilia-logo.png");

function bg(slide, color) {
  slide.background = { color: color || C.paper };
}

function rr(slide, x, y, w, h, fill, line, radius) {
  slide.addShape(S.roundRect, {
    x: x, y: y, w: w, h: h,
    rectRadius: radius || 0.12,
    fill: { color: fill },
    line: { color: line || fill, width: 1 },
  });
}

function line(slide, x, y, w, h, color, width, dash) {
  slide.addShape(S.line, {
    x: x, y: y, w: w, h: h,
    line: { color: color, width: width || 1.5, dash: dash },
  });
}

function text(slide, value, x, y, w, h, opts) {
  slide.addText(value, Object.assign({
    x: x, y: y, w: w, h: h,
    fontFace: "Aptos",
    color: C.ink,
    margin: 0,
    fit: "shrink",
    breakLine: false,
  }, opts || {}));
}

function pill(slide, value, x, y, w, fill, color, opts) {
  rr(slide, x, y, w, 0.34, fill, fill, 0.17);
  text(slide, value, x + 0.06, y + 0.04, w - 0.12, 0.22, Object.assign({
    fontSize: 8.5,
    bold: true,
    color: color || C.white,
    align: "center",
  }, opts || {}));
}

function footer(slide, section, n, dark) {
  const color = dark ? "9AA6BA" : C.muted;
  text(slide, "BARTE  /  VANTARA CONCILIA  /  " + section.toUpperCase(), 0.6, 7.1, 6.5, 0.18, {
    fontSize: 8,
    color: color,
    charSpacing: 0.8,
  });
  text(slide, String(n).padStart(2, "0"), 12.1, 7.08, 0.55, 0.2, {
    fontSize: 9,
    bold: true,
    color: color,
    align: "right",
  });
}

function header(slide, kicker, title, subtitle, n, section) {
  text(slide, kicker.toUpperCase(), 0.65, 0.3, 5.5, 0.2, {
    fontSize: 8.5,
    bold: true,
    color: C.purple,
    charSpacing: 1.5,
  });
  text(slide, title, 0.65, 0.58, 12.0, 0.58, {
    fontFace: "Aptos Display",
    fontSize: 27,
    bold: true,
    color: C.ink,
  });
  if (subtitle) {
    text(slide, subtitle, 0.65, 1.18, 11.7, 0.36, {
      fontSize: 11.5,
      color: C.muted,
    });
  }
  footer(slide, section || "Vantara Concilia", n, false);
}

function darkHeader(slide, kicker, title, subtitle, n, section) {
  text(slide, kicker.toUpperCase(), 0.7, 0.55, 4.7, 0.2, {
    fontSize: 8.5,
    bold: true,
    color: C.mint,
    charSpacing: 1.5,
  });
  text(slide, title, 0.7, 1.25, 9.8, 1.25, {
    fontFace: "Aptos Display",
    fontSize: 36,
    bold: true,
    color: C.white,
  });
  if (subtitle) {
    text(slide, subtitle, 0.72, 2.75, 8.8, 0.6, {
      fontSize: 14,
      color: "C5CEDD",
    });
  }
  footer(slide, section || "Barte", n, true);
}

function card(slide, x, y, w, h, title, body, accent, fill) {
  rr(slide, x, y, w, h, fill || C.white, C.line, 0.1);
  slide.addShape(S.rect, {
    x: x, y: y, w: 0.07, h: h,
    fill: { color: accent || C.purple },
    line: { color: accent || C.purple },
  });
  text(slide, title, x + 0.25, y + 0.22, w - 0.45, 0.35, {
    fontSize: 13,
    bold: true,
    color: C.ink,
  });
  text(slide, body, x + 0.25, y + 0.72, w - 0.45, h - 0.9, {
    fontSize: 10.2,
    color: C.muted,
    valign: "top",
  });
}

function metric(slide, x, y, w, value, label, accent) {
  rr(slide, x, y, w, 1.25, C.white, C.line, 0.1);
  text(slide, value, x + 0.2, y + 0.2, w - 0.4, 0.45, {
    fontSize: 23,
    bold: true,
    color: accent,
  });
  text(slide, label, x + 0.2, y + 0.75, w - 0.4, 0.3, {
    fontSize: 9.5,
    color: C.muted,
  });
}

function node(slide, x, y, w, h, title, body, fill, accent, dark) {
  rr(slide, x, y, w, h, fill, accent, 0.1);
  text(slide, title, x + 0.18, y + 0.18, w - 0.36, 0.28, {
    fontSize: 12,
    bold: true,
    color: dark ? C.white : C.ink,
    align: "center",
  });
  text(slide, body, x + 0.18, y + 0.62, w - 0.36, h - 0.75, {
    fontSize: 9,
    color: dark ? "C5CEDD" : C.muted,
    align: "center",
    valign: "mid",
  });
}

function arrow(slide, x, y, w, color) {
  slide.addShape(S.chevron, {
    x: x, y: y, w: w, h: 0.3,
    fill: { color: color || C.purple },
    line: { color: color || C.purple },
  });
}

function numbered(slide, num, title, body, x, y, accent) {
  slide.addShape(S.ellipse, {
    x: x, y: y, w: 0.48, h: 0.48,
    fill: { color: accent }, line: { color: accent },
  });
  text(slide, String(num), x, y + 0.06, 0.48, 0.28, {
    fontSize: 12,
    bold: true,
    color: C.white,
    align: "center",
  });
  text(slide, title, x + 0.68, y - 0.02, 3.5, 0.28, {
    fontSize: 13,
    bold: true,
    color: C.ink,
  });
  text(slide, body, x + 0.68, y + 0.35, 3.6, 0.58, {
    fontSize: 9.5,
    color: C.muted,
  });
}

// 1 — Capa
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  if (require("fs").existsSync(logoPath)) {
    s.addImage({ path: logoPath, x: 0.7, y: 0.5, w: 3.7, h: 0.72 });
  }
  pill(s, "SOLUÇÃO + ARQUITETURA", 0.72, 1.65, 2.12, C.purple, C.white);
  text(s, "Vantara Concilia", 0.72, 2.2, 7.2, 0.72, {
    fontFace: "Aptos Display",
    fontSize: 40,
    bold: true,
    color: C.white,
  });
  text(s, "Da identidade financeira\na uma operação escalável.", 0.72, 3.05, 7.2, 1.1, {
    fontFace: "Aptos Display",
    fontSize: 28,
    bold: true,
    color: C.mint,
  });
  text(s, "Parte 1: solução para a Vantara\nParte 2: núcleo reutilizável para a Barte e outros clientes", 0.75, 4.55, 6.0, 0.78, {
    fontSize: 14,
    color: "C5CEDD",
  });
  rr(s, 8.35, 1.0, 4.25, 4.9, C.dark2, "39445A", 0.16);
  text(s, "ENTRADA", 8.75, 1.45, 1.2, 0.22, { fontSize: 8, bold: true, color: C.slate, charSpacing: 1.2 });
  ["Protheus", "Omie", "Banco", "Inbox AP"].forEach((v, i) => {
    pill(s, v, 8.75 + (i % 2) * 1.85, 1.9 + Math.floor(i / 2) * 0.62, 1.55, i % 2 ? C.blue : C.purple, C.white);
  });
  arrow(s, 10.1, 3.32, 0.62, C.mint);
  rr(s, 8.75, 3.8, 3.45, 1.3, C.mint, C.mint, 0.15);
  text(s, "IDENTIDADE\n+ EVIDÊNCIA", 9.0, 4.06, 2.95, 0.65, {
    fontSize: 18,
    bold: true,
    color: C.dark,
    align: "center",
  });
  text(s, "Barte AI Services  ·  Outubro 2026", 0.75, 6.55, 5.0, 0.2, { fontSize: 9, color: "9AA6BA" });
  footer(s, "Abertura", 1, true);
}

// 2 — Tese executiva
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Tese executiva", "A recomendação não é comprar uma IA de conciliação", "É criar uma camada de identidade e decisão auditável sobre a operação financeira existente.", 2, "Abertura");
  card(s, 0.72, 1.85, 3.85, 2.15, "Problema real", "Protheus, Omie, banco e planilhas não compartilham uma identidade financeira confiável. O matching vira sintoma de uma operação descentralizada.", C.coral, C.coralSoft);
  card(s, 4.75, 1.85, 3.85, 2.15, "Resposta", "Normalizar entidades, preservar evidências, propor vínculos e encaminhar exceções para a pessoa certa.", C.purple, C.purpleSoft);
  card(s, 8.78, 1.85, 3.85, 2.15, "Barte", "Entregar um core reutilizável: conectores, regras, IA limitada, controles e uma camada de operação que conversa com a stack existente.", C.mint, C.mintSoft);
  rr(s, 0.72, 4.55, 11.9, 1.22, C.dark, C.dark, 0.12);
  text(s, "Regra de ouro", 1.0, 4.82, 1.5, 0.22, { fontSize: 10, bold: true, color: C.mint, charSpacing: 1.1 });
  text(s, "Se a evidência não sustenta a decisão, o sistema se abstém — e explica por quê.", 2.7, 4.75, 8.9, 0.34, { fontSize: 17, bold: true, color: C.white, align: "center" });
}

// 3 — Parte 1 divider
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  darkHeader(s, "Parte 1", "A solução para a Vantara", "Do problema de negócio ao piloto operacional: recebíveis primeiro, zero escrita no ERP e humano no controle.", 3, "Parte 1");
  pill(s, "NEGÓCIO", 0.72, 4.35, 1.2, C.purple, C.white);
  pill(s, "FUNCIONAMENTO", 2.1, 4.35, 1.55, C.blue, C.white);
  pill(s, "ARQUITETURA", 3.85, 4.35, 1.42, C.mint, C.dark);
  rr(s, 8.75, 1.2, 3.2, 3.25, C.dark2, "39445A", 0.15);
  text(s, "O que muda?", 9.15, 1.65, 2.4, 0.3, { fontSize: 14, bold: true, color: C.white, align: "center" });
  text(s, "De arquivos dispersos\npara uma fila auditável\ncom caixa explicado\nlinha a linha.", 9.15, 2.35, 2.4, 1.45, { fontSize: 22, bold: true, color: C.mint, align: "center" });
}

// 4 — Contexto
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Contexto de negócio", "O gargalo é a assimetria de dados", "A operação reage depois que o dinheiro entrou — e antes de saber de quem é o dinheiro.", 4, "Parte 1");
  const stages = [
    ["01", "Operação descentralizada", "Protheus, Omie, bancos e planilhas mantêm versões diferentes da mesma realidade.", C.purple, C.purpleSoft],
    ["02", "Pagamento sem identidade", "Depósitos, PIX e TED chegam com nomes truncados, valores diferentes ou sem documento.", C.blue, C.blueSoft],
    ["03", "Conciliação manual", "O analista abre sistema por sistema e trabalha por exceção, sem uma trilha comum.", C.amber, C.amberSoft],
    ["04", "Atrito e risco", "Cobrança indevida, pagamento duplicado e fechamento tardio afetam caixa e relacionamento.", C.coral, C.coralSoft],
  ];
  stages.forEach((a, i) => {
    const x = 0.72 + i * 3.05;
    rr(s, x, 2.0, 2.72, 2.65, a[4], a[3], 0.12);
    text(s, a[0], x + 0.22, 2.22, 0.45, 0.3, { fontSize: 16, bold: true, color: a[3] });
    text(s, a[1], x + 0.22, 2.78, 2.18, 0.45, { fontSize: 15, bold: true, color: C.ink, align: "center" });
    text(s, a[2], x + 0.28, 3.55, 2.12, 0.72, { fontSize: 10, color: C.muted, align: "center" });
    if (i < 3) arrow(s, x + 2.78, 3.15, 0.28, C.muted);
  });
  text(s, "Premissas do case: piloto em 30 dias · acesso de leitura · sem escrita no ERP nos primeiros 90 dias", 1.4, 5.55, 10.5, 0.32, { fontSize: 12, bold: true, color: C.purple, align: "center" });
}

// 5 — Casos de uso
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Casos de uso", "Onde a solução captura valor", "Cada caso combina uma pista de identidade, uma regra de segurança e uma decisão humana quando necessário.", 5, "Parte 1");
  card(s, 0.72, 1.78, 2.85, 2.0, "Recebível sem identificação", "R$ 5.670,00 no depósito sem identificação associado ao título Omie de Trigo e Cia por valor e contexto.", C.blue, C.blueSoft);
  card(s, 3.78, 1.78, 2.85, 2.0, "Pagamento parcial", "R$ 62.500,00 contra título de R$ 125.000,00. O caixa entra, mas o saldo remanescente permanece aberto.", C.amber, C.amberSoft);
  card(s, 6.84, 1.78, 2.85, 2.0, "Desconto ou juros", "R$ 14.820,00 contra R$ 15.600,00 e R$ 23.358,00 contra R$ 22.900,00: hipótese, não baixa cega.", C.purple, C.purpleSoft);
  card(s, 9.9, 1.78, 2.72, 2.0, "Pagar com evidência", "Boleto reemitido de R$ 19.278,00, entrega parcial e aprovação por WhatsApp entram na esteira de AP.", C.coral, C.coralSoft);
  rr(s, 0.72, 4.45, 11.9, 1.32, C.dark, C.dark, 0.12);
  text(s, "Resultado do data pack de julho", 1.0, 4.72, 2.3, 0.23, { fontSize: 10, bold: true, color: C.mint, charSpacing: 0.7 });
  text(s, "14/15 créditos vinculados  ·  99,4% de cobertura por valor  ·  8 propostas de alta confiança  ·  R$ 50.528 de exposição potencial  ·  R$ 0 de perda confirmada", 1.0, 5.13, 11.1, 0.33, { fontSize: 13, bold: true, color: C.white, align: "center" });
  text(s, "Métricas da amostra sintética; não representam produção.", 4.25, 5.75, 4.8, 0.18, { fontSize: 8.5, color: C.slate, align: "center" });
}

// 6 — Jornada
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Funcionamento", "A jornada do usuário começa no arquivo e termina na decisão", "A aplicação separa preparar dados de validar e fechar caixa para reduzir carga cognitiva.", 6, "Parte 1");
  const flow = [
    ["1", "Preparar dados", "Upload dos quatro arquivos\nou data pack de exemplo", C.purple],
    ["2", "Processar", "Ingestão, normalização,\nidentidade e matching", C.blue],
    ["3", "Revisar", "Fila com evidência,\nconfiança e ação", C.amber],
    ["4", "Fechar caixa", "Validado, análise,\nerro e total", C.mint],
  ];
  flow.forEach((a, i) => {
    const x = 0.78 + i * 3.08;
    rr(s, x, 2.05, 2.45, 2.18, C.white, a[3], 0.12);
    s.addShape(S.ellipse, { x: x + 0.88, y: 2.34, w: 0.68, h: 0.68, fill: { color: a[3] }, line: { color: a[3] } });
    text(s, a[0], x + 0.88, 2.51, 0.68, 0.25, { fontSize: 15, bold: true, color: C.white, align: "center" });
    text(s, a[1], x + 0.22, 3.18, 2.0, 0.3, { fontSize: 15, bold: true, color: C.ink, align: "center" });
    text(s, a[2], x + 0.28, 3.62, 1.9, 0.48, { fontSize: 10, color: C.muted, align: "center" });
    if (i < 3) arrow(s, x + 2.56, 2.95, 0.35, C.muted);
  });
  rr(s, 1.45, 4.85, 10.45, 0.85, C.mintSoft, C.mint, 0.12);
  text(s, "A decisão da analista é o evento que conecta a fila ao caixa: OK entra em validado; erro fica rastreado; pendente permanece em análise.", 1.75, 5.08, 9.85, 0.3, { fontSize: 13, bold: true, color: C.ink, align: "center" });
}

// 7 — Caixa
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Visibilidade operacional", "O fechamento deixa de ser uma opinião", "A visão de caixa não soma alertas novamente: ela acompanha movimentos bancários e decisões sobre cada linha.", 7, "Parte 1");
  metric(s, 0.72, 1.8, 2.75, "R$ 152.880", "caixa validado automaticamente", C.mint);
  metric(s, 3.7, 1.8, 2.75, "R$ 162.928", "em análise humana", C.amber);
  metric(s, 6.68, 1.8, 2.75, "R$ 0", "perda confirmada no data pack", C.blue);
  metric(s, 9.66, 1.8, 2.95, "R$ 315.808", "total de créditos no extrato", C.purple);
  card(s, 0.72, 3.55, 5.7, 2.08, "Caixa / DRE linha a linha", "Cada movimento mostra data, histórico, tipo, valor, status do caixa, vínculo, alerta/problema e próxima ação. O analista consegue explicar o que está errado sem alternar entre telas.", C.purple, C.purpleSoft);
  card(s, 6.62, 3.55, 6.0, 2.08, "Separação importante", "Um alerta pode apontar exposição sobre um movimento já recebido. Ele não é uma segunda entrada. O sistema separa caixa real, risco cadastral e decisão de baixa.", C.coral, C.coralSoft);
  text(s, "Os valores acima são da amostra sintética de julho e servem para demonstrar o modelo de operação.", 3.15, 6.1, 7.1, 0.2, { fontSize: 8.5, color: C.muted, align: "center" });
}

// 8 — Fluxo técnico
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Funcionamento técnico", "O pipeline transforma arquivos em decisões explicáveis", "A ordem importa: ingestão, identidade, valor, controle e ação.", 8, "Parte 1");
  const items = [
    ["Fontes", "Protheus\nOmie\nItaú\nInbox AP", C.purple, C.purpleSoft],
    ["Normalização", "CNPJ\nnomes\nvalores\ndatas", C.blue, C.blueSoft],
    ["Identidade", "nosso número\nCNPJ\nnome\ncandidatos", C.mint, C.mintSoft],
    ["Decisão", "auto aplicar\nconfirmar\ninvestigar", C.amber, C.amberSoft],
    ["Saída", "fila\nalertas\ncaixa\nrelatório", C.coral, C.coralSoft],
  ];
  items.forEach((a, i) => {
    const x = 0.56 + i * 2.55;
    node(s, x, 2.0, 2.05, 2.1, a[0], a[1], a[3], a[2], false);
    if (i < items.length - 1) arrow(s, x + 2.12, 2.88, 0.3, C.muted);
  });
  rr(s, 1.2, 4.85, 10.9, 0.8, C.dark, C.dark, 0.12);
  text(s, "A IA só recebe candidatos previamente filtrados; nunca recebe o universo inteiro e nunca aplica uma baixa sozinha.", 1.55, 5.08, 10.2, 0.3, { fontSize: 13, bold: true, color: C.white, align: "center" });
}

// 9 — Arquitetura Vantara
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Arquitetura técnica", "Componentes do piloto Vantara", "O desenho preserva o ERP como sistema de registro e cria uma camada segura de leitura, decisão e saída.", 9, "Parte 1");
  rr(s, 0.72, 1.72, 3.0, 3.95, C.blueSoft, C.blue, 0.12);
  text(s, "FONTES DE LEITURA", 1.0, 2.02, 2.4, 0.25, { fontSize: 10, bold: true, color: C.blue, charSpacing: 1 });
  ["CSV Protheus", "CSV Omie", "Extrato Itaú", "TXT Inbox AP"].forEach((v, i) => {
    rr(s, 1.0, 2.55 + i * 0.58, 2.42, 0.4, C.white, C.line, 0.08);
    text(s, v, 1.15, 2.65 + i * 0.58, 2.1, 0.2, { fontSize: 10, bold: true, color: C.ink, align: "center" });
  });
  arrow(s, 3.88, 3.45, 0.55, C.muted);
  rr(s, 4.58, 1.72, 4.18, 3.95, C.purpleSoft, C.purple, 0.12);
  text(s, "CORE DE CONCILIAÇÃO", 4.9, 2.02, 3.55, 0.25, { fontSize: 10, bold: true, color: C.purple, charSpacing: 1 });
  const core = [
    "Modelo canônico",
    "Identidade e deduplicação",
    "Cascata de matching",
    "Classificação de valor",
    "Regras de risco e auditoria",
  ];
  core.forEach((v, i) => {
    text(s, "•  " + v, 4.95, 2.58 + i * 0.47, 3.4, 0.25, { fontSize: 11, color: C.ink });
  });
  arrow(s, 8.93, 3.45, 0.55, C.muted);
  rr(s, 9.65, 1.72, 2.98, 3.95, C.mintSoft, C.mint, 0.12);
  text(s, "SAÍDAS CONTROLADAS", 9.92, 2.02, 2.4, 0.25, { fontSize: 10, bold: true, color: C.mint, charSpacing: 0.8 });
  ["Fila humana", "Baixas propostas", "Alertas", "Relatório HTML", "Metricas JSON"].forEach((v, i) => {
    text(s, "✓  " + v, 9.95, 2.58 + i * 0.47, 2.2, 0.25, { fontSize: 11, color: C.ink });
  });
  text(s, "Nenhuma escrita automática no ERP no piloto.", 3.45, 6.05, 6.5, 0.25, { fontSize: 12, bold: true, color: C.purple, align: "center" });
}

// 10 — IA
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Inteligência artificial", "IA como camada de desempate — não como autoridade", "A maior parte do valor vem de regras auditáveis; o modelo entra onde o texto exige interpretação.", 10, "Parte 1");
  card(s, 0.72, 1.85, 3.75, 2.15, "Determinístico primeiro", "Nosso número, CNPJ, valor, data, normalização e invariantes são executados sem chamada externa.", C.blue, C.blueSoft);
  card(s, 4.78, 1.85, 3.75, 2.15, "IA em espaço restrito", "Recebe uma lista fechada de candidatos ou texto de AP para extrair fatos que não possuem coluna estruturada.", C.purple, C.purpleSoft);
  card(s, 8.84, 1.85, 3.78, 2.15, "Abstenção é sucesso", "Resposta inválida, baixa confiança ou falha de API viram diagnóstico e fila humana. Nada é baixado automaticamente pela IA.", C.mint, C.mintSoft);
  rr(s, 0.72, 4.55, 11.9, 1.28, C.dark, C.dark, 0.12);
  text(s, "Guard-rails", 1.0, 4.82, 1.3, 0.22, { fontSize: 10, bold: true, color: C.mint, charSpacing: 1 });
  text(s, "candidatos limitados  ·  IDs fora da lista descartados  ·  schema JSON  ·  cache auditável  ·  fallback determinístico  ·  humano aplica", 2.45, 4.78, 9.65, 0.3, { fontSize: 12.5, bold: true, color: C.white, align: "center" });
}

// 11 — Segurança e piloto
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Segurança e implantação", "A Vantara mantém a casa; a Barte entrega o motor", "Proposta de piloto: execução dentro do ambiente aprovado pela Vantara, com leitura e saídas controladas.", 11, "Parte 1");
  const arch = [
    ["ERP / Banco", "exportações\nread-only", C.blueSoft, C.blue],
    ["Bucket Vantara", "arquivos +\nlogs", C.purpleSoft, C.purple],
    ["Runtime isolado", "core +\nconfiguração", C.mintSoft, C.mint],
    ["Saídas", "fila +\nrelatório", C.amberSoft, C.amber],
  ];
  arch.forEach((a, i) => {
    const x = 0.72 + i * 3.08;
    node(s, x, 1.92, 2.35, 1.5, a[0], a[1], a[2], a[3], false);
    if (i < arch.length - 1) arrow(s, x + 2.43, 2.5, 0.35, C.muted);
  });
  pill(s, "READ-ONLY", 1.3, 3.92, 1.3, C.blue, C.white);
  pill(s, "ISOLAMENTO", 3.0, 3.92, 1.4, C.purple, C.white);
  pill(s, "KMS / LOGS", 4.82, 3.92, 1.25, C.mint, C.dark);
  pill(s, "ZERO ESCRITA ERP", 6.48, 3.92, 1.75, C.amber, C.ink);
  card(s, 0.72, 4.75, 3.72, 1.15, "Semana 1", "Exports e golden set assinados pela Controller.", C.blue, C.blueSoft);
  card(s, 4.8, 4.75, 3.72, 1.15, "Semanas 2–3", "Shadow mode, fila diária e medição por tier.", C.purple, C.purpleSoft);
  card(s, 8.88, 4.75, 3.74, 1.15, "Semana 4", "Decidir aceitar, recalibrar ou interromper.", C.mint, C.mintSoft);
}

// 12 — Parte 2 divider
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  darkHeader(s, "Parte 2", "O que a Barte pode reutilizar", "A Vantara é o caso de prova. O ativo estratégico é um padrão de operação que pode ser configurado para outras empresas.", 12, "Parte 2");
  pill(s, "CORE BARTE", 0.72, 4.35, 1.45, C.purple, C.white);
  pill(s, "CONFIGURAÇÃO", 2.35, 4.35, 1.55, C.blue, C.white);
  pill(s, "MULTI-CLIENTE", 4.1, 4.35, 1.55, C.mint, C.dark);
  rr(s, 8.85, 1.25, 3.0, 3.05, C.dark2, "39445A", 0.15);
  text(s, "O produto não é\num parser de Protheus.", 9.2, 1.72, 2.3, 0.85, { fontSize: 21, bold: true, color: C.white, align: "center" });
  text(s, "É o contrato auditável entre\nentrada suja, evidência,\ndecisão e ação humana.", 9.2, 2.95, 2.3, 0.75, { fontSize: 13, color: C.mint, align: "center" });
}

// 13 — Core vs config
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Reuso", "Parametrizar o cliente, não duplicar o produto", "A fronteira entre core e configuração é o que permite escalar sem perder governança.", 13, "Parte 2");
  rr(s, 0.72, 1.75, 5.78, 4.28, C.purpleSoft, C.purple, 0.12);
  pill(s, "CORE REUTILIZÁVEL", 1.05, 2.03, 1.72, C.purple, C.white);
  [
    "modelo canônico de títulos e movimentos",
    "adapters e contrato de ingestão",
    "normalização de identidade",
    "cascata de matching e confiança",
    "classificação de divergências",
    "fila humana e estados operacionais",
    "invariantes, métricas e auditoria",
    "contrato de IA e fallback",
  ].forEach((v, i) => text(s, "•  " + v, 1.08, 2.65 + i * 0.36, 4.9, 0.23, { fontSize: 10, color: C.ink }));
  rr(s, 6.82, 1.75, 5.8, 4.28, C.blueSoft, C.blue, 0.12);
  pill(s, "CONFIGURAÇÃO POR CLIENTE", 7.15, 2.03, 2.1, C.blue, C.white);
  [
    "layouts e nomes de colunas",
    "contas, unidades e fontes",
    "políticas de tolerância",
    "mapeamentos e destinatários",
    "golden set do cliente",
    "retenção e política de dados",
    "limites de confiança",
    "ambiente e requisitos de segurança",
  ].forEach((v, i) => text(s, "•  " + v, 7.18, 2.65 + i * 0.36, 4.9, 0.23, { fontSize: 10, color: C.ink }));
}

// 14 — Multi-client architecture
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Arquitetura Barte", "Um core, vários ambientes isolados", "Arquitetura proposta para múltiplos clientes: o código é comum; os dados, segredos e parâmetros não se misturam.", 14, "Parte 2");
  rr(s, 0.72, 1.72, 3.2, 4.18, C.dark, C.dark, 0.12);
  text(s, "BARTE CONTROL PLANE", 1.05, 2.03, 2.5, 0.23, { fontSize: 9, bold: true, color: C.mint, charSpacing: 1 });
  ["Imagem assinada", "Versionamento do core", "Registry de configurações", "Observabilidade sem dados financeiros"].forEach((v, i) => {
    rr(s, 1.02, 2.65 + i * 0.62, 2.6, 0.4, C.dark2, "39445A", 0.08);
    text(s, v, 1.13, 2.75 + i * 0.62, 2.35, 0.2, { fontSize: 9.5, color: C.white, align: "center" });
  });
  arrow(s, 4.16, 3.45, 0.5, C.muted);
  const tenants = [
    ["Cliente A", "dados + config A", C.purple, C.purpleSoft],
    ["Vantara", "dados + config V", C.mint, C.mintSoft],
    ["Cliente C", "dados + config C", C.blue, C.blueSoft],
  ];
  tenants.forEach((a, i) => {
    const y = 1.75 + i * 1.45;
    rr(s, 4.95, y, 3.15, 1.05, a[3], a[2], 0.1);
    text(s, a[0], 5.2, y + 0.2, 1.05, 0.25, { fontSize: 12, bold: true, color: C.ink });
    text(s, a[1], 6.28, y + 0.2, 1.5, 0.25, { fontSize: 10, color: C.muted, align: "right" });
    text(s, "runtime isolado  ·  read-only  ·  logs do tenant", 5.2, y + 0.62, 2.5, 0.18, { fontSize: 8.5, color: C.muted });
    arrow(s, 8.3, y + 0.35, 0.42, C.muted);
  });
  rr(s, 9.0, 1.72, 3.62, 4.18, C.mintSoft, C.mint, 0.12);
  text(s, "CONTRATO DE SAÍDA", 9.35, 2.03, 2.9, 0.23, { fontSize: 9, bold: true, color: C.mint, charSpacing: 1 });
  ["fila de revisão", "alertas rastreáveis", "métricas", "relatório", "propostas sem escrita"].forEach((v, i) => {
    text(s, "✓  " + v, 9.35, 2.68 + i * 0.55, 2.65, 0.24, { fontSize: 11, color: C.ink });
  });
}

// 15 — Onboarding
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Modelo de entrega", "Cada novo cliente começa por configuração e evidência", "A Barte pode repetir o método sem prometer automação antes de conhecer a operação.", 15, "Parte 2");
  const steps = [
    ["1", "Mapear fontes", "Quais ERPs, bancos, caixas de entrada e layouts existem?", C.purple],
    ["2", "Criar contrato", "Normalizar campos, identidade, estados e responsáveis.", C.blue],
    ["3", "Montar golden set", "Casos reais assinados pelo cliente e critérios de aceite.", C.amber],
    ["4", "Rodar shadow mode", "Sem escrita; medir precisão, exceções e tempo de revisão.", C.mint],
    ["5", "Expandir", "Só depois parametrizar AP, cobrança ou novas contas.", C.coral],
  ];
  steps.forEach((a, i) => {
    const x = 0.58 + i * 2.55;
    s.addShape(S.ellipse, { x: x + 0.85, y: 1.95, w: 0.62, h: 0.62, fill: { color: a[3] }, line: { color: a[3] } });
    text(s, a[0], x + 0.85, 2.12, 0.62, 0.2, { fontSize: 14, bold: true, color: C.white, align: "center" });
    text(s, a[1], x + 0.08, 2.92, 2.15, 0.3, { fontSize: 13, bold: true, color: C.ink, align: "center" });
    text(s, a[2], x + 0.14, 3.42, 2.0, 0.65, { fontSize: 9.5, color: C.muted, align: "center" });
    if (i < 4) line(s, x + 1.55, 2.26, 0.94, 0, C.line, 2.5);
  });
  rr(s, 1.35, 5.1, 10.65, 0.83, C.dark, C.dark, 0.12);
  text(s, "A unidade de escala não é o número de telas. É a capacidade de transformar exceções de um cliente em configuração e regra reutilizável.", 1.7, 5.34, 9.95, 0.28, { fontSize: 12.5, bold: true, color: C.white, align: "center" });
}

// 16 — Barte value
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Potencial de negócio", "O ativo para a Barte é a camada de operação", "A solução conversa com a stack existente e transforma decisões financeiras em contexto reutilizável.", 16, "Parte 2");
  card(s, 0.72, 1.8, 3.78, 2.15, "Expansão de escopo", "Começar em recebíveis e, com evidência, avançar para AP, cobrança, tesouraria e outras contas.", C.purple, C.purpleSoft);
  card(s, 4.78, 1.8, 3.78, 2.15, "Diferenciação", "Não vender uma tela isolada. Entregar especialistas, agentes e relatórios amarrados à evidência de origem.", C.mint, C.mintSoft);
  card(s, 8.84, 1.8, 3.78, 2.15, "Aprendizado composto", "Cada exceção validada pode virar regra, configuração ou teste do core — desde que seja generalizável.", C.blue, C.blueSoft);
  rr(s, 0.72, 4.52, 11.9, 1.28, C.amberSoft, C.amber, 0.12);
  text(s, "Sem inventar resultado", 1.0, 4.82, 1.8, 0.22, { fontSize: 10, bold: true, color: C.amber, charSpacing: 0.8 });
  text(s, "O potencial comercial é uma hipótese de expansão. Deve ser validado por precisão, tempo de revisão, adesão do time e segurança de cada cliente.", 3.0, 4.77, 8.95, 0.34, { fontSize: 13, bold: true, color: C.ink, align: "center" });
}

// 17 — Premissas e limites
{
  const s = pptx.addSlide();
  bg(s);
  header(s, "Rigor", "O que ainda precisa ser validado", "A proposta é forte quando explicita seus limites — e transforma cada limite em critério de piloto.", 17, "Parte 2");
  const left = [
    "Os dados usados no deck são sintéticos.",
    "Uma conta bancária não representa as quatro contas.",
    "CNPJ + valor + vencimento é indício, não prova.",
    "Anexos fiscais e boletos não foram fornecidos.",
  ];
  const right = [
    "O runtime multi-cliente precisa de aprovação de segurança.",
    "A integração de importação do Protheus precisa ser homologada.",
    "A precisão deve ser medida por cliente e por tier.",
    "A economia operacional ainda não foi quantificada.",
  ];
  rr(s, 0.72, 1.78, 5.78, 3.75, C.coralSoft, C.coral, 0.12);
  pill(s, "EVIDÊNCIA ATUAL", 1.02, 2.08, 1.55, C.coral, C.white);
  left.forEach((v, i) => text(s, "•  " + v, 1.03, 2.72 + i * 0.55, 4.95, 0.25, { fontSize: 11, color: C.ink }));
  rr(s, 6.82, 1.78, 5.8, 3.75, C.amberSoft, C.amber, 0.12);
  pill(s, "GATES DO PILOTO", 7.12, 2.08, 1.45, C.amber, C.ink);
  right.forEach((v, i) => text(s, "•  " + v, 7.13, 2.72 + i * 0.55, 4.95, 0.25, { fontSize: 11, color: C.ink }));
  rr(s, 2.1, 5.85, 9.05, 0.55, C.dark, C.dark, 0.12);
  text(s, "O piloto compra evidência operacional — não uma promessa de automação.", 2.35, 6.02, 8.55, 0.22, { fontSize: 12, bold: true, color: C.white, align: "center" });
}

// 18 — Fechamento
{
  const s = pptx.addSlide();
  bg(s, C.dark);
  darkHeader(s, "Fechamento", "Uma decisão segura antes de uma automação grande", "A solução começa pequena, deixa cada valor rastreável e cria uma base que a Barte pode levar para outros clientes.", 18, "Fechamento");
  const asks = [
    ["01", "Arquivos read-only", "Quais fontes entram no piloto e com qual frequência?", C.blue],
    ["02", "Ambiente aprovado", "Onde o runtime pode processar sem escrever no ERP?", C.purple],
    ["03", "Golden set", "Quem assina os casos e as políticas de exceção?", C.mint],
  ];
  asks.forEach((a, i) => {
    const y = 1.35 + i * 1.32;
    rr(s, 7.15, y, 5.15, 1.0, C.dark2, "39445A", 0.1);
    text(s, a[0], 7.45, y + 0.22, 0.55, 0.3, { fontSize: 19, bold: true, color: a[3] });
    text(s, a[1], 8.22, y + 0.18, 3.7, 0.25, { fontSize: 13, bold: true, color: C.white });
    text(s, a[2], 8.22, y + 0.55, 3.75, 0.22, { fontSize: 9.5, color: "AAB5C8" });
  });
  rr(s, 0.72, 5.78, 5.7, 0.58, C.mint, C.mint, 0.1);
  text(s, "Identidade antes do matching. Evidência antes da ação.", 0.95, 5.96, 5.25, 0.22, { fontSize: 12.5, bold: true, color: C.dark, align: "center" });
  text(s, "Referência de posicionamento e identidade visual: barte.com", 0.75, 6.65, 5.2, 0.2, { fontSize: 8.5, color: "9AA6BA" });
  footer(s, "Fechamento", 18, true);
}

const outPath = path.join(__dirname, "VantaraConcilia_Solucao_Barte.pptx");
pptx.writeFile({ fileName: outPath }).then(() => {
  console.log("PPTX gerado: " + outPath);
}).catch((err) => {
  console.error(err);
  process.exit(1);
});

