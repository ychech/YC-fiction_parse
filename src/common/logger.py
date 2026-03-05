"""
结构化日志配置
"""
import logging
import sys
from typing import Any, Dict

import structlog

from src.config.settings import settings


def configure_logging() -> None:
    """配置结构化日志"""
    
    # 基础日志配置
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.monitoring.log_level.upper()),
    )
    
    # 配置 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.monitoring.log_format == "json" 
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取日志记录器"""
    return structlog.get_logger(name)


class LogContext:
    """日志上下文管理器"""
    
    def __init__(self, **context: Any):
        self.context = context
        self.logger = structlog.get_logger()
    
    def __enter__(self) -> structlog.stdlib.BoundLogger:
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


def log_task_progress(
    logger: structlog.stdlib.BoundLogger,
    task_id: str,
    stage: str,
    progress: float,
    extra: Dict[str, Any] = None
) -> None:
    """记录任务进度日志"""
    data = {
        "task_id": task_id,
        "stage": stage,
        "progress": progress,
    }
    if extra:
        data.update(extra)
    logger.info("task_progress", **data)
