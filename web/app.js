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
  docConversations: {},
  hoveredChunkKey: null,
  selectedChunkKeys: [],
  selectedChunkItems: [],
  chunkPages: [],
  chunkListPage: 1,
  chunkListItems: [],
  activeChunkDetail: null,
  activeChunkNeighbors: null,
  qaChunkContext: null,
  vectorSearchResults: [],
  vectorIndexStatus: null,
  chatHistoryVisible: false,
  citedChunkKeys: [],
  chunkPress: {
    timer: null,
    active: false,
    moved: false,
    anchorKey: null,
    pointerId: null,
    mode: null,
  },
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

function buildOcrBlockImageUrl(doc, filename) {
  if (!doc?.isPdf || !filename || !state.currentProjectId) return null;
  return `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/files/ocr-blocks/${encodeURIComponent(doc.id)}/${encodeURIComponent(filename)}`;
}

function getParsedPdfPages(doc) {
  if (!doc?.isPdf || !Array.isArray(doc.ocrBlocksByPage)) return [];
  return doc.ocrBlocksByPage
    .map((pg, idx) => {
      const pageNo = Number(pg?.pageNo) || idx + 1;
      const originalFilename = Array.isArray(doc.pdfPageImages) ? doc.pdfPageImages[pageNo - 1] : null;
      const parsedFilename = Array.isArray(pg?.files) ? pg.files[0] : null;
      const imageSize = pg?.imageSize || null;
      const chunks = Array.isArray(pg?.chunks) ? pg.chunks : [];
      return {
        pageNo,
        imageFilename: originalFilename || parsedFilename,
        imageKind: "original",
        chunks,
        bands: buildHorizontalBands(chunks, pageNo, imageSize),
        imageSize,
      };
    })
    .filter((pg) => !!pg.imageFilename)
    .sort((a, b) => a.pageNo - b.pageNo);
}

function buildHorizontalBands(chunks, pageNo, imageSize) {
  const pageWidth = Number(imageSize?.width) || 0;
  const ranges = (Array.isArray(chunks) ? chunks : [])
    .map((chunk, idx) => {
      const norm = chunk?.bboxNorm || {};
      const px = chunk?.bboxPx || {};
      const y1 = Number(norm.y1);
      const y2 = Number(norm.y2);
      if (![y1, y2].every(Number.isFinite) || y2 <= y1) return null;
      return {
        chunk,
        idx,
        y1,
        y2,
        y1Px: Number(px.y1),
        y2Px: Number(px.y2),
      };
    })
    .filter(Boolean)
    .sort((a, b) => (a.y1 - b.y1) || (a.y2 - b.y2));

  const groups = [];
  for (const item of ranges) {
    const last = groups[groups.length - 1];
    if (!last || item.y1 > last.y2) {
      groups.push({
        items: [item],
        y1: item.y1,
        y2: item.y2,
      });
      continue;
    }
    last.items.push(item);
    last.y1 = Math.min(last.y1, item.y1);
    last.y2 = Math.max(last.y2, item.y2);
  }

  return groups.map((group, idx) => {
    const y1PxList = group.items.map((item) => item.y1Px).filter(Number.isFinite);
    const y2PxList = group.items.map((item) => item.y2Px).filter(Number.isFinite);
    const labels = [...new Set(group.items.map((item) => String(item.chunk?.label || "text")))];
    return {
      chunkKey: `p${String(pageNo).padStart(4, "0")}_band_${String(idx).padStart(3, "0")}`,
      pageNo,
      index: idx,
      label: "band",
      bboxNorm: {
        x1: 0,
        y1: group.y1,
        x2: 1,
        y2: group.y2,
      },
      bboxPx: {
        x1: 0,
        y1: y1PxList.length ? Math.min(...y1PxList) : null,
        x2: pageWidth || null,
        y2: y2PxList.length ? Math.max(...y2PxList) : null,
      },
      content: group.items
        .map((item) => String(item.chunk?.content || "").trim())
        .filter(Boolean)
        .join("\n\n"),
      sourceLabels: labels,
      sourceChunkCount: group.items.length,
      sourceChunks: group.items.map((item) => ({
        chunkId: item.chunk?.chunkId || `p${pageNo}_c${item.idx}`,
        label: item.chunk?.label || "text",
        content: item.chunk?.content || "",
        bboxPx: item.chunk?.bboxPx || {},
      })),
    };
  });
}

function clearChunkSelection({ persist = true } = {}) {
  state.hoveredChunkKey = null;
  state.selectedChunkKeys = [];
  state.selectedChunkItems = [];
  state.citedChunkKeys = [];
  syncChunkSelectionClasses();
  if (persist) void syncNowConversationSelection();
}

function clearCitedHighlights() {
  if (!Array.isArray(state.citedChunkKeys) || state.citedChunkKeys.length === 0) return;
  state.citedChunkKeys = [];
  syncChunkSelectionClasses();
}

function createMessageId() {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function createChatMessage(role, text, extra = {}) {
  return {
    id: extra.id || createMessageId(),
    role,
    text,
    timestamp: extra.timestamp || new Date().toISOString(),
    ...extra,
  };
}

function isDiskWorkspaceProject() {
  const proj = state.projectsCatalog.find((p) => p.id === state.currentProjectId);
  return !!(state.appPhase === "workspace" && proj?.storage === "disk");
}

function getDocConversationBundle(docId) {
  return docId ? state.docConversations[docId] || null : null;
}

function getActiveConversationSession(docId) {
  const bundle = getDocConversationBundle(docId);
  if (!bundle) return null;
  const sessions = Array.isArray(bundle.sessions) ? bundle.sessions : [];
  const activeId = bundle.activeSessionId || sessions[0]?.id || null;
  return sessions.find((item) => item?.id === activeId) || sessions[0] || null;
}

function conversationSessionToThread(session, docName) {
  if (!session) {
    return {
      meta: "new",
      messages: [{ role: "assistant", text: `已加载《${docName || "未命名"}》。请选择块后提问。` }],
      suggestions: ["总结这份文档", "列出关键要点", "下一步建议是什么？"],
    };
  }
  const messages = Array.isArray(session.messages) ? session.messages : [];
  return {
    meta: messages.length ? "ready" : "new",
    messages: messages.length
      ? messages
      : [{ role: "assistant", text: `已创建《${docName || "未命名"}》的新对话。请选择块后提问。` }],
    suggestions: Array.isArray(session.suggestions) ? session.suggestions : [],
    sessionId: session.id || null,
  };
}

function formatChatTime(timestamp) {
  if (!timestamp) return "";
  const d = new Date(timestamp);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function buildHistoryLabel(text, fallbackIndex) {
  const raw = String(text || "").replace(/\s+/g, " ").trim();
  if (!raw) return `事件 ${fallbackIndex}`;
  return raw.length > 22 ? `${raw.slice(0, 22)}...` : raw;
}

function buildCitedChunkGroups(chunkIds) {
  const ids = Array.isArray(chunkIds) ? chunkIds.filter(Boolean) : [];
  if (!ids.length) return [];

  const parsed = ids.map((id) => {
    const rag = String(id).match(/^rag_(\d+)_(\d+)_(\d+)$/);
    if (rag) {
      return {
        raw: String(id),
        chunkKey: String(id),
        sortable: false,
        citationType: "rag",
        ragIndex: Number(rag[3]),
      };
    }
    const m = String(id).match(/^p(\d+)_band_(\d+)$/);
    if (!m) {
      return {
        raw: String(id),
        sortable: false,
        chunkKey: String(id),
        citationType: "raw",
      };
    }
    return {
      raw: String(id),
      chunkKey: String(id),
      sortable: true,
       citationType: "band",
      page: m[1],
      band: Number(m[2]),
      bandText: m[2],
    };
  });

  const output = [];
  let i = 0;
  while (i < parsed.length) {
    const current = parsed[i];
    if (!current.sortable) {
      output.push({
        chunkKeys: [current.chunkKey],
        page: null,
        bandStartText: "",
        bandEndText: "",
      });
      i += 1;
      continue;
    }

    let j = i;
    while (
      j + 1 < parsed.length &&
      parsed[j + 1].sortable &&
      parsed[j + 1].page === current.page &&
      parsed[j + 1].band === parsed[j].band + 1
    ) {
      j += 1;
    }

    if (j === i) {
      output.push({
        chunkKeys: [current.chunkKey],
        page: Number(current.page),
        bandStartText: current.bandText,
        bandEndText: current.bandText,
      });
    } else {
      const last = parsed[j];
      output.push({
        chunkKeys: parsed.slice(i, j + 1).map((item) => item.chunkKey),
        page: Number(current.page),
        bandStartText: current.bandText,
        bandEndText: String(last.band).padStart(current.bandText.length, "0"),
      });
    }
    i = j + 1;
  }

  return output.map((group, idx) => {
    const firstKey = String(group.chunkKeys?.[0] || "");
    if (/^rag_\d+_\d+_\d+$/.test(firstKey)) {
      const ragMatch = firstKey.match(/^rag_(\d+)_(\d+)_(\d+)$/);
      const ragNo = ragMatch ? Number(ragMatch[3]) + 1 : idx + 1;
      return {
        ...group,
        label: `RAG #${ragNo}`,
      };
    }
    const bandPart = group.bandStartText && group.bandEndText && group.bandStartText !== group.bandEndText
      ? `${group.bandStartText}-${group.bandEndText}`
      : (group.bandStartText || "raw");
    const label = group.page == null
      ? `块${idx + 1}`
      : `P${group.page}.${bandPart} 块${idx + 1}`;
    return {
      ...group,
      label,
    };
  });
}

function buildSourceChunkToBandMap(doc) {
  const pages = getParsedPdfPages(doc);
  const map = new Map();
  pages.forEach((page) => {
    const bands = Array.isArray(page?.bands) ? page.bands : [];
    bands.forEach((band) => {
      const bandKey = String(band?.chunkKey || "");
      const sourceChunks = Array.isArray(band?.sourceChunks) ? band.sourceChunks : [];
      sourceChunks.forEach((source) => {
        const sourceId = String(source?.chunkId || "").trim();
        if (!sourceId || !bandKey || map.has(sourceId)) return;
        map.set(sourceId, bandKey);
      });
    });
  });
  return map;
}

function flattenChunkContextItems(chunkContext) {
  if (!chunkContext || typeof chunkContext !== "object") return [];
  const groups = [
    Array.isArray(chunkContext.currentChunks) ? chunkContext.currentChunks : [],
    Array.isArray(chunkContext.neighborChunks) ? chunkContext.neighborChunks : [],
    Array.isArray(chunkContext.retrievalChunks) ? chunkContext.retrievalChunks : [],
  ];
  const out = [];
  const seen = new Set();
  groups.flat().forEach((item) => {
    if (!item || typeof item !== "object") return;
    const id = String(item.chunkId || item.chunkKey || "");
    if (!id || seen.has(id)) return;
    seen.add(id);
    out.push(item);
  });
  return out;
}

function resolveCitationChunkKeys(chunkKeys, chunkContext, doc) {
  const inputKeys = Array.isArray(chunkKeys) ? chunkKeys.filter(Boolean).map((v) => String(v)) : [];
  if (!inputKeys.length) return [];
  const bandMap = buildSourceChunkToBandMap(doc);
  const contextItems = flattenChunkContextItems(chunkContext);
  const contextById = new Map(contextItems.map((item) => [String(item.chunkId || item.chunkKey || ""), item]));
  const resolved = [];
  const seen = new Set();

  const pushUnique = (key) => {
    const v = String(key || "");
    if (!v || seen.has(v)) return;
    seen.add(v);
    resolved.push(v);
  };

  inputKeys.forEach((id) => {
    if (/^p\d+_band_\d+$/.test(id)) {
      pushUnique(id);
      return;
    }
    if (/^p\d+_c\d+$/.test(id)) {
      const mapped = bandMap.get(id);
      if (mapped) pushUnique(mapped);
      return;
    }
    if (/^rag_\d+_\d+_\d+$/.test(id)) {
      const ragItem = contextById.get(id);
      const sourceIds = Array.isArray(ragItem?.sourceChunkIds) ? ragItem.sourceChunkIds : [];
      sourceIds.forEach((sourceId) => {
        const mapped = bandMap.get(String(sourceId));
        if (mapped) pushUnique(mapped);
      });
      return;
    }
  });
  return resolved;
}

function locateCitedChunks(chunkKeys, chunkContext = null) {
  const doc = getSelectedDoc();
  if (!doc?.isPdf || !doc.ocrParsed) return;
  const resolvedChunkKeys = resolveCitationChunkKeys(chunkKeys, chunkContext, doc);
  if (!resolvedChunkKeys.length) return;
  const prevSorted = [...new Set((state.citedChunkKeys || []).map((v) => String(v)))].sort();
  const nextSorted = [...new Set(resolvedChunkKeys.map((v) => String(v)))].sort();
  if (prevSorted.length === nextSorted.length && prevSorted.every((v, i) => v === nextSorted[i])) {
    clearChunkSelection({ persist: false });
    renderChunkInspector();
    return;
  }
  const groups = buildCitedChunkGroups(resolvedChunkKeys);
  const firstKey = groups[0]?.chunkKeys?.[0] || resolvedChunkKeys?.[0];
  const m = String(firstKey || "").match(/^p(\d+)_band_/);
  const targetPage = m ? Number(m[1]) : state.currentPage;
  if (doc.pdfViewMode !== "parsed") {
    doc.pdfViewMode = "parsed";
    renderDocHeader();
  }
  setCurrentPage(targetPage);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const items = [];
      for (const key of resolvedChunkKeys) {
        const el = document.querySelector(`.chunk-box[data-chunk-key="${key}"]`);
        const payload = getChunkPayloadFromElement(el);
        if (payload?.chunkKey) items.push(payload);
      }
      if (!items.length) return;

      items.sort((a, b) => {
        const pageDiff = Number(a.pageNo || 0) - Number(b.pageNo || 0);
        if (pageDiff !== 0) return pageDiff;
        return Number(a.index || 0) - Number(b.index || 0);
      });
      state.citedChunkKeys = items.map((item) => item.chunkKey);
      state.selectedChunkItems = items;
      state.selectedChunkKeys = items.map((item) => item.chunkKey);
      renderChunkInspector();
      syncChunkSelectionClasses();
      void syncNowConversationSelection();

      const firstEl = document.querySelector(`.chunk-box[data-chunk-key="${items[0].chunkKey}"]`);
      if (firstEl) firstEl.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });
}

function getChunkIndexKey(item) {
  return `${Number(item?.pageNo || 0)}:${Number(item?.index || -1)}`;
}

function getChunkPayloadFromElement(el) {
  if (!el) return null;
  try {
    return JSON.parse(el.dataset.chunkPayload || "{}");
  } catch {
    return null;
  }
}

function setSelectedChunkRange(anchorChunk, currentChunk) {
  if (!anchorChunk || !currentChunk) return;
  clearCitedHighlights();
  const anchorPage = Number(anchorChunk.pageNo || 0);
  const currentPage = Number(currentChunk.pageNo || 0);
  const anchorIndex = Number(anchorChunk.index);
  const currentIndex = Number(currentChunk.index);
  if (!Number.isFinite(anchorPage) || !Number.isFinite(currentPage) || anchorPage !== currentPage) return;
  if (!Number.isFinite(anchorIndex) || !Number.isFinite(currentIndex)) return;

  const start = Math.min(anchorIndex, currentIndex);
  const end = Math.max(anchorIndex, currentIndex);
  const inRange = [];

  document.querySelectorAll(`.chunk-box[data-page-no="${anchorPage}"]`).forEach((el) => {
    const payload = getChunkPayloadFromElement(el);
    const idx = Number(payload?.index);
    if (Number.isFinite(idx) && idx >= start && idx <= end) inRange.push(payload);
  });

  if (inRange.length !== end - start + 1) return;

  inRange.sort((a, b) => Number(a.index || 0) - Number(b.index || 0));

  if (state.chunkPress.mode === "remove") {
    const removeKeys = new Set(inRange.map((item) => item.chunkKey));
    state.selectedChunkItems = state.selectedChunkItems.filter((item) => !removeKeys.has(item.chunkKey));
    state.selectedChunkKeys = state.selectedChunkItems.map((item) => item.chunkKey);
  } else {
    const merged = [...state.selectedChunkItems];
    const existingKeys = new Set(merged.map((item) => item.chunkKey));
    for (const item of inRange) {
      if (!existingKeys.has(item.chunkKey)) {
        merged.push(item);
        existingKeys.add(item.chunkKey);
      }
    }
    merged.sort((a, b) => {
      const pageDiff = Number(a.pageNo || 0) - Number(b.pageNo || 0);
      if (pageDiff !== 0) return pageDiff;
      return Number(a.index || 0) - Number(b.index || 0);
    });
    state.selectedChunkItems = merged;
    state.selectedChunkKeys = merged.map((item) => item.chunkKey);
  }
  state.currentPage = anchorPage;
  $("#pageNum").value = String(state.currentPage);
  void syncNowConversationSelection();
  renderChunkInspector();
  syncChunkSelectionClasses();
}

function clearChunkPressTimer() {
  if (state.chunkPress.timer) {
    clearTimeout(state.chunkPress.timer);
    state.chunkPress.timer = null;
  }
}

function resetChunkPress() {
  clearChunkPressTimer();
  state.chunkPress.active = false;
  state.chunkPress.moved = false;
  state.chunkPress.anchorKey = null;
  state.chunkPress.pointerId = null;
  state.chunkPress.mode = null;
}

function setSelectedChunk(chunk) {
  if (!chunk) {
    clearChunkSelection();
  } else {
    clearCitedHighlights();
    state.activeChunkDetail = null;
    state.activeChunkNeighbors = null;
    state.qaChunkContext = null;
    const idx = state.selectedChunkKeys.indexOf(chunk.chunkKey);
    if (idx >= 0) {
      state.selectedChunkKeys.splice(idx, 1);
      state.selectedChunkItems = state.selectedChunkItems.filter((item) => item.chunkKey !== chunk.chunkKey);
    } else {
      state.selectedChunkKeys = [...state.selectedChunkKeys, chunk.chunkKey];
      state.selectedChunkItems = [...state.selectedChunkItems, chunk];
    }
    if (Number.isFinite(Number(chunk.pageNo))) {
      state.currentPage = Number(chunk.pageNo);
      $("#pageNum").value = String(state.currentPage);
    }
    void syncNowConversationSelection();
  }
  renderChunkInspector();
  syncChunkSelectionClasses();
}

function renderChunkInspector() {
  const wrap = $("#chunkInspector");
  const meta = $("#chunkInspectorMeta");
  const pos = $("#chunkInspectorPosition");
  const content = $("#chunkInspectorContent");
  const neighborWrap = $("#chunkNeighborWrap");
  const neighborList = $("#chunkNeighborList");
  if (!wrap || !meta || !pos || !content) return;

  const doc = getSelectedDoc();
  const activeChunk = state.activeChunkDetail && state.activeChunkDetail.docId === doc?.id
    ? state.activeChunkDetail
    : null;
  const shouldShow = !!(doc?.isPdf && isPdfParsedView(doc) && (state.selectedChunkItems.length || activeChunk));
  wrap.hidden = !shouldShow;
  if (!shouldShow) {
    meta.textContent = "Click a chunk box";
    pos.textContent = "";
    content.textContent = "";
    if (neighborWrap) neighborWrap.hidden = true;
    renderChunkExplorer();
    return;
  }

  if (activeChunk) {
    const neighbors = state.activeChunkNeighbors || { previous: [], next: [] };
    meta.textContent = `chunk ${activeChunk.chunkId} | page ${activeChunk.pageNo}`;
    const box = activeChunk.bboxPx || {};
    pos.textContent = `x1=${box.x1 ?? "-"}, y1=${box.y1 ?? "-"}, x2=${box.x2 ?? "-"}, y2=${box.y2 ?? "-"}`;
    content.textContent = activeChunk.normalizedContent || activeChunk.content || "(empty chunk)";
    if (neighborWrap && neighborList) {
      const around = [...(neighbors.previous || []), ...(neighbors.next || [])];
      neighborWrap.hidden = around.length === 0;
      neighborList.innerHTML = "";
      around.forEach((item) => {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "chunk-list-item";
        card.innerHTML = `
          <div class="chunk-list-head"><span>Page ${item.pageNo} · #${item.index}</span><span>${item.label || "text"}</span></div>
          <div class="chunk-list-snippet">${escapeHtml((item.normalizedContent || item.content || "").slice(0, 180) || "(empty chunk)")}</div>
        `;
        card.addEventListener("click", () => {
          void focusChunkById(item.chunkId, { source: "neighbor_click" });
        });
        neighborList.appendChild(card);
      });
    }
    renderChunkExplorer();
    return;
  }

  const items = state.selectedChunkItems.slice().sort((a, b) => {
    const pageDiff = Number(a.pageNo || 0) - Number(b.pageNo || 0);
    if (pageDiff !== 0) return pageDiff;
    return Number(a.index || 0) - Number(b.index || 0);
  });
  const first = items[0];
  const last = items[items.length - 1];
  meta.textContent = `${items.length} selected | page ${first.pageNo}${last.pageNo !== first.pageNo ? `-${last.pageNo}` : ""}`;
  const y1List = items.map((item) => Number(item?.bboxPx?.y1)).filter(Number.isFinite);
  const y2List = items.map((item) => Number(item?.bboxPx?.y2)).filter(Number.isFinite);
  pos.textContent = `y1=${y1List.length ? Math.min(...y1List) : "-"}, y2=${y2List.length ? Math.max(...y2List) : "-"}`;
  content.textContent = items
    .map((item) => {
      const labels = Array.isArray(item.sourceLabels) && item.sourceLabels.length ? `labels: ${item.sourceLabels.join(", ")}` : "";
      const head = `Page ${item.pageNo} | #${item.index} | ${item.sourceChunkCount || 1} chunks`;
      return [head, labels, item.content || "(empty chunk)"].filter(Boolean).join("\n");
    })
    .join("\n\n---\n\n");
  if (neighborWrap) neighborWrap.hidden = true;
  renderChunkExplorer();
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderChunkCards(container, items, { activeChunkId = null, showScore = false } = {}) {
  if (!container) return;
  container.innerHTML = "";
  if (!Array.isArray(items) || !items.length) {
    const empty = document.createElement("div");
    empty.className = "chunk-list-meta";
    empty.textContent = "暂无结果";
    container.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `chunk-list-item${item?.chunkId === activeChunkId ? " is-active" : ""}`;
    const score = showScore && Number.isFinite(Number(item?.score)) ? `score ${Number(item.score).toFixed(3)}` : item?.label || "text";
    btn.innerHTML = `
      <div class="chunk-list-head"><span>Page ${item?.pageNo || "-"} · #${item?.index || 0}</span><span>${escapeHtml(score)}</span></div>
      <div class="chunk-list-snippet">${escapeHtml(((item?.normalizedContent || item?.content || "").slice(0, 220) || "(empty chunk)"))}</div>
    `;
    btn.addEventListener("click", () => {
      void focusChunkById(item.chunkId, {
        source: showScore ? "vector_search" : "chunk_browser",
        retrievalChunks: showScore ? state.vectorSearchResults : [],
      });
    });
    container.appendChild(btn);
  });
}

function renderChunkExplorer() {
  const doc = getSelectedDoc();
  const pageFilter = $("#chunkPageFilter");
  const chunkMeta = $("#chunkListMeta");
  const chunkList = $("#chunkList");
  const vectorMeta = $("#vectorIndexMeta");
  const vectorList = $("#vectorSearchResults");
  if (!pageFilter || !chunkMeta || !chunkList || !vectorMeta || !vectorList) return;

  const parsed = !!(doc?.isPdf && doc?.ocrParsed);
  pageFilter.innerHTML = "";
  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = "All";
  pageFilter.appendChild(allOption);
  (state.chunkPages || []).forEach((page) => {
    const opt = document.createElement("option");
    opt.value = String(page.pageNo);
    opt.textContent = `Page ${page.pageNo} (${page.chunkCount})`;
    pageFilter.appendChild(opt);
  });
  pageFilter.value = state.chunkListPage ? String(state.chunkListPage) : "all";

  if (!parsed) {
    chunkMeta.textContent = "请先解析 PDF，才能浏览标准化块和向量检索结果。";
    chunkList.innerHTML = "";
    vectorMeta.textContent = "索引状态：未就绪";
    vectorList.innerHTML = "";
    return;
  }

  const total = (state.chunkPages || []).reduce((sum, page) => sum + Number(page?.chunkCount || 0), 0);
  chunkMeta.textContent = `共 ${total} 个块，当前显示 ${state.chunkListPage ? `第 ${state.chunkListPage} 页` : "全部页"}。`;
  const q = String(state.docSearchQuery || "").trim().toLowerCase();
  const filteredChunkItems = q
    ? (state.chunkListItems || []).filter((item) =>
        String(item?.normalizedContent || item?.content || "").toLowerCase().includes(q)
      )
    : state.chunkListItems || [];
  renderChunkCards(chunkList, filteredChunkItems, {
    activeChunkId: state.activeChunkDetail?.chunkId || null,
  });

  const vectorStatus = state.vectorIndexStatus || {};
  const statusText = vectorStatus?.status || "unknown";
  const chunkCount = Number(vectorStatus?.chunkCount || 0);
  vectorMeta.textContent = `索引状态：${statusText} · chunks ${chunkCount}`;
  const filteredVectorResults = q
    ? (state.vectorSearchResults || []).filter((item) =>
        String(item?.normalizedContent || item?.content || "").toLowerCase().includes(q)
      )
    : state.vectorSearchResults || [];
  renderChunkCards(vectorList, filteredVectorResults, {
    activeChunkId: state.activeChunkDetail?.chunkId || null,
    showScore: true,
  });
}

function getAskChunkContext(doc) {
  if (state.qaChunkContext?.docId && state.qaChunkContext.docId === doc?.id) {
    return {
      source: state.qaChunkContext.source || "chunk_browser",
      currentChunks: Array.isArray(state.qaChunkContext.currentChunks) ? state.qaChunkContext.currentChunks : [],
      neighborChunks: Array.isArray(state.qaChunkContext.neighborChunks) ? state.qaChunkContext.neighborChunks : [],
      retrievalChunks: Array.isArray(state.qaChunkContext.retrievalChunks) ? state.qaChunkContext.retrievalChunks : [],
    };
  }
  if (Array.isArray(state.selectedChunkItems) && state.selectedChunkItems.length) {
    return {
      source: "selection",
      currentChunks: state.selectedChunkItems.map((item) => ({ ...item })),
      neighborChunks: [],
      retrievalChunks: [],
    };
  }
  return null;
}

async function focusChunkById(chunkId, { source = "chunk_browser", retrievalChunks = [] } = {}) {
  const doc = getSelectedDoc();
  if (!doc?.id || !chunkId || !isDiskWorkspaceProject()) return;
  const data = await fetchChunkDetailApi(doc.id, chunkId, 1);
  state.activeChunkDetail = { ...(data.chunk || {}), docId: doc.id };
  state.activeChunkNeighbors = data.neighbors || { previous: [], next: [] };
  state.qaChunkContext = {
    docId: doc.id,
    source,
    currentChunks: data.neighbors?.current ? [data.neighbors.current] : data.chunk ? [data.chunk] : [],
    neighborChunks: [...(data.neighbors?.previous || []), ...(data.neighbors?.next || [])],
    retrievalChunks: Array.isArray(retrievalChunks) ? retrievalChunks : [],
  };
  clearChunkSelection({ persist: false });
  if (Number.isFinite(Number(state.activeChunkDetail?.pageNo))) {
    state.currentPage = Number(state.activeChunkDetail.pageNo);
    $("#pageNum").value = String(state.currentPage);
    renderDocumentContinuous();
  } else {
    renderChunkInspector();
  }
}

async function refreshChunkExplorerForDoc(docId, { keepPage = true } = {}) {
  if (!docId || !isDiskWorkspaceProject()) return;
  const pageData = await fetchDocChunksByPageApi(docId);
  state.chunkPages = Array.isArray(pageData?.pages)
    ? pageData.pages.map((page) => ({ pageNo: Number(page.pageNo), chunkCount: Number(page.chunkCount || 0) }))
    : [];
  if (!keepPage || !state.chunkPages.some((page) => page.pageNo === state.chunkListPage)) {
    state.chunkListPage = state.chunkPages[0]?.pageNo || 0;
  }
  const listData = await fetchDocChunksApi(docId, state.chunkListPage || null);
  state.chunkListItems = Array.isArray(listData?.chunks) ? listData.chunks : [];
  try {
    state.vectorIndexStatus = await fetchVectorIndexStatusApi();
  } catch (e) {
    state.vectorIndexStatus = { status: "error", chunkCount: 0, detail: e?.message || "加载失败" };
  }
  renderChunkExplorer();
}

function syncChunkSelectionClasses() {
  const selectedIndexSet = new Set(
    state.selectedChunkItems.map((item) => `${Number(item.pageNo || 0)}:${Number(item.index || 0)}`)
  );
  const itemMap = new Map(
    state.selectedChunkItems.map((item) => [item.chunkKey, item])
  );
  const citeSet = new Set(Array.isArray(state.citedChunkKeys) ? state.citedChunkKeys : []);

  document.querySelectorAll(".chunk-box").forEach((el) => {
    const key = el.dataset.chunkKey;
    const isSelected = state.selectedChunkKeys.includes(key);
    const isCited = citeSet.has(key);
    const item = itemMap.get(key);
    let payloadIndex = -1;
    if (!item) {
      try {
        payloadIndex = Number(JSON.parse(el.dataset.chunkPayload || "{}").index ?? -1);
      } catch {
        payloadIndex = -1;
      }
    }
    const pageNo = Number(item?.pageNo ?? el.dataset.pageNo ?? 0);
    const index = Number(item?.index ?? payloadIndex);
    const hasPrev = isSelected && selectedIndexSet.has(`${pageNo}:${index - 1}`);
    const hasNext = isSelected && selectedIndexSet.has(`${pageNo}:${index + 1}`);

    el.classList.toggle("is-hover", key === state.hoveredChunkKey);
    el.classList.toggle("is-selected", isSelected || isCited);
    el.classList.toggle("is-cited", isCited && !isSelected);
    el.classList.toggle("is-joined-prev", hasPrev);
    el.classList.toggle("is-joined-next", hasNext);
  });
}

async function syncNowConversationSelection() {
  if (!state.currentProjectId || state.appPhase !== "workspace") return;
  const doc = getSelectedDoc();
  const selectedItems = doc
    ? state.selectedChunkItems.map((item) => ({
        ...item,
        docId: doc.id,
        docName: doc.name,
      }))
    : [];
  try {
    await fetch(`${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/now-conversation`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selectedItems }),
    });
  } catch (e) {
    console.warn("[app] sync now_conversation failed", e);
  }
}

async function fetchNowConversationFromApi(projectId) {
  try {
    const res = await fetch(
      `${API_BASE}/api/projects/${encodeURIComponent(projectId)}/now-conversation`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function getPdfNavTotal(doc) {
  if (!doc?.isPdf) return 1;
  if (doc.ocrParsed && doc.pdfViewMode === "parsed" && doc.ocrBlocksByPage?.length) {
    const n = getParsedPdfPages(doc).length;
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
    getParsedPdfPages(doc).length > 0
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
  const hasChunkPayload =
    Array.isArray(doc.ocrBlocksByPage) &&
    doc.ocrBlocksByPage.length > 0 &&
    doc.ocrBlocksByPage.every((pg) => Array.isArray(pg?.chunks));
  if (!doc.ocrParsed) {
    btn.textContent = "解析";
    btn.title = "GLM-OCR 解析（首次），每页生成版面可视化（框+标签）";
    return;
  }
  if (!hasChunkPayload) {
    btn.textContent = "瑙ｆ瀽";
    btn.title = "补齐 chunk 框数据并切换为解析视图";
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
  renderHistory(null);
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
  msgs.forEach((m, idx) => appendMessage(m.role, m.text, {
    id: m.id || `db_msg_legacy_${idx}`,
    timestamp: m.timestamp || "",
    citedChunkIds: Array.isArray(m.citedChunkIds) ? m.citedChunkIds : [],
  }));
  renderHistory(thread);
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

  const userMsg = createChatMessage("user", text);
  appendMessage(userMsg.role, userMsg.text, userMsg);
  if (!state.dbThreads[db.id]) state.dbThreads[db.id] = { messages: [], meta: "ready" };
  state.dbThreads[db.id].messages = state.dbThreads[db.id].messages || [];
  state.dbThreads[db.id].messages.push(userMsg);

  setThreadMeta("thinking...");
  await new Promise((r) => setTimeout(r, 450));

  const reply = simulateDbReply(db, text);
  const assistantMsg = createChatMessage("assistant", reply);
  appendMessage(assistantMsg.role, assistantMsg.text, assistantMsg);
  state.dbThreads[db.id].messages.push(assistantMsg);
  state.dbThreads[db.id].meta = "ready";
  setThreadMeta("ready");
  renderHistory(state.dbThreads[db.id]);
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

  const hasChunkPayload =
    Array.isArray(doc.ocrBlocksByPage) &&
    doc.ocrBlocksByPage.length > 0 &&
    doc.ocrBlocksByPage.every((pg) => Array.isArray(pg?.chunks));

  if (doc.ocrParsed && hasChunkPayload) {
    doc.pdfViewMode = doc.pdfViewMode === "parsed" ? "original" : "parsed";
    clearChunkSelection();
    state.activeChunkDetail = null;
    state.activeChunkNeighbors = null;
    state.qaChunkContext = null;
    state.currentPage = 1;
    renderDocHeader();
    renderDocumentContinuous();
    void refreshChunkExplorerForDoc(doc.id, { keepPage: false }).catch((err) => console.warn("[app] refresh chunks", err));
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
    clearChunkSelection();
    state.activeChunkDetail = null;
    state.activeChunkNeighbors = null;
    state.qaChunkContext = null;
    state.currentPage = 1;
    renderDocHeader();
    renderDocumentContinuous();
    renderFileList();
    void refreshChunkExplorerForDoc(doc.id, { keepPage: false }).catch((err) => console.warn("[app] refresh chunks", err));
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
      if (state.selectedChunkItems.some((item) => item?.docId === docId)) {
        clearChunkSelection({ persist: false });
      }
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
    if (state.selectedChunkItems.some((item) => item?.docId === docId)) {
      clearChunkSelection();
    }
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
  clearChunkSelection();
  state.activeChunkDetail = null;
  state.activeChunkNeighbors = null;
  state.qaChunkContext = null;
  state.chunkPages = [];
  state.chunkListItems = [];
  state.chunkListPage = 1;
  state.vectorSearchResults = [];
  state.vectorIndexStatus = null;
  $("#docSearch").value = "";
  $("#pageNum").value = String(1);

  renderFileList();
  if (isDiskWorkspaceProject() && docId) {
    void loadDocConversations(docId, { render: !keepMessages });
    void refreshChunkExplorerForDoc(docId, { keepPage: false }).catch((err) => console.warn("[app] load chunks", err));
  }
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
    const parsedPages = parsedView ? getParsedPdfPages(doc) : [];
    const flatBlocks = parsedPages;

    if (parsedView && parsedPages.length === 0) {
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
    const numPages = parsedView ? parsedPages.length : pageCount;
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
      let chunks = [];
      if (parsedView) {
        const b = parsedPages[p - 1];
        fn = b.imageFilename;
        src = buildPdfPageImageUrl(doc, fn) || buildOcrBlockImageUrl(doc, fn);
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
      if (parsedView) {
        const parsedPage = parsedPages[p - 1];
        const bands = Array.isArray(parsedPage?.bands) ? parsedPage.bands : [];
        if (bands.length) {
          const overlay = document.createElement("div");
          overlay.className = "chunk-overlay";
          overlay.dataset.pageNo = String(parsedPage.pageNo || p);

          for (const chunk of bands) {
            const norm = chunk.bboxNorm || {};
            const y1 = Number(norm.y1);
            const y2 = Number(norm.y2);
            if (![y1, y2].every(Number.isFinite)) continue;

            const chunkKey = chunk.chunkKey || `p${chunk.pageNo ?? p}_band_${chunk.index ?? 0}`;
            const box = document.createElement("button");
            box.type = "button";
            box.className = "chunk-box";
            box.dataset.chunkKey = chunkKey;
            box.dataset.pageNo = String(chunk.pageNo ?? parsedPage.pageNo ?? p);
            box.dataset.chunkPayload = JSON.stringify({
              chunkKey,
              pageNo: chunk.pageNo ?? parsedPage.pageNo ?? p,
              index: chunk.index ?? 0,
              label: chunk.label || "band",
              content: chunk.content || "",
              bboxPx: chunk.bboxPx || {},
              sourceLabels: chunk.sourceLabels || [],
              sourceChunkCount: chunk.sourceChunkCount || 0,
            });
            box.style.left = "0";
            box.style.top = `${y1 * 100}%`;
            box.style.width = "100%";
            box.style.minWidth = "100%";
            box.style.maxWidth = "100%";
            box.style.height = `${(y2 - y1) * 100}%`;
            box.style.borderRadius = "0";
            box.style.boxSizing = "border-box";
            box.style.zIndex = "6";
            box.title = `Page ${chunk.pageNo ?? parsedPage.pageNo ?? p} · ${chunk.label || "chunk"} #${chunk.index ?? 0}`;
            overlay.appendChild(box);
          }

          wrap.appendChild(overlay);
        }
      }
      section.appendChild(wrap);
      pagesWrap.appendChild(section);
    }

    reorderPdfSections(pagesWrap, start, end);
    syncChunkSelectionClasses();
    renderChunkInspector();
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
  clearChunkSelection();
  renderChunkInspector();

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
  let thread = state.threads[docId] || {
    meta: "new",
    messages: [{
      role: "assistant",
      text: `????${getSelectedDoc()?.name || "???"}????????????????????????????`
    }],
    suggestions: ["??????", "??????", "?????????"]
  };

  const doc = getSelectedDoc();
  if (isDiskWorkspaceProject() && docId && doc && state.viewMode !== "database") {
    thread = conversationSessionToThread(getActiveConversationSession(docId), doc.name);
  }
  setThreadMeta(thread.meta || "ready");
  $("#chatMessages").innerHTML = "";

  const msgs = thread.messages || [];
  msgs.forEach((m, idx) => appendMessage(m.role, m.text, {
    id: m.id || `msg_legacy_${idx}`,
    timestamp: m.timestamp || "",
    citedChunkIds: Array.isArray(m.citedChunkIds) ? m.citedChunkIds : [],
    chunkContext: m.chunkContext || null,
  }));

  renderSuggestions(thread.suggestions || []);
  renderHistory(thread);
}

function appendMessage(role, text, options = {}) {
  const wrap = $("#chatMessages");
  const row = document.createElement("div");
  row.className = `msg ${role}`;
  if (options.id) row.dataset.messageId = options.id;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const head = document.createElement("div");
  head.className = "bubble-head";

  const r = document.createElement("div");
  r.className = "role";
  r.textContent = role === "user" ? "You" : "Assistant";

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = formatChatTime(options.timestamp);

  const t = document.createElement("div");
  t.className = "text";
  t.textContent = text;

  head.appendChild(r);
  head.appendChild(time);
  bubble.appendChild(head);
  bubble.appendChild(t);

  const context = options.chunkContext;
  if (context && (Array.isArray(context.currentChunks) || Array.isArray(context.neighborChunks))) {
    const currentCount = Array.isArray(context.currentChunks) ? context.currentChunks.length : 0;
    const neighborCount = Array.isArray(context.neighborChunks) ? context.neighborChunks.length : 0;
    const retrievalCount = Array.isArray(context.retrievalChunks) ? context.retrievalChunks.length : 0;
    const badge = document.createElement("div");
    badge.className = "chunk-list-meta";
    badge.textContent = `上下文: current ${currentCount} · neighbor ${neighborCount}${retrievalCount ? ` · retrieval ${retrievalCount}` : ""}`;
    bubble.appendChild(badge);
  }

  const groups = buildCitedChunkGroups(options.citedChunkIds);
  if (role === "assistant" && groups.length) {
    const refs = document.createElement("div");
    refs.className = "cited-blocks";

    const title = document.createElement("div");
    title.className = "cited-blocks-title";
    title.textContent = "引用块";
    refs.appendChild(title);

    const list = document.createElement("div");
    list.className = `cited-blocks-list${groups.length > 1 ? " is-vertical" : ""}`;
    groups.forEach((group) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "cited-block-btn";
      btn.textContent = group.label;
      btn.addEventListener("click", () => locateCitedChunks(group.chunkKeys, context));
      list.appendChild(btn);
    });
    refs.appendChild(list);
    bubble.appendChild(refs);
  }

  row.appendChild(bubble);
  wrap.appendChild(row);
  wrap.scrollTop = wrap.scrollHeight;
}

function renderHistory(thread) {
  const panel = $("#chatHistoryPanel");
  const list = $("#chatHistoryList");
  const toggleBtn = $("#btnToggleHistory");
  if (!panel || !list || !toggleBtn) return;

  list.innerHTML = "";
  const docId = state.selectedDocId;
  if (isDiskWorkspaceProject() && docId && state.viewMode !== "database") {
    const bundle = getDocConversationBundle(docId);
    const sessions = Array.isArray(bundle?.sessions) ? bundle.sessions : [];
    const activeId = bundle?.activeSessionId || sessions[0]?.id || null;
    panel.hidden = !state.chatHistoryVisible || sessions.length === 0;
    toggleBtn.classList.toggle("is-active", state.chatHistoryVisible);
    toggleBtn.disabled = sessions.length === 0;
    sessions.forEach((session, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `history-chip${session?.id === activeId ? " is-active" : ""}`;
      const label = session?.title || `对话 ${idx + 1}`;
      btn.textContent = label;
      const time = formatChatTime(session?.updatedAt || session?.startedAt || "");
      if (time) btn.title = `${label} ${time}`;
      btn.addEventListener("click", async () => {
        if (!session?.id) return;
        try {
          const data = await activateDocConversationApi(docId, session.id);
          upsertConversationSession(docId, data.session, data.activeSessionId || session.id);
          renderChat();
        } catch (e) {
          console.warn("[app] activate conversation failed", e);
        }
      });
      list.appendChild(btn);
    });
    const suggestions = $("#suggestions");
    if (suggestions) suggestions.hidden = state.chatHistoryVisible;
    return;
  }
  const messages = Array.isArray(thread?.messages) ? thread.messages : [];
  const historyItems = messages
    .filter((m) => m?.role === "user" && String(m.text || "").trim())
    .map((m, idx) => ({
      label: buildHistoryLabel(m.text, idx + 1),
      messageId: m.id || `msg_legacy_${idx}`,
      timestamp: m.timestamp || "",
    }));

  panel.hidden = !state.chatHistoryVisible || historyItems.length === 0;
  toggleBtn.classList.toggle("is-active", state.chatHistoryVisible);
  toggleBtn.disabled = historyItems.length === 0;

  historyItems.forEach((item) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "history-chip";
    btn.textContent = item.label;
    const time = formatChatTime(item.timestamp);
    if (time) btn.title = `${item.label} ${time}`;
    btn.addEventListener("click", () => {
      const target = document.querySelector(`.msg[data-message-id="${item.messageId}"]`);
      if (target) target.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    list.appendChild(btn);
  });

  const suggestions = $("#suggestions");
  if (suggestions) suggestions.hidden = state.chatHistoryVisible;
}

function renderSuggestions(suggestions) {
  const el = $("#suggestions");
  if (!el) return;
  el.hidden = state.chatHistoryVisible;
  // 只移除之前生成的 chip 行，保留顶部标题。
  el.querySelectorAll(".chip-row").forEach((n) => n.remove());
  if (state.chatHistoryVisible || !suggestions || suggestions.length === 0) return;

  const row = document.createElement("div");
  row.className = "chip-row";
  suggestions.slice(0, 6).forEach((s) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = s;
    chip.addEventListener("click", async () => {
      $("#chatText").value = "";
      $("#chatText").focus();
      await handleSendMessage(s);
    });
    row.appendChild(chip);
  });
  el.appendChild(row);
}

async function askSelectionApi(docId, question) {
  const doc = getSelectedDoc();
  const chunkContext = getAskChunkContext(doc);
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/ask-selection`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, chunkContext }),
    }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `提问失败 (${res.status})`);
  }
  return data;
}

async function fetchDocChunksApi(docId, page = null) {
  const url = new URL(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/chunks`
  );
  if (page) url.searchParams.set("page", String(page));
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `加载块失败 (${res.status})`);
  }
  return data;
}

async function fetchDocChunksByPageApi(docId) {
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/chunks/by-page`
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `加载分页块失败 (${res.status})`);
  }
  return data;
}

async function fetchChunkDetailApi(docId, chunkId, radius = 1) {
  const url = new URL(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/chunks/${encodeURIComponent(chunkId)}`
  );
  url.searchParams.set("radius", String(radius));
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `加载块详情失败 (${res.status})`);
  }
  return data;
}

async function fetchVectorIndexStatusApi() {
  const res = await fetch(`${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/vector-index`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `加载索引状态失败 (${res.status})`);
  }
  return data;
}

async function rebuildVectorIndexApi() {
  const res = await fetch(`${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/vector-index/rebuild`, {
    method: "POST",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `重建索引失败 (${res.status})`);
  }
  return data;
}

async function updateDocVectorIndexApi(docId) {
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/vector-index/docs/${encodeURIComponent(docId)}`,
    { method: "PUT" }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `更新索引失败 (${res.status})`);
  }
  return data;
}

async function deleteDocVectorIndexApi(docId) {
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/vector-index/docs/${encodeURIComponent(docId)}`,
    { method: "DELETE" }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `删除索引失败 (${res.status})`);
  }
  return data;
}

async function searchVectorIndexApi(query, docId, topK = 5) {
  const res = await fetch(`${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/vector-index/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, docId, topK }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `向量检索失败 (${res.status})`);
  }
  return data;
}

async function fetchDocConversationsApi(docId) {
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/conversations`
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `加载对话失败 (${res.status})`);
  }
  return data;
}

async function createDocConversationApi(docId) {
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/conversations`,
    { method: "POST" }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `新建对话失败 (${res.status})`);
  }
  return data;
}

async function activateDocConversationApi(docId, sessionId) {
  const res = await fetch(
    `${API_BASE}/api/projects/${encodeURIComponent(state.currentProjectId)}/docs/${encodeURIComponent(docId)}/conversations/${encodeURIComponent(sessionId)}/activate`,
    { method: "PUT" }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : `切换对话失败 (${res.status})`);
  }
  return data;
}

function upsertConversationSession(docId, session, activeSessionId = null) {
  if (!docId || !session?.id) return;
  const current = getDocConversationBundle(docId) || { sessions: [], activeSessionId: null };
  const sessions = Array.isArray(current.sessions) ? current.sessions.slice() : [];
  const idx = sessions.findIndex((item) => item?.id === session.id);
  if (idx >= 0) sessions[idx] = session;
  else sessions.unshift(session);
  sessions.sort((a, b) => String(b?.updatedAt || "").localeCompare(String(a?.updatedAt || "")));
  state.docConversations[docId] = {
    sessions,
    activeSessionId: activeSessionId || session.id,
  };
}

async function loadDocConversations(docId, { render = true } = {}) {
  if (!docId || !isDiskWorkspaceProject()) return null;
  const data = await fetchDocConversationsApi(docId);
  state.docConversations[docId] = {
    sessions: Array.isArray(data.sessions) ? data.sessions : [],
    activeSessionId: data.activeSessionId || (Array.isArray(data.sessions) ? data.sessions[0]?.id : null) || null,
  };
  if (render && state.selectedDocId === docId && state.viewMode !== "database") {
    renderChat();
  }
  return state.docConversations[docId];
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
  const docId = doc.id;
  const useConversationApi = isDiskWorkspaceProject();
  if (!useConversationApi) {
    if (!state.threads[docId]) state.threads[docId] = { messages: [], suggestions: [], meta: "ready" };
    state.threads[docId].messages = state.threads[docId].messages || [];
    const userMsg = createChatMessage("user", text);
    appendMessage(userMsg.role, userMsg.text, userMsg);
    state.threads[docId].messages.push(userMsg);
  }

  setThreadMeta("thinking...");
  try {
    if (useConversationApi && !getDocConversationBundle(docId)) {
      await loadDocConversations(docId, { render: false });
    }
    const result = await askSelectionApi(docId, text);
    if (useConversationApi && result.session) {
      upsertConversationSession(docId, result.session, result.session.id);
      renderChat();
    } else {
      const reply = `${result.answer || ""}`;
      const assistantMsg = createChatMessage("assistant", reply, {
        citedChunkIds: result.cited_chunk_ids || [],
      });
      appendMessage(assistantMsg.role, assistantMsg.text, assistantMsg);
      state.threads[docId].messages.push(assistantMsg);
      state.threads[docId].suggestions = Array.isArray(result.follow_up_questions)
        ? result.follow_up_questions
        : [];
      renderSuggestions(state.threads[docId].suggestions);
      renderHistory(state.threads[docId]);
    }
    setThreadMeta("ready");
  } catch (err) {
    const msg = err instanceof Error ? err.message : "提问失败";
    const assistantMsg = createChatMessage("assistant", msg);
    appendMessage(assistantMsg.role, assistantMsg.text, assistantMsg);
    if (!useConversationApi) {
      state.threads[docId].messages.push(assistantMsg);
      renderHistory(state.threads[docId]);
    }
    setThreadMeta("error");
  }

  const hint = $("#resultsChatHint");
  if (hint) {
    const activeThread = useConversationApi
      ? conversationSessionToThread(getActiveConversationSession(docId), doc.name)
      : state.threads[docId];
    const lastAssistant = activeThread?.messages?.[activeThread.messages.length - 1]?.text || "";
    if (state.viewMode === "results") {
      const preview = lastAssistant.length > 220 ? `${lastAssistant.slice(0, 220)}…` : lastAssistant;
      hint.textContent = `与当前文档相关的对话摘要：\n${preview}`;
      hint.hidden = false;
    } else {
      hint.hidden = true;
    }
  }
  await saveWorkspaceToDisk();
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
      renderChunkExplorer();
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

  $("#chunkPageFilter")?.addEventListener("change", async (e) => {
    const doc = getSelectedDoc();
    if (!doc?.id || !isDiskWorkspaceProject()) return;
    const value = e.target.value;
    state.chunkListPage = value === "all" ? 0 : Number(value) || 0;
    try {
      const data = await fetchDocChunksApi(doc.id, state.chunkListPage || null);
      state.chunkListItems = Array.isArray(data?.chunks) ? data.chunks : [];
      renderChunkExplorer();
    } catch (err) {
      console.warn("[app] change chunk page", err);
    }
  });

  $("#btnRefreshChunks")?.addEventListener("click", async () => {
    const doc = getSelectedDoc();
    if (!doc?.id || !isDiskWorkspaceProject()) return;
    try {
      await refreshChunkExplorerForDoc(doc.id, { keepPage: true });
    } catch (err) {
      alert(err instanceof Error ? err.message : "刷新块失败");
    }
  });

  $("#btnRebuildVectorIndex")?.addEventListener("click", async () => {
    try {
      state.vectorIndexStatus = await rebuildVectorIndexApi();
      const doc = getSelectedDoc();
      if (doc?.id) await refreshChunkExplorerForDoc(doc.id, { keepPage: true });
    } catch (err) {
      alert(err instanceof Error ? err.message : "重建索引失败");
    }
  });

  $("#btnUpdateDocIndex")?.addEventListener("click", async () => {
    const doc = getSelectedDoc();
    if (!doc?.id || !isDiskWorkspaceProject()) return;
    try {
      state.vectorIndexStatus = await updateDocVectorIndexApi(doc.id);
      await refreshChunkExplorerForDoc(doc.id, { keepPage: true });
    } catch (err) {
      alert(err instanceof Error ? err.message : "更新索引失败");
    }
  });

  $("#btnDeleteDocIndex")?.addEventListener("click", async () => {
    const doc = getSelectedDoc();
    if (!doc?.id || !isDiskWorkspaceProject()) return;
    try {
      state.vectorIndexStatus = await deleteDocVectorIndexApi(doc.id);
      state.vectorSearchResults = [];
      renderChunkExplorer();
    } catch (err) {
      alert(err instanceof Error ? err.message : "删除索引失败");
    }
  });

  $("#btnVectorSearch")?.addEventListener("click", async () => {
    const doc = getSelectedDoc();
    const query = $("#vectorSearchInput")?.value?.trim() || "";
    if (!doc?.id || !query || !isDiskWorkspaceProject()) return;
    try {
      const data = await searchVectorIndexApi(query, doc.id, 5);
      state.vectorSearchResults = Array.isArray(data?.results) ? data.results : [];
      renderChunkExplorer();
    } catch (err) {
      alert(err instanceof Error ? err.message : "向量检索失败");
    }
  });

  $("#chatForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = $("#chatText").value;
    $("#chatText").value = "";
    await handleSendMessage(text);
  });

  $("#btnToggleHistory")?.addEventListener("click", () => {
    state.chatHistoryVisible = !state.chatHistoryVisible;
    if (state.viewMode === "database") {
      renderDbChat();
      return;
    }
    renderChat();
  });

  $("#btnNewConversation")?.addEventListener("click", async () => {
    const doc = getSelectedDoc();
    if (!doc || !isDiskWorkspaceProject()) return;
    try {
      const data = await createDocConversationApi(doc.id);
      upsertConversationSession(doc.id, data.session, data.activeSessionId || data.session?.id);
      $("#chatMessages").innerHTML = "";
      $("#chatText").value = "";
      state.chatHistoryVisible = false;
      renderChat();
    } catch (e) {
      console.warn("[app] create conversation failed", e);
      alert(e instanceof Error ? e.message : "新建对话失败");
    }
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
  pagesWrap.addEventListener("pointerdown", (e) => {
    const chunkEl = e.target.closest(".chunk-box");
    if (!chunkEl || e.button !== 0) return;
    const payload = getChunkPayloadFromElement(chunkEl);
    if (!payload?.chunkKey) return;

    resetChunkPress();
    state.chunkPress.pointerId = e.pointerId;
    state.chunkPress.anchorKey = payload.chunkKey;
    state.chunkPress.mode = state.selectedChunkKeys.includes(payload.chunkKey) ? "remove" : "add";
    state.chunkPress.timer = setTimeout(() => {
      state.chunkPress.active = true;
      state.chunkPress.timer = null;
      setSelectedChunkRange(payload, payload);
    }, 250);
  });
  pagesWrap.addEventListener("pointermove", (e) => {
    if (state.chunkPress.pointerId !== e.pointerId) return;
    const chunkEl = e.target.closest(".chunk-box");
    if (!chunkEl) return;
    const payload = getChunkPayloadFromElement(chunkEl);
    if (!payload?.chunkKey) return;

    state.chunkPress.moved = true;
    if (!state.chunkPress.active) return;

    const anchorEl = pagesWrap.querySelector(`.chunk-box[data-chunk-key="${state.chunkPress.anchorKey}"]`);
    const anchorPayload = getChunkPayloadFromElement(anchorEl);
    setSelectedChunkRange(anchorPayload, payload);
  });
  pagesWrap.addEventListener("pointerup", (e) => {
    if (state.chunkPress.pointerId !== e.pointerId) return;
    clearChunkPressTimer();
    state.chunkPress.active = false;
    state.chunkPress.pointerId = null;
    state.chunkPress.anchorKey = null;
    state.chunkPress.moved = false;
  });
  pagesWrap.addEventListener("pointercancel", () => {
    resetChunkPress();
  });
  pagesWrap.addEventListener("mouseover", (e) => {
    const chunkEl = e.target.closest(".chunk-box");
    if (chunkEl) {
      state.hoveredChunkKey = chunkEl.dataset.chunkKey || null;
      syncChunkSelectionClasses();
      return;
    }
    const el = e.target.closest(".ocr-block");
    if (!el) return;
    if (lastHover === el) return;
    if (lastHover && lastHover.classList) lastHover.classList.remove("block-hover");
    el.classList.add("block-hover");
    lastHover = el;
  });
  pagesWrap.addEventListener("mouseout", (e) => {
    const chunkEl = e.target.closest(".chunk-box");
    if (!chunkEl) return;
    const next = e.relatedTarget?.closest?.(".chunk-box");
    if (next === chunkEl) return;
    if (state.hoveredChunkKey === chunkEl.dataset.chunkKey) {
      state.hoveredChunkKey = null;
      syncChunkSelectionClasses();
    }
  });
  pagesWrap.addEventListener("click", (e) => {
    const chunkEl = e.target.closest(".chunk-box");
    if (!chunkEl) return;
    e.preventDefault();
    e.stopPropagation();
    if (state.chunkPress.active || state.chunkPress.moved) {
      resetChunkPress();
      return;
    }
    try {
      const payload = JSON.parse(chunkEl.dataset.chunkPayload || "{}");
      setSelectedChunk(payload);
    } catch {
      setSelectedChunk(null);
    }
  });

  document.addEventListener("click", (e) => {
    const citedBtn = e.target.closest(".cited-block-btn");
    if (!citedBtn) return;
    const message = citedBtn.closest(".msg.assistant");
    const citedBlocks = message?.querySelectorAll?.(".cited-block-btn") || [];
    const clickedLabel = String(citedBtn.textContent || "").trim();
    const related = Array.from(citedBlocks)
      .filter((btn) => String(btn.textContent || "").trim() === clickedLabel)
      .map((btn) => btn.textContent);
    void related;
  });
  pagesWrap.addEventListener("mouseleave", () => {
    if (lastHover && lastHover.classList) lastHover.classList.remove("block-hover");
    lastHover = null;
    resetChunkPress();
    if (state.hoveredChunkKey) {
      state.hoveredChunkKey = null;
      syncChunkSelectionClasses();
    }
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
  state.docConversations = {};

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
  clearChunkSelection({ persist: false });
  state.activeChunkDetail = null;
  state.activeChunkNeighbors = null;
  state.qaChunkContext = null;
  state.chunkPages = [];
  state.chunkListItems = [];
  state.vectorSearchResults = [];
  state.vectorIndexStatus = null;
  if (proj.storage === "disk") {
    const nowConversation = await fetchNowConversationFromApi(projectId);
    const items = Array.isArray(nowConversation?.selectedItems) ? nowConversation.selectedItems : [];
    if (items.length) {
      const targetDoc = state.docs.find((d) => d.id === items[0].docId);
      if (targetDoc) {
        state.selectedDocId = targetDoc.id;
        state.selectedChunkKeys = items.map((item) => item.chunkKey).filter(Boolean);
        state.selectedChunkItems = items;
      }
    }
    if (state.selectedDocId) {
      try {
        await loadDocConversations(state.selectedDocId, { render: false });
        await refreshChunkExplorerForDoc(state.selectedDocId, { keepPage: false });
      } catch (e) {
        console.warn("[app] load workspace extras failed", e);
      }
    }
  }
  renderChunkInspector();

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
