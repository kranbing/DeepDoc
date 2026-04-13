from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence

from PIL import Image, ImageDraw

from .types import OCRBlock


def save_error_visualization(
    image: Image.Image,
    blocks: Sequence[OCRBlock],
    bad_indices: Iterable[int],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bad_set = set(bad_indices)
    draw_image = image.copy()
    draw = ImageDraw.Draw(draw_image)

    for i, block in enumerate(blocks):
        color = (220, 30, 30) if i in bad_set else (40, 180, 80)
        x1, y1, x2, y2 = block.bbox_2d
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

    draw_image.save(output_path)
