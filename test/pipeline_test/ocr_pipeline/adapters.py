from __future__ import annotations

import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from PIL import Image


class OCRAdapter(ABC):
    @abstractmethod
    def ocr_image(self, image: Image.Image, page: int = 1) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def ocr_pdf(self, pdf_path: Path) -> Optional[List[List[Dict[str, Any]]]]:
        return None

    def close(self) -> None:
        return None


class GlmOcrAdapter(OCRAdapter):
    def __init__(
        self,
        mode: Optional[str] = None,
        api_key: Optional[str] = None,
        config_path: Optional[str] = None,
        env_file: Optional[str] = None,
        log_level: str = "INFO",
    ) -> None:
        from glmocr import GlmOcr

        self._parser = GlmOcr(
            mode=mode,
            api_key=api_key,
            config_path=config_path,
            env_file=env_file,
            log_level=log_level,
        )

    def close(self) -> None:
        if self._parser is not None:
            self._parser.close()

    def _to_page_blocks(self, result_json: Any) -> List[List[Dict[str, Any]]]:
        if isinstance(result_json, list):
            if not result_json:
                return [[]]
            if isinstance(result_json[0], dict):
                return [result_json]
            if isinstance(result_json[0], list):
                return result_json
        return [[]]

    def ocr_image(self, image: Image.Image, page: int = 1) -> List[Dict[str, Any]]:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = Path(f.name)
        try:
            image.save(temp_path)
            parsed = self._parser.parse(str(temp_path))
            pages = self._to_page_blocks(parsed.json_result)
            return pages[0] if pages else []
        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass

    def ocr_pdf(self, pdf_path: Path) -> Optional[List[List[Dict[str, Any]]]]:
        parsed = self._parser.parse(str(pdf_path))
        return self._to_page_blocks(parsed.json_result)


class MockOcrAdapter(OCRAdapter):
    def __init__(self, noisy: bool = False) -> None:
        self.noisy = noisy

    def _make_block(self, idx: int, text: str, bbox: List[int]) -> Dict[str, Any]:
        return {
            "index": idx,
            "label": "text",
            "content": text,
            "bbox_2d": bbox,
        }

    def ocr_image(self, image: Image.Image, page: int = 1) -> List[Dict[str, Any]]:
        w, h = image.size
        left_x1, left_x2 = int(w * 0.06), int(w * 0.45)
        right_x1, right_x2 = int(w * 0.55), int(w * 0.94)

        if self.noisy:
            title = "<div> ## 模拟标题A ## 模拟标题B </div>"
            p1 = "这里是一段非常长的模拟文本" + "测试" * 260
            p2 = "另一段文本没有任何标点它会用于触发结构评分中的段落异常检测"
        else:
            title = "模拟文档标题"
            p1 = "这是用于 Pipeline 调试的 mock OCR 文本。它用于验证后处理、评分与重试流程。"
            p2 = "我们可以在不依赖真实 OCR 服务的前提下，快速回归测试整个系统。"

        blocks = [
            self._make_block(0, title, [int(w * 0.2), int(h * 0.06), int(w * 0.8), int(h * 0.12)]),
            self._make_block(1, p1, [left_x1, int(h * 0.18), left_x2, int(h * 0.58)]),
            self._make_block(2, p2, [right_x1, int(h * 0.18), right_x2, int(h * 0.52)]),
            self._make_block(3, "第 %d 页 mock 结束。" % page, [left_x1, int(h * 0.72), left_x2, int(h * 0.78)]),
        ]
        return blocks

    def ocr_pdf(self, pdf_path: Path) -> Optional[List[List[Dict[str, Any]]]]:
        from .input_loader import render_pdf_pages

        images = render_pdf_pages(pdf_path, dpi=150)
        return [self.ocr_image(img, page=i + 1) for i, img in enumerate(images)]


class FailoverOCRAdapter(OCRAdapter):
    def __init__(self, primary: OCRAdapter, fallback: OCRAdapter) -> None:
        self.primary = primary
        self.fallback = fallback

    def ocr_image(self, image: Image.Image, page: int = 1) -> List[Dict[str, Any]]:
        try:
            blocks = self.primary.ocr_image(image, page=page)
            if blocks:
                return blocks
        except Exception:
            pass
        return self.fallback.ocr_image(image, page=page)

    def ocr_pdf(self, pdf_path: Path) -> Optional[List[List[Dict[str, Any]]]]:
        try:
            pages = self.primary.ocr_pdf(pdf_path)
            if pages and any(page for page in pages):
                return pages
        except Exception:
            pass

        fallback_pages = self.fallback.ocr_pdf(pdf_path)
        if fallback_pages is not None:
            return fallback_pages

        from .input_loader import render_pdf_pages

        images = render_pdf_pages(pdf_path, dpi=150)
        return [self.fallback.ocr_image(img, page=i + 1) for i, img in enumerate(images)]

    def close(self) -> None:
        try:
            self.primary.close()
        finally:
            self.fallback.close()
