"""
深度解析流水线
整合五大核心维度的解析
"""
from typing import Dict, List, Optional

from src.common.deep_schemas import DeepNovelFeatures
from src.common.logger import get_logger
from src.data_layer.benchmark_repository import BenchmarkRepository
from src.processing_layer.deep_extractors import (
    CharacterExtractor,
    CommercialExtractor,
    DeepFusionEngine,
    NarrativeExtractor,
    SettingExtractor,
    StoryCoreExtractor,
)

logger = get_logger(__name__)


class DeepProcessingPipeline:
    """
    深度解析处理流水线
    
    执行顺序：
    1. 故事内核解析（最核心）
    2. 金手指/核心设定解析
    3. 人物弧光与人设模板解析
    4. 叙事节奏与写作技法解析
    5. 商业价值解析（依赖前4个维度）
    6. 结果融合与基准对比
    """
    
    def __init__(self):
        self.story_extractor = StoryCoreExtractor()
        self.setting_extractor = SettingExtractor()
        self.character_extractor = CharacterExtractor()
        self.narrative_extractor = NarrativeExtractor()
        self.commercial_extractor = CommercialExtractor()
        self.fusion_engine = DeepFusionEngine()
        self.benchmark_repo = BenchmarkRepository()
    
    async def process(
        self,
        novel_id: str,
        text: str,
        chapters: List[Dict],
        compare_with_benchmark: bool = True,
    ) -> DeepNovelFeatures:
        """
        执行完整深度解析流程
        
        Args:
            novel_id: 小说ID
            text: 全文文本
            chapters: 章节列表
            compare_with_benchmark: 是否对比基准库
        
        Returns:
            DeepNovelFeatures: 深度解析结果
        """
        logger.info("deep_pipeline_started", novel_id=novel_id)
        
        # ========== 阶段1: 故事内核解析 ==========
        logger.info("stage_1_story_core")
        story_core = self.story_extractor.extract(text, chapters)
        
        # ========== 阶段2: 金手指/核心设定解析 ==========
        logger.info("stage_2_core_setting")
        core_setting = self.setting_extractor.extract(text, chapters)
        
        # ========== 阶段3: 人物弧光与人设模板解析 ==========
        logger.info("stage_3_character_analysis")
        character_analysis = self.character_extractor.extract(text, chapters)
        
        # ========== 阶段4: 叙事节奏与写作技法解析 ==========
        logger.info("stage_4_narrative_technique")
        narrative_technique = self.narrative_extractor.extract(text, chapters)
        
        # ========== 阶段5: 商业价值解析 ==========
        logger.info("stage_5_commercial_value")
        # 构建前4个维度的特征摘要
        story_features = {
            "conflict_type": story_core.conflict_formula.conflict_type.value,
            "rhythm_pattern": story_core.hook_distribution.rhythm_pattern,
        }
        setting_features = {
            "gf_type": core_setting.golden_finger.gf_type.value,
            "world_type": core_setting.world_rules[0].rule_name if core_setting.world_rules else None,
        }
        
        commercial_value = self.commercial_extractor.extract(
            text, chapters, story_features, setting_features
        )
        
        # ========== 阶段6: 结果融合 ==========
        logger.info("stage_6_fusion")
        features = self.fusion_engine.fuse(
            novel_id=novel_id,
            story_core=story_core,
            core_setting=core_setting,
            character_analysis=character_analysis,
            narrative_technique=narrative_technique,
            commercial_value=commercial_value,
        )
        
        # ========== 阶段7: 基准对比（可选）==========
        if compare_with_benchmark:
            logger.info("stage_7_benchmark_comparison")
            comparisons = await self.benchmark_repo.compare_with_benchmarks(
                features=features,
                genre=story_core.conflict_formula.applicable_genres[0] if story_core.conflict_formula.applicable_genres else None,
            )
            features.benchmark_comparisons = comparisons
        
        logger.info(
            "deep_pipeline_completed",
            novel_id=novel_id,
            quality=features.overall_quality_score,
            consistency=features.consistency_check,
        )
        
        return features
    
    def generate_formula_summary(self, features: DeepNovelFeatures) -> str:
        """
        生成公式化总结
        
        示例输出：
        「底层逆袭公式」+「系统金手指(动态+情绪值约束)」+「爽点节奏(3小1大)」+「学生受众(付费点:打脸爽点)」
        """
        return self.fusion_engine.generate_formula_summary(features)
    
    def generate_creative_report(self, features: DeepNovelFeatures) -> Dict:
        """
        生成创意化解析报告
        
        面向创作者和IP开发者的详细报告
        """
        return self.fusion_engine.generate_creative_report(features)
    
    def generate_comparison_report(
        self,
        features: DeepNovelFeatures,
    ) -> str:
        """
        生成对比分析报告
        
        包含：
        - 与标杆作品的对比
        - 差异化优势
        - 可复用元素
        - 优化建议
        """
        if not features.benchmark_comparisons:
            return "暂无基准对比数据"
        
        report_lines = [
            "=" * 60,
            "对比分析报告",
            "=" * 60,
            "",
            "【差异化优势】",
        ]
        
        for diff in features.benchmark_comparisons.get("differentiation_points", []):
            report_lines.append(f"• [{diff['dimension']}] {diff['point']}")
            report_lines.append(f"  独特性评分: {diff['uniqueness_score']}")
            report_lines.append("")
        
        report_lines.extend([
            "【可复用元素】",
        ])
        
        for reuse in features.benchmark_comparisons.get("reusable_elements", []):
            report_lines.append(f"• [{reuse['element']}] 来源:《{reuse['source']}》")
            report_lines.append(f"  {reuse['description']}")
            report_lines.append(f"  可复用性: {reuse['reusability_score']}")
            report_lines.append("")
        
        report_lines.extend([
            "【优化建议】",
        ])
        
        for suggestion in features.benchmark_comparisons.get("optimization_suggestions", []):
            priority_icon = "🔴" if suggestion['priority'] == 'high' else "🟡"
            report_lines.append(f"{priority_icon} [{suggestion['category']}] {suggestion['suggestion']}")
            report_lines.append(f"   参考: {suggestion['reference']}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 60,
        ])
        
        return "\n".join(report_lines)
