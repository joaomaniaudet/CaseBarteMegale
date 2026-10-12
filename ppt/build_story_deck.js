const pptxgen = require("pptxgenjs");
const path = require("path");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Barte AI Services";
pptx.subject = "Case Vantara — solução e arquitetura";
pptx.title = "Vantara Concilia — o dinheiro entra, a identidade não se perde";
pptx.company = "Barte";
pptx.lang = "pt-BR";
pptx.theme = {
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  lang: "pt-BR",
};

const W = 13.333;
const H = 7.5;
const C = {
  ink: "172033",
  muted: "64748B",
  paper: "F7F8FC",
  white: "FFFFFF",
  purple: "6D4AFF",
  purpleSoft: "EEEAFE",
  mint: "21C7A8",
  mintSoft: "DDF8F1",
  coral: "FF6B6B",
  coralSoft: "FFE8E8",
  amber: "F4B740",
  amberSoft: "FFF3D6",
  blue: "3B82F6",
  blueSoft: "E7F0FF",
  line: "DDE3EE",
  dark: "101522",
  darkCard: "20283A",
};

const SH = pptx.ShapeType;

function addBg(slide, color = C.paper) {
  slide.background = { color };
}

function addFooter(slide, section, number, dark = false) {
  const color = dark ? "9AA6BA" : C.muted;
  slide.addText(`BARTE AI SERVICES  /  ${section.toUpperCase()}`, {
    x: 0.55, y: 7.12, w: 5.7, h: 0.18,
    fontFace: "Arial", fontSize: 8, color, margin: 0,
    charSpacing: 0.8,
  });
  slide.addText(String(number).padStart(2, "0"), {
    x: 12.25, y: 7.08, w: 0.5, h: 0.22,
    fontFace: "Arial", fontSize: 9, bold: true, color,
    align: "right", margin: 0,
  });
}

function addHeader(slide, kicker, title, subtitle, number, section = "Vantara Concilia") {
  slide.addText(kicker.toUpperCase(), {
    x: 0.65, y: 0.34, w: 4.3, h: 0.22,
    fontSize: 9, bold: true, color: C.purple, charSpacing: 1.5, margin: 0,
  });
  slide.addText(title, {
    x: 0.65, y: 0.62, w: 12.0, h: 0.58,
    fontSize: 28, bold: true, color: C.ink, margin: 0,
    breakLine: false, fit: "shrink",
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.65, y: 1.22, w: 11.8, h: 0.42,
      fontSize: 12.5, color: C.muted, margin: 0,
      fit: "shrink",
    });
  }
  addFooter(slide, section, number);
}

function roundRect(slide, x, y, w, h, fill, line = fill, radius = 0.12) {
  slide.addShape(SH.roundRect, {
    x, y, w, h,
    rectRadius: radius,
    fill: { color: fill },
    line: { color: line, width: 1 },
  });
}

function pill(slide, text, x, y, w, fill, color = C.ink) {
  roundRect(slide, x, y, w, 0.34, fill, fill, 0.16);
  slide.addText(text, {
    x, y: y + 0.02, w, h: 0.26,
    fontSize: 9, bold: true, color, align: "center", valign: "mid", margin: 0,
  });
}

function card(slide, { x, y, w, h, title, body, fill = C.white, accent = C.purple, value, small }) {
  roundRect(slide, x, y, w, h, fill, C.line);
  slide.addShape(SH.rect, {
    x, y, w: 0.08, h,
    fill: { color: accent }, line: { color: accent },
  });
  if (value) {
    slide.addText(value, {
      x: x + 0.28, y: y + 0.22, w: w - 0.5, h: 0.55,
      fontSize: 23, bold: true, color: accent, margin: 0,
      fit: "shrink",
    });
    slide.addText(title, {
      x: x + 0.28, y: y + 0.82, w: w - 0.5, h: 0.34,
      fontSize: 11, bold: true, color: C.ink, margin: 0,
    });
    slide.addText(body, {
      x: x + 0.28, y: y + 1.2, w: w - 0.5, h: h - 1.4,
      fontSize: small ? 9 : 10, color: C.muted, margin: 0,
      valign: "top", fit: "shrink",
    });
  } else {
    slide.addText(title, {
      x: x + 0.28, y: y + 0.22, w: w - 0.5, h: 0.4,
      fontSize: 13, bold: true, color: C.ink, margin: 0,
      fit: "shrink",
    });
    slide.addText(body, {
      x: x + 0.28, y: y + 0.72, w: w - 0.5, h: h - 0.92,
      fontSize: small ? 9.3 : 10.5, color: C.muted, margin: 0,
      valign: "top", breakLine: false, fit: "shrink",
    });
  }
}

function circleNumber(slide, n, x, y, fill = C.purple, size = 0.48) {
  slide.addShape(SH.ellipse, {
    x, y, w: size, h: size,
    fill: { color: fill }, line: { color: fill },
  });
  slide.addText(String(n), {
    x, y: y + 0.01, w: size, h: size - 0.02,
    fontSize: 13, bold: true, color: C.white, align: "center", valign: "mid", margin: 0,
  });
}

function arrow(slide, x, y, w, color = C.purple) {
  slide.addShape(SH.chevron, {
    x, y, w, h: 0.34,
    fill: { color }, line: { color },
  });
}

function miniFile(slide, x, y, w, h, label, rows, color) {
  roundRect(slide, x, y, w, h, C.white, C.line);
  slide.addShape(SH.rect, {
    x, y, w, h: 0.38,
    fill: { color }, line: { color },
  });
  slide.addText(label, {
    x: x + 0.12, y: y + 0.08, w: w - 0.24, h: 0.2,
    fontSize: 9.5, bold: true, color: C.white, margin: 0,
  });
  rows.forEach((r, i) => {
    slide.addShape(SH.line, {
      x: x + 0.15, y: y + 0.66 + i * 0.34, w: w - 0.3, h: 0,
      line: { color: i === rows.length - 1 ? "FFFFFF" : C.line, width: 0.8 },
    });
    slide.addText(r, {
      x: x + 0.15, y: y + 0.46 + i * 0.34, w: w - 0.3, h: 0.18,
      fontSize: 7.8, color: C.muted, margin: 0, fit: "shrink",
    });
  });
}

// 1 — Cover
{
  const s = pptx.addSlide();
  addBg(s, C.dark);
  s.addShape(SH.ellipse, {
    x: 8.45, y: 0.75, w: 3.65, h: 3.65,
    fill: { color: C.purple, transparency: 12 }, line: { color: C.purple },
  });
  s.addShape(SH.ellipse, {
    x: 9.25, y: 1.55, w: 2.05, h: 2.05,
    fill: { color: C.mint }, line: { color: C.mint },
  });
  s.addText("R$", {
    x: 9.25, y: 2.03, w: 2.05, h: 0.76,
    fontSize: 42, bold: true, color: C.dark, align: "center", margin: 0,
  });
  [
    { t: "PROTHEUS", x: 7.5, y: 4.65, c: C.purple },
    { t: "OMIE", x: 9.35, y: 5.15, c: C.blue },
    { t: "BANCO", x: 11.05, y: 4.55, c: C.mint },
  ].forEach((a) => pill(s, a.t, a.x, a.y, 1.45, a.c, C.white));
  s.addShape(SH.line, { x: 9.75, y: 4.2, w: -1.1, h: 0.5, line: { color: "64748B", width: 2, dash: "dash" } });
  s.addShape(SH.line, { x: 10.15, y: 4.2, w: 0, h: 0.92, line: { color: "64748B", width: 2, dash: "dash" } });
  s.addShape(SH.line, { x: 10.55, y: 4.15, w: 1.2, h: 0.42, line: { color: "64748B", width: 2, dash: "dash" } });

  pill(s, "CASE VANTARA", 0.7, 0.65, 1.65, C.purple, C.white);
  s.addText("O dinheiro entra.\nA identidade não se perde.", {
    x: 0.7, y: 1.35, w: 7.2, h: 2.05,
    fontSize: 38, bold: true, color: C.white, margin: 0,
    breakLine: false, fit: "shrink",
  });
  s.addText("Vantara Concilia transforma exportações bagunçadas em uma fila auditável — sem escrever no ERP e sem chamar hipótese de fato.", {
    x: 0.72, y: 3.73, w: 6.75, h: 0.9,
    fontSize: 16, color: "C5CEDD", margin: 0, fit: "shrink",
  });
  pill(s, "30 DIAS", 0.72, 5.25, 1.28, C.mint, C.dark);
  pill(s, "READ-ONLY", 2.15, 5.25, 1.55, C.darkCard, C.white);
  pill(s, "HUMANO NO CONTROLE", 3.86, 5.25, 2.25, C.darkCard, C.white);
  s.addText("Barte AI Services  ·  Outubro 2026", {
    x: 0.72, y: 6.55, w: 5.2, h: 0.28,
    fontSize: 10, color: "8995AA", margin: 0,
  });
}

// 2 — Case snapshot
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Cena do problema", "Uma operação grande tentando fechar o caixa no escuro", "O pedido é conciliação. As restrições mostram onde a confiança precisa nascer.", 2);

  const stats = [
    ["210", "unidades franqueadas", C.purple],
    ["1.900", "títulos a receber/mês", C.blue],
    ["4", "bancos + sistemas fragmentados", C.mint],
    ["12 dias", "para fechar o mês", C.coral],
  ];
  stats.forEach((d, i) => card(s, {
    x: 0.65 + i * 3.12, y: 1.85, w: 2.83, h: 1.72,
    value: d[0], title: d[1], body: "", accent: d[2], fill: C.white,
  }));

  roundRect(s, 0.65, 3.95, 7.65, 2.25, C.dark, C.dark);
  s.addText("“A cobrança é o motivo de o franqueado ter raiva da gente.\nMeu time liga para quem já pagou.”", {
    x: 1.05, y: 4.38, w: 6.85, h: 0.9,
    fontSize: 20, bold: true, italic: true, color: C.white, margin: 0,
    fit: "shrink",
  });
  s.addText("Head de Operações de Franquias", {
    x: 1.05, y: 5.48, w: 3.7, h: 0.25,
    fontSize: 9.5, color: "9AA6BA", margin: 0,
  });

  card(s, {
    x: 8.65, y: 3.95, w: 4.03, h: 2.25,
    title: "As três paredes do piloto",
    body: "01  Algo funcionando em 30 dias\n\n02  Zero escrita no Protheus por 90 dias\n\n03  Produção dentro da infraestrutura Vantara",
    accent: C.amber, fill: C.amberSoft,
  });
}

// 3 — Reframe
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "A aposta", "Não começar pela IA. Começar pela identidade.", "Automatizar o processo atual aceleraria também as cobranças erradas.", 3);

  roundRect(s, 0.7, 1.9, 3.25, 2.25, C.coralSoft, C.coral);
  pill(s, "PEDIDO", 0.98, 2.17, 0.95, C.coral, C.white);
  s.addText("“Uma IA que bate pagamento”", {
    x: 0.98, y: 2.78, w: 2.65, h: 0.82,
    fontSize: 21, bold: true, color: C.ink, margin: 0, align: "center", fit: "shrink",
  });

  arrow(s, 4.28, 2.8, 0.72, C.muted);

  roundRect(s, 5.3, 1.72, 4.05, 2.62, C.purpleSoft, C.purple);
  pill(s, "REFRAME", 5.58, 2.0, 1.1, C.purple, C.white);
  s.addText("Uma camada auditável de\nidentidade operacional", {
    x: 5.58, y: 2.62, w: 3.5, h: 0.92,
    fontSize: 21, bold: true, color: C.ink, margin: 0, align: "center", fit: "shrink",
  });
  s.addText("Quem pagou?  →  O que quitou?  →  Qual ação é segura?", {
    x: 5.7, y: 3.68, w: 3.25, h: 0.28,
    fontSize: 9.5, color: C.purple, bold: true, align: "center", margin: 0,
  });

  arrow(s, 9.7, 2.8, 0.72, C.muted);

  roundRect(s, 10.7, 1.9, 1.95, 2.25, C.mintSoft, C.mint);
  pill(s, "COMEÇO", 11.08, 2.17, 1.2, C.mint, C.dark);
  s.addText("Recebíveis", {
    x: 10.95, y: 2.88, w: 1.45, h: 0.42,
    fontSize: 18, bold: true, color: C.ink, align: "center", margin: 0,
  });
  s.addText("AP vira radar de expansão — não desvia o piloto.", {
    x: 10.93, y: 3.4, w: 1.5, h: 0.47,
    fontSize: 9.2, color: C.muted, align: "center", margin: 0, fit: "shrink",
  });

  const chain = [
    ["Sistemas separados", C.purple],
    ["Pagamento sem identidade", C.blue],
    ["Conciliação manual", C.amber],
    ["Cobrança indevida", C.coral],
  ];
  chain.forEach((d, i) => {
    roundRect(s, 0.95 + i * 3.02, 5.05, 2.35, 0.82, C.white, C.line);
    s.addShape(SH.ellipse, { x: 1.17 + i * 3.02, y: 5.28, w: 0.34, h: 0.34, fill: { color: d[1] }, line: { color: d[1] } });
    s.addText(d[0], { x: 1.65 + i * 3.02, y: 5.22, w: 1.38, h: 0.38, fontSize: 10, bold: true, color: C.ink, margin: 0, fit: "shrink" });
    if (i < chain.length - 1) arrow(s, 3.42 + i * 3.02, 5.29, 0.42, C.line);
  });
}

// 4 — Step 0 ingest
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Passo 0 · Ingerir", "Os arquivos entram como vieram", "Sem limpeza manual antes: delimitadores, vírgula decimal, encodings e zeros à esquerda são tratados pelo pipeline.", 4, "Passo a passo");

  miniFile(s, 0.7, 1.9, 2.15, 2.25, "PROTHEUS .CSV", ["Padaria Vila Nova Ltda", "18.450,00", "000012345678"], C.purple);
  miniFile(s, 3.05, 1.9, 2.15, 2.25, "OMIE .CSV", ["GRAO NOBRE COM LTDA", "31250.00", "FAT-2026-0331"], C.blue);
  miniFile(s, 5.4, 1.9, 2.15, 2.25, "ITAÚ .CSV", ["PIX RECEBIDO...", "14.820,00 C", "doc. truncado"], C.mint);
  miniFile(s, 7.75, 1.9, 2.15, 2.25, "INBOX .TXT", ["NF 088231", "R$ 19.278,00", "12 de 15 volumes"], C.amber);

  arrow(s, 10.22, 2.86, 0.66, C.purple);
  roundRect(s, 11.15, 1.75, 1.48, 2.55, C.dark, C.dark);
  s.addText("SCHEMA\nCANÔNICO", {
    x: 11.32, y: 2.28, w: 1.14, h: 0.65,
    fontSize: 14, bold: true, color: C.white, align: "center", margin: 0,
  });
  s.addText("entidade\ndocumento\nvalor\ndata\nfonte", {
    x: 11.42, y: 3.02, w: 0.95, h: 0.95,
    fontSize: 9.5, color: "AAB5C8", align: "center", margin: 0,
  });

  const checks = [
    ["Preserva o bruto", "o identificador 000012345678 continua com 12 dígitos", C.mint],
    ["Falha visível", "linha inválida vira aviso/quarentena; não some silenciosamente", C.amber],
    ["Adapter por fonte", "novo ERP exige adapter; o restante do motor permanece igual", C.purple],
  ];
  checks.forEach((d, i) => card(s, {
    x: 0.75 + i * 4.13, y: 4.78, w: 3.8, h: 1.25,
    title: d[0], body: d[1], accent: d[2], fill: C.white, small: true,
  }));
}

// 5 — Identity
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Passo 1 · Resolver identidade", "O mesmo cliente usa dois crachás", "CNPJ une a entidade; coincidência de valor e vencimento gera suspeita — nunca baixa automática.", 5, "Passo a passo");

  card(s, {
    x: 0.72, y: 1.9, w: 4.05, h: 2.25,
    title: "PROTHEUS",
    body: "Grão Nobre Comércio Ltda\nCNPJ 55.666.777/0001-44\nNF 104580\nR$ 31.250 · venc. 20/07",
    accent: C.purple, fill: C.white,
  });
  card(s, {
    x: 8.56, y: 1.9, w: 4.05, h: 2.25,
    title: "OMIE",
    body: "GRAO NOBRE COM LTDA\nCNPJ 55666777000144\nFAT-2026-0331\nR$ 31.250 · venc. 20/07",
    accent: C.blue, fill: C.white,
  });

  s.addShape(SH.ellipse, {
    x: 5.23, y: 1.68, w: 2.85, h: 2.85,
    fill: { color: C.purpleSoft }, line: { color: C.purple, width: 2 },
  });
  s.addText("1 entidade", {
    x: 5.6, y: 2.18, w: 2.1, h: 0.45,
    fontSize: 22, bold: true, color: C.purple, align: "center", margin: 0,
  });
  s.addText("mesmo CNPJ", {
    x: 5.85, y: 2.79, w: 1.6, h: 0.28,
    fontSize: 11, bold: true, color: C.ink, align: "center", margin: 0,
  });
  pill(s, "FORTE INDÍCIO", 5.7, 3.4, 1.9, C.amber, C.ink);

  roundRect(s, 1.2, 4.82, 10.92, 1.16, C.amberSoft, C.amber);
  s.addText("Ação segura", {
    x: 1.5, y: 5.11, w: 1.3, h: 0.3,
    fontSize: 12, bold: true, color: C.ink, margin: 0,
  });
  s.addText("Suspender a cobrança por até 48h → conferir pedido/contrato/documento de origem → só então concluir duplicidade ou dívida legítima.", {
    x: 2.85, y: 5.06, w: 8.92, h: 0.42,
    fontSize: 12.2, color: C.ink, margin: 0, fit: "shrink",
  });
  pill(s, "R$ 31.250 SOB VALIDAÇÃO", 4.85, 6.2, 3.65, C.dark, C.white);
}

// 6 — Cascade
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Passo 2 · Vincular", "A evidência mais forte fala primeiro", "A cascata para no primeiro vínculo defensável. Quanto mais fraca a evidência, maior a intervenção humana.", 6, "Passo a passo");

  const tiers = [
    ["1", "Nosso Número", "5 casos", "campo bancário direto", C.mint, 0.99],
    ["2", "CNPJ no texto", "2 casos", "14 dígitos no histórico", C.blue, 0.95],
    ["3", "Nome", "6 casos", "completo ou truncado", C.purple, 0.84],
    ["4", "IA", "0 casos", "desempate em lista fechada", C.amber, 0.85],
    ["5", "Só valor", "1 caso", "nunca automático", C.coral, 0.45],
  ];
  tiers.forEach((d, i) => {
    const y = 1.78 + i * 0.91;
    circleNumber(s, d[0], 0.75, y, d[4], 0.52);
    s.addText(d[1], { x: 1.48, y: y + 0.05, w: 1.55, h: 0.25, fontSize: 12, bold: true, color: C.ink, margin: 0 });
    s.addText(d[3], { x: 1.48, y: y + 0.36, w: 2.35, h: 0.22, fontSize: 9, color: C.muted, margin: 0 });
    s.addShape(SH.roundRect, { x: 3.72, y: y + 0.11, w: 4.7, h: 0.24, rectRadius: 0.1, fill: { color: C.line }, line: { color: C.line } });
    s.addShape(SH.roundRect, { x: 3.72, y: y + 0.11, w: 4.7 * d[5], h: 0.24, rectRadius: 0.1, fill: { color: d[4] }, line: { color: d[4] } });
    pill(s, d[2], 8.72, y + 0.02, 1.25, d[4], d[4] === C.amber ? C.ink : C.white);
  });

  roundRect(s, 10.35, 1.78, 2.35, 4.4, C.dark, C.dark);
  s.addText("DECISÃO", { x: 10.72, y: 2.1, w: 1.62, h: 0.25, fontSize: 10, bold: true, color: "9AA6BA", align: "center", margin: 0, charSpacing: 1.3 });
  s.addText("8", { x: 10.55, y: 2.56, w: 1.0, h: 0.55, fontSize: 27, bold: true, color: C.mint, align: "center", margin: 0 });
  s.addText("propostas de\nalta confiança", { x: 11.47, y: 2.61, w: 0.95, h: 0.55, fontSize: 9.5, color: C.white, margin: 0, fit: "shrink" });
  s.addShape(SH.line, { x: 10.73, y: 3.4, w: 1.6, h: 0, line: { color: "39445A", width: 1 } });
  s.addText("6", { x: 10.55, y: 3.68, w: 1.0, h: 0.55, fontSize: 27, bold: true, color: C.amber, align: "center", margin: 0 });
  s.addText("casos para\nconfirmação", { x: 11.47, y: 3.73, w: 0.95, h: 0.55, fontSize: 9.5, color: C.white, margin: 0, fit: "shrink" });
  s.addShape(SH.line, { x: 10.73, y: 4.52, w: 1.6, h: 0, line: { color: "39445A", width: 1 } });
  s.addText("1", { x: 10.55, y: 4.8, w: 1.0, h: 0.55, fontSize: 27, bold: true, color: C.coral, align: "center", margin: 0 });
  s.addText("crédito sem\ntítulo", { x: 11.47, y: 4.85, w: 0.95, h: 0.55, fontSize: 9.5, color: C.white, margin: 0, fit: "shrink" });
  pill(s, "ZERO ESCRITA NO ERP", 10.63, 5.62, 1.78, C.purple, C.white);
}

// 7 — Value classification
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Passo 3 · Explicar o valor", "Diferente não significa errado — nem correto", "O motor reconhece padrões; documentos e contratos transformam hipótese em decisão.", 7, "Passo a passo");

  const cases = [
    {
      y: 1.78, color: C.amber, bg: C.amberSoft, tag: "HIPÓTESE · RETENÇÃO",
      left: "R$ 15.600", right: "R$ 14.820", diff: "− R$ 780 (5%)",
      body: "Compatível com retenção. Exige documento fiscal/tributário antes da baixa.",
    },
    {
      y: 3.3, color: C.amber, bg: C.amberSoft, tag: "HIPÓTESE · MORA",
      left: "R$ 22.900", right: "R$ 23.358", diff: "+ R$ 458 (2%)",
      body: "Compatível com multa/juros. Exige contrato e memória de cálculo.",
    },
    {
      y: 4.82, color: C.blue, bg: C.blueSoft, tag: "FATO · PARCIAL",
      left: "R$ 125.000", right: "R$ 62.500", diff: "saldo R$ 62.500",
      body: "O identificador bancário sustenta o recebimento parcial; o saldo permanece aberto.",
    },
  ];
  cases.forEach((d) => {
    roundRect(s, 0.72, d.y, 12.0, 1.18, d.bg, d.color);
    pill(s, d.tag, 0.98, d.y + 0.18, 2.25, d.color, d.color === C.amber ? C.ink : C.white);
    s.addText(d.left, { x: 3.48, y: d.y + 0.19, w: 1.55, h: 0.38, fontSize: 17, bold: true, color: C.ink, align: "right", margin: 0 });
    arrow(s, 5.28, d.y + 0.26, 0.52, d.color);
    s.addText(d.right, { x: 6.05, y: d.y + 0.19, w: 1.55, h: 0.38, fontSize: 17, bold: true, color: C.ink, margin: 0 });
    pill(s, d.diff, 7.83, d.y + 0.2, 1.72, C.white, d.color);
    s.addText(d.body, { x: 9.78, y: d.y + 0.18, w: 2.55, h: 0.58, fontSize: 9.5, color: C.ink, margin: 0, fit: "shrink" });
  });
}

// 8 — Human loop
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Passo 4 · Operar exceções", "A analista não recebe uma caixa-preta. Recebe uma fila.", "Cada linha traz ação, confiança, evidência, saldo e responsável.", 8, "Passo a passo");

  const cols = [0.72, 4.38, 8.04];
  const d = [
    ["AUTO_APLICAR", "8 casos", "Entram no arquivo de propostas. A Vantara continua sendo a autoridade de aplicação.", C.mint, C.mintSoft],
    ["CONFIRMAR", "6 casos", "Retenção, mora, nome parcial ou divergência pedem documento e chancela humana.", C.amber, C.amberSoft],
    ["INVESTIGAR", "1 sem título", "Nenhum saldo é consumido; o caixa permanece visível até surgir evidência suficiente.", C.coral, C.coralSoft],
  ];
  d.forEach((a, i) => {
    roundRect(s, cols[i], 1.9, 3.3, 2.32, a[4], a[3]);
    pill(s, a[0], cols[i] + 0.28, 2.18, 1.62, a[3], a[3] === C.amber ? C.ink : C.white);
    s.addText(a[1], { x: cols[i] + 0.28, y: 2.83, w: 2.72, h: 0.48, fontSize: 22, bold: true, color: C.ink, margin: 0 });
    s.addText(a[2], { x: cols[i] + 0.28, y: 3.41, w: 2.72, h: 0.56, fontSize: 9.8, color: C.muted, margin: 0, fit: "shrink" });
  });

  roundRect(s, 1.1, 4.85, 11.12, 1.16, C.dark, C.dark);
  s.addText("TRAVA", { x: 1.42, y: 5.23, w: 0.8, h: 0.27, fontSize: 11, bold: true, color: C.coral, margin: 0, charSpacing: 1.2 });
  s.addText("Sem baixa automática  ·  sem cobrança automática  ·  sem liberação automática de fornecedor", {
    x: 2.32, y: 5.16, w: 8.55, h: 0.38,
    fontSize: 13.5, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink",
  });
  pill(s, "SHADOW MODE", 10.92, 5.14, 1.05, C.purple, C.white);
}

// 9 — Actual output
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Saída real", "O que a segunda-feira de manhã recebe", "Resultados reproduzidos pelo modo determinístico no data pack de julho.", 9, "Resultado");

  const metrics = [
    ["14/15", "créditos vinculados", "99,4% do valor", C.purple],
    ["8", "propostas de alta confiança", "48,4% do valor", C.mint],
    ["0", "chamadas à IA", "regras bastaram na amostra", C.blue],
    ["46/46", "testes verdes", "inclui stress e limites", C.amber],
  ];
  metrics.forEach((m, i) => card(s, {
    x: 0.66 + i * 3.13, y: 1.78, w: 2.85, h: 1.62,
    value: m[0], title: m[1], body: m[2], accent: m[3], fill: C.white,
  }));

  s.addText("Saldo em aberto, decomposto", { x: 0.72, y: 3.84, w: 4.0, h: 0.34, fontSize: 16, bold: true, color: C.ink, margin: 0 });
  const open = [
    ["R$ 31.250", "possível duplicidade", "suspender e validar", C.amber],
    ["R$ 62.500", "saldo parcial", "cobrar apenas o saldo", C.blue],
    ["R$ 8.120", "sem match neste extrato", "validar outros bancos", C.coral],
  ];
  open.forEach((m, i) => card(s, {
    x: 0.72 + i * 3.25, y: 4.35, w: 2.95, h: 1.55,
    value: m[0], title: m[1], body: m[2], accent: m[3], fill: C.white, small: true,
  }));

  roundRect(s, 10.45, 3.77, 2.18, 2.27, C.coralSoft, C.coral);
  s.addText("1 de 4", { x: 10.72, y: 4.18, w: 1.64, h: 0.55, fontSize: 27, bold: true, color: C.coral, align: "center", margin: 0 });
  s.addText("contas bancárias está no data pack", { x: 10.83, y: 4.86, w: 1.42, h: 0.55, fontSize: 10.5, bold: true, color: C.ink, align: "center", margin: 0, fit: "shrink" });
  s.addText("Sem match não prova inadimplência.", { x: 10.75, y: 5.47, w: 1.58, h: 0.3, fontSize: 8.8, color: C.muted, align: "center", margin: 0 });
  roundRect(s, 0.72, 6.18, 9.45, 0.52, C.dark, C.dark);
  s.addText("Fechamento:  R$ 152.880 validado para proposta  ·  R$ 162.928,50 em análise humana  ·  R$ 315.808,50 total", {
    x: 0.98, y: 6.32, w: 8.93, h: 0.22,
    fontSize: 9.8, bold: true, color: C.white, align: "center", margin: 0, fit: "shrink",
  });
}

// 10 — AP side quest
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Radar secundário", "Contas a pagar mostra valor — mas não rouba o piloto", "A expansão é defensável porque lê evidência não estruturada; a implantação inicial continua em Recebíveis.", 10, "Expansão");

  const timeline = [
    ["06/07", "NF 88231", "R$ 18.900", C.purple],
    ["18/07", "cobrança reemitida", "R$ 19.278", C.coral],
    ["19/07", "agendado lido como pago", "dúvida sem dono", C.amber],
    ["20/07", "débito no extrato", "R$ 18.900", C.mint],
  ];
  s.addShape(SH.line, { x: 1.1, y: 2.92, w: 7.65, h: 0, line: { color: C.line, width: 3 } });
  timeline.forEach((a, i) => {
    const x = 0.78 + i * 2.52;
    s.addShape(SH.ellipse, { x: x + 0.42, y: 2.63, w: 0.58, h: 0.58, fill: { color: a[3] }, line: { color: C.white, width: 2 } });
    pill(s, a[0], x + 0.16, 1.82, 1.1, a[3], a[3] === C.amber ? C.ink : C.white);
    s.addText(a[1], { x, y: 3.46, w: 1.42, h: 0.45, fontSize: 10.5, bold: true, color: C.ink, align: "center", margin: 0, fit: "shrink" });
    s.addText(a[2], { x, y: 3.98, w: 1.42, h: 0.35, fontSize: 9, color: C.muted, align: "center", margin: 0, fit: "shrink" });
  });

  card(s, {
    x: 9.55, y: 1.75, w: 3.08, h: 2.63,
    value: "R$ 19.278", title: "exposição potencial",
    body: "Bloquear e validar com fornecedor e documentos. Não é perda confirmada.",
    accent: C.coral, fill: C.coralSoft,
  });

  roundRect(s, 0.85, 5.0, 5.62, 1.02, C.amberSoft, C.amber);
  s.addText("12 de 15 volumes", { x: 1.15, y: 5.24, w: 1.8, h: 0.32, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  s.addText("prova entrega parcial; não permite calcular perda monetária sem preço por item e condição comercial.", { x: 3.02, y: 5.19, w: 3.1, h: 0.42, fontSize: 9.5, color: C.ink, margin: 0, fit: "shrink" });
  roundRect(s, 6.78, 5.0, 5.55, 1.02, C.blueSoft, C.blue);
  s.addText("R$ 34.117,82", { x: 7.08, y: 5.24, w: 1.65, h: 0.32, fontSize: 15, bold: true, color: C.ink, margin: 0 });
  s.addText("sem controle verificável porque o anexo citado não foi fornecido. Visível, mas não classificado como perda.", { x: 8.87, y: 5.19, w: 3.1, h: 0.42, fontSize: 9.5, color: C.ink, margin: 0, fit: "shrink" });
}

// 11 — Architecture
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Arquitetura de produção", "A Barte leva o motor. A Vantara mantém a casa.", "O protótipo roda localmente; este é o desenho proposto para produção, sujeito à aprovação interna da Barte.", 11, "Arquitetura");

  roundRect(s, 0.72, 1.78, 3.15, 4.7, C.purpleSoft, C.purple);
  pill(s, "BARTE", 1.0, 2.05, 0.9, C.purple, C.white);
  s.addText("Core reutilizável", { x: 1.0, y: 2.62, w: 2.42, h: 0.38, fontSize: 18, bold: true, color: C.ink, margin: 0 });
  const barteItems = ["código-fonte único", "CI e testes", "imagem assinada", "versões e suporte", "adapter contract"];
  barteItems.forEach((t, i) => {
    s.addShape(SH.ellipse, { x: 1.02, y: 3.32 + i * 0.48, w: 0.18, h: 0.18, fill: { color: C.purple }, line: { color: C.purple } });
    s.addText(t, { x: 1.34, y: 3.27 + i * 0.48, w: 1.95, h: 0.24, fontSize: 10.5, color: C.ink, margin: 0 });
  });
  pill(s, "SEM DADOS FINANCEIROS", 1.02, 5.91, 2.55, C.white, C.purple);

  arrow(s, 4.2, 3.65, 0.8, C.purple);
  s.addText("imagem\nassinada", { x: 4.15, y: 4.13, w: 0.9, h: 0.45, fontSize: 8.5, color: C.muted, align: "center", margin: 0 });

  roundRect(s, 5.3, 1.62, 7.35, 5.0, C.dark, C.dark);
  pill(s, "CLOUD VANTARA", 5.65, 1.94, 1.72, C.mint, C.dark);
  s.addText("Dados e execução ficam aqui", { x: 7.62, y: 1.98, w: 3.3, h: 0.3, fontSize: 15, bold: true, color: C.white, margin: 0 });

  const arch = [
    ["Exports", "Protheus · Omie · bancos", C.blue],
    ["Container", "identidade + matching + filas", C.purple],
    ["Saídas", "CSV · HTML · logs", C.mint],
  ];
  arch.forEach((a, i) => {
    const x = 5.72 + i * 2.22;
    roundRect(s, x, 3.0, 1.72, 1.35, C.darkCard, "39445A");
    s.addShape(SH.ellipse, { x: x + 0.66, y: 3.18, w: 0.4, h: 0.4, fill: { color: a[2] }, line: { color: a[2] } });
    s.addText(a[0], { x: x + 0.18, y: 3.72, w: 1.36, h: 0.25, fontSize: 11.5, bold: true, color: C.white, align: "center", margin: 0 });
    s.addText(a[1], { x: x + 0.14, y: 4.0, w: 1.44, h: 0.23, fontSize: 7.8, color: "AAB5C8", align: "center", margin: 0, fit: "shrink" });
    if (i < arch.length - 1) arrow(s, x + 1.82, 3.5, 0.3, "516078");
  });
  pill(s, "READ-ONLY", 5.78, 4.88, 1.22, C.blue, C.white);
  pill(s, "KMS VANTARA", 7.25, 4.88, 1.55, C.darkCard, C.white);
  pill(s, "EGRESS BLOQUEADO", 9.05, 4.88, 1.88, C.coral, C.white);
  pill(s, "ZERO ESCRITA ERP", 11.16, 4.88, 1.18, C.amber, C.ink);
  s.addText("IA desligada por padrão. Se usada: endpoint local ou explicitamente aprovado pela Vantara.", {
    x: 5.78, y: 5.65, w: 6.55, h: 0.36,
    fontSize: 10.5, color: "C5CEDD", align: "center", margin: 0,
  });
}

// 12 — Failure controls
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Confiabilidade", "Como descobrir o erro antes do franqueado", "A conferência ao centavo é necessária, mas não suficiente: matemática certa ainda pode esconder vínculo errado.", 12, "Operação");

  const locks = [
    ["1", "Entrada", "campos obrigatórios e linhas rejeitadas ficam visíveis; erro estrutural interrompe a execução", C.blue],
    ["2", "Aritmética", "duas invariantes conservam títulos e caixa; diferença acima da tolerância de um centavo interrompe a geração", C.mint],
    ["3", "Semântica", "golden set e auditoria medem precisão por tier; confiança sem validação não vira automação", C.purple],
    ["4", "Ação", "shadow mode, zero escrita e zero cobrança automática impedem que erro alcance o cliente", C.coral],
  ];
  locks.forEach((a, i) => {
    const x = 0.72 + i * 3.03;
    roundRect(s, x, 1.9, 2.72, 3.7, C.white, C.line);
    circleNumber(s, a[0], x + 0.26, 2.18, a[3], 0.58);
    s.addText(a[1], { x: x + 0.98, y: 2.22, w: 1.35, h: 0.3, fontSize: 15, bold: true, color: C.ink, margin: 0 });
    s.addText(a[2], { x: x + 0.28, y: 3.02, w: 2.16, h: 1.28, fontSize: 11, color: C.muted, margin: 0, valign: "top", fit: "shrink" });
    pill(s, i < 2 ? "IMPLEMENTADO" : "GATE DO PILOTO", x + 0.44, 4.88, 1.84, i < 2 ? C.mintSoft : C.amberSoft, i < 2 ? C.mint : C.amber);
  });
  roundRect(s, 2.0, 6.0, 9.35, 0.52, C.dark, C.dark);
  s.addText("Se a evidência não sustenta a decisão, o sistema se abstém — e explica por quê.", {
    x: 2.25, y: 6.13, w: 8.85, h: 0.22,
    fontSize: 12, bold: true, color: C.white, align: "center", margin: 0,
  });
}

// 13 — 30 days and reuse
{
  const s = pptx.addSlide();
  addBg(s);
  addHeader(s, "Plano de implantação", "Quatro semanas para provar — ou parar", "O piloto compra evidência operacional, não uma promessa de automação.", 13, "30 dias");

  const weeks = [
    ["SEMANA 1", "Entradas + golden set", "exports read-only, casos de julho assinados pela Controller", C.blue],
    ["SEMANA 2", "Fila em shadow mode", "execução diária, exceção com evidência e dono", C.purple],
    ["SEMANA 3", "Medição por tier", "precisão, falso positivo e tempo de revisão", C.amber],
    ["SEMANA 4", "Decisão", "aceitar, recalibrar ou interromper com métricas", C.mint],
  ];
  weeks.forEach((a, i) => {
    const x = 0.72 + i * 3.06;
    pill(s, a[0], x, 1.82, 1.38, a[3], a[3] === C.amber ? C.ink : C.white);
    s.addShape(SH.line, { x: x + 1.42, y: 1.99, w: 1.3, h: 0, line: { color: i === weeks.length - 1 ? C.paper : C.line, width: 3 } });
    s.addText(a[1], { x, y: 2.42, w: 2.72, h: 0.42, fontSize: 15, bold: true, color: C.ink, margin: 0, fit: "shrink" });
    s.addText(a[2], { x, y: 2.96, w: 2.55, h: 0.72, fontSize: 9.8, color: C.muted, margin: 0, fit: "shrink" });
  });

  card(s, {
    x: 0.72, y: 4.48, w: 5.72, h: 1.62,
    title: "Reutilizável nas próximas cinco contas",
    body: "schema canônico · adapters · resolução de identidade · cascata de matching · invariantes · filas · contrato de IA",
    accent: C.purple, fill: C.purpleSoft,
  });
  card(s, {
    x: 6.87, y: 4.48, w: 5.75, h: 1.62,
    title: "Específico da Vantara",
    body: "layouts de exportação · contas bancárias · políticas aprovadas · tolerâncias · mapeamentos · destinatários",
    accent: C.blue, fill: C.blueSoft,
  });
}

// 14 — Close / CTO ask
{
  const s = pptx.addSlide();
  addBg(s, C.dark);
  pill(s, "REUNIÃO COM O CTO", 0.72, 0.62, 1.92, C.purple, C.white);
  s.addText("Três decisões.\nNenhum salto de fé.", {
    x: 0.72, y: 1.35, w: 5.25, h: 1.42,
    fontSize: 35, bold: true, color: C.white, margin: 0,
  });
  s.addText("O objetivo não é aprovar uma IA. É liberar um piloto controlado que produz evidência dentro das regras da Vantara.", {
    x: 0.74, y: 3.0, w: 4.95, h: 0.88,
    fontSize: 15, color: "C5CEDD", margin: 0, fit: "shrink",
  });
  pill(s, "ZERO ESCRITA", 0.74, 4.35, 1.35, C.darkCard, C.white);
  pill(s, "ZERO COBRANÇA AUTO", 2.25, 4.35, 2.02, C.darkCard, C.white);
  pill(s, "DADOS NA VANTARA", 4.43, 4.35, 1.67, C.mint, C.dark);

  const asks = [
    ["01", "Exports diários read-only", "Quais arquivos e contas entram no piloto?", C.blue],
    ["02", "Ambiente isolado", "Onde o container assinado pode rodar sem escrita?", C.purple],
    ["03", "Dono do golden set", "Quem na Controladoria assina casos e políticas?", C.mint],
  ];
  asks.forEach((a, i) => {
    const y = 1.12 + i * 1.62;
    roundRect(s, 6.72, y, 5.88, 1.27, C.darkCard, "39445A");
    s.addText(a[0], { x: 7.02, y: y + 0.27, w: 0.62, h: 0.48, fontSize: 23, bold: true, color: a[3], margin: 0 });
    s.addText(a[1], { x: 7.92, y: y + 0.22, w: 3.85, h: 0.32, fontSize: 15, bold: true, color: C.white, margin: 0 });
    s.addText(a[2], { x: 7.92, y: y + 0.69, w: 4.05, h: 0.28, fontSize: 10, color: "AAB5C8", margin: 0, fit: "shrink" });
  });
  roundRect(s, 6.72, 6.08, 5.88, 0.58, C.purple, C.purple);
  s.addText("Em 30 dias: precisão medida, risco conhecido e uma decisão objetiva.", {
    x: 6.98, y: 6.24, w: 5.35, h: 0.24,
    fontSize: 11.5, bold: true, color: C.white, align: "center", margin: 0,
  });
  addFooter(s, "Decisão", 14, true);
}

const outPath = path.join(__dirname, "VantaraConcilia_Apresentacao_Ludica.pptx");

(async () => {
  await pptx.writeFile({ fileName: outPath });
  console.log(`PPTX gerado: ${outPath}`);
})();
