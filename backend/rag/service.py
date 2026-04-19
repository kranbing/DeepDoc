from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.logging_config import logger
from backend.services.overview_service import ensure_document_overview, read_document_overview
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
        search_res = search_project_vector_index(project_dir, question, top_k=top_k, doc_id=doc_id)
        retrieved = normalize_chunk_context_items(search_res.get("results"))
        max_current = max(1, min(3, len(retrieved))) if retrieved else 0
        current_chunks = retrieved[:max_current]
        support_chunks: List[Dict[str, Any]] = retrieved[max_current:]
        overview = read_document_overview(project_dir, doc_id)
        if not isinstance(overview, dict) or str(overview.get("status") or "") != "ready":
            overview = ensure_document_overview(root, project_dir, doc)
        logger.info(
            "rag_context done | doc_id=%s | hits=%s | elapsed_ms=%s",
            doc_id,
            len(current_chunks),
            _elapsed_ms(start),
        )
        return current_chunks, support_chunks, overview, "auto_retrieval"
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
