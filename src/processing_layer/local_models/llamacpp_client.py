"""
llama.cpp 客户端
支持 GGUF 格式的量化模型，低资源部署
"""
import json
from typing import Dict, List, Optional

from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class LlamaCppClient:
    """
    llama.cpp 客户端
    
    特性：
    - 支持 GGUF 量化模型
    - 低内存占用
    - 支持 CPU/GPU 混合推理
    - 支持并发请求
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_path: Optional[str] = None,
    ):
        self.base_url = base_url or settings.ai.llamacpp_base_url or "http://localhost:8080"
        self.model_path = model_path or settings.ai.llamacpp_model_path
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化客户端"""
        try:
            import httpx
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=settings.ai.request_timeout,
            )
            logger.info("llamacpp_client_initialized", base_url=self.base_url)
        except Exception as e:
            logger.error("llamacpp_client_init_failed", error=str(e))
            raise
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
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
            top_k: Top-k 采样
            repeat_penalty: 重复惩罚
            stream: 是否流式输出
        
        Returns:
            生成的文本
        """
        # 构建完整提示
        if system_prompt:
            full_prompt = f"<|system|>\n{system_prompt}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
        else:
            full_prompt = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
        
        try:
            if stream:
                return await self._generate_stream(
                    full_prompt, temperature, max_tokens, top_p, top_k, repeat_penalty
                )
            else:
                return await self._generate_batch(
                    full_prompt, temperature, max_tokens, top_p, top_k, repeat_penalty
                )
        except Exception as e:
            logger.error("llamacpp_generation_failed", error=str(e))
            raise
    
    async def _generate_batch(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        repeat_penalty: float,
    ) -> str:
        """批量生成"""
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": max_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "stream": False,
        }
        
        response = await self.client.post("/completion", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("content", "")
    
    async def _generate_stream(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        top_k: int,
        repeat_penalty: float,
    ) -> str:
        """流式生成"""
        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": max_tokens,
            "top_p": top_p,
            "top_k": top_k,
            "repeat_penalty": repeat_penalty,
            "stream": True,
        }
        
        result = []
        async with self.client.stream("POST", "/completion", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if "content" in chunk:
                            result.append(chunk["content"])
                    except json.JSONDecodeError:
                        continue
        
        return "".join(result)
    
    async def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        max_concurrent: int = 3,
    ) -> List[str]:
        """
        批量生成
        
        llama.cpp 的并发能力有限，建议控制并发数
        """
        import asyncio
        
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
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning("llamacpp_health_check_failed", error=str(e))
            return False
    
    async def get_model_info(self) -> Dict:
        """获取模型信息"""
        try:
            response = await self.client.get("/props")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning("get_model_info_failed", error=str(e))
        
        return {
            "model_path": self.model_path,
            "base_url": self.base_url,
            "type": "llamacpp",
        }
    
    async def tokenize(self, text: str) -> List[int]:
        """分词"""
        try:
            response = await self.client.post("/tokenize", json={"content": text})
            response.raise_for_status()
            result = response.json()
            return result.get("tokens", [])
        except Exception as e:
            logger.error("tokenize_failed", error=str(e))
            return []
    
    async def detokenize(self, tokens: List[int]) -> str:
        """反分词"""
        try:
            response = await self.client.post("/detokenize", json={"tokens": tokens})
            response.raise_for_status()
            result = response.json()
            return result.get("content", "")
        except Exception as e:
            logger.error("detokenize_failed", error=str(e))
            return ""
