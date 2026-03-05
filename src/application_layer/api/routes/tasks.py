"""
解析任务路由
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.common.exceptions import NotFoundException
from src.common.logger import get_logger
from src.common.schemas import APIResponse, Priority
from src.data_layer.models import get_db
from src.data_layer.repositories import ParseTaskRepository
from src.service_layer.tasks.parse_tasks import get_task_status, submit_parse_task

logger = get_logger(__name__)
router = APIRouter()


def get_task_repo(db: Session = Depends(get_db)) -> ParseTaskRepository:
    """获取任务仓储"""
    return ParseTaskRepository(db)


@router.get("/{task_id}", response_model=APIResponse)
def get_task(
    task_id: str,
    repo: ParseTaskRepository = Depends(get_task_repo),
):
    """获取任务状态"""
    status = get_task_status(task_id)
    
    if not status:
        raise NotFoundException(f"Task not found: {task_id}")
    
    return APIResponse(data=status)


@router.post("/batch", response_model=APIResponse)
def batch_create_tasks(
    novel_ids: List[str],
    priority: Priority = Priority.NORMAL,
    repo: ParseTaskRepository = Depends(get_task_repo),
):
    """
    批量创建解析任务
    
    - **novel_ids**: 小说ID列表
    - **priority**: 任务优先级
    """
    task_ids = []
    
    for novel_id in novel_ids:
        task_id = submit_parse_task(novel_id, priority)
        task_ids.append({
            "novel_id": novel_id,
            "task_id": task_id,
        })
    
    return APIResponse(
        data={
            "tasks": task_ids,
            "total": len(task_ids),
        }
    )


@router.get("", response_model=APIResponse)
def list_tasks(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    repo: ParseTaskRepository = Depends(get_task_repo),
):
    """获取任务列表"""
    tasks = repo.list_all(skip=skip, limit=limit, status=status)
    
    return APIResponse(
        data={
            "items": tasks,
            "skip": skip,
            "limit": limit,
        }
    )
