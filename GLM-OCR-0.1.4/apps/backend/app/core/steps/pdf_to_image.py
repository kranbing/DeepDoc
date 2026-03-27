"""
PDF转图片步骤 - 适配app_v2
"""

import os
import json
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import sys

from app.core.flows.base import ProcessingContext
from app.utils.logger import logger
from app.utils.converters import FileConverterService


class PdfToImageStepInput:
    file_path: str
    output_dir: str
    dpi: int
    format: str

    def __init__(
        self,
        file_path: str,
        output_dir: str,
        dpi: int = 200,
        format: str = "png",
    ) -> None:
        self.file_path = file_path
        self.output_dir = output_dir
        self.dpi = dpi
        self.format = format


async def pdf_to_image(
    context: ProcessingContext,
    input: PdfToImageStepInput,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Any]:
    """
    将PDF文件转换为图片

    Args:
        file_path: PDF文件路径
        output_dir: 输出目录
        dpi: DPI设置
        format: 输出格式 (png, jpg等)
        progress_callback: 进度回调函数

    Returns:
        Dict[str, Any]: 转换结果
            - output_files: list[str] - 输出图片文件路径列表
            - page_count: int - 页数
            - metadata: dict - 元数据
    """

    output_dir = input.output_dir
    dpi = input.dpi
    format = input.format
    file_path = input.file_path
    logger.info(f"Starting PDF to image conversion: {file_path}")

    if progress_callback:
        await progress_callback(0.0, "Initializing PDF converter")

    try:

        # 创建转换服务
        converter_service = FileConverterService(default_dpi=dpi, default_format=format)

        # 验证文件
        if progress_callback:
            await progress_callback(10.0, "Validating file")

        is_valid = await converter_service.validate(file_path)
        if not is_valid:
            raise ValueError(f"File validation failed: {file_path}")

        # 创建输出目录
        images_output_dir = os.path.join(output_dir, "images")
        os.makedirs(images_output_dir, exist_ok=True)

        if progress_callback:
            await progress_callback(20.0, "Converting PDF to images")

        # 执行转换
        result = await converter_service.convert(
            file_path, output_dir=images_output_dir, dpi=dpi, format=format
        )

        output_files = result["output_files"]
        page_count = result["page_count"]
        metadata = result["metadata"]

        # 保存转换信息到JSON文件
        json_output_path = os.path.join(images_output_dir, "conversion_info.json")
        conversion_info = {
            "input_file": file_path,
            "output_files": output_files,
            "output_dir": images_output_dir,
            "dpi": dpi,
            "format": format,
            "total_images": len(output_files),
            "metadata": metadata,
        }

        try:
            with open(json_output_path, "w", encoding="utf-8") as f:
                json.dump(conversion_info, f, ensure_ascii=False, indent=2)
            logger.info(f"Conversion info saved to: {json_output_path}")
        except Exception as e:
            logger.error(f"Failed to save conversion info JSON: {str(e)}")

        if progress_callback:
            await progress_callback(100.0, f"Converted {len(output_files)} pages")

        logger.info(f"PDF to image conversion completed: {len(output_files)} images")

        return {
            "output_files": output_files,
            "page_count": page_count,
            "metadata": metadata,
            "images_dir": images_output_dir,
            "conversion_info": conversion_info,
        }

    except Exception as e:
        logger.error(f"PDF to image conversion failed: {e}")
        raise
