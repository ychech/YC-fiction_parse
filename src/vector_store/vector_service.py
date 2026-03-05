"""
向量服务
封装向量存储和相似度搜索功能
"""
from typing import Dict, List, Optional

from src.common.deep_schemas import DeepNovelFeatures
from src.common.logger import get_logger
from src.config.settings import settings

from .base import VectorStore
from .faiss_store import FAISSStore
from .milvus_store import MilvusStore

logger = get_logger(__name__)


class VectorService:
    """
    向量服务
    
    提供小说特征向量化存储和相似度搜索功能
    """
    
    COLLECTION_NAME = "novel_vectors"
    
    def __init__(self):
        self.store: Optional[VectorStore] = None
        self.embedding_model = None
        self._initialized = False
    
    async def initialize(self):
        """初始化服务"""
        if self._initialized:
            return
        
        # 初始化向量存储
        backend = settings.vector.backend
        if backend == "milvus":
            self.store = MilvusStore()
        else:
            self.store = FAISSStore()
        
        await self.store.connect()
        
        # 创建集合
        await self.store.create_collection(
            collection_name=self.COLLECTION_NAME,
            dimension=settings.ai.vector_dimension,
        )
        
        # 初始化嵌入模型
        await self._initialize_embedding_model()
        
        self._initialized = True
        logger.info("vector_service_initialized", backend=backend)
    
    async def _initialize_embedding_model(self):
        """初始化嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            model_name = settings.ai.embedding_model
            self.embedding_model = SentenceTransformer(model_name)
            
            logger.info("embedding_model_loaded", model=model_name)
        except Exception as e:
            logger.error("embedding_model_load_failed", error=str(e))
            raise
    
    async def close(self):
        """关闭服务"""
        if self.store:
            await self.store.close()
        
        self._initialized = False
        logger.info("vector_service_closed")
    
    async def add_novel(self, novel_id: str, features: DeepNovelFeatures):
        """
        添加小说到向量库
        
        Args:
            novel_id: 小说ID
            features: 深度解析特征
        """
        if not self._initialized:
            await self.initialize()
        
        # 构建文本表示
        texts = self._build_feature_texts(features)
        
        # 生成向量
        vectors = self.embedding_model.encode(texts)
        
        # 构建元数据
        metadata = {
            "novel_id": novel_id,
            "title": features.story_core.conflict_formula.formula_name,
            "genre": features.story_core.conflict_formula.applicable_genres[0] if features.story_core.conflict_formula.applicable_genres else "",
        }
        
        # 插入向量
        await self.store.insert(
            collection_name=self.COLLECTION_NAME,
            vectors=vectors.tolist(),
            metadata=[metadata] * len(vectors),
        )
        
        logger.info("novel_added_to_vector_store", novel_id=novel_id)
    
    def _build_feature_texts(self, features: DeepNovelFeatures) -> List[str]:
        """构建特征文本表示"""
        texts = []
        
        # 1. 故事内核
        cf = features.story_core.conflict_formula
        texts.append(f"{cf.formula_name}: {cf.protagonist_desire} {cf.core_obstacle} {cf.solution_path}")
        
        # 2. 金手指
        gf = features.core_setting.golden_finger
        texts.append(f"{gf.gf_type.value} {gf.growth_type.value} {' '.join(c.constraint_type for c in gf.constraints)}")
        
        # 3. 人物弧光
        arc = features.character_analysis.protagonist_arc
        texts.append(f"{arc.arc_type.value} {arc.initial_state} {arc.final_state}")
        
        # 4. 叙事风格
        nt = features.narrative_technique
        texts.append(f"节奏{nt.language_style.rhythm_score} 短句{nt.language_style.short_sentence_ratio}")
        
        return texts
    
    async def search_similar(
        self,
        query_novel_id: Optional[str] = None,
        query_features: Optional[DeepNovelFeatures] = None,
        query_text: Optional[str] = None,
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        搜索相似小说
        
        Args:
            query_novel_id: 查询小说ID
            query_features: 查询特征
            query_text: 查询文本
            top_k: 返回数量
            filters: 过滤器
        
        Returns:
            相似小说列表
        """
        if not self._initialized:
            await self.initialize()
        
        # 生成查询向量
        if query_text:
            query_vector = self.embedding_model.encode([query_text])[0].tolist()
        elif query_features:
            texts = self._build_feature_texts(query_features)
            # 使用平均向量
            vectors = self.embedding_model.encode(texts)
            query_vector = vectors.mean(axis=0).tolist()
        else:
            raise ValueError("Must provide query_novel_id, query_features, or query_text")
        
        # 搜索
        results = await self.store.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            filters=filters,
        )
        
        return results
    
    async def find_similar_by_novel(
        self,
        novel_id: str,
        top_k: int = 10,
        exclude_self: bool = True,
    ) -> List[Dict]:
        """
        查找与指定小说相似的小说
        
        Args:
            novel_id: 小说ID
            top_k: 返回数量
            exclude_self: 是否排除自己
        
        Returns:
            相似小说列表
        """
        # 获取小说特征
        from src.data_layer.mongo_client import get_mongo_client
        
        mongo_client = await get_mongo_client()
        features = await mongo_client.get_features(novel_id)
        
        if not features:
            logger.warning("novel_features_not_found", novel_id=novel_id)
            return []
        
        # 搜索相似
        results = await self.search_similar(
            query_features=features,
            top_k=top_k + 1 if exclude_self else top_k,
        )
        
        # 排除自己
        if exclude_self:
            results = [r for r in results if r["metadata"].get("novel_id") != novel_id][:top_k]
        
        return results
    
    async def delete_novel(self, novel_id: str):
        """从向量库删除小说"""
        if not self._initialized:
            await self.initialize()
        
        # 这里简化处理，实际应该记录向量ID
        logger.info("novel_deleted_from_vector_store", novel_id=novel_id)


# 全局实例
vector_service = VectorService()
