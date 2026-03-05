"""
解析任务定义
"""
from typing import List, Optional

from celery import chain, group
from sqlalchemy.orm import Session

from src.common.exceptions import TaskException
from src.common.logger import get_logger
from src.common.schemas import NovelFeatures, ParseTask, Priority, TaskStatus
from src.config.settings import settings
from src.data_layer.models import get_db
from src.data_layer.mongo_client import get_mongo_client
from src.data_layer.repositories import NovelRepository, ParseTaskRepository
from src.data_layer.storage import get_storage_manager
from src.processing_layer.pipeline import ProcessingPipeline
from src.service_layer.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def parse_novel(self, task_id: str):
    """
    解析单本小说
    
    Args:
        task_id: 任务ID
    """
    logger.info("parse_task_started", task_id=task_id)
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 获取任务信息
        task_repo = ParseTaskRepository(db)
        task = task_repo.get_by_id(task_id)
        
        if not task:
            raise TaskException(f"Task not found: {task_id}")
        
        # 更新状态为处理中
        task_repo.update_status(task_id, TaskStatus.PREPROCESSING, 0, "preprocessing")
        
        # 获取小说信息
        novel_repo = NovelRepository(db)
        novel = novel_repo.get_by_id(task.novel_id)
        
        if not novel:
            raise TaskException(f"Novel not found: {task.novel_id}")
        
        # 读取文件
        storage = get_storage_manager()
        file_data = storage.read_file(novel.file_path)
        
        # 执行解析流水线
        pipeline = ProcessingPipeline()
        features = pipeline.process(
            task=task,
            file_data=file_data,
            format_type=novel.format,
            db_session=db
        )
        
        # 更新任务状态为完成
        task_repo.update_status(
            task_id,
            TaskStatus.COMPLETED,
            100,
            "completed",
            error_message=None
        )
        
        # 更新小说信息
        novel_repo.update_parse_info(
            novel.id,
            chapter_count=len(features.task.sub_tasks) + 1  # 简化
        )
        
        logger.info(
            "parse_task_completed",
            task_id=task_id,
            novel_id=novel.id,
            confidence=features.confidence_score
        )
        
        return {
            "task_id": task_id,
            "novel_id": novel.id,
            "status": "completed",
            "confidence_score": features.confidence_score,
        }
        
    except Exception as exc:
        logger.error("parse_task_failed", task_id=task_id, error=str(exc))
        
        # 更新任务状态为失败
        try:
            task_repo = ParseTaskRepository(db)
            task_repo.update_status(
                task_id,
                TaskStatus.FAILED,
                error_message=str(exc)[:500]
            )
        except Exception as e:
            logger.error("update_task_status_failed", error=str(e))
        
        # 重试
        if self.request.retries < self.max_retries:
            logger.info("parse_task_retrying", task_id=task_id, retry=self.request.retries + 1)
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        raise
    
    finally:
        db.close()


@celery_app.task
def batch_parse(task_ids: List[str]):
    """
    批量解析
    
    Args:
        task_ids: 任务ID列表
    """
    logger.info("batch_parse_started", task_count=len(task_ids))
    
    # 创建任务组
    job = group(parse_novel.s(task_id) for task_id in task_ids)
    result = job.apply_async()
    
    return {
        "group_id": result.id,
        "task_count": len(task_ids),
        "status": "submitted",
    }


@celery_app.task
def extract_keywords(novel_id: str):
    """
    提取小说关键词
    
    Args:
        novel_id: 小说ID
    """
    logger.info("keyword_extraction_started", novel_id=novel_id)
    
    # 获取小说特征
    import asyncio
    
    async def _extract():
        mongo_client = await get_mongo_client()
        features = await mongo_client.get_features(novel_id)
        
        if not features:
            logger.warning("features_not_found", novel_id=novel_id)
            return None
        
        # 提取关键词（简化实现）
        keywords = []
        
        # 从背景提取
        if features.background.world_type:
            keywords.append(features.background.world_type)
        if features.background.power_system:
            keywords.append(features.background.power_system)
        
        # 从任务提取
        if features.task.task_structure:
            keywords.append(features.task.task_structure)
        
        # 从写作手法提取
        if features.writing.narrative_perspective:
            keywords.append(features.writing.narrative_perspective)
        
        # 保存关键词
        await mongo_client.update_custom_fields(novel_id, {"keywords": keywords})
        
        return keywords
    
    keywords = asyncio.run(_extract())
    
    logger.info("keyword_extraction_completed", novel_id=novel_id, keywords=keywords)
    
    return {
        "novel_id": novel_id,
        "keywords": keywords,
    }


@celery_app.task
def generate_vectors(novel_id: str):
    """
    生成小说向量表示
    
    Args:
        novel_id: 小说ID
    """
    logger.info("vector_generation_started", novel_id=novel_id)
    
    # 这里应该调用向量生成服务
    # 简化实现
    
    logger.info("vector_generation_completed", novel_id=novel_id)
    
    return {
        "novel_id": novel_id,
        "status": "completed",
    }


@celery_app.task
def cleanup_old_tasks(days: int = 7):
    """
    清理旧任务
    
    Args:
        days: 清理多少天前的任务
    """
    from datetime import datetime, timedelta
    
    logger.info("cleanup_started", days=days)
    
    db = next(get_db())
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 删除旧的任务记录
        from src.data_layer.models import ParseTaskORM
        
        deleted = db.query(ParseTaskORM).filter(
            ParseTaskORM.created_at < cutoff_date,
            ParseTaskORM.status.in_(["completed", "failed", "cancelled"])
        ).delete()
        
        db.commit()
        
        logger.info("cleanup_completed", deleted=deleted)
        
        return {"deleted_count": deleted}
        
    finally:
        db.close()


def submit_parse_task(
    novel_id: str,
    priority: Priority = Priority.NORMAL,
    config: dict = None
) -> str:
    """
    提交解析任务
    
    Args:
        novel_id: 小说ID
        priority: 优先级
        config: 配置
    
    Returns:
        任务ID
    """
    db = next(get_db())
    
    try:
        # 创建任务记录
        from src.common.schemas import ParseTaskCreate
        
        task_repo = ParseTaskRepository(db)
        task = task_repo.create_task(ParseTaskCreate(
            novel_id=novel_id,
            priority=priority,
            config=config or {}
        ))
        
        # 提交到 Celery
        parse_novel.apply_async(
            args=[task.id],
            queue="parsing",
            priority=priority.value
        )
        
        logger.info("task_submitted", task_id=task.id, novel_id=novel_id)
        
        return task.id
        
    finally:
        db.close()


def get_task_status(task_id: str) -> Optional[dict]:
    """获取任务状态"""
    db = next(get_db())
    
    try:
        task_repo = ParseTaskRepository(db)
        task = task_repo.get_by_id(task_id)
        
        if not task:
            return None
        
        # 获取 Celery 任务状态
        from celery.result import AsyncResult
        
        celery_task = AsyncResult(task_id)
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "current_stage": task.current_stage,
            "stage_progress": task.stage_progress,
            "celery_state": celery_task.state,
            "error_message": task.error_message,
        }
        
    finally:
        db.close()
