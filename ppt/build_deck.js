const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5

// ===== THEME: Barte-inspired dark premium =====
const THEME = {
  name: "Barte Concilia",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1A2E",  // dark navy (text on light)
    lt1: "FFFFFF",  // white (text on dark)
    dk2: "3D3D5C",  // secondary dark
    lt2: "F0F0F5",  // light gray bg
    accent1: "6C3FC5", // Barte purple
    accent2: "00D4AA", // Barte green/teal
    accent3: "FF6B6B", // coral for alerts
    accent4: "FFB84D", // amber for warnings
    accent5: "4ECDC4", // seafoam
    accent6: "2D2D44", // dark card bg
    hlink: "6C3FC5",
    folHlink: "3D3D5C",
  },
};

pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

const C = pres.SchemeColor;

// Colors
const DARK_BG = "1A1A2E";
const DARK_CARD = "2D2D44";
const PURPLE = "6C3FC5";
const GREEN = "00D4AA";
const CORAL = "FF6B6B";
const AMBER = "FFB84D";
const WHITE = "FFFFFF";
const LIGHT_BG = "F0F0F5";
const LIGHT_GRAY = "E0E0E8";
const TEXT_DARK = "1A1A2E";
const TEXT_MUTED = "8888AA";

// ===== LAYOUTS =====
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: DARK_BG },
  objects: [
    { rect: { x: 0, y: 6.8, w: 13.33, h: 0.7, fill: { color: DARK_CARD } } },
    { text: { text: "BARTE AI SERVICES", options: { x: 0.5, y: 6.9, w: 5, h: 0.4, fontSize: 10, color: TEXT_MUTED, isTextBox: true, margin: 0 } } },
    { text: { text: "Confidencial", options: { x: 8, y: 6.9, w: 5, h: 0.4, fontSize: 10, color: TEXT_MUTED, align: "right", isTextBox: true, margin: 0 } } },
  ],
  slideNumber: { x: 12.5, y: 7.0, color: TEXT_MUTED, fontSize: 9 },
});

pres.defineSlideMaster({
  title: "CONTENT_LIGHT",
  background: { color: WHITE },
  objects: [
    { rect: { x: 0, y: 0, w: 13.33, h: 0.08, fill: { color: PURPLE } } },
    { rect: { x: 0, y: 6.8, w: 13.33, h: 0.7, fill: { color: LIGHT_BG } } },
    { text: { text: "BARTE AI SERVICES  |  Vantara Concilia", options: { x: 0.5, y: 6.9, w: 6, h: 0.4, fontSize: 9, color: TEXT_MUTED, isTextBox: true, margin: 0 } } },
  ],
  slideNumber: { x: 12.5, y: 7.0, color: TEXT_MUTED, fontSize: 9 },
});

pres.defineSlideMaster({
  title: "SECTION_DARK",
  background: { color: DARK_BG },
  objects: [
    { rect: { x: 0.8, y: 3.2, w: 1.5, h: 0.06, fill: { color: GREEN } } },
  ],
  slideNumber: { x: 12.5, y: 7.0, color: TEXT_MUTED, fontSize: 9 },
});

// ===== SECTIONS & SLIDES =====

// ---------- SLIDE 1: Cover ----------
pres.addSection({ title: "Abertura" });
let slide = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Abertura" });

slide.addText("VANTARA\nCONCILIA", {
  x: 0.8, y: 1.5, w: 6, h: 2.5,
  fontSize: 54, bold: true, color: WHITE, lineSpacingMultiple: 0.9,
  isTextBox: true, margin: 0,
});
slide.addText("Motor de identidade para conciliação\nde recebíveis e controle de contas a pagar", {
  x: 0.8, y: 4.0, w: 7, h: 0.8,
  fontSize: 18, color: GREEN,
  isTextBox: true, margin: 0,
});
slide.addText("Case Vantara  |  Barte AI Services  |  Outubro 2026", {
  x: 0.8, y: 5.2, w: 7, h: 0.5,
  fontSize: 13, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// Decorative stats on right
const stats = [
  { num: "99,4%", label: "valor dos créditos vinculado" },
  { num: "R$ 50,5k", label: "exposição potencial" },
  { num: "46/46", label: "testes automatizados" },
];
stats.forEach((s, i) => {
  const yPos = 1.8 + i * 1.6;
  slide.addText(s.num, {
    x: 9, y: yPos, w: 3.5, h: 0.6,
    fontSize: 36, bold: true, color: PURPLE, align: "right",
    isTextBox: true, margin: 0,
  });
  slide.addText(s.label, {
    x: 9, y: yPos + 0.55, w: 3.5, h: 0.4,
    fontSize: 12, color: TEXT_MUTED, align: "right",
    isTextBox: true, margin: 0,
  });
});

// ---------- SLIDE 2: Executive Summary ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Abertura" });
slide.addText("Resumo executivo", {
  x: 0.8, y: 0.4, w: 10, h: 0.7,
  fontSize: 36, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

const execItems = [
  { icon: "01", title: "O diagnóstico", desc: "A fragmentação entre ERPs e bancos impede uma visão confiável de quem pagou o quê e cria risco de cobrança ou pagamento indevido." },
  { icon: "02", title: "A solução", desc: "Recebíveis primeiro: identidade antes do matching, propostas auditáveis e zero escrita no Protheus. IA é opcional e apenas residual." },
  { icon: "03", title: "O resultado do data pack", desc: "14/15 créditos vinculados (99,4% do valor), 8 propostas de alta confiança e R$ 50.528 de exposição potencial. Sem alegar perda confirmada." },
  { icon: "04", title: "O piloto", desc: "Executar no ambiente Vantara, medir precisão por faixa de confiança e só então decidir automação, expansão a AP e uso de IA." },
];

execItems.forEach((item, i) => {
  const yPos = 1.5 + i * 1.3;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: yPos, w: 0.7, h: 0.7,
    fill: { color: PURPLE }, rectRadius: 0.1,
  });
  slide.addText(item.icon, {
    x: 0.8, y: yPos, w: 0.7, h: 0.7,
    fontSize: 18, bold: true, color: WHITE, align: "center", valign: "middle",
    isTextBox: true, margin: 0,
  });
  slide.addText(item.title, {
    x: 1.8, y: yPos, w: 3.5, h: 0.4,
    fontSize: 16, bold: true, color: TEXT_DARK,
    isTextBox: true, margin: 0,
  });
  slide.addText(item.desc, {
    x: 1.8, y: yPos + 0.35, w: 10.5, h: 0.7,
    fontSize: 12, color: TEXT_MUTED,
    isTextBox: true, margin: 0,
  });
});

// ---------- SLIDE 3: O Diagnóstico ----------
pres.addSection({ title: "Diagnostico" });
slide = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Diagnostico" });
slide.addText("01", {
  x: 0.8, y: 2.0, w: 2, h: 0.8,
  fontSize: 48, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText("O Diagnóstico", {
  x: 0.8, y: 3.4, w: 8, h: 0.8,
  fontSize: 40, bold: true, color: WHITE,
  isTextBox: true, margin: 0,
});
slide.addText("Por que o problema não é matching — é identidade", {
  x: 0.8, y: 4.3, w: 8, h: 0.5,
  fontSize: 16, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// ---------- SLIDE 4: O problema de identidade ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Diagnostico" });
slide.addText("A mesma empresa, dois sistemas, duas identidades", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

// Protheus side
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 1.5, w: 5.5, h: 2.8,
  fill: { color: LIGHT_BG }, rectRadius: 0.15,
});
slide.addText("PROTHEUS (Sede)", {
  x: 1.2, y: 1.7, w: 4.5, h: 0.4,
  fontSize: 14, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText([
  { text: "Grão Nobre Comércio Ltda\n", options: { fontSize: 13, bold: true, color: TEXT_DARK } },
  { text: "CNPJ: 55.666.777/0001-44\n", options: { fontSize: 12, color: TEXT_MUTED } },
  { text: "NF 104580 — R$ 31.250,00\n", options: { fontSize: 12, color: TEXT_DARK } },
  { text: "Tipo: Produto | Venc: 20/07/2026", options: { fontSize: 11, color: TEXT_MUTED } },
], {
  x: 1.2, y: 2.2, w: 4.8, h: 1.8,
  isTextBox: true, margin: 0, valign: "top",
});

// Arrow
slide.addText("=", {
  x: 6.1, y: 2.5, w: 1, h: 0.8,
  fontSize: 36, bold: true, color: GREEN, align: "center",
  isTextBox: true, margin: 0,
});

// Omie side
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 7, y: 1.5, w: 5.5, h: 2.8,
  fill: { color: LIGHT_BG }, rectRadius: 0.15,
});
slide.addText("OMIE (Unidade Norte)", {
  x: 7.4, y: 1.7, w: 4.5, h: 0.4,
  fontSize: 14, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText([
  { text: "GRAO NOBRE COM LTDA\n", options: { fontSize: 13, bold: true, color: TEXT_DARK } },
  { text: "CNPJ: 55666777000144\n", options: { fontSize: 12, color: TEXT_MUTED } },
  { text: "FAT-2026-0331 — R$ 31.250,00\n", options: { fontSize: 12, color: TEXT_DARK } },
  { text: "Tipo: Produto | Venc: 20/07/2026", options: { fontSize: 11, color: TEXT_MUTED } },
], {
  x: 7.4, y: 2.2, w: 4.8, h: 1.8,
  isTextBox: true, margin: 0, valign: "top",
});

// Result box
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 4.7, w: 11.7, h: 2,
  fill: { color: "FFF3CD" }, rectRadius: 0.15,
});
slide.addText([
  { text: "Hipótese que exige validação:\n", options: { fontSize: 14, bold: true, color: TEXT_DARK } },
  { text: "CNPJ, valor e vencimento coincidem em dois ERPs. É forte indício de duplicidade, não prova da mesma obrigação.\nAção segura: suspender a cobrança por até 48h e conferir os documentos de origem.", options: { fontSize: 12, color: "7A6500" } },
], {
  x: 1.2, y: 4.9, w: 11, h: 1.6,
  isTextBox: true, margin: 0, valign: "top",
});

// ---------- SLIDE 5: Volumetria do problema ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Diagnostico" });
slide.addText("O tamanho do problema", {
  x: 0.8, y: 0.4, w: 10, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

// Decomposição do gap
const gapItems = [
  { valor: "R$ 101.870", label: "Aberto ao final", desc: "Após aplicar os vínculos propostos", color: CORAL },
  { valor: "R$ 31.250", label: "Sob validação", desc: "Possível duplicidade cross-ERP", color: AMBER },
  { valor: "R$ 62.500", label: "Pagamento parcial", desc: "Saldo remanescente cobrável", color: PURPLE },
  { valor: "R$ 8.120", label: "Sem match no extrato", desc: "Validar outros bancos antes de cobrar", color: GREEN },
];

gapItems.forEach((item, i) => {
  const xPos = 0.8 + i * 3.1;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: xPos, y: 1.5, w: 2.8, h: 2.5,
    fill: { color: LIGHT_BG }, rectRadius: 0.15,
  });
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: xPos + 0.3, y: 1.8, w: 0.6, h: 0.6,
    fill: { color: item.color }, rectRadius: 0.1,
  });
  slide.addText(item.valor, {
    x: xPos, y: 2.6, w: 2.8, h: 0.5,
    fontSize: 20, bold: true, color: TEXT_DARK, align: "center",
    isTextBox: true, margin: 0,
  });
  slide.addText(item.label, {
    x: xPos, y: 3.1, w: 2.8, h: 0.4,
    fontSize: 13, bold: true, color: item.color, align: "center",
    isTextBox: true, margin: 0,
  });
  slide.addText(item.desc, {
    x: xPos, y: 3.5, w: 2.8, h: 0.4,
    fontSize: 11, color: TEXT_MUTED, align: "center",
    isTextBox: true, margin: 0,
  });
});

slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 4.5, w: 11.7, h: 1.8,
  fill: { color: DARK_BG }, rectRadius: 0.15,
});
slide.addText([
  { text: "A métrica que muda a decisão: ", options: { fontSize: 14, bold: true, color: WHITE } },
  { text: "não apenas quanto está em aberto, mas por que está em aberto.\nO data pack contém uma de quatro contas bancárias; ausência de match não prova inadimplência.", options: { fontSize: 13, color: LIGHT_GRAY } },
], {
  x: 1.2, y: 4.7, w: 11, h: 1.4,
  isTextBox: true, margin: 0, valign: "middle",
});

// ---------- SLIDE 6: Architecture Section ----------
pres.addSection({ title: "Arquitetura" });
slide = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Arquitetura" });
slide.addText("02", {
  x: 0.8, y: 2.0, w: 2, h: 0.8,
  fontSize: 48, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText("A Arquitetura", {
  x: 0.8, y: 3.4, w: 8, h: 0.8,
  fontSize: 40, bold: true, color: WHITE,
  isTextBox: true, margin: 0,
});
slide.addText("Identidade primeiro, matching depois", {
  x: 0.8, y: 4.3, w: 8, h: 0.5,
  fontSize: 16, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// ---------- SLIDE 7: Pipeline 7 etapas ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Arquitetura" });
slide.addText("Pipeline em 7 etapas sequenciais", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

const etapas = [
  { num: "1", nome: "Ingestão", desc: "4 adapters, tudo vira schema canônico", cor: PURPLE },
  { num: "2", nome: "Identidade", desc: "Entidades unificadas entre ERPs", cor: PURPLE },
  { num: "3", nome: "Colisões", desc: "Possíveis duplicidades cross-ERP", cor: AMBER },
  { num: "4", nome: "Conciliação AR", desc: "Cascata de 5 passes", cor: GREEN },
  { num: "5", nome: "Contas a Pagar", desc: "Detecção de duplicidade", cor: CORAL },
  { num: "6", nome: "Conferência", desc: "2 invariantes ao centavo", cor: GREEN },
  { num: "7", nome: "Saídas", desc: "CSVs + relatório HTML", cor: TEXT_MUTED },
];

etapas.forEach((e, i) => {
  const yPos = 1.4 + i * 0.75;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: yPos, w: 0.55, h: 0.55,
    fill: { color: e.cor }, rectRadius: 0.08,
  });
  slide.addText(e.num, {
    x: 0.8, y: yPos, w: 0.55, h: 0.55,
    fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle",
    isTextBox: true, margin: 0,
  });
  slide.addText(e.nome, {
    x: 1.6, y: yPos, w: 3, h: 0.35,
    fontSize: 15, bold: true, color: TEXT_DARK,
    isTextBox: true, margin: 0,
  });
  slide.addText(e.desc, {
    x: 1.6, y: yPos + 0.3, w: 4.5, h: 0.3,
    fontSize: 11, color: TEXT_MUTED,
    isTextBox: true, margin: 0,
  });
  // Connecting line
  if (i < etapas.length - 1) {
    slide.addShape(pres.shapes.LINE, {
      x: 1.07, y: yPos + 0.55, w: 0, h: 0.2,
      line: { color: LIGHT_GRAY, width: 2 },
    });
  }
});

// Right side: key insight
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 7, y: 1.4, w: 5.5, h: 5,
  fill: { color: DARK_BG }, rectRadius: 0.15,
});
slide.addText("Por que essa ordem?", {
  x: 7.4, y: 1.7, w: 4.8, h: 0.4,
  fontSize: 16, bold: true, color: GREEN,
  isTextBox: true, margin: 0,
});
slide.addText([
  { text: "Identidade antes do matching\n", options: { fontSize: 13, bold: true, color: WHITE } },
  { text: "Para que um título duplicado não seja silenciosamente \"resolvido\" e o gêmeo vá para inadimplência.\n\n", options: { fontSize: 12, color: LIGHT_GRAY } },
  { text: "Colisões antes da conciliação\n", options: { fontSize: 13, bold: true, color: WHITE } },
  { text: "Possíveis duplicidades saem temporariamente da cobrança e vão para validação documental. O motor não baixa o título por inferência.\n\n", options: { fontSize: 12, color: LIGHT_GRAY } },
  { text: "Conferência ao final\n", options: { fontSize: 13, bold: true, color: WHITE } },
  { text: "Se as invariantes não fecham, o pipeline aborta. Elas provam conservação aritmética; precisão dos vínculos é medida por auditoria.", options: { fontSize: 12, color: LIGHT_GRAY } },
], {
  x: 7.4, y: 2.3, w: 4.8, h: 3.8,
  isTextBox: true, margin: 0, valign: "top",
});

// ---------- SLIDE 8: Cascata de confiança ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Arquitetura" });
slide.addText("Cascata de confiança — 5 passes", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});
slide.addText("Do mais confiável ao mais fraco. O primeiro que casa, para.", {
  x: 0.8, y: 1.0, w: 10, h: 0.4,
  fontSize: 14, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

const tiers = [
  { pass: "1. Nosso Número", conf: "0.99", qtd: "5", cor: GREEN, desc: "Campo documento do extrato = nosso_numero do boleto" },
  { pass: "2. CNPJ no Texto", conf: "0.95", qtd: "2", cor: GREEN, desc: "14 dígitos do CNPJ extraídos do histórico por regex" },
  { pass: "3. Nome da Empresa", conf: "0.88", qtd: "6", cor: PURPLE, desc: "Tokens do nome no histórico truncado, com tratamento de abreviação" },
  { pass: "4. IA (Desempate)", conf: "0.85", qtd: "0", cor: AMBER, desc: "Lista fechada de candidatos para o modelo. Teto de confiança." },
  { pass: "5. Só Valor", conf: "0.45", qtd: "1", cor: CORAL, desc: "Casou apenas por valor. Nunca automático." },
];

tiers.forEach((t, i) => {
  const yPos = 1.7 + i * 1.0;
  const barW = parseFloat(t.conf) * 9;

  // Background bar
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: yPos, w: 9, h: 0.5,
    fill: { color: LIGHT_BG }, rectRadius: 0.05,
  });
  // Fill bar
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: yPos, w: barW, h: 0.5,
    fill: { color: t.cor, transparency: 80 }, rectRadius: 0.05,
  });
  // Label
  slide.addText(t.pass, {
    x: 1.0, y: yPos, w: 4, h: 0.5,
    fontSize: 13, bold: true, color: TEXT_DARK, valign: "middle",
    isTextBox: true, margin: 0,
  });
  // Conf value
  slide.addText(t.conf, {
    x: 10.0, y: yPos, w: 1, h: 0.5,
    fontSize: 16, bold: true, color: t.cor, align: "center", valign: "middle",
    isTextBox: true, margin: 0,
  });
  // Qty
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 11.3, y: yPos + 0.05, w: 1.2, h: 0.4,
    fill: { color: t.cor }, rectRadius: 0.08,
  });
  slide.addText(`${t.qtd} caso(s)`, {
    x: 11.3, y: yPos + 0.05, w: 1.2, h: 0.4,
    fontSize: 11, bold: true, color: WHITE, align: "center", valign: "middle",
    isTextBox: true, margin: 0,
  });
  // Description
  slide.addText(t.desc, {
    x: 1.0, y: yPos + 0.5, w: 10, h: 0.35,
    fontSize: 10, color: TEXT_MUTED,
    isTextBox: true, margin: 0,
  });
});

// ---------- SLIDE 9: Dois eixos ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Arquitetura" });
slide.addText("Dois eixos independentes", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

// Eixo Identidade
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 1.4, w: 5.8, h: 4.5,
  fill: { color: LIGHT_BG }, rectRadius: 0.15,
});
slide.addText("Eixo Identidade", {
  x: 1.2, y: 1.6, w: 5, h: 0.5,
  fontSize: 18, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText("De quem é esse dinheiro?", {
  x: 1.2, y: 2.1, w: 5, h: 0.3,
  fontSize: 13, italic: true, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});
slide.addText([
  { text: "ID_BANCARIO", options: { fontSize: 12, bold: true, color: GREEN } },
  { text: " → nosso_numero\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "CNPJ_TEXTO", options: { fontSize: 12, bold: true, color: GREEN } },
  { text: " → CNPJ no histórico\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "NOME_FORTE", options: { fontSize: 12, bold: true, color: PURPLE } },
  { text: " → tokens completos\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "NOME_PARCIAL", options: { fontSize: 12, bold: true, color: AMBER } },
  { text: " → cobertura parcial\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "IA", options: { fontSize: 12, bold: true, color: AMBER } },
  { text: " → desempate por modelo\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "SO_VALOR", options: { fontSize: 12, bold: true, color: CORAL } },
  { text: " → sem identidade", options: { fontSize: 11, color: TEXT_MUTED } },
], {
  x: 1.2, y: 2.6, w: 5, h: 3,
  isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.3,
});

// Eixo Valor
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 7, y: 1.4, w: 5.8, h: 4.5,
  fill: { color: LIGHT_BG }, rectRadius: 0.15,
});
slide.addText("Eixo Valor", {
  x: 7.4, y: 1.6, w: 5, h: 0.5,
  fontSize: 18, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText("Por que o valor difere?", {
  x: 7.4, y: 2.1, w: 5, h: 0.3,
  fontSize: 13, italic: true, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});
slide.addText([
  { text: "EXATO", options: { fontSize: 12, bold: true, color: GREEN } },
  { text: " → centavo a centavo\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "AGREGADO", options: { fontSize: 12, bold: true, color: GREEN } },
  { text: " → 1 crédito = N títulos\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "RETENÇÃO", options: { fontSize: 12, bold: true, color: PURPLE } },
  { text: " → hipótese; exige documento fiscal\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "MORA", options: { fontSize: 12, bold: true, color: PURPLE } },
  { text: " → hipótese; exige contrato/cálculo\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "PARCIAL", options: { fontSize: 12, bold: true, color: AMBER } },
  { text: " → saldo permanece cobrável\n", options: { fontSize: 11, color: TEXT_MUTED } },
  { text: "INEXPLICADO", options: { fontSize: 12, bold: true, color: CORAL } },
  { text: " → decisão humana", options: { fontSize: 11, color: TEXT_MUTED } },
], {
  x: 7.4, y: 2.6, w: 5, h: 3,
  isTextBox: true, margin: 0, valign: "top", lineSpacingMultiple: 1.3,
});

// ---------- SLIDE 10: Contas a Pagar ----------
pres.addSection({ title: "Contas a Pagar" });
slide = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Contas a Pagar" });
slide.addText("03", {
  x: 0.8, y: 2.0, w: 2, h: 0.8,
  fontSize: 48, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText("Contas a Pagar", {
  x: 0.8, y: 3.4, w: 8, h: 0.8,
  fontSize: 40, bold: true, color: WHITE,
  isTextBox: true, margin: 0,
});
slide.addText("A cobrança de R$ 19.278 sob bloqueio", {
  x: 0.8, y: 4.3, w: 8, h: 0.5,
  fontSize: 16, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// ---------- SLIDE 11: Caso São Jorge ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Contas a Pagar" });
slide.addText("Caso São Jorge — condição de risco de duplicidade", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 26, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

const timeline = [
  { data: "06/07", evento: "São Jorge envia NF 88231 — R$ 18.900", tipo: "normal" },
  { data: "06/07", evento: "WhatsApp: Rafael confirma recebimento com \"acho que sim\"", tipo: "warning" },
  { data: "18/07", evento: "São Jorge reemite boleto: R$ 19.278 (NF 088231, outro venc.)", tipo: "danger" },
  { data: "19/07", evento: "Camila vê pagamento AGENDADO e lê como já pago", tipo: "danger" },
  { data: "20/07", evento: "Débito real: R$ 18.900 sai da conta", tipo: "normal" },
  { data: "25/07", evento: "Boleto de R$ 19.278 continua vivo e pagável", tipo: "danger" },
];

timeline.forEach((t, i) => {
  const yPos = 1.3 + i * 0.85;
  const cores = { normal: GREEN, warning: AMBER, danger: CORAL };
  const cor = cores[t.tipo];

  // Date badge
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.8, y: yPos, w: 1.2, h: 0.5,
    fill: { color: cor }, rectRadius: 0.08,
  });
  slide.addText(t.data, {
    x: 0.8, y: yPos, w: 1.2, h: 0.5,
    fontSize: 12, bold: true, color: WHITE, align: "center", valign: "middle",
    isTextBox: true, margin: 0,
  });
  slide.addText(t.evento, {
    x: 2.2, y: yPos, w: 10.5, h: 0.5,
    fontSize: 13, color: TEXT_DARK, valign: "middle",
    isTextBox: true, margin: 0,
  });
  // Connector
  if (i < timeline.length - 1) {
    slide.addShape(pres.shapes.LINE, {
      x: 1.4, y: yPos + 0.5, w: 0, h: 0.35,
      line: { color: LIGHT_GRAY, width: 2 },
    });
  }
});

// ---------- SLIDE 12: Exposição financeira ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Contas a Pagar" });
slide.addText("Exposição financeira classificada", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

// Big numbers
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 1.4, w: 5.8, h: 3,
  fill: { color: CORAL, transparency: 92 }, rectRadius: 0.15,
});
slide.addText("Perda confirmada", {
  x: 1.2, y: 1.7, w: 5, h: 0.4,
  fontSize: 14, bold: true, color: CORAL,
  isTextBox: true, margin: 0,
});
slide.addText("R$ 0", {
  x: 1.2, y: 2.3, w: 5, h: 1,
  fontSize: 48, bold: true, color: CORAL,
  isTextBox: true, margin: 0,
});
slide.addText("Nenhuma perda materializada foi comprovada\ncom os documentos do data pack.", {
  x: 1.2, y: 3.4, w: 5, h: 0.7,
  fontSize: 12, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 7, y: 1.4, w: 5.8, h: 3,
  fill: { color: AMBER, transparency: 92 }, rectRadius: 0.15,
});
slide.addText("Exposição potencial", {
  x: 7.4, y: 1.7, w: 5, h: 0.4,
  fontSize: 14, bold: true, color: AMBER,
  isTextBox: true, margin: 0,
});
slide.addText("R$ 50.528", {
  x: 7.4, y: 2.3, w: 5, h: 1,
  fontSize: 48, bold: true, color: AMBER,
  isTextBox: true, margin: 0,
});
slide.addText("Possível duplicidade em AR e AP.\nBloquear ou suspender até validação.", {
  x: 7.4, y: 3.4, w: 5, h: 0.7,
  fontSize: 12, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 4.8, w: 11.7, h: 1.5,
  fill: { color: DARK_BG }, rectRadius: 0.15,
});
slide.addText([
  { text: "R$ 34.117,82 adicionais estão sem controle documental. ", options: { fontSize: 13, bold: true, color: WHITE } },
  { text: "Os alertas compartilham grupos de exposição para não contar o mesmo dinheiro duas vezes. Potencial não é perda: a validação humana fecha a classificação.", options: { fontSize: 12, color: LIGHT_GRAY } },
], {
  x: 1.2, y: 5.0, w: 11, h: 1.1,
  isTextBox: true, margin: 0, valign: "top",
});

// ---------- SLIDE 13: Escala Section ----------
pres.addSection({ title: "Escala" });
slide = pres.addSlide({ masterName: "SECTION_DARK", sectionTitle: "Escala" });
slide.addText("04", {
  x: 0.8, y: 2.0, w: 2, h: 0.8,
  fontSize: 48, bold: true, color: PURPLE,
  isTextBox: true, margin: 0,
});
slide.addText("Em Escala", {
  x: 0.8, y: 3.4, w: 8, h: 0.8,
  fontSize: 40, bold: true, color: WHITE,
  isTextBox: true, margin: 0,
});
slide.addText("De 17 títulos para 1.900 por mês", {
  x: 0.8, y: 4.3, w: 8, h: 0.5,
  fontSize: 16, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// ---------- SLIDE 14: Comparações em escala ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Escala" });
slide.addText("Identidade limita o espaço de busca", {
  x: 0.8, y: 0.4, w: 12, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});

// Sem identidade
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 1.5, w: 5.8, h: 3.5,
  fill: { color: CORAL, transparency: 92 }, rectRadius: 0.15,
});
slide.addText("Sem camada de identidade", {
  x: 1.2, y: 1.7, w: 5, h: 0.4,
  fontSize: 14, bold: true, color: CORAL,
  isTextBox: true, margin: 0,
});
slide.addText("3.230.000*", {
  x: 1.2, y: 2.4, w: 5, h: 0.8,
  fontSize: 44, bold: true, color: CORAL,
  isTextBox: true, margin: 0,
});
slide.addText("comparações por mês", {
  x: 1.2, y: 3.2, w: 5, h: 0.3,
  fontSize: 13, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});
slide.addText("1.700 créditos x 1.900 títulos\nCada crédito testa contra TODOS os títulos", {
  x: 1.2, y: 3.7, w: 5, h: 0.8,
  fontSize: 12, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// Com identidade
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 7, y: 1.5, w: 5.8, h: 3.5,
  fill: { color: GREEN, transparency: 92 }, rectRadius: 0.15,
});
slide.addText("Com camada de identidade", {
  x: 7.4, y: 1.7, w: 5, h: 0.4,
  fontSize: 14, bold: true, color: GREEN,
  isTextBox: true, margin: 0,
});
slide.addText("~8.500*", {
  x: 7.4, y: 2.4, w: 5, h: 0.8,
  fontSize: 44, bold: true, color: GREEN,
  isTextBox: true, margin: 0,
});
slide.addText("comparações por mês", {
  x: 7.4, y: 3.2, w: 5, h: 0.3,
  fontSize: 13, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});
slide.addText("1.700 créditos x ~5 títulos/entidade\nCada crédito testa contra os títulos DA SUA ENTIDADE", {
  x: 7.4, y: 3.7, w: 5, h: 0.8,
  fontSize: 12, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

// IA cost projection
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 0.8, y: 5.3, w: 11.7, h: 1.2,
  fill: { color: LIGHT_BG }, rectRadius: 0.15,
});
slide.addText([
  { text: "* Cenário ilustrativo, não resultado do piloto.  ", options: { fontSize: 13, bold: true, color: TEXT_DARK } },
  { text: "1.700 créditos × 1.900 títulos versus 5 candidatos por entidade. Volume residual, precisão, latência e custo de IA serão medidos nos 30 dias.", options: { fontSize: 12, color: TEXT_MUTED } },
], {
  x: 1.2, y: 5.5, w: 11, h: 0.8,
  isTextBox: true, margin: 0, valign: "middle",
});

// ---------- SLIDE 15: Config não código ----------
slide = pres.addSlide({ masterName: "CONTENT_LIGHT", sectionTitle: "Escala" });
slide.addText("Operação segura no ambiente Vantara", {
  x: 0.8, y: 0.4, w: 10, h: 0.7,
  fontSize: 30, bold: true, color: TEXT_DARK,
  isTextBox: true, margin: 0,
});
slide.addText("Código reutilizável da Barte; dados e execução sob controle da Vantara", {
  x: 0.8, y: 1.0, w: 10, h: 0.4,
  fontSize: 14, color: TEXT_MUTED,
  isTextBox: true, margin: 0,
});

const configItems = [
  { titulo: "Runtime", items: ["Container assinado pela Barte", "Executado na conta cloud Vantara", "Leitura de exportações", "Egress bloqueado por padrão", "Chaves no KMS da Vantara"] },
  { titulo: "Travas do piloto", items: ["Zero escrita no Protheus por 90 dias", "CSVs são propostas genéricas", "Importação nativa exige homologação", "Logs e trilha de evidência", "Rollback = não publicar o lote"] },
  { titulo: "Governança de IA", items: ["IA desligada por padrão", "Somente endpoint aprovado/local", "Sem dados brutos em SaaS externo", "Exceção exige aprovação formal", "Humano confirma divergências"] },
];

configItems.forEach((item, i) => {
  const xPos = 0.8 + i * 4.1;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: xPos, y: 1.6, w: 3.8, h: 4.5,
    fill: { color: LIGHT_BG }, rectRadius: 0.15,
  });
  slide.addText(item.titulo, {
    x: xPos + 0.3, y: 1.8, w: 3.2, h: 0.5,
    fontSize: 14, bold: true, color: PURPLE,
    isTextBox: true, margin: 0,
  });
  item.items.forEach((it, j) => {
    slide.addText(`${it}`, {
      x: xPos + 0.3, y: 2.5 + j * 0.5, w: 3.2, h: 0.4,
      fontSize: 11, color: TEXT_DARK, bullet: true,
      isTextBox: true, margin: 0,
    });
  });
});

// ---------- SLIDE 16: Resultado ----------
pres.addSection({ title: "Resultado" });
slide = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Resultado" });

slide.addText("Resultado", {
  x: 0.8, y: 0.6, w: 8, h: 0.7,
  fontSize: 36, bold: true, color: WHITE,
  isTextBox: true, margin: 0,
});

// KPI grid
const kpis = [
  { valor: "14/15", label: "Créditos vinculados", sub: "99,4% do valor analisado" },
  { valor: "48,4%", label: "Alta confiança", sub: "8 propostas; sem escrita no ERP" },
  { valor: "R$ 50.528", label: "Exposição potencial", sub: "Perda confirmada: R$ 0" },
  { valor: "46/46", label: "Testes verdes", sub: "Inclui limites e casos de estresse" },
  { valor: "0", label: "Chamadas à IA", sub: "Cascata determinística resolveu tudo" },
  { valor: "2/2", label: "Invariantes aritméticas", sub: "Precisão semântica será auditada" },
];

kpis.forEach((k, i) => {
  const col = i % 3;
  const row = Math.floor(i / 3);
  const xPos = 0.8 + col * 4.1;
  const yPos = 1.6 + row * 2.5;

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: xPos, y: yPos, w: 3.8, h: 2.2,
    fill: { color: DARK_CARD }, rectRadius: 0.15,
  });
  slide.addText(k.valor, {
    x: xPos, y: yPos + 0.3, w: 3.8, h: 0.8,
    fontSize: 32, bold: true, color: GREEN, align: "center",
    isTextBox: true, margin: 0,
  });
  slide.addText(k.label, {
    x: xPos, y: yPos + 1.1, w: 3.8, h: 0.4,
    fontSize: 13, bold: true, color: WHITE, align: "center",
    isTextBox: true, margin: 0,
  });
  slide.addText(k.sub, {
    x: xPos, y: yPos + 1.5, w: 3.8, h: 0.4,
    fontSize: 11, color: TEXT_MUTED, align: "center",
    isTextBox: true, margin: 0,
  });
});

// ---------- SLIDE 17: Closing ----------
slide = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Resultado" });

slide.addText("VANTARA\nCONCILIA", {
  x: 0.8, y: 1.5, w: 6, h: 2,
  fontSize: 48, bold: true, color: WHITE, lineSpacingMultiple: 0.9,
  isTextBox: true, margin: 0,
});

slide.addText([
  { text: "A Vantara pediu uma IA que bate pagamento.\n", options: { fontSize: 16, color: LIGHT_GRAY } },
  { text: "O protótipo indica que o gargalo começa na identidade —\ne precisa ser provado em um piloto controlado.", options: { fontSize: 16, bold: true, color: GREEN } },
], {
  x: 0.8, y: 3.5, w: 8, h: 1.5,
  isTextBox: true, margin: 0,
});

slide.addText([
  { text: "barte.com", options: { fontSize: 14, color: PURPLE, bold: true } },
  { text: "  |  AI Services  |  Outubro 2026", options: { fontSize: 14, color: TEXT_MUTED } },
], {
  x: 0.8, y: 5.5, w: 8, h: 0.5,
  isTextBox: true, margin: 0,
});

// ===== WRITE =====
const outPath = path.join(__dirname, "VantaraConcilia_Barte.pptx");

(async () => {
  await pres.writeFile({ fileName: outPath });
  console.log("PPTX gerado: " + outPath);
})();
