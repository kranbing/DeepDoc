"""
转换器基类
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.utils.logger import logger


class BaseConverter(ABC):
    """转换器基类"""

    # 转换器名称
    name: str = "base"

    # 支持的文件扩展名
    supported_extensions: set[str] = set()

    def __init__(self, **kwargs):
        """初始化转换器

        Args:
            **kwargs: 转换器特定配置
        """
        self.config = kwargs

    @abstractmethod
    async def convert(
        self, file_path: str, output_dir: str, **kwargs
    ) -> Dict[str, Any]:
        """转换文件

        Args:
            file_path: 输入文件路径
            output_dir: 输出目录
            **kwargs: 转换参数（如 dpi, format 等）

        Returns:
            Dict: {
                "output_files": List[str],  # 输出文件列表
                "page_count": int,           # 页数/图片数
                "metadata": Dict             # 元数据
            }

        Raises:
            ConversionFailedError: 转换失败
            ConversionTimeoutError: 转换超时
        """
        pass

    @abstractmethod
    async def validate(self, file_path: str) -> bool:
        """验证文件是否可以被此转换器处理

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否可以处理该文件

        Raises:
            ConverterValidationError: 验证失败
        """
        pass

    def can_handle(self, file_path: str) -> bool:
        """检查转换器是否可以处理该文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否可以处理
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_extensions

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文件元数据

        Args:
            file_path: 文件路径

        Returns:
            Dict: 元数据字典
        """
        return {
            "source_file": file_path,
            "converter": self.name,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        }

    def ensure_output_dir(self, output_dir: str) -> None:
        """确保输出目录存在

        Args:
            output_dir: 输出目录路径
        """
        os.makedirs(output_dir, exist_ok=True)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(extensions={self.supported_extensions})>"
