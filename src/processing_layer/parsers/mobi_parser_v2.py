"""
MOBI/AZW3 解析器 v2 - 完整实现
支持 MOBI、AZW、AZW3 格式
"""
import struct
from io import BytesIO
from typing import List, Optional, Tuple

from src.common.logger import get_logger
from src.processing_layer.parsers.base import BaseParser, ChapterInfo, ParseResult

logger = get_logger(__name__)


class MobiParserV2(BaseParser):
    """
    MOBI/AZW3 解析器 v2
    
    特性：
    - 支持 MOBI、AZW、AZW3 格式
    - 解析 PalmDOC 头
    - 解析 MOBI 头
    - 处理 EXTH 头（元数据）
    - 支持文本解压
    """
    
    # PalmDOC 压缩类型
    COMPRESSION_NONE = 1
    COMPRESSION_PALMDOC = 2
    COMPRESSION_HUFF = 17480
    
    # MOBI 魔数
    MOBI_MAGIC = b'MOBI'
    EXTH_MAGIC = b'EXTH'
    
    def __init__(self):
        super().__init__()
        self.raw_text: bytes = b''
        self.encoding: str = 'utf-8'
        self.full_name: str = ''
        
    async def parse(self, file_data: bytes) -> ParseResult:
        """解析 MOBI 文件"""
        logger.info("mobi_v2_parsing_started", size=len(file_data))
        
        try:
            # 解析 PalmDOC 头
            palmdoc_header = self._parse_palmdoc_header(file_data[:78])
            
            # 解析 MOBI 头
            mobi_header, mobi_header_offset = self._parse_mobi_header(file_data)
            
            # 解析 EXTH 头（元数据）
            exth_data = self._parse_exth_header(file_data, mobi_header_offset)
            
            # 解压文本
            self.raw_text = self._decompress_text(file_data, palmdoc_header)
            
            # 检测编码
            self.encoding = self._detect_encoding(mobi_header, exth_data)
            
            # 解码文本
            try:
                text = self.raw_text.decode(self.encoding, errors='ignore')
            except:
                text = self.raw_text.decode('utf-8', errors='ignore')
            
            # 清洗文本
            text = self.clean_text(text)
            
            # 提取元数据
            metadata = self._extract_metadata(exth_data, mobi_header)
            
            # 分割章节
            chapters = self._split_chapters(text, palmdoc_header)
            
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
                    "encoding": self.encoding,
                    "compression": palmdoc_header.get('compression'),
                    "mobi_version": mobi_header.get('version'),
                    "chapter_count": len(chapters),
                    "core_chapter_count": sum(1 for ch in chapters if ch.is_core),
                    **metadata
                }
            )
            
            logger.info(
                "mobi_v2_parsing_completed",
                chapters=len(chapters),
                word_count=total_word_count,
                title=result.title
            )
            
            return result
            
        except Exception as e:
            logger.error("mobi_v2_parsing_failed", error=str(e))
            # 回退到简单解析
            return await self._fallback_parse(file_data)
    
    def _parse_palmdoc_header(self, header_data: bytes) -> dict:
        """解析 PalmDOC 头"""
        if len(header_data) < 78:
            raise ValueError("Invalid PalmDOC header")
        
        header = struct.unpack('>HHIHHHHHHIIHH', header_data[:78])
        
        return {
            'compression': header[0],
            'unused': header[1],
            'text_length': header[2],
            'record_count': header[3],
            'record_size': header[4],
            'encryption_type': header[5],
            'unknown': header[6],
        }
    
    def _parse_mobi_header(self, data: bytes) -> Tuple[dict, int]:
        """解析 MOBI 头"""
        # 查找 MOBI 魔数
        mobi_offset = data.find(self.MOBI_MAGIC)
        if mobi_offset == -1:
            return {}, 0
        
        try:
            # 解析 MOBI 头
            header_data = data[mobi_offset:mobi_offset + 232]
            
            # 基础字段
            magic = header_data[0:4]
            header_length = struct.unpack('>I', header_data[4:8])[0]
            mobi_type = struct.unpack('>I', header_data[8:12])[0]
            text_encoding = struct.unpack('>I', header_data[12:16])[0]
            
            # 查找 full name
            full_name_offset = struct.unpack('>I', header_data[84:88])[0]
            full_name_length = struct.unpack('>I', header_data[88:92])[0]
            
            full_name = ''
            if full_name_offset > 0 and full_name_length > 0:
                name_start = mobi_offset + full_name_offset
                name_end = name_start + full_name_length
                full_name = data[name_start:name_end].decode('utf-8', errors='ignore')
            
            return {
                'magic': magic,
                'header_length': header_length,
                'type': mobi_type,
                'text_encoding': text_encoding,
                'full_name': full_name,
                'version': struct.unpack('>I', header_data[36:40])[0] if len(header_data) > 40 else 0,
            }, mobi_offset
            
        except Exception as e:
            logger.warning("mobi_header_parse_failed", error=str(e))
            return {}, 0
    
    def _parse_exth_header(self, data: bytes, mobi_offset: int) -> dict:
        """解析 EXTH 头（扩展元数据）"""
        exth_data = {}
        
        # 查找 EXTH 魔数
        exth_offset = data.find(self.EXTH_MAGIC, mobi_offset)
        if exth_offset == -1:
            return exth_data
        
        try:
            # 解析 EXTH 头
            header_data = data[exth_offset:exth_offset + 12]
            magic = header_data[0:4]
            header_length = struct.unpack('>I', header_data[4:8])[0]
            record_count = struct.unpack('>I', header_data[8:12])[0]
            
            # 解析记录
            offset = exth_offset + 12
            for _ in range(record_count):
                if offset + 8 > len(data):
                    break
                
                record_type = struct.unpack('>I', data[offset:offset+4])[0]
                record_length = struct.unpack('>I', data[offset+4:offset+8])[0]
                
                if record_length > 8:
                    record_data = data[offset+8:offset+record_length]
                    exth_data[record_type] = record_data.decode('utf-8', errors='ignore')
                
                offset += record_length
        
        except Exception as e:
            logger.warning("exth_header_parse_failed", error=str(e))
        
        return exth_data
    
    def _decompress_text(self, data: bytes, palmdoc_header: dict) -> bytes:
        """解压文本"""
        compression = palmdoc_header.get('compression', self.COMPRESSION_PALMDOC)
        
        if compression == self.COMPRESSION_NONE:
            # 无压缩
            return self._extract_text_records(data, palmdoc_header)
        
        elif compression == self.COMPRESSION_PALMDOC:
            # PalmDOC 压缩
            compressed = self._extract_text_records(data, palmdoc_header)
            return self._decompress_palmdoc(compressed)
        
        elif compression == self.COMPRESSION_HUFF:
            # Huff 压缩 (较少见)
            logger.warning("huff_compression_not_supported")
            return self._extract_text_records(data, palmdoc_header)
        
        else:
            logger.warning("unknown_compression_type", compression=compression)
            return self._extract_text_records(data, palmdoc_header)
    
    def _extract_text_records(self, data: bytes, palmdoc_header: dict) -> bytes:
        """提取文本记录"""
        record_count = palmdoc_header.get('record_count', 0)
        
        # 记录表从偏移 78 开始
        record_table_offset = 78
        records = []
        
        for i in range(record_count):
            offset = record_table_offset + i * 8
            if offset + 8 > len(data):
                break
            
            record_offset = struct.unpack('>I', data[offset:offset+4])[0]
            records.append(record_offset)
        
        # 添加文件长度作为最后一个记录的结束
        records.append(len(data))
        
        # 提取文本记录（通常前几个记录是文本）
        text_parts = []
        first_text_record = 1  # 通常第一个记录是元数据
        
        for i in range(first_text_record, min(len(records)-1, first_text_record + 100)):
            start = records[i]
            end = records[i+1]
            
            if start < len(data) and end <= len(data):
                text_parts.append(data[start:end])
        
        return b''.join(text_parts)
    
    def _decompress_palmdoc(self, data: bytes) -> bytes:
        """解压 PalmDOC 压缩"""
        result = bytearray()
        i = 0
        
        while i < len(data):
            byte = data[i]
            
            if byte >= 0x01 and byte <= 0x08:
                # 字面量
                count = byte
                i += 1
                result.extend(data[i:i+count])
                i += count
            
            elif byte <= 0x7f:
                # 单个字符
                result.append(byte)
                i += 1
            
            elif byte >= 0xc0:
                # 空格 + 字符
                result.append(0x20)
                result.append(byte ^ 0x80)
                i += 1
            
            elif i + 1 < len(data):
                # LZ77 压缩
                next_byte = data[i + 1]
                offset = ((byte << 8) | next_byte) & 0x07ff
                length = ((byte >> 3) & 0x07) + 3
                
                # 回溯复制
                for _ in range(length):
                    if len(result) - offset >= 0:
                        result.append(result[len(result) - offset])
                
                i += 2
            else:
                i += 1
        
        return bytes(result)
    
    def _detect_encoding(self, mobi_header: dict, exth_data: dict) -> str:
        """检测文本编码"""
        # 从 MOBI 头获取编码
        text_encoding = mobi_header.get('text_encoding', 65001)
        
        # 65001 = UTF-8
        if text_encoding == 65001:
            return 'utf-8'
        # 1252 = Windows-1252
        elif text_encoding == 1252:
            return 'cp1252'
        
        # 尝试从 EXTH 获取
        if 505 in exth_data:
            encoding_str = exth_data[505].lower()
            if 'utf-8' in encoding_str or 'utf8' in encoding_str:
                return 'utf-8'
            elif 'gb' in encoding_str:
                return 'gb18030'
        
        return 'utf-8'
    
    def _extract_metadata(self, exth_data: dict, mobi_header: dict) -> dict:
        """提取元数据"""
        metadata = {}
        
        # EXTH 记录类型映射
        # 100 = author
        # 101 = publisher
        # 103 = description
        # 106 = published_date
        # 108 = title
        # 109 = language
        # 503 = title (另一种)
        # 504 = author (另一种)
        
        if 108 in exth_data:
            metadata['title'] = exth_data[108]
        elif 503 in exth_data:
            metadata['title'] = exth_data[503]
        elif mobi_header.get('full_name'):
            metadata['title'] = mobi_header['full_name']
        
        if 100 in exth_data:
            metadata['author'] = exth_data[100]
        elif 504 in exth_data:
            metadata['author'] = exth_data[504]
        
        if 103 in exth_data:
            metadata['description'] = exth_data[103]
        
        if 101 in exth_data:
            metadata['publisher'] = exth_data[101]
        
        if 109 in exth_data:
            metadata['language'] = exth_data[109]
        
        if 106 in exth_data:
            metadata['published_date'] = exth_data[106]
        
        return metadata
    
    def _split_chapters(self, text: str, palmdoc_header: dict) -> List[ChapterInfo]:
        """分割章节"""
        # 使用父类的方法
        return self.split_chapters(text)
    
    async def _fallback_parse(self, file_data: bytes) -> ParseResult:
        """回退解析方法"""
        logger.warning("using_fallback_parser")
        
        # 尝试提取文本
        text = ""
        
        # 方法1: 尝试作为 ZIP 打开 (AZW3)
        try:
            import zipfile
            with zipfile.ZipFile(BytesIO(file_data)) as zf:
                for name in zf.namelist():
                    if name.endswith(('.html', '.htm', '.xhtml')):
                        content = zf.read(name).decode('utf-8', errors='ignore')
                        # 移除 HTML 标签
                        import re
                        text += re.sub(r'<[^>]+>', ' ', content)
        except:
            pass
        
        # 方法2: 直接提取可打印字符
        if not text:
            import re
            # 尝试 UTF-8
            try:
                decoded = file_data.decode('utf-8', errors='ignore')
                text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\n]', '', decoded)
            except:
                pass
        
        # 方法3: 提取中文字符
        if not text:
            import re
            chinese_chars = re.findall(r'[\u4e00-\u9fa5]+', file_data.decode('latin-1', errors='ignore'))
            text = '\n'.join(chinese_chars)
        
        text = self.clean_text(text)
        chapters = self.split_chapters(text)
        chapters = self.identify_core_chapters(chapters)
        
        return ParseResult(
            chapters=chapters,
            total_word_count=sum(ch.word_count for ch in chapters),
            metadata={"format": "mobi", "parsed_with": "fallback"}
        )
