.PHONY: help install dev test lint format clean docker-build docker-up docker-down k8s-deploy k8s-delete demo

# 默认目标
help:
	@echo "小说反向解析系统 - Makefile"
	@echo ""
	@echo "快速开始:"
	@echo "  make setup        - 一键安装并启动"
	@echo "  make demo         - 运行演示"
	@echo ""
	@echo "开发命令:"
	@echo "  make install      - 安装依赖"
	@echo "  make dev          - 启动开发环境"
	@echo "  make test         - 运行测试"
	@echo "  make lint         - 代码检查"
	@echo "  make format       - 代码格式化"
	@echo ""
	@echo "Docker 命令:"
	@echo "  make docker-build - 构建 Docker 镜像"
	@echo "  make docker-up    - 启动 Docker 环境"
	@echo "  make docker-down  - 停止 Docker 环境"
	@echo "  make docker-logs  - 查看日志"
	@echo ""
	@echo "Kubernetes 命令:"
	@echo "  make k8s-deploy   - 部署到 Kubernetes"
	@echo "  make k8s-delete   - 删除 Kubernetes 部署"
	@echo "  make k8s-status   - 查看 K8s 状态"
	@echo ""
	@echo "其他命令:"
	@echo "  make clean        - 清理临时文件"
	@echo "  make migrate      - 执行数据库迁移"
	@echo "  make check        - 代码质量检查"

# ==================== 快速开始 ====================

setup:
	@echo "🚀 开始一键安装..."
	@bash scripts/setup.sh

demo:
	@echo "🎬 运行演示..."
	@python3 scripts/demo.py

# ==================== 开发命令 ====================

install:
	poetry install

dev:
	@echo "🚀 启动开发环境..."
	@docker-compose -f deployments/docker/docker-compose.yml up -d postgres mongo redis
	@sleep 3
	@echo "✓ 数据库已启动"
	@echo "📝 请确保已配置 .env 文件"
	@poetry run uvicorn src.application_layer.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	poetry run flake8 src tests
	poetry run mypy src

format:
	poetry run black src tests
	poetry run isort src tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ 清理完成"

# ==================== Docker 命令 ====================

docker-build:
	cd deployments/docker && docker-compose build

docker-up:
	cd deployments/docker && docker-compose up -d
	@echo "✓ 服务已启动"
	@echo "  API 文档: http://localhost:8000/api/docs"
	@echo "  Flower 监控: http://localhost:5555"

docker-down:
	cd deployments/docker && docker-compose down

docker-logs:
	cd deployments/docker && docker-compose logs -f

docker-logs-api:
	cd deployments/docker && docker-compose logs -f api

docker-logs-worker:
	cd deployments/docker && docker-compose logs -f worker

docker-scale-worker:
	cd deployments/docker && docker-compose up -d --scale worker=$(WORKERS)

# ==================== Kubernetes 命令 ====================

k8s-deploy:
	@echo "🚀 部署到 Kubernetes..."
	@kubectl apply -f deployments/k8s/
	@echo "✓ 部署完成"
	@echo "  查看状态: kubectl get all -n novel-parser"

k8s-delete:
	@echo "🗑️  删除 Kubernetes 部署..."
	@kubectl delete -f deployments/k8s/

k8s-status:
	@kubectl get all -n novel-parser

k8s-logs-api:
	@kubectl logs -f deployment/api-deployment -n novel-parser

k8s-logs-worker:
	@kubectl logs -f deployment/worker-deployment -n novel-parser

# ==================== 数据库命令 ====================

migrate:
	poetry run alembic upgrade head

migrate-create:
	@read -p "输入迁移名称: " name; \
	poetry run alembic revision --autogenerate -m "$$name"

db-reset:
	@echo "⚠️  警告: 这将删除所有数据!"
	@read -p "确认继续? (y/N) " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker-compose -f deployments/docker/docker-compose.yml down -v; \
		docker-compose -f deployments/docker/docker-compose.yml up -d postgres mongo redis; \
		sleep 5; \
		poetry run alembic upgrade head; \
		echo "✓ 数据库已重置"; \
	else \
		echo "已取消"; \
	fi

# ==================== Celery 命令 ====================

celery-worker:
	poetry run celery -A src.service_layer.celery_app worker -l info -Q parsing,analysis,default

celery-beat:
	poetry run celery -A src.service_layer.celery_app beat -l info

celery-flower:
	poetry run celery -A src.service_layer.celery_app flower --port=5555

celery-purge:
	poetry run celery -A src.service_layer.celery_app purge

# ==================== 代码质量 ====================

check: lint test
	@echo "✓ 代码质量检查完成"

# ==================== 文档 ====================

docs:
	@echo "生成 API 文档..."
	@poetry run python -c "from src.application_layer.api.main import app; from fastapi.openapi.utils import get_openapi; import json; print(json.dumps(get_openapi(title=app.title, version=app.version, routes=app.routes), indent=2, ensure_ascii=False))" > docs/openapi.json
	@echo "✓ API 文档已生成: docs/openapi.json"

# ==================== 备份 ====================

backup:
	@mkdir -p backups
	@docker-compose -f deployments/docker/docker-compose.yml exec -T postgres pg_dump -U novel_parser novel_parser > backups/postgres_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✓ 数据库已备份到 backups/"

# ==================== 实用工具 ====================

health-check:
	@curl -s http://localhost:8000/health | python3 -m json.tool

api-docs:
	@open http://localhost:8000/api/docs || xdg-open http://localhost:8000/api/docs || echo "请手动打开: http://localhost:8000/api/docs"

flower:
	@open http://localhost:5555 || xdg-open http://localhost:5555 || echo "请手动打开: http://localhost:5555"
