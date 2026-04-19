from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from .adapters import OCRAdapter


class CustomBlackBoxAdapter(OCRAdapter):
    """Template adapter for integrating a custom OCR service/model.

    Replace the TODOs with your real model invocation logic.
    """

    def ocr_image(self, image: Image.Image, page: int = 1) -> List[Dict[str, Any]]:
        # TODO: call your OCR model here and return a list of dict blocks.
        # Each block should include: index, label, content, bbox_2d.
        return []

    def ocr_pdf(self, pdf_path: Path) -> Optional[List[List[Dict[str, Any]]]]:
        # TODO: if your backend supports PDF directly, return page-wise blocks.
        # Return None to let the pipeline fallback to PDF->image rendering.
        return None
