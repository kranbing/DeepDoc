"""
任务相关的Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TaskSubmitRequest(BaseModel):
    """任务提交请求"""

    original_filename: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., gt=0, description="文件大小")
    file_path: str = Field(..., description="文件路径")
    processing_mode: str = Field(default="pipeline", description="处理模式")
    priority: int = Field(default=2, ge=1, le=4, description="优先级 (1-4)")
    ocr_config: Optional[Dict[str, Any]] = Field(default=None, description="OCR配置")
    output_format: str = Field(default="markdown", description="输出格式")
    retry_config: Optional[Dict[str, Any]] = Field(default=None, description="重试配置")

    class Config:
        json_schema_extra = {
            "example": {
                "original_filename": "document.pdf",
                "file_type": "pdf",
                "file_size": 1024000,
                "file_path": "/path/to/document.pdf",
                "processing_mode": "pipeline",
                "priority": 2,
                "ocr_config": {"dpi": 300, "image_format": "png", "language": "mixed"},
                "output_format": "markdown",
            }
        }


class TaskSubmitResponse(BaseModel):
    """任务提交响应"""

    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""

    task_id: str
    document_id: str
    status: str
    progress: float
    current_step: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    result_file_path: Optional[str]
    processing_mode: str
    priority: int
    retry_count: int
    worker_id: Optional[str]
    metadata: Optional[Dict] = None
    full_markdown: Optional[str] = None
    layout: Optional[List] = None


class TaskInfo(BaseModel):
    """任务信息（用于列表）"""

    task_id: str
    document_id: str
    status: str
    progress: float
    current_step: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_mode: str
    priority: int


class TaskListResponse(BaseModel):
    """任务列表响应"""

    tasks: List[TaskInfo]
    total: int


class TaskCancelResponse(BaseModel):
    """任务取消响应"""

    task_id: str
    status: str
    message: str
