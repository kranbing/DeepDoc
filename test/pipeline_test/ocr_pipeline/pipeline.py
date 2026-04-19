from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image

from .adapters import OCRAdapter
from .input_loader import is_image, is_pdf, load_image, render_pdf_pages
from .logger import setup_logger
from .postprocess import (
    merge_lines_to_paragraphs,
    merge_blocks_to_lines,
    normalize_blocks,
    rebuild_page_text,
    sort_blocks_reading_order,
)
from .quality import evaluate_page_quality
from .structure_quality import evaluate_structure_quality
from .retry_strategies import (
    enhanced_image_variants,
    low_quality_block_indices,
    retry_local_regions,
    retry_pdf_single_page,
)
from .types import OCRBlock, PageResult, PipelineResult
from .visualization import save_error_visualization


@dataclass
class PipelineConfig:
    score_threshold: float = 0.7
    final_score_threshold: float = 0.85
    structure_score_threshold: float = 0.8
    quality_weight: float = 0.7
    structure_weight: float = 0.3
    max_retries: int = 3
    pdf_dpi: int = 200
    retry_pdf_dpi: int = 280
    save_visualization: bool = True
    output_dir: str = "./output/pipeline"


class OCRPipeline:
    def __init__(self, adapter: OCRAdapter, config: Optional[PipelineConfig] = None) -> None:
        self.adapter = adapter
        self.config = config or PipelineConfig()

        self.output_dir = Path(self.config.output_dir).resolve()
        self.log_dir = self.output_dir / "logs"
        self.logger = setup_logger(self.log_dir)

    def _compute_final_score(self, quality_score: float, structure_score: float) -> float:
        q_w = max(0.0, self.config.quality_weight)
        s_w = max(0.0, self.config.structure_weight)
        denom = q_w + s_w
        if denom <= 0:
            q_w, s_w, denom = 0.7, 0.3, 1.0
        return (q_w * quality_score + s_w * structure_score) / denom

    def _need_retry(self, page_result: PageResult) -> bool:
        return (
            page_result.final_score < self.config.final_score_threshold
            or page_result.structure_score < self.config.structure_score_threshold
        )

    def _page_from_blocks(self, page: int, raw_blocks: Sequence[Dict[str, Any]], duration_sec: float = 0.0) -> PageResult:
        blocks = normalize_blocks(raw_blocks, page=page)
        blocks = sort_blocks_reading_order(blocks)
        lines = merge_blocks_to_lines(blocks)
        paragraphs = merge_lines_to_paragraphs(lines)
        text = "\n\n".join(paragraphs).strip() if paragraphs else rebuild_page_text(lines)

        quality = evaluate_page_quality(blocks=blocks, lines=lines, text=text)
        structure = evaluate_structure_quality(blocks=blocks, lines=lines, paragraphs=paragraphs, text=text)
        final_score = self._compute_final_score(quality.score, structure.score)
        return PageResult(
            page=page,
            text=text,
            lines=lines,
            paragraphs=paragraphs,
            blocks=blocks,
            quality_score=quality.score,
            structure_score=structure.score,
            final_score=final_score,
            issues=quality.issues,
            structure_issues=structure.issues,
            metrics=quality.metrics,
            structure_metrics=structure.metrics,
            retry_count=0,
            duration_sec=duration_sec,
        )

    def _retry_page(
        self,
        page_result: PageResult,
        image: Optional[Image.Image],
        source_path: Path,
        is_pdf_source: bool,
    ) -> PageResult:
        best = page_result
        retry_count = 0

        if not self._need_retry(best):
            return best

        page_num = page_result.page

        if image is not None and retry_count < self.config.max_retries:
            for name, variant in enhanced_image_variants(image):
                if retry_count >= self.config.max_retries or not self._need_retry(best):
                    break
                retry_count += 1
                candidate_blocks = self.adapter.ocr_image(variant, page=page_num)
                candidate = self._page_from_blocks(page=page_num, raw_blocks=candidate_blocks)
                self.logger.info(
                    "retry strategy=image_enhance variant=%s page=%s quality=%.4f structure=%.4f final=%.4f",
                    name,
                    page_num,
                    candidate.quality_score,
                    candidate.structure_score,
                    candidate.final_score,
                )
                if (
                    candidate.final_score > best.final_score
                    or (
                        abs(candidate.final_score - best.final_score) < 1e-6
                        and candidate.structure_score > best.structure_score
                    )
                ):
                    best = candidate

        if image is not None and retry_count < self.config.max_retries and self._need_retry(best):
            retry_count += 1
            updated_blocks, replaced = retry_local_regions(
                adapter=self.adapter,
                image=image,
                blocks=best.blocks,
                page=page_num,
            )
            candidate = self._page_from_blocks(page=page_num, raw_blocks=[b.to_dict() for b in updated_blocks])
            self.logger.info(
                "retry strategy=local_regions page=%s replaced=%s quality=%.4f structure=%.4f final=%.4f",
                page_num,
                replaced,
                candidate.quality_score,
                candidate.structure_score,
                candidate.final_score,
            )
            if (
                candidate.final_score > best.final_score
                or (
                    abs(candidate.final_score - best.final_score) < 1e-6
                    and candidate.structure_score > best.structure_score
                )
            ):
                best = candidate

        if (
            is_pdf_source
            and retry_count < self.config.max_retries
            and self._need_retry(best)
        ):
            retry_count += 1
            candidate_blocks = retry_pdf_single_page(
                adapter=self.adapter,
                pdf_path=source_path,
                page_index=page_num - 1,
                dpi=self.config.retry_pdf_dpi,
            )
            candidate = self._page_from_blocks(page=page_num, raw_blocks=candidate_blocks)
            self.logger.info(
                "retry strategy=pdf_single_page page=%s quality=%.4f structure=%.4f final=%.4f",
                page_num,
                candidate.quality_score,
                candidate.structure_score,
                candidate.final_score,
            )
            if (
                candidate.final_score > best.final_score
                or (
                    abs(candidate.final_score - best.final_score) < 1e-6
                    and candidate.structure_score > best.structure_score
                )
            ):
                best = candidate

        best.retry_count = retry_count
        return best

    def process_document(self, input_path: str, doc_id: Optional[str] = None) -> PipelineResult:
        start = time.perf_counter()
        source = Path(input_path).resolve()
        if not source.exists():
            raise FileNotFoundError(f"Input file not found: {source}")

        doc_id = doc_id or f"doc_{uuid.uuid4().hex[:10]}"
        doc_dir = self.output_dir / doc_id
        viz_dir = doc_dir / "error_visualizations"
        doc_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info("start doc_id=%s source=%s", doc_id, source)

        pdf_source = is_pdf(source)
        image_source = is_image(source)
        if not (pdf_source or image_source):
            raise ValueError("Only image/PDF inputs are supported")

        page_images: List[Image.Image] = []
        raw_pages: List[List[Dict[str, Any]]] = []

        if pdf_source:
            try:
                maybe_pages = self.adapter.ocr_pdf(source)
                if maybe_pages:
                    raw_pages = maybe_pages
            except Exception as exc:
                self.logger.warning("adapter.ocr_pdf failed, fallback to per-page image OCR: %s", exc)

            page_images = render_pdf_pages(source, dpi=self.config.pdf_dpi)
            if not raw_pages:
                raw_pages = [self.adapter.ocr_image(img, page=i + 1) for i, img in enumerate(page_images)]
            elif len(page_images) < len(raw_pages):
                # Rare fallback: ensure same length for visualization/retry.
                page_images = render_pdf_pages(source, dpi=self.config.pdf_dpi)

        else:
            image = load_image(source)
            page_images = [image]
            raw_pages = [self.adapter.ocr_image(image, page=1)]

        pages: List[PageResult] = []
        error_samples: List[Dict[str, Any]] = []

        for idx, raw_blocks in enumerate(raw_pages, start=1):
            page_start = time.perf_counter()
            page_image = page_images[idx - 1] if idx - 1 < len(page_images) else None

            page_result = self._page_from_blocks(page=idx, raw_blocks=raw_blocks)
            if self._need_retry(page_result):
                page_result = self._retry_page(
                    page_result=page_result,
                    image=page_image,
                    source_path=source,
                    is_pdf_source=pdf_source,
                )

            page_result.duration_sec = time.perf_counter() - page_start
            pages.append(page_result)

            bad_indices = low_quality_block_indices(page_result.blocks)
            if page_result.issues or page_result.structure_issues:
                error_samples.append(
                    {
                        "page": idx,
                        "issues": page_result.issues,
                        "structure_issues": page_result.structure_issues,
                        "quality_score": round(page_result.quality_score, 4),
                        "structure_score": round(page_result.structure_score, 4),
                        "final_score": round(page_result.final_score, 4),
                    }
                )

            if (
                self.config.save_visualization
                and page_image is not None
                and (bad_indices or page_result.issues or page_result.structure_issues)
            ):
                viz_path = viz_dir / f"page_{idx:03d}.png"
                save_error_visualization(page_image, page_result.blocks, bad_indices, viz_path)

        total_time = time.perf_counter() - start
        success_pages = sum(
            1
            for p in pages
            if p.final_score >= self.config.final_score_threshold
            and p.structure_score >= self.config.structure_score_threshold
        )
        total_retries = sum(p.retry_count for p in pages)
        avg_quality_score = (sum(p.quality_score for p in pages) / len(pages)) if pages else 0.0
        avg_structure_score = (sum(p.structure_score for p in pages) / len(pages)) if pages else 0.0
        avg_score = (sum(p.final_score for p in pages) / len(pages)) if pages else 0.0

        stats = {
            "total_time_sec": round(total_time, 4),
            "pages": len(pages),
            "total_pages": len(pages),
            "retry_times": total_retries,
            "success_rate": round(success_pages / len(pages), 4) if pages else 0.0,
            "avg_score": round(avg_score, 4),
            "avg_quality_score": round(avg_quality_score, 4),
            "avg_structure_score": round(avg_structure_score, 4),
            "per_page_time_sec": [round(p.duration_sec, 4) for p in pages],
            "error_samples": error_samples,
        }

        result = PipelineResult(doc_id=doc_id, pages=pages, stats=stats)
        output_json = doc_dir / "pipeline_result.json"
        output_json.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info("done doc_id=%s output=%s", doc_id, output_json)

        return result
