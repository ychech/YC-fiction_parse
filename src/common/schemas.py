"""
全局数据模型定义
使用 Pydantic 定义所有数据结构，保证类型安全
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class NovelFormat(str, Enum):
    """支持的小说格式"""
    TXT = "txt"
    EPUB = "epub"
    MOBI = "mobi"


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"           # 等待中
    PREPROCESSING = "preprocessing"  # 预处理中
    EXTRACTING = "extracting"     # 特征提取中
    FUSING = "fusing"             # 结果融合中
    COMPLETED = "completed"       # 完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class Priority(int, Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NarrativePerspective(str, Enum):
    """叙事视角"""
    FIRST_PERSON = "first_person"      # 第一人称
    SECOND_PERSON = "second_person"    # 第二人称
    THIRD_PERSON = "third_person"      # 第三人称
    MULTI_PERSON = "multi_person"      # 多视角


class NovelGenre(str, Enum):
    """小说类型"""
    FANTASY = "fantasy"                # 玄幻
    XIANXIA = "xianxia"                # 仙侠
    WUXIA = "wuxia"                    # 武侠
    SCI_FI = "sci_fi"                  # 科幻
    URBAN = "urban"                    # 都市
    HISTORY = "history"                # 历史
    ROMANCE = "romance"                # 言情
    MYSTERY = "mystery"                # 悬疑
    HORROR = "horror"                  # 恐怖
    GAME = "game"                      # 游戏
    SPORTS = "sports"                  # 体育
    MILITARY = "military"              # 军事
    OTHER = "other"                    # 其他


# ==================== 基础模型 ====================

class BaseSchema(BaseModel):
    """基础模型"""
    class Config:
        from_attributes = True
        populate_by_name = True


class TimestampMixin(BaseSchema):
    """时间戳混入"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# ==================== 小说元信息 ====================

class NovelMeta(BaseSchema):
    """小说元信息"""
    id: Optional[str] = None
    title: str
    author: Optional[str] = None
    genre: Optional[NovelGenre] = None
    word_count: Optional[int] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    format: NovelFormat
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    status: str = "active"


class NovelCreate(BaseSchema):
    """创建小说请求"""
    title: str
    author: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[NovelGenre] = None


class NovelResponse(NovelMeta, TimestampMixin):
    """小说响应"""
    pass


# ==================== 章节结构 ====================

class Chapter(BaseSchema):
    """章节信息"""
    id: Optional[str] = None
    novel_id: str
    chapter_number: int
    title: Optional[str] = None
    content: Optional[str] = None
    word_count: int = 0
    is_core: bool = False  # 是否核心章节
    chapter_hash: Optional[str] = None  # 用于增量解析


class ChapterStructure(BaseSchema):
    """章节结构"""
    total_chapters: int
    core_chapters: List[int] = Field(default_factory=list)
    chapters: List[Chapter]


# ==================== 解析特征 ====================

class TaskFeatures(BaseSchema):
    """任务特征"""
    main_task: Optional[str] = None           # 主线任务
    sub_tasks: List[str] = Field(default_factory=list)  # 支线任务
    task_structure: Optional[str] = None      # 任务结构（如"升级流","签到流"）
    task_difficulty: Optional[str] = None     # 任务难度曲线


class BackgroundFeatures(BaseSchema):
    """背景特征"""
    world_type: Optional[str] = None          # 世界观类型
    era_setting: Optional[str] = None         # 时代设定
    power_system: Optional[str] = None        # 力量体系
    major_factions: List[str] = Field(default_factory=list)  # 主要势力
    world_rules: List[str] = Field(default_factory=list)     # 世界规则


class CharacterFeatures(BaseSchema):
    """人设特征"""
    protagonist: Optional[Dict[str, Any]] = None      # 主角设定
    supporting_roles: List[Dict[str, Any]] = Field(default_factory=list)  # 配角
    character_archetypes: List[str] = Field(default_factory=list)  # 角色原型
    character_relationships: List[Dict[str, str]] = Field(default_factory=list)


class WritingFeatures(BaseSchema):
    """写作手法特征"""
    narrative_perspective: Optional[NarrativePerspective] = None
    pacing: Optional[str] = None              # 节奏（慢热/快节奏）
    rhetoric_style: List[str] = Field(default_factory=list)  # 修辞特点
    sentence_structure: Optional[str] = None  # 句式特点
    humor_style: Optional[str] = None         # 幽默风格
    suspense_techniques: List[str] = Field(default_factory=list)  # 悬念设置


class PlotFeatures(BaseSchema):
    """情节结构特征"""
    plot_structure: Optional[str] = None      # 情节结构（如"三幕式"）
    conflict_types: List[str] = Field(default_factory=list)  # 冲突类型
    plot_twists: int = 0                      # 反转次数
    climax_distribution: Optional[str] = None # 高潮分布
    foreshadowing: List[str] = Field(default_factory=list)  # 伏笔


class NovelFeatures(BaseSchema):
    """小说完整特征"""
    novel_id: str
    task: TaskFeatures = Field(default_factory=TaskFeatures)
    background: BackgroundFeatures = Field(default_factory=BackgroundFeatures)
    character: CharacterFeatures = Field(default_factory=CharacterFeatures)
    writing: WritingFeatures = Field(default_factory=WritingFeatures)
    plot: PlotFeatures = Field(default_factory=PlotFeatures)
    
    # 扩展字段
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # 元信息
    confidence_score: float = 0.0             # 置信度
    extraction_method: str = "unknown"        # 提取方法
    version: str = "1.0"


# ==================== 解析任务 ====================

class ParseTask(BaseSchema):
    """解析任务"""
    id: Optional[str] = None
    novel_id: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.NORMAL
    
    # 进度信息
    progress: float = 0.0                     # 0-100
    current_stage: Optional[str] = None
    stage_progress: Dict[str, float] = Field(default_factory=dict)
    
    # 配置
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # 结果
    result: Optional[NovelFeatures] = None
    error_message: Optional[str] = None
    
    # 时间
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ParseTaskCreate(BaseSchema):
    """创建解析任务"""
    novel_id: str
    priority: Priority = Priority.NORMAL
    config: Optional[Dict[str, Any]] = None


class ParseTaskResponse(ParseTask, TimestampMixin):
    """解析任务响应"""
    pass


# ==================== 检索相关 ====================

class SearchQuery(BaseSchema):
    """搜索请求"""
    query: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    genre: Optional[NovelGenre] = None
    min_confidence: float = 0.0
    
    # 分页
    page: int = 1
    page_size: int = 20
    
    # 排序
    sort_by: str = "created_at"
    sort_order: str = "desc"


class SearchResult(BaseSchema):
    """搜索结果"""
    novel_id: str
    title: str
    author: Optional[str]
    genre: Optional[NovelGenre]
    confidence_score: float
    matched_features: Dict[str, Any]
    similarity_score: Optional[float] = None


class SearchResponse(BaseSchema):
    """搜索响应"""
    total: int
    page: int
    page_size: int
    results: List[SearchResult]


# ==================== API 响应包装 ====================

class APIResponse(BaseSchema):
    """标准API响应"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None
    request_id: Optional[str] = None


class APIError(BaseSchema):
    """API错误响应"""
    code: int
    message: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


# ==================== 规则引擎 ====================

class Rule(BaseSchema):
    """解析规则"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    target_field: str                    # 目标字段
    rule_type: str                       # 规则类型：keyword/regex/ml
    condition: Dict[str, Any]            # 规则条件
    weight: float = 1.0                  # 权重
    priority: int = 1                    # 优先级
    enabled: bool = True


class RuleSet(BaseSchema):
    """规则集"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    genre: Optional[NovelGenre] = None   # 适用的类型
    rules: List[Rule] = Field(default_factory=list)
    version: str = "1.0"
    enabled: bool = True
