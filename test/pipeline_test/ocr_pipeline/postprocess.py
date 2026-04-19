from __future__ import annotations

import math
from statistics import median
from typing import Dict, List, Sequence, Tuple

from .types import Line, OCRBlock


def normalize_blocks(raw_blocks: Sequence[Dict], page: int) -> List[OCRBlock]:
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

        index = int(block.get("index", i))
        label = str(block.get("label", "text"))
        content = str(block.get("content", "")).strip()

        meta = {k: v for k, v in block.items() if k not in {"index", "label", "content", "bbox_2d"}}
        normalized.append(
            OCRBlock(
                index=index,
                label=label,
                content=content,
                bbox_2d=[x1, y1, x2, y2],
                page=page,
                meta=meta,
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

            # Avoid merging across distant columns that only share similar y.
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

        lines.append(
            Line(
                text=text,
                bbox_2d=[x1, y1, x2, y2],
                block_indices=[b.index for b in group],
            )
        )

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
    paragraphs = merge_lines_to_paragraphs(lines)
    return "\n\n".join(paragraphs).strip()


def union_bbox(bboxes: Sequence[List[int]]) -> List[int]:
    if not bboxes:
        return [0, 0, 0, 0]
    return [
        min(bb[0] for bb in bboxes),
        min(bb[1] for bb in bboxes),
        max(bb[2] for bb in bboxes),
        max(bb[3] for bb in bboxes),
    ]


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
