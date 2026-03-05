"""
TXT 格式解析器
"""
from src.common.logger import get_logger
from src.processing_layer.parsers.base import BaseParser, ChapterInfo, ParseResult

logger = get_logger(__name__)


class TxtParser(BaseParser):
    """TXT 小说解析器"""
    
    async def parse(self, file_data: bytes) -> ParseResult:
        """解析 TXT 文件"""
        logger.info("txt_parsing_started", size=len(file_data))
        
        # 检测编码
        encoding = self.detect_encoding(file_data)
        logger.debug("encoding_detected", encoding=encoding)
        
        # 解码文本
        try:
            text = file_data.decode(encoding)
        except UnicodeDecodeError:
            # 尝试其他编码
            for enc in ["utf-8", "gb18030", "gbk", "gb2312", "big5"]:
                try:
                    text = file_data.decode(enc)
                    logger.debug("fallback_encoding_used", encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Unable to decode file with any encoding")
        
        # 清洗文本
        text = self.clean_text(text)
        
        # 提取元数据
        metadata = self.extract_metadata(text)
        
        # 分割章节
        chapters = self.split_chapters(text)
        
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
                "encoding": encoding,
                "chapter_count": len(chapters),
                "core_chapter_count": sum(1 for ch in chapters if ch.is_core),
                **metadata
            }
        )
        
        logger.info(
            "txt_parsing_completed",
            chapters=len(chapters),
            word_count=total_word_count
        )
        
        return result
