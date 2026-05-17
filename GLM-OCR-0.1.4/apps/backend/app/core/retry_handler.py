"""
任务重试处理器
"""
import random
from typing import Optional

from app.models.task import Task, TaskStatus
from app.repository.task import TaskRepository
from app.utils.logger import logger


class RetryHandler:
    """任务重试处理器"""

    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    async def handle_failure(
        self,
        task: Task,
        error_message: str,
        error_type: str = "unknown"
    ) -> bool:
        """
        处理任务失败

        Args:
            task: 失败的任务
            error_message: 错误信息
            error_type: 错误类型

        Returns:
            bool: 是否可以重试
        """
        logger.warning(
            f"Task {task.task_id} failed (attempt {task.retry_count + 1}/{task.max_retries}): {error_message}"
        )

        # 检查是否可以重试
        if not task.can_retry:
            logger.error(f"Task {task.task_id} exceeded max retries, moving to dead letter")
            await self._move_to_dead_letter(task, error_message, error_type)
            return False

        # 检查错误类型是否可重试
        if not self._is_retryable_error(error_type):
            logger.error(f"Task {task.task_id} failed with non-retryable error: {error_type}")
            await self._move_to_dead_letter(task, error_message, error_type)
            return False

        # 计算重试延迟
        retry_delay = self._calculate_retry_delay(task.retry_count, task.retry_delay)

        logger.info(
            f"Scheduling retry for task {task.task_id} in {retry_delay}s "
            f"(attempt {task.retry_count + 1}/{task.max_retries})"
        )

        # 重置任务状态为PENDING
        await self.task_repo.reset_task_for_retry(
            task_id=task.task_id,
            error_message=error_message
        )

        return True

    def _calculate_retry_delay(self, retry_count: int, base_delay: int) -> int:
        """
        计算重试延迟时间（指数退避 + 随机抖动）

        Args:
            retry_count: 当前重试次数
            base_delay: 基础延迟时间（秒）

        Returns:
            int: 延迟时间（秒）
        """
        # 指数退避
        exponential_delay = base_delay * (2 ** retry_count)

        # 添加随机抖动（10%）
        jitter = random.randint(0, int(exponential_delay * 0.1))

        # 最大延迟1小时
        return min(exponential_delay + jitter, 3600)

    def _is_retryable_error(self, error_type: str) -> bool:
        """
        判断错误是否可重试

        Args:
            error_type: 错误类型

        Returns:
            bool: 是否可重试
        """
        # 可重试的错误类型
        retryable_errors = {
            "timeout",
            "connection_error",
            "service_unavailable",
            "rate_limit_exceeded",
            "transient_error",
            "resource_temporarily_unavailable"
        }

        # 不可重试的错误类型
        non_retryable_errors = {
            "validation_error",
            "authentication_error",
            "authorization_error",
            "not_found",
            "invalid_input",
            "file_not_found"
        }

        if error_type in non_retryable_errors:
            return False

        if error_type in retryable_errors:
            return True

        # 默认情况下，未知错误可重试
        return True

    async def _move_to_dead_letter(
        self,
        task: Task,
        error_message: str,
        error_type: str
    ):
        """将任务标记为死信"""
        # 更新任务状态
        await self.task_repo.update_task_status(
            task_id=task.task_id,
            status=TaskStatus.DEAD_LETTER,
            error_message=f"Moved to dead letter: {error_message} (error_type: {error_type})"
        )

        logger.warning(f"Task {task.task_id} moved to dead letter")
