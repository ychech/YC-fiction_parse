"""
MOBI 格式解析器
"""
from io import BytesIO

from src.common.logger import get_logger
from src.processing_layer.parsers.base import BaseParser, ChapterInfo, ParseResult

logger = get_logger(__name__)


class MobiParser(BaseParser):
    """MOBI/AZW3 小说解析器"""
    
    async def parse(self, file_data: bytes) -> ParseResult:
        """解析 MOBI 文件"""
        logger.info("mobi_parsing_started", size=len(file_data))
        
        # MOBI 格式较复杂，这里使用简化实现
        # 实际项目中可以使用 mobi 或 kindlelib 库
        
        try:
            # 尝试使用 mobi 库
            import mobi
            temp_path = "/tmp/temp.mobi"
            with open(temp_path, "wb") as f:
                f.write(file_data)
            
            # 解压 MOBI
            opf_path, _ = mobi.extract(temp_path)
            
            # 读取内容
            # 这里简化处理，实际应该解析 OPF 和 HTML 文件
            text = self._read_extracted_content(opf_path)
            
        except ImportError:
            logger.warning("mobi_library_not_found, using_fallback")
            # 回退：尝试作为文本读取
            text = self._fallback_parse(file_data)
        except Exception as e:
            logger.error("mobi_parse_error", error=str(e))
            text = self._fallback_parse(file_data)
        
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
                "format": "mobi",
                "chapter_count": len(chapters),
                "core_chapter_count": sum(1 for ch in chapters if ch.is_core),
                **metadata
            }
        )
        
        logger.info(
            "mobi_parsing_completed",
            chapters=len(chapters),
            word_count=total_word_count
        )
        
        return result
    
    def _read_extracted_content(self, opf_path: str) -> str:
        """读取解压后的内容"""
        import os
        import re
        
        text_parts = []
        
        # 查找 HTML 文件
        for root, dirs, files in os.walk(opf_path):
            for file in sorted(files):
                if file.endswith(".html") or file.endswith(".htm"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # 移除 HTML 标签
                            text = re.sub(r"<[^>]+>", "", content)
                            text_parts.append(text)
                    except Exception:
                        pass
        
        return "\n\n".join(text_parts)
    
    def _fallback_parse(self, file_data: bytes) -> str:
        """
        回退解析方法
        尝试从 MOBI 二进制数据中提取文本
        """
        # MOBI 文件头包含文本偏移信息
        # 这里做简化处理
        
        # 尝试多种编码解码
        for encoding in ["utf-8", "gb18030", "gbk", "latin-1"]:
            try:
                text = file_data.decode(encoding)
                # 提取可打印字符
                import re
                text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s\n\r\p{P}]", "", text)
                if len(text) > 1000:  # 至少有一些文本
                    return text
            except:
                continue
        
        # 最后的回退：提取所有中文字符
        import re
        chinese_chars = re.findall(r"[\u4e00-\u9fa5]+", file_data.decode("latin-1", errors="ignore"))
        return "\n".join(chinese_chars)
