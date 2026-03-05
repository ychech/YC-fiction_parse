"""
商业价值解析引擎
拆解小说的"商业潜力/变现逻辑"
"""
import re
from typing import Dict, List, Tuple

from src.common.deep_schemas import (
    AdaptationPotential,
    AdaptationType,
    AudienceProfile,
    AudienceSegment,
    CommercialValue,
    DerivativeValue,
)
from src.common.logger import get_logger

logger = get_logger(__name__)


class CommercialExtractor:
    """商业价值解析器"""
    
    # 受众群体关键词
    AUDIENCE_KEYWORDS = {
        AudienceSegment.STUDENT_MIDDLE: [
            "高中", "初中", "中考", "高考", "班级", "同学", "老师", "校园",
            "青春期", "叛逆", "成长"
        ],
        AudienceSegment.STUDENT_COLLEGE: [
            "大学", "宿舍", "室友", "社团", "选课", "考试", "毕业", "就业",
            "实习", "考研"
        ],
        AudienceSegment.WORKPLACE_JUNIOR: [
            "职场", "新人", "实习", "面试", "入职", "老板", "同事", "加班",
            "升职加薪", "996"
        ],
        AudienceSegment.WORKPLACE_SENIOR: [
            "管理", "项目", "团队", "总监", "经理", "创业", "融资", "上市",
            "并购", "战略"
        ],
        AudienceSegment.MIDDLE_AGED: [
            "中年", "家庭", "孩子", "教育", "房贷", "压力", "危机", "转型",
            "第二春", "回忆"
        ],
    }
    
    # 付费触发点关键词
    PAYMENT_TRIGGERS = {
        "悬念": ["悬念", "谜团", "未知", "即将", "接下来", "下一章"],
        "爽点": ["打脸", "逆袭", "翻盘", "震惊", "无敌", "碾压"],
        "情感": ["感动", "心疼", "泪目", "虐", "甜", "暖"],
        "认同": ["共鸣", "真实", "像自己", "代入感", "感同身受"],
    }
    
    # 改编适配关键词
    ADAPTATION_KEYWORDS = {
        AdaptationType.SHORT_DRAMA: [
            "冲突", "反转", "快节奏", "爽点密集", "场景简单", "人物少"
        ],
        AdaptationType.ANIME: [
            "世界观", "战斗", "特效", "视觉", "热血", "冒险"
        ],
        AdaptationType.AUDIOBOOK: [
            "对话", "心理描写", "情感", "氛围", "节奏适中"
        ],
        AdaptationType.GAME: [
            "系统", "升级", "装备", "技能", "副本", "任务", "战斗"
        ],
        AdaptationType.FILM: [
            "剧情", "深度", "主题", "视觉", "情感", "冲突"
        ],
        AdaptationType.COMIC: [
            "画面感", "动作", "表情", "分镜", "视觉冲击力"
        ],
    }
    
    def extract(
        self,
        text: str,
        chapters: List[Dict],
        story_features: Dict,
        setting_features: Dict,
    ) -> CommercialValue:
        """
        提取商业价值
        
        Args:
            text: 全文文本
            chapters: 章节列表
            story_features: 故事内核特征
            setting_features: 设定特征
        
        Returns:
            CommercialValue: 商业价值
        """
        logger.info("commercial_extraction_started")
        
        # 1. 分析受众画像
        audience_profile = self._analyze_audience(text, chapters)
        
        # 2. 分析改编潜力
        adaptation_potentials = self._analyze_adaptation_potential(
            text, chapters, story_features, setting_features
        )
        
        # 3. 分析衍生价值
        derivative_values = self._analyze_derivative_values(
            text, setting_features
        )
        
        # 4. 计算整体商业评分
        overall_score = self._calculate_commercial_score(
            audience_profile, adaptation_potentials, derivative_values
        )
        
        # 5. 生成变现路径建议
        monetization_path = self._generate_monetization_path(
            audience_profile, adaptation_potentials
        )
        
        commercial_value = CommercialValue(
            audience_profile=audience_profile,
            adaptation_potentials=adaptation_potentials,
            derivative_values=derivative_values,
            overall_commercial_score=round(overall_score, 2),
            monetization_path=monetization_path,
        )
        
        logger.info(
            "commercial_extraction_completed",
            primary_audience=audience_profile.primary_segment.value,
            adaptations=len(adaptation_potentials),
            overall_score=overall_score,
        )
        
        return commercial_value
    
    def _analyze_audience(self, text: str, chapters: List[Dict]) -> AudienceProfile:
        """分析受众画像"""
        # 1. 识别主要受众
        audience_scores = {}
        for segment, keywords in self.AUDIENCE_KEYWORDS.items():
            score = sum(text.count(kw) for kw in keywords)
            audience_scores[segment] = score
        
        primary_segment = max(audience_scores.items(), key=lambda x: x[1])[0]
        
        # 2. 识别次要受众
        secondary_segments = [
            seg for seg, score in audience_scores.items()
            if score > 0 and seg != primary_segment
        ][:2]
        
        # 3. 推断年龄范围
        age_range = self._infer_age_range(primary_segment)
        
        # 4. 推断性别分布
        gender_dist = self._infer_gender_distribution(text)
        
        # 5. 分析付费动机和触发点
        payment_motivation, payment_triggers = self._analyze_payment_behavior(text)
        
        # 6. 预估ARPU
        estimated_arpu = self._estimate_arpu(primary_segment, payment_motivation)
        
        return AudienceProfile(
            primary_segment=primary_segment,
            secondary_segments=secondary_segments,
            age_range=age_range,
            gender_distribution=gender_dist,
            payment_motivation=payment_motivation,
            payment_triggers=payment_triggers,
            estimated_arpu=estimated_arpu,
        )
    
    def _infer_age_range(self, segment: AudienceSegment) -> Tuple[int, int]:
        """推断年龄范围"""
        age_ranges = {
            AudienceSegment.STUDENT_MIDDLE: (12, 18),
            AudienceSegment.STUDENT_COLLEGE: (18, 25),
            AudienceSegment.WORKPLACE_JUNIOR: (22, 30),
            AudienceSegment.WORKPLACE_SENIOR: (30, 45),
            AudienceSegment.MIDDLE_AGED: (35, 55),
        }
        return age_ranges.get(segment, (18, 45))
    
    def _infer_gender_distribution(self, text: str) -> Dict[str, float]:
        """推断性别分布"""
        # 基于内容特征推断
        male_indicators = ["热血", "战斗", "升级", "争霸", "兄弟", "妹子"]
        female_indicators = ["爱情", "甜宠", "虐恋", "宫斗", "闺蜜", "男神"]
        
        male_score = sum(text.count(w) for w in male_indicators)
        female_score = sum(text.count(w) for w in female_indicators)
        
        total = male_score + female_score
        if total == 0:
            return {"male": 0.5, "female": 0.5}
        
        male_ratio = male_score / total
        female_ratio = female_score / total
        
        # 归一化
        return {
            "male": round(male_ratio, 2),
            "female": round(female_ratio, 2),
        }
    
    def _analyze_payment_behavior(self, text: str) -> Tuple[str, List[str]]:
        """分析付费行为"""
        trigger_scores = {}
        for trigger_type, keywords in self.PAYMENT_TRIGGERS.items():
            score = sum(text.count(kw) for kw in keywords)
            trigger_scores[trigger_type] = score
        
        # 主要付费动机
        primary_trigger = max(trigger_scores.items(), key=lambda x: x[1])[0]
        
        motivation_map = {
            "悬念": "追更解谜",
            "爽点": "获得爽感",
            "情感": "情感满足",
            "认同": "自我代入",
        }
        payment_motivation = motivation_map.get(primary_trigger, "综合需求")
        
        # 付费触发点
        triggers = [t for t, s in trigger_scores.items() if s > 5]
        
        return payment_motivation, triggers
    
    def _estimate_arpu(
        self,
        segment: AudienceSegment,
        motivation: str
    ) -> float:
        """预估ARPU"""
        # 基础ARPU
        base_arpu = {
            AudienceSegment.STUDENT_MIDDLE: 15,
            AudienceSegment.STUDENT_COLLEGE: 25,
            AudienceSegment.WORKPLACE_JUNIOR: 50,
            AudienceSegment.WORKPLACE_SENIOR: 80,
            AudienceSegment.MIDDLE_AGED: 60,
        }.get(segment, 30)
        
        # 付费动机加成
        motivation_multiplier = {
            "追更解谜": 1.2,
            "获得爽感": 1.0,
            "情感满足": 1.3,
            "自我代入": 1.1,
        }.get(motivation, 1.0)
        
        return round(base_arpu * motivation_multiplier, 2)
    
    def _analyze_adaptation_potential(
        self,
        text: str,
        chapters: List[Dict],
        story_features: Dict,
        setting_features: Dict,
    ) -> List[AdaptationPotential]:
        """分析改编潜力"""
        potentials = []
        
        for adaptation_type, keywords in self.ADAPTATION_KEYWORDS.items():
            # 计算适配度
            score = sum(text.count(kw) for kw in keywords)
            max_score = len(keywords) * 10  # 假设每个关键词最多出现10次
            suitability = min(score / max_score, 1.0)
            
            # 识别适配亮点
            key_points = [kw for kw in keywords if text.count(kw) > 5][:3]
            
            # 估算改编成本
            cost_score = self._estimate_adaptation_cost(
                adaptation_type, text, chapters
            )
            
            # 预测ROI
            roi = self._predict_roi(suitability, cost_score)
            
            if suitability > 0.3:  # 只保留有潜力的
                potential = AdaptationPotential(
                    adaptation_type=adaptation_type,
                    suitability_score=round(suitability, 2),
                    key_adaptation_points=key_points,
                    adaptation_cost_score=round(cost_score, 2),
                    roi_prediction=round(roi, 2),
                )
                potentials.append(potential)
        
        # 按ROI排序
        potentials.sort(key=lambda x: x.roi_prediction, reverse=True)
        
        return potentials[:3]  # 最多3个
    
    def _estimate_adaptation_cost(
        self,
        adaptation_type: AdaptationType,
        text: str,
        chapters: List[Dict]
    ) -> float:
        """估算改编成本（分数越高成本越低）"""
        # 基础成本分
        base_cost = {
            AdaptationType.SHORT_DRAMA: 0.8,  # 成本低
            AdaptationType.AUDIOBOOK: 0.9,
            AdaptationType.COMIC: 0.6,
            AdaptationType.ANIME: 0.3,
            AdaptationType.FILM: 0.2,
            AdaptationType.GAME: 0.25,
        }.get(adaptation_type, 0.5)
        
        # 场景复杂度调整
        scene_complexity = len(set(re.findall(r"场景|地点|地方", text)))
        if scene_complexity > 20:
            base_cost -= 0.1
        
        # 人物数量调整
        character_count = len(set(re.findall(r"[\u4e00-\u9fa5]{2,4}(?:说道|说)", text)))
        if character_count > 30:
            base_cost -= 0.1
        
        return max(base_cost, 0.1)
    
    def _predict_roi(self, suitability: float, cost_score: float) -> float:
        """预测ROI"""
        # ROI = 适配度 / (1 - 成本分)
        cost_factor = 1 - cost_score
        if cost_factor < 0.1:
            cost_factor = 0.1
        
        roi = (suitability * 0.7 + cost_score * 0.3) / cost_factor
        return min(roi, 5.0)  # 上限5倍
    
    def _analyze_derivative_values(self, text: str, setting_features: Dict) -> List[DerivativeValue]:
        """分析衍生价值"""
        derivatives = []
        
        # 1. 金手指系统小程序
        if "系统" in text:
            derivatives.append(DerivativeValue(
                derivative_type="金手指系统小程序",
                value_description="将小说中的金手指系统开发为互动小程序",
                development_difficulty=3,
                market_potential=0.7,
            ))
        
        # 2. 人设周边
        character_count = len(set(re.findall(r"[\u4e00-\u9fa5]{2,4}(?:说道|说)", text)))
        if character_count >= 5:
            derivatives.append(DerivativeValue(
                derivative_type="人设周边",
                value_description="基于主要角色开发周边产品",
                development_difficulty=2,
                market_potential=0.6,
            ))
        
        # 3. 系列文开发
        if "世界观" in text or len(text) > 500000:  # 长文本
            derivatives.append(DerivativeValue(
                derivative_type="系列文开发",
                value_description="基于世界观开发系列作品",
                development_difficulty=4,
                market_potential=0.8,
            ))
        
        # 4. 互动小说
        if "选择" in text or "分支" in text:
            derivatives.append(DerivativeValue(
                derivative_type="互动小说",
                value_description="改编为互动叙事作品",
                development_difficulty=3,
                market_potential=0.65,
            ))
        
        return derivatives
    
    def _calculate_commercial_score(
        self,
        audience: AudienceProfile,
        adaptations: List[AdaptationPotential],
        derivatives: List[DerivativeValue],
    ) -> float:
        """计算整体商业评分"""
        # 受众价值 (30%)
        audience_score = min(audience.estimated_arpu / 100, 1.0) * 0.3
        
        # 改编价值 (40%)
        if adaptations:
            adaptation_score = max(a.roi_prediction for a in adaptations) / 5 * 0.4
        else:
            adaptation_score = 0.1
        
        # 衍生价值 (30%)
        if derivatives:
            derivative_score = sum(d.market_potential for d in derivatives) / len(derivatives) * 0.3
        else:
            derivative_score = 0.1
        
        return min(audience_score + adaptation_score + derivative_score, 1.0)
    
    def _generate_monetization_path(
        self,
        audience: AudienceProfile,
        adaptations: List[AdaptationPotential],
    ) -> str:
        """生成变现路径建议"""
        paths = []
        
        # 基础付费阅读
        paths.append(f"付费阅读（核心受众：{audience.primary_segment.value}）")
        
        # 改编变现
        if adaptations:
            top_adaptation = adaptations[0]
            paths.append(f"{top_adaptation.adaptation_type.value}改编（ROI预测：{top_adaptation.roi_prediction:.1f}倍）")
        
        # IP衍生
        paths.append("IP衍生开发（周边、游戏、系列文）")
        
        return " → ".join(paths)
