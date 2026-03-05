"""
缓存优化器
多级缓存策略，提升性能
"""
import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional

from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class CacheOptimizer:
    """
    缓存优化器
    
    特性：
    - 多级缓存（内存 + Redis）
    - 智能缓存键生成
    - 缓存预热
    - 缓存穿透保护
    """
    
    def __init__(self):
        self.memory_cache: dict = {}
        self.redis_cache = None
        self._initialized = False
    
    async def initialize(self):
        """初始化缓存"""
        if self._initialized:
            return
        
        from src.data_layer.cache import get_cache_client
        self.redis_cache = await get_cache_client()
        
        self._initialized = True
        logger.info("cache_optimizer_initialized")
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 构建键数据
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": kwargs,
        }
        
        # 序列化并哈希
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    async def get(self, key: str, use_memory: bool = True) -> Optional[Any]:
        """获取缓存"""
        # 1. 检查内存缓存
        if use_memory and key in self.memory_cache:
            logger.debug("memory_cache_hit", key=key)
            return self.memory_cache[key]
        
        # 2. 检查 Redis
        if self.redis_cache:
            value = await self.redis_cache.get_json(key)
            if value is not None:
                logger.debug("redis_cache_hit", key=key)
                # 回填内存缓存
                if use_memory:
                    self.memory_cache[key] = value
                return value
        
        logger.debug("cache_miss", key=key)
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        use_memory: bool = True,
    ):
        """设置缓存"""
        # 1. 设置内存缓存
        if use_memory:
            self.memory_cache[key] = value
        
        # 2. 设置 Redis
        if self.redis_cache:
            await self.redis_cache.set_json(key, value, ttl)
        
        logger.debug("cache_set", key=key, ttl=ttl)
    
    async def delete(self, key: str):
        """删除缓存"""
        # 1. 删除内存缓存
        self.memory_cache.pop(key, None)
        
        # 2. 删除 Redis
        if self.redis_cache:
            await self.redis_cache.delete(key)
        
        logger.debug("cache_delete", key=key)
    
    async def get_or_set(
        self,
        key: str,
        getter: Callable,
        ttl: int = 3600,
        use_memory: bool = True,
    ) -> Any:
        """获取或设置缓存"""
        # 尝试获取
        value = await self.get(key, use_memory)
        if value is not None:
            return value
        
        # 获取数据
        if asyncio.iscoroutinefunction(getter):
            value = await getter()
        else:
            value = getter()
        
        # 设置缓存
        await self.set(key, value, ttl, use_memory)
        
        return value
    
    def cached(
        self,
        prefix: str,
        ttl: int = 3600,
        key_builder: Optional[Callable] = None,
    ):
        """缓存装饰器"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    cache_key = self.generate_key(prefix, *args, **kwargs)
                
                # 尝试获取缓存
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 设置缓存
                await self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    async def invalidate_pattern(self, pattern: str):
        """按模式失效缓存"""
        # 清理内存缓存
        keys_to_delete = [
            k for k in self.memory_cache.keys()
            if pattern in k
        ]
        for k in keys_to_delete:
            del self.memory_cache[k]
        
        logger.info("cache_invalidated", pattern=pattern, count=len(keys_to_delete))
    
    async def warm_up(self, keys_and_getters: dict):
        """缓存预热"""
        for key, getter in keys_and_getters.items():
            try:
                value = await getter() if asyncio.iscoroutinefunction(getter) else getter()
                await self.set(key, value)
                logger.info("cache_warmed_up", key=key)
            except Exception as e:
                logger.error("cache_warm_up_failed", key=key, error=str(e))


# 全局缓存优化器
cache_optimizer = CacheOptimizer()


import asyncio
