"""
文本预处理模块 - 格式解析器
"""
from .base import BaseParser, ParseResult
from .epub_parser import EpubParser
from .mobi_parser import MobiParser
from .txt_parser import TxtParser

__all__ = [
    "BaseParser",
    "ParseResult",
    "TxtParser",
    "EpubParser",
    "MobiParser",
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
