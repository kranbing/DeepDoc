from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fastapi import HTTPException

from backend.clients.deepseek_client import deepseek_chat_json
from backend.services.chunk_store import read_document_chunks, save_document_chunks


def chunk_key(item: Dict[str, Any]) -> str:
    return str(item.get("chunkKey") or item.get("chunkId") or "").strip()


def chunk_payload_to_prompt_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cid = chunk_key(item)
    if not cid:
        return None
    return {
        "chunkKey": cid,
        "chunkId": cid,
        "docId": str(item.get("docId") or "").strip(),
        "docName": str(item.get("docName") or "").strip(),
        "pageNo": int(item.get("pageNo") or 0),
        "index": int(item.get("index") or 0),
        "label": str(item.get("label") or "chunk"),
        "content": str(item.get("content") or item.get("normalizedContent") or "").strip(),
        "bboxPx": item.get("bboxPx") if isinstance(item.get("bboxPx"), dict) else {},
        "bboxNorm": item.get("bboxNorm") if isinstance(item.get("bboxNorm"), dict) else {},
        "charCount": int(item.get("charCount") or 0),
        "score": float(item.get("score")) if isinstance(item.get("score"), (int, float)) else None,
        "sourceChunkIds": [
            str(v).strip()
            for v in (item.get("sourceChunkIds") if isinstance(item.get("sourceChunkIds"), list) else [])
            if str(v).strip()
        ],
        "sourcePageNos": [
            int(v)
            for v in (item.get("sourcePageNos") if isinstance(item.get("sourcePageNos"), list) else [])
            if isinstance(v, (int, float))
        ],
        "sourceChunkCount": int(item.get("sourceChunkCount") or 0),
        "sourceType": str(item.get("sourceType") or "").strip(),
    }


def normalize_chunk_context_items(items: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    seen: Set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized = chunk_payload_to_prompt_item(item)
        if not normalized:
            continue
        cid = str(normalized.get("chunkId") or "")
        if cid in seen:
            continue
        seen.add(cid)
        out.append(normalized)
    out.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
    return out


def dedupe_chunk_items(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for group in groups:
        for item in group:
            if not isinstance(item, dict):
                continue
            normalized = chunk_payload_to_prompt_item(item)
            if not normalized:
                continue
            cid = str(normalized.get("chunkId") or "")
            if cid in seen:
                continue
            seen.add(cid)
            out.append(normalized)
    out.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
    return out


def serialize_chunk_context_payload(
    *,
    source: str,
    current_chunks: List[Dict[str, Any]],
    neighbor_chunks: List[Dict[str, Any]],
    retrieval_chunks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "source": source,
        "currentChunks": current_chunks,
        "neighborChunks": neighbor_chunks,
        "retrievalChunks": retrieval_chunks or [],
    }


def ensure_doc_chunks_ready(project_dir: Path, doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("id") or "")
    payload = read_document_chunks(project_dir, doc_id)
    if isinstance(payload, dict) and str(payload.get("status") or "") == "ready":
        return payload
    if not doc.get("ocrParsed"):
        raise HTTPException(status_code=400, detail="文档尚未完成 OCR 解析，无法读取块信息。")
    return save_document_chunks(project_dir, doc)


def normalize_qa_response(payload: Dict[str, Any], allowed_ids: Sequence[str]) -> Dict[str, Any]:
    allowed = {str(item) for item in allowed_ids}
    cited = payload.get("cited_chunk_ids")
    if not isinstance(cited, list):
        cited = []
    cited_ids = [str(value) for value in cited if str(value) in allowed]
    answer = str(payload.get("answer") or "").strip()
    follow = payload.get("follow_up_questions")
    if not isinstance(follow, list):
        follow = []
    follow_up = [str(value).strip() for value in follow if str(value).strip()][:2]
    while len(follow_up) < 2:
        follow_up.append("继续追问这部分")
    if not answer:
        raise ValueError("empty answer")
    return {
        "cited_chunk_ids": cited_ids,
        "answer": answer,
        "follow_up_questions": follow_up,
    }


def _normalize_selected_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cid = chunk_key(item)
    if not cid:
        return None
    return {
        "chunkKey": cid,
        "chunkId": str(item.get("chunkId") or cid),
        "pageNo": int(item.get("pageNo") or 0),
        "index": int(item.get("index") or 0),
        "label": str(item.get("label") or "chunk"),
        "content": str(item.get("content") or "").strip(),
        "bboxPx": item.get("bboxPx") if isinstance(item.get("bboxPx"), dict) else {},
        "bboxNorm": item.get("bboxNorm") if isinstance(item.get("bboxNorm"), dict) else {},
        "sourceLabels": item.get("sourceLabels") if isinstance(item.get("sourceLabels"), list) else [],
        "sourceChunkCount": int(item.get("sourceChunkCount") or 0),
    }


def _build_page_bands(page: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
    page_no = int(page.get("pageNo") or 0)
    image_size = page.get("imageSize") if isinstance(page.get("imageSize"), dict) else {}
    page_width = int(image_size.get("width") or 0)
    ranges: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            continue
        norm = chunk.get("bboxNorm") if isinstance(chunk.get("bboxNorm"), dict) else {}
        px = chunk.get("bboxPx") if isinstance(chunk.get("bboxPx"), dict) else {}
        try:
            y1 = float(norm.get("y1"))
            y2 = float(norm.get("y2"))
        except (TypeError, ValueError):
            continue
        if y2 <= y1:
            continue
        ranges.append(
            {
                "chunk": chunk,
                "idx": idx,
                "y1": y1,
                "y2": y2,
                "y1Px": px.get("y1"),
                "y2Px": px.get("y2"),
            }
        )
    ranges.sort(key=lambda item: (float(item["y1"]), float(item["y2"])))
    groups: List[Dict[str, Any]] = []
    for item in ranges:
        last = groups[-1] if groups else None
        if not last or float(item["y1"]) > float(last["y2"]):
            groups.append({"items": [item], "y1": float(item["y1"]), "y2": float(item["y2"])})
            continue
        last["items"].append(item)
        last["y1"] = min(float(last["y1"]), float(item["y1"]))
        last["y2"] = max(float(last["y2"]), float(item["y2"]))

    bands: List[Dict[str, Any]] = []
    for idx, group in enumerate(groups):
        items = group["items"]
        y1_px_list = [int(value) for value in (it.get("y1Px") for it in items) if isinstance(value, (int, float))]
        y2_px_list = [int(value) for value in (it.get("y2Px") for it in items) if isinstance(value, (int, float))]
        labels = sorted({str(it["chunk"].get("label") or "text") for it in items})
        bands.append(
            {
                "chunkKey": f"p{page_no:04d}_band_{idx:03d}",
                "chunkId": f"p{page_no:04d}_band_{idx:03d}",
                "pageNo": page_no,
                "index": idx,
                "label": "band",
                "bboxNorm": {
                    "x1": 0,
                    "y1": round(float(group["y1"]), 6),
                    "x2": 1,
                    "y2": round(float(group["y2"]), 6),
                },
                "bboxPx": {
                    "x1": 0,
                    "y1": min(y1_px_list) if y1_px_list else None,
                    "x2": page_width or None,
                    "y2": max(y2_px_list) if y2_px_list else None,
                },
                "content": "\n\n".join(
                    str(it["chunk"].get("content") or "").strip()
                    for it in items
                    if str(it["chunk"].get("content") or "").strip()
                ),
                "sourceLabels": labels,
                "sourceChunkCount": len(items),
            }
        )
    return bands


def _flatten_doc_bands(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages = doc.get("ocrBlocksByPage") if isinstance(doc.get("ocrBlocksByPage"), list) else []
    bands: List[Dict[str, Any]] = []
    for page in pages:
        if isinstance(page, dict):
            bands.extend(_build_page_bands(page))
    bands.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
    return bands


def expand_selected_with_neighbors(
    doc: Dict[str, Any], selected_items: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    all_bands = _flatten_doc_bands(doc)
    if not all_bands:
        selected: List[Dict[str, Any]] = []
        for item in selected_items:
            normalized = _normalize_selected_item(item)
            if normalized:
                selected.append(normalized)
        return selected, []
    key_to_pos = {chunk_key(item): idx for idx, item in enumerate(all_bands)}
    selected_map: Dict[str, Dict[str, Any]] = {}
    positions: List[int] = []
    for item in selected_items:
        normalized = _normalize_selected_item(item)
        if not normalized:
            continue
        key = chunk_key(normalized)
        selected_map[key] = normalized
        pos = key_to_pos.get(key)
        if pos is not None:
            positions.append(pos)
    if not selected_map:
        return [], []
    positions = sorted(set(positions))
    neighbor_keys: Set[str] = set()
    if positions:
        run_start = positions[0]
        run_prev = positions[0]
        for pos in positions[1:] + [None]:
            if pos is not None and pos == run_prev + 1:
                run_prev = pos
                continue
            if run_start - 1 >= 0:
                neighbor_keys.add(chunk_key(all_bands[run_start - 1]))
            if run_prev + 1 < len(all_bands):
                neighbor_keys.add(chunk_key(all_bands[run_prev + 1]))
            if pos is None:
                break
            run_start = pos
            run_prev = pos
    neighbors = [
        band for band in all_bands if chunk_key(band) in neighbor_keys and chunk_key(band) not in selected_map
    ]
    selected = [selected_map[key] for key in sorted(selected_map, key=lambda value: key_to_pos.get(value, 10**9))]
    return selected, neighbors


def session_context_summary(compaction: Optional[Dict[str, Any]]) -> str:
    if not isinstance(compaction, dict):
        return ""
    summary = str(compaction.get("summary") or "").strip()
    if not summary:
        return ""
    parts = [f"摘要: {summary}"]
    recent_focus = compaction.get("recentFocus")
    if isinstance(recent_focus, list):
        focus_text = " | ".join(str(item).strip() for item in recent_focus if str(item).strip())
        if focus_text:
            parts.append(f"近期重点: {focus_text}")
    open_questions = compaction.get("openQuestions")
    if isinstance(open_questions, list):
        question_text = " | ".join(str(item).strip() for item in open_questions if str(item).strip())
        if question_text:
            parts.append(f"未解决问题: {question_text}")
    return "\n".join(parts)


def format_overview_for_prompt(overview: Optional[Dict[str, Any]]) -> str:
    if not isinstance(overview, dict):
        return ""
    parts: List[str] = []
    title = str(overview.get("title") or "").strip()
    if title:
        parts.append(f"title: {title}")
    doc_type = str(overview.get("docTypeGuess") or "").strip()
    if doc_type:
        parts.append(f"doc_type: {doc_type}")
    short = str(overview.get("overviewShort") or "").strip()
    if short:
        parts.append(f"overview_short: {short}")
    long_text = str(overview.get("overviewLong") or "").strip()
    if long_text:
        parts.append(f"overview_long: {long_text}")
    keywords = overview.get("keywords")
    if isinstance(keywords, list):
        joined = ", ".join(str(item).strip() for item in keywords if str(item).strip())
        if joined:
            parts.append(f"keywords: {joined}")
    topics = overview.get("topics")
    if isinstance(topics, list):
        joined = ", ".join(str(item).strip() for item in topics if str(item).strip())
        if joined:
            parts.append(f"topics: {joined}")
    quality = overview.get("qualityContext")
    if isinstance(quality, dict):
        parts.append(
            "quality_context: "
            f"avgFinalScore={float(quality.get('avgFinalScore') or 0.0):.3f}, "
            f"avgLayoutScore={float(quality.get('avgLayoutScore') or 0.0):.3f}, "
            f"pagesWithIssues={int(quality.get('pagesWithIssues') or 0)}, "
            f"pagesWithLayoutIssues={int(quality.get('pagesWithLayoutIssues') or 0)}"
        )
    if not parts:
        return ""
    return "document_overview:\n" + "\n".join(parts)


def _format_chunks_for_prompt(items: List[Dict[str, Any]], heading: str) -> str:
    if not items:
        return f"{heading}\n(empty)\n"
    lines = [heading]
    for item in items:
        cid = chunk_key(item)
        page_no = item.get("pageNo")
        label = str(item.get("label") or "chunk")
        content = str(item.get("content") or "").strip() or "(empty chunk)"
        lines.append(f"[{cid}] page={page_no} label={label}\n{content}")
    return "\n\n".join(lines) + "\n"


def ask_deepseek_with_selection_v2(
    root: Path,
    current_items: List[Dict[str, Any]],
    support_items: List[Dict[str, Any]],
    question: str,
    doc_name: str,
    *,
    doc_id: str = "",
    doc_overview: Optional[Dict[str, Any]] = None,
    compacted_context: str = "",
    recent_turns: Optional[List[Dict[str, Any]]] = None,
    manual_selected: bool = False,
    context_source: str = "",
) -> Dict[str, Any]:
    allowed_ids: List[str] = []
    for group in (current_items, support_items):
        for item in group:
            cid = chunk_key(item)
            if cid and cid not in allowed_ids:
                allowed_ids.append(cid)
    history_lines: List[str] = []
    for turn in recent_turns or []:
        role = str(turn.get("role") or "").strip()
        text = str(turn.get("text") or "").strip()
        if role and text:
            history_lines.append(f"{role}: {text}")

    if manual_selected:
        system_prompt = (
            "You are a document QA assistant for Chinese PDFs. Follow these rules strictly: "
            "1) Answer primarily from provided chunks and document_overview/context; use concise reasoning when needed, but do not invent facts. "
            "2) ranked_chunks are the primary evidence; extra_chunks are secondary evidence. "
            "3) If evidence is partially insufficient, first answer what can be supported, then explicitly state the missing part with '文档中未明确说明'. "
            "4) If evidence is largely insufficient, say '文档中未找到足够依据' and briefly explain what is missing. "
            "5) Only cite chunk ids that were provided. "
            "6) Return exactly one JSON object with keys: cited_chunk_ids, answer, follow_up_questions. "
            "7) answer should be concise, factual, and in Chinese unless the document itself is clearly English."
        )
    else:
        system_prompt = (
            "You are a document QA assistant for Chinese PDFs. Follow these rules strictly: "
            "1) Answer primarily from provided chunks and document_overview/context; use concise reasoning when needed, but do not invent facts. "
            "2) ranked_chunks are the primary evidence; extra_chunks are supporting evidence. "
            "3) If evidence is partially insufficient, first answer what can be supported, then explicitly state the missing part with '文档中未明确说明'. "
            "4) If evidence is largely insufficient, say '文档中未找到足够依据' and briefly explain what is missing. "
            "5) Only cite chunk ids that were provided. "
            "6) Return exactly one JSON object with keys: cited_chunk_ids, answer, follow_up_questions. "
            "7) answer should be concise, factual, and in Chinese unless the document itself is clearly English."
        )
    prompt_parts = [
        f"Document: {doc_name}",
        f"Question: {question}",
        "Response requirements: return JSON only; answer should prefer supported facts first, then mention any missing detail explicitly; do not add extra explanation outside JSON.",
        "If the answer is a list/process, preserve the document's structure and keep the wording close to the source.",
    ]
    if context_source:
        prompt_parts.append(f"Context source: {context_source}")
    if current_items:
        prompt_parts.append(_format_chunks_for_prompt(current_items, "ranked_chunks"))
    if support_items:
        prompt_parts.append(_format_chunks_for_prompt(support_items, "extra_chunks"))
    if compacted_context.strip():
        prompt_parts.append("Conversation context:\n" + compacted_context.strip())
    if history_lines:
        prompt_parts.append("Recent turns:\n" + "\n".join(history_lines[-8:]))
    overview_text = format_overview_for_prompt(doc_overview)
    if overview_text:
        prompt_parts.append(overview_text)
    prompt_parts.append("Return JSON only.")
    payload = deepseek_chat_json(root, system_prompt, "\n\n".join(prompt_parts), temperature=0.2)
    try:
        return normalize_qa_response(payload, allowed_ids)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"DeepSeek response parse failed: {exc!s}") from exc


def compact_session_with_deepseek(
    root: Path,
    transcript_parts: Sequence[str],
    *,
    raw_char_count: int,
    turn_count: int,
) -> Dict[str, Any]:
    system_prompt = (
        "你是对话压缩助手。请压缩长对话，保留最近问题的优先级更高。"
        "输出 JSON，字段必须包含 summary, userGoal, keyPoints, recentFocus, openQuestions。"
        "summary 要可直接作为后续问答上下文。recentFocus 和 openQuestions 控制在 3 条以内。"
    )
    payload = deepseek_chat_json(root, system_prompt, "\n".join(transcript_parts[-40:]), temperature=0.1)
    return {
        "summary": str(payload.get("summary") or "").strip(),
        "userGoal": str(payload.get("userGoal") or "").strip(),
        "keyPoints": payload.get("keyPoints") if isinstance(payload.get("keyPoints"), list) else [],
        "recentFocus": payload.get("recentFocus") if isinstance(payload.get("recentFocus"), list) else [],
        "openQuestions": payload.get("openQuestions") if isinstance(payload.get("openQuestions"), list) else [],
        "sourceTurnCount": int(turn_count),
        "rawCharCount": int(raw_char_count),
    }
