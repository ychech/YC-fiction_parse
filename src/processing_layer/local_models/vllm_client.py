"""
vLLM 客户端
支持高吞吐量的本地大模型推理
"""
import asyncio
from typing import AsyncGenerator, Dict, List, Optional

from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class VLLMClient:
    """
    vLLM 客户端
    
    特性：
    - 支持异步流式生成
    - 自动批处理请求
    - 支持多 GPU
    - 与 OpenAI API 兼容的接口
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url or settings.ai.vllm_base_url or "http://localhost:8000/v1"
        self.model = model or settings.ai.vllm_model or "Qwen-7B-Chat"
        self.api_key = api_key or "dummy"  # vLLM 默认不需要 API key
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化客户端"""
        try:
            from openai import AsyncOpenAI
            
            self.client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=settings.ai.request_timeout,
            )
            logger.info("vllm_client_initialized", base_url=self.base_url, model=self.model)
        except Exception as e:
            logger.error("vllm_client_init_failed", error=str(e))
            raise
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        stream: bool = False,
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度
            max_tokens: 最大 token 数
            top_p: Top-p 采样
            stream: 是否流式输出
        
        Returns:
            生成的文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            if stream:
                return await self._generate_stream(messages, temperature, max_tokens, top_p)
            else:
                return await self._generate_batch(messages, temperature, max_tokens, top_p)
        except Exception as e:
            logger.error("vllm_generation_failed", error=str(e))
            raise
    
    async def _generate_batch(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> str:
        """批量生成"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=False,
        )
        
        return response.choices[0].message.content
    
    async def _generate_stream(
        self,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        top_p: float,
    ) -> str:
        """流式生成"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            stream=True,
        )
        
        result = []
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                result.append(chunk.choices[0].delta.content)
        
        return "".join(result)
    
    async def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_concurrent: int = 5,
    ) -> List[str]:
        """
        批量生成
        
        Args:
            prompts: 提示列表
            system_prompt: 系统提示
            temperature: 温度
            max_tokens: 最大 token 数
            max_concurrent: 最大并发数
        
        Returns:
            生成结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_limit(prompt: str) -> str:
            async with semaphore:
                return await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
        
        tasks = [generate_with_limit(p) for p in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试获取模型列表
            models = await self.client.models.list()
            return len(models.data) > 0
        except Exception as e:
            logger.warning("vllm_health_check_failed", error=str(e))
            return False
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "type": "vllm",
        }
