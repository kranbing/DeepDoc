"""
Pydantic Schema定义

提供统一的API请求和响应模型
"""

from app.schemas.task import (
    TaskSubmitRequest,
    TaskSubmitResponse,
    TaskStatusResponse,
    TaskListResponse,
    TaskCancelResponse,
    TaskInfo,
)

from app.schemas.system import (
    WorkerStats,
    TasksMetrics,
    WorkersMetrics,
    MetricsResponse,
    HealthResponse,
    SystemInfoResponse,
)

from app.schemas.common import (
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
    ProgressUpdate,
)

from app.schemas.response import ApiResponse, TaskData, TaskResultData

__all__ = [
    # Task schemas
    "TaskSubmitRequest",
    "TaskSubmitResponse",
    "TaskStatusResponse",
    "TaskListResponse",
    "TaskCancelResponse",
    "TaskInfo",
    # System schemas
    "WorkerStats",
    "TasksMetrics",
    "WorkersMetrics",
    "MetricsResponse",
    "HealthResponse",
    "SystemInfoResponse",
    # Common schemas
    "ErrorResponse",
    "MessageResponse",
    "PaginatedResponse",
    "ProgressUpdate",
    # Response schemas
    "ApiResponse",
    "TaskData",
    "TaskResultData",
]
