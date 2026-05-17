"""
通用响应模型
"""
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")
    error_code: Optional[str] = Field(None, description="错误码")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"key": "value"},
                "message": "操作成功",
                "error_code": None
            }
        }


class TaskData(BaseModel):
    """任务数据"""
    task_id: str
    document_id: str
    status: str
    processing_mode: str
    priority: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[float] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    worker_id: Optional[str] = None


class TaskResultData(BaseModel):
    """任务结果数据"""
    metadata: Optional[dict] = None
    full_markdown: Optional[str] = None
    layout: Optional[list] = None
