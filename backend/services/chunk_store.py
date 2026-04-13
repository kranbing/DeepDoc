from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from backend.services.project_store import document_dir, read_json, utc_now, write_json


def document_chunks_path(project_dir, doc_id: str):
    return document_dir(project_dir, doc_id) / "chunks.json"


def normalize_chunk_content(text: Any) -> str:
    value = str(text or "")
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _normalize_chunk(chunk: Dict[str, Any], *, doc_id: str, doc_name: str) -> Optional[Dict[str, Any]]:
    chunk_id = str(chunk.get("chunkId") or chunk.get("chunkKey") or "").strip()
    if not chunk_id:
        return None
    page_no = int(chunk.get("pageNo") or 0)
    index = int(chunk.get("index") or 0)
    content = str(chunk.get("content") or "").strip()
    normalized = normalize_chunk_content(content)
    bbox_norm = chunk.get("bboxNorm") if isinstance(chunk.get("bboxNorm"), dict) else {}
    bbox_px = chunk.get("bboxPx") if isinstance(chunk.get("bboxPx"), dict) else {}
    label = str(chunk.get("label") or "text").strip() or "text"
    return {
        "chunkId": chunk_id,
        "chunkKey": chunk_id,
        "docId": doc_id,
        "docName": doc_name,
        "pageNo": page_no,
        "index": index,
        "label": label,
        "content": content,
        "normalizedContent": normalized,
        "charCount": len(normalized),
        "bboxNorm": bbox_norm,
        "bboxPx": bbox_px,
    }


def build_doc_chunks_payload(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("id") or "").strip()
    doc_name = str(doc.get("name") or doc_id).strip() or doc_id
    pages = doc.get("ocrBlocksByPage") if isinstance(doc.get("ocrBlocksByPage"), list) else []
    page_entries: List[Dict[str, Any]] = []
    flat_chunks: List[Dict[str, Any]] = []

    for page in pages:
        if not isinstance(page, dict):
            continue
        page_no = int(page.get("pageNo") or len(page_entries) + 1)
        raw_chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
        normalized_chunks: List[Dict[str, Any]] = []
        for raw in raw_chunks:
            if not isinstance(raw, dict):
                continue
            chunk = _normalize_chunk(raw, doc_id=doc_id, doc_name=doc_name)
            if not chunk:
                continue
            normalized_chunks.append(chunk)
        normalized_chunks.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
        for idx, item in enumerate(normalized_chunks):
            item["prevChunkId"] = normalized_chunks[idx - 1]["chunkId"] if idx > 0 else None
            item["nextChunkId"] = normalized_chunks[idx + 1]["chunkId"] if idx + 1 < len(normalized_chunks) else None
        page_entry = {
            "pageNo": page_no,
            "chunkCount": len(normalized_chunks),
            "imageSize": page.get("imageSize") if isinstance(page.get("imageSize"), dict) else {},
            "chunks": normalized_chunks,
        }
        page_entries.append(page_entry)
        flat_chunks.extend(normalized_chunks)

    flat_chunks.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
    return {
        "status": "ready",
        "docId": doc_id,
        "docName": doc_name,
        "pageCount": len(page_entries),
        "totalChunks": len(flat_chunks),
        "generatedAt": utc_now(),
        "pages": page_entries,
    }


def read_document_chunks(project_dir, doc_id: str) -> Optional[Dict[str, Any]]:
    data = read_json(document_chunks_path(project_dir, doc_id), None)
    return data if isinstance(data, dict) else None


def write_document_chunks(project_dir, doc_id: str, payload: Dict[str, Any]) -> None:
    write_json(document_chunks_path(project_dir, doc_id), payload)


def save_document_chunks(project_dir, doc: Dict[str, Any]) -> Dict[str, Any]:
    payload = build_doc_chunks_payload(doc)
    write_document_chunks(project_dir, str(doc.get("id") or ""), payload)
    return payload


def flatten_document_chunks(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else []
    out: List[Dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
        out.extend(chunk for chunk in chunks if isinstance(chunk, dict))
    out.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
    return out


def chunk_page_summary(payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else []
    out: List[Dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        out.append(
            {
                "pageNo": int(page.get("pageNo") or 0),
                "chunkCount": int(page.get("chunkCount") or 0),
            }
        )
    out.sort(key=lambda item: item["pageNo"])
    return out


def get_page_chunks(payload: Optional[Dict[str, Any]], page_no: int) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else []
    for page in pages:
        if isinstance(page, dict) and int(page.get("pageNo") or 0) == int(page_no):
            chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
            return [chunk for chunk in chunks if isinstance(chunk, dict)]
    return []


def get_chunk_detail(payload: Optional[Dict[str, Any]], chunk_id: str) -> Optional[Tuple[Dict[str, Any], List[Dict[str, Any]]]]:
    target = str(chunk_id or "").strip()
    if not target:
        return None
    chunks = flatten_document_chunks(payload)
    for idx, chunk in enumerate(chunks):
        if str(chunk.get("chunkId") or "") != target:
            continue
        return chunk, chunks
    return None


def get_neighbor_chunks(payload: Optional[Dict[str, Any]], chunk_id: str, radius: int = 1) -> Dict[str, Any]:
    radius = max(1, min(int(radius or 1), 5))
    detail = get_chunk_detail(payload, chunk_id)
    if not detail:
        return {"current": None, "previous": [], "next": [], "combined": []}
    current, chunks = detail
    page_no = int(current.get("pageNo") or 0)
    same_page = [chunk for chunk in chunks if int(chunk.get("pageNo") or 0) == page_no]
    pos = next((idx for idx, chunk in enumerate(same_page) if str(chunk.get("chunkId") or "") == chunk_id), -1)
    if pos < 0:
        return {"current": current, "previous": [], "next": [], "combined": [current]}
    previous = same_page[max(0, pos - radius) : pos]
    nxt = same_page[pos + 1 : pos + 1 + radius]
    combined = previous + [current] + nxt
    return {
        "current": current,
        "previous": previous,
        "next": nxt,
        "combined": combined,
    }
