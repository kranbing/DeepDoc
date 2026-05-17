"""
图片转换器
"""

from __future__ import annotations

import os
from typing import Dict, Any

from PIL import Image

from app.utils.converters.base import BaseConverter
from app.utils.converters.exceptions import ConversionFailedError
from app.utils.logger import logger


class ImageConverter(BaseConverter):
    """图片格式转换器（统一转换为PNG）"""

    name = "image_converter"

    supported_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

    async def convert(
        self,
        file_path: str,
        output_dir: str,
        format: str = "png",
        **kwargs
    ) -> Dict[str, Any]:
        """将图片转换为指定格式（默认PNG）

        Args:
            file_path: 图片文件路径
            output_dir: 输出目录
            format: 输出格式（默认png）
            **kwargs: 其他参数

        Returns:
            Dict: 转换结果
        """
        self.ensure_output_dir(output_dir)

        try:
            # 打开图片文件
            with Image.open(file_path) as img:
                width, height = img.size
                original_format = img.format.lower() if img.format else "unknown"

                logger.info(f"图片尺寸: {width}x{height}, 原始格式: {original_format}")

                # 获取DPI信息
                dpi_info = getattr(img, "info", {}).get("dpi", (None, None))

                page_size = {
                    "width": width,
                    "height": height,
                    "dpi": dpi_info,
                }

                # 保存图片元数据
                metadata = self.get_metadata(file_path)
                metadata.update({
                    "width": width,
                    "height": height,
                    "format": format,  # 输出格式
                    "original_format": original_format,  # 原始格式
                    "dpi": dpi_info,
                    "mode": img.mode,
                    "pages": 1,
                    "page_size": page_size,
                })

                # 构造输出文件路径
                output_filename = f"page_0001.{format}"
                output_path = os.path.join(output_dir, output_filename)

                # 将图片转换为RGB模式（如果需要）并保存为指定格式
                if format == "png":
                    if img.mode in ("RGBA", "P"):
                        # 如果是RGBA或调色板模式，转换为RGB
                        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "RGBA":
                            rgb_img.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                        else:
                            rgb_img.paste(img)
                        rgb_img.save(output_path, "PNG")
                    else:
                        img.save(output_path, "PNG")
                elif format == "jpg":
                    if img.mode in ("RGBA", "P"):
                        # JPEG不支持透明度，需要转换
                        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "RGBA":
                            rgb_img.paste(img, mask=img.split()[3])
                        else:
                            rgb_img.paste(img)
                        rgb_img.save(output_path, "JPEG", quality=95)
                    else:
                        img.save(output_path, "JPEG", quality=95)
                else:
                    raise ValueError(f"不支持的输出格式: {format}")

                logger.info(f"图片已保存到: {output_path}")

                return {
                    "output_files": [output_path],
                    "page_count": 1,
                    "metadata": metadata,
                }

        except Exception as e:
            logger.error(f"图片转换失败: {str(e)}")
            raise ConversionFailedError(f"图片转换失败: {str(e)}") from e

    async def validate(self, file_path: str) -> bool:
        """验证图片文件

        Args:
            file_path: 图片文件路径

        Returns:
            bool: 是否有效
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"图片文件不存在: {file_path}")
                return False

            # 检查文件扩展名
            if not self.can_handle(file_path):
                logger.error(f"不支持的图片格式: {file_path}")
                return False

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.error("图片文件为空")
                return False

            # 尝试打开图片验证
            with Image.open(file_path) as img:
                width, height = img.size
                logger.info(f"图片文件验证通过，尺寸: {width}x{height}")
                return True

        except Exception as e:
            logger.error(f"图片文件验证失败: {str(e)}")
            return False
