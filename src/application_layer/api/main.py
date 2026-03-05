"""
FastAPI 主应用
"""
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.common.exceptions import NovelParserException
from src.common.logger import configure_logging, get_logger
from src.config.settings import settings
from src.data_layer.cache import cache_client
from src.data_layer.mongo_client import mongo_client

# 配置日志
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("application_starting", version=settings.app_version)
    
    # 连接数据库
    await mongo_client.connect()
    await cache_client.connect()
    
    logger.info("application_started")
    
    yield
    
    # 关闭
    logger.info("application_shutting_down")
    
    await mongo_client.close()
    await cache_client.close()
    
    logger.info("application_shutdown_complete")


# 创建应用
app = FastAPI(
    title="小说反向解析系统 API",
    description="将非结构化小说文本转化为结构化特征库",
    version=settings.app_version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 中间件 ==========

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """请求中间件"""
    # 生成请求ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # 记录请求开始时间
    start_time = time.time()
    
    # 记录请求
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else None,
    )
    
    try:
        response = await call_next(request)
        
        # 计算耗时
        duration = time.time() - start_time
        
        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            "request_completed",
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        
        return response
        
    except Exception as exc:
        duration = time.time() - start_time
        
        logger.error(
            "request_failed",
            request_id=request_id,
            error=str(exc),
            duration_ms=round(duration * 1000, 2),
        )
        
        raise


# ========== 异常处理 ==========

@app.exception_handler(NovelParserException)
async def novel_parser_exception_handler(request: Request, exc: NovelParserException):
    """处理业务异常"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "business_exception",
        request_id=request_id,
        code=exc.code,
        message=exc.message,
    )
    
    return JSONResponse(
        status_code=exc.code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "Internal server error",
            "request_id": request_id,
        },
    )


# ========== 路由 ==========

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": time.time(),
    }


@app.get("/api/v1/stats")
async def get_stats():
    """获取系统统计"""
    # 这里应该查询数据库获取真实统计
    return {
        "novels_count": 0,
        "tasks_count": 0,
        "parsing_success_rate": 0,
        "avg_parsing_time": 0,
    }


# 导入并注册路由
from src.application_layer.api.routes import novels, tasks, search, admin, deep_analysis

app.include_router(novels.router, prefix="/api/v1/novels", tags=["小说管理"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["解析任务"])
app.include_router(search.router, prefix="/api/v1/search", tags=["检索"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["管理后台"])
app.include_router(deep_analysis.router, prefix="/api/v1/deep", tags=["深度解析"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
