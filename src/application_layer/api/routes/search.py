"""
检索路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends

from src.common.logger import get_logger
from src.common.schemas import (
    APIResponse,
    NovelGenre,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from src.data_layer.mongo_client import get_mongo_client

logger = get_logger(__name__)
router = APIRouter()


@router.post("/features", response_model=APIResponse)
async def search_by_features(
    query: Optional[str] = None,
    genre: Optional[NovelGenre] = None,
    world_type: Optional[str] = None,
    power_system: Optional[str] = None,
    task_structure: Optional[str] = None,
    narrative_perspective: Optional[str] = None,
    min_confidence: float = 0.5,
    page: int = 1,
    page_size: int = 20,
):
    """
    按特征搜索小说
    
    - **query**: 文本搜索关键词
    - **genre**: 小说类型
    - **world_type**: 世界观类型
    - **power_system**: 力量体系
    - **task_structure**: 任务结构
    - **narrative_perspective**: 叙事视角
    - **min_confidence**: 最小置信度
    """
    mongo_client = await get_mongo_client()
    
    # 构建查询
    search_query = SearchQuery(
        query=query,
        genre=genre,
        min_confidence=min_confidence,
        page=page,
        page_size=page_size,
        filters={}
    )
    
    if world_type:
        search_query.filters["background.world_type"] = world_type
    if power_system:
        search_query.filters["background.power_system"] = power_system
    if task_structure:
        search_query.filters["task.task_structure"] = task_structure
    if narrative_perspective:
        search_query.filters["writing.narrative_perspective"] = narrative_perspective
    
    # 执行搜索
    results, total = await mongo_client.search_features(search_query)
    
    return APIResponse(
        data=SearchResponse(
            total=total,
            page=page,
            page_size=page_size,
            results=results,
        )
    )


@router.get("/similar/{novel_id}", response_model=APIResponse)
async def find_similar(
    novel_id: str,
    limit: int = 10,
):
    """
    查找相似小说
    
    - **novel_id**: 参考小说ID
    - **limit**: 返回数量
    """
    mongo_client = await get_mongo_client()
    
    # 获取参考小说的特征
    features = await mongo_client.get_features(novel_id)
    if not features:
        return APIResponse(
            code=404,
            message="Novel features not found",
            data=None,
        )
    
    # 构建相似性查询
    filters = {}
    if features.background.world_type:
        filters["background.world_type"] = features.background.world_type
    if features.task.task_structure:
        filters["task.task_structure"] = features.task.task_structure
    
    search_query = SearchQuery(
        filters=filters,
        min_confidence=0.6,
        page=1,
        page_size=limit + 1,  # 多取一个，排除自己
    )
    
    results, _ = await mongo_client.search_features(search_query)
    
    # 排除自己
    results = [r for r in results if r.novel_id != novel_id][:limit]
    
    return APIResponse(
        data={
            "reference_novel_id": novel_id,
            "similar_novels": results,
            "total": len(results),
        }
    )


@router.get("/stats/features", response_model=APIResponse)
async def get_feature_stats():
    """获取特征分布统计"""
    mongo_client = await get_mongo_client()
    
    # 聚合统计
    pipeline = [
        {
            "$group": {
                "_id": "$background.world_type",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    world_type_stats = []
    async for doc in mongo_client.db.novel_features.aggregate(pipeline):
        if doc["_id"]:
            world_type_stats.append({
                "world_type": doc["_id"],
                "count": doc["count"]
            })
    
    # 任务结构统计
    pipeline = [
        {
            "$group": {
                "_id": "$task.task_structure",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}}
    ]
    
    task_structure_stats = []
    async for doc in mongo_client.db.novel_features.aggregate(pipeline):
        if doc["_id"]:
            task_structure_stats.append({
                "task_structure": doc["_id"],
                "count": doc["count"]
            })
    
    return APIResponse(
        data={
            "world_type_distribution": world_type_stats,
            "task_structure_distribution": task_structure_stats,
        }
    )
