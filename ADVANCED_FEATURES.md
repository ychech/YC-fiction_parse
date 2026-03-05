# 进阶功能文档

## 概述

本文档介绍小说反向解析系统的进阶功能，包括完整格式支持、本地模型部署、向量检索、批量处理等。

---

## 1. 完整格式支持

### EPUB 解析器 v2

支持 EPUB2/EPUB3 标准，处理复杂目录结构。

```python
from src.processing_layer.parsers import EpubParserV2

parser = EpubParserV2()
result = await parser.parse(file_data)
```

**特性**:
- 解析 OPF 元数据
- 处理 NCX/NAV 目录
- 提取封面图片
- 支持多文件章节
- 清理样式和脚本

### MOBI 解析器 v2

支持 MOBI、AZW、AZW3 格式。

```python
from src.processing_layer.parsers import MobiParserV2

parser = MobiParserV2()
result = await parser.parse(file_data)
```

**特性**:
- 解析 PalmDOC 头
- 处理 MOBI 和 EXTH 头
- 支持文本解压
- 自动编码检测
- 元数据提取

---

## 2. 本地模型部署

### vLLM 部署

适合高吞吐量场景，支持多 GPU。

**启动 vLLM 服务**:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen-7B-Chat \
  --tensor-parallel-size 2 \
  --port 8000
```

**配置**:
```env
AI_USE_LOCAL_MODEL=true
AI_LOCAL_MODEL_TYPE=vllm
AI_VLLM_BASE_URL=http://localhost:8000/v1
AI_VLLM_MODEL=Qwen-7B-Chat
```

**使用**:
```python
from src.processing_layer.local_models import VLLMClient

client = VLLMClient()
response = await client.generate("解析这段文本...")
```

### llama.cpp 部署

适合低资源场景，支持 GGUF 量化模型。

**启动 llama.cpp 服务**:
```bash
./server \
  -m models/qwen-7b-chat-q4_k_m.gguf \
  --port 8080 \
  -ngl 35
```

**配置**:
```env
AI_USE_LOCAL_MODEL=true
AI_LOCAL_MODEL_TYPE=llamacpp
AI_LLAMACPP_BASE_URL=http://localhost:8080
AI_LLAMACPP_MODEL_PATH=/path/to/model.gguf
```

**使用**:
```python
from src.processing_layer.local_models import LlamaCppClient

client = LlamaCppClient()
response = await client.generate("解析这段文本...")
```

### 模型管理器

统一管理多种本地模型:

```python
from src.processing_layer.local_models import model_manager

# 初始化
await model_manager.initialize()

# 生成文本
response = await model_manager.generate("解析这段文本...")

# 批量生成
responses = await model_manager.generate_batch(["文本1", "文本2"])
```

---

## 3. 向量检索系统

### FAISS 存储

适合单机部署，无需外部服务。

```python
from src.vector_store import FAISSStore

store = FAISSStore(index_path="./data/faiss")
await store.connect()

# 创建集合
await store.create_collection("novels", dimension=384)

# 插入向量
ids = await store.insert(
    collection_name="novels",
    vectors=[[0.1, 0.2, ...]],
    metadata=[{"title": "小说1"}],
)

# 搜索
results = await store.search(
    collection_name="novels",
    query_vector=[0.1, 0.2, ...],
    top_k=10,
)
```

### Milvus 存储

适合大规模数据，分布式部署。

```python
from src.vector_store import MilvusStore

store = MilvusStore(host="localhost", port=19530)
await store.connect()

# 创建集合
await store.create_collection("novels", dimension=384)

# 搜索（支持过滤）
results = await store.search(
    collection_name="novels",
    query_vector=[0.1, 0.2, ...],
    filters={"genre": "玄幻"},
)
```

### 向量服务

高级封装，自动特征提取:

```python
from src.vector_store import vector_service

# 初始化
await vector_service.initialize()

# 添加小说
await vector_service.add_novel(novel_id, features)

# 搜索相似小说
results = await vector_service.search_similar(
    query_features=features,
    top_k=10,
)

# 查找与某小说相似的小说
results = await vector_service.find_similar_by_novel(
    novel_id="xxx",
    top_k=10,
)
```

---

## 4. 批量处理优化

### 批量解析

```python
from src.processing_layer.batch_processor import NovelBatchProcessor

processor = NovelBatchProcessor()

# 批量解析
results = await processor.parse_novels_batch(
    novel_ids=["id1", "id2", "id3"],
    parse_type="deep",
)
```

### 目录批量解析

```python
# 自动上传并解析
results = await processor.parse_directory(
    directory="/path/to/novels",
    pattern="*.txt",
    auto_upload=True,
)
```

### 批量处理器特性

- **动态批次大小**: 根据系统负载自动调整
- **失败重试**: 自动重试失败的任务
- **进度追踪**: 实时显示处理进度
- **并发控制**: 限制并发数避免过载
- **流式处理**: 实时返回处理结果

---

## 5. 监控告警

### Prometheus 指标

```python
from src.service_layer.monitoring import (
    HTTP_REQUESTS_TOTAL,
    PARSE_TASK_DURATION,
    AI_CALLS_TOTAL,
)

# 自动收集的指标:
# - HTTP 请求数和延迟
# - 解析任务数和耗时
# - AI 调用数和延迟
# - 数据库查询耗时
# - 缓存命中率
```

### 自定义监控

```python
from src.service_layer.monitoring import monitor_parse_task, monitor_ai_call

@monitor_parse_task(stage="feature_extraction")
async def extract_features(...):
    ...

@monitor_ai_call(model="gpt-3.5-turbo")
async def call_ai_api(...):
    ...
```

### 告警管理

```python
from src.service_layer.monitoring import alert_manager

# 发送告警
await alert_manager.send_alert(
    title="解析失败率过高",
    message="最近1小时解析失败率超过20%",
    level="warning",
)
```

### 查看指标

```bash
# Prometheus 指标
curl http://localhost:8000/metrics

# Flower 监控
open http://localhost:5555
```

---

## 6. 缓存优化

### 多级缓存

```python
from src.processing_layer.cache_optimizer import cache_optimizer

# 初始化
await cache_optimizer.initialize()

# 获取或设置缓存
result = await cache_optimizer.get_or_set(
    key="novel:features:123",
    getter=lambda: get_features_from_db(),
    ttl=3600,
)
```

### 缓存装饰器

```python
@cache_optimizer.cached(prefix="novel", ttl=3600)
async def get_novel_features(novel_id: str):
    return await db.get_features(novel_id)
```

### 缓存预热

```python
await cache_optimizer.warm_up({
    "popular:novels": get_popular_novels,
    "trending:features": get_trending_features,
})
```

---

## 7. 性能优化建议

### 解析性能

1. **使用本地模型**: 减少 API 调用延迟
2. **启用缓存**: 避免重复解析
3. **批量处理**: 提高吞吐量
4. **核心章节优先**: 快速生成基础特征

### 部署优化

1. **水平扩展 Worker**: 增加并发处理能力
2. **使用 GPU**: 加速 AI 推理
3. **分离服务**: API 和 Worker 独立部署
4. **数据库优化**: 索引和连接池

### 配置示例

```env
# 性能配置
PROC_MAX_WORKERS=8
AI_MAX_CONCURRENT_CALLS=10
DB_POSTGRES_POOL_SIZE=50

# 缓存配置
CACHE_TTL=7200
CACHE_MEMORY_SIZE=10000

# 批处理配置
BATCH_SIZE=20
BATCH_RETRY_ATTEMPTS=3
```

---

## 8. API 新增接口

### 批量解析接口

```bash
POST /api/v1/batch/parse
{
    "novel_ids": ["id1", "id2", "id3"],
    "parse_type": "deep",
    "priority": 2
}
```

### 向量搜索接口

```bash
POST /api/v1/vector/search
{
    "novel_id": "xxx",
    "top_k": 10,
    "filters": {"genre": "玄幻"}
}
```

### 相似小说查找

```bash
GET /api/v1/vector/similar/{novel_id}?top_k=10
```

---

## 9. 部署架构建议

### 小型部署 (单机)

```
[Docker Compose]
├── API (1实例)
├── Worker (2-4实例)
├── PostgreSQL
├── MongoDB
├── Redis
└── FAISS (本地存储)
```

### 中型部署 (多机)

```
[Kubernetes]
├── API (2-4 Pod, HPA)
├── Worker (4-10 Pod, HPA)
├── PostgreSQL (主从)
├── MongoDB (副本集)
├── Redis (集群)
├── Milvus (分布式)
└── vLLM (GPU节点)
```

### 大型部署 (分布式)

```
[多集群]
├── 解析集群 (多个 Worker 集群)
├── AI推理集群 (vLLM/llama.cpp 集群)
├── 存储集群 (MongoDB分片)
├── 向量集群 (Milvus分布式)
└── CDN (静态资源)
```

---

## 10. 故障排查

### 常见问题

**Q: 本地模型加载失败**
```bash
# 检查模型文件
ls -lh /path/to/model.gguf

# 检查显存
nvidia-smi

# 测试服务
curl http://localhost:8080/health
```

**Q: 向量搜索返回空结果**
```bash
# 检查集合是否存在
# 检查向量维度是否匹配
# 检查索引是否创建
```

**Q: 批量处理速度慢**
```bash
# 检查 Worker 数量
docker-compose ps

# 检查队列长度
celery -A src.service_layer.celery_app inspect active

# 增加并发
make docker-scale-worker WORKERS=10
```

---

更多详细信息请参考各模块的源码注释。
