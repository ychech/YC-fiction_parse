"""
Redis 缓存层
"""
import json
import pickle
from typing import Any, Optional, Type, TypeVar, Union

import redis.asyncio as redis

from src.config.settings import settings

T = TypeVar("T")


class CacheClient:
    """Redis 缓存客户端"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._redis = None
        return cls._instance
    
    async def connect(self):
        """连接Redis"""
        if self._redis is None:
            self._redis = await redis.from_url(
                f"redis://{settings.db.redis_host}:{settings.db.redis_port}/{settings.db.redis_db}",
                password=settings.db.redis_password,
                max_connections=settings.db.redis_pool_size,
                decode_responses=False,  # 二进制数据支持
            )
    
    async def close(self):
        """关闭连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def ping(self) -> bool:
        """检查连接"""
        return await self._redis.ping()
    
    # ==================== 基础操作 ====================
    
    async def get(self, key: str) -> Optional[bytes]:
        """获取值"""
        return await self._redis.get(key)
    
    async def set(
        self,
        key: str,
        value: Union[str, bytes],
        ttl: Optional[int] = None
    ) -> bool:
        """设置值"""
        if isinstance(value, str):
            value = value.encode("utf-8")
        return await self._redis.set(key, value, ex=ttl)
    
    async def delete(self, key: str) -> int:
        """删除键"""
        return await self._redis.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self._redis.exists(key) > 0
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return await self._redis.ttl(key)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        return await self._redis.expire(key, ttl)
    
    # ==================== 序列化操作 ====================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """获取JSON数据"""
        data = await self.get(key)
        if data:
            return json.loads(data.decode("utf-8"))
        return None
    
    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置JSON数据"""
        return await self.set(key, json.dumps(value, ensure_ascii=False), ttl)
    
    async def get_object(self, key: str) -> Optional[Any]:
        """获取Python对象（使用pickle）"""
        data = await self.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    async def set_object(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置Python对象"""
        return await self.set(key, pickle.dumps(value), ttl)
    
    # ==================== 哈希操作 ====================
    
    async def hget(self, key: str, field: str) -> Optional[bytes]:
        """获取哈希字段"""
        return await self._redis.hget(key, field)
    
    async def hset(self, key: str, field: str, value: Union[str, bytes]) -> int:
        """设置哈希字段"""
        if isinstance(value, str):
            value = value.encode("utf-8")
        return await self._redis.hset(key, field, value)
    
    async def hgetall(self, key: str) -> dict:
        """获取所有哈希字段"""
        return await self._redis.hgetall(key)
    
    async def hdel(self, key: str, *fields: str) -> int:
        """删除哈希字段"""
        return await self._redis.hdel(key, *fields)
    
    # ==================== 列表操作 ====================
    
    async def lpush(self, key: str, *values: Union[str, bytes]) -> int:
        """左侧推入列表"""
        encoded = [v.encode("utf-8") if isinstance(v, str) else v for v in values]
        return await self._redis.lpush(key, *encoded)
    
    async def rpop(self, key: str) -> Optional[bytes]:
        """右侧弹出列表"""
        return await self._redis.rpop(key)
    
    async def llen(self, key: str) -> int:
        """获取列表长度"""
        return await self._redis.llen(key)
    
    # ==================== 集合操作 ====================
    
    async def sadd(self, key: str, *members: str) -> int:
        """添加集合成员"""
        return await self._redis.sadd(key, *members)
    
    async def sismember(self, key: str, member: str) -> bool:
        """检查集合成员"""
        return await self._redis.sismember(key, member)
    
    async def smembers(self, key: str) -> set:
        """获取所有集合成员"""
        return await self._redis.smembers(key)
    
    # ==================== 分布式锁 ====================
    
    async def acquire_lock(
        self,
        lock_key: str,
        lock_value: str,
        ttl: int = 30
    ) -> bool:
        """获取分布式锁"""
        return await self._redis.set(
            f"lock:{lock_key}",
            lock_value.encode(),
            nx=True,
            ex=ttl
        )
    
    async def release_lock(self, lock_key: str, lock_value: str) -> bool:
        """释放分布式锁"""
        key = f"lock:{lock_key}"
        current_value = await self.get(key)
        if current_value and current_value.decode() == lock_value:
            return await self.delete(key) > 0
        return False
    
    # ==================== 业务封装 ====================
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态缓存"""
        return await self.get_json(f"task:status:{task_id}")
    
    async def set_task_status(
        self,
        task_id: str,
        status: dict,
        ttl: int = 3600  # 1小时
    ) -> bool:
        """设置任务状态缓存"""
        return await self.set_json(f"task:status:{task_id}", status, ttl)
    
    async def get_novel_features(self, novel_id: str) -> Optional[Any]:
        """获取小说特征缓存"""
        return await self.get_object(f"novel:features:{novel_id}")
    
    async def set_novel_features(
        self,
        novel_id: str,
        features: Any,
        ttl: int = 86400  # 24小时
    ) -> bool:
        """设置小说特征缓存"""
        return await self.set_object(f"novel:features:{novel_id}", features, ttl)
    
    async def invalidate_novel_cache(self, novel_id: str) -> int:
        """清除小说相关缓存"""
        keys = [
            f"novel:features:{novel_id}",
            f"novel:meta:{novel_id}",
        ]
        return sum(await self.delete(k) for k in keys)
    
    async def get_rate_limit_count(
        self,
        key: str,
        window: int = 60
    ) -> tuple[int, int]:
        """
        获取限流计数
        返回: (当前计数, 剩余窗口秒数)
        """
        pipe = self._redis.pipeline()
        pipe.incr(f"rate_limit:{key}")
        pipe.expire(f"rate_limit:{key}", window)
        pipe.ttl(f"rate_limit:{key}")
        results = await pipe.execute()
        return results[0], results[2]
    
    async def increment_counter(
        self,
        counter_name: str,
        increment: int = 1
    ) -> int:
        """增加计数器"""
        return await self._redis.incrby(f"counter:{counter_name}", increment)
    
    async def get_counter(self, counter_name: str) -> int:
        """获取计数器值"""
        value = await self.get(f"counter:{counter_name}")
        return int(value) if value else 0


# 全局实例
cache_client = CacheClient()


async def get_cache_client() -> CacheClient:
    """获取缓存客户端"""
    if cache_client._redis is None:
        await cache_client.connect()
    return cache_client
