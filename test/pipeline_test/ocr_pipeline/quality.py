from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Sequence

from .postprocess import block_garbled_ratio
from .types import Line, OCRBlock, QualityResult


_MOJIBAKE_MARKERS = {
    "锟",
    "锛",
    "銆",
    "鈥",
    "鏄",
    "鐨",
    "鍦",
    "鎴",
    "鍙",
    "��",
}


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


def evaluate_page_quality(blocks: Sequence[OCRBlock], lines: Sequence[Line], text: str) -> QualityResult:
    issues: List[str] = []
    metrics: Dict[str, float] = {}

    total_blocks = len(blocks)
    total_lines = len(lines)

    non_empty_blocks = [b for b in blocks if b.content.strip()]
    empty_ratio = 1.0 if total_blocks == 0 else 1.0 - (len(non_empty_blocks) / total_blocks)

    text_no_space = "".join(text.split())
    char_len = len(text_no_space)

    garbled_ratios = [block_garbled_ratio(b.content) for b in non_empty_blocks]
    garbled_ratio = sum(garbled_ratios) / len(garbled_ratios) if garbled_ratios else 1.0

    marker_hits = 0
    for marker in _MOJIBAKE_MARKERS:
        marker_hits += text.count(marker)
    mojibake_ratio = marker_hits / max(1, len(text_no_space))

    overlap_pairs = 0
    heavy_overlap_pairs = 0
    for a, b in combinations(blocks, 2):
        overlap_pairs += 1
        if _iou(a.bbox_2d, b.bbox_2d) > 0.5:
            heavy_overlap_pairs += 1
    overlap_ratio = (heavy_overlap_pairs / overlap_pairs) if overlap_pairs else 0.0

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

    score = max(0.0, min(1.0, 1.0 - penalty))

    metrics.update(
        {
            "char_len": float(char_len),
            "line_count": float(total_lines),
            "block_count": float(total_blocks),
            "garbled_ratio": round(garbled_ratio, 4),
            "mojibake_ratio": round(mojibake_ratio, 4),
            "empty_ratio": round(empty_ratio, 4),
            "overlap_ratio": round(overlap_ratio, 4),
            "line_count_anomaly": round(line_count_anomaly, 4),
            "text_length_penalty": round(text_length_penalty, 4),
        }
    )

    dedup_issues = sorted(set(issues))
    return QualityResult(score=score, issues=dedup_issues, metrics=metrics)
