"""
FAISS 向量存储
适合单机部署，无需额外服务
"""
import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from src.common.logger import get_logger
from src.config.settings import settings

from .base import VectorStore

logger = get_logger(__name__)


class FAISSStore(VectorStore):
    """
    FAISS 向量存储
    
    特性：
    - 纯本地，无需外部服务
    - 支持多种索引类型
    - 自动持久化
    - 适合中小规模数据
    """
    
    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path or settings.vector.faiss_index_path or "./data/faiss_index"
        self.index_dir = Path(self.index_path)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.indices: Dict[str, any] = {}
        self.metadata: Dict[str, Dict[str, Dict]] = {}
        self.dimension: Dict[str, int] = {}
    
    async def connect(self):
        """连接（加载已有索引）"""
        # 加载已有索引
        for index_file in self.index_dir.glob("*.faiss"):
            collection_name = index_file.stem
            try:
                import faiss
                self.indices[collection_name] = faiss.read_index(str(index_file))
                
                # 加载元数据
                meta_file = self.index_dir / f"{collection_name}.json"
                if meta_file.exists():
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        self.metadata[collection_name] = json.load(f)
                
                logger.info("faiss_index_loaded", collection=collection_name)
            except Exception as e:
                logger.warning("faiss_index_load_failed", collection=collection_name, error=str(e))
    
    async def close(self):
        """关闭（保存索引）"""
        for collection_name, index in self.indices.items():
            try:
                import faiss
                index_file = self.index_dir / f"{collection_name}.faiss"
                faiss.write_index(index, str(index_file))
                
                # 保存元数据
                meta_file = self.index_dir / f"{collection_name}.json"
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(self.metadata.get(collection_name, {}), f, ensure_ascii=False)
                
                logger.info("faiss_index_saved", collection=collection_name)
            except Exception as e:
                logger.error("faiss_index_save_failed", collection=collection_name, error=str(e))
    
    async def create_collection(
        self,
        collection_name: str,
        dimension: int,
        index_type: str = "Flat",  # Flat, IVF, HNSW
        **kwargs
    ):
        """创建集合"""
        import faiss
        
        if index_type == "Flat":
            # 精确搜索，适合小数据量
            index = faiss.IndexFlatIP(dimension)  # 内积相似度
        elif index_type == "IVF":
            # 倒排文件，加速搜索
            nlist = kwargs.get('nlist', 100)
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        elif index_type == "HNSW":
            # 图索引，高召回率
            M = kwargs.get('M', 16)
            index = faiss.IndexHNSWFlat(dimension, M)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        self.indices[collection_name] = index
        self.metadata[collection_name] = {}
        self.dimension[collection_name] = dimension
        
        logger.info("faiss_collection_created", collection=collection_name, dimension=dimension, index_type=index_type)
    
    async def insert(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadata: List[Dict],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """插入向量"""
        if collection_name not in self.indices:
            raise ValueError(f"Collection not found: {collection_name}")
        
        import faiss
        
        # 生成 ID
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
        
        # 转换为 numpy
        vectors_np = np.array(vectors, dtype=np.float32)
        
        # 归一化（用于内积相似度）
        faiss.normalize_L2(vectors_np)
        
        # 添加到索引
        index = self.indices[collection_name]
        
        # 如果是 IVF 索引且未训练，先训练
        if isinstance(index, faiss.IndexIVFFlat) and not index.is_trained:
            index.train(vectors_np)
        
        index.add(vectors_np)
        
        # 保存元数据
        start_idx = index.ntotal - len(vectors)
        for i, (id, meta) in enumerate(zip(ids, metadata)):
            self.metadata[collection_name][id] = {
                "index": start_idx + i,
                "metadata": meta,
            }
        
        logger.info("faiss_vectors_inserted", collection=collection_name, count=len(vectors))
        
        return ids
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """搜索相似向量"""
        if collection_name not in self.indices:
            raise ValueError(f"Collection not found: {collection_name}")
        
        import faiss
        
        # 转换为 numpy
        query_np = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_np)
        
        # 搜索
        index = self.indices[collection_name]
        distances, indices = index.search(query_np, top_k * 2)  # 多搜一些，过滤后用
        
        # 构建结果
        results = []
        meta_dict = self.metadata.get(collection_name, {})
        
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            
            # 查找对应的 ID
            for id, info in meta_dict.items():
                if info["index"] == idx:
                    # 应用过滤器
                    if filters:
                        meta = info["metadata"]
                        match = True
                        for key, value in filters.items():
                            if meta.get(key) != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    results.append({
                        "id": id,
                        "score": float(distance),
                        "metadata": info["metadata"],
                    })
                    break
            
            if len(results) >= top_k:
                break
        
        return results
    
    async def delete(
        self,
        collection_name: str,
        ids: List[str],
    ) -> bool:
        """删除向量（FAISS 不支持直接删除，需要重建索引）"""
        logger.warning("faiss_delete_not_supported_directly", collection=collection_name)
        
        # 标记为已删除
        for id in ids:
            if id in self.metadata.get(collection_name, {}):
                self.metadata[collection_name][id]["deleted"] = True
        
        return True
    
    async def get(
        self,
        collection_name: str,
        id: str,
    ) -> Optional[Dict]:
        """获取单个向量"""
        if collection_name not in self.metadata:
            return None
        
        info = self.metadata[collection_name].get(id)
        if not info:
            return None
        
        return {
            "id": id,
            "metadata": info["metadata"],
        }
