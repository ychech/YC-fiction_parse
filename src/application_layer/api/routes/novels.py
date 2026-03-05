"""
小说管理路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.common.exceptions import NotFoundException, ValidationException
from src.common.logger import get_logger
from src.common.schemas import (
    APIResponse,
    NovelCreate,
    NovelFormat,
    NovelGenre,
    NovelResponse,
    Priority,
)
from src.config.settings import settings
from src.data_layer.models import get_db
from src.data_layer.mongo_client import get_mongo_client
from src.data_layer.repositories import NovelRepository
from src.data_layer.storage import get_storage_manager
from src.service_layer.tasks.parse_tasks import submit_parse_task

logger = get_logger(__name__)
router = APIRouter()


def get_novel_repo(db: Session = Depends(get_db)) -> NovelRepository:
    """获取小说仓储"""
    return NovelRepository(db)


@router.post("/upload", response_model=APIResponse)
async def upload_novel(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    genre: Optional[NovelGenre] = Form(None),
    description: Optional[str] = Form(None),
    auto_parse: bool = Form(True),
    priority: Priority = Form(Priority.NORMAL),
    repo: NovelRepository = Depends(get_novel_repo),
):
    """
    上传小说文件
    
    - **file**: 小说文件（支持 TXT/EPUB/MOBI）
    - **title**: 书名（可选，自动提取）
    - **author**: 作者（可选，自动提取）
    - **genre**: 类型（可选）
    - **description**: 简介（可选）
    - **auto_parse**: 是否自动开始解析
    - **priority**: 解析优先级
    """
    # 验证文件格式
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in [f.value for f in NovelFormat]:
        raise ValidationException(
            f"Unsupported file format: {file_ext}",
            detail={"supported_formats": [f.value for f in NovelFormat]}
        )
    
    # 验证文件大小
    file_data = await file.read()
    if len(file_data) > settings.security.max_upload_size:
        raise ValidationException(
            "File too large",
            detail={
                "max_size": settings.security.max_upload_size,
                "actual_size": len(file_data)
            }
        )
    
    # 保存文件
    storage = get_storage_manager()
    file_info = await storage.save_upload(file_data, file.filename)
    
    # 创建小说记录
    novel_data = NovelCreate(
        title=title or file.filename.rsplit(".", 1)[0],
        author=author,
        description=description,
        genre=genre,
    )
    
    novel = repo.create_from_meta(novel_data, {
        "format": file_ext,
        "file_path": file_info["path"],
        "file_size": file_info["size"],
        "file_hash": file_info["hash"],
    })
    
    logger.info("novel_uploaded", novel_id=novel.id, title=novel.title)
    
    # 自动开始解析
    task_id = None
    if auto_parse:
        task_id = submit_parse_task(novel.id, priority)
    
    return APIResponse(
        data={
            "novel": novel,
            "task_id": task_id,
            "auto_parse": auto_parse,
        }
    )


@router.get("", response_model=APIResponse)
def list_novels(
    skip: int = 0,
    limit: int = 20,
    genre: Optional[NovelGenre] = None,
    status: Optional[str] = None,
    repo: NovelRepository = Depends(get_novel_repo),
):
    """获取小说列表"""
    novels = repo.list_all(skip=skip, limit=limit, genre=genre, status=status)
    total = 0  # 应该查询总数
    
    return APIResponse(
        data={
            "items": novels,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
    )


@router.get("/{novel_id}", response_model=APIResponse)
async def get_novel(
    novel_id: str,
    include_features: bool = True,
    repo: NovelRepository = Depends(get_novel_repo),
):
    """获取小说详情"""
    novel = repo.get_by_id(novel_id)
    if not novel:
        raise NotFoundException(f"Novel not found: {novel_id}")
    
    result = {"novel": novel}
    
    # 获取解析结果
    if include_features:
        mongo_client = await get_mongo_client()
        features = await mongo_client.get_features(novel_id)
        result["features"] = features
    
    return APIResponse(data=result)


@router.post("/{novel_id}/parse", response_model=APIResponse)
def start_parsing(
    novel_id: str,
    priority: Priority = Priority.NORMAL,
    repo: NovelRepository = Depends(get_novel_repo),
):
    """开始解析小说"""
    novel = repo.get_by_id(novel_id)
    if not novel:
        raise NotFoundException(f"Novel not found: {novel_id}")
    
    task_id = submit_parse_task(novel_id, priority)
    
    return APIResponse(
        data={
            "novel_id": novel_id,
            "task_id": task_id,
            "status": "submitted",
        }
    )


@router.delete("/{novel_id}", response_model=APIResponse)
async def delete_novel(
    novel_id: str,
    repo: NovelRepository = Depends(get_novel_repo),
):
    """删除小说"""
    novel = repo.get_by_id(novel_id)
    if not novel:
        raise NotFoundException(f"Novel not found: {novel_id}")
    
    # 删除文件
    if novel.file_path:
        storage = get_storage_manager()
        await storage.delete_file(novel.file_path)
    
    # 删除解析结果
    mongo_client = await get_mongo_client()
    await mongo_client.delete_features(novel_id)
    
    # 删除数据库记录
    repo.delete(novel_id)
    
    logger.info("novel_deleted", novel_id=novel_id)
    
    return APIResponse(data={"deleted": True})
