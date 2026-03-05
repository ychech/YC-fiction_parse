"""
解析器基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ChapterInfo:
    """章节信息"""
    chapter_number: int
    title: Optional[str] = None
    content: str = ""
    word_count: int = 0
    is_core: bool = False  # 是否核心章节


@dataclass
class ParseResult:
    """解析结果"""
    title: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    chapters: List[ChapterInfo] = field(default_factory=list)
    total_word_count: int = 0
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    """基础解析器"""
    
    # 章节标题正则模式
    CHAPTER_PATTERNS = [
        r"第[一二三四五六七八九十百千零\d]+章[\s:：]",  # 第X章
        r"第[\d]+章[\s:：]",  # 第1章
        r"Chapter[\s]*[\d]+",  # Chapter 1
        r"^[\d]+[\s:：]",  # 1. 或 1：
        r"^[\(（]?[\d]+[\)）]?[\s:：]",  # (1) 或（1）
    ]
    
    # 需要过滤的广告/无关文本
    JUNK_PATTERNS = [
        r"本书由.+整理",
        r"VIP章节请订阅",
        r"正版订阅在阅文",
        r"起点中文网",
        r"QQ阅读",
        r"手机用户请到.+阅读",
        r"请记住本书首发域名",
        r"笔趣阁",
        r"小说网",
        r"www\..+\.com",
    ]
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式"""
        import re
        self.chapter_regexes = [re.compile(p, re.IGNORECASE) for p in self.CHAPTER_PATTERNS]
        self.junk_regex = re.compile("|".join(self.JUNK_PATTERNS), re.IGNORECASE)
    
    @abstractmethod
    async def parse(self, file_data: bytes) -> ParseResult:
        """解析文件数据"""
        pass
    
    def detect_encoding(self, data: bytes) -> str:
        """检测文本编码"""
        import chardet
        
        result = chardet.detect(data)
        encoding = result.get("encoding", "utf-8")
        
        # 处理常见编码别名
        if encoding.lower() in ["gb2312", "gbk", "gb18030"]:
            return "gb18030"
        
        return encoding or "utf-8"
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        import re
        
        # 移除广告文本
        text = self.junk_regex.sub("", text)
        
        # 规范化空白字符
        text = re.sub(r"\r\n", "\n", text)  # 统一换行符
        text = re.sub(r"[ \t]+", " ", text)  # 合并空格
        text = re.sub(r"\n{3,}", "\n\n", text)  # 合并多余空行
        
        # 移除特殊控制字符
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f]", "", text)
        
        return text.strip()
    
    def split_chapters(self, text: str) -> List[ChapterInfo]:
        """
        按章节分割文本
        使用多种策略识别章节边界
        """
        import re
        
        chapters = []
        lines = text.split("\n")
        
        current_chapter = None
        current_content = []
        chapter_num = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是章节标题
            is_chapter_title = False
            chapter_title = None
            
            for regex in self.chapter_regexes:
                match = regex.match(line)
                if match:
                    is_chapter_title = True
                    chapter_title = line
                    break
            
            if is_chapter_title:
                # 保存前一章节
                if current_chapter is not None and current_content:
                    content = "\n".join(current_content)
                    current_chapter.content = content
                    current_chapter.word_count = len(content)
                    chapters.append(current_chapter)
                
                # 开始新章节
                chapter_num += 1
                current_chapter = ChapterInfo(
                    chapter_number=chapter_num,
                    title=chapter_title
                )
                current_content = []
            else:
                if current_chapter is not None:
                    current_content.append(line)
        
        # 保存最后一章
        if current_chapter is not None and current_content:
            content = "\n".join(current_content)
            current_chapter.content = content
            current_chapter.word_count = len(content)
            chapters.append(current_chapter)
        
        # 如果没有识别到章节，将整个文本作为一章
        if not chapters:
            chapters.append(ChapterInfo(
                chapter_number=1,
                title=None,
                content=text,
                word_count=len(text)
            ))
        
        return chapters
    
    def identify_core_chapters(self, chapters: List[ChapterInfo]) -> List[ChapterInfo]:
        """
        识别核心章节
        策略：前10章 + 中间章节 + 最后5章
        """
        if len(chapters) <= 20:
            # 短小说，全部标记为核心
            for ch in chapters:
                ch.is_core = True
            return chapters
        
        total = len(chapters)
        
        # 前10章
        for i in range(min(10, total)):
            chapters[i].is_core = True
        
        # 中间章节（每10章取1章）
        for i in range(10, total - 5, 10):
            if i < total:
                chapters[i].is_core = True
        
        # 最后5章
        for i in range(max(0, total - 5), total):
            chapters[i].is_core = True
        
        return chapters
    
    def extract_metadata(self, text: str) -> dict:
        """从文本中提取元数据"""
        import re
        
        metadata = {}
        lines = text.split("\n")[:50]  # 只检查前50行
        
        for line in lines:
            line = line.strip()
            
            # 书名
            if not metadata.get("title"):
                match = re.search(r"[书书名稱][:：\s]*(.+)", line)
                if match:
                    metadata["title"] = match.group(1).strip()
            
            # 作者
            if not metadata.get("author"):
                match = re.search(r"[作者著][:：\s]*(.+)", line)
                if match:
                    metadata["author"] = match.group(1).strip()
            
            # 简介
            if not metadata.get("description"):
                match = re.search(r"[简介介紹][:：\s]*(.+)", line)
                if match:
                    metadata["description"] = match.group(1).strip()
        
        return metadata
