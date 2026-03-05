"""
全局异常定义
"""
from typing import Any, Dict, Optional


class NovelParserException(Exception):
    """基础异常"""
    
    def __init__(
        self,
        message: str,
        code: int = 500,
        detail: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.detail = detail or {}
        super().__init__(self.message)


class ValidationException(NovelParserException):
    """参数验证异常"""
    
    def __init__(self, message: str = "参数验证失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=400, detail=detail)


class NotFoundException(NovelParserException):
    """资源不存在异常"""
    
    def __init__(self, message: str = "资源不存在", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=404, detail=detail)


class FileParseException(NovelParserException):
    """文件解析异常"""
    
    def __init__(self, message: str = "文件解析失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=422, detail=detail)


class AIEngineException(NovelParserException):
    """AI引擎异常"""
    
    def __init__(self, message: str = "AI解析失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=503, detail=detail)


class RuleEngineException(NovelParserException):
    """规则引擎异常"""
    
    def __init__(self, message: str = "规则引擎错误", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, detail=detail)


class StorageException(NovelParserException):
    """存储异常"""
    
    def __init__(self, message: str = "存储操作失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, detail=detail)


class TaskException(NovelParserException):
    """任务异常"""
    
    def __init__(self, message: str = "任务执行失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=500, detail=detail)


class RateLimitException(NovelParserException):
    """限流异常"""
    
    def __init__(self, message: str = "请求过于频繁", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=429, detail=detail)


class AuthenticationException(NovelParserException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=401, detail=detail)


class AuthorizationException(NovelParserException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, code=403, detail=detail)
