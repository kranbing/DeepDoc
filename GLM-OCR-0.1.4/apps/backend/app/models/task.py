"""
任务数据模型
"""
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, Float, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TaskStatus:
    """任务状态常量"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


class TaskPriority:
    """任务优先级常量"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class Task(Base, TimestampMixin):
    """
    任务模型
    """
    __tablename__ = "tasks"

    # 主键和唯一标识
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )

    # 文档信息
    document_id: Mapped[str] = mapped_column(String(64), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # 处理配置
    processing_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=TaskPriority.NORMAL)
    output_format: Mapped[str] = mapped_column(String(50), default="markdown")

    # 任务状态
    status: Mapped[str] = mapped_column(
        String(50),
        default=TaskStatus.PENDING,
        index=True,
        nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    current_step: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )  # 当前执行的步骤名称（如：pdf_to_images, ocr_processing）
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 结果
    result_file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # 配置
    ocr_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # 时间戳
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # 重试相关
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay: Mapped[int] = mapped_column(Integer, default=60)
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Worker相关（用于分布式锁）
    worker_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    lock_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        index=True,
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<Task(task_id={self.task_id}, status={self.status}, progress={self.progress})>"

    @property
    def is_locked(self) -> bool:
        """检查任务是否被锁定"""
        if not self.lock_expires_at:
            return False
        return self.lock_expires_at > datetime.now()

    @property
    def is_expired(self) -> bool:
        """检查任务锁是否已过期"""
        if not self.lock_expires_at:
            return False
        return self.lock_expires_at <= datetime.now()

    @property
    def can_retry(self) -> bool:
        """检查任务是否可以重试"""
        return self.retry_count < self.max_retries

    @property
    def execution_time(self) -> Optional[float]:
        """计算任务执行时间（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
