"""
转换器工厂和注册表
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Type

from app.utils.converters.base import BaseConverter
from app.utils.converters.pdf import PDFConverter
from app.utils.converters.image import ImageConverter
from app.utils.converters.word import WordConverter
from app.utils.converters.converter import FileConverterService, default_converter, convert_file
from app.utils.converters.exceptions import UnsupportedFormatError
from app.utils.logger import logger


class ConverterFactory:
    """转换器工厂"""

    # 转换器注册表
    _converters: Dict[str, Type[BaseConverter]] = {}

    @classmethod
    def register(cls, converter_class: Type[BaseConverter]) -> None:
        """注册转换器

        Args:
            converter_class: 转换器类
        """
        converter = converter_class()
        for ext in converter.supported_extensions:
            cls._converters[ext] = converter_class
        logger.info(f"已注册转换器: {converter.name}, 支持扩展名: {converter.supported_extensions}")

    @classmethod
    def get_converter(cls, file_path: str) -> BaseConverter:
        """根据文件路径获取合适的转换器

        Args:
            file_path: 文件路径

        Returns:
            BaseConverter: 转换器实例

        Raises:
            UnsupportedFormatError: 不支持的文件格式
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext not in cls._converters:
            supported_formats = list(cls._converters.keys())
            raise UnsupportedFormatError(
                f"不支持的文件格式: {ext}. 支持的格式: {supported_formats}"
            )

        converter_class = cls._converters[ext]
        return converter_class()

    @classmethod
    def get_converter_by_name(cls, name: str) -> Optional[BaseConverter]:
        """根据名称获取转换器

        Args:
            name: 转换器名称

        Returns:
            Optional[BaseConverter]: 转换器实例，如果不存在则返回None
        """
        for converter_class in cls._converters.values():
            converter = converter_class()
            if converter.name == name:
                return converter
        return None

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """获取所有支持的文件格式

        Returns:
            List[str]: 支持的文件扩展名列表
        """
        return list(cls._converters.keys())

    @classmethod
    def list_converters(cls) -> List[str]:
        """列出所有已注册的转换器名称

        Returns:
            List[str]: 转换器名称列表
        """
        names = set()
        for converter_class in cls._converters.values():
            converter = converter_class()
            names.add(converter.name)
        return list(names)


# 注册所有转换器
def register_default_converters():
    """注册默认的转换器"""
    ConverterFactory.register(PDFConverter)
    ConverterFactory.register(ImageConverter)
    ConverterFactory.register(WordConverter)


# 自动注册默认转换器
register_default_converters()


# 导出
__all__ = [
    # 工厂和基类
    "ConverterFactory",
    "BaseConverter",

    # 具体转换器
    "PDFConverter",
    "ImageConverter",
    "WordConverter",

    # 统一服务（推荐使用）
    "FileConverterService",
    "default_converter",
    "convert_file",

    # 异常
    "UnsupportedFormatError",
    "ConversionFailedError",
    "ConversionTimeoutError",
    "ConverterValidationError",
]
