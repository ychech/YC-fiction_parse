"""
金手指/核心设定解析引擎
拆解"让小说差异化的核心设定"
"""
import re
from typing import Dict, List, Optional, Tuple

from src.common.deep_schemas import (
    CoreSetting,
    GoldenFingerConstraint,
    GoldenFingerDesign,
    GoldenFingerType,
    GrowthType,
    WorldRule,
    WorldRuleExploit,
)
from src.common.logger import get_logger

logger = get_logger(__name__)


class SettingExtractor:
    """设定解析器"""
    
    # 金手指类型关键词
    GF_TYPE_KEYWORDS = {
        GoldenFingerType.SYSTEM: [
            "系统", "叮", "面板", "任务", "奖励", "兑换", "积分", "等级提升",
            "系统提示", "系统商城"
        ],
        GoldenFingerType.SUPERNATURAL: [
            "异能", "超能力", "觉醒", "精神力", "念力", "元素", "火球", "冰箭",
            "雷电", "瞬移", "透视"
        ],
        GoldenFingerType.SPACE: [
            "空间", "小世界", "秘境", "洞天", "随身空间", "储物空间", "农场空间",
            "仙府", "洞府"
        ],
        GoldenFingerType.KNOWLEDGE: [
            "预知", "重生", "未来", "记忆", "知识", "信息差", "先知", "预测",
            "看穿", "洞察"
        ],
        GoldenFingerType.CONNECTIONS: [
            "人脉", "关系", "背景", "靠山", "师父", "贵人", "家族", "势力",
            "组织", "门派"
        ],
        GoldenFingerType.ITEM: [
            "法宝", "神器", "宝物", "戒指", "项链", "玉佩", "古籍", "传承",
            "丹药", "符箓"
        ],
        GoldenFingerType.REBIRTH: [
            "重生", "转世", "投胎", "回到", "再来一次", "前世", "上一世",
            "曾经"
        ],
        GoldenFingerType.TIME_TRAVEL: [
            "穿越", "异界", "异世界", "古代", "星际", "平行世界", "时空",
            "另一个世界"
        ],
    }
    
    # 约束条件关键词
    CONSTRAINT_KEYWORDS = {
        "代价": ["代价", "牺牲", "折寿", "消耗生命", "以命换", "付出"],
        "限制": ["限制", "冷却", "CD", "次数限制", "每日", "每月", "只能"],
        "副作用": ["副作用", "后遗症", "反噬", "失控", "暴走", "副作用"],
        "条件": ["条件", "必须", "才能", "只有", "要求", "前提"],
    }
    
    # 力量体系关键词
    POWER_SYSTEM_KEYWORDS = {
        "修仙": ["炼气", "筑基", "金丹", "元婴", "化神", "合体", "大乘", "渡劫"],
        "武侠": ["后天", "先天", "宗师", "大宗师", "绝世", "内力", "真气"],
        "魔法": ["魔法", "法师", "魔导", "元素", "咒语", "魔力", "法杖"],
        "斗气": ["斗气", "斗者", "斗师", "大斗师", "斗灵", "斗王", "斗皇"],
        "武魂": ["武魂", "魂环", "魂兽", "魂力", "魂师", "大魂师", "魂尊"],
    }
    
    def extract(self, text: str, chapters: List[Dict]) -> CoreSetting:
        """
        提取核心设定
        
        Args:
            text: 全文文本
            chapters: 章节列表
        
        Returns:
            CoreSetting: 核心设定
        """
        logger.info("setting_extraction_started")
        
        # 1. 提取金手指设计
        golden_finger = self._extract_golden_finger(text, chapters)
        
        # 2. 提取世界观规则
        world_rules = self._extract_world_rules(text)
        
        # 3. 提取规则漏洞利用
        rule_exploits = self._extract_rule_exploits(text, chapters)
        
        # 4. 计算整体评分
        setting_coherence = self._calculate_coherence(golden_finger, world_rules)
        setting_novelty = self._calculate_novelty(golden_finger)
        
        setting = CoreSetting(
            golden_finger=golden_finger,
            world_rules=world_rules,
            rule_exploits=rule_exploits,
            setting_coherence=round(setting_coherence, 2),
            setting_novelty=round(setting_novelty, 2),
        )
        
        logger.info(
            "setting_extraction_completed",
            gf_type=golden_finger.gf_type.value,
            gf_growth=golden_finger.growth_type.value,
            constraints=len(golden_finger.constraints),
            coherence=setting_coherence,
            novelty=setting_novelty,
        )
        
        return setting
    
    def _extract_golden_finger(self, text: str, chapters: List[Dict]) -> GoldenFingerDesign:
        """提取金手指设计"""
        # 1. 识别金手指类型
        gf_scores = {}
        for gf_type, keywords in self.GF_TYPE_KEYWORDS.items():
            score = sum(text.count(kw) for kw in keywords)
            gf_scores[gf_type] = score
        
        primary_gf = max(gf_scores.items(), key=lambda x: x[1])[0]
        
        # 2. 判断成长性
        growth_type = self._determine_growth_type(text, primary_gf)
        
        # 3. 提取约束条件
        constraints = self._extract_constraints(text)
        
        # 4. 分析适配性
        fit_score, pain_point = self._analyze_fit(text, primary_gf, chapters)
        
        # 5. 识别创新点
        innovation_points = self._identify_innovations(text, primary_gf, constraints)
        
        # 6. 计算与常见设定相似度
        similarity = self._calculate_similarity(primary_gf, growth_type, constraints)
        
        return GoldenFingerDesign(
            gf_type=primary_gf,
            gf_name=self._get_gf_name(text, primary_gf),
            growth_type=growth_type,
            initial_power=self._extract_initial_power(text, primary_gf),
            max_potential=self._extract_max_potential(text),
            constraints=constraints,
            protagonist_pain_point=pain_point,
            fit_score=round(fit_score, 2),
            innovation_points=innovation_points,
            similarity_to_common=round(similarity, 2),
        )
    
    def _determine_growth_type(self, text: str, gf_type: GoldenFingerType) -> GrowthType:
        """判断金手指成长性"""
        # 静态金手指关键词
        static_keywords = ["无限", "无尽", "永恒", "固定", "不变"]
        # 动态成长关键词
        growth_keywords = ["升级", "提升", "进化", "成长", "进阶", "突破"]
        # 指数成长关键词
        exp_keywords = ["翻倍", "倍增", "指数", "爆炸", "暴涨"]
        
        static_score = sum(text.count(kw) for kw in static_keywords)
        growth_score = sum(text.count(kw) for kw in growth_keywords)
        exp_score = sum(text.count(kw) for kw in exp_keywords)
        
        if exp_score > 5:
            return GrowthType.DYNAMIC_EXP
        elif growth_score > static_score:
            return GrowthType.DYNAMIC_LINEAR
        elif static_score > growth_score:
            return GrowthType.STATIC
        else:
            return GrowthType.DYNAMIC_STEP
    
    def _extract_constraints(self, text: str) -> List[GoldenFingerConstraint]:
        """提取约束条件"""
        constraints = []
        
        for constraint_type, keywords in self.CONSTRAINT_KEYWORDS.items():
            for keyword in keywords:
                # 查找包含关键词的句子
                pattern = f"[^。]*{keyword}[^。]*。"
                matches = re.findall(pattern, text)
                
                for match in matches[:3]:  # 限制数量
                    # 判断严重程度
                    severity = 3
                    if any(w in match for w in ["死", "命", "生命", "灵魂"]):
                        severity = 5
                    elif any(w in match for w in ["严重", "巨大", "重大"]):
                        severity = 4
                    
                    constraint = GoldenFingerConstraint(
                        constraint_type=constraint_type,
                        description=match.strip(),
                        severity=severity,
                        plot_impact=self._infer_plot_impact(constraint_type),
                    )
                    constraints.append(constraint)
        
        # 去重
        seen = set()
        unique_constraints = []
        for c in constraints:
            if c.description not in seen:
                seen.add(c.description)
                unique_constraints.append(c)
        
        return unique_constraints[:5]  # 最多5个
    
    def _infer_plot_impact(self, constraint_type: str) -> str:
        """推断对剧情的影响"""
        impacts = {
            "代价": "增加主角决策的沉重感，提升剧情张力",
            "限制": "创造剧情瓶颈，推动主角寻找突破方法",
            "副作用": "增加不确定性，制造危机时刻",
            "条件": "设置剧情触发门槛，控制节奏",
        }
        return impacts.get(constraint_type, "影响剧情发展")
    
    def _analyze_fit(
        self,
        text: str,
        gf_type: GoldenFingerType,
        chapters: List[Dict]
    ) -> Tuple[float, str]:
        """分析金手指与主角的适配性"""
        # 提取主角初期状态
        early_chapters = chapters[:5] if chapters else []
        early_text = " ".join(ch.get("content", "") for ch in early_chapters)
        
        # 识别痛点关键词
        pain_keywords = [
            "穷", "弱", "废物", "废柴", "被欺负", "被看不起", "没钱",
            "没背景", "没天赋", "困境", "绝境", "危机"
        ]
        
        pain_point = ""
        for kw in pain_keywords:
            if kw in early_text:
                pain_point = f"主角初期面临{kw}的困境"
                break
        
        if not pain_point:
            pain_point = "主角初期处于普通状态"
        
        # 计算适配度
        # 检查金手指是否解决痛点
        gf_solves_pain = False
        
        if gf_type == GoldenFingerType.SYSTEM and "弱" in early_text:
            gf_solves_pain = True
        elif gf_type == GoldenFingerType.KNOWLEDGE and "信息" in pain_point:
            gf_solves_pain = True
        elif gf_type == GoldenFingerType.ITEM and "穷" in early_text:
            gf_solves_pain = True
        
        fit_score = 0.8 if gf_solves_pain else 0.5
        
        return fit_score, pain_point
    
    def _identify_innovations(
        self,
        text: str,
        gf_type: GoldenFingerType,
        constraints: List[GoldenFingerConstraint]
    ) -> List[str]:
        """识别创新点"""
        innovations = []
        
        # 检查约束条件的创新性
        constraint_types = [c.constraint_type for c in constraints]
        if "情绪值" in text or "情绪" in str(constraint_types):
            innovations.append("使用'情绪值'作为系统兑换资源，而非传统积分")
        if "代价" in constraint_types and any(c.severity >= 4 for c in constraints):
            innovations.append("金手指使用需要付出沉重代价，增加剧情张力")
        
        # 检查金手指组合
        gf_types_found = []
        for gf_type_enum, keywords in self.GF_TYPE_KEYWORDS.items():
            if any(kw in text for kw in keywords[:3]):
                gf_types_found.append(gf_type_enum)
        
        if len(gf_types_found) > 1:
            innovations.append(f"多金手指组合：{', '.join(g.value for g in gf_types_found)}")
        
        return innovations
    
    def _calculate_similarity(
        self,
        gf_type: GoldenFingerType,
        growth_type: GrowthType,
        constraints: List[GoldenFingerConstraint]
    ) -> float:
        """计算与常见设定的相似度"""
        # 常见组合的基础相似度
        common_combinations = [
            (GoldenFingerType.SYSTEM, GrowthType.DYNAMIC_LINEAR),
            (GoldenFingerType.REBIRTH, GrowthType.STATIC),
            (GoldenFingerType.SUPERNATURAL, GrowthType.DYNAMIC_LINEAR),
        ]
        
        base_similarity = 0.7 if (gf_type, growth_type) in common_combinations else 0.5
        
        # 约束条件增加独特性
        if constraints:
            base_similarity -= 0.1 * len(constraints)
        
        return max(base_similarity, 0.1)
    
    def _get_gf_name(self, text: str, gf_type: GoldenFingerType) -> Optional[str]:
        """提取金手指名称"""
        # 尝试匹配"XX系统"、"XX空间"等模式
        patterns = {
            GoldenFingerType.SYSTEM: r"(\w+系统)",
            GoldenFingerType.SPACE: r"(\w+空间)",
            GoldenFingerType.ITEM: r"(\w+戒指|\w+项链|\w+玉佩)",
        }
        
        pattern = patterns.get(gf_type)
        if pattern:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        
        return None
    
    def _extract_initial_power(self, text: str, gf_type: GoldenFingerType) -> str:
        """提取初始能力"""
        # 简化处理，实际应该分析前几章
        initial_powers = {
            GoldenFingerType.SYSTEM: "基础功能开启，可接取初级任务",
            GoldenFingerType.SUPERNATURAL: "初级异能觉醒，能力微弱",
            GoldenFingerType.SPACE: "小型空间开启，可存储少量物品",
            GoldenFingerType.KNOWLEDGE: "获得部分未来信息或知识",
            GoldenFingerType.ITEM: "获得初级法宝或道具",
            GoldenFingerType.REBIRTH: "保留前世记忆",
            GoldenFingerType.TIME_TRAVEL: "穿越到异世界/过去",
            GoldenFingerType.CONNECTIONS: "获得某位贵人关注",
        }
        return initial_powers.get(gf_type, "未知初始能力")
    
    def _extract_max_potential(self, text: str) -> str:
        """提取最大潜力"""
        # 查找最高境界/最强状态描述
        peak_keywords = ["巅峰", "最强", "无敌", "至高", "终极", "圆满"]
        for kw in peak_keywords:
            if kw in text:
                return f"可达到{kw}境界"
        return "潜力巨大，上限未知"
    
    def _extract_world_rules(self, text: str) -> List[WorldRule]:
        """提取世界观规则"""
        rules = []
        
        # 力量体系规则
        for system_name, keywords in self.POWER_SYSTEM_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                rule = WorldRule(
                    rule_name=f"{system_name}体系",
                    rule_description=f"以{keywords[0]}、{keywords[1]}等为核心的等级体系",
                    rule_category="力量体系",
                    consistency_score=0.9,  # 简化
                )
                rules.append(rule)
        
        # 资源分配规则
        if "资源" in text or "分配" in text or "垄断" in text:
            rules.append(WorldRule(
                rule_name="资源分配规则",
                rule_description="资源被特定势力垄断，普通人获取困难",
                rule_category="资源分配",
                consistency_score=0.8,
            ))
        
        return rules
    
    def _extract_rule_exploits(self, text: str, chapters: List[Dict]) -> List[WorldRuleExploit]:
        """提取规则漏洞利用"""
        exploits = []
        
        # 查找"漏洞"、"bug"、"未被公开"等关键词
        exploit_keywords = ["漏洞", "bug", "未被公开", "不知道", "秘密", "独占", "先机"]
        
        for chapter in chapters:
            ch_text = chapter.get("content", "")
            ch_num = chapter.get("chapter_number", 0)
            
            for keyword in exploit_keywords:
                if keyword in ch_text:
                    # 提取相关句子
                    sentences = ch_text.split("。")
                    for sent in sentences:
                        if keyword in sent:
                            exploit = WorldRuleExploit(
                                exploit_description=sent.strip(),
                                exploited_by="主角",
                                exploit_benefit="获得先发优势或额外收益",
                                exploit_chapter=ch_num,
                            )
                            exploits.append(exploit)
                            break
        
        # 去重
        seen = set()
        unique_exploits = []
        for e in exploits:
            if e.exploit_description not in seen:
                seen.add(e.exploit_description)
                unique_exploits.append(e)
        
        return unique_exploits[:3]
    
    def _calculate_coherence(
        self,
        golden_finger: GoldenFingerDesign,
        world_rules: List[WorldRule]
    ) -> float:
        """计算设定自洽性"""
        base_score = 0.8
        
        # 有约束条件增加自洽性
        if golden_finger.constraints:
            base_score += 0.05 * len(golden_finger.constraints)
        
        # 有世界观规则增加自洽性
        if world_rules:
            base_score += 0.05 * len(world_rules)
        
        return min(base_score, 1.0)
    
    def _calculate_novelty(self, golden_finger: GoldenFingerDesign) -> float:
        """计算设定新颖度"""
        # 基于相似度反向计算
        return 1 - golden_finger.similarity_to_common
