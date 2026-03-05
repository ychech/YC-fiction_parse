"""
结果融合模块 - 融合规则引擎和 AI 引擎的结果
"""
from typing import Any, Dict, List, Optional, Tuple

from src.common.logger import get_logger
from src.common.schemas import (
    BackgroundFeatures,
    CharacterFeatures,
    NovelFeatures,
    PlotFeatures,
    TaskFeatures,
    WritingFeatures,
)
from src.config.settings import settings

logger = get_logger(__name__)


class ResultFusionEngine:
    """结果融合引擎"""
    
    def __init__(self):
        self.rule_weight = 0.4  # 规则引擎权重
        self.ai_weight = 0.6    # AI引擎权重
        self.confidence_threshold = 0.7
    
    def fuse(
        self,
        rule_features: NovelFeatures,
        ai_features: NovelFeatures,
        novel_id: str
    ) -> NovelFeatures:
        """
        融合两个引擎的结果
        
        Args:
            rule_features: 规则引擎结果
            ai_features: AI引擎结果
            novel_id: 小说ID
        
        Returns:
            NovelFeatures: 融合后的结果
        """
        logger.info(
            "fusion_started",
            rule_confidence=rule_features.confidence_score,
            ai_confidence=ai_features.confidence_score
        )
        
        fused = NovelFeatures(
            novel_id=novel_id,
            task=self._fuse_task(rule_features.task, ai_features.task),
            background=self._fuse_background(rule_features.background, ai_features.background),
            character=self._fuse_character(rule_features.character, ai_features.character),
            writing=self._fuse_writing(rule_features.writing, ai_features.writing),
            plot=self._fuse_plot(rule_features.plot, ai_features.plot),
            extraction_method="fusion"
        )
        
        # 计算融合后的置信度
        fused.confidence_score = self._calculate_fusion_confidence(
            rule_features, ai_features, fused
        )
        
        logger.info("fusion_completed", confidence=fused.confidence_score)
        
        return fused
    
    def _fuse_task(
        self,
        rule: TaskFeatures,
        ai: TaskFeatures
    ) -> TaskFeatures:
        """融合任务特征"""
        return TaskFeatures(
            main_task=self._select_best(rule.main_task, ai.main_task, ai_weight=0.7),
            sub_tasks=self._merge_lists(rule.sub_tasks, ai.sub_tasks),
            task_structure=self._select_best(
                rule.task_structure,
                ai.task_structure,
                ai_weight=0.6
            ),
            task_difficulty=self._select_best(
                rule.task_difficulty,
                ai.task_difficulty,
                ai_weight=0.7
            )
        )
    
    def _fuse_background(
        self,
        rule: BackgroundFeatures,
        ai: BackgroundFeatures
    ) -> BackgroundFeatures:
        """融合背景特征"""
        # 世界观类型：规则引擎更擅长关键词匹配
        world_type = self._select_best(
            rule.world_type,
            ai.world_type,
            ai_weight=0.4  # 规则引擎权重更高
        )
        
        return BackgroundFeatures(
            world_type=world_type,
            era_setting=self._select_best(rule.era_setting, ai.era_setting, ai_weight=0.6),
            power_system=self._select_best(
                rule.power_system,
                ai.power_system,
                ai_weight=0.3  # 规则引擎更擅长力量体系识别
            ),
            major_factions=self._merge_lists(rule.major_factions, ai.major_factions),
            world_rules=self._merge_lists(rule.world_rules, ai.world_rules)
        )
    
    def _fuse_character(
        self,
        rule: CharacterFeatures,
        ai: CharacterFeatures
    ) -> CharacterFeatures:
        """融合人设特征"""
        # 人设主要依赖 AI 提取
        return CharacterFeatures(
            protagonist=ai.protagonist or rule.protagonist,
            supporting_roles=ai.supporting_roles or rule.supporting_roles,
            character_archetypes=self._merge_lists(
                rule.character_archetypes,
                ai.character_archetypes
            ),
            character_relationships=ai.character_relationships or rule.character_relationships
        )
    
    def _fuse_writing(
        self,
        rule: WritingFeatures,
        ai: WritingFeatures
    ) -> WritingFeatures:
        """融合写作手法特征"""
        # 叙事视角：规则引擎更可靠
        perspective = self._select_best(
            rule.narrative_perspective,
            ai.narrative_perspective,
            ai_weight=0.3
        )
        
        return WritingFeatures(
            narrative_perspective=perspective,
            pacing=self._select_best(rule.pacing, ai.pacing, ai_weight=0.5),
            rhetoric_style=self._merge_lists(rule.rhetoric_style, ai.rhetoric_style),
            sentence_structure=self._select_best(
                rule.sentence_structure,
                ai.sentence_structure,
                ai_weight=0.6
            ),
            humor_style=self._select_best(rule.humor_style, ai.humor_style, ai_weight=0.5),
            suspense_techniques=self._merge_lists(
                rule.suspense_techniques,
                ai.suspense_techniques
            )
        )
    
    def _fuse_plot(
        self,
        rule: PlotFeatures,
        ai: PlotFeatures
    ) -> PlotFeatures:
        """融合情节特征"""
        # 冲突类型：合并两个来源
        conflict_types = self._merge_lists(rule.conflict_types, ai.conflict_types)
        
        # 反转次数：优先使用 AI 的数字
        plot_twists = ai.plot_twists if ai.plot_twists > 0 else rule.plot_twists
        
        return PlotFeatures(
            plot_structure=self._select_best(
                rule.plot_structure,
                ai.plot_structure,
                ai_weight=0.7
            ),
            conflict_types=conflict_types,
            plot_twists=plot_twists,
            climax_distribution=self._select_best(
                rule.climax_distribution,
                ai.climax_distribution,
                ai_weight=0.6
            ),
            foreshadowing=self._merge_lists(rule.foreshadowing, ai.foreshadowing)
        )
    
    def _select_best(
        self,
        rule_value: Optional[Any],
        ai_value: Optional[Any],
        ai_weight: float = 0.5
    ) -> Optional[Any]:
        """
        选择最佳值
        
        策略：
        1. 如果只有一个有值，使用那个
        2. 如果两个都有值，根据权重选择
        3. 如果两个都为空，返回 None
        """
        if rule_value is None:
            return ai_value
        if ai_value is None:
            return rule_value
        
        # 如果值相同，直接返回
        if rule_value == ai_value:
            return ai_value
        
        # 根据权重选择
        # 这里简化处理，实际可以基于置信度做更复杂的决策
        if ai_weight >= 0.5:
            return ai_value
        else:
            return rule_value
    
    def _merge_lists(
        self,
        rule_list: List[Any],
        ai_list: List[Any]
    ) -> List[Any]:
        """合并列表，去重"""
        merged = []
        seen = set()
        
        # 优先添加 AI 的结果（通常更全面）
        for item in ai_list:
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
        
        # 添加规则引擎的结果（补充）
        for item in rule_list:
            if item and item not in seen:
                merged.append(item)
                seen.add(item)
        
        return merged
    
    def _calculate_fusion_confidence(
        self,
        rule_features: NovelFeatures,
        ai_features: NovelFeatures,
        fused: NovelFeatures
    ) -> float:
        """计算融合后的置信度"""
        # 基础置信度：两个引擎的加权平均
        base_confidence = (
            self.rule_weight * rule_features.confidence_score +
            self.ai_weight * ai_features.confidence_score
        )
        
        # 一致性奖励：如果两个引擎结果一致，增加置信度
        consistency_bonus = self._calculate_consistency(
            rule_features, ai_features
        )
        
        # 完整性奖励：字段越完整，置信度越高
        completeness = self._calculate_completeness(fused)
        
        # 最终置信度
        final_confidence = (
            base_confidence * 0.6 +
            consistency_bonus * 0.2 +
            completeness * 0.2
        )
        
        return min(final_confidence, 1.0)
    
    def _calculate_consistency(
        self,
        rule: NovelFeatures,
        ai: NovelFeatures
    ) -> float:
        """计算两个结果的一致性"""
        matches = 0
        total = 0
        
        # 检查世界观类型
        if rule.background.world_type and ai.background.world_type:
            total += 1
            if rule.background.world_type == ai.background.world_type:
                matches += 1
        
        # 检查力量体系
        if rule.background.power_system and ai.background.power_system:
            total += 1
            if rule.background.power_system == ai.background.power_system:
                matches += 1
        
        # 检查叙事视角
        if rule.writing.narrative_perspective and ai.writing.narrative_perspective:
            total += 1
            if rule.writing.narrative_perspective == ai.writing.narrative_perspective:
                matches += 1
        
        # 检查任务结构
        if rule.task.task_structure and ai.task.task_structure:
            total += 1
            if rule.task.task_structure == ai.task.task_structure:
                matches += 1
        
        return matches / total if total > 0 else 0.5
    
    def _calculate_completeness(self, features: NovelFeatures) -> float:
        """计算结果完整性"""
        fields = []
        
        # 任务特征
        fields.append(features.task.main_task is not None)
        fields.append(features.task.task_structure is not None)
        fields.append(len(features.task.sub_tasks) > 0)
        
        # 背景特征
        fields.append(features.background.world_type is not None)
        fields.append(features.background.power_system is not None)
        
        # 人设特征
        fields.append(features.character.protagonist is not None)
        
        # 写作特征
        fields.append(features.writing.narrative_perspective is not None)
        fields.append(features.writing.pacing is not None)
        
        # 情节特征
        fields.append(features.plot.plot_structure is not None)
        fields.append(len(features.plot.conflict_types) > 0)
        
        return sum(fields) / len(fields) if fields else 0
    
    def validate_result(self, features: NovelFeatures) -> Tuple[bool, List[str]]:
        """
        验证融合结果
        
        Returns:
            (是否有效, 问题列表)
        """
        issues = []
        
        # 检查置信度
        if features.confidence_score < self.confidence_threshold:
            issues.append(f"Confidence score too low: {features.confidence_score}")
        
        # 检查必要字段
        if not features.background.world_type:
            issues.append("Missing world_type")
        
        if not features.task.task_structure:
            issues.append("Missing task_structure")
        
        # 检查数据一致性
        if features.background.world_type == "仙侠" and not features.background.power_system:
            issues.append("Xianxia novel missing power_system")
        
        return len(issues) == 0, issues
