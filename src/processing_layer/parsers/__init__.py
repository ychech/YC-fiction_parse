"""
文本预处理模块 - 格式解析器
"""
from .base import BaseParser, ParseResult
from .epub_parser import EpubParser
from .epub_parser_v2 import EpubParserV2
from .mobi_parser import MobiParser
from .mobi_parser_v2 import MobiParserV2
from .txt_parser import TxtParser

__all__ = [
    "BaseParser",
    "ParseResult",
    "TxtParser",
    "EpubParser",
    "EpubParserV2",
    "MobiParser",
    "MobiParserV2",
    "get_parser",
]


# 解析器注册表
PARSER_REGISTRY = {
    "txt": TxtParser,
    "epub": EpubParser,
    "mobi": MobiParser,
}


def get_parser(format_type: str) -> BaseParser:
    """获取对应格式的解析器"""
    format_type = format_type.lower()
    if format_type not in PARSER_REGISTRY:
        raise ValueError(f"Unsupported format: {format_type}")
    return PARSER_REGISTRY[format_type]()
