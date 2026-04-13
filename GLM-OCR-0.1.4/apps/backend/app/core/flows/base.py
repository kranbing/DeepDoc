"""
任务处理流程基类和上下文
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Type, List
from dataclasses import dataclass
from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repository.task import TaskRepository
from app.models.task import TaskStatus


@dataclass
class StepProgress:
    """步骤进度信息"""

    step_name: str  # 步骤名称
    progress: float  # 当前步骤进度 (0.0-100.0)
    overall_progress: float  # 整体进度 (0.0-100.0)
    message: Optional[str] = None  # 进度消息
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据


class ProcessingContext:
    """
    任务处理上下文

    在任务执行过程中传递数据和配置
    """

    def __init__(
        self,
        task_id: str,
        document_id: str,
        file_path: str,
        file_type: str,
        processing_mode: str,
        ocr_config: Dict[str, Any],
        output_format: str,
        metadata: Dict[str, Any] = None,
        db_session: Optional[AsyncSession] = None,
        progress_callback: Optional[Callable[[StepProgress], None]] = None,
    ):
        self.task_id = task_id
        self.document_id = document_id
        self.file_path = file_path
        self.file_type = file_type
        self.processing_mode = processing_mode
        self.ocr_config = ocr_config
        self.output_format = output_format
        self.db_session = db_session
        self.progress_callback = progress_callback
        self.metadata = metadata
        # 执行过程中的数据存储
        self._data: Dict[str, Any] = {}

        # 输出目录
        self._output_dir: Optional[str] = None

    def set(self, key: str, value: Any):
        """存储中间数据"""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取中间数据"""
        return self._data.get(key, default)

    def set_output_dir(self, output_dir: str):
        """设置输出目录"""
        self._output_dir = output_dir

    def get_output_dir(self) -> Optional[str]:
        """获取输出目录"""
        return self._output_dir

    async def update_task_progress(
        self, current_step: str, progress: float, message: Optional[str] = None
    ):
        """更新数据库中的任务进度"""
        if not self.db_session:
            return

        try:
            task_repo = TaskRepository(self.db_session)
            await task_repo.update_task_progress(
                task_id=self.task_id, progress=progress, current_stage=current_step
            )
            await self.db_session.commit()
        except Exception as e:
            # 进度更新失败不应该影响主流程
            pass


class TaskProcessingFlow(ABC):
    """
    任务处理流程抽象基类

    子类需要实现 process() 方法，在其中定义处理流程
    """

    def __init__(self, context: ProcessingContext):
        self.context = context

    @abstractmethod
    async def process(self) -> Dict[str, Any]:
        """
        执行完整的处理流程

        子类实现时，在其中定义具体的处理步骤

        Returns:
            Dict[str, Any]: 处理结果，必须包含 success 字段
        """
        pass

    async def update_progress(
        self,
        step_name: str,
        progress: float,
        overall_progress: Optional[float] = None,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        更新任务进度

        Args:
            step_name: 当前步骤名称
            progress: 当前步骤进度 (0.0-100.0)
            overall_progress: 整体进度 (0.0-100.0)，如果不提供则自动计算
            message: 进度消息
            metadata: 额外的元数据
        """
        if overall_progress is None:
            overall_progress = progress

        # 创建进度信息
        progress_info = StepProgress(
            step_name=step_name,
            progress=progress,
            overall_progress=overall_progress,
            message=message,
            metadata=metadata,
        )

        # 回调通知（如果有）
        if self.context.progress_callback:
            try:
                await self.context.progress_callback(progress_info)
            except Exception as e:
                # 回调失败不影响主流程
                pass

        # 更新数据库
        await self.context.update_task_progress(
            current_step=step_name, progress=overall_progress, message=message
        )


class FlowFactory:
    """处理流程工厂"""

    # 注册的流程类
    _flows: Dict[str, Type[TaskProcessingFlow]] = {}

    @classmethod
    def register_flow(cls, processing_mode: str, flow_class: Type[TaskProcessingFlow]):
        """
        注册处理流程

        Args:
            processing_mode: 处理模式名称
            flow_class: 流程类
        """
        cls._flows[processing_mode] = flow_class

    @classmethod
    def create_flow(
        cls, processing_mode: str, context: ProcessingContext
    ) -> TaskProcessingFlow:
        """
        创建处理流程实例

        Args:
            processing_mode: 处理模式
            context: 处理上下文

        Returns:
            TaskProcessingFlow: 处理流程实例

        Raises:
            ValueError: 不支持的处理模式
        """
        flow_class = cls._flows.get(processing_mode)

        if not flow_class:
            raise ValueError(
                f"Unsupported processing mode: {processing_mode}. "
                f"Available modes: {list(cls._flows.keys())}"
            )

        return flow_class(context)

    @classmethod
    def get_registered_modes(cls) -> List[str]:
        """获取所有已注册的处理模式"""
        return list(cls._flows.keys())
