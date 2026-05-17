"""
日志封装模块
支持自动从请求header中提取并打印requestid
"""

import contextvars
import logging
from contextlib import contextmanager
from typing import Optional

from fastapi import Request

# 定义上下文变量
_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


class RequestContextFilter(logging.Filter):
    """日志过滤器，用于自动添加request_id到日志记录中"""

    def set_context(self, request_id: Optional[str] = None):
        """设置当前上下文的request_id"""
        if request_id is not None:
            _request_id_var.set(request_id)

    def set_request_id(self, request_id: Optional[str]):
        """设置当前上下文的request_id"""
        if request_id is not None:
            _request_id_var.set(request_id)

    def get_request_id(self) -> Optional[str]:
        """获取当前上下文的request_id"""
        return _request_id_var.get()

    def clear_context(self):
        """清除当前上下文的request_id"""
        # 使用 set_token 来清除变量
        _request_id_var.set(None)

    def clear_request_id(self):
        """清除当前上下文的request_id"""
        _request_id_var.set(None)

    def filter(self, record):
        """为日志记录添加request_id字段"""
        request_id = self.get_request_id()

        record.request_id = request_id if request_id else "N/A"
        return True


# 全局请求上下文过滤器实例
_context_filter = RequestContextFilter()


class Logger:
    """日志封装类"""

    def __init__(self, name: str | None = None):
        self.logger = logging.getLogger(name or __name__)
        self._setup_logger()

    def _setup_logger(self):
        """配置日志格式"""
        # 防止重复添加处理器
        if self.logger.handlers:
            return

        # 创建处理器
        handler = logging.StreamHandler()

        # 设置日志格式，包含request_id和行号（向上跳一级）
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [request_id:%(request_id)s] - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # 添加上下文过滤器
        self.logger.addFilter(_context_filter)

        # 设置日志级别
        self.logger.setLevel(logging.DEBUG)

        # 防止日志传播到根logger，避免重复输出
        self.logger.propagate = False

    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(message, *args, **kwargs, stacklevel=2)

    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(message, *args, **kwargs, stacklevel=2)

    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(message, *args, **kwargs, stacklevel=2)

    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(message, *args, **kwargs, stacklevel=2)

    def exception(self, message: str, *args, **kwargs):
        """异常日志"""
        self.logger.exception(message, *args, **kwargs, stacklevel=2)


def extract_request_id(
    request: Request, header_name: str = "X-Request-ID"
) -> Optional[str]:
    """
    从请求header中提取request_id

    Args:
        request: Starlette请求对象
        header_name: header名称，默认为'X-Request-ID'

    Returns:
        request_id字符串或None
    """
    return request.headers.get(header_name) or request.headers.get("requestid")


@contextmanager
def request_context(
    request: Request,
    request_header_name: str = "X-Request-ID",
):
    """
    请求上下文管理器，自动设置和清理request_id

    Args:
        request: Starlette请求对象
        request_header_name: request_id的header名称，默认为'X-Request-ID'
    """
    request_id = extract_request_id(request, request_header_name)

    _context_filter.set_context(
        request_id=request_id,
    )
    try:
        yield
    finally:
        _context_filter.clear_context()


def set_request_id(request_id: str):
    """
    手动设置request_id

    Args:
        request_id: request_id字符串
    """
    _context_filter.set_request_id(request_id)


def get_request_id() -> Optional[str]:
    """
    获取当前上下文的request_id

    Returns:
        request_id字符串或None
    """
    return _context_filter.get_request_id()


def set_context(request_id: str | None = None):
    """
    手动设置request_id

    Args:
        request_id: request_id字符串
    """
    _context_filter.set_context(request_id=request_id)


def clear_request_id():
    """清除当前线程的request_id"""
    _context_filter.clear_request_id()


def clear_context():
    """清除当前线程的上下文（request_id）"""
    _context_filter.clear_context()


# 便捷的logger实例
logger = Logger()
