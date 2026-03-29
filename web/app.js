/* eslint-disable no-console */

const state = {
  docs: [],
  threads: {},
  filteredDocs: [],
  selectedDocId: null,
  currentPage: 1,
  zoom: 1,
  docSearchQuery: '',
  /** 中间文档区视图：document | database | results */
  viewMode: 'document',
  /** 数据库视图：项目内库列表（来自 sampleData / 兜底） */
  databases: [],
  filteredDatabases: [],
  selectedDbId: null,
  /** 每个数据库独立对话（与文档线程分离） */
  dbThreads: {},
  /** 生成结果 / 交付物（PDF+DB 报告、查询导出表等） */
  artifacts: [],
  filteredArtifacts: [],
  selectedArtifactId: null,
  /** landing | workspace */
  appPhase: "landing",
  user: null,
  /** 来自 sampleData 的完整项目包（点击后注入 state） */
  projectsCatalog: [],
  currentProjectId: null,
};

let suppressScrollSync = false;

function reorderPdfSections(pagesWrap, start, end) {
  const frag = document.createDocumentFragment();
  for (let p = start; p <= end; p++) {
    const el = pagesWrap.querySelector(`.pdf-page-section[data-page-no="${p}"]`);
    if (el) frag.appendChild(el);
  }
  pagesWrap.appendChild(frag);
}

function pdfImageSectionNeedsRebuild(section, filename, viewKind) {
  return section.dataset.imgFile !== filename || section.dataset.viewKind !== viewKind;
}

/** 与后端同源；file:// 打开时默认连本机 8765 */
const API_BASE = (() => {
  if (typeof window !== "undefined") {
    const p = window.location;
    if (p.protocol === "http:" || p.protocol === "https:") {
      return `${p.protocol}//${p.host}`;
    }
  }
  return "http://127.0.0.1:8765";
})();

/** 磁盘项目内 PDF 文档的某一页 PNG */
function buildPdfPageImageUrl(doc, filename) {
  if (!doc?.isPdf || !filename || !state.currentProjectId) return null;
  return `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/files/pdf-pages/${encodeURIComponent(doc.id)}/${encodeURIComponent(filename)}`;
}

function rebuildPdfDocDerivedFields() {
  for (const d of state.docs) {
    if (d.isPdf && Array.isArray(d.pdfPageImages)) {
      d.pdfNumPages = d.pdfPageImages.length;
    }
    if (d.isPdf && d.ocrParsed && d.pdfViewMode !== "parsed" && d.pdfViewMode !== "original") {
      d.pdfViewMode = "parsed";
    }
  }
}

function flattenOcrBlockList(doc) {
  const out = [];
  for (const pg of doc.ocrBlocksByPage || []) {
    const pn = pg.pageNo;
    for (const f of pg.files || []) {
      out.push({ pageNo: pn, filename: f });
    }
  }
  return out;
}

function buildOcrBlockImageUrl(doc, filename) {
  if (!doc?.isPdf || !filename || !state.currentProjectId) return null;
  return `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/files/ocr-blocks/${encodeURIComponent(doc.id)}/${encodeURIComponent(filename)}`;
}

function getPdfNavTotal(doc) {
  if (!doc?.isPdf) return 1;
  if (doc.ocrParsed && doc.pdfViewMode === "parsed" && doc.ocrBlocksByPage?.length) {
    const n = flattenOcrBlockList(doc).length;
    return n > 0 ? n : 1;
  }
  return doc.pdfNumPages || doc.pdfPageImages?.length || 1;
}

function isPdfParsedView(doc) {
  return !!(
    doc?.isPdf &&
    doc.ocrParsed &&
    doc.pdfViewMode === "parsed" &&
    doc.ocrBlocksByPage?.length &&
    flattenOcrBlockList(doc).length > 0
  );
}

function updateParseOcrButton() {
  const btn = $("#btnParseOcr");
  if (!btn) return;
  const doc = getSelectedDoc();
  const proj = state.projectsCatalog.find((p) => p.id === state.currentProjectId);
  const disk = proj?.storage === "disk" && state.appPhase === "workspace";
  if (!doc?.isPdf || !disk) {
    btn.disabled = true;
    btn.textContent = "解析";
    btn.title = "请先选择本地项目中的 PDF 文档";
    return;
  }
  btn.disabled = false;
  if (!doc.ocrParsed) {
    btn.textContent = "解析";
    btn.title = "GLM-OCR 解析（首次），每页生成版面可视化（框+标签）";
    return;
  }
  if (doc.pdfViewMode === "parsed") {
    btn.textContent = "原文";
    btn.title = "切换为整页原图";
  } else {
    btn.textContent = "解析";
    btn.title = "切换为版面可视化";
  }
}

// 兜底示例数据：即使你直接双击打开 index.html（没有跑本地 server）也能正常展示。
const fallbackData = {
  docs: [
    {
      id: "doc_1912",
      name: "1912.09555v1.pdf",
      createdAt: "2025-03-23",
      pages: [
        { pageNo: 1, text: "Abstract\nThis paper introduces a web-based document chat mock for demonstration.\nWe simulate file list, page navigation, and a simple assistant response." },
        { pageNo: 2, text: "1. Introduction\nDeep-document assistants help users search, summarize, and reason over long PDFs.\nIn this mock UI we keep everything client-side." },
        { pageNo: 3, text: "3. Formalization and Assumptions\nAssumption A: The interface should be responsive.\nAssumption B: The chat UI must keep context per document.\nConclusion: Use lightweight JS state." },
        { pageNo: 4, text: "4. Experiments\nWe evaluate interaction flows.\n- Click file\n- Search within document\n- Ask chat question\nResult: The UI updates instantly." },
        { pageNo: 5, text: "5. Related Work\nExisting systems provide PDF viewing and chat.\nOur goal: mimic layout and interactions only." },
        { pageNo: 6, text: "6. Conclusion\nThis is a mock implementation for UI design.\nNo real PDF parsing is performed." },
      ],
      docSummary: "示例论文：展示左侧文件列表、中心文档预览与右侧聊天的联动。"
    },
    {
      id: "doc_bilingual",
      name: "样本-多语言设计.pdf",
      createdAt: "2025-01-10",
      pages: [
        { pageNo: 1, text: "Overview\n本示例用于展示界面样式。\n页面内容是静态文本（不解析真实 PDF）。" },
        { pageNo: 2, text: "需求\n- 左侧：文件检索\n- 中间：页码切换与文档关键词搜索\n- 右侧：聊天与追问建议" },
        { pageNo: 3, text: "示例\n你可以输入：总结这份文档、给出要点、下一步建议。\n界面会根据关键词返回不同风格的回复。" }
      ],
      docSummary: "多语言样式示例：用于验证 UI 与交互是否通顺。"
    }
  ],
  threads: {
    doc_1912: {
      meta: "ready",
      suggestions: [
        "总结这份文档",
        "列出关键要点",
        "下一步建议是什么？",
        "解释一下第3页在讲什么"
      ],
      messages: [
        { role: "assistant", text: "已加载《1912.09555v1.pdf》。你可以点击左侧其它文件，或在右侧输入问题（例如“总结这份文档”）。" }
      ]
    },
    doc_bilingual: {
      meta: "ready",
      suggestions: [
        "用要点总结",
        "给出实现建议",
        "把界面交互讲清楚"
      ],
      messages: [
        { role: "assistant", text: "已加载《样本-多语言设计.pdf》。这个页面的内容是示例文本，用于演示搜索高亮与聊天联动。" }
      ]
    }
  }
};

const fallbackArtifacts = [
  {
    id: 'art_report_01',
    name: 'DeepDoc_Analysis_Report.docx',
    kind: 'docx',
    source: 'Sources: 1912.09555v1.pdf × deepdoc_vectors',
    createdAt: '2025-03-22',
    preview:
      'Executive Summary\n\nThis report synthesizes the uploaded PDF with vector-retrieved passages.\n\n( Demo — replace with real DOCX pipeline output. )',
  },
  {
    id: 'art_query_01',
    name: 'metadata_query_export.xlsx',
    kind: 'xlsx',
    source: 'Sources: metadata_store · query export',
    createdAt: '2025-03-21',
    preview:
      'Sheet: query_result\n\ndoc_id\tchunk_id\tscore\n doc_1912\tc_12\t0.91\n\n( Demo — replace with real XLSX. )',
  },
];

const fallbackDatabases = [
  {
    id: 'db_vectors',
    name: 'deepdoc_vectors',
    description: '向量索引 · 文档块嵌入（演示）',
    meta: 'SQLite + FAISS',
  },
  {
    id: 'db_meta',
    name: 'metadata_store',
    description: '元数据与表结构登记',
    meta: 'PostgreSQL',
  },
];

const fallbackUser = {
  displayName: "演示用户",
  email: "demo@deepdoc.local",
  note: "DeepDOC 知识工作台 · 每个项目绑定一套 PDF、数据库与生成结果",
};

const fallbackProjects = [
  {
    id: "proj_paper_vectors",
    name: "论文检索 · 向量索引",
    summary: "1912.09555v1.pdf ↔ deepdoc_vectors ↔ 分析报告（演示）",
    docs: [fallbackData.docs[0]],
    databases: [fallbackDatabases[0]],
    artifacts: [fallbackArtifacts[0]],
    threads: { doc_1912: fallbackData.threads.doc_1912 },
  },
  {
    id: "proj_ui_meta",
    name: "多语言 UI · 元数据",
    summary: "样本 PDF ↔ metadata_store ↔ 查询导出（演示）",
    docs: [fallbackData.docs[1]],
    databases: [fallbackDatabases[1]],
    artifacts: [
      {
        ...fallbackArtifacts[1],
        source: "Sources: 样本-多语言设计.pdf × metadata_store",
      },
    ],
    threads: { doc_bilingual: fallbackData.threads.doc_bilingual },
  },
];

function $(sel) {
  return document.querySelector(sel);
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function highlightText(text, query) {
  if (!query) return escapeHtml(text);
  const q = query.trim();
  if (!q) return escapeHtml(text);
  const safeText = escapeHtml(text);
  // 简化高亮：仅对 escaped 后的字符串做替换可能与原始索引略有差异，但 UI足够用于演示。
  // 对于小范围 demo 足够。
  const safeQ = escapeHtml(q);
  const re = new RegExp(safeQ.replaceAll(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
  return safeText.replace(re, (m) => `<mark>${m}</mark>`);
}

function formatDate(iso) {
  return iso || "-";
}

/** 切换中间区域视图（不改变三栏整体布局） */
function setViewMode(mode) {
  const allowed = ["document", "database", "results"];
  if (!allowed.includes(mode)) return;
  state.viewMode = mode;

  const ids = {
    document: "centerViewDocument",
    database: "centerViewDatabase",
    results: "centerViewResults",
  };
  Object.entries(ids).forEach(([key, id]) => {
    const el = document.getElementById(id);
    if (!el) return;
    const active = key === mode;
    el.classList.toggle("is-active", active);
    el.setAttribute("aria-hidden", active ? "false" : "true");
  });

  document.querySelectorAll(".view-tab").forEach((btn) => {
    const active = btn.dataset.view === mode;
    btn.classList.toggle("is-active", active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
  });

  const ctrl = document.querySelector(".doc-controls");
  if (ctrl) {
    ctrl.classList.toggle("is-disabled", mode !== "document");
    ctrl.setAttribute("aria-disabled", mode !== "document" ? "true" : "false");
  }

  const leftFiles = $("#leftSectionFiles");
  const leftDb = $("#leftSectionDatabase");
  const leftRes = $("#leftSectionResults");
  if (leftFiles && leftDb && leftRes) {
    leftFiles.hidden = mode !== "document";
    leftDb.hidden = mode !== "database";
    leftRes.hidden = mode !== "results";
  }

  const pr = $("#panelRight");
  if (pr) pr.dataset.viewmode = mode;

  if (mode === "database" && !state.selectedDbId && state.databases.length) {
    state.selectedDbId = state.databases[0].id;
  }
  if (mode === "results" && !state.selectedArtifactId && state.artifacts.length) {
    state.selectedArtifactId = state.artifacts[0].id;
  }

  renderCenterHeader();

  if (mode === "database") {
    renderDbList();
    renderDbChat();
  } else if (mode === "results") {
    restoreDocumentChatUI();
    renderFileList();
    renderArtifactList();
    renderChat();
  } else {
    restoreDocumentChatUI();
    renderFileList();
    renderChat();
    renderDocumentContinuous();
    updateParseOcrButton();
  }
}

/** 中间顶栏标题：文档名 / 数据库名 / 交付物文件名 */
function renderCenterHeader() {
  if (state.viewMode === "database") {
    const db = getSelectedDb();
    if (!db) {
      $("#docName").textContent = "请选择一个数据库";
      $("#docSubmeta").textContent = "-";
    } else {
      $("#docName").textContent = db.name;
      $("#docSubmeta").textContent = db.description || db.meta || "";
    }
    updateDatabaseCenterPanel();
    return;
  }
  if (state.viewMode === "results") {
    const a = getSelectedArtifact();
    if (!a) {
      $("#docName").textContent = "Select a deliverable";
      $("#docSubmeta").textContent = "-";
    } else {
      $("#docName").textContent = a.name;
      $("#docSubmeta").textContent = a.source || `Updated ${formatDate(a.createdAt)}`;
    }
    renderResultsCenterPanel();
    return;
  }
  renderDocHeader();
}

function getSelectedArtifact() {
  return state.artifacts.find((x) => x.id === state.selectedArtifactId) || null;
}

function renderArtifactList() {
  const list = $("#artifactList");
  if (!list) return;
  const count = state.filteredArtifacts.length;
  const cEl = $("#artifactCount");
  if (cEl) cEl.textContent = String(count);
  list.innerHTML = "";

  state.filteredArtifacts.forEach((a) => {
    const li = document.createElement("li");
    li.className = "file-item" + (a.id === state.selectedArtifactId ? " active" : "");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", a.id === state.selectedArtifactId ? "true" : "false");
    li.dataset.artifactId = a.id;

    const icon = document.createElement("div");
    icon.className = "file-icon file-icon--artifact";
    icon.textContent = a.kind === "xlsx" ? "X" : "W";

    const main = document.createElement("div");
    main.className = "file-main";

    const name = document.createElement("div");
    name.className = "file-name";
    name.textContent = a.name;

    const sub = document.createElement("div");
    sub.className = "file-sub";
    sub.textContent = `${(a.kind || "").toUpperCase()} · ${formatDate(a.createdAt)}`;

    main.appendChild(name);
    main.appendChild(sub);

    li.appendChild(icon);
    li.appendChild(main);
    list.appendChild(li);
  });
}

function setSelectedArtifact(id) {
  state.selectedArtifactId = id;
  renderArtifactList();
  renderCenterHeader();
}

function renderResultsCenterPanel() {
  const a = getSelectedArtifact();
  const badge = $("#resultsKindBadge");
  const created = $("#resultsCreatedAt");
  const title = $("#resultsDetailTitle");
  const source = $("#resultsDetailSource");
  const preview = $("#resultsPreview");

  if (!a) {
    if (badge) badge.textContent = "—";
    if (created) created.textContent = "";
    if (title) title.textContent = "—";
    if (source) source.textContent = "从左侧选择一项生成结果。";
    if (preview) preview.textContent = "";
    return;
  }

  const kind = (a.kind || "file").toUpperCase();
  if (badge) badge.textContent = kind;
  if (created) created.textContent = a.createdAt ? ` · ${a.createdAt}` : "";
  if (title) title.textContent = a.name;
  if (source) source.textContent = a.source || "";
  if (preview) preview.textContent = a.preview || "（无预览文本）";
}

function getSelectedDb() {
  return state.databases.find((d) => d.id === state.selectedDbId) || null;
}

function updateDatabaseCenterPanel() {
  const db = getSelectedDb();
  const nameHint = $("#dbViewNameHint");
  const desc = $("#dbViewDesc");
  if (nameHint) nameHint.textContent = db ? db.name : "—";
  if (desc) {
    desc.textContent = db
      ? db.description || "可在此接入向量检索、元数据表或知识库条目。"
      : "从左侧选择一个数据库以查看说明与连接信息。";
  }
}

function renderDbList() {
  const list = $("#dbList");
  if (!list) return;
  const count = state.filteredDatabases.length;
  const cEl = $("#dbCount");
  if (cEl) cEl.textContent = String(count);
  list.innerHTML = "";

  state.filteredDatabases.forEach((db, idx) => {
    const li = document.createElement("li");
    li.className = "file-item" + (db.id === state.selectedDbId ? " active" : "");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", db.id === state.selectedDbId ? "true" : "false");
    li.dataset.dbId = db.id;

    const icon = document.createElement("div");
    icon.className = "file-icon";
    icon.textContent = "DB";

    const main = document.createElement("div");
    main.className = "file-main";

    const name = document.createElement("div");
    name.className = "file-name";
    name.textContent = db.name;

    const sub = document.createElement("div");
    sub.className = "file-sub";
    sub.textContent = db.meta ? `${db.meta}` : "";

    main.appendChild(name);
    main.appendChild(sub);

    li.appendChild(icon);
    li.appendChild(main);
    list.appendChild(li);
  });
}

function setSelectedDb(dbId) {
  state.selectedDbId = dbId;
  renderDbList();
  renderCenterHeader();
  renderDbChat();
}

function restoreDocumentChatUI() {
  const st = $("#suggestTitle");
  if (st) st.style.display = "";
  const rt = $("#rightPanelTitle");
  if (rt) rt.textContent = "Chat";
  const ph = $("#chatText");
  if (ph) {
    ph.placeholder =
      "Type a question...（例如：总结这份文档、给出要点、下一步建议）";
  }
}

/** 数据库视图右侧：无 Follow up、无文档向导语境 */
function renderDbChat() {
  const wrap = $("#chatMessages");
  if (!wrap) return;
  wrap.innerHTML = "";
  $("#suggestions").querySelectorAll(".chip-row").forEach((n) => n.remove());
  const st = $("#suggestTitle");
  if (st) st.style.display = "none";
  const rt = $("#rightPanelTitle");
  if (rt) rt.textContent = "Query";

  const ph = $("#chatText");
  if (ph) {
    ph.placeholder = "输入查询描述或 SQL 说明（演示，非真实执行）";
  }

  const db = getSelectedDb();
  if (!db) {
    appendMessage("assistant", "请从左侧选择一个数据库。");
    setThreadMeta("idle");
    return;
  }

  if (!state.dbThreads[db.id]) {
    state.dbThreads[db.id] = {
      meta: "ready",
      messages: [
        {
          role: "assistant",
          text: `已选择数据库「${db.name}」。此处为与文档/阅读无关的查询助手（演示）。`,
        },
      ],
    };
  }

  const thread = state.dbThreads[db.id];
  setThreadMeta(thread.meta || "ready");
  const msgs = thread.messages || [];
  msgs.forEach((m) => appendMessage(m.role, m.text));
}

function simulateDbReply(db, userText) {
  const t = (userText || "").trim();
  if (!t) return "请输入内容后再发送。";
  return `（演示）针对库「${db.name}」收到：${t}\n实际部署时请连接后端执行查询或向量检索。`;
}

async function handleDbMessage(userText) {
  const db = getSelectedDb();
  if (!db) {
    appendMessage("assistant", "请先从左侧选择一个数据库。");
    return;
  }
  const text = (userText || "").trim();
  if (!text) return;

  appendMessage("user", text);
  if (!state.dbThreads[db.id]) state.dbThreads[db.id] = { messages: [], meta: "ready" };
  state.dbThreads[db.id].messages = state.dbThreads[db.id].messages || [];
  state.dbThreads[db.id].messages.push({ role: "user", text });

  setThreadMeta("thinking...");
  await new Promise((r) => setTimeout(r, 450));

  const reply = simulateDbReply(db, text);
  appendMessage("assistant", reply);
  state.dbThreads[db.id].messages.push({ role: "assistant", text: reply });
  state.dbThreads[db.id].meta = "ready";
  setThreadMeta("ready");
}

function setThreadMeta(text) {
  $("#threadMeta").textContent = text;
}

function renderFileList() {
  const list = $("#fileList");
  const count = state.filteredDocs.length;
  $("#filesCount").textContent = String(count);
  list.innerHTML = "";

  state.filteredDocs.forEach((doc, idx) => {
    const li = document.createElement("li");
    li.className = "file-item" + (doc.id === state.selectedDocId ? " active" : "");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", doc.id === state.selectedDocId ? "true" : "false");
    li.dataset.docId = doc.id;

    const icon = document.createElement("div");
    icon.className = "file-icon";
    icon.textContent = idx % 2 === 0 ? "D" : "P";

    const main = document.createElement("div");
    main.className = "file-main";

    const name = document.createElement("div");
    name.className = "file-name";
    name.textContent = doc.name;

    const sub = document.createElement("div");
    sub.className = "file-sub";
    sub.textContent = doc.isPdf
      ? doc.pdfNumPages
        ? `Created: ${formatDate(doc.createdAt)} • Pages: ${doc.pdfNumPages}`
        : `Created: ${formatDate(doc.createdAt)} • PDF`
      : `Created: ${formatDate(doc.createdAt)} • Pages: ${doc.pages?.length ?? 0}`;

    main.appendChild(name);
    main.appendChild(sub);

    const del = document.createElement("button");
    del.type = "button";
    del.className = "file-item-delete";
    del.title = "删除";
    del.setAttribute("aria-label", `删除 ${doc.name}`);
    del.textContent = "×";

    li.appendChild(icon);
    li.appendChild(main);
    li.appendChild(del);
    list.appendChild(li);
  });
}

function getSelectedDoc() {
  return state.docs.find((d) => d.id === state.selectedDocId) || null;
}

async function handleParseOcrClick() {
  const doc = getSelectedDoc();
  const proj = state.projectsCatalog.find((p) => p.id === state.currentProjectId);
  if (!doc?.isPdf || proj?.storage !== "disk" || state.appPhase !== "workspace") return;

  if (doc.ocrParsed) {
    doc.pdfViewMode = doc.pdfViewMode === "parsed" ? "original" : "parsed";
    state.currentPage = 1;
    renderDocHeader();
    renderDocumentContinuous();
    updateParseOcrButton();
    await saveWorkspaceToDisk();
    return;
  }

  const btn = $("#btnParseOcr");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "解析中…";
  }
  try {
    const res = await fetch(
      `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(doc.id)}/ocr-parse`,
      { method: "POST" }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(typeof err.detail === "string" ? err.detail : `解析失败 (${res.status})`);
      return;
    }
    const data = await res.json();
    const updated = data.doc;
    if (updated) {
      const idx = state.docs.findIndex((d) => d.id === doc.id);
      if (idx >= 0) {
        state.docs[idx] = { ...state.docs[idx], ...updated };
      }
    }
    state.currentPage = 1;
    renderDocHeader();
    renderDocumentContinuous();
    renderFileList();
    updateParseOcrButton();
  } catch (e) {
    console.warn(e);
    alert("解析失败，请确认后端已启动。");
  } finally {
    updateParseOcrButton();
  }
}

async function deleteDocument(docId) {
  const doc = state.docs.find((d) => d.id === docId);
  if (!doc) return;
  if (!confirm(`确定删除「${doc.name}」？此操作不可恢复。`)) return;

  const proj = state.projectsCatalog.find((p) => p.id === state.currentProjectId);
  const useApi =
    state.currentProjectId &&
    proj?.storage === "disk" &&
    state.appPhase === "workspace";

  if (useApi) {
    try {
      const res = await fetch(
        `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}`,
        { method: "DELETE" }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        alert(typeof detail === "string" ? detail : `删除失败 (${res.status})`);
        return;
      }
      const data = await res.json().catch(() => ({}));
      state.docs = state.docs.filter((d) => d.id !== docId);
      delete state.threads[docId];
      if (Object.prototype.hasOwnProperty.call(data, "selectedDocId")) {
        state.selectedDocId = data.selectedDocId;
      } else if (state.selectedDocId === docId) {
        state.selectedDocId = state.docs[0]?.id ?? null;
      }
    } catch (e) {
      console.warn(e);
      alert("删除失败，请确认后端已启动。");
      return;
    }
  } else {
    state.docs = state.docs.filter((d) => d.id !== docId);
    delete state.threads[docId];
    if (state.selectedDocId === docId) {
      state.selectedDocId = null;
    }
  }

  const q = ($("#fileSearch") && $("#fileSearch").value.trim().toLowerCase()) || "";
  if (!q) state.filteredDocs = state.docs.slice();
  else state.filteredDocs = state.docs.filter((d) => d.name.toLowerCase().includes(q));

  if (state.docs.length && !state.selectedDocId) {
    initThreadSelection();
  }
  if (
    state.selectedDocId &&
    !state.filteredDocs.some((d) => d.id === state.selectedDocId)
  ) {
    const next = state.filteredDocs[0] || state.docs[0];
    state.selectedDocId = next ? next.id : null;
  }

  renderFileList();
  if (state.viewMode === "document") {
    renderDocHeader();
    renderDocumentContinuous();
    renderChat();
  } else {
    renderCenterHeader();
  }
}

function setSelectedDoc(docId, { keepMessages = false } = {}) {
  state.selectedDocId = docId;
  state.currentPage = 1;
  state.docSearchQuery = "";
  $("#docSearch").value = "";
  $("#pageNum").value = String(1);

  renderFileList();
  if (state.viewMode === "document") {
    renderDocHeader();
    renderDocumentContinuous();
    if (!keepMessages) renderChat();
  } else {
    renderCenterHeader();
  }
}

function renderDocHeader() {
  const doc = getSelectedDoc();
  if (!doc) {
    $("#docName").textContent = "请选择一个文件";
    $("#docSubmeta").textContent = "-";
    $("#pageTotal").textContent = "/ 1";
    $("#viewerHint").style.display = "block";
    updateParseOcrButton();
    return;
  }

  $("#viewerHint").style.display = "none";
  $("#docName").textContent = doc.name;
  if (doc.isPdf && doc.ocrParsed) {
    $("#docSubmeta").textContent =
      (doc.pdfViewMode === "parsed" ? "解析视图 · " : "原文视图 · ") +
      (doc.docSummary || `Created: ${formatDate(doc.createdAt)}`);
  } else {
    $("#docSubmeta").textContent = doc.docSummary || `Created: ${formatDate(doc.createdAt)}`;
  }

  if (doc.isPdf) {
    const total = getPdfNavTotal(doc);
    if (total) {
      $("#pageTotal").textContent = `/ ${total}`;
      $("#pageNum").max = String(total);
      if (state.currentPage > total) state.currentPage = 1;
      $("#pageNum").value = String(state.currentPage);
    } else {
      $("#pageTotal").textContent = "/ …";
      $("#pageNum").max = "9999";
      $("#pageNum").value = String(state.currentPage);
    }
    updateParseOcrButton();
    return;
  }

  const total = doc.pages?.length ?? 1;
  $("#pageTotal").textContent = `/ ${total}`;
  $("#pageNum").max = String(total);
  if (state.currentPage > total) state.currentPage = 1;
  $("#pageNum").value = String(state.currentPage);
  updateParseOcrButton();
}

function scrollToPage(pageNo) {
  const el = document.querySelector(`#pages [data-page-no="${pageNo}"]`);
  if (!el) return;
  // “连续阅读”模式下，滚动定位用于上一页/下一页/搜索跳转。
  suppressScrollSync = true;
  el.scrollIntoView({ behavior: "auto", block: "start" });
  window.setTimeout(() => {
    suppressScrollSync = false;
  }, 250);
}

function renderDocumentContinuous() {
  const doc = getSelectedDoc();
  const pagesWrap = $("#pages");

  document.documentElement.style.setProperty("--zoom", String(state.zoom));

  if (doc && doc.isPdf) {
    const images = doc.pdfPageImages;
    const pageCount =
      doc.pdfNumPages ||
      (Array.isArray(images) ? images.length : 0) ||
      0;
    const parsedView = isPdfParsedView(doc);
    const flatBlocks = parsedView ? flattenOcrBlockList(doc) : [];

    if (parsedView && flatBlocks.length === 0) {
      pagesWrap.innerHTML = "";
      delete pagesWrap.dataset.pdfDocId;
      delete pagesWrap.dataset.pdfViewKey;
      const hint = document.createElement("div");
      hint.className = "viewer-hint";
      hint.textContent = "解析数据为空，请重新解析或切换为原文。";
      pagesWrap.appendChild(hint);
      return;
    }

    if (
      !parsedView &&
      (!state.currentProjectId ||
        !Array.isArray(images) ||
        images.length === 0 ||
        !pageCount)
    ) {
      pagesWrap.innerHTML = "";
      delete pagesWrap.dataset.pdfDocId;
      delete pagesWrap.dataset.pdfViewKey;
      const hint = document.createElement("div");
      hint.className = "viewer-hint";
      hint.textContent =
        "无法展示页面图片：缺少项目数据或本地未生成页面图。请在服务端打开项目后重新上传 PDF。";
      pagesWrap.appendChild(hint);
      return;
    }
    $("#viewerHint").style.display = "none";

    doc.pdfNumPages = pageCount;
    const numPages = parsedView ? flatBlocks.length : pageCount;
    renderDocHeader();
    const cur = clamp(state.currentPage, 1, numPages);
    state.currentPage = cur;
    $("#pageNum").value = String(cur);
    $("#pageTotal").textContent = `/ ${numPages}`;
    $("#pageNum").max = String(numPages);

    const viewKey = `${doc.id}|${parsedView ? "p" : "o"}`;
    if (pagesWrap.dataset.pdfViewKey !== viewKey) {
      pagesWrap.innerHTML = "";
      pagesWrap.dataset.pdfViewKey = viewKey;
      pagesWrap.dataset.pdfDocId = doc.id;
    } else if (String(pagesWrap.dataset.pdfDocId || "") !== doc.id) {
      pagesWrap.innerHTML = "";
      pagesWrap.dataset.pdfDocId = doc.id;
      pagesWrap.dataset.pdfViewKey = viewKey;
    }

    const start = 1;
    const end = numPages;

    pagesWrap.querySelectorAll(".pdf-page-section[data-page-no]").forEach((el) => {
      const pn = Number(el.dataset.pageNo);
      if (pn > numPages || pn < 1) el.remove();
    });

    const viewKind = parsedView ? "parsed" : "original";

    for (let p = start; p <= end; p++) {
      let fn;
      let src;
      let alt;
      if (parsedView) {
        const b = flatBlocks[p - 1];
        fn = b.filename;
        src = buildOcrBlockImageUrl(doc, fn);
        alt = `第 ${b.pageNo} 页 · 版面可视化`;
      } else {
        fn = images[p - 1];
        src = buildPdfPageImageUrl(doc, fn);
        alt = `第 ${p} 页`;
      }
      if (!src) continue;

      const existing = pagesWrap.querySelector(`.pdf-page-section[data-page-no="${p}"]`);
      if (existing && !pdfImageSectionNeedsRebuild(existing, fn, viewKind)) {
        continue;
      }
      if (existing) existing.remove();

      const section = document.createElement("div");
      section.className = "page-section pdf-page-section";
      section.dataset.pageNo = String(p);
      section.dataset.imgFile = fn;
      section.dataset.viewKind = viewKind;

      const wrap = document.createElement("div");
      wrap.className = "pdf-page-img-wrap";

      const img = document.createElement("img");
      img.className = "pdf-page-img";
      img.alt = alt;
      img.decoding = "sync";
      img.src = src;

      wrap.appendChild(img);
      section.appendChild(wrap);
      pagesWrap.appendChild(section);
    }

    reorderPdfSections(pagesWrap, start, end);
    renderFileList();

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        scrollToPage(cur);
      });
    });
    return;
  }

  pagesWrap.innerHTML = "";
  delete pagesWrap.dataset.pdfDocId;
  delete pagesWrap.dataset.pdfViewKey;

  const total = doc?.pages?.length ?? 0;
  if (!doc || total === 0) return;

  for (const p of doc.pages) {
    const section = document.createElement("div");
    section.className = "page-section";
    section.dataset.pageNo = String(p.pageNo);

    const head = document.createElement("div");
    head.className = "page-section-head";

    const badge = document.createElement("div");
    badge.className = "page-badge";
    badge.textContent = `Page ${p.pageNo}`;
    head.appendChild(badge);

    const text = document.createElement("div");
    text.className = "page-text";

    // 将一页内容按“空行”拆成多个分块（模拟 OCR 的 region 粒度）。
    // 当你接入真实 OCR json_result 后，可以在这里换成真实 blocks 渲染即可。
    const pageRaw = String(p.text ?? "");
    const blocks = pageRaw
      .replace(/\r\n/g, "\n")
      .split(/\n\s*\n/g)
      .map((s) => s.trimEnd())
      .filter((s) => s.trim().length > 0);

    let blockIndex = 0;
    for (const b of blocks) {
      const span = document.createElement("span");
      span.className = "ocr-block";
      span.dataset.blockId = `${p.pageNo}_${blockIndex}`;
      span.innerHTML = highlightText(b, state.docSearchQuery);
      text.appendChild(span);

      // 块间用双换行模拟段落间距
      text.appendChild(document.createTextNode("\n\n"));
      blockIndex += 1;
    }

    section.appendChild(head);
    section.appendChild(text);
    pagesWrap.appendChild(section);
  }

  // 渲染完成后，定位到当前页（上一页/下一页/搜索跳转会改这个状态）。
  scrollToPage(state.currentPage);
}

function renderChat() {
  const docId = state.selectedDocId;
  const thread = state.threads[docId] || {
    meta: "new",
    messages: [{ role: "assistant", text: `已加载《${getSelectedDoc()?.name || "未命名"}》。请提问。` }],
    suggestions: ["总结这份文档", "列出关键要点", "下一步建议是什么？"]
  };

  setThreadMeta(thread.meta || "ready");
  $("#chatMessages").innerHTML = "";

  const msgs = thread.messages || [];
  msgs.forEach((m) => appendMessage(m.role, m.text));

  renderSuggestions(thread.suggestions || []);
}

function appendMessage(role, text) {
  const wrap = $("#chatMessages");
  const row = document.createElement("div");
  row.className = `msg ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const r = document.createElement("div");
  r.className = "role";
  r.textContent = role === "user" ? "You" : "Assistant";

  const t = document.createElement("div");
  t.className = "text";
  t.textContent = text;

  bubble.appendChild(r);
  bubble.appendChild(t);
  row.appendChild(bubble);
  wrap.appendChild(row);
  wrap.scrollTop = wrap.scrollHeight;
}

function renderSuggestions(suggestions) {
  const el = $("#suggestions");
  // 只移除之前生成的 chip 行，保留顶部标题。
  el.querySelectorAll(".chip-row").forEach((n) => n.remove());
  if (!suggestions || suggestions.length === 0) return;

  const row = document.createElement("div");
  row.className = "chip-row";
  suggestions.slice(0, 6).forEach((s) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = s;
    chip.addEventListener("click", () => {
      $("#chatText").value = s;
      $("#chatText").focus();
    });
    row.appendChild(chip);
  });
  el.appendChild(row);
}

function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function setCurrentPage(pageNo, { withRender = false } = {}) {
  const doc = getSelectedDoc();
  if (!doc) return;
  if (doc.isPdf) {
    const total = getPdfNavTotal(doc);
    if (total) {
      state.currentPage = clamp(Number(pageNo) || 1, 1, total);
    } else {
      state.currentPage = 1;
    }
    $("#pageNum").value = String(state.currentPage);
    if (total) renderDocumentContinuous();
    return;
  }
  const total = doc.pages?.length ?? 1;
  state.currentPage = clamp(Number(pageNo) || 1, 1, total);
  $("#pageNum").value = String(state.currentPage);
  if (withRender) renderDocumentContinuous();
  else scrollToPage(state.currentPage);
}

function simulateAssistantReply(doc, userText) {
  const t = (userText || "").trim();
  const lower = t.toLowerCase();
  const name = doc?.name || "当前文档";
  const page = state.currentPage;

  // 简单规则：根据关键词返回不同“风格”的回复（纯演示）
  if (!t) return "请输入问题后再发送。";

  if (lower.includes("总结") || lower.includes("summary") || lower.includes("sum")) {
    return `《${name}》的要点总结如下（基于示例页面文本）：\n1) 该界面演示了“三栏布局 + JS 交互”。\n2) 支持文件切换、页码切换与文档内搜索高亮。\n3) 聊天会在每个文件上保留独立的对话线程（演示版）。`;
  }

  if (lower.includes("关键") || lower.includes("要点") || lower.includes("bullet") || lower.includes("list")) {
    return `《${name}》关键要点（演示版）：\n- UI 结构：左侧文件列表、中心文档预览、右侧聊天。\n- 交互：搜索过滤、页码导航、缩放、发送消息。\n- 数据：使用示例数据渲染，不解析真实 PDF。`;
  }

  if (lower.includes("下一步") || lower.includes("next") || lower.includes("recommend")) {
    return `下一步建议（演示版）：\n1) 上传的 PDF 已在服务端转为页面图片；可将“文档搜索”接到全文索引。\n2) 聊天回复对接你的后端/LLM，并把对话状态持久化到服务端。`;
  }

  if (lower.includes("第") || lower.includes("page") || lower.includes("页")) {
    const inferred = (() => {
      const m = t.match(/(\d+)/);
      if (m && m[1]) return Number(m[1]);
      return page;
    })();
    const p = doc?.pages?.find((x) => x.pageNo === inferred);
    const snippet = p?.text ? p.text.slice(0, 160) : "（未找到对应示例页）";
    return `关于第 ${inferred} 页（演示版读取示例文本）：\n${snippet}${snippet.length >= 160 ? "..." : ""}\n你可以继续问“总结要点”或“下一步建议”。`;
  }

  return `我已读取《${name}》当前上下文（演示版）。\n你问的是：${t}\n为了更贴近你的需求，可以再加一句具体目标，例如“给出要点/总结/下一步建议”。`;
}

async function handleSendMessage(userText) {
  if (state.viewMode === "database") {
    await handleDbMessage(userText);
    return;
  }

  const doc = getSelectedDoc();
  if (!doc) {
    appendMessage("assistant", "请先从左侧选择一个文件。");
    return;
  }

  const text = (userText || "").trim();
  if (!text) return;

  // 追加 user
  appendMessage("user", text);

  const docId = doc.id;
  if (!state.threads[docId]) state.threads[docId] = { messages: [], suggestions: [], meta: "ready" };
  state.threads[docId].messages = state.threads[docId].messages || [];
  state.threads[docId].messages.push({ role: "user", text });

  setThreadMeta("thinking...");
  // 演示延迟
  await new Promise((r) => setTimeout(r, 550));

  const reply = simulateAssistantReply(doc, text);
  appendMessage("assistant", reply);
  state.threads[docId].messages.push({ role: "assistant", text: reply });
  setThreadMeta("ready");

  const hint = $("#resultsChatHint");
  if (hint) {
    if (state.viewMode === "results") {
      const preview = reply.length > 220 ? `${reply.slice(0, 220)}…` : reply;
      hint.textContent = `与当前文档相关的对话摘要（演示）：\n${preview}`;
      hint.hidden = false;
    } else {
      hint.hidden = true;
    }
  }
}

function setupEventHandlers() {
  $("#btnBackToProjects")?.addEventListener("click", () => exitToLanding());

  $("#projectGrid")?.addEventListener("click", (e) => {
    const card = e.target.closest(".project-card");
    if (!card?.dataset.projectId) return;
    void enterWorkspace(card.dataset.projectId).catch((err) => console.warn("[app] enter workspace", err));
  });

  const modal = $("#createProjectModal");
  const openCreate = () => {
    if (modal) modal.hidden = false;
    $("#inputProjectName")?.focus();
  };
  const closeCreate = () => {
    if (modal) modal.hidden = true;
    const inp = $("#inputProjectName");
    if (inp) inp.value = "";
  };
  $("#btnCreateProject")?.addEventListener("click", openCreate);
  modal?.addEventListener("click", (e) => {
    if (e.target?.dataset?.close === "modal") closeCreate();
  });
  $("#btnCancelCreate")?.addEventListener("click", closeCreate);
  $("#btnSubmitCreate")?.addEventListener("click", () => void submitCreateProject(closeCreate));

  window.addEventListener("beforeunload", () => {
    if (state.appPhase !== "workspace") return;
    const proj = state.projectsCatalog.find((p) => p.id === state.currentProjectId);
    if (!proj || proj.storage !== "disk") return;
    const body = JSON.stringify({
      threads: state.threads,
      dbThreads: state.dbThreads,
      docs: state.docs,
      databases: state.databases,
      artifacts: state.artifacts,
      selectedDocId: state.selectedDocId,
      selectedDbId: state.selectedDbId,
      selectedArtifactId: state.selectedArtifactId,
      viewMode: state.viewMode,
    });
    fetch(`${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/workspace`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    }).catch(() => {});
  });

  $("#fileSearch").addEventListener("input", () => {
    const q = $("#fileSearch").value.trim().toLowerCase();
    if (!q) state.filteredDocs = state.docs.slice();
    else state.filteredDocs = state.docs.filter((d) => d.name.toLowerCase().includes(q));
    renderFileList();
    // 若当前选中项被过滤掉，自动选中第一项
    if (state.selectedDocId && !state.filteredDocs.some((d) => d.id === state.selectedDocId)) {
      const next = state.filteredDocs[0];
      if (next) setSelectedDoc(next.id);
    }
  });

  $("#fileList").addEventListener("click", (e) => {
    if (e.target.closest(".file-item-delete")) {
      e.preventDefault();
      e.stopPropagation();
      const row = e.target.closest(".file-item");
      if (row?.dataset.docId) void deleteDocument(row.dataset.docId);
      return;
    }
    const item = e.target.closest(".file-item");
    if (!item) return;
    const docId = item.dataset.docId;
    setSelectedDoc(docId);
  });

  const dbList = $("#dbList");
  if (dbList) {
    dbList.addEventListener("click", (e) => {
      const item = e.target.closest(".file-item");
      if (!item || !item.dataset.dbId) return;
      setSelectedDb(item.dataset.dbId);
    });
  }

  $("#dbSearch").addEventListener("input", () => {
    const q = $("#dbSearch").value.trim().toLowerCase();
    if (!q) state.filteredDatabases = state.databases.slice();
    else {
      state.filteredDatabases = state.databases.filter(
        (d) =>
          d.name.toLowerCase().includes(q) ||
          (d.description && d.description.toLowerCase().includes(q)) ||
          (d.meta && d.meta.toLowerCase().includes(q))
      );
    }
    renderDbList();
    if (
      state.selectedDbId &&
      !state.filteredDatabases.some((d) => d.id === state.selectedDbId)
    ) {
      const next = state.filteredDatabases[0];
      if (next) setSelectedDb(next.id);
    }
  });

  const artifactList = $("#artifactList");
  if (artifactList) {
    artifactList.addEventListener("click", (e) => {
      const item = e.target.closest(".file-item");
      if (!item || !item.dataset.artifactId) return;
      setSelectedArtifact(item.dataset.artifactId);
    });
  }

  const artifactSearch = $("#artifactSearch");
  if (artifactSearch) {
    artifactSearch.addEventListener("input", () => {
      const q = $("#artifactSearch").value.trim().toLowerCase();
      if (!q) state.filteredArtifacts = state.artifacts.slice();
      else {
        state.filteredArtifacts = state.artifacts.filter(
          (a) =>
            a.name.toLowerCase().includes(q) ||
            (a.source && a.source.toLowerCase().includes(q)) ||
            (a.kind && a.kind.toLowerCase().includes(q))
        );
      }
      renderArtifactList();
      if (
        state.selectedArtifactId &&
        !state.filteredArtifacts.some((a) => a.id === state.selectedArtifactId)
      ) {
        const next = state.filteredArtifacts[0];
        if (next) setSelectedArtifact(next.id);
      }
    });
  }

  $("#btnPrevPage").addEventListener("click", () => setCurrentPage(state.currentPage - 1));
  $("#btnNextPage").addEventListener("click", () => setCurrentPage(state.currentPage + 1));

  $("#pageNum").addEventListener("change", (e) => {
    setCurrentPage(Number(e.target.value));
  });

  $("#zoomRange").addEventListener("input", (e) => {
    state.zoom = Number(e.target.value) || 1;
    document.documentElement.style.setProperty("--zoom", String(state.zoom));
  });

  $("#docSearch").addEventListener("input", (e) => {
    const q = e.target.value.trim();
    state.docSearchQuery = q;

    const doc = getSelectedDoc();
    if (doc?.isPdf) {
      return;
    }
    if (doc && q) {
      const first = doc.pages?.find((p) =>
        String(p.text ?? "").toLowerCase().includes(q.toLowerCase())
      );
      if (first) {
        state.currentPage = clamp(first.pageNo, 1, doc.pages?.length ?? 1);
        $("#pageNum").value = String(state.currentPage);
      }
      renderDocumentContinuous();
    } else {
      renderDocumentContinuous();
    }
  });

  $("#chatForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = $("#chatText").value;
    $("#chatText").value = "";
    await handleSendMessage(text);
  });

  const btnParseOcr = $("#btnParseOcr");
  if (btnParseOcr) {
    btnParseOcr.addEventListener("click", () => void handleParseOcrClick());
  }

  $("#btnUpload").addEventListener("click", () => $("#fileInput").click());

  $("#fileInput").addEventListener("change", async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;

    if (!f.name.toLowerCase().endsWith(".pdf")) {
      alert("请选择 PDF 文件");
      $("#fileInput").value = "";
      return;
    }

    const proj = state.projectsCatalog.find((p) => p.id === state.currentProjectId);
    if (
      state.currentProjectId &&
      proj?.storage === "disk" &&
      state.appPhase === "workspace"
    ) {
      try {
        const fd = new FormData();
        fd.append("file", f, f.name);
        const res = await fetch(
          `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/upload/pdf`,
          { method: "POST", body: fd }
        );
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          const detail = err.detail;
          alert(
            typeof detail === "string"
              ? detail
              : Array.isArray(detail)
                ? detail.map((x) => x.msg || JSON.stringify(x)).join("\n")
                : `上传失败 (${res.status})`
          );
          $("#fileInput").value = "";
          return;
        }
        const data = await res.json();
        const pdfFileName = data.savedFilename;
        const newDocId = data.docId;
        const pageImages = Array.isArray(data.pageImages) ? data.pageImages : [];
        const pageCount = Number(data.pageCount) || pageImages.length;
        const uploadedDoc = {
          id: newDocId,
          name: f.name,
          createdAt: new Date().toISOString().slice(0, 10),
          isPdf: true,
          pdfFileName,
          pdfPageImages: pageImages,
          pdfNumPages: pageCount,
          pdfViewMode: "original",
          pages: [],
          docSummary: "已上传 PDF，服务端已转为页面图片并保存在项目目录。"
        };

        state.docs.unshift(uploadedDoc);
        state.filteredDocs = state.docs.slice();

        state.threads[newDocId] = {
          meta: "ready",
          suggestions: ["总结这份文档", "列出要点", "下一步建议是什么？"],
          messages: [
            {
              role: "assistant",
              text: `已上传并保存《${f.name}》，已生成 ${pageCount} 张页面图，中间区域按页展示。`
            }
          ]
        };

        $("#fileInput").value = "";
        setSelectedDoc(newDocId);
        await saveWorkspaceToDisk();
        return;
      } catch (err) {
        console.warn(err);
        alert("上传失败，请确认后端已启动且当前为本地项目。");
        $("#fileInput").value = "";
        return;
      }
    }

    const newDocId = `upload_${Date.now()}`;
    const uploadedDoc = {
      id: newDocId,
      name: f.name,
      createdAt: new Date().toISOString().slice(0, 10),
      pages: [
        {
          pageNo: 1,
          text: `上传文件：${f.name}\n（演示版不解析真实 PDF 内容）\n你可以继续测试：\n- 左侧切换文件\n- 中间页码导航\n- 右侧聊天回复`
        },
        {
          pageNo: 2,
          text: "第二页示例文本\n用于演示：缩放、文档搜索高亮、以及聊天联动。"
        }
      ],
      docSummary: "模拟上传文档（无真实 PDF 解析）。"
    };

    state.docs.unshift(uploadedDoc);
    state.filteredDocs = state.docs.slice();

    state.threads[newDocId] = {
      meta: "ready",
      suggestions: ["总结这份文档", "列出要点", "下一步建议是什么？"],
      messages: [
        { role: "assistant", text: `已上传并加载《${uploadedDoc.name}》（演示版）。你想先总结还是问要点？` }
      ]
    };

    $("#fileInput").value = "";
    setSelectedDoc(newDocId);
  });

  // 中间文档：鼠标悬停时，高亮当前“分块”（对应模拟的 region）
  const pagesWrap = $("#pages");
  let lastHover = null;
  pagesWrap.addEventListener("mouseover", (e) => {
    const el = e.target.closest(".ocr-block");
    if (!el) return;
    if (lastHover === el) return;
    if (lastHover && lastHover.classList) lastHover.classList.remove("block-hover");
    el.classList.add("block-hover");
    lastHover = el;
  });
  pagesWrap.addEventListener("mouseleave", () => {
    if (lastHover && lastHover.classList) lastHover.classList.remove("block-hover");
    lastHover = null;
  });

  // “连续阅读”模式：滚动时自动更新当前页码（用于右侧聊天上下文/页码控件显示）。
  const centerDoc = $("#centerViewDocument");
  if (centerDoc) {
    centerDoc.addEventListener(
      "scroll",
      () => {
        if (suppressScrollSync) return;
        if (state.viewMode !== "document") return;

        const sections = Array.from(document.querySelectorAll("#pages [data-page-no]"));
        if (sections.length === 0) return;

        const viewerTop = centerDoc.getBoundingClientRect().top;
        const anchor = viewerTop + 90;

        let bestPage = state.currentPage;
        for (const s of sections) {
          const rect = s.getBoundingClientRect();
          if (rect.top <= anchor) bestPage = Number(s.dataset.pageNo || bestPage);
        }

        if (bestPage !== state.currentPage) {
          state.currentPage = bestPage;
          $("#pageNum").value = String(state.currentPage);
        }
      },
      { passive: true }
    );
  }

  document.querySelectorAll(".view-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.dataset.view;
      if (mode) setViewMode(mode);
    });
  });
}

function legacyProjectBundle(json) {
  return {
    id: "proj_legacy",
    name: "默认项目",
    summary: "单套 PDF、数据库与生成结果（兼容旧版数据文件）",
    docs: json.docs,
    threads: json.threads,
    databases: json.databases,
    artifacts: json.artifacts,
  };
}

function normalizeProject(p) {
  const isDisk = p.storage === "disk";
  const databases = Array.isArray(p.databases)
    ? p.databases
    : isDisk
      ? []
      : fallbackDatabases.slice();
  const artifacts = Array.isArray(p.artifacts)
    ? p.artifacts
    : isDisk
      ? []
      : fallbackArtifacts.slice();
  return {
    id: p.id,
    name: p.name,
    summary: p.summary || "",
    docs: p.docs?.length ? p.docs : [],
    threads: p.threads && typeof p.threads === "object" ? p.threads : {},
    databases,
    artifacts,
    storage: p.storage,
    dbThreads: p.dbThreads && typeof p.dbThreads === "object" ? p.dbThreads : undefined,
    selectedDocId: p.selectedDocId,
    selectedDbId: p.selectedDbId,
    selectedArtifactId: p.selectedArtifactId,
    viewMode: p.viewMode,
  };
}

function applyProjectBundle(proj) {
  state.docs = Array.isArray(proj.docs) ? proj.docs.slice() : [];
  try {
    state.threads = proj.threads ? JSON.parse(JSON.stringify(proj.threads)) : {};
  } catch {
    state.threads = {};
  }
  try {
    state.dbThreads = proj.dbThreads ? JSON.parse(JSON.stringify(proj.dbThreads)) : {};
  } catch {
    state.dbThreads = {};
  }
  state.filteredDocs = state.docs.slice();
  const isDisk = proj.storage === "disk";
  state.databases = proj.databases?.length
    ? proj.databases.slice()
    : isDisk
      ? []
      : fallbackDatabases.slice();
  state.filteredDatabases = state.databases.slice();
  state.artifacts = proj.artifacts?.length
    ? proj.artifacts.slice()
    : isDisk
      ? []
      : fallbackArtifacts.slice();
  state.filteredArtifacts = state.artifacts.slice();

  state.selectedDbId =
    proj.selectedDbId !== undefined && proj.selectedDbId !== null
      ? proj.selectedDbId
      : state.databases[0]?.id ?? null;
  state.selectedArtifactId =
    proj.selectedArtifactId !== undefined && proj.selectedArtifactId !== null
      ? proj.selectedArtifactId
      : state.artifacts[0]?.id ?? null;

  state.selectedDocId = null;
  state.currentPage = 1;
  state.zoom = 1;
  document.documentElement.style.setProperty("--zoom", "1");
  const zr = $("#zoomRange");
  if (zr) zr.value = "1";
  state.docSearchQuery = "";
  const ds = $("#docSearch");
  if (ds) ds.value = "";

  if (proj.selectedDocId !== undefined && proj.selectedDocId !== null) {
    state.selectedDocId = proj.selectedDocId;
  } else {
    initThreadSelection();
  }
  if (!state.docs.length) state.selectedDocId = null;

  if (proj.viewMode && ["document", "database", "results"].includes(proj.viewMode)) {
    state.viewMode = proj.viewMode;
  }

  if (proj.storage === "disk") rebuildPdfDocDerivedFields();
}

function renderLandingUser() {
  const el = $("#landingUser");
  if (!el) return;
  const u = state.user || fallbackUser;
  el.innerHTML = `<div class="landing-user-name">${escapeHtml(u.displayName || "用户")}</div>
    <div class="landing-user-email">${escapeHtml(u.email || "")}</div>
    <p class="landing-user-note">${escapeHtml(u.note || "")}</p>`;
}

function renderLandingProjects() {
  const grid = $("#projectGrid");
  if (!grid) return;
  grid.innerHTML = "";
  if (!state.projectsCatalog.length) {
    const empty = document.createElement("p");
    empty.className = "landing-empty-hint";
    empty.textContent = "暂无项目，请点击「新建项目」创建。";
    grid.appendChild(empty);
    return;
  }
  state.projectsCatalog.forEach((p) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "project-card";
    btn.dataset.projectId = p.id;
    btn.setAttribute("role", "listitem");
    const t = document.createElement("div");
    t.className = "project-card-title";
    t.textContent = p.name;
    const s = document.createElement("div");
    s.className = "project-card-summary";
    s.textContent = p.summary || "";
    btn.appendChild(t);
    btn.appendChild(s);
    grid.appendChild(btn);
  });
}

async function fetchWorkspaceFromApi(projectId) {
  try {
    const res = await fetch(
      `${API_BASE}/api/projects/${encodeURIComponent(projectId)}/workspace`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

async function saveWorkspaceToDisk() {
  const id = state.currentProjectId;
  const proj = state.projectsCatalog.find((p) => p.id === id);
  if (!id || !proj || proj.storage !== "disk") return;
  const docsForSave = state.docs.map((d) => {
    const c = { ...d };
    if (c.isPdf) {
      delete c.pdfUrl;
    }
    return c;
  });
  const body = {
    threads: state.threads,
    dbThreads: state.dbThreads,
    docs: docsForSave,
    databases: state.databases,
    artifacts: state.artifacts,
    selectedDocId: state.selectedDocId,
    selectedDbId: state.selectedDbId,
    selectedArtifactId: state.selectedArtifactId,
    viewMode: state.viewMode,
  };
  try {
    await fetch(`${API_BASE}/api/projects/${encodeURIComponent(id)}/workspace`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    console.warn("[app] save workspace failed", e);
  }
}

async function enterWorkspace(projectId) {
  const proj = state.projectsCatalog.find((p) => p.id === projectId);
  if (!proj) return;
  state.currentProjectId = projectId;
  state.appPhase = "workspace";

  let bundle = proj;
  if (proj.storage === "disk") {
    const data = await fetchWorkspaceFromApi(projectId);
    if (data) {
      const ws = data.workspace || {};
      const meta = data.meta || {};
      bundle = normalizeProject({
        id: meta.id || proj.id,
        name: meta.name || proj.name,
        summary: meta.summary ?? proj.summary,
        docs: ws.docs,
        threads: ws.threads,
        dbThreads: ws.dbThreads,
        databases: ws.databases,
        artifacts: ws.artifacts,
        selectedDocId: ws.selectedDocId,
        selectedDbId: ws.selectedDbId,
        selectedArtifactId: ws.selectedArtifactId,
        viewMode: ws.viewMode,
        storage: "disk",
      });
    }
  }

  applyProjectBundle(bundle);

  const landing = $("#landingView");
  const ws = $("#workspace");
  if (landing) landing.hidden = true;
  if (ws) ws.hidden = false;
  $("#app")?.classList.remove("app--landing");

  stopLandingMesh();

  const sub = $("#brandSubtitle");
  if (sub) sub.textContent = bundle.name;

  const vm =
    state.viewMode && ["document", "database", "results"].includes(state.viewMode)
      ? state.viewMode
      : "document";
  setViewMode(vm);

  const doc = getSelectedDoc();
  if (doc) setCurrentPage(1, { withRender: false });
  updateParseOcrButton();
}

function exitToLanding() {
  void (async () => {
    await saveWorkspaceToDisk();

    state.appPhase = "landing";
    state.currentProjectId = null;

    const landing = $("#landingView");
    const ws = $("#workspace");
    if (landing) landing.hidden = false;
    if (ws) ws.hidden = true;
    $("#app")?.classList.add("app--landing");

    const sub = $("#brandSubtitle");
    if (sub) sub.textContent = "PDF · 数据库 · 交付物（演示）";

    landingMeshResize();
    startLandingMesh();
  })();
}

/** 落地页：动态网状背景（canvas） */
let landingMeshCtx = null;
let landingMeshRaf = 0;
let landingMeshNodes = [];

function landingMeshResize() {
  const cv = $("#landingMeshCanvas");
  const landing = $("#landingView");
  if (!cv || !landing) return;
  const w = landing.clientWidth;
  const h = landing.clientHeight;
  if (w < 2 || h < 2) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  cv.width = Math.floor(w * dpr);
  cv.height = Math.floor(h * dpr);
  cv.style.width = `${w}px`;
  cv.style.height = `${h}px`;
  landingMeshCtx = cv.getContext("2d");
  if (!landingMeshCtx) return;
  landingMeshCtx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const count = Math.max(32, Math.min(72, Math.floor((w * h) / 16000)));
  landingMeshNodes = [];
  for (let i = 0; i < count; i += 1) {
    landingMeshNodes.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.65,
      vy: (Math.random() - 0.5) * 0.65,
    });
  }
}

function landingMeshTick() {
  const landing = $("#landingView");
  if (!landing || landing.hidden) {
    landingMeshRaf = 0;
    return;
  }
  const cv = $("#landingMeshCanvas");
  const ctx = landingMeshCtx;
  if (!cv || !ctx) {
    landingMeshRaf = 0;
    return;
  }
  const w = cv.clientWidth;
  const h = cv.clientHeight;
  if (w < 2 || h < 2) {
    landingMeshRaf = requestAnimationFrame(landingMeshTick);
    return;
  }

  if (!landingMeshNodes.length) {
    landingMeshResize();
  }

  ctx.clearRect(0, 0, w, h);

  const maxDist = Math.min(140, (w + h) * 0.08);
  const nodes = landingMeshNodes;

  for (let i = 0; i < nodes.length; i += 1) {
    const n = nodes[i];
    n.vx += (Math.random() - 0.5) * 0.12;
    n.vy += (Math.random() - 0.5) * 0.12;
    n.vx *= 0.988;
    n.vy *= 0.988;
    n.x += n.vx;
    n.y += n.vy;
    if (n.x < -40) n.x = w + 40;
    if (n.x > w + 40) n.x = -40;
    if (n.y < -40) n.y = h + 40;
    if (n.y > h + 40) n.y = -40;
  }

  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const a = nodes[i];
      const b = nodes[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const d = Math.hypot(dx, dy);
      if (d < maxDist && d > 0.5) {
        const t = 1 - d / maxDist;
        ctx.strokeStyle = `rgba(74, 111, 165, ${t * 0.2})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }

  ctx.fillStyle = "rgba(74, 111, 165, 0.42)";
  for (const n of nodes) {
    ctx.beginPath();
    ctx.arc(n.x, n.y, 2.4, 0, Math.PI * 2);
    ctx.fill();
  }

  landingMeshRaf = requestAnimationFrame(landingMeshTick);
}

function stopLandingMesh() {
  if (landingMeshRaf) {
    cancelAnimationFrame(landingMeshRaf);
    landingMeshRaf = 0;
  }
}

function startLandingMesh() {
  if (landingMeshRaf) return;
  landingMeshResize();
  if (!landingMeshCtx) return;
  landingMeshRaf = requestAnimationFrame(landingMeshTick);
}

function initLandingMesh() {
  if (!$("#landingMeshCanvas")) return;
  let resizeTimer = 0;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      const landing = $("#landingView");
      if (landing && !landing.hidden) {
        stopLandingMesh();
        landingMeshResize();
        startLandingMesh();
      }
    }, 100);
  });
  requestAnimationFrame(() => {
    landingMeshResize();
    startLandingMesh();
  });
}

async function tryFetchProjectsFromApi() {
  try {
    const res = await fetch(`${API_BASE}/api/projects`, { cache: "no-store" });
    if (!res.ok) return null;
    const list = await res.json();
    if (!Array.isArray(list)) return null;
    return list.map((m) =>
      normalizeProject({
        ...m,
        storage: "disk",
        summary: m.summary || "本地项目 · 数据保存在 data/projects",
      })
    );
  } catch {
    return null;
  }
}

async function submitCreateProject(closeModal) {
  const inp = $("#inputProjectName");
  const name = inp?.value?.trim() || "";
  if (!name) return;
  try {
    const res = await fetch(`${API_BASE}/api/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) {
      let detail = `创建失败（HTTP ${res.status}）`;
      try {
        const j = await res.json();
        if (j.detail !== undefined) {
          if (typeof j.detail === "string") {
            detail = j.detail;
          } else if (Array.isArray(j.detail)) {
            detail = j.detail.map((x) => x.msg || JSON.stringify(x)).join("；");
          } else {
            detail = JSON.stringify(j.detail);
          }
        }
      } catch {
        /* ignore */
      }
      alert(detail);
      return;
    }
    const meta = await res.json();
    const p = normalizeProject({
      ...meta,
      storage: "disk",
      summary: meta.summary || "本地项目 · 数据保存在 data/projects",
    });
    state.projectsCatalog.push(p);
    closeModal();
    renderLandingProjects();
  } catch (e) {
    console.warn(e);
    alert(
      "无法连接后端。请确认：\n\n" +
        "1）在仓库根目录已激活 .venv 并启动：\n" +
        "   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765\n\n" +
        "2）用浏览器打开 http://127.0.0.1:8765 （不要双击本地 index.html，否则可能无法访问 API）"
    );
  }
}

async function loadData() {
  const apiProjects = await tryFetchProjectsFromApi();
  if (apiProjects !== null) {
    return {
      user: fallbackUser,
      projects: apiProjects,
    };
  }

  try {
    const res = await fetch("./data/sampleData.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
    const json = await res.json();

    if (json.projects?.length) {
      return {
        user: json.user || fallbackUser,
        projects: json.projects.map(normalizeProject),
      };
    }

    if (json?.docs && json?.threads) {
      if (!json.databases?.length) json.databases = fallbackDatabases;
      if (!json.artifacts?.length) json.artifacts = fallbackArtifacts;
      return {
        user: fallbackUser,
        projects: [legacyProjectBundle(json)],
      };
    }
    throw new Error("invalid json format");
  } catch (err) {
    console.warn("[app] load sampleData.json failed, using fallback:", err?.message || err);
    return {
      user: fallbackUser,
      projects: fallbackProjects,
    };
  }
}

function initThreadSelection() {
  if (state.docs.length === 0) return;
  if (!state.selectedDocId) state.selectedDocId = state.docs[0].id;
}

async function main() {
  const data = await loadData();
  state.user = data.user || fallbackUser;
  state.projectsCatalog = Array.isArray(data.projects) ? data.projects : fallbackProjects;

  renderLandingUser();
  renderLandingProjects();
  setupEventHandlers();
  initLandingMesh();
}

main();

