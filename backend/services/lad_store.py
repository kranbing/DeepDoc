from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from backend.services.chunk_store import flatten_document_chunks, normalize_chunk_content, read_document_chunks
from backend.services.project_store import document_dir, read_json, utc_now, write_json


HEADING_PREFIX_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
DECIMAL_HEADING_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,6})(?:[.)])?\s+(\S.{0,120})$")
ZH_CHAPTER_RE = re.compile(r"^\s*\u7b2c[\u4e00-\u9fff\d]+[\u7ae0\u8282\u7bc7]\s*\S.{0,120}$")
EN_CHAPTER_RE = re.compile(r"^\s*(chapter|section|part)\s+[A-Za-z0-9IVXLCDM]+[.:\-\s]+.{1,120}$", re.I)
APPENDIX_RE = re.compile(r"^\s*(appendix|\u9644\u5f55)\s*[A-Za-z\d\u4e00-\u9fff]*[.:\-\s]+.{0,120}$", re.I)
COMMON_SECTION_RE = re.compile(
    r"^\s*(abstract|introduction|background|methodology|method|methods|experiment|experiments|"
    r"result|results|discussion|conclusion|references|acknowledgements?)\s*$",
    re.I,
)
PAREN_ENUM_RE = re.compile(r"^\s*[\(（]\s*(?:\d{1,3}|[A-Za-z]|[\u4e00-\u9fff]{1,3})\s*[\)）]\s*\S.{0,120}$")
TRAILING_ENUM_RE = re.compile(r"^\s*(?:\d{1,3}|[A-Za-z]|[\u4e00-\u9fff]{1,3})[\)）]\s*\S.{0,120}$")
SCENE_RE = re.compile(
    r"^\s*(?:\u573a\u666f|\u6848\u4f8b|\u793a\u4f8b|\u6b65\u9aa4|\u9636\u6bb5|\u4efb\u52a1|"
    r"scenario|case|example|step|stage|task)\s*[\u4e00-\u9fff\dA-Za-z]*[:：.\-\s]\s*\S.{0,120}$",
    re.I,
)


def lad_chunk_path(project_dir: Path, doc_id: str) -> Path:
    return document_dir(project_dir, doc_id) / "lad_chunk.json"


def lad_graph_path(project_dir: Path, doc_id: str) -> Path:
    return document_dir(project_dir, doc_id) / "lad_graph.json"


def read_lad_chunks(project_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    data = read_json(lad_chunk_path(project_dir, doc_id), None)
    return data if isinstance(data, dict) else None


def read_preferred_lad_chunks(project_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    lad_payload = read_lad_chunks(project_dir, doc_id)
    if isinstance(lad_payload, dict) and str(lad_payload.get("status") or "") == "ready":
        return lad_payload
    payload = read_document_chunks(project_dir, doc_id)
    return payload if isinstance(payload, dict) else None


def read_lad_graph(project_dir: Path, doc_id: str) -> Optional[Dict[str, Any]]:
    data = read_json(lad_graph_path(project_dir, doc_id), None)
    return data if isinstance(data, dict) else None


def clean_text(value: Any) -> str:
    text = normalize_chunk_content(str(value or ""))
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def detect_profile(samples: Iterable[str], requested: str = "auto") -> str:
    if requested in {"zh", "en", "mixed"}:
        return requested
    joined = "\n".join(samples)[:20000]
    cjk = sum(1 for ch in joined if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in joined if ch.isascii() and ch.isalpha())
    if cjk and latin and min(cjk, latin) / max(cjk, latin) > 0.15:
        return "mixed"
    return "zh" if cjk > latin else "en"


def infer_block_type(label: Any) -> str:
    value = str(label or "").strip().lower()
    if value in {"title", "heading", "header"}:
        return "title"
    if value in {"table", "table_caption"}:
        return "table"
    if value in {"image", "figure", "chart"}:
        return "image"
    if value in {"formula", "equation"}:
        return "formula"
    if value in {"caption", "figure_caption"}:
        return "caption"
    if value in {"list", "list_item"}:
        return "list"
    if value in {"code", "code_block"}:
        return "code"
    if value in {"text", "plain_text", "paragraph"}:
        return "text"
    return value or "unknown"


def _line_features(chunk: Dict[str, Any], text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bbox = chunk.get("bboxNorm") if isinstance(chunk.get("bboxNorm"), dict) else {}
    x1 = float(bbox.get("x1", 0) or 0)
    x2 = float(bbox.get("x2", 0) or 0)
    width = max(0.0, x2 - x1)
    center_x = (x1 + x2) / 2 if x2 else 0.0
    return {
        "lineCount": len(lines),
        "charCount": len(text),
        "isShort": len(text) <= 140 and len(lines) <= 2,
        "isCentered": 0.35 <= center_x <= 0.65 and width <= 0.78,
    }


def _normalized_heading_text(text: str) -> str:
    match = HEADING_PREFIX_RE.match(text)
    if match:
        text = match.group(2)
    return re.sub(r"\s+", " ", text).strip()


def _decimal_level(text: str) -> Optional[int]:
    match = DECIMAL_HEADING_RE.match(text)
    if not match:
        return None
    return max(1, min(match.group(1).count(".") + 1, 6))


def detect_heading(chunk: Dict[str, Any], profile: str) -> Dict[str, Any]:
    text = _normalized_heading_text(clean_text(chunk.get("normalizedContent") or chunk.get("content")))
    block_type = infer_block_type(chunk.get("label"))
    features = _line_features(chunk, text)
    if not text:
        return {"isHeading": False, "level": None, "text": "", "confidence": 0.0, "role": "text", "pattern": "empty"}

    level: Optional[int] = None
    pattern = "none"
    role = "text"
    score = 0.0

    markdown = HEADING_PREFIX_RE.match(clean_text(chunk.get("normalizedContent") or chunk.get("content")))
    if markdown:
        level = len(markdown.group(1))
        pattern = "markdown"
        score += 0.72
    decimal_level = _decimal_level(text)
    if decimal_level:
        level = decimal_level
        pattern = "decimal"
        score += 0.78
    elif ZH_CHAPTER_RE.match(text) or EN_CHAPTER_RE.match(text) or APPENDIX_RE.match(text):
        level = 1
        pattern = "chapter"
        score += 0.78
    elif COMMON_SECTION_RE.match(text):
        level = 1
        pattern = "common"
        score += 0.62
    elif PAREN_ENUM_RE.match(text) or TRAILING_ENUM_RE.match(text) or SCENE_RE.match(text):
        level = -1
        pattern = "attached"
        score += 0.56

    if block_type == "title":
        level = level or 1
        pattern = "source_label" if pattern == "none" else pattern
        score += 0.35
    if features["isShort"]:
        score += 0.12
    else:
        score -= 0.25
    if features["lineCount"] <= 2:
        score += 0.06
    if features["isCentered"]:
        score += 0.06
    if profile in {"zh", "mixed"} and re.search(r"[\u4e00-\u9fff]", text):
        score += 0.03
    if profile in {"en", "mixed"} and re.search(r"[A-Za-z]", text):
        score += 0.03

    score = max(0.0, min(score, 1.0))
    if score < 0.52 or level is None:
        return {"isHeading": False, "level": None, "text": "", "confidence": score, "role": "text", "pattern": pattern}
    if level < 0:
        role = "attached_subheading"
    else:
        role = "formal_section"
        level = max(1, min(level, 6))
    return {"isHeading": True, "level": level, "text": text, "confidence": score, "role": role, "pattern": pattern}


def resolve_section_parent(section_stack: List[Dict[str, Any]], heading_level: int) -> Tuple[Optional[str], int]:
    if heading_level < 0:
        while section_stack and section_stack[-1].get("structureRole") == "attached_subheading":
            section_stack.pop()
        parent_id = section_stack[-1]["sectionId"] if section_stack else None
        base_level = int(section_stack[-1]["level"]) if section_stack else 0
        return parent_id, min(base_level + 1, 6)
    while section_stack and int(section_stack[-1]["level"]) >= heading_level:
        section_stack.pop()
    parent_id = section_stack[-1]["sectionId"] if section_stack else None
    return parent_id, heading_level


def build_lad_payload(chunk_payload: Dict[str, Any], source_path: Path, profile: str = "auto") -> Dict[str, Any]:
    flat_chunks = flatten_document_chunks(chunk_payload)
    resolved_profile = detect_profile(
        [clean_text(chunk.get("normalizedContent") or chunk.get("content")) for chunk in flat_chunks[:120]],
        profile,
    )
    sections: List[Dict[str, Any]] = []
    section_stack: List[Dict[str, Any]] = []
    enhanced: List[Dict[str, Any]] = []
    heading_stats: Dict[str, int] = {}
    by_page: Dict[int, List[Dict[str, Any]]] = {}

    for global_index, original in enumerate(flat_chunks):
        chunk = dict(original)
        chunk["globalIndex"] = global_index
        chunk["blockType"] = infer_block_type(chunk.get("label"))
        chunk["cleanText"] = clean_text(chunk.get("normalizedContent") or chunk.get("content"))
        decision = detect_heading(chunk, resolved_profile)
        chunk["isHeading"] = decision["isHeading"]
        chunk["headingLevel"] = decision["level"]
        chunk["headingText"] = decision["text"]
        chunk["headingConfidence"] = round(float(decision["confidence"]), 3)
        chunk["headingPattern"] = decision["pattern"]
        chunk["structureRole"] = decision["role"]

        if decision["isHeading"] and decision["level"]:
            parent_id, resolved_level = resolve_section_parent(section_stack, int(decision["level"]))
            parent_path = [item["title"] for item in section_stack]
            section_id = f"sec_{len(sections):04d}"
            section = {
                "sectionId": section_id,
                "title": decision["text"],
                "level": resolved_level,
                "isAttachedSubheading": int(decision["level"]) < 0,
                "structureRole": decision["role"],
                "headingConfidence": round(float(decision["confidence"]), 3),
                "headingPattern": decision["pattern"],
                "chunkId": str(chunk.get("chunkId") or ""),
                "pageNo": int(chunk.get("pageNo") or 0),
                "globalIndex": global_index,
                "parentId": parent_id,
                "path": parent_path + [decision["text"]],
            }
            sections.append(section)
            section_stack.append(section)
            heading_stats[decision["role"]] = heading_stats.get(decision["role"], 0) + 1

        current_section = section_stack[-1] if section_stack else None
        section_path = [item["title"] for item in section_stack]
        chunk["sectionId"] = current_section["sectionId"] if current_section else None
        chunk["sectionTitle"] = current_section["title"] if current_section else ""
        chunk["sectionLevel"] = current_section["level"] if current_section else None
        chunk["sectionPath"] = section_path
        chunk["sectionPathText"] = " > ".join(section_path)

        page_no = int(chunk.get("pageNo") or 0)
        by_page.setdefault(page_no, []).append(chunk)
        enhanced.append(chunk)

    for idx, chunk in enumerate(enhanced):
        chunk["prevGlobalChunkId"] = enhanced[idx - 1].get("chunkId") if idx > 0 else None
        chunk["nextGlobalChunkId"] = enhanced[idx + 1].get("chunkId") if idx + 1 < len(enhanced) else None

    source_pages = chunk_payload.get("pages") if isinstance(chunk_payload.get("pages"), list) else []
    image_size_map = {
        int(page.get("pageNo") or 0): page.get("imageSize")
        for page in source_pages
        if isinstance(page, dict)
    }
    pages_out: List[Dict[str, Any]] = []
    for page_no in sorted(by_page):
        page_chunks = by_page[page_no]
        for idx, chunk in enumerate(page_chunks):
            chunk["prevSamePageChunkId"] = page_chunks[idx - 1].get("chunkId") if idx > 0 else None
            chunk["nextSamePageChunkId"] = page_chunks[idx + 1].get("chunkId") if idx + 1 < len(page_chunks) else None
        pages_out.append(
            {
                "pageNo": page_no,
                "chunkCount": len(page_chunks),
                "imageSize": image_size_map.get(page_no) if isinstance(image_size_map.get(page_no), dict) else {},
                "chunks": page_chunks,
            }
        )

    return {
        "status": "ready",
        "sourceChunkPath": str(source_path),
        "generatedAt": utc_now(),
        "docId": str(chunk_payload.get("docId") or ""),
        "docName": str(chunk_payload.get("docName") or ""),
        "profile": resolved_profile,
        "pageCount": len(pages_out),
        "totalChunks": len(enhanced),
        "structure": {
            "sectionCount": len(sections),
            "headingStats": heading_stats,
            "sections": sections,
        },
        "pages": pages_out,
        "chunks": enhanced,
    }


def build_lad_graph(lad_payload: Dict[str, Any]) -> Dict[str, Any]:
    doc_id = str(lad_payload.get("docId") or "")
    doc_node_id = f"doc:{doc_id or 'document'}"
    nodes: List[Dict[str, Any]] = [
        {
            "id": doc_node_id,
            "type": "document",
            "label": str(lad_payload.get("docName") or doc_id or "Document"),
            "pageNo": 1,
        }
    ]
    edges: List[Dict[str, Any]] = []
    sections = lad_payload.get("structure", {}).get("sections") if isinstance(lad_payload.get("structure"), dict) else []
    section_ids = set()
    if isinstance(sections, list):
        for section in sections:
            if not isinstance(section, dict):
                continue
            section_id = str(section.get("sectionId") or "")
            if not section_id:
                continue
            node_id = f"section:{section_id}"
            section_ids.add(section_id)
            nodes.append(
                {
                    "id": node_id,
                    "type": "section",
                    "label": str(section.get("title") or section_id),
                    "sectionId": section_id,
                    "parentId": section.get("parentId"),
                    "level": section.get("level"),
                    "pageNo": section.get("pageNo"),
                    "chunkId": section.get("chunkId"),
                    "path": section.get("path") if isinstance(section.get("path"), list) else [],
                }
            )
            parent_id = str(section.get("parentId") or "")
            edges.append(
                {
                    "source": f"section:{parent_id}" if parent_id in section_ids else doc_node_id,
                    "target": node_id,
                    "type": "contains",
                }
            )

    for chunk in lad_payload.get("chunks") if isinstance(lad_payload.get("chunks"), list) else []:
        if not isinstance(chunk, dict) or chunk.get("isHeading"):
            continue
        chunk_id = str(chunk.get("chunkId") or "")
        if not chunk_id:
            continue
        parent_section = str(chunk.get("sectionId") or "")
        nodes.append(
            {
                "id": f"chunk:{chunk_id}",
                "type": "chunk",
                "label": clean_text(chunk.get("cleanText") or chunk.get("normalizedContent") or chunk.get("content"))[:80],
                "chunkId": chunk_id,
                "pageNo": chunk.get("pageNo"),
                "blockType": chunk.get("blockType"),
                "sectionId": parent_section or None,
            }
        )
        edges.append(
            {
                "source": f"section:{parent_section}" if parent_section in section_ids else doc_node_id,
                "target": f"chunk:{chunk_id}",
                "type": "contains",
            }
        )

    return {
        "status": "ready",
        "generatedAt": utc_now(),
        "docId": doc_id,
        "docName": str(lad_payload.get("docName") or ""),
        "nodeCount": len(nodes),
        "edgeCount": len(edges),
        "nodes": nodes,
        "edges": edges,
    }


def expand_lad_related_chunks(
    payload: Optional[Dict[str, Any]],
    seed_chunks: List[Dict[str, Any]],
    *,
    max_items: int = 6,
    strategy: str = "section_first",
) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    chunks = flatten_document_chunks(payload)
    if not chunks:
        return []
    by_id = {str(chunk.get("chunkId") or chunk.get("chunkKey") or ""): chunk for chunk in chunks}
    seed_ids: List[str] = []
    seed_sections: List[str] = []
    for seed in seed_chunks:
        source_ids = seed.get("sourceChunkIds") if isinstance(seed.get("sourceChunkIds"), list) else []
        for cid in source_ids:
            value = str(cid or "").strip()
            if value and value not in seed_ids:
                seed_ids.append(value)
        cid = str(seed.get("chunkId") or seed.get("chunkKey") or "").strip()
        if cid and cid not in seed_ids:
            seed_ids.append(cid)
        source_sections = seed.get("sourceSectionIds") if isinstance(seed.get("sourceSectionIds"), list) else []
        for section_id in source_sections:
            value = str(section_id or "").strip()
            if value and value not in seed_sections:
                seed_sections.append(value)
        section_id = str(seed.get("sectionId") or "").strip()
        if section_id and section_id not in seed_sections:
            seed_sections.append(section_id)

    for cid in seed_ids:
        chunk = by_id.get(cid)
        section_id = str(chunk.get("sectionId") or "").strip() if isinstance(chunk, dict) else ""
        if section_id and section_id not in seed_sections:
            seed_sections.append(section_id)

    seen = set(seed_ids)
    related: List[Dict[str, Any]] = []

    def add_chunk(chunk: Any) -> bool:
        if not isinstance(chunk, dict):
            return False
        cid = str(chunk.get("chunkId") or chunk.get("chunkKey") or "").strip()
        if not cid or cid in seen:
            return False
        seen.add(cid)
        related.append(chunk)
        return len(related) >= max_items

    def _expand_neighbors() -> bool:
        for cid in seed_ids:
            chunk = by_id.get(cid)
            if not isinstance(chunk, dict):
                continue
            for neighbor_id in (
                chunk.get("prevGlobalChunkId"),
                chunk.get("nextGlobalChunkId"),
                chunk.get("prevSamePageChunkId"),
                chunk.get("nextSamePageChunkId"),
            ):
                if add_chunk(by_id.get(str(neighbor_id or ""))):
                    return True
        return False

    def _expand_section(budget: Optional[int] = None) -> bool:
        for section_id in seed_sections:
            for chunk in chunks:
                if str(chunk.get("sectionId") or "") != section_id:
                    continue
                if bool(chunk.get("isHeading")):
                    continue
                if add_chunk(chunk):
                    return True
                if budget is not None and len(related) >= budget:
                    return False
        return False

    if strategy == "section_first":
        if _expand_section():
            return related
        if _expand_neighbors():
            return related
    elif strategy == "mixed":
        half = max(1, max_items // 2)
        _expand_section(budget=half)
        if len(related) < max_items:
            _expand_neighbors()
    else:
        # neighbor_first (original behavior)
        if _expand_neighbors():
            return related
        if _expand_section():
            return related

    return related


def save_lad_artifacts(
    project_dir: Path,
    doc_id: str,
    chunk_payload: Optional[Dict[str, Any]] = None,
    *,
    profile: str = "auto",
) -> Dict[str, Any]:
    payload = chunk_payload if isinstance(chunk_payload, dict) else read_document_chunks(project_dir, doc_id)
    if not isinstance(payload, dict):
        raise FileNotFoundError(f"chunks.json not found for document: {doc_id}")
    source_path = document_dir(project_dir, doc_id) / "chunks.json"
    lad_payload = build_lad_payload(payload, source_path, profile=profile)
    graph_payload = build_lad_graph(lad_payload)
    write_json(lad_chunk_path(project_dir, doc_id), lad_payload)
    write_json(lad_graph_path(project_dir, doc_id), graph_payload)
    return {"ladChunk": lad_payload, "ladGraph": graph_payload}
