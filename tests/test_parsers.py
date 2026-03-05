"""
解析器单元测试
"""
import pytest

from src.processing_layer.parsers import get_parser
from src.processing_layer.parsers.base import ChapterInfo, ParseResult
from src.processing_layer.parsers.txt_parser import TxtParser


class TestTxtParser:
    """TXT 解析器测试"""
    
    @pytest.fixture
    def parser(self):
        return TxtParser()
    
    @pytest.fixture
    def sample_novel(self):
        """示例小说文本"""
        return """
书名：测试修仙小说
作者：测试作者

简介：这是一个测试用的修仙小说

第一章 初入仙门

这是一个修仙的世界。

主角张三从一个小村庄出发，踏上了修仙之路。

第二章 突破境界

经过努力修炼，张三终于突破了炼气期。

第三章 宗门大比

宗门大比开始了，张三展现出惊人的实力。
"""
    
    def test_detect_encoding(self, parser):
        """测试编码检测"""
        # UTF-8 编码
        text = "测试文本".encode("utf-8")
        encoding = parser.detect_encoding(text)
        assert encoding in ["utf-8", "utf-8-sig"]
        
        # GBK 编码
        text = "测试文本".encode("gbk")
        encoding = parser.detect_encoding(text)
        assert encoding == "gb18030"
    
    def test_clean_text(self, parser):
        """测试文本清洗"""
        dirty_text = """
        本书由XXX整理
        
        正文内容
        
        VIP章节请订阅
        """
        
        cleaned = parser.clean_text(dirty_text)
        assert "本书由XXX整理" not in cleaned
        assert "VIP章节请订阅" not in cleaned
        assert "正文内容" in cleaned
    
    def test_split_chapters(self, parser, sample_novel):
        """测试章节分割"""
        chapters = parser.split_chapters(sample_novel)
        
        assert len(chapters) >= 3
        assert chapters[0].chapter_number == 1
        assert "第一章" in (chapters[0].title or "")
    
    def test_identify_core_chapters(self, parser):
        """测试核心章节识别"""
        chapters = [
            ChapterInfo(chapter_number=i, content=f"第{i}章内容")
            for i in range(1, 31)
        ]
        
        result = parser.identify_core_chapters(chapters)
        
        # 前10章应该是核心
        assert all(ch.is_core for ch in result[:10])
        # 最后5章应该是核心
        assert all(ch.is_core for ch in result[-5:])
    
    def test_extract_metadata(self, parser, sample_novel):
        """测试元数据提取"""
        metadata = parser.extract_metadata(sample_novel)
        
        assert metadata.get("title") == "测试修仙小说"
        assert metadata.get("author") == "测试作者"
    
    @pytest.mark.asyncio
    async def test_parse(self, parser, sample_novel):
        """测试完整解析流程"""
        file_data = sample_novel.encode("utf-8")
        result = await parser.parse(file_data)
        
        assert isinstance(result, ParseResult)
        assert result.title == "测试修仙小说"
        assert result.author == "测试作者"
        assert len(result.chapters) >= 3
        assert result.total_word_count > 0


class TestParserFactory:
    """解析器工厂测试"""
    
    def test_get_txt_parser(self):
        parser = get_parser("txt")
        assert isinstance(parser, TxtParser)
    
    def test_get_parser_case_insensitive(self):
        parser1 = get_parser("TXT")
        parser2 = get_parser("Txt")
        assert type(parser1) == type(parser2)
    
    def test_get_parser_invalid_format(self):
        with pytest.raises(ValueError):
            get_parser("pdf")
