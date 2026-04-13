from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib import error as urlerror
from urllib import request as urlrequest

from backend.services.project_store import (
    read_document_overview,
    read_documents_index,
    utc_now,
    write_document_overview,
    write_documents_index,
)
from backend.services.runtime_logger import log_event


def _deepseek_api_key(root: Path) -> Optional[str]:
    key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if key:
        return key
    local = root / "backend" / ".deepseek_api_key"
    if local.is_file():
        try:
            txt = local.read_text(encoding="utf-8").strip()
            return txt or None
        except OSError:
            return None
    return None


def _extract_json_object(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty response")
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(text[start : end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("no valid json object found")


def _deepseek_chat_json(root: Path, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    api_key = _deepseek_api_key(root)
    if not api_key:
        raise RuntimeError("missing DEEPSEEK_API_KEY")
    body = {
        "model": "deepseek-chat",
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urlrequest.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=120) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urlerror.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"DeepSeek API error: {detail[:400]}") from e
    except Exception as e:
        raise RuntimeError(f"DeepSeek request failed: {e!s}") from e
    return _extract_json_object(str(raw["choices"][0]["message"]["content"]))


def _clean_text(text: str) -> str:
    return " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split()).strip()


def _label_rank(label: str) -> int:
    label = str(label or "").lower()
    if any(token in label for token in ("title", "heading", "header")):
        return 0
    if any(token in label for token in ("section", "subtitle")):
        return 1
    return 2


def collect_overview_samples(doc: Dict[str, Any], *, max_pages: int = 3, max_chunks: int = 24) -> Tuple[List[Dict[str, Any]], List[str]]:
    pages = doc.get("ocrBlocksByPage") if isinstance(doc.get("ocrBlocksByPage"), list) else []
    selected: List[Dict[str, Any]] = []
    seen_ids = set()
    title_candidates: List[str] = []
    for page in pages[:max_pages]:
        if not isinstance(page, dict):
            continue
        page_no = int(page.get("pageNo") or 0)
        chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
        ranked = [
            chunk
            for chunk in chunks
            if isinstance(chunk, dict) and _clean_text(chunk.get("content") or "")
        ]
        ranked.sort(
            key=lambda chunk: (
                _label_rank(chunk.get("label") or ""),
                int(chunk.get("index") or 0),
            )
        )
        page_limit = 8 if page_no == 1 else 4
        for chunk in ranked[:page_limit]:
            chunk_id = str(chunk.get("chunkId") or "").strip()
            if not chunk_id or chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)
            selected.append(chunk)
            text = _clean_text(chunk.get("content") or "")
            if len(text) <= 80 and text not in title_candidates:
                title_candidates.append(text)
            if len(selected) >= max_chunks:
                return selected, title_candidates[:5]
    return selected, title_candidates[:5]


def default_overview_payload(doc: Dict[str, Any], quality_report: Optional[Dict[str, Any]], samples: List[Dict[str, Any]], title_candidates: List[str]) -> Dict[str, Any]:
    sample_ids = [str(chunk.get("chunkId") or "") for chunk in samples if str(chunk.get("chunkId") or "").strip()]
    sample_pages = sorted({int(chunk.get("pageNo") or 0) for chunk in samples if int(chunk.get("pageNo") or 0) > 0})
    quality_report = quality_report if isinstance(quality_report, dict) else {}
    return {
        "_comment": "Single-document overview used for document understanding and future multi-document RAG.",
        "docId": doc.get("id"),
        "docName": doc.get("name"),
        "generatedAt": utc_now(),
        "status": "ready",
        "samplingStrategy": {
            "_comment": "Current strategy: title-first and front-pages-first.",
            "titleFirst": True,
            "frontPagesFirst": True,
            "maxPages": 3,
            "maxChunks": 24,
        },
        "source": {
            "_comment": "Traceability back to OCR chunks used to build the overview.",
            "sourceChunkIds": sample_ids,
            "sourcePageNos": sample_pages,
        },
        "title": title_candidates[0] if title_candidates else str(doc.get("name") or ""),
        "titleCandidates": title_candidates,
        "docTypeGuess": "document",
        "overviewShort": "",
        "overviewLong": "",
        "keywords": [],
        "topics": [],
        "qualityContext": {
            "avgFinalScore": float(quality_report.get("avgFinalScore") or 0.0),
            "avgLayoutScore": float(quality_report.get("avgLayoutScore") or 0.0),
            "pagesWithIssues": int(quality_report.get("pagesWithIssues") or 0),
            "pagesWithLayoutIssues": int(quality_report.get("pagesWithLayoutIssues") or 0),
        },
    }


def _heuristic_overview(doc: Dict[str, Any], payload: Dict[str, Any], samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    texts = [_clean_text(chunk.get("content") or "") for chunk in samples]
    texts = [text for text in texts if text]
    short = texts[0][:120] if texts else str(doc.get("name") or "")
    long_parts = texts[:6]
    payload["overviewShort"] = short
    payload["overviewLong"] = "\n".join(long_parts)
    payload["keywords"] = [token for token in payload.get("titleCandidates", [])[:3] if token]
    payload["topics"] = payload["keywords"][:]
    return payload


def generate_overview(root: Path, doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("id") or "")
    log_event("overview.generate.start", docId=doc_id)
    samples, title_candidates = collect_overview_samples(doc)
    payload = default_overview_payload(doc, doc.get("ocrQualityReport"), samples, title_candidates)
    if not samples:
        log_event("overview.generate.empty", docId=doc_id, reason="no_samples")
        return payload
    sample_lines = []
    for chunk in samples:
        cid = str(chunk.get("chunkId") or "")
        page_no = int(chunk.get("pageNo") or 0)
        label = str(chunk.get("label") or "text")
        text = _clean_text(chunk.get("content") or "")
        sample_lines.append(f"[{cid}] page={page_no} label={label}\n{text}")
    system_prompt = (
        "You summarize OCR documents for retrieval. Prefer title candidates and early pages. "
        "Return JSON with title, docTypeGuess, overviewShort, overviewLong, keywords, topics."
    )
    user_prompt = "\n\n".join([
        f"Document name: {doc.get('name') or doc.get('id')}",
        "Title candidates:\n" + "\n".join(title_candidates[:5]),
        "Sample chunks:\n" + "\n\n".join(sample_lines[:24]),
    ])
    try:
        result = _deepseek_chat_json(root, system_prompt, user_prompt)
        payload["title"] = str(result.get("title") or payload["title"]).strip()
        payload["docTypeGuess"] = str(result.get("docTypeGuess") or payload["docTypeGuess"]).strip() or "document"
        payload["overviewShort"] = str(result.get("overviewShort") or "").strip()
        payload["overviewLong"] = str(result.get("overviewLong") or "").strip()
        payload["keywords"] = result.get("keywords") if isinstance(result.get("keywords"), list) else []
        payload["topics"] = result.get("topics") if isinstance(result.get("topics"), list) else []
        log_event(
            "overview.generate.end",
            docId=doc_id,
            mode="deepseek",
            keywordCount=len(payload["keywords"]),
            topicCount=len(payload["topics"]),
        )
        return payload
    except Exception as exc:
        log_event(
            "overview.generate.fallback",
            level="WARNING",
            docId=doc_id,
            mode="heuristic",
            error=str(exc),
        )
        return _heuristic_overview(doc, payload, samples)


def upsert_document_overview(root: Path, project_dir: Path, doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("id") or "").strip()
    if not doc_id:
        raise ValueError("missing doc id")
    overview = generate_overview(root, doc)
    write_document_overview(project_dir, doc_id, overview)

    index = read_documents_index(project_dir)
    entries = index.get("documents") if isinstance(index.get("documents"), list) else []
    item = {
        "docId": doc_id,
        "docName": doc.get("name"),
        "updatedAt": overview.get("generatedAt"),
        "hasOcr": bool(doc.get("ocrParsed")),
        "hasOverview": True,
        "title": overview.get("title") or "",
        "docTypeGuess": overview.get("docTypeGuess") or "",
        "overviewShort": overview.get("overviewShort") or "",
        "keywords": overview.get("keywords") if isinstance(overview.get("keywords"), list) else [],
        "topics": overview.get("topics") if isinstance(overview.get("topics"), list) else [],
        "pageCount": int(doc.get("pdfNumPages") or len(doc.get("pdfPageImages") or [])),
        "avgFinalScore": float((doc.get("ocrQualityReport") or {}).get("avgFinalScore") or 0.0),
        "avgLayoutScore": float((doc.get("ocrQualityReport") or {}).get("avgLayoutScore") or 0.0),
        "_comment": "Lightweight document entry used before deeper chunk-level retrieval.",
    }
    found = False
    for idx, entry in enumerate(entries):
        if isinstance(entry, dict) and str(entry.get("docId") or "") == doc_id:
            entries[idx] = item
            found = True
            break
    if not found:
        entries.append(item)
    entries.sort(key=lambda entry: str(entry.get("updatedAt") or ""), reverse=True)
    index["documents"] = entries
    write_documents_index(project_dir, index)
    log_event(
        "overview.upserted",
        docId=doc_id,
        hasOverview=True,
        pageCount=item["pageCount"],
        avgFinalScore=item["avgFinalScore"],
    )
    return overview


def ensure_document_overview(root: Path, project_dir: Path, doc: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(doc.get("id") or "").strip()
    if not doc_id:
        raise ValueError("missing doc id")
    existing = read_document_overview(project_dir, doc_id)
    if isinstance(existing, dict) and str(existing.get("status") or "") == "ready":
        return existing
    return upsert_document_overview(root, project_dir, doc)
