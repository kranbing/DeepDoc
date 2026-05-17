"""
任务恢复处理器
"""
from typing import Dict, Any

from app.models.task import Task, TaskStatus
from app.repository.task import TaskRepository
from app.utils.logger import logger


class RecoveryHandler:
    """任务恢复处理器"""

    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    async def recover_on_startup(self) -> Dict[str, int]:
        """
        系统启动时恢复任务

        Returns:
            Dict[str, int]: 恢复统计信息
        """
        logger.info("Starting task recovery on startup")

        stats = {
            "total_checked": 0,
            "expired_locks_recovered": 0,
            "failed_recoveries": 0
        }

        try:
            # 恢复锁已过期的任务
            expired_count = await self._recover_expired_locks()
            stats["expired_locks_recovered"] = expired_count

            stats["total_checked"] = expired_count

            logger.info(f"Task recovery completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Task recovery failed: {e}")
            stats["failed_recoveries"] = 1
            return stats

    async def _recover_expired_locks(self) -> int:
        """恢复锁已过期的任务"""
        expired_tasks = await self.task_repo.get_expired_locks(limit=1000)

        recovered_count = 0
        for task in expired_tasks:
            try:
                await self._recover_single_task(task, reason="lock_expired")
                recovered_count += 1
            except Exception as e:
                logger.error(f"Failed to recover task {task.task_id}: {e}")

        if recovered_count > 0:
            logger.info(f"Recovered {recovered_count} tasks with expired locks")

        return recovered_count

    async def _recover_single_task(self, task: Task, reason: str):
        """恢复单个任务"""
        logger.info(f"Recovering task {task.task_id}, reason: {reason}")

        # 检查是否可以重试
        if not task.can_retry:
            # 超过最大重试次数，标记为死信
            await self.task_repo.update_task_status(
                task_id=task.task_id,
                status=TaskStatus.DEAD_LETTER,
                error_message=f"Task recovered but max retries exceeded: {reason}"
            )
            logger.warning(f"Task {task.task_id} marked as dead letter (max retries exceeded)")
            return

        # 重置任务为PENDING状态
        await self.task_repo.update_task_status(
            task_id=task.task_id,
            status=TaskStatus.PENDING,
            error_message=f"Task recovered: {reason}"
        )

        # 重置为初始状态
        from sqlalchemy import update

        stmt = (
            update(Task)
            .where(Task.task_id == task.task_id)
            .values(
                worker_id=None,
                lock_expires_at=None,
                retry_count=task.retry_count + 1,
                started_at=None,
                current_step=None,
                progress=0.0
            )
        )
        await self.task_repo.session.execute(stmt)

        logger.info(f"Task {task.task_id} recovered successfully")
