from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, List


KG_DIR_NAME = "kg"
KG_GRAPH_FILE = "question_driven_kg.json"
KG_ALGORITHM_VERSION = "question_event_v2"
MAX_KNOWLEDGE_NODES_PER_EVENT = 4
_STOP_TERMS = {
    "什么",
    "如何",
    "为什么",
    "是否",
    "哪些",
    "这个",
    "一下",
    "进行",
    "通过",
    "根据",
    "文档",
    "问题",
    "回答",
    "生成",
    "说明",
    "总结",
    "包括",
    "以及",
    "其中",
    "项目",
    "具体",
    "哪些",
    "文中",
    "报告",
}


def default_project_kg(project_id: str) -> Dict[str, Any]:
    return {
        "metadata": {
            "projectId": project_id,
            "mode": "question_driven_incremental_kg",
            "structuralPolicy": "Document sections and chunks are evidence only, not main graph nodes.",
            "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "nodeCount": 0,
            "edgeCount": 0,
        },
        "nodes": [],
        "edges": [],
        "events": [],
    }


def project_kg_dir(project_dir: Path) -> Path:
    return project_dir / KG_DIR_NAME


def project_kg_path(project_dir: Path) -> Path:
    return project_kg_dir(project_dir) / KG_GRAPH_FILE


def ensure_project_kg(project_dir: Path, project_id: str) -> Dict[str, Any]:
    kg_dir = project_kg_dir(project_dir)
    kg_dir.mkdir(parents=True, exist_ok=True)
    path = project_kg_path(project_dir)
    if not path.is_file():
        payload = default_project_kg(project_id)
        write_project_kg(project_dir, payload)
        return payload
    return read_project_kg(project_dir, project_id)


def read_project_kg(project_dir: Path, project_id: str) -> Dict[str, Any]:
    path = project_kg_path(project_dir)
    if not path.is_file():
        return default_project_kg(project_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default_project_kg(project_id)
    if not isinstance(payload, dict):
        return default_project_kg(project_id)
    nodes = payload.get("nodes") if isinstance(payload.get("nodes"), list) else []
    edges = payload.get("edges") if isinstance(payload.get("edges"), list) else []
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    metadata.setdefault("projectId", project_id)
    metadata.setdefault("mode", "question_driven_incremental_kg")
    metadata["nodeCount"] = len(nodes)
    metadata["edgeCount"] = len(edges)
    payload["metadata"] = metadata
    payload["nodes"] = [node for node in nodes if isinstance(node, dict)]
    payload["edges"] = [edge for edge in edges if isinstance(edge, dict)]
    payload["events"] = payload.get("events") if isinstance(payload.get("events"), list) else []
    return payload


def write_project_kg(project_dir: Path, payload: Dict[str, Any]) -> None:
    kg_dir = project_kg_dir(project_dir)
    kg_dir.mkdir(parents=True, exist_ok=True)
    path = project_kg_path(project_dir)
    nodes = payload.get("nodes") if isinstance(payload.get("nodes"), list) else []
    edges = payload.get("edges") if isinstance(payload.get("edges"), list) else []
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    metadata["nodeCount"] = len(nodes)
    metadata["edgeCount"] = len(edges)
    payload["metadata"] = metadata
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _node_id(prefix: str, text: str) -> str:
    cleaned = re.sub(r"\s+", "_", str(text or "").strip().lower())
    cleaned = re.sub(r"[^0-9a-zA-Z_\-\u4e00-\u9fff]+", "", cleaned).strip("_")
    return f"{prefix}:{cleaned[:48] or 'unknown'}"


def _upsert_node(
    nodes_by_id: Dict[str, Dict[str, Any]],
    node_id: str,
    label: str,
    node_type: str,
    qa_id: str,
    *,
    evidence: List[Dict[str, Any]] | None = None,
    score: float | None = None,
) -> Dict[str, Any]:
    node = nodes_by_id.get(node_id)
    if not node:
        node = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "sourceQaIds": [],
            "evidence": [],
        }
        nodes_by_id[node_id] = node
    if qa_id and qa_id not in node["sourceQaIds"]:
        node["sourceQaIds"].append(qa_id)
    if evidence:
        existing = {str(item.get("chunkId") or "") for item in node.get("evidence", []) if isinstance(item, dict)}
        for item in evidence:
            cid = str(item.get("chunkId") or "")
            if cid and cid not in existing:
                node.setdefault("evidence", []).append(item)
                existing.add(cid)
    if score is not None:
        node["score"] = round(max(float(node.get("score") or 0.0), float(score)), 3)
    return node


def _upsert_edge(
    edges_by_key: Dict[tuple[str, str, str], Dict[str, Any]],
    source: str,
    target: str,
    relation: str,
    qa_id: str,
    *,
    weight: float = 1.0,
) -> None:
    key = (source, target, relation)
    edge = edges_by_key.get(key)
    if not edge:
        edge = {
            "source": source,
            "target": target,
            "relation": relation,
            "sourceQaIds": [],
            "weight": 0.0,
        }
        edges_by_key[key] = edge
    if qa_id and qa_id not in edge["sourceQaIds"]:
        edge["sourceQaIds"].append(qa_id)
    edge["weight"] = round(float(edge.get("weight") or 0.0) + weight, 3)


def _clean_knowledge_label(value: str) -> str:
    label = re.sub(r"^[\s,，;；:：.\-、（(]*\d+[\)）.、\s]*", "", str(value or "").strip())
    label = re.sub(r"^(其|该|本|这个|一种|一个|项目的?|具体的?)", "", label)
    label = re.sub(r"(包括|为|是|指|通过|用于).*$", "", label).strip(" ，,;；:：。")
    return label[:24].strip()


def _knowledge_type(label: str) -> str:
    lower = label.lower()
    if any(token in label for token in ("机制", "方法", "流程", "框架", "模型")) or any(
        token in lower for token in ("rag", "sql", "agent", "t2sql")
    ):
        return "Method"
    if any(token in label for token in ("指标", "准确率", "召回", "分数", "率")):
        return "Metric"
    if any(token in label for token in ("数据集", "样本", "报告", "文档")):
        return "Dataset"
    if any(token in label for token in ("任务", "问题", "场景")):
        return "Task"
    if any(token in label for token in ("结论", "发现", "创新", "优势")):
        return "Claim"
    return "Concept"


def _question_focus_terms(question: str) -> List[str]:
    q = str(question or "")
    parts = re.split(r"[，,。？?；;：:\s]+", q)
    terms: List[str] = []
    for part in parts:
        label = _clean_knowledge_label(part)
        if 2 <= len(label) <= 18 and label not in _STOP_TERMS:
            terms.append(label)
    return terms[:3]


def _extract_terms(question: str, answer: str, limit: int = MAX_KNOWLEDGE_NODES_PER_EVENT) -> List[Dict[str, Any]]:
    text = f"{question}\n{answer}"
    segments = [item.strip() for item in re.split(r"(?:\(\d+\)|（\d+）|[。；;\n])", str(answer or "")) if item.strip()]
    counts: Counter[str] = Counter()
    reasons: Dict[str, List[str]] = {}
    question_terms = set(_question_focus_terms(question))

    for term in question_terms:
        counts[term] += 3
        reasons.setdefault(term, []).append("question_focus")

    for segment in segments:
        phrase = _clean_knowledge_label(segment)
        if 2 <= len(phrase) <= 24:
            counts[phrase] += 3
            reasons.setdefault(phrase, []).append("answer_claim")
        for raw in re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,10}", segment):
            term = _clean_knowledge_label(raw)
            if not term or term.lower() in _STOP_TERMS or term in _STOP_TERMS:
                continue
            if len(term) > 18:
                term = term[:18]
            counts[term] += 1
            reasons.setdefault(term, []).append("term_frequency")

    ranked: List[Dict[str, Any]] = []
    seen_labels: set[str] = set()
    for term, count in counts.most_common(limit * 3):
        if term in seen_labels or term.lower() in _STOP_TERMS or term in _STOP_TERMS:
            continue
        if len(term) < 2:
            continue
        reason_list = reasons.get(term, [])
        score = min(
            1.0,
            0.35
            + min(count, 5) * 0.08
            + (0.18 if "answer_claim" in reason_list else 0.0)
            + (0.18 if "question_focus" in reason_list else 0.0)
            + (0.12 if re.search(r"[A-Z]{2,}|Agent|SQL|RAG", term) else 0.0),
        )
        ranked.append(
            {
                "label": term,
                "type": _knowledge_type(term),
                "score": round(score, 3),
                "reasons": sorted(set(reason_list)),
            }
        )
        seen_labels.add(term)
        if len(ranked) >= limit:
            break
    return ranked


def _chunk_evidence(result: Dict[str, Any], cited_ids: List[str]) -> List[Dict[str, Any]]:
    evidence_by_id: Dict[str, Dict[str, Any]] = {}
    chunk_context = result.get("chunk_context") if isinstance(result.get("chunk_context"), dict) else {}
    for key in (
        "current",
        "neighbors",
        "retrieval",
        "current_chunks",
        "neighbor_chunks",
        "retrieval_chunks",
        "currentChunks",
        "neighborChunks",
        "retrievalChunks",
    ):
        items = chunk_context.get(key) if isinstance(chunk_context.get(key), list) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("chunkId") or item.get("chunkKey") or item.get("id") or "").strip()
            if not cid or cid in evidence_by_id:
                continue
            evidence_by_id[cid] = {
                "chunkId": cid,
                "pageNo": item.get("pageNo") or item.get("page") or "",
                "textPreview": str(item.get("text") or item.get("content") or item.get("preview") or "")[:220],
            }
    out: List[Dict[str, Any]] = []
    for cid in cited_ids:
        out.append(evidence_by_id.get(cid, {"chunkId": cid, "pageNo": "", "textPreview": ""}))
    return out[:8]


def _edge_key(edge: Dict[str, Any]) -> tuple[str, str, str]:
    return (str(edge.get("source") or ""), str(edge.get("target") or ""), str(edge.get("relation") or ""))


def _build_graph_from_events(project_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes_by_id: Dict[str, Dict[str, Any]] = {}
    edges_by_key: Dict[tuple[str, str, str], Dict[str, Any]] = {}

    _upsert_node(nodes_by_id, "deepdoc", "DeepDOC", "System", "", score=1.0)
    _upsert_node(nodes_by_id, "question_driven_kg", "Question Driven KG", "Capability", "", score=1.0)
    _upsert_edge(edges_by_key, "deepdoc", "question_driven_kg", "USES", "", weight=1.0)

    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            continue
        qa_id = str(event.get("id") or f"qa:event:{index}")
        question = str(event.get("question") or "").strip()
        answer = str(event.get("answerPreview") or event.get("answer") or "").strip()
        doc_id = str(event.get("docId") or "").strip()
        doc_name = str(event.get("docName") or doc_id or "Document").strip()
        evidence = event.get("evidence") if isinstance(event.get("evidence"), list) else []
        candidates = event.get("knowledgeCandidates")
        if not isinstance(candidates, list):
            candidates = _extract_terms(question, answer)

        doc_node_id = _node_id("doc", doc_id or doc_name)
        question_node_id = _node_id("question", qa_id)
        _upsert_node(nodes_by_id, doc_node_id, doc_name or doc_id, "Document", qa_id, evidence=evidence, score=0.8)
        question_node = _upsert_node(
            nodes_by_id,
            question_node_id,
            question[:80] or qa_id,
            "QuestionEvent",
            qa_id,
            evidence=evidence,
            score=1.0,
        )
        question_node["intent"] = str(event.get("taskType") or "")
        question_node["retrievalMode"] = str(event.get("retrievalMode") or "")
        question_node["answerPreview"] = answer[:280]

        _upsert_edge(edges_by_key, "question_driven_kg", question_node_id, "EXPANDS_FROM", qa_id, weight=1.0)
        _upsert_edge(edges_by_key, question_node_id, doc_node_id, "ASKS_ABOUT", qa_id, weight=0.8)

        for candidate in candidates[:MAX_KNOWLEDGE_NODES_PER_EVENT]:
            if not isinstance(candidate, dict):
                continue
            label = _clean_knowledge_label(str(candidate.get("label") or ""))
            if not label:
                continue
            node_type = str(candidate.get("type") or _knowledge_type(label))
            score = float(candidate.get("score") or 0.6)
            concept_node_id = _node_id("knowledge", label)
            node = _upsert_node(
                nodes_by_id,
                concept_node_id,
                label,
                node_type,
                qa_id,
                evidence=evidence,
                score=score,
            )
            node["reasons"] = sorted(set((node.get("reasons") or []) + list(candidate.get("reasons") or [])))
            _upsert_edge(edges_by_key, question_node_id, concept_node_id, "FOCUSES_ON", qa_id, weight=score)
            _upsert_edge(edges_by_key, concept_node_id, doc_node_id, "GROUNDED_IN", qa_id, weight=max(0.4, score - 0.1))

    metadata = {
        "projectId": project_id,
        "mode": "question_driven_incremental_kg",
        "algorithm": KG_ALGORITHM_VERSION,
        "structuralPolicy": (
            "The graph is rebuilt from question events. Chunks stay as evidence in node detail; "
            "weak co-occurrence edges are excluded from the main graph."
        ),
        "updatedAt": _utc_now(),
    }
    return {
        "metadata": metadata,
        "nodes": list(nodes_by_id.values()),
        "edges": list(edges_by_key.values()),
        "events": events,
    }


def update_project_kg_from_qa(
    project_dir: Path,
    project_id: str,
    *,
    doc_id: str,
    doc_name: str,
    session_id: str,
    question: str,
    result: Dict[str, Any],
    task_type: str = "",
    retrieval_mode: str = "",
) -> Dict[str, Any]:
    payload = ensure_project_kg(project_dir, project_id)
    qa_id = f"qa:{session_id}:{len(payload.get('events') or []) + 1}"
    answer = str(result.get("answer") or "")
    cited_ids = [str(item) for item in (result.get("cited_chunk_ids") or []) if str(item).strip()]
    evidence = _chunk_evidence(result, cited_ids)
    events = payload.get("events") if isinstance(payload.get("events"), list) else []
    events.append(
        {
            "id": qa_id,
            "createdAt": _utc_now(),
            "docId": doc_id,
            "docName": doc_name,
            "sessionId": session_id,
            "question": question,
            "answerPreview": answer[:280],
            "taskType": task_type,
            "retrievalMode": retrieval_mode,
            "citedChunkIds": cited_ids,
            "evidence": evidence,
            "knowledgeCandidates": _extract_terms(question, answer),
        }
    )
    payload = _build_graph_from_events(project_id, events)
    write_project_kg(project_dir, payload)
    return payload


def render_project_kg_html(payload: Dict[str, Any]) -> str:
    nodes = [node for node in payload.get("nodes", []) if isinstance(node, dict)]
    edges = [edge for edge in payload.get("edges", []) if isinstance(edge, dict)]
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    project_id = str(metadata.get("projectId") or "")
    node_ids = {str(node.get("id") or "") for node in nodes}
    visible_edges = [
        edge
        for edge in edges
        if str(edge.get("source") or "") in node_ids and str(edge.get("target") or "") in node_ids
    ]
    node_types = Counter(str(node.get("type") or "Unknown") for node in nodes)
    rel_types = Counter(str(edge.get("relation") or "related_to") for edge in visible_edges)
    default_center = str(nodes[0].get("id") or "") if nodes else ""
    for preferred in ("deepdoc", "question_driven_kg", "knowledge_graph"):
        if preferred in node_ids:
            default_center = preferred
            break

    type_color = {
        "System": "#4e79a7",
        "Method": "#e15759",
        "Capability": "#59a14f",
        "Problem": "#f28e2c",
        "Task": "#b07aa1",
        "QuestionEvent": "#b07aa1",
        "Concept": "#76b7b2",
        "Claim": "#8cd17d",
        "Metric": "#edc948",
        "Scenario": "#9c755f",
        "Dataset": "#f1ce63",
        "Evidence": "#86bcb6",
        "Deliverable": "#ff9da7",
        "Interaction": "#bab0ac",
    }

    node_legend = "".join(
        f'<span><i style="background:{type_color.get(t, "#64748b")}"></i>{escape(t)} ({count})</span>'
        for t, count in node_types.most_common()
    ) or '<span class="muted">No nodes yet</span>'
    rel_legend = "".join(
        f"<span>{escape(t)} ({count})</span>" for t, count in rel_types.most_common()
    ) or '<span class="muted">No relations yet</span>'

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DeepDOC Project KG</title>
  <style>
    :root {{
      --bg-page:#f7f8fa; --surface:#fff; --surface-muted:#fafafa;
      --accent:#4a6fa5; --accent-ring:rgba(74,111,165,.22);
      --btn-primary-bg:#1a1d24; --btn-primary-hover:#2a2f3a;
      --btn-secondary-bg:#eceef2; --btn-secondary-hover:#e0e3e9;
      --border-subtle:#eeeeee; --border-input:#e5e5e5;
      --text-title:#111; --text-body:#333; --text-muted:#888;
      --radius-control:12px; --radius-btn:11px; --shadow-float:0 2px 8px rgba(0,0,0,.04);
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg-page); color:var(--text-body); overflow:hidden; font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Microsoft YaHei",sans-serif; }}
    .app-shell {{ height:100vh; display:flex; flex-direction:column; overflow:hidden; }}
    .topbar {{ height:56px; display:flex; align-items:center; justify-content:space-between; padding:0 16px; background:rgba(255,255,255,.88); border-bottom:1px solid var(--border-subtle); backdrop-filter:blur(10px); box-shadow:0 1px 0 rgba(0,0,0,.03); flex:0 0 auto; }}
    .brand {{ display:flex; align-items:center; gap:12px; }}
    .brand-icon {{ width:36px; height:36px; border-radius:var(--radius-control); background:var(--btn-primary-bg); color:#fff; display:grid; place-items:center; box-shadow:var(--shadow-float); }}
    .brand-title {{ font-weight:700; font-size:15px; color:var(--text-title); line-height:1.15; }}
    .brand-subtitle {{ font-size:12px; color:var(--text-muted); margin-top:3px; font-weight:500; }}
    .layout {{ display:grid; grid-template-columns:320px minmax(0,1fr) 360px; min-height:0; flex:1; }}
    aside,.detail {{ background:var(--surface); padding:18px; overflow:auto; border-color:var(--border-subtle); }}
    aside {{ border-right:1px solid var(--border-subtle); }}
    .detail {{ border-left:1px solid var(--border-subtle); }}
    h1 {{ margin:0 0 12px; color:var(--text-title); font-size:16px; font-weight:700; }}
    h2 {{ margin:18px 0 8px; color:var(--text-title); font-size:13px; font-weight:700; }}
    .stat {{ margin:6px 0; color:var(--text-muted); font-size:13px; }}
    .hint,.muted {{ color:var(--text-muted); font-size:12px; line-height:1.55; }}
    input,select {{ width:100%; padding:10px 12px; margin:6px 0; border:1px solid var(--border-input); border-radius:var(--radius-control); background:var(--surface); color:var(--text-body); outline:none; font:inherit; font-size:13px; }}
    input:focus,select:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-ring); }}
    button {{ background:var(--btn-secondary-bg); color:var(--text-body); border:1px solid var(--border-subtle); border-radius:var(--radius-btn); padding:10px 14px; cursor:pointer; font-weight:600; font-size:13px; }}
    button:hover {{ background:var(--btn-secondary-hover); }}
    #btnSearch,#btnCore {{ background:var(--btn-primary-bg); color:#fff; border-color:var(--btn-primary-bg); }}
    #btnSearch:hover,#btnCore:hover {{ background:var(--btn-primary-hover); }}
    .actions {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:8px; }}
    .chips {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }}
    .chip {{ padding:5px 9px; border:1px solid var(--border-subtle); border-radius:999px; font-size:12px; color:var(--text-body); background:var(--surface-muted); }}
    .chip:hover {{ border-color:var(--accent); color:var(--accent); cursor:pointer; }}
    .legend {{ display:grid; gap:6px; margin-top:8px; }}
    .legend span {{ display:flex; gap:8px; align-items:center; font-size:13px; color:var(--text-body); }}
    .legend i {{ width:10px; height:10px; border-radius:50%; display:inline-block; box-shadow:inset 0 0 0 1px rgba(0,0,0,.08); }}
    main {{ position:relative; min-width:0; background:linear-gradient(180deg,#fff 0%,#fafafa 100%); overflow:hidden; }}
    svg {{ display:block; width:100%; height:100%; cursor:grab; }}
    svg.dragging {{ cursor:grabbing; }}
    .toolbar {{ position:absolute; left:16px; top:16px; display:flex; gap:8px; z-index:2; }}
    .badge {{ position:absolute; right:16px; top:16px; padding:8px 10px; border:1px solid var(--border-subtle); border-radius:var(--radius-control); background:rgba(255,255,255,.88); color:var(--text-muted); font-size:12px; box-shadow:var(--shadow-float); z-index:2; }}
    .edge {{ stroke:#c7ccd6; stroke-opacity:.72; stroke-width:1.45; }}
    .edge.focus {{ stroke:var(--accent); stroke-opacity:.95; stroke-width:2.4; }}
    .edge.dim {{ stroke:#d8dce3; stroke-opacity:.16; stroke-width:1; }}
    .edge-label {{ fill:#6b7280; font-size:10px; pointer-events:none; text-anchor:middle; paint-order:stroke; stroke:#fff; stroke-width:4px; }}
    .edge-label.dim {{ fill:#aeb5c0; opacity:.18; }}
    .node circle {{ stroke:#fff; stroke-width:2.4px; cursor:pointer; filter:drop-shadow(0 2px 4px rgba(0,0,0,.12)); }}
    .node.center circle {{ stroke:var(--accent); stroke-width:4px; }}
    .node.selected circle {{ stroke:var(--btn-primary-bg); stroke-width:3px; }}
    .node.dim circle {{ opacity:.18; filter:grayscale(1); }}
    .node.dim text {{ opacity:.22; fill:#9ca3af; }}
    .node.neighbor circle {{ stroke:var(--accent); stroke-width:2.8px; }}
    .node text {{ fill:var(--text-title); font-size:11px; font-weight:600; text-anchor:middle; pointer-events:none; paint-order:stroke; stroke:#fff; stroke-width:4px; }}
    .item {{ border:1px solid var(--border-subtle); background:var(--surface-muted); border-radius:8px; padding:8px; margin:8px 0; font-size:12px; line-height:1.5; }}
    code {{ color:var(--accent); font-family:ui-monospace,SFMono-Regular,Consolas,monospace; }}
    b {{ color:var(--text-title); font-weight:700; }}
    .empty-state {{ height:100%; display:grid; place-items:center; padding:32px; text-align:center; color:var(--text-muted); }}
  </style>
</head>
<body>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand"><div class="brand-icon" aria-hidden="true">◆</div><div><div class="brand-title">DeepDOC</div><div class="brand-subtitle">问题驱动知识图谱</div></div></div>
      <div class="stat">Project KG · Query-centered view</div>
    </header>
    <div class="layout">
      <aside>
        <h1>查询中心图谱</h1>
        <div class="stat">全量节点: <code>{len(nodes)}</code></div>
        <div class="stat">全量关系: <code>{len(visible_edges)}</code></div>
        <div class="stat">Project: <code>{escape(project_id)}</code></div>
        <div class="hint">输入问题或实体名后，只展示匹配实体及其一跳/二跳邻居。双击图中节点会以该节点为中心重新展开。</div>
        <input id="queryInput" placeholder="例如：LAD-RAG、传统 RAG、图表生成" />
        <select id="hopSelect"><option value="1">展开一跳关系</option><option value="2" selected>展开二跳关系</option></select>
        <div class="actions"><button id="btnSearch" type="button">查询</button><button id="btnCore" type="button">核心图</button></div>
        <h2>推荐入口</h2><div class="chips" id="chips"></div>
        <h2>节点类型</h2><div class="legend">{node_legend}</div>
        <h2>关系类型</h2><div class="legend">{rel_legend}</div>
      </aside>
      <main><div class="toolbar"><button id="btnFit" type="button">适配</button><button id="btnReset" type="button">重排</button></div><div class="badge" id="subgraphBadge"></div><svg id="graphSvg"></svg><div id="emptyState" class="empty-state" hidden><div><h1>当前项目还没有问题驱动知识图谱</h1><p>在文档问答后，系统会把有价值的实体、关系和证据沉淀到这里。</p></div></div></main>
      <section class="detail" id="detail"><h1>当前子图</h1><div class="muted">选择一个入口实体或输入查询。</div></section>
    </div>
  </div>
  <script>
    const allNodes = {json.dumps(nodes, ensure_ascii=False)};
    const allEdges = {json.dumps(visible_edges, ensure_ascii=False)};
    const colors = {json.dumps(type_color, ensure_ascii=False)};
    const defaultCenter = {json.dumps(default_center, ensure_ascii=False)};
    const nodeById = new Map(allNodes.map(n => [n.id, n]));
    const adj = new Map();
    allEdges.forEach(edge => {{
      if (!adj.has(edge.source)) adj.set(edge.source, []);
      if (!adj.has(edge.target)) adj.set(edge.target, []);
      adj.get(edge.source).push(edge);
      adj.get(edge.target).push(edge);
    }});
    const svg = document.getElementById("graphSvg");
    const detail = document.getElementById("detail");
    const badge = document.getElementById("subgraphBadge");
    const emptyState = document.getElementById("emptyState");
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const labelLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.append(edgeLayer, labelLayer, nodeLayer);
    svg.appendChild(g);
    let width = 1, height = 1, viewNodes = [], viewEdges = [], centerId = defaultCenter, selectedId = null;
    let transform = {{ x: 0, y: 0, scale: 1 }}, panning = false, draggingNode = null, last = {{ x: 0, y: 0 }};
    const chipIds = ["deepdoc", "rag", "lad", "knowledge_graph", "question_driven_kg", "chart_generation", "cross_document_qa"];
    const chips = document.getElementById("chips");
    chipIds.filter(id => nodeById.has(id)).forEach(id => {{
      const item = document.createElement("span");
      item.className = "chip";
      item.textContent = nodeById.get(id).label;
      item.onclick = () => setCenter(id, Number(document.getElementById("hopSelect").value));
      chips.appendChild(item);
    }});
    if (!chips.children.length) chips.innerHTML = '<span class="muted">暂无入口实体</span>';
    function subgraphFromCenter(id, hops) {{
      const ids = new Set([id]); let frontier = new Set([id]);
      for (let step = 0; step < hops; step++) {{
        const next = new Set();
        frontier.forEach(nodeId => (adj.get(nodeId) || []).forEach(edge => {{
          const other = edge.source === nodeId ? edge.target : edge.source;
          ids.add(other); next.add(other);
        }}));
        frontier = next;
      }}
      const nodes = allNodes.filter(node => ids.has(node.id));
      const nodeSet = new Set(nodes.map(node => node.id));
      const edges = allEdges.filter(edge => nodeSet.has(edge.source) && nodeSet.has(edge.target));
      return {{ nodes, edges }};
    }}
    function searchBest(query) {{
      const q = query.trim().toLowerCase();
      if (!q) return defaultCenter;
      const exact = allNodes.find(node => node.label.toLowerCase() === q || node.id.toLowerCase() === q);
      if (exact) return exact.id;
      const partial = allNodes.find(node => node.label.toLowerCase().includes(q) || node.id.toLowerCase().includes(q));
      return partial ? partial.id : defaultCenter;
    }}
    function setCenter(id, hops) {{
      if (!id || !nodeById.has(id)) return showEmpty();
      centerId = id; selectedId = id;
      const sub = subgraphFromCenter(id, hops);
      viewNodes = sub.nodes.map(node => ({{ ...node }})); viewEdges = sub.edges;
      layout(); render(); fitView(); showDetail(nodeById.get(id));
      badge.textContent = `${{nodeById.get(id).label}} · ${{viewNodes.length}} nodes · ${{viewEdges.length}} edges`;
      emptyState.hidden = true; svg.hidden = false;
    }}
    function showCore() {{
      if (!allNodes.length) return showEmpty();
      const coreIds = ["deepdoc", "document_parsing", "rag", "lad", "knowledge_graph", "evidence_traceability", "content_generation", "chart_generation", "report_generation"].filter(id => nodeById.has(id));
      const ids = coreIds.length ? coreIds : [defaultCenter];
      const coreSet = new Set(ids);
      viewNodes = allNodes.filter(node => coreSet.has(node.id)).map(node => ({{ ...node }}));
      viewEdges = allEdges.filter(edge => coreSet.has(edge.source) && coreSet.has(edge.target));
      centerId = ids[0]; selectedId = centerId; layout(); render(); fitView(); showDetail(nodeById.get(centerId));
      badge.textContent = `核心图 · ${{viewNodes.length}} nodes · ${{viewEdges.length}} edges`;
      emptyState.hidden = true; svg.hidden = false;
    }}
    function showEmpty() {{
      svg.hidden = true; emptyState.hidden = false; badge.textContent = "Empty KG";
    }}
    function layout() {{
      const local = new Map(viewNodes.map(node => [node.id, node]));
      viewNodes.forEach((node, index) => {{
        const angle = index / Math.max(1, viewNodes.length) * Math.PI * 2;
        const ring = node.id === centerId ? 0 : 180 + (index % 3) * 70;
        node.x = width / 2 + Math.cos(angle) * ring; node.y = height / 2 + Math.sin(angle) * ring;
        node.vx = 0; node.vy = 0; node.r = node.id === centerId ? 21 : node.type === "Method" ? 16 : 14;
      }});
      for (let i = 0; i < 180; i++) {{
        viewNodes.forEach((a, ai) => {{
          for (let bi = ai + 1; bi < viewNodes.length; bi++) {{
            const b = viewNodes[bi]; let dx = b.x - a.x, dy = b.y - a.y;
            let d2 = dx * dx + dy * dy || 1, d = Math.sqrt(d2), f = Math.min(1600 / d2, 1.8);
            dx /= d; dy /= d; a.vx -= dx * f; a.vy -= dy * f; b.vx += dx * f; b.vy += dy * f;
          }}
        }});
        viewEdges.forEach(edge => {{
          const a = local.get(edge.source), b = local.get(edge.target); if (!a || !b) return;
          let dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) || 1, f = (d - 145) * .016;
          dx /= d; dy /= d; a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
        }});
        viewNodes.forEach(node => {{
          node.vx += (width / 2 - node.x) * .004; node.vy += (height / 2 - node.y) * .004;
          if (node.id === centerId) {{ node.vx += (width / 2 - node.x) * .08; node.vy += (height / 2 - node.y) * .08; }}
          node.x += node.vx; node.y += node.vy; node.vx *= .76; node.vy *= .76;
        }});
      }}
    }}
    function render() {{
      const local = new Map(viewNodes.map(node => [node.id, node]));
      const focusIds = new Set();
      const focusEdgeKeys = new Set();
      if (selectedId && nodeById.has(selectedId)) {{
        focusIds.add(selectedId);
        (adj.get(selectedId) || []).forEach(edge => {{
          const other = edge.source === selectedId ? edge.target : edge.source;
          focusIds.add(other);
          focusEdgeKeys.add(`${{edge.source}}|${{edge.target}}|${{edge.relation}}`);
        }});
      }}
      edgeLayer.textContent = ""; labelLayer.textContent = ""; nodeLayer.textContent = "";
      viewEdges.forEach(edge => {{
        const s = local.get(edge.source), t = local.get(edge.target); if (!s || !t) return;
        const edgeKey = `${{edge.source}}|${{edge.target}}|${{edge.relation}}`;
        const isFocus = !selectedId || focusEdgeKeys.has(edgeKey);
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("class", `edge ${{isFocus ? "focus" : "dim"}}`);
        line.setAttribute("x1", s.x); line.setAttribute("y1", s.y); line.setAttribute("x2", t.x); line.setAttribute("y2", t.y); edgeLayer.appendChild(line);
        const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
        label.setAttribute("class", `edge-label ${{isFocus ? "" : "dim"}}`); label.setAttribute("x", (s.x + t.x) / 2); label.setAttribute("y", (s.y + t.y) / 2); label.textContent = edge.relation; labelLayer.appendChild(label);
      }});
      viewNodes.forEach(node => {{
        const item = document.createElementNS("http://www.w3.org/2000/svg", "g");
        const isFocusNode = !selectedId || focusIds.has(node.id);
        item.setAttribute("class", `node ${{node.id === centerId ? "center" : ""}} ${{node.id === selectedId ? "selected" : ""}} ${{selectedId && node.id !== selectedId && focusIds.has(node.id) ? "neighbor" : ""}} ${{isFocusNode ? "" : "dim"}}`);
        item.setAttribute("transform", `translate(${{node.x}},${{node.y}})`); item.dataset.id = node.id;
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle"); circle.setAttribute("r", node.r); circle.setAttribute("fill", colors[node.type] || "#64748b"); item.appendChild(circle);
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text"); text.setAttribute("y", -(node.r + 8)); text.textContent = node.label.length > 14 ? `${{node.label.slice(0, 13)}}...` : node.label; item.appendChild(text);
        nodeLayer.appendChild(item);
      }});
      applyTransform();
    }}
    function showDetail(node) {{
      const relations = (adj.get(node.id) || []).filter(edge => viewEdges.includes(edge));
      const evidence = (node.evidence || []).slice(0, 5);
      const score = Number.isFinite(Number(node.score)) ? `<span class="chip">score ${{Number(node.score).toFixed(2)}}</span>` : "";
      const intent = node.intent ? `<div class="item"><b>Intent</b>: ${{escapeHtml(node.intent)}}<br><b>Retrieval</b>: ${{escapeHtml(node.retrievalMode || "")}}</div>` : "";
      const answerPreview = node.answerPreview ? `<div class="item">${{escapeHtml(node.answerPreview)}}</div>` : "";
      const reasons = (node.reasons || []).length ? `<h2>Calculation</h2>${{node.reasons.map(reason => `<span class="chip">${{escapeHtml(reason)}}</span>`).join(" ")}}` : "";
      detail.innerHTML = `<h1>${{escapeHtml(node.label)}}</h1><div><span class="chip">${{escapeHtml(node.type)}}</span><span class="chip">${{escapeHtml(node.id)}}</span>${{score}}</div>${{intent}}${{answerPreview}}${{reasons}}<h2>Source QA</h2>${{(node.sourceQaIds || []).map(id => `<div class="item"><code>${{escapeHtml(id)}}</code></div>`).join("") || "<div class='muted'>None</div>"}}<h2>Subgraph Relations</h2>${{relations.map(edge => {{ const otherId = edge.source === node.id ? edge.target : edge.source; const other = nodeById.get(otherId); const arrow = edge.source === node.id ? "->" : "<-"; return `<div class="item"><b>${{escapeHtml(edge.relation)}}</b> ${{arrow}} <code>${{escapeHtml(other?.label || otherId)}}</code>${{Number.isFinite(Number(edge.weight)) ? `<br>weight ${{Number(edge.weight).toFixed(2)}}` : ""}}</div>`; }}).join("") || "<div class='muted'>None</div>"}}<h2>Evidence Chunks</h2>${{evidence.map(ev => `<div class="item"><code>${{escapeHtml(ev.chunkId || "")}}</code> ? page ${{escapeHtml(String(ev.pageNo || ""))}}<br>${{escapeHtml(ev.textPreview || "")}}</div>`).join("") || "<div class='muted'>None</div>"}}`;
    }}
    function escapeHtml(value) {{ return String(value).replace(/[&<>"']/g, ch => ({{ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }}[ch])); }}
    function point(event) {{ const r = svg.getBoundingClientRect(); return {{ x: event.clientX - r.left, y: event.clientY - r.top }}; }}
    function screenToWorld(p) {{ return {{ x: (p.x - transform.x) / transform.scale, y: (p.y - transform.y) / transform.scale }}; }}
    function applyTransform() {{ g.setAttribute("transform", `translate(${{transform.x}},${{transform.y}}) scale(${{transform.scale}})`); }}
    function fitView() {{
      if (!viewNodes.length) return; const xs = viewNodes.map(n => n.x), ys = viewNodes.map(n => n.y);
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys), pad = 110;
      transform.scale = Math.max(.25, Math.min(width / (maxX - minX + pad * 2), height / (maxY - minY + pad * 2), 1.5));
      transform.x = width / 2 - ((minX + maxX) / 2) * transform.scale; transform.y = height / 2 - ((minY + maxY) / 2) * transform.scale; applyTransform();
    }}
    svg.addEventListener("mousedown", event => {{
      const target = event.target.closest(".node"); last = point(event);
      if (target) {{ const id = target.dataset.id; draggingNode = viewNodes.find(n => n.id === id); selectedId = id; showDetail(nodeById.get(id)); render(); }}
      else {{ panning = true; svg.classList.add("dragging"); }}
    }});
    window.addEventListener("mousemove", event => {{
      const p = point(event);
      if (draggingNode) {{ const w = screenToWorld(p); draggingNode.x = w.x; draggingNode.y = w.y; render(); }}
      else if (panning) {{ transform.x += p.x - last.x; transform.y += p.y - last.y; applyTransform(); }}
      last = p;
    }});
    window.addEventListener("mouseup", () => {{ draggingNode = null; panning = false; svg.classList.remove("dragging"); }});
    svg.addEventListener("dblclick", event => {{ const target = event.target.closest(".node"); if (target) setCenter(target.dataset.id, Number(document.getElementById("hopSelect").value)); }});
    svg.addEventListener("wheel", event => {{ event.preventDefault(); const p = point(event), before = screenToWorld(p); transform.scale = Math.max(.2, Math.min(4, transform.scale * (event.deltaY > 0 ? .9 : 1.1))); transform.x = p.x - before.x * transform.scale; transform.y = p.y - before.y * transform.scale; applyTransform(); }}, {{ passive:false }});
    document.getElementById("btnSearch").onclick = () => setCenter(searchBest(document.getElementById("queryInput").value), Number(document.getElementById("hopSelect").value));
    document.getElementById("queryInput").addEventListener("keydown", event => {{ if (event.key === "Enter") document.getElementById("btnSearch").click(); }});
    document.getElementById("btnCore").onclick = showCore; document.getElementById("btnFit").onclick = fitView; document.getElementById("btnReset").onclick = () => setCenter(centerId, Number(document.getElementById("hopSelect").value));
    function resize() {{ const r = svg.getBoundingClientRect(); width = r.width; height = r.height; svg.setAttribute("viewBox", `0 0 ${{width}} ${{height}}`); }}
    window.addEventListener("resize", () => {{ resize(); fitView(); }}); resize(); showCore();
  </script>
</body>
</html>"""
