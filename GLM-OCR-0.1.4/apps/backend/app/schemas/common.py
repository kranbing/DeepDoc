"""
通用的Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, TypeVar, Generic
from datetime import datetime


T = TypeVar('T')


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid input",
                "detail": "File size must be greater than 0"
            }
        }


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProgressUpdate(BaseModel):
    """进度更新"""
    task_id: str
    step_name: str
    progress: float
    overall_progress: float
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
