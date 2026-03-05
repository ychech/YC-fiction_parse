"""
处理流水线 - 整合所有处理模块
"""
import hashlib
from typing import List, Optional

from src.common.logger import get_logger, log_task_progress
from src.common.schemas import Chapter, NovelFeatures, ParseTask, TaskStatus
from src.config.settings import settings
from src.data_layer.mongo_client import get_mongo_client
from src.data_layer.repositories import ParseTaskRepository
from src.processing_layer.extractors.ai_engine import AIEngine
from src.processing_layer.extractors.rule_engine import RuleEngine
from src.processing_layer.fusion.result_fusion import ResultFusionEngine
from src.processing_layer.parsers import get_parser
from src.processing_layer.parsers.base import ParseResult

logger = get_logger(__name__)


class ProcessingPipeline:
    """小说解析处理流水线"""
    
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.ai_engine = AIEngine()
        self.fusion_engine = ResultFusionEngine()
    
    async def process(
        self,
        task: ParseTask,
        file_data: bytes,
        format_type: str,
        db_session=None
    ) -> NovelFeatures:
        """
        执行完整处理流程
        
        Args:
            task: 解析任务
            file_data: 文件数据
            format_type: 文件格式
            db_session: 数据库会话
        
        Returns:
            NovelFeatures: 解析结果
        """
        task_id = task.id
        novel_id = task.novel_id
        
        logger.info("pipeline_started", task_id=task_id, novel_id=novel_id)
        
        # ========== 阶段1: 文本预处理 ==========
        await self._update_task_status(
            task_id, TaskStatus.PREPROCESSING, 0, "preprocessing", db_session
        )
        
        parse_result = await self._preprocess(file_data, format_type)
        
        await self._update_task_status(
            task_id, TaskStatus.PREPROCESSING, 100, "preprocessing", db_session
        )
        
        # 保存章节信息
        await self._save_chapters(novel_id, parse_result)
        
        # ========== 阶段2: 特征提取 ==========
        await self._update_task_status(
            task_id, TaskStatus.EXTRACTING, 0, "feature_extraction", db_session
        )
        
        features = await self._extract_features(task, parse_result)
        
        await self._update_task_status(
            task_id, TaskStatus.EXTRACTING, 100, "feature_extraction", db_session
        )
        
        # ========== 阶段3: 结果融合（可选）==========
        if settings.processing.enable_fusion:
            await self._update_task_status(
                task_id, TaskStatus.FUSING, 0, "result_fusion", db_session
            )
            
            # 融合已经在 _extract_features 中完成
            
            await self._update_task_status(
                task_id, TaskStatus.FUSING, 100, "result_fusion", db_session
            )
        
        # ========== 阶段4: 保存结果 ==========
        features.novel_id = novel_id
        
        mongo_client = await get_mongo_client()
        await mongo_client.save_features(features)
        
        logger.info(
            "pipeline_completed",
            task_id=task_id,
            novel_id=novel_id,
            confidence=features.confidence_score
        )
        
        return features
    
    async def _preprocess(self, file_data: bytes, format_type: str) -> ParseResult:
        """文本预处理"""
        logger.info("preprocessing_started", format=format_type)
        
        # 获取解析器
        parser = get_parser(format_type)
        
        # 解析文件
        result = await parser.parse(file_data)
        
        logger.info(
            "preprocessing_completed",
            chapters=len(result.chapters),
            word_count=result.total_word_count
        )
        
        return result
    
    async def _extract_features(
        self,
        task: ParseTask,
        parse_result: ParseResult
    ) -> NovelFeatures:
        """特征提取"""
        logger.info("feature_extraction_started")
        
        # 准备文本
        chapters_data = [
            {
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "content": ch.content,
                "is_core": ch.is_core
            }
            for ch in parse_result.chapters
        ]
        
        # 获取核心章节文本
        core_text = "\n\n".join(
            ch.content for ch in parse_result.chapters if ch.is_core
        )
        
        # 如果没有核心章节，使用前10章
        if not core_text:
            core_text = "\n\n".join(
                ch.content for ch in parse_result.chapters[:10]
            )
        
        rule_features = None
        ai_features = None
        
        # 规则引擎提取
        if settings.processing.enable_rule_engine:
            logger.debug("rule_extraction_started")
            rule_features = self.rule_engine.extract_features(core_text, chapters_data)
            logger.debug("rule_extraction_completed", confidence=rule_features.confidence_score)
        
        # AI 引擎提取
        if settings.processing.enable_ai_engine:
            logger.debug("ai_extraction_started")
            ai_features = await self.ai_engine.extract_from_chapters(
                chapters_data,
                strategy="core_first"
            )
            logger.debug("ai_extraction_completed", confidence=ai_features.confidence_score)
        
        # 结果融合
        if rule_features and ai_features:
            logger.debug("fusion_started")
            fused_features = self.fusion_engine.fuse(
                rule_features, ai_features, task.novel_id
            )
            
            # 验证结果
            is_valid, issues = self.fusion_engine.validate_result(fused_features)
            if not is_valid:
                logger.warning("fusion_validation_failed", issues=issues)
            
            return fused_features
        
        # 如果只有一个引擎有结果
        if rule_features:
            rule_features.novel_id = task.novel_id
            return rule_features
        if ai_features:
            ai_features.novel_id = task.novel_id
            return ai_features
        
        # 都没有结果，返回空特征
        return NovelFeatures(novel_id=task.novel_id)
    
    async def _save_chapters(self, novel_id: str, parse_result: ParseResult):
        """保存章节信息"""
        mongo_client = await get_mongo_client()
        
        chapters_data = []
        for ch in parse_result.chapters:
            chapter_hash = hashlib.md5(ch.content.encode()).hexdigest()
            chapters_data.append({
                "novel_id": novel_id,
                "chapter_number": ch.chapter_number,
                "title": ch.title,
                "word_count": ch.word_count,
                "is_core": ch.is_core,
                "chapter_hash": chapter_hash,
            })
        
        await mongo_client.save_chapters(novel_id, chapters_data)
        logger.debug("chapters_saved", count=len(chapters_data))
    
    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: float,
        stage: str,
        db_session=None
    ):
        """更新任务状态"""
        if db_session:
            repo = ParseTaskRepository(db_session)
            repo.update_status(task_id, status, progress, stage)
        
        log_task_progress(logger, task_id, stage, progress)
    
    async def process_incremental(
        self,
        novel_id: str,
        new_chapters: List[Chapter],
        db_session=None
    ) -> Optional[NovelFeatures]:
        """
        增量解析 - 只解析新增章节
        
        Args:
            novel_id: 小说ID
            new_chapters: 新增章节
            db_session: 数据库会话
        
        Returns:
            更新后的特征，如果没有变化则返回 None
        """
        logger.info("incremental_parsing_started", novel_id=novel_id, new_chapters=len(new_chapters))
        
        mongo_client = await get_mongo_client()
        
        # 检查哪些章节是真正的新增
        truly_new = []
        for ch in new_chapters:
            chapter_hash = hashlib.md5(ch.content.encode()).hexdigest()
            existing = await mongo_client.get_chapter_by_hash(chapter_hash)
            if not existing:
                truly_new.append(ch)
        
        if not truly_new:
            logger.info("no_new_chapters", novel_id=novel_id)
            return None
        
        logger.info("truly_new_chapters", count=len(truly_new))
        
        # 获取现有特征
        existing_features = await mongo_client.get_features(novel_id)
        
        # 准备新章节的文本
        new_text = "\n\n".join(ch.content for ch in truly_new)
        
        # 提取新章节的特征
        new_features_rule = self.rule_engine.extract_features(new_text)
        new_features_ai = await self.ai_engine.extract_features(new_text)
        new_features = self.fusion_engine.fuse(
            new_features_rule, new_features_ai, novel_id
        )
        
        # 合并特征（简化处理：如果新特征置信度更高，则替换）
        if existing_features:
            merged = self._merge_features(existing_features, new_features)
        else:
            merged = new_features
        
        # 保存更新后的特征
        await mongo_client.save_features(merged)
        
        logger.info("incremental_parsing_completed", novel_id=novel_id)
        
        return merged
    
    def _merge_features(
        self,
        existing: NovelFeatures,
        new: NovelFeatures
    ) -> NovelFeatures:
        """合并新旧特征"""
        # 简化策略：保留置信度更高的字段
        # 实际项目中可以更精细地合并
        
        if new.confidence_score > existing.confidence_score:
            return new
        
        return existing
