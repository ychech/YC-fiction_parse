"""
Milvus 向量存储
适合大规模数据，分布式部署
"""
from typing import Dict, List, Optional

from src.common.logger import get_logger
from src.config.settings import settings

from .base import VectorStore

logger = get_logger(__name__)


class MilvusStore(VectorStore):
    """
    Milvus 向量存储
    
    特性：
    - 分布式架构，支持大规模数据
    - 多种索引类型
    - 支持过滤搜索
    - 高可用性
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        self.host = host or settings.vector.milvus_host or "localhost"
        self.port = port or settings.vector.milvus_port or 19530
        self.client = None
    
    async def connect(self):
        """连接 Milvus"""
        try:
            from pymilvus import MilvusClient
            
            self.client = MilvusClient(
                uri=f"http://{self.host}:{self.port}"
            )
            
            logger.info("milvus_connected", host=self.host, port=self.port)
        except Exception as e:
            logger.error("milvus_connect_failed", error=str(e))
            raise
    
    async def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()
            logger.info("milvus_disconnected")
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        **kwargs
    ):
        """创建集合"""
        from pymilvus import DataType
        
        # 检查集合是否存在
        if self.client.has_collection(collection_name):
            logger.info("milvus_collection_exists", collection=collection_name)
            return
        
        # 创建 schema
        schema = self.client.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )
        
        # 添加字段
        schema.add_field(field_name="id", datatype=DataType.VARCHAR, max_length=64, is_primary=True)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dimension)
        schema.add_field(field_name="novel_id", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=256)
        schema.add_field(field_name="genre", datatype=DataType.VARCHAR, max_length=64)
        schema.add_field(field_name="created_at", datatype=DataType.INT64)
        
        # 创建集合
        self.client.create_collection(
            collection_name=collection_name,
            schema=schema,
        )
        
        # 创建索引
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="IVF_FLAT",  # 或 HNSW
            metric_type="IP",  # 内积
            params={"nlist": 128},
        )
        
        self.client.create_index(
            collection_name=collection_name,
            index_params=index_params,
        )
        
        logger.info("milvus_collection_created", collection=collection_name, dimension=dimension)
    
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadata: List[Dict],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """插入向量"""
        from datetime import datetime
        
        # 生成 ID
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        # 构建数据
        data = []
        for i, (id, vector, meta) in enumerate(zip(ids, vectors, metadata)):
            record = {
                "id": id,
                "vector": vector,
                "novel_id": meta.get("novel_id", ""),
                "title": meta.get("title", "")[:256],
                "genre": meta.get("genre", "")[:64],
                "created_at": int(datetime.utcnow().timestamp()),
            }
            data.append(record)
        
        # 插入
        self.client.insert(collection_name=collection_name, data=data)
        
        logger.info("milvus_vectors_inserted", collection=collection_name, count=len(vectors))
        
        return ids
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """搜索相似向量"""
        # 构建过滤表达式
        expr = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f'{key} == "{value}"')
                else:
                    conditions.append(f'{key} == {value}')
            expr = " and ".join(conditions)
        
        # 加载集合
        self.client.load_collection(collection_name)
        
        # 搜索
        results = self.client.search(
            collection_name=collection_name,
            data=[query_vector],
            anns_field="vector",
            limit=top_k,
            search_params={"metric_type": "IP", "params": {"nprobe": 10}},
            filter=expr,
            output_fields=["novel_id", "title", "genre"],
        )
        
        # 格式化结果
        formatted = []
        for result in results[0]:
            formatted.append({
                "id": result["id"],
                "score": result["distance"],
                "metadata": {
                    "novel_id": result["entity"]["novel_id"],
                    "title": result["entity"]["title"],
                    "genre": result["entity"]["genre"],
                }
            })
        
        return formatted
    
    async def delete(
        self,
        collection_name: str,
        ids: List[str],
    ) -> bool:
        """删除向量"""
        expr = f'id in ["{", "'.join(ids)}"]'
        self.client.delete(collection_name=collection_name, expr=expr)
        
        logger.info("milvus_vectors_deleted", collection=collection_name, count=len(ids))
        
        return True
    
    async def get(
        self,
        collection_name: str,
        id: str,
    ) -> Optional[Dict]:
        """获取单个向量"""
        results = self.client.get(
            collection_name=collection_name,
            ids=[id],
            output_fields=["novel_id", "title", "genre"],
        )
        
        if not results:
            return None
        
        result = results[0]
        return {
            "id": result["id"],
            "metadata": {
                "novel_id": result["novel_id"],
                "title": result["title"],
                "genre": result["genre"],
            }
        }
