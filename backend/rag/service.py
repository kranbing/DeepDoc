from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.logging_config import logger
from backend.services.overview_service import ensure_document_overview, read_document_overview
from backend.services.chunk_store import get_neighbor_chunks
from backend.services.lad_store import expand_lad_related_chunks, read_preferred_lad_chunks
from backend.services.qa_service import (
    ask_deepseek_with_selection_v2,
    dedupe_chunk_items,
    expand_selected_with_neighbors,
    normalize_chunk_context_items,
    serialize_chunk_context_payload,
)
from backend.services.vector_store import search_project_vector_index
from backend.rag.config import RAG_TOP_K


def _elapsed_ms(start: datetime) -> int:
    return int((datetime.now(timezone.utc) - start).total_seconds() * 1000)


def _is_complex_question(question: str) -> bool:
    q = str(question or "")
    markers = (
        "哪些",
        "什么",
        "如何",
        "流程",
        "步骤",
        "模块",
        "功能",
        "维度",
        "关键",
        "创新",
        "区别",
        "为什么",
        "怎么",
    )
    return any(m in q for m in markers)


def _adaptive_top_k(question: str, requested_top_k: int) -> int:
    base = max(1, int(requested_top_k or RAG_TOP_K))
    if _is_complex_question(question):
        return min(20, max(base, 6))
    return min(20, max(base, 3))


def _merge_retrieval_results(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for group in groups:
        for item in group:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("chunkId") or item.get("chunkKey") or "").strip()
            if not cid:
                continue
            prev = merged.get(cid)
            if not prev:
                merged[cid] = item
                continue
            prev_score = float(prev.get("score") or 0.0)
            now_score = float(item.get("score") or 0.0)
            if now_score > prev_score:
                merged[cid] = item
    return sorted(
        merged.values(),
        key=lambda item: (
            -float(item.get("score") or 0.0),
            int(item.get("pageNo") or 0),
            int(item.get("index") or 0),
        ),
    )


def _expand_neighbors_from_sources(
    project_dir: Path,
    doc_id: str,
    seed_chunks: List[Dict[str, Any]],
    *,
    max_neighbors: int = 6,
) -> List[Dict[str, Any]]:
    payload = read_preferred_lad_chunks(project_dir, doc_id)
    if not isinstance(payload, dict):
        return []
    lad_related = expand_lad_related_chunks(payload, seed_chunks, max_items=max_neighbors)
    if lad_related:
        return normalize_chunk_context_items(lad_related[:max_neighbors])
    source_ids: List[str] = []
    for chunk in seed_chunks:
        source_chunk_ids = chunk.get("sourceChunkIds") if isinstance(chunk.get("sourceChunkIds"), list) else []
        if source_chunk_ids:
            source_ids.extend(str(cid).strip() for cid in source_chunk_ids if str(cid).strip())
            continue
        cid = str(chunk.get("chunkId") or chunk.get("chunkKey") or "").strip()
        if cid:
            source_ids.append(cid)
    seen: set[str] = set()
    neighbors: List[Dict[str, Any]] = []
    for src in source_ids:
        if src in seen:
            continue
        seen.add(src)
        item = get_neighbor_chunks(payload, src, radius=1)
        for side in ("previous", "next"):
            group = item.get(side) if isinstance(item, dict) else []
            if not isinstance(group, list):
                continue
            for chunk in group:
                if not isinstance(chunk, dict):
                    continue
                cid = str(chunk.get("chunkId") or chunk.get("chunkKey") or "").strip()
                if not cid or cid in seen:
                    continue
                seen.add(cid)
                neighbors.append(chunk)
                if len(neighbors) >= max_neighbors:
                    return normalize_chunk_context_items(neighbors)
    return normalize_chunk_context_items(neighbors)


def build_rag_context(
    root: Path,
    project_dir: Path,
    doc: Dict[str, Any],
    question: str,
    *,
    top_k: int = RAG_TOP_K,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], str]:
    start = datetime.now(timezone.utc)
    doc_id = str(doc.get("id") or "")
    logger.info(
        "rag_context start | doc_id=%s | top_k=%s | question=%s",
        doc_id,
        top_k,
        question,
    )
    try:
        adaptive_k = _adaptive_top_k(question, top_k)
        search_res = search_project_vector_index(project_dir, question, top_k=adaptive_k, doc_id=doc_id)
        retrieved = normalize_chunk_context_items(search_res.get("results"))

        # Retry with wider top-k when first-pass retrieval is weak.
        retry_k = min(20, adaptive_k + 4)
        top_score = float((retrieved[0].get("score") if retrieved else 0.0) or 0.0)
        if retry_k > adaptive_k and top_score < 0.2:
            retry_res = search_project_vector_index(project_dir, question, top_k=retry_k, doc_id=doc_id)
            retry_chunks = normalize_chunk_context_items(retry_res.get("results"))
            retrieved = _merge_retrieval_results(retrieved, retry_chunks)

        is_complex = _is_complex_question(question)
        max_current = max(1, min(4 if is_complex else 3, len(retrieved))) if retrieved else 0
        current_chunks = retrieved[:max_current]
        support_chunks: List[Dict[str, Any]] = retrieved[max_current: max_current + (6 if is_complex else 4)]

        neighbor_chunks = _expand_neighbors_from_sources(
            project_dir,
            doc_id,
            current_chunks[:2],
            max_neighbors=6 if is_complex else 4,
        )
        support_chunks = dedupe_chunk_items(support_chunks, neighbor_chunks)
        overview = read_document_overview(project_dir, doc_id)
        if not isinstance(overview, dict) or str(overview.get("status") or "") != "ready":
            overview = ensure_document_overview(root, project_dir, doc)
        logger.info(
            "rag_context done | doc_id=%s | hits=%s | support=%s | top_k=%s | elapsed_ms=%s",
            doc_id,
            len(current_chunks),
            len(support_chunks),
            adaptive_k,
            _elapsed_ms(start),
        )
        return current_chunks, support_chunks, overview, "auto_retrieval_hybrid"
    except HTTPException:
        logger.exception("rag_context failed | doc_id=%s", doc_id)
        raise


def ask_rag_with_selection(
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
    start = datetime.now(timezone.utc)
    logger.info(
        "rag_ask start | doc_id=%s | manual_selected=%s | question=%s",
        doc_id,
        manual_selected,
        question,
    )
    result = ask_deepseek_with_selection_v2(
        root,
        current_items,
        support_items,
        question,
        doc_name,
        doc_id=doc_id,
        doc_overview=doc_overview,
        compacted_context=compacted_context,
        recent_turns=recent_turns,
        manual_selected=manual_selected,
        context_source=context_source,
    )
    result["chunk_context"] = serialize_chunk_context_payload(
        source=context_source or "auto_retrieval",
        current_chunks=current_items,
        neighbor_chunks=support_items,
        retrieval_chunks=[],
    )
    logger.info(
        "rag_ask done | doc_id=%s | cited=%s | elapsed_ms=%s",
        doc_id,
        len(result.get("cited_chunk_ids") or []),
        _elapsed_ms(start),
    )
    return result
