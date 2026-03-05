"""
人物弧光与人设模板解析引擎
拆解"读者愿意追更的人物逻辑"
"""
import re
from typing import Dict, List, Tuple

from src.common.deep_schemas import (
    CharacterAnalysis,
    CharacterArc,
    CharacterArcType,
    CharacterTag,
    SupportingRoleFunction,
    SupportingRoleTemplate,
)
from src.common.logger import get_logger

logger = get_logger(__name__)


class CharacterExtractor:
    """人物解析器"""
    
    # 人物弧光关键词
    ARC_KEYWORDS = {
        CharacterArcType.COWARD_TO_BRAVE: [
            ("胆小", "懦弱", "害怕", "退缩"),
            ("勇敢", "坚强", "无畏", "挺身而出")
        ],
        CharacterArcType.SELFISH_TO_ALTRUISTIC: [
            ("自私", "自利", "只顾自己", "冷漠"),
            ("无私", "奉献", "为他人", "牺牲")
        ],
        CharacterArcType.NAIVE_TO_SCHEMING: [
            ("天真", "单纯", "幼稚", "轻信"),
            ("腹黑", "深沉", "算计", "城府")
        ],
        CharacterArcType.WEAK_TO_STRONG: [
            ("弱小", "无力", "被欺负", "废物"),
            ("强大", "无敌", "碾压", "顶尖")
        ],
        CharacterArcType.LOST_TO_PURPOSEFUL: [
            ("迷茫", "困惑", "没有目标", "随波逐流"),
            ("坚定", "目标明确", "有追求", "方向清晰")
        ],
        CharacterArcType.ISOLATED_TO_CONNECTED: [
            ("孤独", "孤立", "没有朋友", "独行侠"),
            ("融入", "有伙伴", "团队", "归属")
        ],
    }
    
    # 人设标签类型
    TAG_PATTERNS = {
        "语言": [
            r"([\w]{1,2})说[道着]",  # XX说道
            r"['\"]([^'\"]{1,20})['\"].*?说",  # 带引号的对话
        ],
        "行为": [
            r"(?:喜欢|习惯|经常|总是)(\w{2,10})",  # 喜欢XX
            r"(?:一.+就.+)",  # 一XX就XX
        ],
        "习惯": [
            r"(?:每次|总是|习惯)(\w{2,10})",
            r"(?:必|一定|肯定)(\w{2,10})",
        ],
    }
    
    # 配角功能关键词
    SUPPORTING_ROLE_PATTERNS = {
        SupportingRoleFunction.TOOL_INFO: [
            "告诉", "消息", "情报", "信息", "听说", "据说", "透露",
            "知道", "了解", "清楚"
        ],
        SupportingRoleFunction.TOOL_RESOURCE: [
            "给", "送", "提供", "资源", "钱", "丹药", "法宝", "帮助",
            "支持", "资助"
        ],
        SupportingRoleFunction.TOOL_ESCAPE: [
            "救", "掩护", "撤退", "后路", "退路", "接应", "支援",
            "脱险", "逃生"
        ],
        SupportingRoleFunction.EMOTION_TRIGGER: [
            "激怒", "刺激", "感动", "心疼", "愤怒", "悲伤", "开心",
            "激动", "兴奋"
        ],
        SupportingRoleFunction.EMOTION_SACRIFICE: [
            "死", "牺牲", "保护", "挡", "为了", "付出", "代价",
            "生命", "舍命"
        ],
        SupportingRoleFunction.CONTRAST_FOIL: [
            "傲慢", "嚣张", "愚蠢", "聪明", "善良", "邪恶", "相反",
            "对比", "衬托"
        ],
        SupportingRoleFunction.CONFLICT_ANTAGONIST: [
            "敌人", "对手", "仇", "恨", "针对", "陷害", "阻挠",
            "破坏", "对抗"
        ],
    }
    
    def extract(self, text: str, chapters: List[Dict]) -> CharacterAnalysis:
        """
        提取人物特征
        
        Args:
            text: 全文文本
            chapters: 章节列表
        
        Returns:
            CharacterAnalysis: 人物分析
        """
        logger.info("character_extraction_started")
        
        # 1. 提取主角弧光
        protagonist_arc = self._extract_protagonist_arc(text, chapters)
        
        # 2. 提取人设记忆点
        protagonist_tags = self._extract_character_tags(text)
        
        # 3. 提取配角模板
        supporting_roles = self._extract_supporting_roles(text, chapters)
        
        # 4. 计算人物记忆度
        memorability = self._calculate_memorability(
            protagonist_arc, protagonist_tags, supporting_roles
        )
        
        analysis = CharacterAnalysis(
            protagonist_arc=protagonist_arc,
            protagonist_tags=protagonist_tags,
            supporting_roles=supporting_roles,
            character_memorability=round(memorability, 2),
        )
        
        logger.info(
            "character_extraction_completed",
            arc_type=protagonist_arc.arc_type.value,
            tags=len(protagonist_tags),
            supporting_roles=len(supporting_roles),
            memorability=memorability,
        )
        
        return analysis
    
    def _extract_protagonist_arc(self, text: str, chapters: List[Dict]) -> CharacterArc:
        """提取主角弧光"""
        # 1. 识别弧光类型
        arc_scores = {}
        
        for arc_type, (start_words, end_words) in self.ARC_KEYWORDS.items():
            # 计算前期出现的前期关键词
            early_text = " ".join(ch.get("content", "") for ch in chapters[:10])
            start_score = sum(early_text.count(w) for w in start_words)
            
            # 计算后期出现的后期关键词
            late_text = " ".join(ch.get("content", "") for ch in chapters[-10:])
            end_score = sum(late_text.count(w) for w in end_words)
            
            # 弧光强度 = 前期起点状态 + 后期终点状态
            arc_scores[arc_type] = start_score + end_score
        
        primary_arc = max(arc_scores.items(), key=lambda x: x[1])[0]
        
        # 2. 提取初始状态
        initial_state = self._extract_initial_state(text, primary_arc)
        
        # 3. 提取转折点
        turning_points = self._extract_turning_points(text, chapters, primary_arc)
        
        # 4. 提取最终状态
        final_state = self._extract_final_state(text, primary_arc)
        
        # 5. 计算完成度和满意度
        completion = self._calculate_completion(turning_points, len(chapters))
        satisfaction = self._predict_satisfaction(primary_arc, completion)
        
        return CharacterArc(
            arc_type=primary_arc,
            initial_state=initial_state,
            turning_points=turning_points,
            final_state=final_state,
            completion_degree=round(completion, 2),
            reader_satisfaction=round(satisfaction, 2),
        )
    
    def _extract_initial_state(self, text: str, arc_type: CharacterArcType) -> str:
        """提取初始状态"""
        state_map = {
            CharacterArcType.COWARD_TO_BRAVE: "胆小懦弱，遇事退缩",
            CharacterArcType.SELFISH_TO_ALTRUISTIC: "自私冷漠，只顾自己",
            CharacterArcType.NAIVE_TO_SCHEMING: "天真单纯，容易轻信",
            CharacterArcType.WEAK_TO_STRONG: "实力弱小，常被欺负",
            CharacterArcType.LOST_TO_PURPOSEFUL: "迷茫困惑，没有方向",
            CharacterArcType.ISOLATED_TO_CONNECTED: "孤独孤立，没有归属",
        }
        return state_map.get(arc_type, "普通状态")
    
    def _extract_final_state(self, text: str, arc_type: CharacterArcType) -> str:
        """提取最终状态"""
        state_map = {
            CharacterArcType.COWARD_TO_BRAVE: "勇敢坚强，挺身而出",
            CharacterArcType.SELFISH_TO_ALTRUISTIC: "无私奉献，心系他人",
            CharacterArcType.NAIVE_TO_SCHEMING: "深沉腹黑，善于算计",
            CharacterArcType.WEAK_TO_STRONG: "实力强大，无人敢欺",
            CharacterArcType.LOST_TO_PURPOSEFUL: "目标明确，坚定不移",
            CharacterArcType.ISOLATED_TO_CONNECTED: "融入集体，有归属感",
        }
        return state_map.get(arc_type, "成长后的状态")
    
    def _extract_turning_points(
        self,
        text: str,
        chapters: List[Dict],
        arc_type: CharacterArcType
    ) -> List[Tuple[int, str]]:
        """提取转折点"""
        turning_points = []
        
        # 转折点关键词
        turning_keywords = [
            "终于", "第一次", "意识到", "明白了", "决定", "改变",
            "从那以后", "转折点", "关键时刻", "顿悟", "觉醒"
        ]
        
        for chapter in chapters:
            ch_num = chapter.get("chapter_number", 0)
            ch_text = chapter.get("content", "")
            
            for keyword in turning_keywords:
                if keyword in ch_text:
                    # 提取包含关键词的句子
                    idx = ch_text.find(keyword)
                    start = max(0, idx - 20)
                    end = min(len(ch_text), idx + 30)
                    context = ch_text[start:end]
                    
                    turning_points.append((ch_num, context.strip()))
                    break  # 每章只取一个转折点
        
        # 限制数量，选择关键转折点
        if len(turning_points) > 5:
            # 均匀选择
            step = len(turning_points) // 5
            turning_points = turning_points[::step][:5]
        
        return turning_points
    
    def _calculate_completion(
        self,
        turning_points: List[Tuple[int, str]],
        total_chapters: int
    ) -> float:
        """计算弧光完成度"""
        if not turning_points:
            return 0.5
        
        # 基于转折点数量和分布计算
        base_completion = min(len(turning_points) / 5, 1.0)
        
        # 如果转折点分布到后期，完成度更高
        if turning_points:
            last_turning = max(tp[0] for tp in turning_points)
            coverage = last_turning / total_chapters if total_chapters > 0 else 0
            coverage_bonus = coverage * 0.2
        else:
            coverage_bonus = 0
        
        return min(base_completion + coverage_bonus, 1.0)
    
    def _predict_satisfaction(
        self,
        arc_type: CharacterArcType,
        completion: float
    ) -> float:
        """预测读者满意度"""
        # 某些弧光类型天然更受欢迎
        popular_arcs = [
            CharacterArcType.WEAK_TO_STRONG,
            CharacterArcType.COWARD_TO_BRAVE,
            CharacterArcType.NAIVE_TO_SCHEMING,
        ]
        
        base_satisfaction = 0.75 if arc_type in popular_arcs else 0.7
        
        # 完成度影响满意度
        completion_factor = completion * 0.25
        
        return min(base_satisfaction + completion_factor, 1.0)
    
    def _extract_character_tags(self, text: str) -> List[CharacterTag]:
        """提取人设记忆点"""
        tags = []
        
        # 1. 语言特征
        # 查找口头禅
        speech_patterns = re.findall(r"['\"][^'\"]*?(?:啧|哼|啊|呢|吧|吗)[^'\"]*?['\"]", text)
        if speech_patterns:
            tag = CharacterTag(
                tag_type="语言",
                tag_description=f"说话喜欢带语气词",
                frequency=len(speech_patterns),
                example_quotes=speech_patterns[:3],
            )
            tags.append(tag)
        
        # 2. 行为特征
        # 查找重复行为
        behavior_patterns = [
            ("摸鼻子", r"摸.{0,2}鼻子"),
            ("皱眉", r"皱.{0,2}眉"),
            ("冷笑", r"冷.{0,2}笑"),
            ("挑眉", r"挑.{0,2}眉"),
        ]
        
        for behavior_name, pattern in behavior_patterns:
            matches = re.findall(pattern, text)
            if len(matches) >= 3:
                tag = CharacterTag(
                    tag_type="行为",
                    tag_description=f"经常{behavior_name}",
                    frequency=len(matches),
                    example_quotes=[],
                )
                tags.append(tag)
        
        # 3. 习惯特征
        # 查找特定习惯
        habit_keywords = ["喝茶", "喝酒", "抽烟", "看书", "练剑", "打坐"]
        for habit in habit_keywords:
            count = text.count(habit)
            if count >= 5:
                tag = CharacterTag(
                    tag_type="习惯",
                    tag_description=f"有{habit}的习惯",
                    frequency=count,
                    example_quotes=[],
                )
                tags.append(tag)
        
        # 按频次排序
        tags.sort(key=lambda x: x.frequency, reverse=True)
        
        return tags[:5]  # 最多5个标签
    
    def _extract_supporting_roles(
        self,
        text: str,
        chapters: List[Dict]
    ) -> List[SupportingRoleTemplate]:
        """提取配角功能性模板"""
        roles = []
        
        # 识别人物（简化：基于称呼）
        # 实际应该用NER
        person_patterns = [
            r"(\w{2,4})(?:师兄|师弟|师姐|师妹|师父|徒弟|长老|掌门|家主|少爷|小姐)",
            r"(\w{2,4})(?:哥|姐|弟|妹|叔|姨|伯|爷)",
        ]
        
        persons = set()
        for pattern in person_patterns:
            matches = re.findall(pattern, text)
            persons.update(matches)
        
        # 分析每个人物的功能
        for person in list(persons)[:10]:  # 限制数量
            # 提取包含该人物的文本
            person_contexts = []
            for chapter in chapters:
                ch_text = chapter.get("content", "")
                if person in ch_text:
                    # 提取相关句子
                    sentences = ch_text.split("。")
                    for sent in sentences:
                        if person in sent:
                            person_contexts.append(sent)
            
            if not person_contexts:
                continue
            
            person_text = " ".join(person_contexts)
            
            # 判断功能类型
            function_scores = {}
            for func_type, keywords in self.SUPPORTING_ROLE_PATTERNS.items():
                score = sum(person_text.count(kw) for kw in keywords)
                function_scores[func_type] = score
            
            primary_function = max(function_scores.items(), key=lambda x: x[1])[0]
            
            # 计算可复用性
            reusability = self._calculate_role_reusability(primary_function)
            
            role = SupportingRoleTemplate(
                role_name=person,
                function_type=primary_function,
                role_description=self._describe_role(primary_function),
                relationship_to_protagonist=self._infer_relationship(person),
                plot_function=self._describe_plot_function(primary_function),
                reusability_score=round(reusability, 2),
            )
            roles.append(role)
        
        # 按可复用性排序
        roles.sort(key=lambda x: x.reusability_score, reverse=True)
        
        return roles[:5]
    
    def _calculate_role_reusability(self, function_type: SupportingRoleFunction) -> float:
        """计算角色模板可复用性"""
        # 某些功能类型更通用
        highly_reusable = [
            SupportingRoleFunction.TOOL_INFO,
            SupportingRoleFunction.CONFLICT_ANTAGONIST,
            SupportingRoleFunction.EMOTION_TRIGGER,
        ]
        
        if function_type in highly_reusable:
            return 0.85 + 0.1  # 基础分 + 通用加分
        else:
            return 0.75
    
    def _describe_role(self, function_type: SupportingRoleFunction) -> str:
        """描述角色"""
        descriptions = {
            SupportingRoleFunction.TOOL_INFO: "信息提供者，为主角提供关键情报",
            SupportingRoleFunction.TOOL_RESOURCE: "资源提供者，给予主角物资支持",
            SupportingRoleFunction.TOOL_ESCAPE: "退路提供者，在危机时刻救助主角",
            SupportingRoleFunction.EMOTION_TRIGGER: "情绪触发器，激发主角情感反应",
            SupportingRoleFunction.EMOTION_SACRIFICE: "牺牲型配角，为剧情提供虐点",
            SupportingRoleFunction.CONTRAST_FOIL: "对比衬托型，突出主角特质",
            SupportingRoleFunction.CONFLICT_ANTAGONIST: "冲突制造者，推动剧情发展",
        }
        return descriptions.get(function_type, "功能性配角")
    
    def _infer_relationship(self, person_name: str) -> str:
        """推断与主角关系"""
        # 基于称呼推断
        if any(t in person_name for t in ["师兄", "师姐", "师弟", "师妹"]):
            return "同门"
        elif any(t in person_name for t in ["师父", "师傅"]):
            return "师徒"
        elif any(t in person_name for t in ["哥", "姐", "弟", "妹"]):
            return "亲属"
        else:
            return "其他"
    
    def _describe_plot_function(self, function_type: SupportingRoleFunction) -> str:
        """描述剧情功能"""
        functions = {
            SupportingRoleFunction.TOOL_INFO: "推动信息线，提供剧情线索",
            SupportingRoleFunction.TOOL_RESOURCE: "解决资源困境，助力主角成长",
            SupportingRoleFunction.TOOL_ESCAPE: "制造安全网，增加剧情容错",
            SupportingRoleFunction.EMOTION_TRIGGER: "激发情感波动，增强代入感",
            SupportingRoleFunction.EMOTION_SACRIFICE: "制造情感高潮，深化主题",
            SupportingRoleFunction.CONTRAST_FOIL: "强化主角形象，突出特质",
            SupportingRoleFunction.CONFLICT_ANTAGONIST: "制造冲突，推动情节",
        }
        return functions.get(function_type, "辅助剧情")
    
    def _calculate_memorability(
        self,
        protagonist_arc: CharacterArc,
        protagonist_tags: List[CharacterTag],
        supporting_roles: List[SupportingRoleTemplate],
    ) -> float:
        """计算人物记忆度"""
        base_score = 0.6
        
        # 弧光清晰度加分
        arc_bonus = protagonist_arc.completion_degree * 0.15
        
        # 人设标签加分
        tag_bonus = min(len(protagonist_tags) * 0.03, 0.15)
        
        # 配角丰富度加分
        role_bonus = min(len(supporting_roles) * 0.02, 0.1)
        
        return min(base_score + arc_bonus + tag_bonus + role_bonus, 1.0)
