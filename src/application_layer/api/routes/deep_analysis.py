"""
深度解析 API 路由
提供五大核心维度的深度解析接口
"""
from typing import Optional

from fastapi import APIRouter, Depends

from src.common.deep_schemas import DeepNovelFeatures
from src.common.exceptions import NotFoundException
from src.common.logger import get_logger
from src.common.schemas import APIResponse
from src.data_layer.mongo_client import get_mongo_client
from src.data_layer.repositories import NovelRepository
from src.data_layer.storage import get_storage_manager
from src.processing_layer.deep_pipeline import DeepProcessingPipeline

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{novel_id}/deep-parse", response_model=APIResponse)
async def deep_parse_novel(
    novel_id: str,
    compare_with_benchmark: bool = True,
):
    """
    执行深度解析
    
    解析五大核心维度：
    1. 故事内核（核心冲突公式、情绪钩子分布、价值主张）
    2. 金手指/核心设定（金手指设计逻辑、世界观规则）
    3. 人物弧光与人设模板（主角弧光、配角功能、人设记忆点）
    4. 叙事节奏与写作技法（章节结构、信息释放、语言风格）
    5. 商业价值（受众画像、改编潜力、衍生价值）
    
    - **compare_with_benchmark**: 是否对比标杆库
    """
    from src.data_layer.models import get_db
    db = next(get_db())
    
    try:
        # 获取小说信息
        novel_repo = NovelRepository(db)
        novel = novel_repo.get_by_id(novel_id)
        
        if not novel:
            raise NotFoundException(f"Novel not found: {novel_id}")
        
        # 读取文件
        storage = get_storage_manager()
        file_data = await storage.read_file(novel.file_path)
        
        # 解析文本（复用原有解析器）
        from src.processing_layer.parsers import get_parser
        parser = get_parser(novel.format)
        parse_result = await parser.parse(file_data)
        
        # 准备章节数据
        chapters = [
            {
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "content": ch.content,
                "is_core": ch.is_core,
            }
            for ch in parse_result.chapters
        ]
        
        # 获取全文文本
        full_text = "\n\n".join(ch.get("content", "") for ch in chapters)
        
        # 执行深度解析
        pipeline = DeepProcessingPipeline()
        features = await pipeline.process(
            novel_id=novel_id,
            text=full_text,
            chapters=chapters,
            compare_with_benchmark=compare_with_benchmark,
        )
        
        # 保存解析结果
        mongo_client = await get_mongo_client()
        await mongo_client.db.deep_features.replace_one(
            {"novel_id": novel_id},
            features.dict(),
            upsert=True
        )
        
        # 生成公式化总结
        formula_summary = pipeline.generate_formula_summary(features)
        
        return APIResponse(
            data={
                "novel_id": novel_id,
                "deep_features": features,
                "formula_summary": formula_summary,
                "overall_quality": features.overall_quality_score,
                "consistency_check": features.consistency_check,
            }
        )
        
    finally:
        db.close()


@router.get("/{novel_id}/deep-features", response_model=APIResponse)
async def get_deep_features(novel_id: str):
    """获取深度解析结果"""
    mongo_client = await get_mongo_client()
    
    features_doc = await mongo_client.db.deep_features.find_one({"novel_id": novel_id})
    
    if not features_doc:
        raise NotFoundException(f"Deep features not found for novel: {novel_id}")
    
    features_doc.pop("_id", None)
    features = DeepNovelFeatures(**features_doc)
    
    # 生成报告
    pipeline = DeepProcessingPipeline()
    creative_report = pipeline.generate_creative_report(features)
    
    return APIResponse(
        data={
            "novel_id": novel_id,
            "deep_features": features,
            "creative_report": creative_report,
            "formula_summary": features.generate_formula_summary(),
        }
    )


@router.get("/{novel_id}/comparison-report", response_model=APIResponse)
async def get_comparison_report(novel_id: str):
    """获取对比分析报告"""
    mongo_client = await get_mongo_client()
    
    features_doc = await mongo_client.db.deep_features.find_one({"novel_id": novel_id})
    
    if not features_doc:
        raise NotFoundException(f"Deep features not found for novel: {novel_id}")
    
    features_doc.pop("_id", None)
    features = DeepNovelFeatures(**features_doc)
    
    pipeline = DeepProcessingPipeline()
    report = pipeline.generate_comparison_report(features)
    
    return APIResponse(
        data={
            "novel_id": novel_id,
            "report": report,
            "has_comparison": bool(features.benchmark_comparisons),
        }
    )


@router.get("/{novel_id}/formula-summary", response_model=APIResponse)
async def get_formula_summary(novel_id: str):
    """
    获取公式化总结
    
    示例输出：
    「底层逆袭公式」+「系统金手指(动态+情绪值约束)」+「爽点节奏(3小1大)」+「学生受众(付费点:打脸爽点)」
    """
    mongo_client = await get_mongo_client()
    
    features_doc = await mongo_client.db.deep_features.find_one({"novel_id": novel_id})
    
    if not features_doc:
        raise NotFoundException(f"Deep features not found for novel: {novel_id}")
    
    features_doc.pop("_id", None)
    features = DeepNovelFeatures(**features_doc)
    
    return APIResponse(
        data={
            "novel_id": novel_id,
            "formula_summary": features.generate_formula_summary(),
            "reusable_tags": features.reusable_tags,
        }
    )


@router.get("/{novel_id}/reverse-summary", response_model=APIResponse)
async def get_reverse_summary(novel_id: str):
    """
    获取逆向验证梗概
    
    基于解析结果反向生成的故事梗概，用于验证解析准确性
    """
    mongo_client = await get_mongo_client()
    
    features_doc = await mongo_client.db.deep_features.find_one({"novel_id": novel_id})
    
    if not features_doc:
        raise NotFoundException(f"Deep features not found for novel: {novel_id}")
    
    return APIResponse(
        data={
            "novel_id": novel_id,
            "reverse_summary": features_doc.get("reverse_summary", ""),
            "consistency_check": features_doc.get("consistency_check", 0),
        }
    )


# ==================== 标杆库管理接口 ====================

@router.post("/benchmarks", response_model=APIResponse)
async def add_benchmark(
    novel_id: str,
    title: str,
    author: str,
    genre: str,
    market_data: Optional[dict] = None,
    tags: Optional[list] = None,
):
    """添加标杆小说到基准库"""
    from src.data_layer.benchmark_repository import BenchmarkRepository
    
    # 获取深度解析结果
    mongo_client = await get_mongo_client()
    features_doc = await mongo_client.db.deep_features.find_one({"novel_id": novel_id})
    
    if not features_doc:
        raise NotFoundException(f"Deep features not found for novel: {novel_id}")
    
    features_doc.pop("_id", None)
    features = DeepNovelFeatures(**features_doc)
    
    # 添加到基准库
    repo = BenchmarkRepository()
    await repo.add_benchmark(
        novel_id=novel_id,
        title=title,
        author=author,
        genre=genre,
        features=features,
        market_data=market_data,
        tags=tags,
    )
    
    return APIResponse(
        data={
            "novel_id": novel_id,
            "added_to_benchmark": True,
        }
    )


@router.get("/benchmarks", response_model=APIResponse)
async def list_benchmarks(
    genre: Optional[str] = None,
    limit: int = 20,
):
    """获取标杆小说列表"""
    from src.data_layer.benchmark_repository import BenchmarkRepository
    
    repo = BenchmarkRepository()
    benchmarks = await repo.list_benchmarks(genre=genre, limit=limit)
    
    return APIResponse(
        data={
            "benchmarks": benchmarks,
            "total": len(benchmarks),
        }
    )


@router.get("/trending-features", response_model=APIResponse)
async def get_trending_features(
    genre: Optional[str] = None,
    days: int = 30,
):
    """获取 trending 特征"""
    from src.data_layer.benchmark_repository import BenchmarkRepository
    
    repo = BenchmarkRepository()
    trending = await repo.get_trending_features(genre=genre, days=days)
    
    return APIResponse(
        data=trending
    )
