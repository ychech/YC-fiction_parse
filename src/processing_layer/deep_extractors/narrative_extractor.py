"""
叙事节奏与写作技法解析引擎
拆解"可复制的写作技巧"
"""
import re
from typing import Dict, List, Tuple

from src.common.deep_schemas import (
    ChapterStructureTemplate,
    InformationRelease,
    LanguageStyleFeatures,
    NarrativeTechnique,
)
from src.common.logger import get_logger

logger = get_logger(__name__)


class NarrativeExtractor:
    """叙事技法解析器"""
    
    def extract(self, text: str, chapters: List[Dict]) -> NarrativeTechnique:
        """
        提取叙事技法
        
        Args:
            text: 全文文本
            chapters: 章节列表
        
        Returns:
            NarrativeTechnique: 叙事技法
        """
        logger.info("narrative_extraction_started")
        
        # 1. 分析章节结构模板
        chapter_template = self._analyze_chapter_structure(chapters)
        
        # 2. 分析信息释放节奏
        info_releases = self._analyze_info_releases(text, chapters)
        
        # 3. 分析语言风格
        language_style = self._analyze_language_style(text, chapters)
        
        # 4. 确定适用场景和难度
        applicable_scenarios = self._determine_applicable_scenarios(chapter_template, language_style)
        technique_difficulty = self._calculate_technique_difficulty(chapter_template, info_releases)
        
        technique = NarrativeTechnique(
            chapter_template=chapter_template,
            info_releases=info_releases,
            language_style=language_style,
            applicable_scenarios=applicable_scenarios,
            technique_difficulty=technique_difficulty,
        )
        
        logger.info(
            "narrative_extraction_completed",
            hook_ratio=chapter_template.hook_ratio,
            short_sentence_ratio=language_style.short_sentence_ratio,
            difficulty=technique_difficulty,
        )
        
        return technique
    
    def _analyze_chapter_structure(self, chapters: List[Dict]) -> ChapterStructureTemplate:
        """分析章节结构模板"""
        if not chapters:
            return ChapterStructureTemplate(
                template_name="标准模板",
                hook_ratio=0.1,
                development_ratio=0.7,
                cliffhanger_ratio=0.2,
                avg_paragraph_length=200,
                dialogue_ratio=0.3,
            )
        
        # 分析每章结构
        hook_ratios = []
        development_ratios = []
        cliffhanger_ratios = []
        paragraph_lengths = []
        dialogue_ratios = []
        
        for chapter in chapters:
            ch_text = chapter.get("content", "")
            if not ch_text:
                continue
            
            # 分割段落
            paragraphs = [p.strip() for p in ch_text.split("\n") if p.strip()]
            if not paragraphs:
                continue
            
            # 计算段落长度
            para_lengths = [len(p) for p in paragraphs]
            paragraph_lengths.extend(para_lengths)
            
            # 分析章节结构
            total_len = len(ch_text)
            
            # 开头钩子（前10%）
            hook_len = int(total_len * 0.1)
            hook_text = ch_text[:hook_len]
            
            # 中间推进（中间70%）
            dev_start = hook_len
            dev_end = int(total_len * 0.9)
            dev_text = ch_text[dev_start:dev_end]
            
            # 结尾留钩（后20%）
            cliff_text = ch_text[dev_end:]
            
            # 计算各部分占比
            hook_ratios.append(0.1)
            development_ratios.append(0.8)
            cliffhanger_ratios.append(0.1)
            
            # 计算对话占比
            dialogue_pattern = r"['\"].*?['\"]"
            dialogues = re.findall(dialogue_pattern, ch_text)
            dialogue_len = sum(len(d) for d in dialogues)
            dialogue_ratio = dialogue_len / total_len if total_len > 0 else 0
            dialogue_ratios.append(dialogue_ratio)
        
        # 计算平均值
        avg_hook_ratio = sum(hook_ratios) / len(hook_ratios) if hook_ratios else 0.1
        avg_dev_ratio = sum(development_ratios) / len(development_ratios) if development_ratios else 0.7
        avg_cliff_ratio = sum(cliffhanger_ratios) / len(cliffhanger_ratios) if cliffhanger_ratios else 0.2
        avg_para_length = sum(paragraph_lengths) / len(paragraph_lengths) if paragraph_lengths else 200
        avg_dialogue_ratio = sum(dialogue_ratios) / len(dialogue_ratios) if dialogue_ratios else 0.3
        
        return ChapterStructureTemplate(
            template_name="分析模板",
            hook_ratio=round(avg_hook_ratio, 2),
            development_ratio=round(avg_dev_ratio, 2),
            cliffhanger_ratio=round(avg_cliff_ratio, 2),
            avg_paragraph_length=int(avg_para_length),
            dialogue_ratio=round(avg_dialogue_ratio, 2),
        )
    
    def _analyze_info_releases(self, text: str, chapters: List[Dict]) -> List[InformationRelease]:
        """分析信息释放节奏"""
        releases = []
        
        # 信息类型关键词
        info_types = {
            "世界观": ["世界", "大陆", "帝国", "宗门", "势力", "规则", "法则"],
            "人物背景": ["身世", "来历", "过去", "经历", "背景", "家族", "身份"],
            "剧情伏笔": ["秘密", "真相", "阴谋", "计划", "目的", "幕后"],
        }
        
        for info_type, keywords in info_types.items():
            release_chapters = []
            release_methods = []
            
            for chapter in chapters:
                ch_num = chapter.get("chapter_number", 0)
                ch_text = chapter.get("content", "")
                
                for keyword in keywords:
                    if keyword in ch_text:
                        release_chapters.append(ch_num)
                        
                        # 判断释放方式
                        if any(w in ch_text for w in ["告诉", "说", "解释", "介绍"]):
                            release_methods.append("主动告知")
                        elif any(w in ch_text for w in ["暗示", "透露", "隐约", "似乎"]):
                            release_methods.append("侧面暗示")
                        else:
                            release_methods.append("探索发现")
                        
                        break
            
            if release_chapters:
                # 计算留白比例
                total_chapters = len(chapters)
                revealed_chapters = len(set(release_chapters))
                mystery_ratio = 1 - (revealed_chapters / total_chapters) if total_chapters > 0 else 0.5
                
                # 取最常见的释放方式
                from collections import Counter
                method_counter = Counter(release_methods)
                primary_method = method_counter.most_common(1)[0][0]
                
                release = InformationRelease(
                    info_type=info_type,
                    release_method=primary_method,
                    release_chapters=sorted(set(release_chapters)),
                    mystery_ratio=round(mystery_ratio, 2),
                )
                releases.append(release)
        
        return releases
    
    def _analyze_language_style(self, text: str, chapters: List[Dict]) -> LanguageStyleFeatures:
        """分析语言风格"""
        # 分割句子
        sentences = re.split(r"[。！？；]", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return LanguageStyleFeatures(
                short_sentence_ratio=0.3,
                long_sentence_ratio=0.2,
                avg_sentence_length=15,
                perspective_switches=0,
                primary_perspective="第三人称",
                sensory_distribution={},
                rhythm_score=0.5,
            )
        
        # 计算句式特征
        short_sentences = [s for s in sentences if len(s) < 10]
        long_sentences = [s for s in sentences if len(s) > 30]
        
        short_ratio = len(short_sentences) / len(sentences)
        long_ratio = len(long_sentences) / len(sentences)
        avg_length = sum(len(s) for s in sentences) / len(sentences)
        
        # 分析视角
        perspective_switches, primary_perspective = self._analyze_perspective(text)
        
        # 分析感官描写
        sensory_dist = self._analyze_sensory_distribution(text)
        
        # 计算节奏感
        rhythm_score = self._calculate_rhythm_score(
            short_ratio, long_ratio, perspective_switches
        )
        
        return LanguageStyleFeatures(
            short_sentence_ratio=round(short_ratio, 2),
            long_sentence_ratio=round(long_ratio, 2),
            avg_sentence_length=round(avg_length, 1),
            perspective_switches=perspective_switches,
            primary_perspective=primary_perspective,
            sensory_distribution=sensory_dist,
            rhythm_score=round(rhythm_score, 2),
        )
    
    def _analyze_perspective(self, text: str) -> Tuple[int, str]:
        """分析视角"""
        # 第一人称标记
        first_person = len(re.findall(r"我|俺|咱|本人", text))
        # 第三人称标记
        third_person = len(re.findall(r"他|她|它|主角|男主|女主", text))
        
        if first_person > third_person * 2:
            return 0, "第一人称"
        elif third_person > first_person * 2:
            return 0, "第三人称"
        else:
            # 计算切换次数
            switches = len(re.findall(r"我.*?(?:他|她)|(?:他|她).*?我", text[:10000]))
            return switches, "多视角" if switches > 5 else "第三人称"
    
    def _analyze_sensory_distribution(self, text: str) -> Dict[str, float]:
        """分析感官描写分布"""
        sensory_keywords = {
            "视觉": ["看", "见", "望", "视", "颜色", "光", "影", "形", "貌"],
            "听觉": ["听", "闻", "声", "音", "响", "叫", "喊", "说"],
            "触觉": ["摸", "触", "感", "温度", "冷", "热", "痛", "软", "硬"],
            "嗅觉": ["闻", "香", "臭", "味", "气", "嗅"],
            "味觉": ["吃", "尝", "甜", "苦", "辣", "酸", "咸", "鲜"],
        }
        
        sensory_counts = {}
        total_sensory = 0
        
        for sense, keywords in sensory_keywords.items():
            count = sum(text.count(kw) for kw in keywords)
            sensory_counts[sense] = count
            total_sensory += count
        
        # 转换为比例
        if total_sensory > 0:
            sensory_dist = {
                sense: round(count / total_sensory, 2)
                for sense, count in sensory_counts.items()
            }
        else:
            sensory_dist = {sense: 0.2 for sense in sensory_keywords.keys()}
        
        return sensory_dist
    
    def _calculate_rhythm_score(
        self,
        short_ratio: float,
        long_ratio: float,
        perspective_switches: int
    ) -> float:
        """计算节奏感评分"""
        # 短句多 = 节奏快
        base_score = 0.5 + (short_ratio - 0.3) * 0.5
        
        # 视角切换多 = 节奏变化多
        switch_penalty = min(perspective_switches * 0.02, 0.1)
        
        return min(max(base_score - switch_penalty, 0), 1)
    
    def _determine_applicable_scenarios(
        self,
        chapter_template: ChapterStructureTemplate,
        language_style: LanguageStyleFeatures,
    ) -> List[str]:
        """确定适用场景"""
        scenarios = []
        
        # 基于章节结构判断
        if chapter_template.hook_ratio > 0.15:
            scenarios.append("快节奏爽文")
        else:
            scenarios.append("慢热型作品")
        
        # 基于对话占比判断
        if chapter_template.dialogue_ratio > 0.4:
            scenarios.append("对话驱动型")
        else:
            scenarios.append("叙述驱动型")
        
        # 基于句式判断
        if language_style.short_sentence_ratio > 0.4:
            scenarios.append("快节奏战斗场景")
        if language_style.long_sentence_ratio > 0.3:
            scenarios.append("氛围渲染场景")
        
        return scenarios
    
    def _calculate_technique_difficulty(
        self,
        chapter_template: ChapterStructureTemplate,
        info_releases: List[InformationRelease],
    ) -> int:
        """计算技法难度"""
        difficulty = 3  # 基础难度
        
        # 章节结构复杂度
        if abs(chapter_template.hook_ratio - 0.1) > 0.05:
            difficulty += 1  # 非标准结构
        
        # 信息释放复杂度
        if len(info_releases) > 2:
            difficulty += 1
        
        # 留白比例
        avg_mystery = sum(r.mystery_ratio for r in info_releases) / len(info_releases) if info_releases else 0
        if avg_mystery > 0.6:
            difficulty += 1
        
        return min(difficulty, 5)
