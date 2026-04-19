from __future__ import annotations

from pathlib import Path
import importlib
from typing import List, Sequence, Tuple

from PIL import Image, ImageEnhance, ImageOps
import numpy as np

from .adapters import OCRAdapter
from .input_loader import render_pdf_pages
from .postprocess import block_garbled_ratio
from .types import OCRBlock


def enhanced_image_variants(image: Image.Image) -> List[Tuple[str, Image.Image]]:
    variants: List[Tuple[str, Image.Image]] = []

    gray = ImageOps.grayscale(image)
    variants.append(("gray", gray.convert("RGB")))

    contrast = ImageEnhance.Contrast(gray).enhance(1.8)
    variants.append(("contrast", contrast.convert("RGB")))

    try:
        cv2 = importlib.import_module("cv2")

        arr = np.array(gray)
        binary = cv2.adaptiveThreshold(
            arr,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            25,
            15,
        )
        variants.append(("binary", Image.fromarray(binary).convert("RGB")))
    except Exception:
        arr = np.array(gray)
        binary = (arr > 165).astype("uint8") * 255
        variants.append(("binary", Image.fromarray(binary).convert("RGB")))

    return variants


def low_quality_block_indices(blocks: Sequence[OCRBlock]) -> List[int]:
    bad: List[int] = []
    for i, block in enumerate(blocks):
        text = block.content.strip()
        if not text:
            bad.append(i)
            continue

        garbled = block_garbled_ratio(text)
        if garbled > 0.45 or len(text) < 2:
            bad.append(i)

    return sorted(set(bad))


def _crop_region(image: Image.Image, bbox: List[int], pad: int = 8) -> Image.Image:
    w, h = image.size
    x1, y1, x2, y2 = bbox
    cx1 = max(0, x1 - pad)
    cy1 = max(0, y1 - pad)
    cx2 = min(w, x2 + pad)
    cy2 = min(h, y2 + pad)
    return image.crop((cx1, cy1, cx2, cy2)).convert("RGB")


def retry_local_regions(adapter: OCRAdapter, image: Image.Image, blocks: List[OCRBlock], page: int) -> Tuple[List[OCRBlock], int]:
    updated = list(blocks)
    bad_ids = low_quality_block_indices(updated)
    replaced = 0

    for i in bad_ids:
        crop = _crop_region(image, updated[i].bbox_2d, pad=10)
        crop_blocks = adapter.ocr_image(crop, page=page)
        candidate_texts = [str(b.get("content", "")).strip() for b in crop_blocks if str(b.get("content", "")).strip()]
        if not candidate_texts:
            continue

        best_text = max(candidate_texts, key=len)
        if len(best_text) > len(updated[i].content.strip()):
            updated[i].content = best_text
            replaced += 1

    return updated, replaced


def retry_pdf_single_page(adapter: OCRAdapter, pdf_path: Path, page_index: int, dpi: int = 260) -> List[dict]:
    images = render_pdf_pages(pdf_path, dpi=dpi, pages=[page_index])
    if not images:
        return []
    return adapter.ocr_image(images[0], page=page_index + 1)
