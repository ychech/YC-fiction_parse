#!/bin/bash
# 小说反向解析系统 - 快速安装脚本

set -e

echo "=========================================="
echo "小说反向解析系统 - 快速安装"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 打印信息
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    info "检查系统要求..."
    
    # 检查 Docker
    if command_exists docker; then
        info "✓ Docker 已安装 ($(docker --version))"
    else
        error "✗ Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查 Docker Compose
    if command_exists docker-compose; then
        info "✓ Docker Compose 已 installed ($(docker-compose --version))"
    else
        error "✗ Docker Compose 未安装"
        exit 1
    fi
    
    # 检查内存
    MEMORY=$(docker system info 2>/dev/null | grep "Total Memory" | awk '{print $3}')
    if [ -n "$MEMORY" ]; then
        info "✓ 可用内存: $MEMORY"
    fi
}

# 配置环境变量
setup_env() {
    info "配置环境变量..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        warn "已创建 .env 文件，请编辑配置必要的参数"
        
        # 生成随机密钥
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i.bak "s/your-secret-key-change-in-production/$SECRET_KEY/" .env
        rm -f .env.bak
        
        # 提示用户配置
        echo ""
        echo "请编辑 .env 文件，配置以下必需项："
        echo "  - AI_OPENAI_API_KEY (必需)"
        echo "  - DB_POSTGRES_PASSWORD (建议修改)"
        echo ""
        read -p "是否现在编辑 .env 文件? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vi} .env
        fi
    else
        info "✓ .env 文件已存在"
    fi
}

# 创建必要目录
create_directories() {
    info "创建必要目录..."
    
    mkdir -p storage
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/mongo
    mkdir -p data/redis
    mkdir -p data/minio
    
    info "✓ 目录创建完成"
}

# 启动服务
start_services() {
    info "启动服务..."
    
    cd deployments/docker
    
    # 拉取镜像
    info "拉取 Docker 镜像..."
    docker-compose pull
    
    # 构建应用镜像
    info "构建应用镜像..."
    docker-compose build
    
    # 启动服务
    info "启动所有服务..."
    docker-compose up -d
    
    # 等待数据库就绪
    info "等待数据库就绪..."
    sleep 10
    
    # 检查服务状态
    info "检查服务状态..."
    docker-compose ps
    
    cd ../..
}

# 初始化数据库
init_database() {
    info "初始化数据库..."
    
    # 等待 PostgreSQL 就绪
    until docker-compose -f deployments/docker/docker-compose.yml exec -T postgres pg_isready -U novel_parser; do
        info "等待 PostgreSQL..."
        sleep 2
    done
    
    info "✓ PostgreSQL 已就绪"
    
    # 执行迁移
    info "执行数据库迁移..."
    docker-compose -f deployments/docker/docker-compose.yml exec -T api alembic upgrade head
    
    info "✓ 数据库初始化完成"
}

# 验证安装
verify_installation() {
    info "验证安装..."
    
    # 检查 API 服务
    if curl -s http://localhost:8000/health > /dev/null; then
        info "✓ API 服务运行正常"
    else
        error "✗ API 服务未响应"
        return 1
    fi
    
    # 检查 Flower
    if curl -s http://localhost:5555 > /dev/null; then
        info "✓ Flower 监控运行正常"
    else
        warn "⚠ Flower 监控未响应"
    fi
    
    echo ""
    echo "=========================================="
    echo -e "${GREEN}安装完成！${NC}"
    echo "=========================================="
    echo ""
    echo "服务地址："
    echo "  - API 文档: http://localhost:8000/api/docs"
    echo "  - Flower 监控: http://localhost:5555"
    echo "  - MinIO 控制台: http://localhost:9001"
    echo ""
    echo "常用命令："
    echo "  查看日志: docker-compose -f deployments/docker/docker-compose.yml logs -f"
    echo "  停止服务: docker-compose -f deployments/docker/docker-compose.yml down"
    echo "  重启服务: docker-compose -f deployments/docker/docker-compose.yml restart"
    echo ""
    echo "开始使用："
    echo "  1. 访问 http://localhost:8000/api/docs 查看 API 文档"
    echo "  2. 使用 POST /api/v1/novels/upload 上传小说"
    echo "  3. 使用 POST /api/v1/deep/{novel_id}/deep-parse 执行深度解析"
    echo ""
}

# 主函数
main() {
    echo ""
    
    # 检查是否在项目根目录
    if [ ! -f "pyproject.toml" ]; then
        error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行安装步骤
    check_requirements
    setup_env
    create_directories
    start_services
    init_database
    verify_installation
}

# 运行主函数
main "$@"
