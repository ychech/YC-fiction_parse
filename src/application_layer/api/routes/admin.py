"""
管理后台路由
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from src.common.logger import get_logger
from src.common.schemas import APIResponse, Rule, RuleSet
from src.config.settings import settings
from src.data_layer.mongo_client import get_mongo_client
from src.data_layer.repositories import RuleSetRepository
from src.processing_layer.extractors.rule_engine import RuleEngine

logger = get_logger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=APIResponse)
async def get_dashboard():
    """获取仪表盘数据"""
    mongo_client = await get_mongo_client()
    
    # 统计
    total_novels = await mongo_client.db.novel_features.count_documents({})
    
    # 今日新增
    from datetime import datetime, timedelta
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_new = await mongo_client.db.novel_features.count_documents({
        "created_at": {"$gte": today}
    })
    
    # 平均置信度
    pipeline = [
        {
            "$group": {
                "_id": None,
                "avg_confidence": {"$avg": "$confidence_score"}
            }
        }
    ]
    
    avg_confidence = 0
    async for doc in mongo_client.db.novel_features.aggregate(pipeline):
        avg_confidence = doc.get("avg_confidence", 0)
    
    return APIResponse(
        data={
            "total_novels": total_novels,
            "today_new": today_new,
            "avg_confidence": round(avg_confidence, 2),
            "system_version": settings.app_version,
        }
    )


@router.get("/rules", response_model=APIResponse)
def list_rules():
    """获取所有规则"""
    engine = RuleEngine()
    
    return APIResponse(
        data={
            "rules": [rule.dict() for rule in engine.rules],
            "total": len(engine.rules),
        }
    )


@router.post("/rules", response_model=APIResponse)
def create_rule(rule: Rule):
    """创建新规则"""
    # 这里应该保存到数据库
    logger.info("rule_created", rule_id=rule.id, rule_name=rule.name)
    
    return APIResponse(
        data={"rule": rule, "created": True}
    )


@router.put("/rules/{rule_id}", response_model=APIResponse)
def update_rule(rule_id: str, rule: Rule):
    """更新规则"""
    logger.info("rule_updated", rule_id=rule_id, rule_name=rule.name)
    
    return APIResponse(
        data={"rule": rule, "updated": True}
    )


@router.delete("/rules/{rule_id}", response_model=APIResponse)
def delete_rule(rule_id: str):
    """删除规则"""
    logger.info("rule_deleted", rule_id=rule_id)
    
    return APIResponse(
        data={"rule_id": rule_id, "deleted": True}
    )


@router.get("/system/config", response_model=APIResponse)
def get_system_config():
    """获取系统配置"""
    return APIResponse(
        data={
            "ai": {
                "model": settings.ai.openai_model,
                "use_local": settings.ai.use_local_model,
            },
            "processing": {
                "enable_rule_engine": settings.processing.enable_rule_engine,
                "enable_ai_engine": settings.processing.enable_ai_engine,
                "enable_fusion": settings.processing.enable_fusion,
            },
            "storage": {
                "type": settings.db.storage_type,
            },
        }
    )


@router.post("/system/config", response_model=APIResponse)
def update_system_config(config: Dict[str, Any]):
    """更新系统配置"""
    # 这里应该更新配置并热加载
    logger.info("system_config_updated", config=config)
    
    return APIResponse(
        data={"updated": True}
    )


@router.get("/logs", response_model=APIResponse)
def get_logs(
    level: str = "INFO",
    limit: int = 100,
):
    """获取系统日志"""
    # 这里应该从日志系统获取
    return APIResponse(
        data={
            "logs": [],
            "level": level,
            "limit": limit,
        }
    )


@router.post("/maintenance/cleanup", response_model=APIResponse)
def cleanup_system(
    days: int = 7,
):
    """清理系统数据"""
    from src.service_layer.tasks.parse_tasks import cleanup_old_tasks
    
    result = cleanup_old_tasks.delay(days)
    
    return APIResponse(
        data={
            "cleanup_started": True,
            "task_id": result.id,
            "days": days,
        }
    )
