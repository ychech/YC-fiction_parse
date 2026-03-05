"""
故事内核解析引擎
挖掘小说"不变的核心逻辑"
"""
import re
from typing import Dict, List, Tuple

from src.common.deep_schemas import (
    ConflictType,
    CoreConflictFormula,
    EmotionalHook,
    EmotionalHookDistribution,
    HookType,
    StoryCore,
    ValueProposition,
)
from src.common.logger import get_logger

logger = get_logger(__name__)


class StoryCoreExtractor:
    """故事内核解析器"""
    
    # 冲突类型关键词映射
    CONFLICT_KEYWORDS = {
        ConflictType.UNDERDOG_REVENGE: [
            "底层", "逆袭", "翻身", "崛起", "草根", "平民", "寒门", "废物", "废柴",
            "被看不起", "被嘲笑", "被欺压", "讨回", "证明"
        ],
        ConflictType.REVENGE: [
            "复仇", "报仇", "血债", "灭门", "背叛", "陷害", "屈辱", "恨", "怨",
            "讨还", "清算", "以牙还牙"
        ],
        ConflictType.SURVIVAL: [
            "生存", "活下去", "危机", "绝境", "生死", "危机", "逃命", "挣扎",
            "末日", "灾难", "危险"
        ],
        ConflictType.IDENTITY: [
            "身份", "我是谁", "归属", "认同", "找回", "迷失", "寻找", "真相",
            "身世", "秘密"
        ],
        ConflictType.LOVE: [
            "爱", "喜欢", "心动", "表白", "在一起", "守护", "追求", "缘分",
            "命中注定", "相思"
        ],
        ConflictType.POWER_STRUGGLE: [
            "权力", "斗争", "争夺", "竞争", "上位", "掌控", "统治", "领导",
            "势力", "派系"
        ],
        ConflictType.MORAL_DILEMMA: [
            "选择", "牺牲", "取舍", "两难", "道德", "正义", "邪恶", "善恶",
            "良心", "底线"
        ],
        ConflictType.COMING_OF_AGE: [
            "成长", "成熟", "蜕变", "经历", "历练", "磨练", "懂事", "担当",
            "责任"
        ],
    }
    
    # 情绪钩子关键词
    HOOK_KEYWORDS = {
        HookType.FACE_SLAP: [
            "嘲讽", "轻视", "不屑", "冷笑", "打脸", "震惊", "目瞪口呆",
            "不可置信", "颜面扫地", "无地自容", "后悔", "求饶"
        ],
        HookType.COMEBACK: [
            "绝境", "绝境反击", "翻盘", "逆转", "反杀", "逆袭", "起死回生",
            "绝处逢生", "力挽狂澜", "扭转乾坤"
        ],
        HookType.REVELATION: [
            "真相", "揭秘", "原来", "竟是", "没想到", "竟然", "身份曝光",
            "身世", "秘密揭开", "真相大白"
        ],
        HookType.ROMANCE: [
            "心动", "喜欢", "表白", "约会", "吃醋", "误会", "和好", "甜蜜",
            "浪漫", "告白", "在一起"
        ],
        HookType.CLIMAX: [
            "高潮", "决战", "最终战", "巅峰", "最强", "无敌", "碾压", "横扫",
            "一统", "登顶"
        ],
        HookType.SUSPENSE: [
            "悬念", "谜团", "未知", "即将", "将要", "危机", "阴谋", "陷阱",
            "幕后", "真相"
        ],
        HookType.TRAGEDY: [
            "死", "牺牲", "离别", "永别", "泪", "痛", "伤", "虐", "心碎",
            "绝望", "无能为力"
        ],
        HookType.HUMOR: [
            "笑", "哈哈", "搞笑", "逗", "吐槽", "幽默", "有趣", "好玩",
            "无厘头", "沙雕"
        ],
    }
    
    # 价值主张关键词
    VALUE_KEYWORDS = {
        "奋斗": ["努力", "奋斗", "拼搏", "坚持", "不放弃", "汗水", "付出", "收获"],
        "真诚": ["真诚", "真心", "诚实", "信任", "坦诚", "实在", "不虚伪"],
        "丛林法则": ["弱肉强食", "适者生存", "强者为尊", "实力至上", "拳头", "力量"],
        "因果报应": ["报应", "因果", "善恶有报", "天道", "轮回", "公道"],
        "自我实现": ["梦想", "追求", "理想", "目标", "实现", "价值", "意义"],
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则模式"""
        self.hook_patterns = {}
        for hook_type, keywords in self.HOOK_KEYWORDS.items():
            pattern = "|".join(keywords)
            self.hook_patterns[hook_type] = re.compile(pattern)
    
    def extract(self, text: str, chapters: List[Dict]) -> StoryCore:
        """
        提取故事内核
        
        Args:
            text: 全文文本
            chapters: 章节列表
        
        Returns:
            StoryCore: 故事内核
        """
        logger.info("story_core_extraction_started")
        
        # 1. 提取核心冲突公式
        conflict_formula = self._extract_conflict_formula(text, chapters)
        
        # 2. 提取情绪钩子分布
        hook_distribution = self._extract_hook_distribution(text, chapters)
        
        # 3. 提取价值主张
        value_proposition = self._extract_value_proposition(text)
        
        # 4. 生成核心吸引力总结
        core_attraction = self._generate_core_attraction(
            conflict_formula, hook_distribution, value_proposition
        )
        
        # 5. 计算独特性评分
        uniqueness_score = self._calculate_uniqueness(conflict_formula, hook_distribution)
        
        story_core = StoryCore(
            conflict_formula=conflict_formula,
            hook_distribution=hook_distribution,
            value_proposition=value_proposition,
            core_attraction=core_attraction,
            uniqueness_score=uniqueness_score,
        )
        
        logger.info(
            "story_core_extraction_completed",
            conflict_type=conflict_formula.conflict_type.value,
            hooks_count=hook_distribution.total_hooks,
            uniqueness=uniqueness_score,
        )
        
        return story_core
    
    def _extract_conflict_formula(self, text: str, chapters: List[Dict]) -> CoreConflictFormula:
        """提取核心冲突公式"""
        # 1. 识别冲突类型
        conflict_scores = {}
        for conflict_type, keywords in self.CONFLICT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            conflict_scores[conflict_type] = score
        
        primary_conflict = max(conflict_scores.items(), key=lambda x: x[1])[0]
        
        # 2. 根据冲突类型生成公式
        formula_templates = {
            ConflictType.UNDERDOG_REVENGE: {
                "name": "底层逆袭公式",
                "desire": "摆脱底层身份，获得尊重和地位",
                "obstacle": "资源匮乏、权力压制、阶层固化",
                "path": "金手指/认知差/贵人相助",
                "applicable": ["都市", "修仙", "玄幻"],
            },
            ConflictType.REVENGE: {
                "name": "复仇公式",
                "desire": "讨还不公，让仇人付出代价",
                "obstacle": "仇人实力强大、信息不对等",
                "path": "隐忍积累、借力打力、以弱胜强",
                "applicable": ["武侠", "都市", "历史"],
            },
            ConflictType.SURVIVAL: {
                "name": "生存公式",
                "desire": "在极端环境中活下去",
                "obstacle": "资源匮乏、环境恶劣、敌人环伺",
                "path": "智慧、勇气、结盟、进化",
                "applicable": ["末日", "荒野", "无限流"],
            },
            ConflictType.COMING_OF_AGE: {
                "name": "成长公式",
                "desire": "从幼稚到成熟，找到人生方向",
                "obstacle": "认知局限、外界诱惑、内心迷茫",
                "path": "经历挫折、获得 mentorship、自我反思",
                "applicable": ["青春", "职场", "修仙"],
            },
        }
        
        template = formula_templates.get(primary_conflict, {
            "name": "通用冲突公式",
            "desire": "实现核心目标",
            "obstacle": "面临主要阻碍",
            "path": "采取解决行动",
            "applicable": ["通用"],
        })
        
        # 计算可复用性评分（基于该冲突类型的流行度）
        total_score = sum(conflict_scores.values())
        reusability = conflict_scores[primary_conflict] / total_score if total_score > 0 else 0.5
        
        return CoreConflictFormula(
            conflict_type=primary_conflict,
            formula_name=template["name"],
            protagonist_desire=template["desire"],
            core_obstacle=template["obstacle"],
            solution_path=template["path"],
            reusability_score=round(reusability, 2),
            applicable_genres=template["applicable"],
        )
    
    def _extract_hook_distribution(self, text: str, chapters: List[Dict]) -> EmotionalHookDistribution:
        """提取情绪钩子分布"""
        hooks = []
        type_distribution = {hook_type: 0 for hook_type in HookType}
        intensity_curve = []
        
        for chapter in chapters:
            ch_num = chapter.get("chapter_number", 0)
            ch_text = chapter.get("content", "")
            
            # 分析每个钩子类型
            for hook_type, pattern in self.hook_patterns.items():
                matches = pattern.findall(ch_text)
                
                for match in matches:
                    # 确定位置
                    match_pos = ch_text.find(match)
                    if match_pos < len(ch_text) * 0.2:
                        position = "开头"
                    elif match_pos > len(ch_text) * 0.8:
                        position = "结尾"
                    else:
                        position = "中间"
                    
                    # 计算强度（基于关键词密度和上下文）
                    intensity = min(len(matches), 5)
                    
                    hook = EmotionalHook(
                        hook_type=hook_type,
                        chapter_number=ch_num,
                        position_in_chapter=position,
                        intensity=intensity,
                        trigger_keywords=[match] if isinstance(match, str) else [],
                        emotional_response=self._get_emotional_response(hook_type),
                    )
                    hooks.append(hook)
                    type_distribution[hook_type] += 1
            
            # 记录章节强度
            chapter_intensity = sum(
                1 for h in hooks if h.chapter_number == ch_num
            )
            intensity_curve.append((ch_num, min(chapter_intensity, 5)))
        
        # 分析节奏模式
        rhythm_pattern = self._analyze_rhythm_pattern(hooks)
        
        # 找出高潮章节
        peak_chapters = [
            ch_num for ch_num, intensity in intensity_curve
            if intensity >= 4
        ]
        
        return EmotionalHookDistribution(
            total_hooks=len(hooks),
            type_distribution=type_distribution,
            rhythm_pattern=rhythm_pattern,
            intensity_curve=intensity_curve,
            peak_chapters=peak_chapters,
        )
    
    def _get_emotional_response(self, hook_type: HookType) -> str:
        """获取预期情绪反应"""
        responses = {
            HookType.FACE_SLAP: "爽快感、满足感",
            HookType.COMEBACK: "激动、振奋",
            HookType.REVELATION: "惊讶、恍然大悟",
            HookType.ROMANCE: "心动、甜蜜",
            HookType.CLIMAX: "兴奋、满足",
            HookType.SUSPENSE: "紧张、好奇",
            HookType.TRAGEDY: "悲伤、共鸣",
            HookType.HUMOR: "轻松、愉悦",
        }
        return responses.get(hook_type, "情绪共鸣")
    
    def _analyze_rhythm_pattern(self, hooks: List[EmotionalHook]) -> str:
        """分析节奏模式"""
        if not hooks:
            return "无明显节奏"
        
        # 按章节分组统计
        chapter_hooks: Dict[int, List[EmotionalHook]] = {}
        for hook in hooks:
            if hook.chapter_number not in chapter_hooks:
                chapter_hooks[hook.chapter_number] = []
            chapter_hooks[hook.chapter_number].append(hook)
        
        # 计算平均间隔
        chapters_with_hooks = sorted(chapter_hooks.keys())
        if len(chapters_with_hooks) < 2:
            return "钩子分布稀疏"
        
        intervals = [
            chapters_with_hooks[i+1] - chapters_with_hooks[i]
            for i in range(len(chapters_with_hooks)-1)
        ]
        avg_interval = sum(intervals) / len(intervals)
        
        # 识别大爽点（高强度钩子）
        major_hooks = [h for h in hooks if h.intensity >= 4]
        major_intervals = []
        if len(major_hooks) >= 2:
            major_chapters = sorted(set(h.chapter_number for h in major_hooks))
            major_intervals = [
                major_chapters[i+1] - major_chapters[i]
                for i in range(len(major_chapters)-1)
            ]
        
        # 生成模式描述
        if avg_interval <= 3:
            small_pattern = "每1-3章1个小爽点"
        elif avg_interval <= 5:
            small_pattern = "每3-5章1个小爽点"
        else:
            small_pattern = "每5章以上1个小爽点"
        
        if major_intervals:
            avg_major = sum(major_intervals) / len(major_intervals)
            if avg_major <= 10:
                large_pattern = "每10章1个大爽点"
            elif avg_major <= 20:
                large_pattern = "每10-20章1个大爽点"
            else:
                large_pattern = "每20章以上1个大爽点"
        else:
            large_pattern = "无明显大爽点节奏"
        
        return f"{small_pattern}，{large_pattern}"
    
    def _extract_value_proposition(self, text: str) -> ValueProposition:
        """提取价值主张"""
        value_scores = {}
        for value_type, keywords in self.VALUE_KEYWORDS.items():
            score = sum(text.count(kw) for kw in keywords)
            value_scores[value_type] = score
        
        # 找出主要价值
        primary_value = max(value_scores.items(), key=lambda x: x[1])
        
        # 计算可代入性（基于关键词密度和情感词）
        relatability = min(primary_value[1] / 100, 1.0)
        
        # 找出价值表达时刻（包含关键词的章节）
        expression_moments = []
        # 简化处理，实际应该按章节分析
        
        return ValueProposition(
            core_value=f"{primary_value[0]}的价值",
            value_type=primary_value[0],
            relatability_score=round(relatability, 2),
            expression_moments=expression_moments,
        )
    
    def _generate_core_attraction(
        self,
        conflict_formula: CoreConflictFormula,
        hook_distribution: EmotionalHookDistribution,
        value_proposition: ValueProposition,
    ) -> str:
        """生成核心吸引力总结"""
        # 找出最主要的钩子类型
        top_hook_type = max(
            hook_distribution.type_distribution.items(),
            key=lambda x: x[1]
        )[0]
        
        attraction = (
            f"以『{conflict_formula.formula_name}』为核心冲突，"
            f"通过『{top_hook_type.value}』类情绪钩子驱动剧情，"
            f"传递『{value_proposition.value_type}』的价值主张，"
            f"形成{hook_distribution.rhythm_pattern}的阅读节奏。"
        )
        
        return attraction
    
    def _calculate_uniqueness(
        self,
        conflict_formula: CoreConflictFormula,
        hook_distribution: EmotionalHookDistribution,
    ) -> float:
        """计算独特性评分"""
        # 基于冲突类型的常见度扣分
        common_conflicts = [ConflictType.UNDERDOG_REVENGE, ConflictType.REVENGE]
        base_score = 0.7 if conflict_formula.conflict_type in common_conflicts else 0.85
        
        # 基于钩子多样性加分
        hook_types_used = sum(1 for count in hook_distribution.type_distribution.values() if count > 0)
        diversity_bonus = (hook_types_used / len(HookType)) * 0.2
        
        # 基于节奏复杂度加分
        rhythm_complexity = 0.1 if "大爽点" in hook_distribution.rhythm_pattern else 0
        
        return min(base_score + diversity_bonus + rhythm_complexity, 1.0)
