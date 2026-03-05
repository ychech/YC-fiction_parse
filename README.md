# 小说反向解析系统

将非结构化小说文本转化为结构化特征库的工程化系统。

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (Application)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Web API    │  │  管理后台    │  │   Python SDK     │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        服务层 (Service)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  任务调度    │  │   REST API   │  │   监控告警       │  │
│  │  (Celery)    │  │  (FastAPI)   │  │  (Prometheus)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        处理层 (Processing)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  文本预处理  │  │  特征提取    │  │   结果融合       │  │
│  │  (Parser)    │  │(Rule + AI)   │  │  (Fusion)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        数据层 (Data)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  PostgreSQL  │  │   MongoDB    │  │     Redis        │  │
│  │  (元信息)    │  │  (解析结果)  │  │    (缓存)        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 核心特性

- **多格式支持**: TXT, EPUB, MOBI
- **双引擎解析**: 规则引擎 + AI 引擎，结果融合
- **高性能**: 异步处理，批量解析，增量更新
- **可扩展**: 插件化架构，支持自定义规则
- **高可用**: 容器化部署，自动扩缩容

## 快速开始

### 环境要求

- Python 3.10+
- PostgreSQL 15+
- MongoDB 7+
- Redis 7+

### 本地开发

```bash
# 1. 克隆仓库
git clone <repo-url>
cd novel-parser

# 2. 安装依赖
poetry install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 4. 启动数据库
docker-compose -f deployments/docker/docker-compose.yml up -d postgres mongo redis

# 5. 初始化数据库
poetry run alembic upgrade head

# 6. 启动服务
poetry run uvicorn src.application_layer.api.main:app --reload

# 7. 启动 Celery Worker
poetry run celery -A src.service_layer.celery_app worker -l info
```

### Docker 部署

```bash
# 使用 Docker Compose 一键部署
cd deployments/docker
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### Kubernetes 部署

```bash
# 应用所有配置
kubectl apply -f deployments/k8s/

# 查看 Pod 状态
kubectl get pods -n novel-parser

# 查看服务
kubectl get svc -n novel-parser
```

## API 使用

### 上传小说

```bash
curl -X POST "http://localhost:8000/api/v1/novels/upload" \
  -H "accept: application/json" \
  -F "file=@novel.txt" \
  -F "title=小说标题" \
  -F "author=作者名"
```

### 查询解析结果

```bash
curl "http://localhost:8000/api/v1/novels/{novel_id}?include_features=true"
```

### 搜索小说

```bash
curl -X POST "http://localhost:8000/api/v1/search/features" \
  -H "Content-Type: application/json" \
  -d '{
    "world_type": "修仙",
    "task_structure": "升级流",
    "page": 1,
    "page_size": 20
  }'
```

## 项目结构

```
novel-parser/
├── src/
│   ├── application_layer/     # 应用层
│   │   └── api/               # REST API
│   ├── service_layer/         # 服务层
│   │   ├── tasks/             # Celery 任务
│   │   └── celery_app.py      # Celery 配置
│   ├── processing_layer/      # 处理层
│   │   ├── parsers/           # 文本解析器
│   │   ├── extractors/        # 特征提取器
│   │   ├── fusion/            # 结果融合
│   │   └── pipeline.py        # 处理流水线
│   ├── data_layer/            # 数据层
│   │   ├── models.py          # ORM 模型
│   │   ├── repositories.py    # 数据访问
│   │   ├── mongo_client.py    # MongoDB 客户端
│   │   ├── cache.py           # Redis 缓存
│   │   └── storage.py         # 文件存储
│   ├── common/                # 公共模块
│   │   ├── schemas.py         # 数据模型
│   │   ├── exceptions.py      # 异常定义
│   │   └── logger.py          # 日志配置
│   └── config/                # 配置
│       └── settings.py        # 系统配置
├── deployments/               # 部署配置
│   ├── docker/                # Docker 配置
│   └── k8s/                   # Kubernetes 配置
├── tests/                     # 测试
└── docs/                      # 文档
```

## 核心指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 解析准确率 | ≥85% | 特征提取与人工标注的匹配度 |
| 单本解析耗时 | ≤5分钟 | 百万字小说 |
| 并发解析能力 | ≥10本/批次 | 批量处理 |

## 开发计划

### MVP 阶段
- [x] 基础架构搭建
- [x] TXT 格式支持
- [x] 核心特征解析（任务、背景、写作手法）
- [x] 规则引擎 + OpenAI API
- [x] 简单 Web 端

### 进阶阶段
- [ ] EPUB/MOBI 格式支持
- [ ] 人设、情节结构解析
- [ ] 本地模型部署
- [ ] 批量解析功能

### 全量阶段
- [ ] 向量检索
- [ ] 相似小说分析
- [ ] 规则引擎可视化配置
- [ ] 监控告警体系
- [ ] 多端适配

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License
