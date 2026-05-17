"""
Word文档转换器
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any

from app.utils.converters.base import BaseConverter
from app.utils.converters.exceptions import ConversionFailedError, ConversionTimeoutError
from app.utils.config import settings
from app.utils.logger import logger


class WordConverter(BaseConverter):
    """Word文档转PDF转换器"""

    name = "word_converter"

    supported_extensions = {".doc", ".docx"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 根据环境选择LibreOffice命令
        self.libreoffice_cmd = (
            "soffice" if settings.environment == "development" else "libreoffice"
        )

    async def convert(
        self,
        file_path: str,
        output_dir: str,
        **kwargs
    ) -> Dict[str, Any]:
        """将Word文档转换为PDF

        Args:
            file_path: Word文档路径
            output_dir: 输出目录
            **kwargs: 其他参数

        Returns:
            Dict: 转换结果（包含PDF文件路径）
        """
        self.ensure_output_dir(output_dir)

        try:
            # 创建临时目录用于转换
            temp_dir = tempfile.mkdtemp(prefix="word_convert_")

            try:
                logger.info(f"开始转换Word文档到PDF: {file_path}")

                # 使用LibreOffice进行转换
                cmd = [
                    self.libreoffice_cmd,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", temp_dir,
                    file_path
                ]

                logger.info(f"执行命令: {' '.join(cmd)}")

                # 执行转换命令
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,  # 2分钟超时
                    check=True
                )

                logger.info(f"LibreOffice输出: {result.stdout}")
                if result.stderr:
                    logger.warning(f"LibreOffice警告: {result.stderr}")

                # 查找生成的PDF文件
                word_filename = os.path.basename(file_path)
                pdf_filename = os.path.splitext(word_filename)[0] + ".pdf"
                pdf_path = os.path.join(temp_dir, pdf_filename)

                if not os.path.exists(pdf_path):
                    # 尝试查找任何生成的PDF文件
                    pdf_files = [f for f in os.listdir(temp_dir) if f.endswith('.pdf')]
                    if pdf_files:
                        pdf_path = os.path.join(temp_dir, pdf_files[0])
                    else:
                        raise FileNotFoundError(f"LibreOffice未生成PDF文件: {file_path}")

                # 将PDF文件移动到最终输出目录
                final_pdf_path = os.path.join(output_dir, os.path.basename(pdf_path))
                shutil.move(pdf_path, final_pdf_path)

                logger.info(f"Word文档转换成功，PDF已保存到: {final_pdf_path}")

                # 返回转换结果
                metadata = self.get_metadata(file_path)
                metadata.update({
                    "converted_from": "word_document",
                    "pdf_path": final_pdf_path,
                    "original_format": os.path.splitext(word_filename)[1],
                })

                return {
                    "output_files": [final_pdf_path],
                    "page_count": 0,  # Word转PDF后需要PDF转换器来确定页数
                    "metadata": metadata,
                    "pdf_path": final_pdf_path,  # 额外返回PDF路径供后续使用
                }

            finally:
                # 清理临时目录
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {str(e)}")

        except subprocess.TimeoutExpired as e:
            logger.error("Word文档转换超时")
            raise ConversionTimeoutError(
                "Word文档转换超时，请检查文件是否过大或LibreOffice是否正常运行"
            ) from e
        except subprocess.CalledProcessError as e:
            logger.error(f"LibreOffice转换失败: {e.stderr}")
            raise ConversionFailedError(f"Word文档转换失败: {e.stderr}") from e
        except Exception as e:
            logger.error(f"Word文档转换异常: {str(e)}")
            raise ConversionFailedError(f"Word文档转换异常: {str(e)}") from e

    async def validate(self, file_path: str) -> bool:
        """验证Word文档和LibreOffice环境

        Args:
            file_path: Word文档路径

        Returns:
            bool: 是否有效
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"Word文档不存在: {file_path}")
                return False

            # 检查文件扩展名
            if not self.can_handle(file_path):
                logger.error(f"不是Word文档: {file_path}")
                return False

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.error("Word文档为空")
                return False

            # 检查LibreOffice是否可用
            try:
                result = subprocess.run(
                    [self.libreoffice_cmd, "--version"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Word文档验证通过，LibreOffice可用")
                    return True
                else:
                    logger.error("LibreOffice未安装或不可用，无法转换Word文档")
                    return False
            except FileNotFoundError:
                logger.error("未找到LibreOffice，无法转换Word文档")
                return False
            except Exception as e:
                logger.error(f"LibreOffice检查失败: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"Word文档验证失败: {str(e)}")
            return False
