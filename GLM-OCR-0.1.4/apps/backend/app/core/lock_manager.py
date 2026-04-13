"""
任务锁管理器
"""
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.repository.task import TaskRepository
from app.utils.logger import logger


class LockManager:
    """任务锁管理器"""

    def __init__(self, session: AsyncSession, default_timeout: int = 3600):
        self.session = session
        self.default_timeout = default_timeout
        self.task_repo = TaskRepository(session)

    async def acquire(
        self,
        task_id: str,
        worker_id: str,
        timeout: Optional[int] = None
    ) -> Optional[Task]:
        """
        获取任务锁

        Args:
            task_id: 任务ID
            worker_id: Worker ID
            timeout: 锁超时时间（秒）

        Returns:
            Optional[Task]: 成功返回任务，失败返回None
        """
        lock_timeout = timeout or self.default_timeout

        try:
            task = await self.task_repo.acquire_task_lock(
                task_id=task_id,
                worker_id=worker_id,
                lock_timeout=lock_timeout
            )

            if task:
                logger.info(f"Lock acquired for task {task_id} by worker {worker_id}")
            else:
                logger.warning(f"Failed to acquire lock for task {task_id} by worker {worker_id}")

            return task

        except Exception as e:
            logger.error(f"Failed to acquire lock for task {task_id}: {e}")
            return None

    async def release(
        self,
        task_id: str,
        worker_id: str,
        status: str = TaskStatus.COMPLETED,
        error_message: Optional[str] = None
    ) -> bool:
        """
        释放任务锁

        Args:
            task_id: 任务ID
            worker_id: Worker ID
            status: 最终状态
            error_message: 错误信息

        Returns:
            bool: 是否成功释放
        """
        try:
            success = await self.task_repo.release_task_lock(
                task_id=task_id,
                worker_id=worker_id,
                status=status,
                error_message=error_message
            )

            if success:
                logger.info(f"Lock released for task {task_id} by worker {worker_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to release lock for task {task_id}: {e}")
            return False

    async def renew(self, task_id: str, worker_id: str) -> bool:
        """
        续期任务锁

        Args:
            task_id: 任务ID
            worker_id: Worker ID

        Returns:
            bool: 是否成功续期
        """
        try:
            success = await self.task_repo.renew_task_lock(
                task_id=task_id,
                worker_id=worker_id,
                lock_timeout=self.default_timeout
            )

            if success:
                logger.debug(f"Lock renewed for task {task_id} by worker {worker_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to renew lock for task {task_id}: {e}")
            return False

    async def recover_expired_locks(self) -> int:
        """
        恢复过期的锁

        Returns:
            int: 恢复的任务数量
        """
        try:
            expired_tasks = await self.task_repo.get_expired_locks(limit=100)

            recovered_count = 0
            for task in expired_tasks:
                try:
                    # 检查是否可以重试
                    if task.can_retry:
                        await self.task_repo.reset_task_for_retry(
                            task_id=task.task_id,
                            error_message="Lock expired, recovered for retry"
                        )
                        recovered_count += 1
                        logger.info(f"Recovered task {task.task_id} (lock expired)")
                    else:
                        # 超过最大重试次数，标记为死信
                        await self.task_repo.update_task_status(
                            task_id=task.task_id,
                            status=TaskStatus.DEAD_LETTER,
                            error_message="Lock expired and max retries exceeded"
                        )
                        logger.warning(f"Task {task.task_id} moved to dead letter (lock expired)")

                except Exception as e:
                    logger.error(f"Failed to recover task {task.task_id}: {e}")

            if recovered_count > 0:
                logger.info(f"Recovered {recovered_count} tasks with expired locks")
                await self.session.commit()

            return recovered_count

        except Exception as e:
            logger.error(f"Failed to recover expired locks: {e}")
            await self.session.rollback()
            return 0
