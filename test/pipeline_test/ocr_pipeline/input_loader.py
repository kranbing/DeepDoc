from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
PDF_EXTENSIONS = {".pdf"}


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() in PDF_EXTENSIONS


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def load_image(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def render_pdf_pages(path: Path, dpi: int = 200, pages: Optional[List[int]] = None) -> List[Image.Image]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError("pypdfium2 is required for PDF processing. Install with: pip install pypdfium2") from exc

    pdf = pdfium.PdfDocument(str(path))
    scale = dpi / 72.0

    images: List[Image.Image] = []
    page_indices = pages if pages is not None else list(range(len(pdf)))

    for page_idx in page_indices:
        page = pdf[page_idx]
        bitmap = page.render(scale=scale)  # type: ignore[arg-type]
        pil_image = bitmap.to_pil().convert("RGB")
        images.append(pil_image)

    return images
