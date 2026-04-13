"""
任务Worker实现
"""
import asyncio
import uuid
from datetime import datetime, UTC
from typing import Optional
from dataclasses import dataclass, field

from app.db.database import AsyncSessionLocal
from app.models.task import Task, TaskStatus
from app.repository.task import TaskRepository
from app.core.flows.base import FlowFactory, ProcessingContext
from app.core.lock_manager import LockManager
from app.core.retry_handler import RetryHandler
from app.utils.logger import logger


@dataclass
class WorkerMetrics:
    """Worker统计信息"""
    worker_id: str
    tasks_started: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0

    def record_execution_time(self, time: float):
        """记录执行时间"""
        self.total_execution_time += time

    @property
    def avg_execution_time(self) -> float:
        """平均执行时间"""
        if self.tasks_completed == 0:
            return 0.0
        return self.total_execution_time / self.tasks_completed


class Worker:
    """
    任务Worker

    从任务队列中获取任务并执行
    """

    def __init__(
        self,
        worker_id: Optional[str] = None,
        poll_interval: int = 5,
        task_timeout: int = 3600
    ):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.task_timeout = task_timeout

        # 当前任务
        self.current_task_id: Optional[str] = None
        self.is_running = False
        self._stop_event = asyncio.Event()

        # 统计信息
        self.metrics = WorkerMetrics(worker_id=self.worker_id)

        logger.info(f"Worker initialized: {self.worker_id}")

    async def start(self):
        """启动Worker"""
        if self.is_running:
            logger.warning(f"Worker {self.worker_id} is already running")
            return

        logger.info(f"Starting worker: {self.worker_id}")
        self.is_running = True
        self._stop_event.clear()

        # 启动主循环
        await self._main_loop()

    async def stop(self):
        """停止Worker"""
        if not self.is_running:
            return

        logger.info(f"Stopping worker: {self.worker_id}")
        self.is_running = False
        self._stop_event.set()

        # 等待当前任务完成（最多等待30秒）
        if self.current_task_id:
            logger.info(f"Waiting for current task to complete: {self.current_task_id}")
            await asyncio.sleep(30)

        logger.info(f"Worker stopped: {self.worker_id}")

    async def _main_loop(self):
        """Worker主循环"""
        logger.info(f"Worker main loop started: {self.worker_id}")

        while not self._stop_event.is_set():
            try:
                # 如果已有任务在执行，等待完成
                if self.current_task_id:
                    await asyncio.sleep(1)
                    continue

                # 获取新任务
                task = await self._acquire_task()

                if task:
                    # 处理任务
                    await self._process_task(task)
                else:
                    # 没有任务，等待一段时间
                    await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info(f"Worker cancelled: {self.worker_id}")
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(self.poll_interval)

        logger.info(f"Worker main loop stopped: {self.worker_id}")

    async def _acquire_task(self) -> Optional[Task]:
        """获取待处理任务"""
        try:
            async with AsyncSessionLocal() as db:
                task_repo = TaskRepository(db)
                lock_manager = LockManager(db, self.task_timeout)

                # 获取待处理任务
                pending_tasks = await task_repo.get_pending_tasks(limit=1)

                if not pending_tasks:
                    return None

                task = pending_tasks[0]

                # 尝试获取锁
                locked_task = await lock_manager.acquire(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    timeout=self.task_timeout
                )

                if locked_task:
                    await db.commit()
                    logger.info(f"Acquired task: {task.task_id}")
                    return locked_task
                else:
                    return None

        except Exception as e:
            logger.error(f"Failed to acquire task: {e}")
            return None

    async def _process_task(self, task: Task):
        """处理单个任务"""
        self.current_task_id = task.task_id
        self.metrics.tasks_started += 1

        logger.info(f"Processing task: {task.task_id}")
        start_time = datetime.now(UTC)

        try:
            async with AsyncSessionLocal() as db:
                task_repo = TaskRepository(db)
                lock_manager = LockManager(db, self.task_timeout)
                retry_handler = RetryHandler(task_repo)

                try:
                    # 创建进度回调
                    progress_callback = self._create_progress_callback(task.task_id, db)

                    # 创建处理上下文
                    context = ProcessingContext(
                        task_id=task.task_id,
                        document_id=task.document_id,
                        file_path=task.file_path,
                        file_type=task.file_type,
                        processing_mode=task.processing_mode,
                        ocr_config=task.ocr_config or {},
                        output_format=task.output_format,
                        db_session=db,
                        progress_callback=progress_callback
                    )

                    # 获取处理流程
                    flow = FlowFactory.create_flow(
                        processing_mode=task.processing_mode,
                        context=context
                    )

                    # 执行流程
                    result = await flow.process()

                    # 任务成功
                    await lock_manager.release(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status=TaskStatus.COMPLETED
                    )

                    # 更新结果
                    await task_repo.update_task_status(
                        task_id=task.task_id,
                        status=TaskStatus.COMPLETED,
                        progress=100.0,
                        result_file_path=result.get('json_output_path'),
                        result=result
                    )

                    await db.commit()

                    self.metrics.tasks_completed += 1
                    execution_time = (datetime.now(UTC) - start_time).total_seconds()
                    self.metrics.record_execution_time(execution_time)

                    logger.info(
                        f"Task completed: {task.task_id} "
                        f"in {execution_time:.2f}s"
                    )

                except Exception as e:
                    # 处理过程中的异常
                    await db.rollback()

                    # 分类错误
                    error_type = self._classify_error(str(e))

                    # 处理重试
                    can_retry = await retry_handler.handle_failure(
                        task=task,
                        error_message=str(e),
                        error_type=error_type
                    )

                    await lock_manager.release(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status=TaskStatus.FAILED if not can_retry else TaskStatus.PENDING,
                        error_message=str(e)
                    )

                    await db.commit()

                    self.metrics.tasks_failed += 1
                    logger.error(f"Task processing error: {task.task_id}, error: {e}")

        except Exception as e:
            logger.error(f"Failed to process task {task.task_id}: {e}")
            self.metrics.tasks_failed += 1

        finally:
            self.current_task_id = None

    def _create_progress_callback(self, task_id: str, db):
        """创建进度回调"""
        async def callback(progress_info):
            # 进度回调已经在流程中通过context更新了数据库
            # 这里主要用于日志记录
            logger.debug(
                f"Task {task_id} progress: "
                f"{progress_info.step_name} - {progress_info.overall_progress:.1f}%"
            )
        return callback

    def _classify_error(self, error_message: str) -> str:
        """
        分类错误类型

        Args:
            error_message: 错误信息

        Returns:
            str: 错误类型
        """
        error_message_lower = error_message.lower()

        if "timeout" in error_message_lower:
            return "timeout"
        elif "connection" in error_message_lower:
            return "connection_error"
        elif "validation" in error_message_lower or "invalid" in error_message_lower:
            return "validation_error"
        elif "not found" in error_message_lower:
            return "not_found"
        elif "rate limit" in error_message_lower:
            return "rate_limit_exceeded"
        elif "file" in error_message_lower and "not found" in error_message_lower:
            return "file_not_found"
        else:
            return "unknown"

    def __repr__(self) -> str:
        return (
            f"<Worker(worker_id={self.worker_id}, "
            f"running={self.is_running}, "
            f"current_task={self.current_task_id})>"
        )
