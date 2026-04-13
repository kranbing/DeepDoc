"""
系统监控API
"""
from fastapi import APIRouter, HTTPException, status

from app.schemas import MetricsResponse, HealthResponse
from app.core.task_manager import get_task_manager
from app.utils.logger import logger
from app.utils.config import settings


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    获取系统指标

    返回任务和Worker的统计信息
    """
    try:
        task_manager = get_task_manager()
        metrics = await task_manager.get_metrics()

        # 直接返回，FastAPI会自动验证
        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查
    """
    try:
        task_manager = get_task_manager()

        return HealthResponse(
            status="healthy",
            task_manager_running=task_manager.is_running,
            workers_count=len(task_manager.workers),
            active_workers=sum(1 for w in task_manager.workers if w.is_running),
            version=settings.APP_VERSION
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            error=str(e)
        )
