"""
向量存储基类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def connect(self):
        """连接数据库"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭连接"""
        pass
    
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ):
        """创建集合"""
        pass
    
    @abstractmethod
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadata: List[Dict],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """插入向量"""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        ids: List[str],
    ) -> bool:
        """删除向量"""
        pass
    
    @abstractmethod
    async def get(
        self,
        collection_name: str,
        id: str,
    ) -> Optional[Dict]:
        """获取单个向量"""
        pass
