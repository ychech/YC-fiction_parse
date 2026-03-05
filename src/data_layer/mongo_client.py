"""
MongoDB 客户端 - 存储解析结果
"""
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

from src.common.schemas import NovelFeatures, SearchQuery, SearchResult
from src.config.settings import settings


class MongoClient:
    """MongoDB 异步客户端"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
            cls._instance._db = None
        return cls._instance
    
    async def connect(self):
        """连接数据库"""
        if self._client is None:
            self._client = AsyncIOMotorClient(
                settings.db.mongodb_url,
                maxPoolSize=settings.db.mongodb_max_pool_size,
            )
            self._db = self._client[settings.db.mongodb_db]
            await self._create_indexes()
    
    async def close(self):
        """关闭连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
    
    async def _create_indexes(self):
        """创建索引"""
        # 解析结果集合
        await self._db.novel_features.create_indexes([
            IndexModel([("novel_id", ASCENDING)], unique=True),
            IndexModel([("confidence_score", DESCENDING)]),
            IndexModel([("background.world_type", ASCENDING)]),
            IndexModel([("task.task_structure", ASCENDING)]),
            IndexModel([("writing.narrative_perspective", ASCENDING)]),
        ])
        
        # 章节集合
        await self._db.chapters.create_indexes([
            IndexModel([("novel_id", ASCENDING), ("chapter_number", ASCENDING)]),
            IndexModel([("chapter_hash", ASCENDING)], unique=True, sparse=True),
        ])
    
    @property
    def db(self):
        """获取数据库实例"""
        return self._db
    
    # ==================== 解析结果操作 ====================
    
    async def save_features(self, features: NovelFeatures) -> str:
        """保存解析结果"""
        doc = features.dict()
        doc["_id"] = features.novel_id
        
        await self._db.novel_features.replace_one(
            {"novel_id": features.novel_id},
            doc,
            upsert=True
        )
        return features.novel_id
    
    async def get_features(self, novel_id: str) -> Optional[NovelFeatures]:
        """获取解析结果"""
        doc = await self._db.novel_features.find_one({"novel_id": novel_id})
        if doc:
            doc.pop("_id", None)
            return NovelFeatures(**doc)
        return None
    
    async def delete_features(self, novel_id: str) -> bool:
        """删除解析结果"""
        result = await self._db.novel_features.delete_one({"novel_id": novel_id})
        return result.deleted_count > 0
    
    async def search_features(
        self,
        query: SearchQuery
    ) -> tuple[List[SearchResult], int]:
        """搜索解析结果"""
        
        # 构建查询条件
        mongo_query = {}
        
        if query.genre:
            mongo_query["background.world_type"] = query.genre.value
        
        if query.min_confidence > 0:
            mongo_query["confidence_score"] = {"$gte": query.min_confidence}
        
        # 应用自定义过滤器
        for key, value in query.filters.items():
            if "." in key:
                mongo_query[key] = value
            else:
                mongo_query[f"custom_fields.{key}"] = value
        
        # 文本搜索
        if query.query:
            mongo_query["$text"] = {"$search": query.query}
        
        # 计算总数
        total = await self._db.novel_features.count_documents(mongo_query)
        
        # 排序
        sort_field = query.sort_by
        sort_direction = DESCENDING if query.sort_order == "desc" else ASCENDING
        
        # 分页查询
        cursor = self._db.novel_features.find(mongo_query)
        cursor = cursor.sort(sort_field, sort_direction)
        cursor = cursor.skip((query.page - 1) * query.page_size)
        cursor = cursor.limit(query.page_size)
        
        results = []
        async for doc in cursor:
            doc.pop("_id", None)
            features = NovelFeatures(**doc)
            
            # 获取小说元信息（简化处理）
            results.append(SearchResult(
                novel_id=features.novel_id,
                title="",  # 需要从PostgreSQL获取
                author=None,
                genre=None,
                confidence_score=features.confidence_score,
                matched_features=doc,
            ))
        
        return results, total
    
    async def update_custom_fields(
        self,
        novel_id: str,
        custom_fields: Dict[str, Any]
    ) -> bool:
        """更新自定义字段"""
        result = await self._db.novel_features.update_one(
            {"novel_id": novel_id},
            {"$set": {"custom_fields": custom_fields}}
        )
        return result.modified_count > 0
    
    # ==================== 章节操作 ====================
    
    async def save_chapters(self, novel_id: str, chapters: List[Dict[str, Any]]):
        """批量保存章节"""
        if not chapters:
            return
        
        for ch in chapters:
            ch["novel_id"] = novel_id
        
        await self._db.chapters.insert_many(chapters, ordered=False)
    
    async def get_chapters(
        self,
        novel_id: str,
        chapter_numbers: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """获取章节"""
        query = {"novel_id": novel_id}
        if chapter_numbers:
            query["chapter_number"] = {"$in": chapter_numbers}
        
        cursor = self._db.chapters.find(query).sort("chapter_number", ASCENDING)
        return await cursor.to_list(length=None)
    
    async def get_chapter_by_hash(self, chapter_hash: str) -> Optional[Dict[str, Any]]:
        """根据hash获取章节（用于增量解析）"""
        return await self._db.chapters.find_one({"chapter_hash": chapter_hash})
    
    async def update_chapter_content(
        self,
        novel_id: str,
        chapter_number: int,
        content: str,
        chapter_hash: str
    ):
        """更新章节内容"""
        await self._db.chapters.update_one(
            {"novel_id": novel_id, "chapter_number": chapter_number},
            {
                "$set": {
                    "content": content,
                    "chapter_hash": chapter_hash,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )


# 全局实例
mongo_client = MongoClient()


async def get_mongo_client() -> MongoClient:
    """获取MongoDB客户端"""
    if mongo_client._client is None:
        await mongo_client.connect()
    return mongo_client
