"""
规则引擎 - 基于规则的文本特征提取
"""
import json
import re
from typing import Any, Dict, List, Optional

from src.common.logger import get_logger
from src.common.schemas import (
    BackgroundFeatures,
    CharacterFeatures,
    NovelFeatures,
    PlotFeatures,
    Rule,
    TaskFeatures,
    WritingFeatures,
)
from src.config.settings import settings

logger = get_logger(__name__)


class RuleEngine:
    """规则引擎"""
    
    def __init__(self):
        self.rules: List[Rule] = []
        self._compile_rules()
    
    def _compile_rules(self):
        """编译内置规则"""
        self.rules = self._load_builtin_rules()
        for rule in self.rules:
            if rule.rule_type == "regex":
                pattern = rule.condition.get("pattern", "")
                rule.condition["_compiled"] = re.compile(pattern, re.IGNORECASE)
    
    def _load_builtin_rules(self) -> List[Rule]:
        """加载内置规则"""
        builtin_rules = [
            # ========== 任务特征规则 ==========
            Rule(
                id="rule_task_system",
                name="系统流识别",
                target_field="task.task_structure",
                rule_type="keyword",
                condition={"keywords": ["系统面板", "系统提示", "叮！", "任务完成", "奖励发放"]},
                weight=0.9
            ),
            Rule(
                id="rule_task_signin",
                name="签到流识别",
                target_field="task.task_structure",
                rule_type="keyword",
                condition={"keywords": ["签到", "打卡", "连续签到", "签到奖励"]},
                weight=0.8
            ),
            Rule(
                id="rule_task_levelup",
                name="升级流识别",
                target_field="task.task_structure",
                rule_type="keyword",
                condition={"keywords": ["突破", "升级", "境界提升", "等级提升", "经验值"]},
                weight=0.7
            ),
            
            # ========== 背景特征规则 ==========
            Rule(
                id="rule_bg_xianxia",
                name="仙侠背景识别",
                target_field="background.world_type",
                rule_type="keyword",
                condition={"keywords": ["修真", "修仙", "灵根", "筑基", "金丹", "元婴", "渡劫", "飞升", "宗门", "法宝"]},
                weight=0.9
            ),
            Rule(
                id="rule_bg_fantasy",
                name="玄幻背景识别",
                target_field="background.world_type",
                rule_type="keyword",
                condition={"keywords": ["斗气", "魔法", "武魂", "魂环", "魂兽", "异火", "秘境", "遗迹"]},
                weight=0.9
            ),
            Rule(
                id="rule_bg_urban",
                name="都市背景识别",
                target_field="background.world_type",
                rule_type="keyword",
                condition={"keywords": ["都市", "现代", "公司", "学校", "医院", "警察", "总裁", "校花"]},
                weight=0.8
            ),
            Rule(
                id="rule_bg_history",
                name="历史背景识别",
                target_field="background.world_type",
                rule_type="keyword",
                condition={"keywords": ["大明", "大唐", "大宋", "清朝", "秦朝", "汉朝", "皇帝", "宰相", "科举"]},
                weight=0.8
            ),
            Rule(
                id="rule_bg_scifi",
                name="科幻背景识别",
                target_field="background.world_type",
                rule_type="keyword",
                condition={"keywords": ["星际", "宇宙", "飞船", "机甲", "基因", "虫族", "未来", "AI", "人工智能"]},
                weight=0.9
            ),
            
            # ========== 力量体系规则 ==========
            Rule(
                id="rule_power_cultivation",
                name="修仙境界识别",
                target_field="background.power_system",
                rule_type="keyword",
                condition={"keywords": ["炼气", "筑基", "金丹", "元婴", "化神", "合体", "大乘", "渡劫"]},
                weight=0.95
            ),
            Rule(
                id="rule_power_martial",
                name="武侠境界识别",
                target_field="background.power_system",
                rule_type="keyword",
                condition={"keywords": ["后天", "先天", "宗师", "大宗师", "绝世", "内力", "真气", "经脉"]},
                weight=0.9
            ),
            Rule(
                id="rule_power_magic",
                name="魔法体系识别",
                target_field="background.power_system",
                rule_type="keyword",
                condition={"keywords": ["魔法", "法师", "魔导", "元素", "火球术", "冰箭", "咒语"]},
                weight=0.85
            ),
            
            # ========== 写作手法规则 ==========
            Rule(
                id="rule_write_firstperson",
                name="第一人称识别",
                target_field="writing.narrative_perspective",
                rule_type="regex",
                condition={"pattern": r"^(我|俺|咱)[\s\p{P}]"},
                weight=0.8
            ),
            Rule(
                id="rule_write_thirdperson",
                name="第三人称识别",
                target_field="writing.narrative_perspective",
                rule_type="regex",
                condition={"pattern": r"^(他|她|它|主角|男主|女主)[\s\p{P}]"},
                weight=0.7
            ),
            Rule(
                id="rule_write_fast",
                name="快节奏识别",
                target_field="writing.pacing",
                rule_type="keyword",
                condition={"keywords": ["瞬间", "立刻", "马上", "直接", "毫不犹豫"]},
                weight=0.6
            ),
            Rule(
                id="rule_write_humor",
                name="幽默风格识别",
                target_field="writing.humor_style",
                rule_type="keyword",
                condition={"keywords": ["吐槽", "搞笑", "逗比", "沙雕", "无厘头", "哈哈哈"]},
                weight=0.7
            ),
            
            # ========== 情节结构规则 ==========
            Rule(
                id="rule_plot_revenge",
                name="复仇情节识别",
                target_field="plot.conflict_types",
                rule_type="keyword",
                condition={"keywords": ["复仇", "报仇", "血债", "灭门", "背叛", "陷害", "屈辱"]},
                weight=0.8
            ),
            Rule(
                id="rule_plot_romance",
                name="恋爱情节识别",
                target_field="plot.conflict_types",
                rule_type="keyword",
                condition={"keywords": ["喜欢", "爱", "心动", "表白", "约会", "吃醋", "分手", "复合"]},
                weight=0.7
            ),
            Rule(
                id="rule_plot_competition",
                name="竞争情节识别",
                target_field="plot.conflict_types",
                rule_type="keyword",
                condition={"keywords": ["比赛", "竞争", "对决", "挑战", "排名", "冠军", "第一"]},
                weight=0.7
            ),
        ]
        return builtin_rules
    
    def add_rule(self, rule: Rule):
        """添加自定义规则"""
        if rule.rule_type == "regex":
            pattern = rule.condition.get("pattern", "")
            rule.condition["_compiled"] = re.compile(pattern, re.IGNORECASE)
        self.rules.append(rule)
    
    def extract_features(
        self,
        text: str,
        chapters: Optional[List[Dict]] = None
    ) -> NovelFeatures:
        """
        基于规则提取特征
        
        Args:
            text: 小说全文或核心章节文本
            chapters: 章节列表（可选）
        
        Returns:
            NovelFeatures: 提取的特征
        """
        logger.info("rule_extraction_started", text_length=len(text))
        
        features = NovelFeatures(novel_id="")
        
        # 按目标字段分组执行规则
        field_rules: Dict[str, List[Rule]] = {}
        for rule in self.rules:
            if not rule.enabled:
                continue
            if rule.target_field not in field_rules:
                field_rules[rule.target_field] = []
            field_rules[rule.target_field].append(rule)
        
        # 执行每个字段的规则
        for field_path, rules in field_rules.items():
            result = self._apply_rules(text, rules)
            self._set_nested_field(features, field_path, result)
        
        # 统计置信度
        features.confidence_score = self._calculate_confidence(features)
        features.extraction_method = "rule_engine"
        
        logger.info("rule_extraction_completed", confidence=features.confidence_score)
        
        return features
    
    def _apply_rules(self, text: str, rules: List[Rule]) -> Any:
        """应用规则组"""
        scores: Dict[str, float] = {}
        
        for rule in rules:
            score = self._evaluate_rule(text, rule)
            if score > 0:
                # 提取目标值
                target_value = rule.condition.get("value")
                if target_value is None:
                    # 从规则名或条件推断
                    if "keywords" in rule.condition:
                        # 对于关键词规则，返回匹配的关键词
                        target_value = self._extract_matching_keyword(text, rule)
                    else:
                        target_value = rule.name
                
                if target_value:
                    scores[target_value] = scores.get(target_value, 0) + score * rule.weight
        
        if not scores:
            return None
        
        # 返回得分最高的值
        best_match = max(scores.items(), key=lambda x: x[1])
        return best_match[0]
    
    def _evaluate_rule(self, text: str, rule: Rule) -> float:
        """评估单个规则"""
        if rule.rule_type == "keyword":
            keywords = rule.condition.get("keywords", [])
            matches = sum(1 for kw in keywords if kw in text)
            return matches / len(keywords) if keywords else 0
        
        elif rule.rule_type == "regex":
            compiled = rule.condition.get("_compiled")
            if compiled:
                matches = len(compiled.findall(text))
                return min(matches / 10, 1.0)  # 归一化
            return 0
        
        elif rule.rule_type == "ml":
            # 机器学习规则，需要外部模型
            model_name = rule.condition.get("model")
            # 这里简化处理，实际应该调用模型
            return 0
        
        return 0
    
    def _extract_matching_keyword(self, text: str, rule: Rule) -> Optional[str]:
        """提取匹配的关键词"""
        keywords = rule.condition.get("keywords", [])
        for kw in keywords:
            if kw in text:
                return kw
        return None
    
    def _set_nested_field(self, obj: Any, field_path: str, value: Any):
        """设置嵌套字段"""
        parts = field_path.split(".")
        current = obj
        
        for part in parts[:-1]:
            current = getattr(current, part)
        
        setattr(current, parts[-1], value)
    
    def _calculate_confidence(self, features: NovelFeatures) -> float:
        """计算整体置信度"""
        scores = []
        
        # 检查各字段是否有值
        if features.task.main_task or features.task.task_structure:
            scores.append(0.8)
        if features.background.world_type:
            scores.append(0.9)
        if features.background.power_system:
            scores.append(0.85)
        if features.writing.narrative_perspective:
            scores.append(0.7)
        if features.plot.conflict_types:
            scores.append(0.75)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_rule_stats(self) -> Dict[str, Any]:
        """获取规则统计"""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "rule_types": {},
            "target_fields": list(set(r.target_field for r in self.rules)),
        }
