"""
本地模型管理器
统一管理 vLLM 和 llama.cpp 两种部署方式
"""
from enum import Enum
from typing import Dict, Optional

from src.common.logger import get_logger
from src.config.settings import settings

from .llamacpp_client import LlamaCppClient
from .vllm_client import VLLMClient

logger = get_logger(__name__)


class LocalModelType(str, Enum):
    """本地模型类型"""
    VLLM = "vllm"
    LLAMACPP = "llamacpp"


class LocalModelManager:
    """
    本地模型管理器
    
    统一管理多种本地模型部署方式，提供统一的调用接口
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.clients: Dict[LocalModelType, object] = {}
        self.default_type: LocalModelType = LocalModelType.VLLM
        self._initialized = True
    
    def initialize(
        self,
        model_type: Optional[LocalModelType] = None,
        **kwargs
    ):
        """
        初始化模型客户端
        
        Args:
            model_type: 模型类型，不指定则初始化默认类型
            **kwargs: 传递给客户端的参数
        """
        if model_type is None:
            model_type = self._get_default_model_type()
        
        try:
            if model_type == LocalModelType.VLLM:
                client = VLLMClient(**kwargs)
            elif model_type == LocalModelType.LLAMACPP:
                client = LlamaCppClient(**kwargs)
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            self.clients[model_type] = client
            self.default_type = model_type
            
            logger.info("local_model_initialized", type=model_type.value)
            
        except Exception as e:
            logger.error("local_model_init_failed", type=model_type.value, error=str(e))
            raise
    
    def _get_default_model_type(self) -> LocalModelType:
        """获取默认模型类型"""
        # 从配置读取
        config_type = settings.ai.local_model_type
        if config_type == "llamacpp":
            return LocalModelType.LLAMACPP
        return LocalModelType.VLLM
    
    def get_client(self, model_type: Optional[LocalModelType] = None):
        """
        获取模型客户端
        
        Args:
            model_type: 模型类型，不指定则返回默认客户端
        
        Returns:
            模型客户端
        """
        if model_type is None:
            model_type = self.default_type
        
        if model_type not in self.clients:
            # 自动初始化
            self.initialize(model_type)
        
        return self.clients[model_type]
    
    async def generate(
        self,
        prompt: str,
        model_type: Optional[LocalModelType] = None,
        **kwargs
    ) -> str:
        """
        生成文本（统一接口）
        
        Args:
            prompt: 提示
            model_type: 模型类型
            **kwargs: 其他参数
        
        Returns:
            生成的文本
        """
        client = self.get_client(model_type)
        return await client.generate(prompt, **kwargs)
    
    async def generate_batch(
        self,
        prompts: list,
        model_type: Optional[LocalModelType] = None,
        **kwargs
    ) -> list:
        """
        批量生成（统一接口）
        
        Args:
            prompts: 提示列表
            model_type: 模型类型
            **kwargs: 其他参数
        
        Returns:
            生成结果列表
        """
        client = self.get_client(model_type)
        return await client.generate_batch(prompts, **kwargs)
    
    async def health_check(self, model_type: Optional[LocalModelType] = None) -> bool:
        """
        健康检查
        
        Args:
            model_type: 模型类型
        
        Returns:
            是否健康
        """
        try:
            client = self.get_client(model_type)
            return await client.health_check()
        except Exception as e:
            logger.warning("health_check_failed", error=str(e))
            return False
    
    def get_model_info(self, model_type: Optional[LocalModelType] = None) -> dict:
        """
        获取模型信息
        
        Args:
            model_type: 模型类型
        
        Returns:
            模型信息
        """
        try:
            client = self.get_client(model_type)
            if hasattr(client, 'get_model_info'):
                import asyncio
                return asyncio.run(client.get_model_info())
            return client.get_model_info()
        except Exception as e:
            logger.warning("get_model_info_failed", error=str(e))
            return {}
    
    def list_models(self) -> list:
        """列出已初始化的模型"""
        return [
            {
                "type": mt.value,
                "initialized": mt in self.clients,
                "is_default": mt == self.default_type,
            }
            for mt in LocalModelType
        ]


# 全局实例
model_manager = LocalModelManager()
