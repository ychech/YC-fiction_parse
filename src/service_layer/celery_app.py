"""
Celery 任务队列配置
"""
from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun

from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

# 创建 Celery 应用
celery_app = Celery(
    "novel_parser",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "src.service_layer.tasks.parse_tasks",
    ]
)

# 配置
celery_app.conf.update(
    task_serializer=settings.celery.task_serializer,
    accept_content=settings.celery.accept_content,
    result_serializer=settings.celery.result_serializer,
    timezone=settings.celery.timezone,
    enable_utc=settings.celery.enable_utc,
    task_track_started=settings.celery.task_track_started,
    task_time_limit=settings.celery.task_time_limit,
    worker_prefetch_multiplier=settings.celery.worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery.worker_max_tasks_per_child,
    
    # 任务路由
    task_routes={
        "src.service_layer.tasks.parse_tasks.parse_novel": {"queue": "parsing"},
        "src.service_layer.tasks.parse_tasks.batch_parse": {"queue": "parsing"},
        "src.service_layer.tasks.parse_tasks.extract_keywords": {"queue": "analysis"},
    },
    
    # 任务默认配置
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)


# ========== 信号处理 ==========

@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """任务开始前的处理"""
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task.name,
    )


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **extras):
    """任务完成后的处理"""
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task.name,
        state=state,
    )


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extras):
    """任务失败处理"""
    logger.error(
        "task_failed",
        task_id=task_id,
        exception=str(exception),
        traceback=traceback,
    )


# 启动命令:
# celery -A src.service_layer.celery_app worker -l info -Q parsing,analysis,default
# celery -A src.service_layer.celery_app flower --port=5555
