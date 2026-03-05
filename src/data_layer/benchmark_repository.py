"""
对比基准库 Repository
存储和管理标杆小说的解析结果，支持对比分析
"""
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.common.deep_schemas import DeepNovelFeatures
from src.common.logger import get_logger
from src.data_layer.mongo_client import get_mongo_client

logger = get_logger(__name__)


class BenchmarkRepository:
    """
    对比基准库
    
    功能：
    1. 存储标杆小说的深度解析结果
    2. 支持按类型/标签检索标杆
    3. 提供对比分析功能
    4. 支持动态更新（基于市场数据）
    """
    
    COLLECTION_NAME = "benchmark_novels"
    
    def __init__(self):
        self.mongo_client = None
    
    async def _get_client(self):
        """获取 MongoDB 客户端"""
        if self.mongo_client is None:
            self.mongo_client = await get_mongo_client()
        return self.mongo_client
    
    # ==================== CRUD 操作 ====================
    
    async def add_benchmark(
        self,
        novel_id: str,
        title: str,
        author: str,
        genre: str,
        features: DeepNovelFeatures,
        market_data: Optional[Dict] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        添加标杆小说
        
        Args:
            novel_id: 小说ID
            title: 书名
            author: 作者
            genre: 类型
            features: 深度解析结果
            market_data: 市场数据（阅读量、评分等）
            tags: 标签
        """
        client = await self._get_client()
        
        doc = {
            "novel_id": novel_id,
            "title": title,
            "author": author,
            "genre": genre,
            "features": features.dict(),
            "market_data": market_data or {},
            "tags": tags or [],
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        await client.db[self.COLLECTION_NAME].replace_one(
            {"novel_id": novel_id},
            doc,
            upsert=True
        )
        
        logger.info("benchmark_added", novel_id=novel_id, title=title)
        return novel_id
    
    async def get_benchmark(self, novel_id: str) -> Optional[Dict]:
        """获取标杆小说"""
        client = await self._get_client()
        return await client.db[self.COLLECTION_NAME].find_one({
            "novel_id": novel_id,
            "is_active": True
        })
    
    async def list_benchmarks(
        self,
        genre: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """列表查询标杆小说"""
        client = await self._get_client()
        
        query = {"is_active": True}
        if genre:
            query["genre"] = genre
        if tags:
            query["tags"] = {"$in": tags}
        
        cursor = client.db[self.COLLECTION_NAME].find(query)
        cursor = cursor.limit(limit)
        cursor = cursor.sort("market_data.read_count", -1)  # 按阅读量排序
        
        return await cursor.to_list(length=limit)
    
    async def update_market_data(
        self,
        novel_id: str,
        market_data: Dict,
    ) -> bool:
        """更新市场数据"""
        client = await self._get_client()
        
        result = await client.db[self.COLLECTION_NAME].update_one(
            {"novel_id": novel_id},
            {
                "$set": {
                    "market_data": market_data,
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        return result.modified_count > 0
    
    # ==================== 对比分析 ====================
    
    async def compare_with_benchmarks(
        self,
        features: DeepNovelFeatures,
        genre: Optional[str] = None,
        top_n: int = 3,
    ) -> Dict[str, Any]:
        """
        与标杆小说对比
        
        Returns:
            {
                "differentiation_points": [...],  # 差异化点
                "reusable_elements": [...],       # 可复用元素
                "optimization_suggestions": [...], # 优化建议
                "similar_benchmarks": [...],      # 相似标杆
            }
        """
        # 获取同类型标杆
        benchmarks = await self.list_benchmarks(genre=genre, limit=top_n * 2)
        
        if not benchmarks:
            return {
                "differentiation_points": [],
                "reusable_elements": [],
                "optimization_suggestions": ["暂无标杆数据，建议添加同类标杆进行对比"],
                "similar_benchmarks": [],
            }
        
        # 计算相似度
        similarities = []
        for bm in benchmarks:
            similarity = self._calculate_similarity(features, bm["features"])
            similarities.append((bm, similarity))
        
        # 排序并取最相似的
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_benchmarks = similarities[:top_n]
        
        # 生成对比结果
        differentiation_points = self._find_differentiation(features, top_benchmarks)
        reusable_elements = self._find_reusable_elements(features, top_benchmarks)
        optimization_suggestions = self._generate_suggestions(features, top_benchmarks)
        
        return {
            "differentiation_points": differentiation_points,
            "reusable_elements": reusable_elements,
            "optimization_suggestions": optimization_suggestions,
            "similar_benchmarks": [
                {
                    "novel_id": bm["novel_id"],
                    "title": bm["title"],
                    "similarity": round(sim, 2),
                }
                for bm, sim in top_benchmarks
            ],
        }
    
    def _calculate_similarity(
        self,
        features: DeepNovelFeatures,
        benchmark_features: Dict,
    ) -> float:
        """计算与标杆的相似度"""
        scores = []
        
        # 1. 冲突公式相似度
        if features.story_core.conflict_formula.conflict_type.value == \
           benchmark_features.get("story_core", {}).get("conflict_formula", {}).get("conflict_type"):
            scores.append(0.2)
        
        # 2. 金手指类型相似度
        if features.core_setting.golden_finger.gf_type.value == \
           benchmark_features.get("core_setting", {}).get("golden_finger", {}).get("gf_type"):
            scores.append(0.15)
        
        # 3. 人物弧光相似度
        if features.character_analysis.protagonist_arc.arc_type.value == \
           benchmark_features.get("character_analysis", {}).get("protagonist_arc", {}).get("arc_type"):
            scores.append(0.15)
        
        # 4. 情绪节奏相似度
        rhythm1 = features.story_core.hook_distribution.rhythm_pattern
        rhythm2 = benchmark_features.get("story_core", {}).get("hook_distribution", {}).get("rhythm_pattern")
        if rhythm1 and rhythm2 and "每" in rhythm1 and "每" in rhythm2:
            # 简化比较
            scores.append(0.1)
        
        # 5. 叙事风格相似度
        if features.narrative_technique.language_style.short_sentence_ratio > 0.4:
            if benchmark_features.get("narrative_technique", {}).get("language_style", {}).get("short_sentence_ratio", 0) > 0.4:
                scores.append(0.1)
        
        return sum(scores)
    
    def _find_differentiation(
        self,
        features: DeepNovelFeatures,
        top_benchmarks: List[tuple],
    ) -> List[Dict]:
        """找出差异化点"""
        differentiations = []
        
        for bm, sim in top_benchmarks[:1]:  # 与最相似的对比
            bm_features = bm["features"]
            
            # 1. 金手指创新点
            gf_innovations = features.core_setting.golden_finger.innovation_points
            if gf_innovations:
                differentiations.append({
                    "dimension": "金手指设定",
                    "point": f"相比《{bm['title']}》，本作金手指具有创新性：{gf_innovations[0]}",
                    "uniqueness_score": 0.8,
                })
            
            # 2. 情绪钩子差异
            hooks1 = features.story_core.hook_distribution.type_distribution
            hooks2 = bm_features.get("story_core", {}).get("hook_distribution", {}).get("type_distribution", {})
            
            top_hook1 = max(hooks1.items(), key=lambda x: x[1])[0] if hooks1 else None
            top_hook2 = max(hooks2.items(), key=lambda x: x[1])[0] if hooks2 else None
            
            if top_hook1 and top_hook2 and top_hook1 != top_hook2:
                differentiations.append({
                    "dimension": "情绪驱动",
                    "point": f"《{bm['title']}》以{top_hook2}为主，本作以{top_hook1}为主",
                    "uniqueness_score": 0.7,
                })
            
            # 3. 人物弧光差异
            arc1 = features.character_analysis.protagonist_arc.arc_type.value
            arc2 = bm_features.get("character_analysis", {}).get("protagonist_arc", {}).get("arc_type")
            
            if arc1 and arc2 and arc1 != arc2:
                differentiations.append({
                    "dimension": "人物成长",
                    "point": f"人物弧光类型不同：{arc1} vs {arc2}",
                    "uniqueness_score": 0.6,
                })
        
        return differentiations
    
    def _find_reusable_elements(
        self,
        features: DeepNovelFeatures,
        top_benchmarks: List[tuple],
    ) -> List[Dict]:
        """找出可复用元素"""
        reusables = []
        
        for bm, sim in top_benchmarks[:2]:
            bm_features = bm["features"]
            
            # 1. 可复用的冲突公式
            if features.story_core.conflict_formula.conflict_type.value == \
               bm_features.get("story_core", {}).get("conflict_formula", {}).get("conflict_type"):
                reusables.append({
                    "element": "冲突公式",
                    "source": bm["title"],
                    "description": f"可复用《{bm['title']}》的冲突公式结构",
                    "reusability_score": features.story_core.conflict_formula.reusability_score,
                })
            
            # 2. 可复用的配角模板
            for role in features.character_analysis.supporting_roles[:2]:
                if role.reusability_score > 0.8:
                    reusables.append({
                        "element": "配角模板",
                        "source": bm["title"],
                        "description": f"『{role.role_name}』类型的{role.function_type.value}配角可复用",
                        "reusability_score": role.reusability_score,
                    })
            
            # 3. 可复用的爽点节奏
            rhythm = features.story_core.hook_distribution.rhythm_pattern
            if "每" in rhythm:
                reusables.append({
                    "element": "爽点节奏",
                    "source": bm["title"],
                    "description": f"可复用节奏模式：{rhythm}",
                    "reusability_score": 0.75,
                })
        
        return reusables
    
    def _generate_suggestions(
        self,
        features: DeepNovelFeatures,
        top_benchmarks: List[tuple],
    ) -> List[Dict]:
        """生成优化建议"""
        suggestions = []
        
        # 1. 情绪钩子优化
        hook_count = features.story_core.hook_distribution.total_hooks
        if hook_count < 20:
            suggestions.append({
                "category": "情绪节奏",
                "suggestion": "情绪钩子密度偏低，建议增加爽点/悬念的分布密度",
                "priority": "high",
                "reference": f"标杆作品平均钩子数：50+",
            })
        
        # 2. 金手指约束优化
        constraints = features.core_setting.golden_finger.constraints
        if len(constraints) < 2:
            suggestions.append({
                "category": "设定设计",
                "suggestion": "金手指约束条件较少，建议增加'代价/限制'类约束以提升剧情张力",
                "priority": "medium",
                "reference": "优秀作品的约束条件数：2-4个",
            })
        
        # 3. 人物弧光优化
        completion = features.character_analysis.protagonist_arc.completion_degree
        if completion < 0.6:
            suggestions.append({
                "category": "人物塑造",
                "suggestion": "人物弧光完成度不足，建议增加关键转折点",
                "priority": "high",
                "reference": f"标杆作品完成度：0.8+",
            })
        
        # 4. 商业价值优化
        if features.commercial_value.overall_commercial_score < 0.6:
            suggestions.append({
                "category": "商业潜力",
                "suggestion": "商业潜力评分偏低，建议优化受众定位或增加改编适配点",
                "priority": "medium",
                "reference": "高商业潜力作品特征：明确受众+强改编适配性",
            })
        
        return suggestions
    
    # ==================== 动态更新 ====================
    
    async def update_parsing_weights(self) -> Dict[str, float]:
        """
        基于市场数据更新解析权重
        
        例如：
        - 如果"金手指约束"类小说近期表现好，增加其解析权重
        - 如果某种"情绪钩子"点击率低，降低其权重
        
        Returns:
            更新后的权重配置
        """
        client = await self._get_client()
        
        # 聚合分析市场数据
        pipeline = [
            {"$match": {"is_active": True, "market_data": {"$exists": True}}},
            {"$sort": {"market_data.read_count": -1}},
            {"$limit": 100},
        ]
        
        top_novels = []
        async for doc in client.db[self.COLLECTION_NAME].aggregate(pipeline):
            top_novels.append(doc)
        
        # 分析高表现作品的共同特征
        weights = {
            "story_core": 0.25,
            "core_setting": 0.20,
            "character_analysis": 0.25,
            "narrative_technique": 0.20,
            "commercial_value": 0.10,
        }
        
        # TODO: 基于数据分析动态调整权重
        
        logger.info("parsing_weights_updated", weights=weights)
        return weights
    
    async def get_trending_features(
        self,
        genre: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        获取 trending 特征
        
        分析近期热门作品的共同特征
        """
        client = await self._get_client()
        
        # 获取近期热门
        since = datetime.utcnow().timestamp() - days * 86400
        
        query = {
            "is_active": True,
            "updated_at": {"$gte": datetime.fromtimestamp(since)},
        }
        if genre:
            query["genre"] = genre
        
        cursor = client.db[self.COLLECTION_NAME].find(query)
        cursor = cursor.sort("market_data.read_count", -1)
        cursor = cursor.limit(50)
        
        novels = await cursor.to_list(length=50)
        
        if not novels:
            return {"message": "暂无近期数据"}
        
        # 聚合特征
        conflict_types = {}
        gf_types = {}
        arc_types = {}
        
        for novel in novels:
            features = novel.get("features", {})
            
            # 冲突类型
            ct = features.get("story_core", {}).get("conflict_formula", {}).get("conflict_type")
            if ct:
                conflict_types[ct] = conflict_types.get(ct, 0) + 1
            
            # 金手指类型
            gt = features.get("core_setting", {}).get("golden_finger", {}).get("gf_type")
            if gt:
                gf_types[gt] = gf_types.get(gt, 0) + 1
            
            # 人物弧光
            at = features.get("character_analysis", {}).get("protagonist_arc", {}).get("arc_type")
            if at:
                arc_types[at] = arc_types.get(at, 0) + 1
        
        return {
            "period_days": days,
            "sample_count": len(novels),
            "trending_conflict_types": sorted(conflict_types.items(), key=lambda x: x[1], reverse=True)[:3],
            "trending_gf_types": sorted(gf_types.items(), key=lambda x: x[1], reverse=True)[:3],
            "trending_arc_types": sorted(arc_types.items(), key=lambda x: x[1], reverse=True)[:3],
        }
