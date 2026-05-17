from __future__ import annotations

import re
from typing import Any, Dict, List, Set


REQUIRED_STRUCTURED_KEYS = {
    "answer",
    "cited_chunk_ids",
    "claim_evidence_map",
    "insufficient_evidence",
    "follow_up_questions",
}


def extract_tokens(text: str) -> Set[str]:
    raw = str(text or "").lower()
    tokens = re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?|[\u4e00-\u9fff]{2,}", raw)
    stop_words = {
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "a",
        "an",
        "is",
        "are",
        "with",
        "for",
        "on",
        "by",
        "as",
        "that",
        "this",
        "they",
        "their",
        "paper",
    }
    return {token for token in tokens if token not in stop_words and len(token) > 1}


def normalize_cited_ids(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        cid = str(item or "").strip()
        if cid and cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


def flatten_chunk_context(chunk_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    groups = [
        chunk_context.get("currentChunks"),
        chunk_context.get("neighborChunks"),
        chunk_context.get("retrievalChunks"),
        chunk_context.get("chunks"),
    ]
    for group in groups:
        if not isinstance(group, list):
            continue
        for item in group:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("chunkId") or item.get("chunkKey") or "").strip()
            if not cid or cid in out:
                continue
            out[cid] = item
    return out


def validate_structured_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "valid": False,
            "missing_keys": sorted(REQUIRED_STRUCTURED_KEYS),
            "type_errors": ["payload is not an object"],
        }
    missing = sorted(key for key in REQUIRED_STRUCTURED_KEYS if key not in payload)
    type_errors: List[str] = []
    if "answer" in payload and not isinstance(payload.get("answer"), str):
        type_errors.append("answer must be string")
    if "cited_chunk_ids" in payload and not isinstance(payload.get("cited_chunk_ids"), list):
        type_errors.append("cited_chunk_ids must be list")
    if "claim_evidence_map" in payload and not isinstance(payload.get("claim_evidence_map"), dict):
        type_errors.append("claim_evidence_map must be object")
    if "insufficient_evidence" in payload and not isinstance(payload.get("insufficient_evidence"), bool):
        type_errors.append("insufficient_evidence must be boolean")
    if "follow_up_questions" in payload and not isinstance(payload.get("follow_up_questions"), list):
        type_errors.append("follow_up_questions must be list")
    return {
        "valid": not missing and not type_errors,
        "missing_keys": missing,
        "type_errors": type_errors,
    }


def chunk_location(chunk: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "chunk_id": str(chunk.get("chunkId") or chunk.get("chunkKey") or ""),
        "page_no": chunk.get("pageNo"),
        "index": chunk.get("index"),
        "bbox_px": chunk.get("bboxPx") if isinstance(chunk.get("bboxPx"), dict) else {},
        "bbox_norm": chunk.get("bboxNorm") if isinstance(chunk.get("bboxNorm"), dict) else {},
        "section_id": str(chunk.get("sectionId") or ""),
        "section_path": str(chunk.get("sectionPathText") or ""),
        "heading": str(chunk.get("headingText") or ""),
        "content_preview": str(chunk.get("content") or chunk.get("normalizedContent") or "")[:240],
    }


def support_score(claim: str, chunks: List[Dict[str, Any]]) -> float:
    claim_tokens = extract_tokens(claim)
    if not claim_tokens or not chunks:
        return 0.0
    evidence_tokens: Set[str] = set()
    for chunk in chunks:
        evidence_tokens |= extract_tokens(str(chunk.get("content") or chunk.get("normalizedContent") or ""))
    return round(len(claim_tokens & evidence_tokens) / max(len(claim_tokens), 1), 4)


def support_level(score: float) -> str:
    if score >= 0.65:
        return "strong"
    if score >= 0.35:
        return "partial"
    if score > 0:
        return "weak"
    return "none"


def default_claim_map(payload: Dict[str, Any]) -> Dict[str, List[str]]:
    claim_map = payload.get("claim_evidence_map")
    if isinstance(claim_map, dict) and claim_map:
        out: Dict[str, List[str]] = {}
        for claim, ids in claim_map.items():
            out[str(claim)] = normalize_cited_ids(ids)
        return out
    answer = str(payload.get("answer") or "").strip()
    return {answer: normalize_cited_ids(payload.get("cited_chunk_ids"))} if answer else {}


def build_evidence_trace(answer_payload: Dict[str, Any], chunk_context: Dict[str, Any]) -> Dict[str, Any]:
    validation = validate_structured_payload(answer_payload)
    chunk_map = flatten_chunk_context(chunk_context)
    cited_ids = normalize_cited_ids(answer_payload.get("cited_chunk_ids"))
    resolved = []
    missing = []
    for cid in cited_ids:
        chunk = chunk_map.get(cid)
        if chunk:
            resolved.append({**chunk_location(chunk), "exists": True})
        else:
            missing.append(cid)

    claim_traces = []
    for claim, ids in default_claim_map(answer_payload).items():
        existing_chunks = [chunk_map[cid] for cid in ids if cid in chunk_map]
        score = support_score(claim, existing_chunks)
        claim_traces.append(
            {
                "claim": claim,
                "chunk_ids": ids,
                "existing_chunk_ids": [cid for cid in ids if cid in chunk_map],
                "missing_chunk_ids": [cid for cid in ids if cid not in chunk_map],
                "support_score": score,
                "support_level": support_level(score),
            }
        )

    citation_total = len(cited_ids)
    citation_exist_rate = len(resolved) / citation_total if citation_total else 0.0
    trace_complete_count = sum(
        1
        for item in resolved
        if item.get("page_no") is not None
        or item.get("bbox_px")
        or item.get("bbox_norm")
        or item.get("section_path")
    )
    trace_complete_rate = trace_complete_count / len(resolved) if resolved else 0.0
    claim_supported = [item for item in claim_traces if item["support_score"] > 0]
    claim_supported_rate = len(claim_supported) / len(claim_traces) if claim_traces else 0.0

    return {
        "structured_validation": validation,
        "cited_chunk_ids": cited_ids,
        "resolved_citations": resolved,
        "missing_chunk_ids": missing,
        "claim_traces": claim_traces,
        "consistency": {
            "citation_exist_rate": round(citation_exist_rate, 4),
            "trace_complete_rate": round(trace_complete_rate, 4),
            "claim_supported_rate": round(claim_supported_rate, 4),
            "invalid_citation_count": len(missing),
            "missing_citation": bool(str(answer_payload.get("answer") or "").strip() and not cited_ids),
            "avg_support_score": round(
                sum(float(item["support_score"]) for item in claim_traces) / max(len(claim_traces), 1),
                4,
            ),
        },
    }
