"""
FastAPI应用入口
"""
import sys
from pathlib import Path


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tasks import router as tasks_router
from app.api.system import router as system_router
from app.core.task_manager import init_task_system, shutdown_task_system
from app.db.database import init_db, close_db
from app.utils.logger import logger
from app.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Application starting up...")

    # 1. 初始化数据库
    await init_db()

    # 2. 初始化任务系统
    await init_task_system()

    logger.info("Application startup complete")

    yield

    # 关闭时
    logger.info("Application shutting down...")

    # 1. 关闭任务系统
    await shutdown_task_system()

    # 2. 关闭数据库连接
    await close_db()

    logger.info("Application shutdown complete")


# 创建FastAPI应用
app = FastAPI(
    title=f"{settings.APP_NAME}",
    description="Async task execution system",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
