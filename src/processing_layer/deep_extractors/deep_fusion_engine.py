"""
深度解析结果融合引擎
整合五大维度的解析结果，生成公式化总结
"""
from typing import Any, Dict, List

from src.common.deep_schemas import (
    CharacterAnalysis,
    CommercialValue,
    CoreSetting,
    DeepNovelFeatures,
    NarrativeTechnique,
    StoryCore,
)
from src.common.logger import get_logger

logger = get_logger(__name__)


class DeepFusionEngine:
    """深度解析融合引擎"""
    
    def __init__(self):
        self.benchmark_db = None  # 对比基准库，后续可注入
    
    def fuse(
        self,
        novel_id: str,
        story_core: StoryCore,
        core_setting: CoreSetting,
        character_analysis: CharacterAnalysis,
        narrative_technique: NarrativeTechnique,
        commercial_value: CommercialValue,
    ) -> DeepNovelFeatures:
        """
        融合五大维度解析结果
        
        Returns:
            DeepNovelFeatures: 完整的深度解析结果
        """
        logger.info("deep_fusion_started", novel_id=novel_id)
        
        # 1. 计算整体质量评分
        overall_quality = self._calculate_overall_quality(
            story_core, core_setting, character_analysis, narrative_technique
        )
        
        # 2. 生成可复用标签
        reusable_tags = self._generate_reusable_tags(
            story_core, core_setting, character_analysis
        )
        
        # 3. 生成逆向验证梗概
        reverse_summary = self._generate_reverse_summary(
            story_core, core_setting, character_analysis
        )
        
        # 4. 执行一致性检查
        consistency_check = self._check_consistency(
            story_core, core_setting, character_analysis, narrative_technique
        )
        
        # 5. 对比基准库（如果有）
        benchmark_comparisons = {}
        if self.benchmark_db:
            benchmark_comparisons = self._compare_with_benchmark(
                story_core, core_setting, character_analysis
            )
        
        features = DeepNovelFeatures(
            novel_id=novel_id,
            story_core=story_core,
            core_setting=core_setting,
            character_analysis=character_analysis,
            narrative_technique=narrative_technique,
            commercial_value=commercial_value,
            overall_quality_score=round(overall_quality, 2),
            reusable_tags=reusable_tags,
            benchmark_comparisons=benchmark_comparisons,
            reverse_summary=reverse_summary,
            consistency_check=round(consistency_check, 2),
        )
        
        logger.info(
            "deep_fusion_completed",
            novel_id=novel_id,
            quality=overall_quality,
            consistency=consistency_check,
        )
        
        return features
    
    def _calculate_overall_quality(
        self,
        story_core: StoryCore,
        core_setting: CoreSetting,
        character_analysis: CharacterAnalysis,
        narrative_technique: NarrativeTechnique,
    ) -> float:
        """计算整体质量评分"""
        # 故事内核 (25%)
        story_score = (
            story_core.conflict_formula.reusability_score * 0.15 +
            story_core.uniqueness_score * 0.10
        )
        
        # 核心设定 (20%)
        setting_score = (
            core_setting.setting_coherence * 0.10 +
            core_setting.setting_novelty * 0.10
        )
        
        # 人物分析 (25%)
        character_score = (
            character_analysis.protagonist_arc.reader_satisfaction * 0.15 +
            character_analysis.character_memorability * 0.10
        )
        
        # 叙事技法 (20%)
        narrative_score = (
            narrative_technique.language_style.rhythm_score * 0.10 +
            (1 - narrative_technique.technique_difficulty / 5) * 0.10
        )
        
        # 商业价值 (10%，单独计算)
        # 这里简化处理
        
        total_score = story_score + setting_score + character_score + narrative_score
        return min(total_score, 1.0)
    
    def _generate_reusable_tags(
        self,
        story_core: StoryCore,
        core_setting: CoreSetting,
        character_analysis: CharacterAnalysis,
    ) -> List[str]:
        """生成可复用标签"""
        tags = []
        
        # 冲突公式标签
        tags.append(f"冲突公式:{story_core.conflict_formula.formula_name}")
        
        # 金手指标签
        gf = core_setting.golden_finger
        tags.append(f"金手指:{gf.gf_type.value}")
        tags.append(f"成长性:{gf.growth_type.value}")
        
        # 情绪节奏标签
        tags.append(f"情绪节奏:{story_core.hook_distribution.rhythm_pattern}")
        
        # 人物弧光标签
        tags.append(f"人物弧光:{character_analysis.protagonist_arc.arc_type.value}")
        
        # 创新点标签
        for innovation in gf.innovation_points:
            tags.append(f"创新:{innovation[:20]}")
        
        return tags
    
    def _generate_reverse_summary(
        self,
        story_core: StoryCore,
        core_setting: CoreSetting,
        character_analysis: CharacterAnalysis,
    ) -> str:
        """
        逆向生成梗概
        基于解析结果反向生成故事梗概，用于验证解析准确性
        """
        parts = []
        
        # 核心冲突
        cf = story_core.conflict_formula
        parts.append(
            f"这是一个关于『{cf.protagonist_desire}』的故事，"
            f"主角面临『{cf.core_obstacle}』的阻碍，"
            f"通过『{cf.solution_path}』实现目标。"
        )
        
        # 金手指
        gf = core_setting.golden_finger
        parts.append(
            f"主角拥有『{gf.gf_type.value}』金手指，"
            f"具有『{gf.growth_type.value}』特性，"
            f"初始能力为『{gf.initial_power}』。"
        )
        
        # 人物弧光
        arc = character_analysis.protagonist_arc
        parts.append(
            f"主角从『{arc.initial_state}』成长为『{arc.final_state}』，"
            f"完成『{arc.arc_type.value}』的人物弧光。"
        )
        
        # 情绪驱动
        top_hook = max(
            story_core.hook_distribution.type_distribution.items(),
            key=lambda x: x[1]
        )[0]
        parts.append(
            f"故事以『{top_hook.value}』为主要情绪驱动，"
            f"形成『{story_core.hook_distribution.rhythm_pattern}』的阅读体验。"
        )
        
        return "\n".join(parts)
    
    def _check_consistency(
        self,
        story_core: StoryCore,
        core_setting: CoreSetting,
        character_analysis: CharacterAnalysis,
        narrative_technique: NarrativeTechnique,
    ) -> float:
        """
        一致性检查
        检查各维度之间是否逻辑一致
        """
        consistency_scores = []
        
        # 1. 冲突公式与金手指适配性
        cf = story_core.conflict_formula
        gf = core_setting.golden_finger
        
        if cf.conflict_type.value in ["underdog_revenge", "revenge"]:
            # 逆袭/复仇类应该有成长型金手指
            if gf.growth_type.value in ["dynamic_linear", "dynamic_exp"]:
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.7)
        
        # 2. 人物弧光与冲突公式一致性
        arc = character_analysis.protagonist_arc
        if "逆袭" in cf.formula_name and arc.arc_type.value == "weak_to_strong":
            consistency_scores.append(1.0)
        elif "成长" in cf.formula_name and arc.arc_type.value == "coming_of_age":
            consistency_scores.append(1.0)
        else:
            consistency_scores.append(0.8)
        
        # 3. 叙事节奏与情绪钩子匹配
        if "快节奏" in narrative_technique.applicable_scenarios:
            if "每1-3章" in story_core.hook_distribution.rhythm_pattern:
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.8)
        
        # 4. 金手指约束与剧情复杂度
        if len(gf.constraints) >= 2:
            # 有约束的金手指应该有相应的剧情复杂度
            if narrative_technique.technique_difficulty >= 3:
                consistency_scores.append(1.0)
            else:
                consistency_scores.append(0.8)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.8
    
    def _compare_with_benchmark(
        self,
        story_core: StoryCore,
        core_setting: CoreSetting,
        character_analysis: CharacterAnalysis,
    ) -> Dict[str, Any]:
        """与基准库对比"""
        # 这里简化实现，实际应该查询数据库
        return {
            "differentiation_points": [],  # 差异化点
            "reusable_elements": [],        # 可复用元素
            "optimization_suggestions": [], # 优化建议
        }
    
    def generate_formula_summary(self, features: DeepNovelFeatures) -> str:
        """
        生成公式化总结
        用于快速理解和对比
        """
        return features.generate_formula_summary()
    
    def generate_creative_report(self, features: DeepNovelFeatures) -> Dict[str, Any]:
        """
        生成创意化解析报告
        面向创作者和IP开发者的详细报告
        """
        return {
            "core_formula": features.story_core.conflict_formula.to_formula_string(),
            "emotional_rhythm": features.story_core.hook_distribution.rhythm_pattern,
            "golden_finger_design": {
                "type": features.core_setting.golden_finger.gf_type.value,
                "growth": features.core_setting.golden_finger.growth_type.value,
                "constraints": [
                    c.constraint_type for c in features.core_setting.golden_finger.constraints
                ],
            },
            "character_arc": {
                "type": features.character_analysis.protagonist_arc.arc_type.value,
                "completion": features.character_analysis.protagonist_arc.completion_degree,
            },
            "commercial_highlights": {
                "target_audience": features.commercial_value.audience_profile.primary_segment.value,
                "best_adaptation": features.commercial_value.adaptation_potentials[0].adaptation_type.value if features.commercial_value.adaptation_potentials else None,
                "monetization_path": features.commercial_value.monetization_path,
            },
            "reusable_template": {
                "tags": features.reusable_tags,
                "applicable_genres": features.story_core.conflict_formula.applicable_genres,
            },
        }
