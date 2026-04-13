"""
统一的文件转换服务 - 自动识别文件类型并转换
"""

from __future__ import annotations

import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.utils.converters.base import BaseConverter
from app.utils.converters.exceptions import UnsupportedFormatError, ConversionFailedError
from app.utils.logger import logger


class FileConverterService:
    """文件转换服务 - 统一的转换接口"""

    def __init__(self, default_dpi: int = 200, default_format: str = "png"):
        """初始化转换服务

        Args:
            default_dpi: 默认DPI
            default_format: 默认输出格式
        """
        self.default_dpi = default_dpi
        self.default_format = default_format

    async def convert(
        self,
        file_path: str,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """转换文件为图片（自动识别文件类型）

        这是唯一的对外接口，会自动识别文件类型并选择合适的转换器

        Args:
            file_path: 输入文件路径（支持PDF、图片、Word文档）
            output_dir: 输出目录（如果为None，则自动创建）
            **kwargs: 转换参数
                - dpi: DPI设置（仅对PDF有效）
                - format: 输出格式（png, jpg等）
                - 其他转换器特定参数

        Returns:
            Dict[str, Any]: 转换结果，包含:
                - output_files: List[str] - 输出图片文件路径列表
                - page_count: int - 页数/图片数
                - metadata: Dict - 元数据信息

        Raises:
            UnsupportedFormatError: 不支持的文件格式
            ConversionFailedError: 转换失败

        Examples:
            >>> service = FileConverterService()
            >>> # 转换PDF
            >>> result = await service.convert("document.pdf")
            >>> images = result["output_files"]
            >>> metadata = result["metadata"]
            >>> # 转换图片
            >>> result = await service.convert("photo.jpg")
            >>> # 转换Word文档
            >>> result = await service.convert("report.docx")
            >>> # 指定输出目录和DPI
            >>> result = await service.convert("doc.pdf", output_dir="/tmp/output", dpi=300)
        """
        # 验证文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 确定输出目录
        if output_dir is None:
            # 自动创建输出目录
            output_dir = os.path.join(
                os.path.dirname(file_path),
                f"converted_{Path(file_path).stem}"
            )

        # 获取转换器（延迟导入避免循环）
        from app.utils.converters import ConverterFactory
        converter = ConverterFactory.get_converter(file_path)

        logger.info(f"开始转换文件: {file_path}")
        logger.info(f"使用转换器: {converter.name}")
        logger.info(f"输出目录: {output_dir}")

        # 特殊处理Word文档（需要两步转换）
        if converter.name == "word_converter":
            return await self._convert_word_document(
                file_path, output_dir, **kwargs
            )

        # 直接转换（PDF或图片）
        # 提取dpi和format参数，使用默认值
        dpi = kwargs.pop("dpi", self.default_dpi)
        format = kwargs.pop("format", self.default_format)

        result = await converter.convert(
            file_path,
            output_dir,
            dpi=dpi,
            format=format,
            **kwargs  # kwargs中已不包含dpi和format
        )

        output_files = result["output_files"]
        page_count = result["page_count"]
        metadata = result["metadata"]

        logger.info(f"转换完成，生成 {len(output_files)} 个文件")

        return {
            "output_files": output_files,
            "page_count": page_count,
            "metadata": metadata,
        }

    async def _convert_word_document(
        self,
        file_path: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """处理Word文档（先转PDF，再转图片）

        Args:
            file_path: Word文档路径
            output_dir: 输出目录
            **kwargs: 转换参数

        Returns:
            Dict[str, Any]: 转换结果，包含:
                - output_files: List[str] - 输出图片文件路径列表
                - page_count: int - 页数/图片数
                - metadata: Dict - 元数据信息
        """
        from app.utils.converters import WordConverter, PDFConverter

        # 提取dpi和format参数，使用默认值
        dpi = kwargs.pop("dpi", self.default_dpi)
        format = kwargs.pop("format", self.default_format)

        # Step 1: Word -> PDF
        word_converter = WordConverter()
        word_result = await word_converter.convert(file_path, output_dir)
        pdf_path = word_result["pdf_path"]

        # Step 2: PDF -> Images
        pdf_converter = PDFConverter()
        pdf_result = await pdf_converter.convert(
            pdf_path, output_dir, dpi=dpi, format=format
        )

        # 合并元数据
        pdf_result["metadata"]["source_file"] = file_path
        pdf_result["metadata"]["converted_from"] = "word_document"
        pdf_result["metadata"]["word_metadata"] = word_result["metadata"]

        # 删除临时PDF文件
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                logger.info(f"已删除临时PDF文件: {pdf_path}")
        except Exception as e:
            logger.warning(f"删除临时PDF文件失败: {str(e)}")

        return {
            "output_files": pdf_result["output_files"],
            "page_count": pdf_result["page_count"],
            "metadata": pdf_result["metadata"],
        }

    async def validate(self, file_path: str) -> bool:
        """验证文件是否可以转换

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否可以转换
        """
        try:
            from app.utils.converters import ConverterFactory
            converter = ConverterFactory.get_converter(file_path)
            return await converter.validate(file_path)
        except Exception:
            return False

    @staticmethod
    def get_supported_formats() -> List[str]:
        """获取所有支持的文件格式

        Returns:
            List[str]: 支持的文件扩展名列表
        """
        from app.utils.converters import ConverterFactory
        return ConverterFactory.get_supported_formats()

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """检查文件格式是否支持

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否支持
        """
        try:
            from app.utils.converters import ConverterFactory
            ConverterFactory.get_converter(file_path)
            return True
        except UnsupportedFormatError:
            return False


# 创建默认实例
default_converter = FileConverterService()


# 便捷函数
async def convert_file(
    file_path: str,
    output_dir: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """转换文件为图片（便捷函数）

    Args:
        file_path: 输入文件路径
        output_dir: 输出目录（可选）
        **kwargs: 转换参数

    Returns:
        Dict[str, Any]: 转换结果，包含:
            - output_files: List[str] - 输出图片文件路径列表
            - page_count: int - 页数/图片数
            - metadata: Dict - 元数据信息

    Examples:
        >>> from app.utils.converters import convert_file
        >>> result = await convert_file("document.pdf")
        >>> images = result["output_files"]
        >>> metadata = result["metadata"]
        >>> result = await convert_file("photo.jpg", output_dir="/tmp/output")
    """
    return await default_converter.convert(file_path, output_dir, **kwargs)
