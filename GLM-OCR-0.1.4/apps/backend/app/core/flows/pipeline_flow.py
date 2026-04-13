"""
Pipeline处理流程实现

流程：PDF转图片 -> 版面分析和OCR识别 -> 结果合并
"""

import os
from typing import Dict, Any
from pathlib import Path

from app.core.flows.base import FlowFactory, TaskProcessingFlow, ProcessingContext
from app.core.steps.pdf_to_image import PdfToImageStepInput, pdf_to_image
from app.core.steps.layout_ocr import LayoutOcrStepInput, layout_and_ocr
from app.core.steps.merge_results import MergeResultsStepInput, merge_results

from app.utils.logger import logger
from app.utils.config import settings


class PipelineFlow(TaskProcessingFlow):
    """
    Pipeline处理流程

    处理步骤：
    1. PDF转图片 (0-20%)
    2. 版面分析和OCR (20-85%)
    3. 结果合并 (85-100%)
    """

    # 步骤权重配置
    STEP_WEIGHTS = {
        "pdf_to_image": 0.20,  # PDF转图片 占20%
        "layout_and_ocr": 0.65,  # 版面分析+OCR 占65%
        "result_merge": 0.15,  # 结果合并 占15%
    }

    async def process(self) -> Dict[str, Any]:
        """执行完整的Pipeline流程"""

        logger.info(f"[{self.context.task_id}] Starting Pipeline flow")

        # 准备输出目录
        output_dir = self._prepare_output_dir()
        self.context.set_output_dir(output_dir)

        # 步骤1: PDF转图片 (0-20%)
        pdf_result = await self._step_pdf_to_image()
        self.context.set("pdf_result", pdf_result)
        self.context.set("metadata", pdf_result.get("metadata"))
        self.context.metadata = pdf_result.get("metadata")
        # 步骤2: 版面分析和OCR处理 (20-85%)
        ocr_results = await self._step_layout_and_ocr(pdf_result)
        self.context.set("ocr_results", ocr_results)

        # 步骤3: 结果合并 (85-100%)
        final_result = await self._step_result_merge(ocr_results)

        logger.info(f"[{self.context.task_id}] Pipeline flow completed")

        return {
            "success": True,
            "md_output_path": final_result["md_output_path"],
            "json_output_path": final_result["json_output_path"],
            "output_files": final_result.get("output_files", []),
            "metadata": final_result.get("metadata", {}),
        }

    def _prepare_output_dir(self) -> str:
        """准备输出目录"""

        # 创建输出目录：output/<task_id>/
        output_base = Path(settings.OUTPUT_DIR) / self.context.task_id
        output_base.mkdir(parents=True, exist_ok=True)

        return str(output_base)

    async def _step_pdf_to_image(self) -> Dict[str, Any]:
        """步骤1: PDF转图片"""
        step_name = "pdf_to_image"
        logger.info(f"[{self.context.task_id}] Starting step: {step_name}")

        await self.update_progress(
            step_name=step_name,
            progress=0.0,
            overall_progress=0.0,
            message="Converting PDF to images",
        )

        # 实际处理逻辑
        result = await pdf_to_image(
            context=self.context,
            input=PdfToImageStepInput(
                file_path=self.context.file_path,
                output_dir=self.context.get_output_dir(),
                dpi=self.context.ocr_config.get("dpi", 200),
                format=self.context.ocr_config.get("image_format", "png"),
            ),
            progress_callback=lambda p, msg: self.update_progress(
                step_name=step_name,
                progress=p,
                overall_progress=p * self.STEP_WEIGHTS["pdf_to_image"],
                message=msg,
            ),
        )

        await self.update_progress(
            step_name=step_name,
            progress=100.0,
            overall_progress=self.STEP_WEIGHTS["pdf_to_image"] * 100,
            message=f"Converted {result['page_count']} pages to images",
        )

        return result

    async def _step_layout_and_ocr(self, pdf_result: Dict[str, Any]) -> Dict[str, Any]:
        """步骤2: 版面分析和OCR处理"""
        step_name = "layout_and_ocr"
        logger.info(f"[{self.context.task_id}] Starting step: {step_name}")

        base_progress = self.STEP_WEIGHTS["pdf_to_image"] * 100  # 从20%开始

        await self.update_progress(
            step_name=step_name,
            progress=0.0,
            overall_progress=base_progress,
            message="Starting layout analysis and OCR",
        )

        # 实际处理逻辑
        result = await layout_and_ocr(
            context=self.context,
            input=LayoutOcrStepInput(
                image_files_path=pdf_result.get("output_files", []),
                page_count=pdf_result.get("page_count", 0),
                images_dir=pdf_result.get("images_dir", ""),
            ),
            progress_callback=lambda p, msg: self.update_progress(
                step_name=step_name,
                progress=p,
                overall_progress=base_progress
                + p * self.STEP_WEIGHTS["layout_and_ocr"],
                message=msg,
            ),
        )

        await self.update_progress(
            step_name=step_name,
            progress=100.0,
            overall_progress=(
                self.STEP_WEIGHTS["pdf_to_image"] + self.STEP_WEIGHTS["layout_and_ocr"]
            )
            * 100,
            message="Layout analysis and OCR completed",
        )

        return result

    async def _step_result_merge(self, ocr_results: Dict[str, Any]) -> Dict[str, Any]:
        """步骤3: 结果合并"""
        step_name = "result_merge"
        logger.info(f"[{self.context.task_id}] Starting step: {step_name}")

        base_progress = (
            self.STEP_WEIGHTS["pdf_to_image"] + self.STEP_WEIGHTS["layout_and_ocr"]
        ) * 100  # 从85%开始

        await self.update_progress(
            step_name=step_name,
            progress=0.0,
            overall_progress=base_progress,
            message="Merging results",
        )
        input = MergeResultsStepInput(
            ocr_result_path=ocr_results.get("ocr_result_file"),
        )
        # 实际处理逻辑
        result = await merge_results(
            context=self.context,
            input=input,
            progress_callback=lambda p, msg: self.update_progress(
                step_name=step_name,
                progress=p,
                overall_progress=base_progress + p * self.STEP_WEIGHTS["result_merge"],
                message=msg,
            ),
        )

        await self.update_progress(
            step_name=step_name,
            progress=100.0,
            overall_progress=100.0,
            message="Results merged",
        )

        return result
