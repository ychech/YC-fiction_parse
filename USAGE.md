# 小说反向解析系统 - 使用与部署指南

## 📋 目录

1. [快速开始](#快速开始)
2. [本地开发部署](#本地开发部署)
3. [Docker 部署](#docker-部署)
4. [Kubernetes 部署](#kubernetes-部署)
5. [API 使用指南](#api-使用指南)
6. [系统配置](#系统配置)
7. [常见问题](#常见问题)

---

## 快速开始

### 环境要求

- **Python**: 3.10+
- **数据库**: PostgreSQL 15+, MongoDB 7+, Redis 7+
- **可选**: MinIO (对象存储)

### 一键启动（Docker Compose）

```bash
# 1. 克隆项目
git clone <repo-url>
cd novel-parser

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，设置必要的配置项

# 3. 启动所有服务
cd deployments/docker
docker-compose up -d

# 4. 查看服务状态
docker-compose ps

# 5. 访问 API 文档
open http://localhost:8000/api/docs
```

---

## 本地开发部署

### 1. 安装依赖

```bash
# 安装 Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 2. 启动基础设施

```bash
# 使用 Docker 启动数据库
docker-compose -f deployments/docker/docker-compose.yml up -d postgres mongo redis

# 或者使用本地安装的数据库
# 确保 PostgreSQL、MongoDB、Redis 已启动
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置以下关键项：
```

**.env 关键配置：**

```env
# 基础配置
ENV=development
DEBUG=true

# 数据库配置
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_USER=novel_parser
DB_POSTGRES_PASSWORD=your_password
DB_POSTGRES_DB=novel_parser

DB_MONGODB_URL=mongodb://localhost:27017/novel_parser

DB_REDIS_HOST=localhost
DB_REDIS_PORT=6379

# AI 配置（必需）
AI_OPENAI_API_KEY=sk-your-openai-api-key
AI_OPENAI_MODEL=gpt-3.5-turbo

# 存储配置
DB_STORAGE_TYPE=local
DB_LOCAL_STORAGE_PATH=./storage
```

### 4. 初始化数据库

```bash
# 创建数据库表
poetry run alembic upgrade head

# 或者使用 Makefile
make migrate
```

### 5. 启动服务

**终端 1 - 启动 API 服务：**
```bash
poetry run uvicorn src.application_layer.api.main:app --reload --host 0.0.0.0 --port 8000

# 或者
make dev
```

**终端 2 - 启动 Celery Worker：**
```bash
poetry run celery -A src.service_layer.celery_app worker -l info -Q parsing,analysis,default

# 或者
make celery-worker
```

**终端 3 - 启动 Celery Beat（定时任务）：**
```bash
poetry run celery -A src.service_layer.celery_app beat -l info

# 或者
make celery-beat
```

### 6. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 查看 API 文档
open http://localhost:8000/api/docs
```

---

## Docker 部署

### 生产环境部署

```bash
cd deployments/docker

# 1. 配置生产环境变量
vim .env

# 2. 构建镜像
docker-compose build

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f api
docker-compose logs -f worker

# 5. 停止服务
docker-compose down

# 6. 完全清理（包括数据卷）
docker-compose down -v
```

### 服务架构

```
docker-compose 部署架构：

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   API 服务   │  │ Celery Worker│  │ Celery Beat │
│   :8000     │  │   (x2)      │  │             │
└──────┬──────┘  └──────┬──────┘  └─────────────┘
       │                │
       └────────────────┘
              │
       ┌──────┴──────┐
       │   Redis     │
       │  :6379      │
       └──────┬──────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───┴───┐ ┌───┴───┐ ┌───┴────┐
│Postgre│ │MongoDB│ │ MinIO  │
│SQL:5432│ │:27017 │ │:9000   │
└───────┘ └───────┘ └────────┘
```

### 扩展 Worker 数量

```bash
# 水平扩展 Worker
docker-compose up -d --scale worker=4
```

---

## Kubernetes 部署

### 前置要求

- Kubernetes 1.24+
- kubectl
- Helm 3（可选）

### 部署步骤

```bash
cd deployments/k8s

# 1. 创建命名空间
kubectl apply -f namespace.yaml

# 2. 创建配置和密钥
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
# 注意：编辑 secret.yaml，设置真实的密码和 API Key

# 3. 部署数据库（或使用现有数据库）
# 如果使用外部数据库，跳过此步骤

# 4. 部署应用
kubectl apply -f api-deployment.yaml
kubectl apply -f worker-deployment.yaml

# 5. 部署 HPA（自动扩缩容）
kubectl apply -f hpa.yaml

# 6. 部署 Ingress
kubectl apply -f ingress.yaml

# 7. 查看部署状态
kubectl get all -n novel-parser

# 8. 查看日志
kubectl logs -f deployment/api-deployment -n novel-parser
kubectl logs -f deployment/worker-deployment -n novel-parser
```

### 常用命令

```bash
# 查看 Pod 状态
kubectl get pods -n novel-parser

# 查看服务
kubectl get svc -n novel-parser

# 扩容 Worker
kubectl scale deployment worker-deployment --replicas=5 -n novel-parser

# 进入 Pod 调试
kubectl exec -it <pod-name> -n novel-parser -- /bin/bash

# 删除部署
kubectl delete -f deployments/k8s/
```

---

## API 使用指南

### 1. 上传小说

```bash
# 上传 TXT 文件
curl -X POST "http://localhost:8000/api/v1/novels/upload" \
  -F "file=@/path/to/your/novel.txt" \
  -F "title=我的小说" \
  -F "author=作者名" \
  -F "auto_parse=true"

# 响应
{
  "code": 200,
  "data": {
    "novel": {
      "id": "novel-uuid",
      "title": "我的小说",
      ...
    },
    "task_id": "task-uuid",
    "auto_parse": true
  }
}
```

### 2. 基础解析

```bash
# 查询解析任务状态
curl "http://localhost:8000/api/v1/tasks/{task_id}"

# 获取小说基础特征
curl "http://localhost:8000/api/v1/novels/{novel_id}?include_features=true"
```

### 3. 深度解析（核心功能）

```bash
# 执行深度解析（五大维度）
curl -X POST "http://localhost:8000/api/v1/deep/{novel_id}/deep-parse" \
  -H "Content-Type: application/json" \
  -d '{
    "compare_with_benchmark": true
  }'

# 获取深度解析结果
curl "http://localhost:8000/api/v1/deep/{novel_id}/deep-features"

# 获取公式化总结
curl "http://localhost:8000/api/v1/deep/{novel_id}/formula-summary"

# 获取对比分析报告
curl "http://localhost:8000/api/v1/deep/{novel_id}/comparison-report"
```

### 4. 深度解析响应示例

```json
{
  "code": 200,
  "data": {
    "novel_id": "xxx",
    "deep_features": {
      "story_core": {
        "conflict_formula": {
          "formula_name": "底层逆袭公式",
          "protagonist_desire": "摆脱底层身份，获得尊重和地位",
          "core_obstacle": "资源匮乏、权力压制、阶层固化",
          "solution_path": "金手指/认知差/贵人相助",
          "reusability_score": 0.85
        },
        "hook_distribution": {
          "rhythm_pattern": "每3章1个小爽点，每10章1个大爽点",
          "total_hooks": 156
        },
        "core_attraction": "以『底层逆袭公式』为核心冲突..."
      },
      "core_setting": {
        "golden_finger": {
          "gf_type": "system",
          "growth_type": "dynamic_linear",
          "innovation_points": ["使用'情绪值'作为系统兑换资源"]
        }
      },
      "overall_quality_score": 0.82,
      "consistency_check": 0.91
    },
    "formula_summary": "「底层逆袭公式」+「系统金手指(动态+情绪值约束)」+「爽点节奏(3小1大)」+「学生受众(付费点:打脸爽点)」"
  }
}
```

### 5. 标杆库管理

```bash
# 添加标杆小说
curl -X POST "http://localhost:8000/api/v1/deep/benchmarks" \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "xxx",
    "title": "斗破苍穹",
    "author": "天蚕土豆",
    "genre": "玄幻",
    "market_data": {
      "read_count": 10000000,
      "rating": 4.5
    }
  }'

# 获取 trending 特征
curl "http://localhost:8000/api/v1/deep/trending-features?genre=玄幻&days=30"
```

### 6. 搜索

```bash
# 按特征搜索
curl -X POST "http://localhost:8000/api/v1/search/features" \
  -H "Content-Type: application/json" \
  -d '{
    "world_type": "修仙",
    "task_structure": "升级流",
    "min_confidence": 0.7
  }'

# 查找相似小说
curl "http://localhost:8000/api/v1/search/similar/{novel_id}?limit=5"
```

---

## 系统配置

### 环境变量完整列表

```env
# ==================== 基础配置 ====================
ENV=development                    # 环境: development/staging/production
DEBUG=true                         # 调试模式
APP_NAME=novel-parser
APP_VERSION=0.1.0

# ==================== 数据库配置 ====================
# PostgreSQL
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_USER=novel_parser
DB_POSTGRES_PASSWORD=password
DB_POSTGRES_DB=novel_parser

# MongoDB
DB_MONGODB_URL=mongodb://localhost:27017/novel_parser

# Redis
DB_REDIS_HOST=localhost
DB_REDIS_PORT=6379
DB_REDIS_DB=0

# 存储类型: local/minio/oss
DB_STORAGE_TYPE=local
DB_LOCAL_STORAGE_PATH=./storage

# MinIO (可选)
DB_MINIO_ENDPOINT=localhost:9000
DB_MINIO_ACCESS_KEY=minioadmin
DB_MINIO_SECRET_KEY=minioadmin
DB_MINIO_BUCKET=novels

# ==================== AI 配置 ====================
# OpenAI (必需)
AI_OPENAI_API_KEY=sk-your-key
AI_OPENAI_BASE_URL=https://api.openai.com/v1
AI_OPENAI_MODEL=gpt-3.5-turbo
AI_OPENAI_MAX_TOKENS=4000
AI_OPENAI_TEMPERATURE=0.3

# 本地模型 (可选)
AI_USE_LOCAL_MODEL=false
AI_LOCAL_MODEL_PATH=/path/to/model
AI_LOCAL_MODEL_DEVICE=cuda

# 向量模型
AI_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 并发控制
AI_MAX_CONCURRENT_CALLS=5
AI_REQUEST_TIMEOUT=120

# ==================== Celery 配置 ====================
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# ==================== 处理配置 ====================
# 文本处理
PROC_CHUNK_SIZE=2000
PROC_CHUNK_OVERLAP=200
PROC_MAX_WORKERS=4

# 解析引擎开关
PROC_ENABLE_RULE_ENGINE=true
PROC_ENABLE_AI_ENGINE=true
PROC_ENABLE_FUSION=true

# ==================== 安全配置 ====================
SECURITY_SECRET_KEY=your-secret-key
SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30
SECURITY_RATE_LIMIT_PER_MINUTE=60
SECURITY_MAX_UPLOAD_SIZE=104857600  # 100MB

# ==================== 监控配置 ====================
MONITOR_ENABLE_PROMETHEUS=true
MONITOR_PROMETHEUS_PORT=9090
MONITOR_LOG_LEVEL=INFO
MONITOR_LOG_FORMAT=json

# Sentry (可选)
MONITOR_SENTRY_DSN=
```

---

## 常见问题

### Q1: 启动时报数据库连接错误

```bash
# 检查数据库是否启动
docker-compose ps

# 检查连接配置
cat .env | grep DB_

# 测试 PostgreSQL 连接
psql -h localhost -U novel_parser -d novel_parser

# 测试 MongoDB 连接
mongosh mongodb://localhost:27017/novel_parser

# 测试 Redis 连接
redis-cli ping
```

### Q2: Celery Worker 不消费任务

```bash
# 检查 Redis 连接
celery -A src.service_layer.celery_app inspect ping

# 查看队列状态
celery -A src.service_layer.celery_app inspect active

# 重启 Worker
docker-compose restart worker
```

### Q3: AI 解析失败

```bash
# 检查 API Key 是否设置
echo $AI_OPENAI_API_KEY

# 测试 OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $AI_OPENAI_API_KEY"

# 查看错误日志
docker-compose logs -f worker | grep ERROR
```

### Q4: 文件上传失败

```bash
# 检查存储目录权限
ls -la ./storage

# 检查文件大小限制
cat .env | grep MAX_UPLOAD_SIZE

# 检查磁盘空间
df -h
```

### Q5: 如何清理数据

```bash
# 清理解析任务（保留7天）
curl -X POST "http://localhost:8000/api/v1/admin/maintenance/cleanup" \
  -d '{"days": 7}'

# 或者使用 Celery 任务
docker-compose exec worker celery -A src.service_layer.celery_app call src.service_layer.tasks.parse_tasks.cleanup_old_tasks -k '{"days": 7}'

# 完全重置数据库
docker-compose down -v
docker-compose up -d postgres mongo redis
poetry run alembic upgrade head
```

### Q6: 性能优化

```bash
# 1. 增加 Worker 数量
docker-compose up -d --scale worker=4

# 2. 调整并发设置
# 编辑 .env
AI_MAX_CONCURRENT_CALLS=10
PROC_MAX_WORKERS=8

# 3. 启用本地模型（减少 API 调用）
AI_USE_LOCAL_MODEL=true
AI_LOCAL_MODEL_PATH=/path/to/qwen-7b

# 4. 使用缓存
# Redis 已默认启用，确保 REDIS 配置正确
```

---

## 监控与运维

### 查看指标

```bash
# Prometheus 指标
curl http://localhost:8000/metrics

# Flower (Celery 监控)
open http://localhost:5555

# API 文档
open http://localhost:8000/api/docs
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f api
docker-compose logs -f worker

# 导出日志
docker-compose logs > logs.txt
```

### 备份与恢复

```bash
# 备份 PostgreSQL
docker-compose exec postgres pg_dump -U novel_parser novel_parser > backup.sql

# 备份 MongoDB
docker-compose exec mongo mongodump --out /data/backup

# 恢复 PostgreSQL
docker-compose exec -T postgres psql -U novel_parser novel_parser < backup.sql
```

---

## 更多资源

- [深度解析系统文档](./docs/DEEP_ANALYSIS.md)
- [API 文档](http://localhost:8000/api/docs)
- [项目 README](./README.md)
