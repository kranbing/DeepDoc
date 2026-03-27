from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile

from app.utils.config import settings
from app.utils.logger import logger


class FileUploadHandler:
    """文件上传处理器，只负责校验和保存"""

    DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx"}
    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".gif",
        ".tiff",
        ".tif",
        ".webp",
    }

    DOCUMENT_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self) -> None:
        pass

    def valid(self, file: UploadFile) -> bool:
        """校验文件是否是 PDF、Word 或常见图片类型"""
        filename = (file.filename or "").strip()
        suffix = Path(filename).suffix.lower()
        content_type = (file.content_type or "").lower()

        if suffix in self.DOCUMENT_EXTENSIONS or suffix in self.IMAGE_EXTENSIONS:
            return True

        if content_type in self.DOCUMENT_MIME_TYPES or content_type.startswith("image/"):
            return True

        return False

    async def save_to_path(
        self, file: UploadFile, filename: str | None = None, upload_dir: str | Path | None = None
    ) -> str:
        """校验后将上传文件保存到指定目录，并返回保存路径"""
        if not self.valid(file):
            raise HTTPException(status_code=400, detail="仅支持 PDF、Word 或常见图片格式文件")

        safe_name = Path(filename or file.filename or "upload").name
        base_dir = Path(upload_dir) if upload_dir else Path(settings.OUTPUT_DIR)
        dest_path = base_dir / safe_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        await file.seek(0)
        async with aiofiles.open(dest_path, "wb") as target:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await target.write(chunk)

        logger.info("文件已保存到: %s", dest_path)
        return str(dest_path)


# 全局文件上传处理器实例
file_upload_handler = FileUploadHandler()