"""
深度解析维度数据模型
从"基础特征"到"创作/商业价值特征"的升级
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


# ==================== 枚举定义 ====================

class ConflictType(str, Enum):
    """核心冲突类型"""
    UNDERDOG_REVENGE = "underdog_revenge"           # 底层逆袭
    REVENGE = "revenge"                              # 复仇
    SURVIVAL = "survival"                            # 生存
    IDENTITY = "identity"                            # 身份认同
    LOVE = "love"                                    # 爱情
    POWER_STRUGGLE = "power_struggle"                # 权力斗争
    MORAL_DILEMMA = "moral_dilemma"                  # 道德困境
    COMING_OF_AGE = "coming_of_age"                  # 成长


class HookType(str, Enum):
    """情绪钩子类型"""
    FACE_SLAP = "face_slap"                          # 打脸爽点
    COMEBACK = "comeback"                            # 绝境翻盘
    REVELATION = "revelation"                        # 身世揭秘
    ROMANCE = "romance"                              # 感情线
    CLIMAX = "climax"                                # 高潮
    SUSPENSE = "suspense"                            # 悬念
    TRAGEDY = "tragedy"                              # 虐点
    HUMOR = "humor"                                  # 幽默


class GoldenFingerType(str, Enum):
    """金手指类型"""
    SYSTEM = "system"                                # 系统
    SUPERNATURAL = "supernatural"                    # 异能
    SPACE = "space"                                  # 空间
    KNOWLEDGE = "knowledge"                          # 认知差
    CONNECTIONS = "connections"                      # 人脉
    ITEM = "item"                                    # 道具
    REBIRTH = "rebirth"                              # 重生
    TIME_TRAVEL = "time_travel"                      # 穿越


class GrowthType(str, Enum):
    """金手指成长性"""
    STATIC = "static"                                # 静态
    DYNAMIC_LINEAR = "dynamic_linear"                # 线性成长
    DYNAMIC_EXP = "dynamic_exp"                      # 指数成长
    DYNAMIC_STEP = "dynamic_step"                    # 阶梯成长


class CharacterArcType(str, Enum):
    """人物弧光类型"""
    COWARD_TO_BRAVE = "coward_to_brave"              # 懦弱到强硬
    SELFISH_TO_ALTRUISTIC = "selfish_to_altruistic"  # 自私到利他
    NAIVE_TO_SCHEMING = "naive_to_scheming"          # 天真到腹黑
    WEAK_TO_STRONG = "weak_to_strong"                # 弱到强
    LOST_TO_PURPOSEFUL = "lost_to_purposeful"        # 迷茫到坚定
    ISOLATED_TO_CONNECTED = "isolated_to_connected"  # 孤立到融入


class SupportingRoleFunction(str, Enum):
    """配角功能类型"""
    TOOL_INFO = "tool_info"                          # 信息提供者
    TOOL_RESOURCE = "tool_resource"                  # 资源提供者
    TOOL_ESCAPE = "tool_escape"                      # 退路提供者
    EMOTION_TRIGGER = "emotion_trigger"              # 情绪触发器
    EMOTION_SACRIFICE = "emotion_sacrifice"          # 牺牲型虐点
    CONTRAST_FOIL = "contrast_foil"                  # 对比衬托
    CONFLICT_ANTAGONIST = "conflict_antagonist"      # 冲突制造者


class AdaptationType(str, Enum):
    """改编类型"""
    SHORT_DRAMA = "short_drama"                      # 短剧
    ANIME = "anime"                                  # 动漫
    AUDIOBOOK = "audiobook"                          # 有声书
    GAME = "game"                                    # 游戏
    FILM = "film"                                    # 影视
    COMIC = "comic"                                  # 漫画


class AudienceSegment(str, Enum):
    """受众群体"""
    STUDENT_MIDDLE = "student_middle"                # 中学生
    STUDENT_COLLEGE = "student_college"              # 大学生
    WORKPLACE_JUNIOR = "workplace_junior"            # 职场新人
    WORKPLACE_SENIOR = "workplace_senior"            # 资深职场
    MIDDLE_AGED = "middle_aged"                      # 中年群体


# ==================== 1. 故事内核解析 ====================

class CoreConflictFormula(BaseModel):
    """核心冲突公式"""
    conflict_type: ConflictType
    formula_name: str                                # 公式名称，如"底层逆袭公式"
    protagonist_desire: str                          # 主角核心诉求
    core_obstacle: str                               # 核心阻碍
    solution_path: str                               # 解决路径
    reusability_score: float = Field(ge=0, le=1)     # 可复用性评分
    applicable_genres: List[str] = Field(default_factory=list)  # 适用类型
    
    def to_formula_string(self) -> str:
        """转换为公式字符串"""
        return f"「{self.formula_name}」= 诉求({self.protagonist_desire}) + 阻碍({self.core_obstacle}) + 路径({self.solution_path})"


class EmotionalHook(BaseModel):
    """情绪钩子"""
    hook_type: HookType
    chapter_number: int                              # 出现章节
    position_in_chapter: str                         # 章节位置(开头/中间/结尾)
    intensity: int = Field(ge=1, le=5)               # 情绪强度 1-5
    trigger_keywords: List[str] = Field(default_factory=list)  # 触发关键词
    emotional_response: str                          # 预期读者反应
    
    
class EmotionalHookDistribution(BaseModel):
    """情绪钩子分布"""
    total_hooks: int
    type_distribution: Dict[HookType, int]           # 类型分布
    rhythm_pattern: str                              # 节奏模式，如"每3章1小爽点，每10章1大爽点"
    intensity_curve: List[Tuple[int, int]]           # 强度曲线 [(章节号, 强度)]
    peak_chapters: List[int]                         # 高潮章节


class ValueProposition(BaseModel):
    """价值主张"""
    core_value: str                                  # 核心价值观
    value_type: str                                  # 价值类型(奋斗/真诚/丛林法则等)
    relatability_score: float = Field(ge=0, le=1)    # 可代入性评分
    expression_moments: List[int] = Field(default_factory=list)  # 表达时刻(章节号)


class StoryCore(BaseModel):
    """故事内核"""
    conflict_formula: CoreConflictFormula
    hook_distribution: EmotionalHookDistribution
    value_proposition: ValueProposition
    core_attraction: str                             # 核心吸引力总结
    uniqueness_score: float = Field(ge=0, le=1)      # 独特性评分


# ==================== 2. 金手指/核心设定解析 ====================

class GoldenFingerConstraint(BaseModel):
    """金手指约束条件"""
    constraint_type: str                             # 约束类型(代价/限制/副作用)
    description: str                                 # 具体描述
    severity: int = Field(ge=1, le=5)                # 严重程度 1-5
    plot_impact: str                                 # 对剧情的影响


class GoldenFingerDesign(BaseModel):
    """金手指设计"""
    gf_type: GoldenFingerType
    gf_name: Optional[str] = None                    # 金手指名称
    growth_type: GrowthType
    initial_power: str                               # 初始能力
    max_potential: str                               # 最大潜力
    constraints: List[GoldenFingerConstraint] = Field(default_factory=list)
    
    # 适配性分析
    protagonist_pain_point: str                      # 主角初期痛点
    fit_score: float = Field(ge=0, le=1)             # 适配度评分
    
    # 创新性
    innovation_points: List[str] = Field(default_factory=list)  # 创新点
    similarity_to_common: float = Field(ge=0, le=1)  # 与常见设定相似度


class WorldRule(BaseModel):
    """世界观规则"""
    rule_name: str
    rule_description: str
    rule_category: str                               # 力量体系/资源分配/社会结构
    consistency_score: float = Field(ge=0, le=1)     # 自洽性评分
    

class WorldRuleExploit(BaseModel):
    """规则漏洞利用"""
    exploit_description: str                         # 漏洞描述
    exploited_by: str                                # 利用者
    exploit_benefit: str                             # 获得的好处
    exploit_chapter: int                             # 利用章节


class CoreSetting(BaseModel):
    """核心设定"""
    golden_finger: GoldenFingerDesign
    world_rules: List[WorldRule] = Field(default_factory=list)
    rule_exploits: List[WorldRuleExploit] = Field(default_factory=list)
    setting_coherence: float = Field(ge=0, le=1)     # 设定整体自洽性
    setting_novelty: float = Field(ge=0, le=1)       # 设定新颖度


# ==================== 3. 人物弧光与人设模板 ====================

class CharacterArc(BaseModel):
    """人物弧光"""
    arc_type: CharacterArcType
    initial_state: str                               # 初始状态
    turning_points: List[Tuple[int, str]]            # 转折点 [(章节, 事件)]
    final_state: str                                 # 最终状态
    completion_degree: float = Field(ge=0, le=1)     # 完成度
    reader_satisfaction: float = Field(ge=0, le=1)   # 读者满意度预测


class CharacterTag(BaseModel):
    """人设记忆点"""
    tag_type: str                                    # 语言/行为/外貌/习惯
    tag_description: str                             # 标签描述
    frequency: int                                   # 出现频次
    example_quotes: List[str] = Field(default_factory=list)  # 示例引用


class SupportingRoleTemplate(BaseModel):
    """配角功能性模板"""
    role_name: str
    function_type: SupportingRoleFunction
    role_description: str
    relationship_to_protagonist: str                 # 与主角关系
    plot_function: str                               # 剧情功能
    reusability_score: float = Field(ge=0, le=1)     # 模板可复用性


class CharacterAnalysis(BaseModel):
    """人物分析"""
    protagonist_arc: CharacterArc
    protagonist_tags: List[CharacterTag] = Field(default_factory=list)
    supporting_roles: List[SupportingRoleTemplate] = Field(default_factory=list)
    character_memorability: float = Field(ge=0, le=1)  # 人物记忆度


# ==================== 4. 叙事节奏与写作技法 ====================

class ChapterStructureTemplate(BaseModel):
    """章节结构模板"""
    template_name: str
    hook_ratio: float                                # 钩子占比
    development_ratio: float                         # 推进占比
    cliffhanger_ratio: float                         # 留钩占比
    avg_paragraph_length: int                        # 平均段落长度
    dialogue_ratio: float                            # 对话占比
    
    def validate_ratios(self) -> bool:
        """验证比例总和"""
        total = self.hook_ratio + self.development_ratio + self.cliffhanger_ratio
        return abs(total - 1.0) < 0.01


class InformationRelease(BaseModel):
    """信息释放"""
    info_type: str                                   # 世界观/人物/剧情
    release_method: str                              # 主动告知/侧面暗示/探索发现
    release_chapters: List[int]                      # 释放章节
    mystery_ratio: float = Field(ge=0, le=1)         # 留白比例


class LanguageStyleFeatures(BaseModel):
    """语言风格量化特征"""
    short_sentence_ratio: float                      # 短句占比(<10字)
    long_sentence_ratio: float                       # 长句占比(>30字)
    avg_sentence_length: float                       # 平均句长
    
    perspective_switches: int                        # 视角切换次数
    primary_perspective: str                         # 主要视角
    
    sensory_distribution: Dict[str, float] = Field(default_factory=dict)  # 感官描写占比
    
    rhythm_score: float = Field(ge=0, le=1)          # 节奏感评分


class NarrativeTechnique(BaseModel):
    """叙事技法"""
    chapter_template: ChapterStructureTemplate
    info_releases: List[InformationRelease] = Field(default_factory=list)
    language_style: LanguageStyleFeatures
    
    applicable_scenarios: List[str] = Field(default_factory=list)  # 适用场景
    technique_difficulty: int = Field(ge=1, le=5)    # 技法难度


# ==================== 5. 商业价值解析 ====================

class AudienceProfile(BaseModel):
    """受众画像"""
    primary_segment: AudienceSegment                 # 主要受众
    secondary_segments: List[AudienceSegment] = Field(default_factory=list)
    age_range: Tuple[int, int]                       # 年龄范围
    gender_distribution: Dict[str, float]            # 性别分布
    
    # 付费意愿
    payment_motivation: str                          # 付费动机
    payment_triggers: List[str] = Field(default_factory=list)  # 付费触发点
    estimated_arpu: float                            # 预估ARPU


class AdaptationPotential(BaseModel):
    """改编潜力"""
    adaptation_type: AdaptationType
    suitability_score: float = Field(ge=0, le=1)     # 适配度评分
    key_adaptation_points: List[str] = Field(default_factory=list)  # 适配亮点
    adaptation_cost_score: float = Field(ge=0, le=1) # 改编成本评分(越低成本越高分)
    roi_prediction: float                            # ROI预测


class DerivativeValue(BaseModel):
    """衍生价值"""
    derivative_type: str                             # 周边/小程序/系列文等
    value_description: str
    development_difficulty: int = Field(ge=1, le=5)  # 开发难度
    market_potential: float = Field(ge=0, le=1)      # 市场潜力


class CommercialValue(BaseModel):
    """商业价值"""
    audience_profile: AudienceProfile
    adaptation_potentials: List[AdaptationPotential] = Field(default_factory=list)
    derivative_values: List[DerivativeValue] = Field(default_factory=list)
    
    overall_commercial_score: float = Field(ge=0, le=1)  # 整体商业评分
    monetization_path: str                           # 变现路径建议


# ==================== 深度解析结果汇总 ====================

class DeepNovelFeatures(BaseModel):
    """深度小说特征 - 完整解析结果"""
    novel_id: str
    
    # 五大核心维度
    story_core: StoryCore                            # 故事内核
    core_setting: CoreSetting                        # 核心设定
    character_analysis: CharacterAnalysis            # 人物分析
    narrative_technique: NarrativeTechnique          # 叙事技法
    commercial_value: CommercialValue                # 商业价值
    
    # 元信息
    analysis_version: str = "2.0"
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    overall_quality_score: float = Field(ge=0, le=1) # 整体质量评分
    
    # 对比基准
    benchmark_comparisons: Dict[str, Any] = Field(default_factory=dict)
    
    # 可复用标签
    reusable_tags: List[str] = Field(default_factory=list)
    
    # 逆向验证
    reverse_summary: str                             # 逆向生成的梗概
    consistency_check: float = Field(ge=0, le=1)     # 一致性检查评分
    
    def generate_formula_summary(self) -> str:
        """生成公式化总结"""
        parts = [
            f"「{self.story_core.conflict_formula.formula_name}」",
            f"「{self.core_setting.golden_finger.gf_type.value}金手指({self.core_setting.golden_finger.growth_type.value})」",
            f"「爽点节奏({self.story_core.hook_distribution.rhythm_pattern})」",
            f"「{self.commercial_value.audience_profile.primary_segment.value}受众(付费点:{self.commercial_value.audience_profile.payment_motivation})」"
        ]
        return " + ".join(parts)
