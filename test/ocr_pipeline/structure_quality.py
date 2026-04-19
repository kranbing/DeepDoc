from __future__ import annotations

import re
from statistics import median
from typing import Dict, List, Sequence, Tuple

from .types import Line, OCRBlock, StructureResult


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MD_HEADING_RE = re.compile(r"(^|\n)\s{0,3}#{1,6}\s+", re.M)
_PUNCT_RE = re.compile(r"[。！？；：.!?;:]")


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

    switches = 0
    for i in range(1, len(labels)):
        if labels[i] != labels[i - 1]:
            switches += 1

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

    overlap_ratio = (vertical_overlap / comparable) if comparable else 0.0
    risk = switch_ratio > 0.45 and overlap_ratio > 0.35

    return risk, {
        "column_switch_ratio": round(switch_ratio, 4),
        "column_balance": round(balance, 4),
        "cross_column_overlap_ratio": round(overlap_ratio, 4),
    }


def evaluate_structure_quality(
    blocks: Sequence[OCRBlock],
    lines: Sequence[Line],
    paragraphs: Sequence[str],
    text: str,
) -> StructureResult:
    issues: List[str] = []
    metrics: Dict[str, float] = {}

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

    score = max(0.0, min(1.0, 1.0 - penalty))

    metrics.update(
        {
            "html_tag_count": float(html_tag_count),
            "mixed_md_html": float(1 if mixed_md_html else 0),
            "heading_multi_hash_lines": float(heading_multi_hash_lines),
            "heading_inline_lines": float(heading_inline_lines),
            "long_paragraph_count": float(long_paragraph_count),
            "no_punctuation_paragraph_count": float(no_punctuation_paragraph_count),
        }
    )
    metrics.update(order_metrics)

    return StructureResult(score=score, issues=sorted(set(issues)), metrics=metrics)
