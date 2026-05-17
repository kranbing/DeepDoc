"""
任务管理器实现
"""

import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, UTC

from app.db.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus, TaskPriority
from app.repository.task import TaskRepository
from app.core.worker import Worker
from app.core.lock_manager import LockManager
from app.core.recovery_handler import RecoveryHandler
from app.utils.logger import logger
from app.utils.config import settings


class TaskManager:
    """
    任务管理器

    负责任务的提交、调度和监控
    """

    def __init__(self, max_concurrent_tasks: int = 5, worker_count: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.worker_count = worker_count

        # Workers
        self.workers: List[Worker] = []

        # 状态管理
        self.is_running = False
        self._shutdown_event = asyncio.Event()

        logger.info(
            f"TaskManager initialized: "
            f"max_concurrent={max_concurrent_tasks}, workers={worker_count}"
        )

    async def start(self):
        """启动任务管理器"""
        if self.is_running:
            logger.warning("TaskManager is already running")
            return

        logger.info("Starting TaskManager...")

        self.is_running = True
        self._shutdown_event.clear()

        # 启动时恢复任务
        await self._recover_tasks()

        # 启动Workers
        for i in range(self.worker_count):
            worker = Worker(
                worker_id=f"worker-{i+1}",
                poll_interval=settings.WORKER_POLL_INTERVAL,
                task_timeout=settings.TASK_TIMEOUT,
            )
            self.workers.append(worker)

            # 在后台启动worker
            asyncio.create_task(worker.start())

        # 启动监控和清理协程
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._cleanup_loop())

        logger.info(f"TaskManager started with {len(self.workers)} workers")

    async def stop(self):
        """停止任务管理器"""
        if not self.is_running:
            return

        logger.info("Stopping TaskManager...")

        self.is_running = False
        self._shutdown_event.set()

        # 停止所有Workers
        for worker in self.workers:
            await worker.stop()

        self.workers.clear()

        logger.info("TaskManager stopped")

    async def submit_task(
        self,
        task_id: Optional[str],
        document_id: str,
        original_filename: str,
        file_type: str,
        file_size: int,
        file_path: str,
        processing_mode: str = "pipeline",
        priority: int = TaskPriority.NORMAL,
        ocr_config: Optional[Dict[str, Any]] = None,
        output_format: str = "markdown",
        retry_config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        提交新任务

        Args:
            document_id: 文档ID
            original_filename: 原始文件名
            file_type: 文件类型
            file_size: 文件大小
            file_path: 文件路径
            processing_mode: 处理模式
            priority: 优先级
            ocr_config: OCR配置
            output_format: 输出格式
            retry_config: 重试配置

        Returns:
            str: 任务ID
        """
        if not self.is_running:
            raise RuntimeError("TaskManager is not running")
        if task_id is None :
            # 生成任务ID
            task_id = str(uuid.uuid4())

        logger.info(
            f"Submitting task: {task_id}, "
            f"file={original_filename}, mode={processing_mode}"
        )

        try:
            async with AsyncSessionLocal() as db:
                task_repo = TaskRepository(db)

                # 创建任务
                task = await task_repo.create_task(
                    task_id=task_id,
                    document_id=document_id,
                    original_filename=original_filename,
                    file_type=file_type,
                    file_size=file_size,
                    file_path=file_path,
                    processing_mode=processing_mode,
                    priority=priority,
                    ocr_config=ocr_config,
                    output_format=output_format,
                    retry_config=retry_config,
                )

                await db.commit()
                logger.info(f"Task created: {task_id}")

                return task_id

        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            Optional[Dict]: 任务信息
        """
        async with AsyncSessionLocal() as db:
            task_repo = TaskRepository(db)
            task = await task_repo.get_by_task_id(task_id)

            if not task:
                return None

            return {
                "task_id": task.task_id,
                "document_id": task.document_id,
                "status": task.status,
                "progress": task.progress,
                "current_step": task.current_step,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
                "result_file_path": task.result_file_path,
                "processing_mode": task.processing_mode,
                "priority": task.priority,
                "retry_count": task.retry_count,
                "worker_id": task.worker_id,
            }

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        try:
            async with AsyncSessionLocal() as db:
                task_repo = TaskRepository(db)
                task = await task_repo.get_by_task_id(task_id)

                if not task:
                    return False

                # 只能取消pending或processing的任务
                if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    return False

                # 更新状态
                await task_repo.update_task_status(
                    task_id=task_id, status=TaskStatus.CANCELLED
                )
                await db.commit()

                logger.info(f"Task cancelled: {task_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False

    async def list_tasks(
        self, status: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出任务

        Args:
            status: 过滤状态
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Dict]: 任务列表
        """
        async with AsyncSessionLocal() as db:
            task_repo = TaskRepository(db)
            tasks = await task_repo.list_tasks_by_status(
                status=status, skip=offset, limit=limit
            )

            return [
                {
                    "task_id": task.task_id,
                    "document_id": task.document_id,
                    "status": task.status,
                    "progress": task.progress,
                    "current_step": task.current_step,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "processing_mode": task.processing_mode,
                    "priority": task.priority,
                }
                for task in tasks
            ]

    async def get_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        async with AsyncSessionLocal() as db:
            task_repo = TaskRepository(db)

            # 统计各状态任务数量
            status_counts = await task_repo.count_tasks_by_status()

            # 构造任务指标
            tasks_metrics = {
                "status_counts": status_counts,
                "total": sum(status_counts.values()),
            }

            # Worker统计
            worker_stats = []
            for worker in self.workers:
                worker_stats.append(
                    {
                        "worker_id": worker.worker_id,
                        "is_running": worker.is_running,
                        "current_task": worker.current_task_id,
                        "tasks_completed": worker.metrics.tasks_completed,
                        "tasks_failed": worker.metrics.tasks_failed,
                        "avg_execution_time": worker.metrics.avg_execution_time,
                    }
                )

            # 构造Worker指标
            workers_metrics = {
                "total": len(self.workers),
                "active": sum(1 for w in self.workers if w.is_running),
                "idle": sum(1 for w in self.workers if w.current_task_id is None),
                "busy": sum(1 for w in self.workers if w.current_task_id is not None),
                "stats": worker_stats,
            }

            return {
                "tasks": tasks_metrics,
                "workers": workers_metrics,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    async def _recover_tasks(self):
        """启动时恢复任务"""
        logger.info("Recovering tasks on startup...")

        try:
            async with AsyncSessionLocal() as db:
                task_repo = TaskRepository(db)
                recovery_handler = RecoveryHandler(task_repo)

                stats = await recovery_handler.recover_on_startup()
                await db.commit()

                logger.info(f"Task recovery completed: {stats}")

        except Exception as e:
            logger.error(f"Task recovery failed: {e}")

    async def _monitoring_loop(self):
        """监控协程"""
        logger.info("Monitoring loop started")

        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(settings.METRICS_INTERVAL)

                # 恢复过期锁
                async with AsyncSessionLocal() as db:
                    lock_manager = LockManager(db)
                    recovered = await lock_manager.recover_expired_locks()
                    if recovered > 0:
                        logger.info(
                            f"Recovered {recovered} expired locks in monitoring loop"
                        )

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")

        logger.info("Monitoring loop stopped")

    async def _cleanup_loop(self):
        """清理协程"""
        logger.info("Cleanup loop started")

        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(settings.CLEANUP_INTERVAL)

                # 清理旧任务
                async with AsyncSessionLocal() as db:
                    task_repo = TaskRepository(db)
                    deleted = await task_repo.cleanup_old_tasks(
                        days=settings.OLD_TASK_DAYS
                    )
                    if deleted > 0:
                        logger.info(f"Cleaned up {deleted} old tasks")

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

        logger.info("Cleanup loop stopped")

    def __repr__(self) -> str:
        return (
            f"<TaskManager(running={self.is_running}, " f"workers={len(self.workers)})>"
        )


# 全局任务管理器实例
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(
            max_concurrent_tasks=settings.MAX_CONCURRENT_TASKS,
            worker_count=settings.WORKER_COUNT,
        )
    return _task_manager


async def init_task_system():
    """初始化任务系统"""
    task_manager = get_task_manager()
    await task_manager.start()
    logger.info("Task system initialized")


async def shutdown_task_system():
    """关闭任务系统"""
    global _task_manager
    if _task_manager:
        await _task_manager.stop()
        logger.info("Task system shutdown")
