"""
EPUB 格式解析器
"""
from io import BytesIO

from src.common.logger import get_logger
from src.processing_layer.parsers.base import BaseParser, ChapterInfo, ParseResult

logger = get_logger(__name__)


class EpubParser(BaseParser):
    """EPUB 小说解析器"""
    
    async def parse(self, file_data: bytes) -> ParseResult:
        """解析 EPUB 文件"""
        logger.info("epub_parsing_started", size=len(file_data))
        
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("ebooklib and beautifulsoup4 are required for EPUB parsing")
        
        # 读取 EPUB
        book = epub.read_epub(BytesIO(file_data))
        
        # 提取元数据
        metadata = self._extract_metadata(book)
        
        # 提取章节
        chapters = []
        chapter_num = 0
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # 解析 HTML
                soup = BeautifulSoup(item.get_content(), "html.parser")
                
                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # 提取文本
                text = soup.get_text()
                text = self.clean_text(text)
                
                if len(text) > 100:  # 过滤过短的页面
                    chapter_num += 1
                    
                    # 尝试提取标题
                    title = None
                    title_tag = soup.find(["h1", "h2", "h3", "title"])
                    if title_tag:
                        title = title_tag.get_text().strip()
                    
                    chapters.append(ChapterInfo(
                        chapter_number=chapter_num,
                        title=title,
                        content=text,
                        word_count=len(text)
                    ))
        
        # 如果没有提取到章节，尝试按章节分割
        if not chapters:
            all_text = "\n\n".join(ch.content for ch in chapters)
            chapters = self.split_chapters(all_text)
        
        # 识别核心章节
        chapters = self.identify_core_chapters(chapters)
        
        # 计算总字数
        total_word_count = sum(ch.word_count for ch in chapters)
        
        result = ParseResult(
            title=metadata.get("title"),
            author=metadata.get("author"),
            description=metadata.get("description"),
            chapters=chapters,
            total_word_count=total_word_count,
            metadata={
                "format": "epub",
                "chapter_count": len(chapters),
                "core_chapter_count": sum(1 for ch in chapters if ch.is_core),
                **metadata
            }
        )
        
        logger.info(
            "epub_parsing_completed",
            chapters=len(chapters),
            word_count=total_word_count
        )
        
        return result
    
    def _extract_metadata(self, book) -> dict:
        """从 EPUB 提取元数据"""
        metadata = {}
        
        # 书名
        titles = book.get_metadata("DC", "title")
        if titles:
            metadata["title"] = titles[0][0]
        
        # 作者
        creators = book.get_metadata("DC", "creator")
        if creators:
            metadata["author"] = creators[0][0]
        
        # 描述
        descriptions = book.get_metadata("DC", "description")
        if descriptions:
            metadata["description"] = descriptions[0][0]
        
        # 语言
        languages = book.get_metadata("DC", "language")
        if languages:
            metadata["language"] = languages[0][0]
        
        # 出版日期
        dates = book.get_metadata("DC", "date")
        if dates:
            metadata["date"] = dates[0][0]
        
        return metadata
