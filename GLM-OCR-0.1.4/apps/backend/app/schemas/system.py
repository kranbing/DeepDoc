"""
系统相关的Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class WorkerStats(BaseModel):
    """Worker统计信息"""
    worker_id: str
    is_running: bool
    current_task: Optional[str]
    tasks_completed: int
    tasks_failed: int
    avg_execution_time: float


class TasksMetrics(BaseModel):
    """任务指标"""
    status_counts: Dict[str, int]
    total: int


class WorkersMetrics(BaseModel):
    """Worker指标"""
    total: int
    active: int
    idle: int
    busy: int
    stats: List[WorkerStats]


class MetricsResponse(BaseModel):
    """系统指标响应"""
    tasks: TasksMetrics
    workers: WorkersMetrics
    timestamp: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    task_manager_running: Optional[bool] = None
    workers_count: Optional[int] = None
    active_workers: Optional[int] = None
    version: Optional[str] = None
    error: Optional[str] = None


class SystemInfoResponse(BaseModel):
    """系统信息响应"""
    name: str
    version: str
    status: str
