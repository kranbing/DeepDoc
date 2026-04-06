// DeepDOC Design Generator
// Generates starter frames in Figma that mirror the current HTML/CSS look.
// No UI: running the plugin will create/update frames and then close.

// Design tokens (kept aligned with web/styles.css :root)
const TOKENS = {
  bgPage: "#f7f8fa",
  surface: "#ffffff",
  surfaceMuted: "#fafafa",

  accent: "#4a6fa5",
  accentHover: "#5a7fb5",

  btnPrimaryBg: "#1a1d24",
  btnPrimaryHover: "#2a2f3a",
  btnPrimaryText: "#ffffff",

  btnSecondaryBg: "#eceef2",

  borderSubtle: "#eeeeee",
  borderInput: "#e5e5e5",

  textTitle: "#111111",
  textBody: "#333333",
  textMuted: "#888888",

  radiusCard: 14,
  radiusControl: 12,
  radiusBtn: 11,

  shadowFloat: {
    type: "DROP_SHADOW",
    color: { r: 0, g: 0, b: 0, a: 0.04 },
    offset: { x: 0, y: 2 },
    radius: 8,
    spread: 0,
    visible: true,
    blendMode: "NORMAL",
  },
};

const DESKTOP = { w: 1440, h: 900 };
const TOPBAR_H = 56;

function hexToRgb(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex);
  if (!m) throw new Error(`Invalid hex: ${hex}`);
  const n = parseInt(m[1], 16);
  return {
    r: ((n >> 16) & 255) / 255,
    g: ((n >> 8) & 255) / 255,
    b: (n & 255) / 255,
  };
}

function solidFill(hex, opacity = 1) {
  const rgb = hexToRgb(hex);
  return [{ type: "SOLID", color: rgb, opacity }];
}

function stroke(hex, opacity = 1) {
  const rgb = hexToRgb(hex);
  return [{ type: "SOLID", color: rgb, opacity }];
}

async function ensureFonts() {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Medium" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });
}

function findOrCreatePage(name) {
  const existing = figma.root.children.find((p) => p.type === "PAGE" && p.name === name);
  if (existing) return existing;
  const p = figma.createPage();
  p.name = name;
  return p;
}

function removeExistingByName(parent, name) {
  const hit = parent.children.find((n) => n.name === name);
  if (hit) hit.remove();
}

function mkText(text, { size = 12, style = "Regular", fill = TOKENS.textBody, lineHeight } = {}) {
  const t = figma.createText();
  t.fontName = { family: "Inter", style };
  t.characters = text;
  t.fontSize = size;
  t.fills = solidFill(fill);
  if (lineHeight) t.lineHeight = { unit: "PIXELS", value: lineHeight };
  return t;
}

function mkFrame(name, { w, h, x = 0, y = 0, fill } = {}) {
  const f = figma.createFrame();
  f.name = name;
  f.resizeWithoutConstraints(w, h);
  f.x = x;
  f.y = y;
  f.fills = fill ? solidFill(fill) : [];
  return f;
}

function mkTopbar() {
  const top = figma.createFrame();
  top.name = "Topbar";
  top.resizeWithoutConstraints(DESKTOP.w, TOPBAR_H);
  top.fills = solidFill(TOKENS.surface, 0.88);
  top.strokes = stroke(TOKENS.borderSubtle);
  top.strokeWeight = 1;
  top.strokeAlign = "INSIDE";
  top.effects = [TOKENS.shadowFloat];
  top.cornerRadius = 0;
  return top;
}

function mkBrand() {
  const brand = figma.createFrame();
  brand.name = "Brand";
  brand.fills = [];
  brand.layoutMode = "HORIZONTAL";
  brand.primaryAxisAlignItems = "MIN";
  brand.counterAxisAlignItems = "CENTER";
  brand.itemSpacing = 12;
  brand.paddingLeft = 0;
  brand.paddingRight = 0;
  brand.paddingTop = 0;
  brand.paddingBottom = 0;

  const icon = figma.createFrame();
  icon.name = "Brand Icon";
  icon.resizeWithoutConstraints(36, 36);
  icon.fills = solidFill(TOKENS.btnPrimaryBg);
  icon.cornerRadius = TOKENS.radiusControl;
  icon.effects = [TOKENS.shadowFloat];
  icon.layoutMode = "VERTICAL";
  icon.primaryAxisAlignItems = "CENTER";
  icon.counterAxisAlignItems = "CENTER";

  const glyph = mkText("◆", { size: 14, style: "Bold", fill: TOKENS.btnPrimaryText });
  icon.appendChild(glyph);

  const textCol = figma.createFrame();
  textCol.name = "Brand Text";
  textCol.fills = [];
  textCol.layoutMode = "VERTICAL";
  textCol.primaryAxisAlignItems = "MIN";
  textCol.counterAxisAlignItems = "MIN";
  textCol.itemSpacing = 3;

  const title = mkText("DeepDOC", { size: 15, style: "Bold", fill: TOKENS.textTitle, lineHeight: 18 });
  const sub = mkText("PDF · 数据库 · 交付物（演示）", { size: 12, style: "Medium", fill: TOKENS.textMuted, lineHeight: 16 });

  textCol.appendChild(title);
  textCol.appendChild(sub);

  brand.appendChild(icon);
  brand.appendChild(textCol);
  return brand;
}

function mkButton(label, { primary = false } = {}) {
  const btn = figma.createFrame();
  btn.name = primary ? "Button / Primary" : "Button";
  btn.fills = primary ? solidFill(TOKENS.btnPrimaryBg) : solidFill(TOKENS.btnSecondaryBg);
  btn.strokes = primary ? [] : stroke(TOKENS.borderSubtle);
  btn.strokeWeight = 1;
  btn.strokeAlign = "INSIDE";
  btn.cornerRadius = TOKENS.radiusBtn;
  btn.effects = primary ? [TOKENS.shadowFloat] : [];
  btn.layoutMode = "HORIZONTAL";
  btn.primaryAxisAlignItems = "CENTER";
  btn.counterAxisAlignItems = "CENTER";
  btn.paddingLeft = primary ? 18 : 16;
  btn.paddingRight = primary ? 18 : 16;
  btn.paddingTop = 10;
  btn.paddingBottom = 10;

  const t = mkText(label, { size: 13, style: "Medium", fill: primary ? TOKENS.btnPrimaryText : TOKENS.textBody, lineHeight: 16 });
  btn.appendChild(t);
  return btn;
}

function mkCard(name, { w = 300, h = 180 } = {}) {
  const c = figma.createFrame();
  c.name = name;
  c.resizeWithoutConstraints(w, h);
  c.fills = solidFill(TOKENS.surface);
  c.strokes = stroke(TOKENS.borderSubtle);
  c.strokeWeight = 1;
  c.strokeAlign = "INSIDE";
  c.cornerRadius = TOKENS.radiusCard;
  c.effects = [TOKENS.shadowFloat];
  return c;
}

function mkTokensPanel() {
  const wrap = figma.createFrame();
  wrap.name = "Tokens";
  wrap.fills = [];
  wrap.layoutMode = "VERTICAL";
  wrap.primaryAxisAlignItems = "MIN";
  wrap.counterAxisAlignItems = "MIN";
  wrap.itemSpacing = 12;

  const title = mkText("Tokens", { size: 14, style: "Bold", fill: TOKENS.textTitle });
  wrap.appendChild(title);

  const row = figma.createFrame();
  row.name = "Colors";
  row.fills = [];
  row.layoutMode = "HORIZONTAL";
  row.primaryAxisAlignItems = "MIN";
  row.counterAxisAlignItems = "CENTER";
  row.itemSpacing = 10;

  const swatches = [
    ["bgPage", TOKENS.bgPage],
    ["surface", TOKENS.surface],
    ["accent", TOKENS.accent],
    ["btnPrimaryBg", TOKENS.btnPrimaryBg],
    ["borderSubtle", TOKENS.borderSubtle],
    ["textMuted", TOKENS.textMuted],
  ];

  for (const [key, hex] of swatches) {
    const s = figma.createFrame();
    s.name = `Swatch / ${key}`;
    s.resizeWithoutConstraints(120, 44);
    s.cornerRadius = 12;
    s.fills = solidFill(hex);
    s.strokes = stroke(TOKENS.borderSubtle);
    s.strokeAlign = "INSIDE";
    s.strokeWeight = 1;
    s.layoutMode = "VERTICAL";
    s.primaryAxisAlignItems = "MIN";
    s.counterAxisAlignItems = "MIN";
    s.paddingLeft = 10;
    s.paddingRight = 10;
    s.paddingTop = 8;
    s.paddingBottom = 8;
    const label = mkText(key, { size: 11, style: "Medium", fill: TOKENS.surface === hex ? TOKENS.textBody : TOKENS.surface, lineHeight: 14 });
    s.appendChild(label);
    row.appendChild(s);
  }

  wrap.appendChild(row);
  return wrap;
}

function buildLandingFrame() {
  const root = mkFrame("Landing (Projects)", { w: DESKTOP.w, h: DESKTOP.h, fill: TOKENS.bgPage });

  // Header
  const header = mkTopbar();
  header.name = "Landing Header";
  const brand = mkBrand();
  brand.x = 16;
  brand.y = (TOPBAR_H - 36) / 2;
  header.appendChild(brand);
  root.appendChild(header);

  // Content area (mimics grid with padding 28/32 and gap 32)
  const padX = 32;
  const padTop = 28;
  const gap = 32;

  const userCardW = 300;
  const userCard = mkCard("User Card", { w: userCardW, h: 200 });
  userCard.x = padX;
  userCard.y = TOPBAR_H + padTop;
  const userName = mkText("Demo User", { size: 16, style: "Bold", fill: TOKENS.textTitle, lineHeight: 20 });
  userName.x = 22;
  userName.y = 22;
  const userEmail = mkText("demo@deepdoc.local", { size: 12, style: "Medium", fill: TOKENS.textMuted, lineHeight: 16 });
  userEmail.x = 22;
  userEmail.y = 48;
  const userNote = mkText("选择一个项目开始。你也可以新建项目来导入 PDF。", { size: 13, style: "Regular", fill: TOKENS.textBody, lineHeight: 20 });
  userNote.x = 22;
  userNote.y = 78;
  userNote.resizeWithoutConstraints(userCardW - 44, 80);
  userCard.appendChild(userName);
  userCard.appendChild(userEmail);
  userCard.appendChild(userNote);
  root.appendChild(userCard);

  const rightX = padX + userCardW + gap;
  const rightW = DESKTOP.w - rightX - padX;

  const headerRow = figma.createFrame();
  headerRow.name = "Projects Header";
  headerRow.fills = [];
  headerRow.resizeWithoutConstraints(rightW, 40);
  headerRow.x = rightX;
  headerRow.y = TOPBAR_H + padTop;
  const sectionTitle = mkText("项目", { size: 13, style: "Bold", fill: TOKENS.textMuted, lineHeight: 16 });
  sectionTitle.textCase = "UPPER";
  sectionTitle.letterSpacing = { unit: "PERCENT", value: 6 };
  sectionTitle.x = 0;
  sectionTitle.y = 10;
  headerRow.appendChild(sectionTitle);
  const createBtn = mkButton("新建项目", { primary: true });
  // Smaller padding for this one (matches CSS .btn-create-project)
  createBtn.paddingLeft = 14;
  createBtn.paddingRight = 14;
  createBtn.paddingTop = 8;
  createBtn.paddingBottom = 8;
  createBtn.x = rightW - 110;
  createBtn.y = 4;
  headerRow.appendChild(createBtn);
  root.appendChild(headerRow);

  // A simple 2x2 project card grid (visual placeholder)
  const grid = figma.createFrame();
  grid.name = "Project Grid";
  grid.fills = [];
  grid.x = rightX;
  grid.y = TOPBAR_H + padTop + 54;
  grid.resizeWithoutConstraints(rightW, 520);
  const cardW = 260;
  const cardH = 120;
  const cardGap = 14;
  const cols = Math.max(1, Math.floor((rightW + cardGap) / (cardW + cardGap)));

  for (let i = 0; i < 4; i++) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const card = mkCard(`Project Card ${i + 1}`, { w: cardW, h: cardH });
    card.x = col * (cardW + cardGap);
    card.y = row * (cardH + cardGap);
    const t1 = mkText(`示例项目 ${i + 1}`, { size: 14, style: "Bold", fill: TOKENS.textTitle, lineHeight: 18 });
    t1.x = 18;
    t1.y = 18;
    const t2 = mkText("点击进入工作台，上传 PDF 并开始对话。", { size: 12, style: "Medium", fill: TOKENS.textMuted, lineHeight: 18 });
    t2.x = 18;
    t2.y = 44;
    t2.resizeWithoutConstraints(cardW - 36, 54);
    card.appendChild(t1);
    card.appendChild(t2);
    grid.appendChild(card);
  }

  root.appendChild(grid);
  return root;
}

function buildWorkspaceFrame() {
  const root = mkFrame("Workspace (Chat)", { w: DESKTOP.w, h: DESKTOP.h, fill: TOKENS.bgPage });

  const header = mkTopbar();
  header.name = "Topbar";
  const brand = mkBrand();
  brand.x = 80; // leave space for back button
  brand.y = (TOPBAR_H - 36) / 2;
  header.appendChild(brand);

  const backBtn = mkButton("← 项目", { primary: false });
  backBtn.name = "Back Button";
  backBtn.paddingLeft = 12;
  backBtn.paddingRight = 12;
  backBtn.paddingTop = 8;
  backBtn.paddingBottom = 8;
  backBtn.x = 16;
  backBtn.y = 10;
  header.appendChild(backBtn);

  const actionRow = figma.createFrame();
  actionRow.name = "Actions";
  actionRow.fills = [];
  actionRow.layoutMode = "HORIZONTAL";
  actionRow.primaryAxisAlignItems = "CENTER";
  actionRow.counterAxisAlignItems = "CENTER";
  actionRow.itemSpacing = 8;
  const parseBtn = mkButton("解析", { primary: false });
  parseBtn.name = "解析";
  const uploadBtn = mkButton("Upload", { primary: false });
  uploadBtn.name = "Upload";
  actionRow.appendChild(parseBtn);
  actionRow.appendChild(uploadBtn);
  actionRow.x = DESKTOP.w - 16 - (parseBtn.width + uploadBtn.width + 8);
  actionRow.y = 10;
  header.appendChild(actionRow);

  root.appendChild(header);

  // 3-column layout
  const leftW = 290;
  const rightW = 360;
  const bodyY = TOPBAR_H;
  const bodyH = DESKTOP.h - TOPBAR_H;

  const left = mkCard("Panel / Left (Files)", { w: leftW, h: bodyH });
  left.cornerRadius = 0;
  left.x = 0;
  left.y = bodyY;
  left.effects = [TOKENS.shadowFloat];

  const center = mkCard("Panel / Center (Viewer)", { w: DESKTOP.w - leftW - rightW, h: bodyH });
  center.cornerRadius = 0;
  center.x = leftW;
  center.y = bodyY;
  center.effects = [];

  const right = mkCard("Panel / Right (Chat)", { w: rightW, h: bodyH });
  right.cornerRadius = 0;
  right.x = DESKTOP.w - rightW;
  right.y = bodyY;
  right.effects = [TOKENS.shadowFloat];

  const mkPanelHeader = (title) => {
    const h = figma.createFrame();
    h.name = "Panel Header";
    h.resizeWithoutConstraints(10, 54);
    h.fills = solidFill(TOKENS.surface, 1);
    h.strokes = [];
    const t = mkText(title, { size: 12, style: "Bold", fill: TOKENS.textTitle, lineHeight: 16 });
    t.x = 16;
    t.y = 18;
    h.appendChild(t);
    return h;
  };

  const leftHeader = mkPanelHeader("Files");
  leftHeader.resizeWithoutConstraints(leftW, 54);
  left.appendChild(leftHeader);

  const centerHeader = mkPanelHeader("Document Viewer");
  centerHeader.resizeWithoutConstraints(center.width, 54);
  center.appendChild(centerHeader);

  const rightHeader = mkPanelHeader("Chat");
  rightHeader.resizeWithoutConstraints(rightW, 54);
  right.appendChild(rightHeader);

  // Simple chat input placeholder
  const chatInput = mkCard("Chat Input", { w: rightW - 24, h: 64 });
  chatInput.x = 12;
  chatInput.y = bodyH - 12 - 64;
  chatInput.cornerRadius = TOKENS.radiusCard;
  chatInput.effects = [];
  const placeholder = mkText("Type a question…", { size: 12, style: "Medium", fill: TOKENS.textMuted, lineHeight: 16 });
  placeholder.x = 14;
  placeholder.y = 12;
  chatInput.appendChild(placeholder);
  right.appendChild(chatInput);

  root.appendChild(left);
  root.appendChild(center);
  root.appendChild(right);

  return root;
}

async function run() {
  await ensureFonts();

  const page = findOrCreatePage("DeepDOC");
  await figma.setCurrentPageAsync(page);

  // Re-create frames on each run to avoid partial state drift.
  removeExistingByName(page, "Landing (Projects)");
  removeExistingByName(page, "Workspace (Chat)");
  removeExistingByName(page, "Tokens");

  const landing = buildLandingFrame();
  const workspace = buildWorkspaceFrame();
  const tokens = mkTokensPanel();

  page.appendChild(landing);
  page.appendChild(workspace);
  page.appendChild(tokens);

  landing.x = 0;
  landing.y = 0;

  workspace.x = DESKTOP.w + 160;
  workspace.y = 0;

  tokens.x = 0;
  tokens.y = DESKTOP.h + 120;

  figma.viewport.scrollAndZoomIntoView([landing, workspace, tokens]);
  figma.closePlugin();
}

run().catch((err) => {
  console.error("[deepdoc-design-generator] failed:", err);
  figma.closePlugin();
});

