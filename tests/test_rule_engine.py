"""
规则引擎单元测试
"""
import pytest

from src.common.schemas import Rule
from src.processing_layer.extractors.rule_engine import RuleEngine


class TestRuleEngine:
    """规则引擎测试"""
    
    @pytest.fixture
    def engine(self):
        return RuleEngine()
    
    @pytest.fixture
    def xianxia_text(self):
        """仙侠小说示例文本"""
        return """
        这是一个修仙的世界。
        
        主角修炼灵根，从炼气期开始修炼。
        经过筑基、金丹、元婴，最终渡劫飞升。
        
        他加入了一个大宗门，学习各种法宝的使用。
        
        修真之路漫漫，需要不断突破境界。
        """
    
    @pytest.fixture
    def system_text(self):
        """系统流小说示例文本"""
        return """
        叮！系统绑定成功！
        
        【系统面板】
        宿主：张三
        等级：1级
        
        叮！任务完成！
        奖励发放中...
        
        系统提示：请继续完成下一个任务。
        """
    
    def test_load_builtin_rules(self, engine):
        """测试内置规则加载"""
        assert len(engine.rules) > 0
        
        # 检查是否有仙侠规则
        xianxia_rules = [r for r in engine.rules if "仙侠" in r.name]
        assert len(xianxia_rules) > 0
    
    def test_add_custom_rule(self, engine):
        """测试添加自定义规则"""
        rule = Rule(
            id="test_rule",
            name="测试规则",
            target_field="custom.field",
            rule_type="keyword",
            condition={"keywords": ["测试"]},
            weight=1.0
        )
        
        engine.add_rule(rule)
        
        assert rule in engine.rules
    
    def test_evaluate_keyword_rule(self, engine, xianxia_text):
        """测试关键词规则评估"""
        rule = Rule(
            id="test_keyword",
            name="关键词测试",
            target_field="test.field",
            rule_type="keyword",
            condition={"keywords": ["修仙", "修真", "灵根"]},
            weight=1.0
        )
        
        score = engine._evaluate_rule(xianxia_text, rule)
        
        assert score > 0
        assert score <= 1.0
    
    def test_evaluate_regex_rule(self, engine):
        """测试正则规则评估"""
        text = "我是一个人。他在修炼。"
        
        rule = Rule(
            id="test_regex",
            name="正则测试",
            target_field="test.field",
            rule_type="regex",
            condition={"pattern": r"^我[\s\p{P}]"},
            weight=1.0
        )
        
        # 编译正则
        import re
        rule.condition["_compiled"] = re.compile(rule.condition["pattern"])
        
        score = engine._evaluate_rule(text, rule)
        
        assert score > 0
    
    def test_extract_xianxia_features(self, engine, xianxia_text):
        """测试仙侠特征提取"""
        features = engine.extract_features(xianxia_text)
        
        assert features.background.world_type == "仙侠"
        assert features.background.power_system == "修仙境界"
        assert features.confidence_score > 0
    
    def test_extract_system_features(self, engine, system_text):
        """测试系统流特征提取"""
        features = engine.extract_features(system_text)
        
        assert features.task.task_structure == "系统流"
        assert features.confidence_score > 0
    
    def test_merge_lists(self, engine):
        """测试列表合并"""
        list1 = ["a", "b", "c"]
        list2 = ["b", "c", "d"]
        
        merged = engine._merge_lists(list1, list2)
        
        assert "a" in merged
        assert "b" in merged
        assert "c" in merged
        assert "d" in merged
        assert len(merged) == 4  # 去重
    
    def test_select_best(self, engine):
        """测试最佳值选择"""
        # 只有 rule 有值
        result = engine._select_best("rule_value", None, ai_weight=0.6)
        assert result == "rule_value"
        
        # 只有 AI 有值
        result = engine._select_best(None, "ai_value", ai_weight=0.6)
        assert result == "ai_value"
        
        # 都有值，AI 权重高
        result = engine._select_best("rule_value", "ai_value", ai_weight=0.7)
        assert result == "ai_value"
        
        # 都有值，Rule 权重高
        result = engine._select_best("rule_value", "ai_value", ai_weight=0.3)
        assert result == "rule_value"
        
        # 值相同
        result = engine._select_best("same", "same", ai_weight=0.5)
        assert result == "same"
    
    def test_calculate_completeness(self, engine, xianxia_text):
        """测试完整性计算"""
        features = engine.extract_features(xianxia_text)
        
        completeness = engine._calculate_completeness(features)
        
        assert 0 <= completeness <= 1
    
    def test_get_rule_stats(self, engine):
        """测试规则统计"""
        stats = engine.get_rule_stats()
        
        assert "total_rules" in stats
        assert "enabled_rules" in stats
        assert stats["total_rules"] > 0
