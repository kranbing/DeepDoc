"""
PDF转换器
"""

from __future__ import annotations

import io
import os
from typing import Dict, Any

from PIL import Image
import fitz

from app.utils.converters.base import BaseConverter
from app.utils.converters.exceptions import ConversionFailedError
from app.utils.logger import logger


class PDFConverter(BaseConverter):
    """PDF转图片转换器"""

    name = "pdf_converter"

    supported_extensions = {".pdf"}

    async def convert(
        self,
        file_path: str,
        output_dir: str,
        dpi: int = 200,
        format: str = "png",
        **kwargs
    ) -> Dict[str, Any]:
        """将PDF转换为图片

        Args:
            file_path: PDF文件路径
            output_dir: 输出目录
            dpi: DPI设置
            format: 输出格式 (png, jpg)
            **kwargs: 其他参数

        Returns:
            Dict: 转换结果
        """
        self.ensure_output_dir(output_dir)

        output_files = []

        try:
            # 打开PDF文件
            pdf_document = fitz.open(file_path)
            page_count = pdf_document.page_count

            # 提取PDF元数据
            metadata = self.get_metadata(file_path)
            metadata.update({
                "title": pdf_document.metadata.get("title", ""),
                "author": pdf_document.metadata.get("author", ""),
                "subject": pdf_document.metadata.get("subject", ""),
                "creator": pdf_document.metadata.get("creator", ""),
                "producer": pdf_document.metadata.get("producer", ""),
                "creation_date": str(pdf_document.metadata.get("creationDate", "")),
                "modification_date": str(pdf_document.metadata.get("modDate", "")),
                "pages": page_count,
                "format": format,
                "dpi": dpi,
            })

            # 设置缩放比例（基于DPI）
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            # 存储首页图片尺寸信息
            target_width = None
            target_height = None

            # 转换每一页
            for page_num in range(page_count):
                # 报告进度
                progress = (page_num / page_count) * 100
                if page_num % 5 == 0:  # 每5页报告一次
                    logger.info(
                        f"PDF转换进度: {progress:.1f}% ({page_num + 1}/{page_count})"
                    )

                page = pdf_document[page_num]

                # 渲染页面为图片
                pix = page.get_pixmap(matrix=mat)

                # 如果是第一页，记录尺寸信息并设为目标尺寸
                if page_num == 0:
                    target_width = pix.width
                    target_height = pix.height
                    metadata["page_size"] = {
                        "width": pix.width,
                        "height": pix.height,
                        "dpi": dpi,
                    }
                    metadata["width"] = target_width
                    metadata["height"] = target_height
                    logger.info(f"首页图片尺寸: {pix.width}x{pix.height} (DPI: {dpi})")
                else:
                    # 检查当前页面转换后的尺寸是否与首页一致
                    if pix.width != target_width or pix.height != target_height:
                        logger.warning(
                            f"第{page_num + 1}页尺寸({pix.width}x{pix.height})与首页不一致({target_width}x{target_height})"
                        )
                        # 统一尺寸：将当前页面resize为首页尺寸
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        resized_image = pil_image.resize(
                            (target_width, target_height), Image.Resampling.LANCZOS
                        )

                        # 保存调整后的图片
                        output_filename = f"page_{page_num + 1:04d}.{format}"
                        output_path = os.path.join(output_dir, output_filename)

                        if format == "png":
                            resized_image.save(output_path, "PNG")
                        elif format == "jpg":
                            resized_image.save(output_path, "JPEG", quality=95)
                        else:
                            raise ValueError(f"不支持的图片格式: {format}")

                        logger.info(
                            f"第{page_num + 1}页已调整为统一尺寸: {target_width}x{target_height}"
                        )

                        output_files.append(output_path)
                        continue  # 跳过常规保存流程

                # 保存图片
                output_filename = f"page_{page_num + 1:04d}.{format}"
                output_path = os.path.join(output_dir, output_filename)

                if format == "png":
                    pix.save(output_path)
                elif format == "jpg":
                    pix.save(output_path, jpeg=True)
                else:
                    raise ValueError(f"不支持的图片格式: {format}")

                output_files.append(output_path)

            pdf_document.close()

            return {
                "output_files": output_files,
                "page_count": page_count,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"PDF转换失败: {str(e)}")
            raise ConversionFailedError(f"PDF转换失败: {str(e)}") from e

    async def validate(self, file_path: str) -> bool:
        """验证PDF文件

        Args:
            file_path: PDF文件路径

        Returns:
            bool: 是否有效
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"PDF文件不存在: {file_path}")
                return False

            # 检查文件扩展名
            if not file_path.lower().endswith(".pdf"):
                logger.error(f"不是PDF文件: {file_path}")
                return False

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.error("PDF文件为空")
                return False

            # 尝试打开PDF文件验证
            pdf_document = fitz.open(file_path)
            page_count = pdf_document.page_count
            pdf_document.close()

            if page_count == 0:
                logger.error("PDF文件没有页面")
                return False

            logger.info(f"PDF文件验证通过，共 {page_count} 页")
            return True

        except Exception as e:
            logger.error(f"PDF文件验证失败: {str(e)}")
            return False
