from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.logging_config import logger
from backend.services.lad_store import expand_lad_related_chunks, read_preferred_lad_chunks
from backend.services.overview_service import ensure_document_overview, read_document_overview
from backend.services.qa_service import dedupe_chunk_items, normalize_chunk_context_items
from backend.services.vector_store import search_project_vector_index

LAD_HYBRID_TOP_K = 30
LAD_SEED_COUNT = 8
LAD_TOTAL_CHUNKS = 15


def _elapsed_ms(start: datetime) -> int:
    return int((datetime.now(timezone.utc) - start).total_seconds() * 1000)


def build_lad_context(
    root: Path,
    project_dir: Path,
    doc: Dict[str, Any],
    question: str,
    *,
    top_k: int = LAD_HYBRID_TOP_K,
    seed_count: int = LAD_SEED_COUNT,
    total_chunks: int = LAD_TOTAL_CHUNKS,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], str]:
    """Three-stage LAD-RAG pipeline.

    Stage 1: Hybrid retrieval (FAISS + BM25) -> top-30 candidates
    Stage 2: Seed selection (top-8 by score; extension point for cross-encoder rerank)
    3: LAD section_first expansion -> final context (15 chunks)
    """
    start = datetime.now(timezone.utc)
    doc_id = str(doc.get("id") or "")
    logger.info(
        "lad_context start | doc_id=%s | top_k=%s | seed_count=%s | total=%s | question=%s",
        doc_id, top_k, seed_count, total_chunks, question,
    )

    # Stage 1: Hybrid retrieval
    try:
        search_res = search_project_vector_index(project_dir, question, top_k=top_k, doc_id=doc_id)
    except HTTPException:
        logger.warning("lad_context vector search failed, falling back | doc_id=%s", doc_id)
        return [], [], {}, "lad_fallback"
    candidates = normalize_chunk_context_items(search_res.get("results"))

    # Retry with wider k when retrieval is weak
    top_score = float((candidates[0].get("score") if candidates else 0.0) or 0.0)
    if top_score < 0.2:
        retry_k = min(40, top_k + 10)
        try:
            retry_res = search_project_vector_index(project_dir, question, top_k=retry_k, doc_id=doc_id)
            retry_chunks = normalize_chunk_context_items(retry_res.get("results"))
            seen_ids: set[str] = set()
            merged: List[Dict[str, Any]] = []
            for item in candidates + retry_chunks:
                cid = str(item.get("chunkId") or item.get("chunkKey") or "").strip()
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    merged.append(item)
            candidates = sorted(merged, key=lambda x: -float(x.get("score") or 0))
        except HTTPException:
            pass

    # Stage 2: Seed selection (top-N by hybrid score)
    seeds = candidates[:seed_count]

    # Stage 3: LAD section_first expansion
    payload = read_preferred_lad_chunks(project_dir, doc_id)
    expand_budget = max(0, total_chunks - len(seeds))
    expanded: List[Dict[str, Any]] = []
    if isinstance(payload, dict) and expand_budget > 0:
        expanded = expand_lad_related_chunks(
            payload, seeds, max_items=expand_budget, strategy="section_first",
        )

    current_chunks = list(seeds)
    support_chunks = dedupe_chunk_items(expanded, candidates[seed_count:seed_count + 4])

    # Trim to total budget
    total_unique = len(current_chunks) + len(support_chunks)
    if total_unique > total_chunks:
        support_chunks = support_chunks[: total_chunks - len(current_chunks)]

    # Load document overview
    overview = read_document_overview(project_dir, doc_id)
    if not isinstance(overview, dict) or str(overview.get("status") or "") != "ready":
        try:
            overview = ensure_document_overview(root, project_dir, doc)
        except Exception:
            overview = {}

    logger.info(
        "lad_context done | doc_id=%s | seeds=%s | expanded=%s | support=%s | elapsed_ms=%s",
        doc_id, len(seeds), len(expanded), len(support_chunks), _elapsed_ms(start),
    )
    return current_chunks, support_chunks, overview, "lad_rag_section_first"
