from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.chunk_store import normalize_chunk_content  # noqa: E402


DEFAULT_SOURCE_CHUNK_PATH = (
    ROOT
    / "data"
    / "projects"
    / "6cf73d20-55fb-43c6-987e-efc088417ca9"
    / "documents"
    / "pdf_7f3c742d"
    / "chunks.json"
)
DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent / "lad_chunk.json"


HTML_TAG_RE = re.compile(r"<[^>]+>")
HEADING_PREFIX_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
DECIMAL_HEADING_RE = re.compile(r"^\s*(\d+(?:\.\d+){0,6})(?:[.．])?\s+(\S.{0,120})$")
ZH_CHAPTER_RE = re.compile(r"^\s*第[一二三四五六七八九十百千万\d]+[章节篇]\s*\S.{0,100}$")
ZH_TOP_ENUM_RE = re.compile(r"^\s*[一二三四五六七八九十百千万]+[、.．]\s*\S.{0,100}$")
EN_CHAPTER_RE = re.compile(r"^\s*(chapter|section|part)\s+[A-Za-z0-9IVXLCDM]+[.:：\-\s]+.{1,100}$", re.I)
APPENDIX_RE = re.compile(r"^\s*(appendix|附录)\s*[A-Za-z\d一二三四五六七八九十百千万]*[.:：\-\s]+.{0,120}$", re.I)
ROMAN_HEADING_RE = re.compile(r"^\s*[IVXLCDM]{1,8}[.)]\s+\S.{0,100}$", re.I)
PAREN_ENUM_RE = re.compile(r"^\s*[\(（]\s*(?:\d{1,3}|[一二三四五六七八九十百千万]+|[A-Za-z])\s*[\)）]\s*\S.{0,120}$")
TRAILING_ENUM_RE = re.compile(r"^\s*(?:\d{1,3}|[一二三四五六七八九十百千万]+|[A-Za-z])[\)）]\s*\S.{0,120}$")
ZH_ENUM_RE = re.compile(r"^\s*[一二三四五六七八九十百千万]+[、.．]\s*\S.{0,120}$")
CIRCLED_ENUM_RE = re.compile(r"^\s*(?:[①②③④⑤⑥⑦⑧⑨⑩]|\\?textcircled\s*\{?\d+\}?|[$\s\\{}]*textcircled\s*\{?\d+\}?[$\s\\{}]*)\s*\S.{0,120}$")
SCENE_RE = re.compile(
    r"^\s*(?:场景|案例|示例|步骤|阶段|任务|scenario|case|example|step|stage|task)\s*"
    r"[一二三四五六七八九十百千万\dA-Za-z]*[：:、.\-\s]\s*\S.{0,120}$",
    re.I,
)
KEY_VALUE_HEADING_RE = re.compile(r"^\s*[^。！？!?]{1,42}[：:]\s*$")
COMMON_SECTION_RE = re.compile(
    r"^\s*(abstract|introduction|background|methodology|method|methods|experiment|experiments|"
    r"result|results|discussion|conclusion|references|acknowledgements?|摘要|目录|绪论|结论|参考文献)\s*$",
    re.I,
)
CODE_FENCE_RE = re.compile(r"```[\s\S]*?```")


@dataclass
class HeadingDecision:
    is_heading: bool
    level: Optional[int]
    text: str
    confidence: float
    role: str
    pattern: str
    reasons: List[str] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Source chunk file does not exist: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Source chunk file must contain a JSON object: {path}")
    return data


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def repair_mojibake(value: str) -> str:
    """Repair common UTF-8 text decoded as GBK without changing healthy text."""
    if not value:
        return value
    candidates = [value]
    for encoding in ("gbk", "cp936", "latin1"):
        try:
            candidates.append(value.encode(encoding).decode("utf-8"))
        except UnicodeError:
            pass
    return max(candidates, key=text_health_score)


def text_health_score(value: str) -> float:
    if not value:
        return 0.0
    cjk = sum(1 for ch in value if "\u4e00" <= ch <= "\u9fff")
    ascii_letters = sum(1 for ch in value if ch.isascii() and ch.isalpha())
    bad = value.count("�") * 8 + value.count("锟") * 5 + value.count("�") * 5
    mojibake_markers = sum(value.count(marker) for marker in ("浜", "鍥", "绗", "锛", "銆", "鐨"))
    return cjk * 2.0 + ascii_letters * 0.25 - bad - mojibake_markers * 2.5


def clean_text(text: Any) -> str:
    value = str(text or "")
    value = HTML_TAG_RE.sub("\n", value)
    value = repair_mojibake(value)
    value = normalize_chunk_content(value)
    value = re.sub(r"\n{2,}", "\n", value)
    return value.strip()


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


def strip_markdown_prefix(text: str) -> str:
    match = HEADING_PREFIX_RE.match(text)
    if match:
        return match.group(2).strip()
    return text.strip()


def normalize_heading_candidate(text: str) -> str:
    stripped = strip_markdown_prefix(clean_text(text))
    stripped = stripped.replace("\\(", "(").replace("\\)", ")")
    stripped = stripped.replace("（", "(").replace("）", ")")
    stripped = re.sub(r"\s+", " ", stripped)
    return stripped.strip()


def detect_profile(texts: Iterable[str], requested: str) -> str:
    if requested != "auto":
        return requested
    joined = "\n".join(texts)[:20000]
    cjk = sum(1 for ch in joined if "\u4e00" <= ch <= "\u9fff")
    latin = sum(1 for ch in joined if ch.isascii() and ch.isalpha())
    if cjk and latin and min(cjk, latin) / max(cjk, latin) > 0.15:
        return "mixed"
    if cjk > latin:
        return "zh"
    return "en"


def line_features(chunk: Dict[str, Any], clean: str) -> Dict[str, Any]:
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    bbox = chunk.get("bboxNorm") if isinstance(chunk.get("bboxNorm"), dict) else {}
    width = float(bbox.get("x2", 0) or 0) - float(bbox.get("x1", 0) or 0)
    height = float(bbox.get("y2", 0) or 0) - float(bbox.get("y1", 0) or 0)
    x1 = float(bbox.get("x1", 0) or 0)
    x2 = float(bbox.get("x2", 0) or 0)
    center_x = (x1 + x2) / 2 if x2 else 0
    return {
        "lines": lines,
        "lineCount": len(lines),
        "charCount": len(clean),
        "bboxWidth": width,
        "bboxHeight": height,
        "centerX": center_x,
        "isCentered": 0.35 <= center_x <= 0.65 and width <= 0.75,
        "isShort": len(clean) <= 120 and len(lines) <= 2,
        "hasCodeFence": bool(CODE_FENCE_RE.search(clean)),
    }


def is_formal_heading(text: str) -> bool:
    stripped = normalize_heading_candidate(text)
    return bool(
        DECIMAL_HEADING_RE.match(stripped)
        or ZH_CHAPTER_RE.match(stripped)
        or EN_CHAPTER_RE.match(stripped)
        or APPENDIX_RE.match(stripped)
        or COMMON_SECTION_RE.match(stripped)
    )


def is_attached_subheading(text: str) -> bool:
    stripped = normalize_heading_candidate(text)
    if not stripped or is_formal_heading(stripped):
        return False
    compact = re.sub(r"\s+", "", stripped)
    enum_like = bool(
        PAREN_ENUM_RE.match(stripped)
        or TRAILING_ENUM_RE.match(stripped)
        or ZH_ENUM_RE.match(stripped)
        or CIRCLED_ENUM_RE.match(stripped)
    )
    if enum_like:
        if len(compact) <= 72:
            return True
        return stripped.rstrip().endswith((":", "："))
    return bool(SCENE_RE.match(stripped) or KEY_VALUE_HEADING_RE.match(stripped))


def infer_numbered_heading_level(text: str) -> int:
    stripped = normalize_heading_candidate(text)
    if ZH_CHAPTER_RE.match(stripped) or EN_CHAPTER_RE.match(stripped):
        return 1
    decimal = re.match(r"^\s*(\d+(?:\.\d+)*)", stripped)
    if decimal:
        return min(decimal.group(1).count(".") + 1, 6)
    if APPENDIX_RE.match(stripped) or COMMON_SECTION_RE.match(stripped):
        return 1
    if ZH_TOP_ENUM_RE.match(stripped) or ROMAN_HEADING_RE.match(stripped):
        return 1
    return 1


def infer_heading_level(text: str, fallback_level: int) -> int:
    stripped = normalize_heading_candidate(text)
    if (
        DECIMAL_HEADING_RE.match(stripped)
        or ZH_CHAPTER_RE.match(stripped)
        or EN_CHAPTER_RE.match(stripped)
        or APPENDIX_RE.match(stripped)
        or COMMON_SECTION_RE.match(stripped)
    ):
        return infer_numbered_heading_level(stripped)
    return max(1, min(int(fallback_level or 1), 6))


def detect_heading(chunk: Dict[str, Any], profile: str) -> HeadingDecision:
    clean = chunk.get("cleanText") or clean_text(chunk.get("normalizedContent") or chunk.get("content"))
    if not clean:
        return HeadingDecision(False, None, "", 0.0, "text", "empty")

    features = line_features(chunk, clean)
    lines = features["lines"]
    block_type = infer_block_type(chunk.get("label"))
    first_line = lines[0] if lines else ""
    candidate = normalize_heading_candidate(first_line)
    reasons: List[str] = []
    score = 0.0
    level: Optional[int] = None
    role = "text"
    pattern = "none"

    if features["hasCodeFence"] or block_type in {"code", "table", "image", "formula"}:
        return HeadingDecision(False, None, "", 0.0, block_type, "blocked_content")

    md = HEADING_PREFIX_RE.match(first_line)
    if md:
        score += 0.62
        reasons.append("markdown_heading")
        pattern = "markdown"
        level = infer_heading_level(candidate, min(len(md.group(1)), 6))

    if is_formal_heading(candidate):
        score += 0.58
        reasons.append("formal_number_or_named_section")
        pattern = "formal"
        level = infer_numbered_heading_level(candidate)

    if is_attached_subheading(candidate):
        score += 0.5
        reasons.append("attached_subheading_pattern")
        pattern = "attached"
        level = -1

    if block_type == "title":
        score += 0.45
        reasons.append("source_label_title")
        pattern = "source_label" if pattern == "none" else pattern
        level = level or 1

    if features["isShort"]:
        score += 0.12
        reasons.append("short_block")
    else:
        score -= 0.25
        reasons.append("long_block_penalty")

    if features["lineCount"] <= 2:
        score += 0.08
    else:
        score -= 0.2

    if features["isCentered"]:
        score += 0.08
        reasons.append("centered_layout")

    if profile in {"zh", "mixed"} and re.search(r"[\u4e00-\u9fff]", candidate):
        score += 0.03
    if profile in {"en", "mixed"} and re.search(r"[A-Za-z]", candidate):
        score += 0.03

    score = max(0.0, min(score, 1.0))
    if score < 0.52 or not candidate:
        return HeadingDecision(False, None, "", score, "text", pattern, reasons)

    if level == -1:
        role = "attached_subheading"
    else:
        role = "formal_section"
        level = max(1, min(int(level or 1), 6))
    return HeadingDecision(True, level, candidate, score, role, pattern, reasons)


def flatten_pages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    pages = payload.get("pages") if isinstance(payload.get("pages"), list) else []
    chunks: List[Dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_chunks = page.get("chunks") if isinstance(page.get("chunks"), list) else []
        for chunk in page_chunks:
            if isinstance(chunk, dict):
                chunks.append(dict(chunk))
    chunks.sort(key=lambda item: (int(item.get("pageNo") or 0), int(item.get("index") or 0)))
    return chunks


def resolve_section_parent(
    section_stack: List[Dict[str, Any]],
    heading_level: int,
) -> Tuple[Optional[str], int]:
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


def build_lad_payload(payload: Dict[str, Any], source_path: Path, profile: str) -> Dict[str, Any]:
    flat_chunks = flatten_pages(payload)
    clean_samples = [clean_text(chunk.get("normalizedContent") or chunk.get("content")) for chunk in flat_chunks[:120]]
    resolved_profile = detect_profile(clean_samples, profile)
    sections: List[Dict[str, Any]] = []
    section_stack: List[Dict[str, Any]] = []
    enhanced: List[Dict[str, Any]] = []
    heading_stats: Dict[str, int] = {}

    by_page: Dict[int, List[Dict[str, Any]]] = {}
    for global_index, chunk in enumerate(flat_chunks):
        chunk["globalIndex"] = global_index
        chunk["blockType"] = infer_block_type(chunk.get("label"))
        chunk["cleanText"] = clean_text(chunk.get("normalizedContent") or chunk.get("content"))

        decision = detect_heading(chunk, resolved_profile)
        chunk["isHeading"] = decision.is_heading
        chunk["headingLevel"] = decision.level
        chunk["headingText"] = decision.text
        chunk["headingConfidence"] = round(decision.confidence, 3)
        chunk["headingPattern"] = decision.pattern
        chunk["structureRole"] = decision.role
        chunk["headingReasons"] = decision.reasons

        if decision.is_heading and decision.level:
            parent_id, resolved_level = resolve_section_parent(section_stack, decision.level)
            parent_path = [item["title"] for item in section_stack]
            section_id = f"sec_{len(sections):04d}"
            section = {
                "sectionId": section_id,
                "title": decision.text,
                "level": resolved_level,
                "isAttachedSubheading": decision.level < 0,
                "structureRole": decision.role,
                "headingConfidence": round(decision.confidence, 3),
                "headingPattern": decision.pattern,
                "headingReasons": decision.reasons,
                "chunkId": str(chunk.get("chunkId") or ""),
                "pageNo": int(chunk.get("pageNo") or 0),
                "globalIndex": global_index,
                "parentId": parent_id,
                "path": parent_path + [decision.text],
            }
            sections.append(section)
            section_stack.append(section)
            heading_stats[decision.role] = heading_stats.get(decision.role, 0) + 1

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

    pages_out: List[Dict[str, Any]] = []
    source_pages = payload.get("pages") if isinstance(payload.get("pages"), list) else []
    image_size_map = {
        int(page.get("pageNo") or 0): page.get("imageSize")
        for page in source_pages
        if isinstance(page, dict)
    }
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

    low_confidence = [
        {
            "chunkId": str(chunk.get("chunkId") or ""),
            "pageNo": int(chunk.get("pageNo") or 0),
            "headingText": chunk.get("headingText", ""),
            "headingConfidence": chunk.get("headingConfidence"),
            "headingPattern": chunk.get("headingPattern"),
        }
        for chunk in enhanced
        if chunk.get("isHeading") and float(chunk.get("headingConfidence") or 0) < 0.68
    ][:80]

    return {
        "status": "ready",
        "sourceChunkPath": str(source_path),
        "generatedAt": utc_now(),
        "docId": str(payload.get("docId") or ""),
        "docName": repair_mojibake(str(payload.get("docName") or "")),
        "profile": resolved_profile,
        "pageCount": len(pages_out),
        "totalChunks": len(enhanced),
        "structure": {
            "sectionCount": len(sections),
            "headingStats": heading_stats,
            "lowConfidenceHeadings": low_confidence,
            "sections": sections,
        },
        "pages": pages_out,
        "chunks": enhanced,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build isolated LAD-enriched chunks for testing.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_CHUNK_PATH, help="Source chunks.json path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output lad_chunk.json path.")
    parser.add_argument(
        "--profile",
        choices=("auto", "zh", "en", "mixed"),
        default="auto",
        help="Heading detection profile.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = read_json(args.source)
    lad_payload = build_lad_payload(payload, args.source, args.profile)
    write_json(args.output, lad_payload)
    print(f"Wrote {args.output}")
    print(
        "Summary: "
        f"profile={lad_payload['profile']}, "
        f"chunks={lad_payload['totalChunks']}, "
        f"pages={lad_payload['pageCount']}, "
        f"sections={lad_payload['structure']['sectionCount']}, "
        f"headingStats={lad_payload['structure']['headingStats']}"
    )


if __name__ == "__main__":
    main()
