from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from statistics import median
import re
from typing import Any, Dict, List, Sequence, Tuple


@dataclass
class OCRBlock:
    index: int
    label: str
    content: str
    bbox_2d: List[int]
    page: int = 1


@dataclass
class Line:
    text: str
    bbox_2d: List[int]
    block_indices: List[int]


def normalize_blocks(raw_blocks: Sequence[Dict[str, Any]], page: int) -> List[OCRBlock]:
    normalized: List[OCRBlock] = []
    for i, block in enumerate(raw_blocks):
        bbox = block.get("bbox_2d") or []
        if not isinstance(bbox, list) or len(bbox) != 4:
            continue
        try:
            x1, y1, x2, y2 = [int(round(float(v))) for v in bbox]
        except Exception:
            continue
        if x2 <= x1 or y2 <= y1:
            continue
        normalized.append(
            OCRBlock(
                index=int(block.get("index", i)),
                label=str(block.get("label", "text")),
                content=str(block.get("content", "")).strip(),
                bbox_2d=[x1, y1, x2, y2],
                page=page,
            )
        )
    return normalized


def sort_blocks_reading_order(blocks: Sequence[OCRBlock]) -> List[OCRBlock]:
    return sorted(blocks, key=lambda b: ((b.bbox_2d[1] + b.bbox_2d[3]) / 2.0, b.bbox_2d[0]))


def _line_tolerance(blocks: Sequence[OCRBlock]) -> float:
    heights = [b.bbox_2d[3] - b.bbox_2d[1] for b in blocks]
    if not heights:
        return 12.0
    return max(6.0, median(heights) * 0.45)


def merge_blocks_to_lines(blocks: Sequence[OCRBlock]) -> List[Line]:
    sorted_blocks = sort_blocks_reading_order(blocks)
    if not sorted_blocks:
        return []

    tolerance = _line_tolerance(sorted_blocks)
    line_groups: List[List[OCRBlock]] = []

    for block in sorted_blocks:
        y_center = (block.bbox_2d[1] + block.bbox_2d[3]) / 2.0
        matched = False
        for group in line_groups:
            gy = sum((g.bbox_2d[1] + g.bbox_2d[3]) / 2.0 for g in group) / len(group)
            group_x1 = min(g.bbox_2d[0] for g in group)
            group_x2 = max(g.bbox_2d[2] for g in group)
            block_x1, _, block_x2, _ = block.bbox_2d

            horizontal_gap = 0
            if block_x1 > group_x2:
                horizontal_gap = block_x1 - group_x2
            elif group_x1 > block_x2:
                horizontal_gap = group_x1 - block_x2

            max_gap = max(50.0, tolerance * 3.0)
            if abs(y_center - gy) <= tolerance and horizontal_gap <= max_gap:
                group.append(block)
                matched = True
                break
        if not matched:
            line_groups.append([block])

    lines: List[Line] = []
    for group in line_groups:
        group = sorted(group, key=lambda b: b.bbox_2d[0])
        text = " ".join([b.content for b in group if b.content]).strip()
        if not text:
            continue
        x1 = min(g.bbox_2d[0] for g in group)
        y1 = min(g.bbox_2d[1] for g in group)
        x2 = max(g.bbox_2d[2] for g in group)
        y2 = max(g.bbox_2d[3] for g in group)
        lines.append(Line(text=text, bbox_2d=[x1, y1, x2, y2], block_indices=[b.index for b in group]))
    return sorted(lines, key=lambda ln: (ln.bbox_2d[1], ln.bbox_2d[0]))


def merge_lines_to_paragraphs(lines: Sequence[Line]) -> List[str]:
    if not lines:
        return []
    sorted_lines = sorted(lines, key=lambda ln: (ln.bbox_2d[1], ln.bbox_2d[0]))
    line_heights = [ln.bbox_2d[3] - ln.bbox_2d[1] for ln in sorted_lines]
    base_height = median(line_heights) if line_heights else 18.0
    paragraph_gap = base_height * 1.25

    paragraphs: List[List[str]] = [[sorted_lines[0].text]]
    prev = sorted_lines[0]
    for line in sorted_lines[1:]:
        gap = line.bbox_2d[1] - prev.bbox_2d[3]
        if gap <= paragraph_gap:
            paragraphs[-1].append(line.text)
        else:
            paragraphs.append([line.text])
        prev = line
    return ["\n".join(p).strip() for p in paragraphs if any(x.strip() for x in p)]


def rebuild_page_text(lines: Sequence[Line]) -> str:
    return "\n\n".join(merge_lines_to_paragraphs(lines)).strip()


def block_garbled_ratio(text: str) -> float:
    if not text:
        return 1.0
    valid = 0
    total = 0
    for ch in text:
        if ch.isspace():
            continue
        total += 1
        if ch.isalnum() or ch in "，。！？、；：,.!?;:()[]{}<>/\\+-=_@#%^&*'\"`~|":
            valid += 1
        elif "\u4e00" <= ch <= "\u9fff":
            valid += 1
    if total == 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - valid / total))


_MOJIBAKE_MARKERS = {"閿", "閵", "閳", "閺", "閻", "閸", "閹", "锟斤拷"}
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MD_HEADING_RE = re.compile(r"(^|\n)\s{0,3}#{1,6}\s+", re.M)
_PUNCT_RE = re.compile(r"[。！？；:!?;：]")


def _iou(a: List[int], b: List[int]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    inter = iw * ih
    if inter == 0:
        return 0.0
    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))
    return inter / float(area_a + area_b - inter)


def _bbox_area(bbox: List[int]) -> int:
    return max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])


def _intersection_area(a: List[int], b: List[int]) -> int:
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    return max(0, ix2 - ix1) * max(0, iy2 - iy1)


def _is_nested(inner: List[int], outer: List[int], tolerance: int = 2) -> bool:
    return (
        inner[0] >= outer[0] - tolerance
        and inner[1] >= outer[1] - tolerance
        and inner[2] <= outer[2] + tolerance
        and inner[3] <= outer[3] + tolerance
        and inner != outer
    )


def _collect_layout_metrics(blocks: Sequence[OCRBlock]) -> Tuple[Dict[str, Any], List[str], float]:
    issues: List[str] = []
    total_blocks = len(blocks)
    if not blocks:
        metrics = {
            "empty_block_ratio": 1.0,
            "consecutive_empty_blocks": 0.0,
            "max_consecutive_empty_blocks": 0.0,
            "empty_block_area_ratio": 0.0,
            "empty_block_label_distribution": {},
            "fragmentation_score": 0.0,
            "nested_box_ratio": 0.0,
            "overlap_ratio": 0.0,
            "coverage_ratio": 0.0,
        }
        return metrics, ["no_blocks_detected"], 0.0

    page_bbox = [
        min(b.bbox_2d[0] for b in blocks),
        min(b.bbox_2d[1] for b in blocks),
        max(b.bbox_2d[2] for b in blocks),
        max(b.bbox_2d[3] for b in blocks),
    ]
    page_area = max(1, _bbox_area(page_bbox))
    areas = [_bbox_area(b.bbox_2d) for b in blocks]
    empty_blocks = [b for b in blocks if not b.content.strip()]
    empty_ratio = len(empty_blocks) / max(1, total_blocks)
    empty_area_ratio = sum(_bbox_area(b.bbox_2d) for b in empty_blocks) / page_area

    sorted_blocks = sort_blocks_reading_order(blocks)
    consecutive_empty = 0
    max_consecutive_empty = 0
    for block in sorted_blocks:
        if block.content.strip():
            consecutive_empty = 0
            continue
        consecutive_empty += 1
        max_consecutive_empty = max(max_consecutive_empty, consecutive_empty)

    empty_label_distribution: Dict[str, int] = {}
    for block in empty_blocks:
        empty_label_distribution[block.label] = empty_label_distribution.get(block.label, 0) + 1

    overlap_pairs = 0
    heavy_overlap_pairs = 0
    nested_pairs = 0
    intersect_area = 0
    for a, b in combinations(blocks, 2):
        overlap_pairs += 1
        iou = _iou(a.bbox_2d, b.bbox_2d)
        if iou > 0.5:
            heavy_overlap_pairs += 1
        if _is_nested(a.bbox_2d, b.bbox_2d) or _is_nested(b.bbox_2d, a.bbox_2d):
            nested_pairs += 1
        intersect_area += _intersection_area(a.bbox_2d, b.bbox_2d)

    overlap_ratio = heavy_overlap_pairs / overlap_pairs if overlap_pairs else 0.0
    nested_ratio = nested_pairs / overlap_pairs if overlap_pairs else 0.0

    total_block_area = sum(areas)
    coverage_ratio = min(1.0, total_block_area / page_area)
    fragmentation_score = total_blocks / max(1.0, coverage_ratio * 100.0)

    if empty_ratio > 0.25:
        issues.append("high_empty_block_ratio")
    if max_consecutive_empty >= 3:
        issues.append("consecutive_empty_blocks")
    if empty_area_ratio > 0.2:
        issues.append("high_empty_block_area_ratio")
    if overlap_ratio > 0.1:
        issues.append("heavy_bbox_overlap")
    if nested_ratio > 0.08:
        issues.append("nested_bbox_anomaly")
    if coverage_ratio < 0.15:
        issues.append("low_layout_coverage")
    elif coverage_ratio > 0.95:
        issues.append("high_layout_coverage")
    if fragmentation_score > 1.2:
        issues.append("layout_fragmentation")

    penalty = 0.0
    penalty += min(0.25, empty_ratio * 0.6)
    penalty += min(0.18, empty_area_ratio * 0.6)
    penalty += min(0.15, max_consecutive_empty * 0.05)
    penalty += min(0.16, overlap_ratio * 0.8)
    penalty += min(0.12, nested_ratio * 1.2)
    penalty += 0.12 if coverage_ratio < 0.15 or coverage_ratio > 0.95 else 0.0
    penalty += min(0.16, max(0.0, fragmentation_score - 0.6) * 0.25)
    layout_score = max(0.0, min(1.0, 1.0 - penalty))

    metrics = {
        "empty_block_ratio": round(empty_ratio, 4),
        "consecutive_empty_blocks": float(sum(1 for b in sorted_blocks if not b.content.strip())),
        "max_consecutive_empty_blocks": float(max_consecutive_empty),
        "empty_block_area_ratio": round(empty_area_ratio, 4),
        "empty_block_label_distribution": empty_label_distribution,
        "fragmentation_score": round(fragmentation_score, 4),
        "nested_box_ratio": round(nested_ratio, 4),
        "overlap_ratio": round(overlap_ratio, 4),
        "coverage_ratio": round(coverage_ratio, 4),
    }
    return metrics, sorted(set(issues)), round(layout_score, 4)


def evaluate_page_quality(blocks: Sequence[OCRBlock], lines: Sequence[Line], text: str) -> Dict[str, Any]:
    issues: List[str] = []
    total_blocks = len(blocks)
    total_lines = len(lines)
    non_empty_blocks = [b for b in blocks if b.content.strip()]
    empty_ratio = 1.0 if total_blocks == 0 else 1.0 - (len(non_empty_blocks) / total_blocks)
    text_no_space = "".join(text.split())
    char_len = len(text_no_space)
    garbled_ratios = [block_garbled_ratio(b.content) for b in non_empty_blocks]
    garbled_ratio = sum(garbled_ratios) / len(garbled_ratios) if garbled_ratios else 1.0
    marker_hits = sum(text.count(marker) for marker in _MOJIBAKE_MARKERS)
    mojibake_ratio = marker_hits / max(1, len(text_no_space))

    overlap_pairs = 0
    heavy_overlap_pairs = 0
    for a, b in combinations(blocks, 2):
        overlap_pairs += 1
        if _iou(a.bbox_2d, b.bbox_2d) > 0.5:
            heavy_overlap_pairs += 1
    overlap_ratio = heavy_overlap_pairs / overlap_pairs if overlap_pairs else 0.0

    line_count_anomaly = 0.0
    if total_lines < 2:
        line_count_anomaly = 1.0
    elif total_lines > 220:
        line_count_anomaly = min(1.0, (total_lines - 220) / 120.0)

    text_length_penalty = 0.0
    if char_len < 20:
        text_length_penalty = min(1.0, (20 - char_len) / 20.0)
        issues.append("low_text_density")
    elif char_len > 20000:
        text_length_penalty = min(1.0, (char_len - 20000) / 15000.0)
        issues.append("abnormal_text_length")

    if garbled_ratio > 0.22:
        issues.append("possible_garbled_text")
    if mojibake_ratio > 0.01:
        issues.append("possible_encoding_mismatch")
    if empty_ratio > 0.3:
        issues.append("high_empty_content_ratio")
    if overlap_ratio > 0.1:
        issues.append("bbox_overlap_anomaly")
    if line_count_anomaly > 0.0:
        issues.append("abnormal_line_count")

    penalty = (
        text_length_penalty * 0.25
        + garbled_ratio * 0.3
        + min(1.0, mojibake_ratio * 8.0) * 0.15
        + empty_ratio * 0.2
        + overlap_ratio * 0.15
        + line_count_anomaly * 0.1
    )
    return {
        "score": max(0.0, min(1.0, 1.0 - penalty)),
        "issues": sorted(set(issues)),
        "metrics": {
            "char_len": float(char_len),
            "line_count": float(total_lines),
            "block_count": float(total_blocks),
            "garbled_ratio": round(garbled_ratio, 4),
            "mojibake_ratio": round(mojibake_ratio, 4),
            "empty_ratio": round(empty_ratio, 4),
            "overlap_ratio": round(overlap_ratio, 4),
            "line_count_anomaly": round(line_count_anomaly, 4),
            "text_length_penalty": round(text_length_penalty, 4),
        },
    }


def _column_interleave_risk(lines: Sequence[Line]) -> Tuple[bool, Dict[str, float]]:
    if len(lines) < 6:
        return False, {"column_switch_ratio": 0.0, "column_balance": 0.0}
    x_centers = [((ln.bbox_2d[0] + ln.bbox_2d[2]) / 2.0) for ln in lines]
    y_spans = [ln.bbox_2d[3] - ln.bbox_2d[1] for ln in lines]
    x_min = min(ln.bbox_2d[0] for ln in lines)
    x_max = max(ln.bbox_2d[2] for ln in lines)
    page_width = max(1.0, x_max - x_min)
    x_mid = median(x_centers)
    labels: List[str] = ["L" if x < x_mid else "R" for x in x_centers]
    left_count = labels.count("L")
    right_count = labels.count("R")
    balance = min(left_count, right_count) / max(1, len(labels))
    spread = (max(x_centers) - min(x_centers)) / page_width
    if balance < 0.2 or spread < 0.35:
        return False, {"column_switch_ratio": 0.0, "column_balance": round(balance, 4)}

    switches = sum(1 for i in range(1, len(labels)) if labels[i] != labels[i - 1])
    switch_ratio = switches / max(1, len(labels) - 1)
    mean_height = median(y_spans) if y_spans else 20.0
    vertical_overlap = 0
    comparable = 0
    for i in range(1, len(lines)):
        if labels[i] == labels[i - 1]:
            continue
        comparable += 1
        gap = lines[i].bbox_2d[1] - lines[i - 1].bbox_2d[3]
        if abs(gap) <= mean_height * 0.8:
            vertical_overlap += 1
    overlap_ratio = vertical_overlap / comparable if comparable else 0.0
    risk = switch_ratio > 0.45 and overlap_ratio > 0.35
    return risk, {
        "column_switch_ratio": round(switch_ratio, 4),
        "column_balance": round(balance, 4),
        "cross_column_overlap_ratio": round(overlap_ratio, 4),
    }


def evaluate_structure_quality(lines: Sequence[Line], paragraphs: Sequence[str], text: str) -> Dict[str, Any]:
    issues: List[str] = []
    html_tag_count = len(_HTML_TAG_RE.findall(text))
    has_markdown_heading = bool(_MD_HEADING_RE.search(text))
    mixed_md_html = html_tag_count > 0 and has_markdown_heading
    heading_multi_hash_lines = 0
    heading_inline_lines = 0
    for line in lines:
        hash_count = line.text.count("##")
        if hash_count >= 2:
            heading_multi_hash_lines += 1
        if "##" in line.text and not line.text.strip().startswith("##"):
            heading_inline_lines += 1

    long_paragraph_count = 0
    no_punctuation_paragraph_count = 0
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped:
            continue
        if len(para_stripped) > 500:
            long_paragraph_count += 1
        if len(para_stripped) > 120 and not _PUNCT_RE.search(para_stripped):
            no_punctuation_paragraph_count += 1

    order_risk, order_metrics = _column_interleave_risk(lines)

    if html_tag_count > 0:
        issues.append("html_tag_detected")
    if mixed_md_html:
        issues.append("markdown_html_mixed")
    if heading_multi_hash_lines > 0:
        issues.append("heading_multi_hash_same_line")
    if heading_inline_lines > 0:
        issues.append("heading_not_separated")
    if long_paragraph_count > 0:
        issues.append("paragraph_too_long")
    if no_punctuation_paragraph_count > 0:
        issues.append("paragraph_missing_punctuation")
    if order_risk:
        issues.append("reading_order_column_risk")

    penalty = 0.0
    penalty += min(0.18, html_tag_count * 0.02)
    penalty += 0.08 if mixed_md_html else 0.0
    penalty += min(0.2, heading_multi_hash_lines * 0.1)
    penalty += min(0.15, heading_inline_lines * 0.08)
    penalty += min(0.22, long_paragraph_count * 0.08)
    penalty += min(0.2, no_punctuation_paragraph_count * 0.08)
    penalty += 0.22 if order_risk else 0.0

    return {
        "score": max(0.0, min(1.0, 1.0 - penalty)),
        "issues": sorted(set(issues)),
        "metrics": {
            "html_tag_count": float(html_tag_count),
            "mixed_md_html": float(1 if mixed_md_html else 0),
            "heading_multi_hash_lines": float(heading_multi_hash_lines),
            "heading_inline_lines": float(heading_inline_lines),
            "long_paragraph_count": float(long_paragraph_count),
            "no_punctuation_paragraph_count": float(no_punctuation_paragraph_count),
            **order_metrics,
        },
    }


def _chunks_to_raw_blocks(page: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = page.get("chunks")
    if not isinstance(chunks, list):
        return []
    raw_blocks: List[Dict[str, Any]] = []
    for i, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            continue
        bbox_px = chunk.get("bboxPx")
        if not isinstance(bbox_px, dict):
            continue
        raw_blocks.append(
            {
                "index": int(chunk.get("index", i)),
                "label": str(chunk.get("label", "text")),
                "content": str(chunk.get("content", "")).strip(),
                "bbox_2d": [
                    int(bbox_px.get("x1", 0)),
                    int(bbox_px.get("y1", 0)),
                    int(bbox_px.get("x2", 0)),
                    int(bbox_px.get("y2", 0)),
                ],
            }
        )
    return raw_blocks


def evaluate_ocr_quality(ocr_blocks_by_page: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    page_reports: List[Dict[str, Any]] = []
    quality_scores: List[float] = []
    structure_scores: List[float] = []
    layout_scores: List[float] = []

    for fallback_page_no, page in enumerate(ocr_blocks_by_page, start=1):
        page_no = int(page.get("pageNo", fallback_page_no))
        raw_blocks = _chunks_to_raw_blocks(page)
        blocks = normalize_blocks(raw_blocks, page_no)
        lines = merge_blocks_to_lines(blocks)
        paragraphs = merge_lines_to_paragraphs(lines)
        text = "\n\n".join(paragraphs).strip() if paragraphs else rebuild_page_text(lines)
        quality = evaluate_page_quality(blocks, lines, text)
        structure = evaluate_structure_quality(lines, paragraphs, text)
        layout_metrics, layout_issues, layout_score = _collect_layout_metrics(blocks)
        final_score = round((quality["score"] * 0.5 + structure["score"] * 0.2 + layout_score * 0.3), 4)
        report = {
            "pageNo": page_no,
            "blockCount": len(blocks),
            "lineCount": len(lines),
            "paragraphCount": len(paragraphs),
            "textLength": len("".join(text.split())),
            "qualityScore": round(float(quality["score"]), 4),
            "structureScore": round(float(structure["score"]), 4),
            "layoutScore": layout_score,
            "finalScore": final_score,
            "issues": quality["issues"],
            "structureIssues": structure["issues"],
            "layoutIssues": layout_issues,
            "metrics": quality["metrics"],
            "structureMetrics": structure["metrics"],
            "layoutMetrics": layout_metrics,
        }
        page_reports.append(report)
        quality_scores.append(float(quality["score"]))
        structure_scores.append(float(structure["score"]))
        layout_scores.append(layout_score)

    document_report = {
        "pageCount": len(page_reports),
        "avgQualityScore": round(sum(quality_scores) / len(quality_scores), 4) if quality_scores else 0.0,
        "avgStructureScore": round(sum(structure_scores) / len(structure_scores), 4) if structure_scores else 0.0,
        "avgLayoutScore": round(sum(layout_scores) / len(layout_scores), 4) if layout_scores else 0.0,
        "avgFinalScore": round(sum(p["finalScore"] for p in page_reports) / len(page_reports), 4) if page_reports else 0.0,
        "pagesWithIssues": sum(1 for p in page_reports if p["issues"] or p["structureIssues"] or p["layoutIssues"]),
        "pagesWithLayoutIssues": sum(1 for p in page_reports if p["layoutIssues"]),
        "layoutSummary": {
            "highEmptyBlockPages": sum(1 for p in page_reports if "high_empty_block_ratio" in p["layoutIssues"]),
            "fragmentedPages": sum(1 for p in page_reports if "layout_fragmentation" in p["layoutIssues"]),
            "nestedBoxPages": sum(1 for p in page_reports if "nested_bbox_anomaly" in p["layoutIssues"]),
            "overlapPages": sum(1 for p in page_reports if "heavy_bbox_overlap" in p["layoutIssues"]),
            "coverageAnomalyPages": sum(
                1
                for p in page_reports
                if "low_layout_coverage" in p["layoutIssues"] or "high_layout_coverage" in p["layoutIssues"]
            ),
        },
        "pages": page_reports,
    }
    return document_report
