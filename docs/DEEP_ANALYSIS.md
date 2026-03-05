# 小说深度解析系统 - 技术文档

## 概述

深度解析系统从"基础特征"升级到"创作/商业价值特征"，挖掘小说的核心竞争力和商业潜力。

## 五大核心解析维度

### 1. 故事内核解析

**目标**：挖掘小说"不变的核心逻辑"

#### 1.1 核心冲突公式
```python
CoreConflictFormula:
    conflict_type: ConflictType          # 冲突类型
    formula_name: str                     # 公式名称
    protagonist_desire: str               # 主角核心诉求
    core_obstacle: str                    # 核心阻碍
    solution_path: str                    # 解决路径
    reusability_score: float              # 可复用性评分
```

**示例输出**：
```
「底层逆袭公式」= 诉求(摆脱底层身份，获得尊重和地位) + 
                 阻碍(资源匮乏、权力压制、阶层固化) + 
                 路径(金手指/认知差/贵人相助)
可复用性: 0.85
适用类型: ["都市", "修仙", "玄幻"]
```

#### 1.2 情绪钩子分布
```python
EmotionalHookDistribution:
    total_hooks: int                      # 钩子总数
    type_distribution: Dict[HookType, int] # 类型分布
    rhythm_pattern: str                   # 节奏模式
    intensity_curve: List[Tuple[int, int]] # 强度曲线
    peak_chapters: List[int]              # 高潮章节
```

**示例输出**：
```
节奏模式: 每3章1个小爽点，每10章1个大爽点
主要钩子类型: 打脸爽点(45%), 绝境翻盘(20%), 悬念(15%)
高潮章节: [10, 25, 50, 80, 100]
```

#### 1.3 价值主张
```python
ValueProposition:
    core_value: str                       # 核心价值观
    value_type: str                       # 价值类型
    relatability_score: float             # 可代入性评分
    expression_moments: List[int]         # 表达时刻
```

---

### 2. 金手指/核心设定解析

**目标**：拆解"让小说差异化的核心设定"

#### 2.1 金手指设计逻辑
```python
GoldenFingerDesign:
    gf_type: GoldenFingerType             # 金手指类型
    growth_type: GrowthType               # 成长性
    initial_power: str                    # 初始能力
    max_potential: str                    # 最大潜力
    constraints: List[GoldenFingerConstraint]  # 约束条件
    fit_score: float                      # 与主角适配度
    innovation_points: List[str]          # 创新点
    similarity_to_common: float           # 与常见设定相似度
```

**示例输出**：
```
金手指类型: 系统
成长性: 动态线性成长
约束条件:
  - 类型: 代价, 描述: 使用系统兑换需消耗情绪值, 严重程度: 4/5
  - 类型: 限制, 描述: 每日兑换次数有限制, 严重程度: 3/5
创新点: ["使用'情绪值'作为系统兑换资源，而非传统积分"]
与常见设定相似度: 0.6
```

#### 2.2 世界观规则
```python
WorldRule:
    rule_name: str                        # 规则名称
    rule_description: str                 # 规则描述
    rule_category: str                    # 规则类别
    consistency_score: float              # 自洽性评分
```

#### 2.3 规则漏洞利用
```python
WorldRuleExploit:
    exploit_description: str              # 漏洞描述
    exploited_by: str                     # 利用者
    exploit_benefit: str                  # 获得的好处
    exploit_chapter: int                  # 利用章节
```

---

### 3. 人物弧光与人设模板解析

**目标**：拆解"读者愿意追更的人物逻辑"

#### 3.1 主角弧光
```python
CharacterArc:
    arc_type: CharacterArcType            # 弧光类型
    initial_state: str                    # 初始状态
    turning_points: List[Tuple[int, str]] # 转折点
    final_state: str                      # 最终状态
    completion_degree: float              # 完成度
    reader_satisfaction: float            # 读者满意度预测
```

**示例输出**：
```
弧光类型: 弱到强
初始状态: 实力弱小，常被欺负
转折点:
  - 第5章: 获得神秘戒指
  - 第20章: 首次突破境界
  - 第50章: 击败宿敌
最终状态: 实力强大，无人敢欺
完成度: 0.85
读者满意度预测: 0.90
```

#### 3.2 人设记忆点
```python
CharacterTag:
    tag_type: str                         # 标签类型(语言/行为/习惯)
    tag_description: str                  # 标签描述
    frequency: int                        # 出现频次
    example_quotes: List[str]             # 示例引用
```

**示例输出**：
```
标签类型: 语言
标签描述: 说话喜欢带语气词"啧"
出现频次: 128次
示例: ["'啧，真是麻烦。'张三说道", "'啧，看来不得不出手了。'"]
```

#### 3.3 配角功能性模板
```python
SupportingRoleTemplate:
    role_name: str                        # 角色名称
    function_type: SupportingRoleFunction # 功能类型
    role_description: str                 # 角色描述
    relationship_to_protagonist: str      # 与主角关系
    plot_function: str                    # 剧情功能
    reusability_score: float              # 模板可复用性
```

**示例输出**：
```
角色名称: 李长老
功能类型: 工具型-信息提供者
角色描述: 信息提供者，为主角提供关键情报
与主角关系: 师徒
剧情功能: 推动信息线，提供剧情线索
可复用性: 0.90
```

---

### 4. 叙事节奏与写作技法解析

**目标**：拆解"可复制的写作技巧"

#### 4.1 章节结构模板
```python
ChapterStructureTemplate:
    template_name: str                    # 模板名称
    hook_ratio: float                     # 钩子占比
    development_ratio: float              # 推进占比
    cliffhanger_ratio: float              # 留钩占比
    avg_paragraph_length: int             # 平均段落长度
    dialogue_ratio: float                 # 对话占比
```

**示例输出**：
```
章节结构: 标准网文章节结构
钩子占比: 15%
推进占比: 70%
留钩占比: 15%
平均段落长度: 180字
对话占比: 35%
```

#### 4.2 信息释放节奏
```python
InformationRelease:
    info_type: str                        # 信息类型
    release_method: str                   # 释放方式
    release_chapters: List[int]           # 释放章节
    mystery_ratio: float                  # 留白比例
```

#### 4.3 语言风格量化
```python
LanguageStyleFeatures:
    short_sentence_ratio: float           # 短句占比
    long_sentence_ratio: float            # 长句占比
    avg_sentence_length: float            # 平均句长
    perspective_switches: int             # 视角切换次数
    primary_perspective: str              # 主要视角
    sensory_distribution: Dict[str, float] # 感官描写占比
    rhythm_score: float                   # 节奏感评分
```

**示例输出**：
```
短句占比: 45% (节奏快)
长句占比: 15%
平均句长: 12.5字
视角切换: 0次 (全程第三人称限知视角)
感官描写分布: {视觉: 0.5, 听觉: 0.2, 触觉: 0.15, 嗅觉: 0.1, 味觉: 0.05}
节奏感评分: 0.85
```

---

### 5. 商业价值解析

**目标**：拆解小说的"商业潜力/变现逻辑"

#### 5.1 受众画像
```python
AudienceProfile:
    primary_segment: AudienceSegment       # 主要受众
    secondary_segments: List[AudienceSegment] # 次要受众
    age_range: Tuple[int, int]             # 年龄范围
    gender_distribution: Dict[str, float]  # 性别分布
    payment_motivation: str                # 付费动机
    payment_triggers: List[str]            # 付费触发点
    estimated_arpu: float                  # 预估ARPU
```

**示例输出**：
```
主要受众: 大学生 (18-25岁)
性别分布: {male: 0.7, female: 0.3}
付费动机: 获得爽感
付费触发点: ["打脸", "逆袭", "震惊"]
预估ARPU: 32.5元
```

#### 5.2 改编潜力
```python
AdaptationPotential:
    adaptation_type: AdaptationType        # 改编类型
    suitability_score: float               # 适配度评分
    key_adaptation_points: List[str]       # 适配亮点
    adaptation_cost_score: float           # 改编成本评分
    roi_prediction: float                  # ROI预测
```

**示例输出**：
```
改编类型: 短剧
适配度: 0.85
适配亮点: ["冲突密集", "场景简单", "节奏快"]
改编成本: 0.8 (低成本)
ROI预测: 3.5倍
```

#### 5.3 衍生价值
```python
DerivativeValue:
    derivative_type: str                   # 衍生类型
    value_description: str                 # 价值描述
    development_difficulty: int            # 开发难度
    market_potential: float                # 市场潜力
```

---

## API 接口

### 执行深度解析
```bash
POST /api/v1/deep/{novel_id}/deep-parse

Request:
{
    "compare_with_benchmark": true
}

Response:
{
    "code": 200,
    "data": {
        "novel_id": "xxx",
        "deep_features": {...},
        "formula_summary": "「底层逆袭公式」+「系统金手指(动态+情绪值约束)」+...",
        "overall_quality": 0.85,
        "consistency_check": 0.92
    }
}
```

### 获取公式化总结
```bash
GET /api/v1/deep/{novel_id}/formula-summary

Response:
{
    "code": 200,
    "data": {
        "formula_summary": "「底层逆袭公式」+「系统金手指(动态+情绪值约束)」+「爽点节奏(3小1大)」+「学生受众(付费点:打脸爽点)」",
        "reusable_tags": [
            "冲突公式:底层逆袭公式",
            "金手指:system",
            "成长性:dynamic_linear",
            ...
        ]
    }
}
```

### 获取对比分析报告
```bash
GET /api/v1/deep/{novel_id}/comparison-report

Response:
{
    "code": 200,
    "data": {
        "report": "对比分析报告...",
        "has_comparison": true
    }
}
```

---

## 对比基准库

### 功能
1. **标杆管理**：存储优秀小说的深度解析结果
2. **对比分析**：自动对比新小说与标杆的差异
3. **趋势分析**：分析近期热门作品的共同特征
4. **动态更新**：基于市场数据更新解析权重

### 使用示例
```python
# 添加标杆
POST /api/v1/deep/benchmarks
{
    "novel_id": "xxx",
    "title": "斗破苍穹",
    "author": "天蚕土豆",
    "genre": "玄幻",
    "market_data": {
        "read_count": 10000000,
        "rating": 4.5
    }
}

# 获取 trending 特征
GET /api/v1/deep/trending-features?genre=玄幻&days=30

Response:
{
    "trending_conflict_types": [
        ["underdog_revenge", 45],
        ["coming_of_age", 25],
        ...
    ],
    "trending_gf_types": [
        ["system", 35],
        ["supernatural", 20],
        ...
    ]
}
```

---

## 工程化落地技巧

### 1. 公式化表达
所有解析结果转为"定量公式/标签"：
```
节奏 = 爽点密度(3个/10章) + 信息释放速度(500字/关键信息) + 章节闭环率(90%)
```

### 2. 逆向验证
解析完成后，基于结果生成"100字核心梗概"，对比原小说核心吸引力是否一致。

### 3. 动态迭代
基于用户反馈和市场数据迭代解析规则：
```python
# 如果发现某类特征近期表现好，增加其权重
if trending_analysis["gf_constraints"] > threshold:
    update_parsing_weight("golden_finger.constraints", increase=0.1)
```

---

## 应用场景

### 1. 网文创作辅助
- 提供可复用的冲突公式和人物模板
- 分析爽点节奏，优化情绪钩子分布
- 评估设定自洽性和创新性

### 2. 竞品分析
- 对比同类标杆，找出差异化优势
- 识别可复用的成功元素
- 获取优化建议

### 3. IP开发决策
- 评估改编潜力和ROI
- 分析受众画像和付费意愿
- 识别衍生价值点

### 4. 平台运营
- 分析 trending 特征，指导内容方向
- 评估新作品的商业潜力
- 优化推荐算法
