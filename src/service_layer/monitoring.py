"""
监控告警服务
完善的监控指标和告警机制
"""
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


# ==================== Prometheus 指标 ====================

# HTTP 请求指标
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint']
)

# 解析任务指标
PARSE_TASKS_TOTAL = Counter(
    'parse_tasks_total',
    'Total parse tasks',
    ['status', 'priority']
)

PARSE_TASK_DURATION = Histogram(
    'parse_task_duration_seconds',
    'Parse task duration',
    ['stage'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

PARSE_TASKS_IN_PROGRESS = Gauge(
    'parse_tasks_in_progress',
    'Parse tasks in progress',
    ['priority']
)

# AI 调用指标
AI_CALLS_TOTAL = Counter(
    'ai_calls_total',
    'Total AI API calls',
    ['model', 'status']
)

AI_CALL_DURATION = Histogram(
    'ai_call_duration_seconds',
    'AI API call duration',
    ['model'],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

AI_TOKENS_USED = Counter(
    'ai_tokens_used_total',
    'Total tokens used',
    ['model', 'type']
)

# 数据库指标
DB_CONNECTIONS = Gauge(
    'db_connections',
    'Database connections',
    ['db_type', 'status']
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['db_type', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# 缓存指标
CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Cache operations',
    ['operation', 'status']
)

CACHE_HIT_RATIO = Gauge(
    'cache_hit_ratio',
    'Cache hit ratio'
)

# 业务指标
NOVELS_PROCESSED = Counter(
    'novels_processed_total',
    'Total novels processed',
    ['format', 'status']
)

FEATURES_EXTRACTED = Counter(
    'features_extracted_total',
    'Total features extracted',
    ['dimension']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus 监控中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method
        path = request.url.path
        
        # 记录正在处理的请求
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            
            # 记录指标
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()
        
        return response


def monitor_parse_task(stage: str):
    """解析任务监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功
                PARSE_TASK_DURATION.labels(stage=stage).observe(
                    time.time() - start_time
                )
                
                return result
            except Exception as e:
                # 记录失败
                logger.error("parse_task_failed", stage=stage, error=str(e))
                raise
        
        return wrapper
    return decorator


def monitor_ai_call(model: str):
    """AI 调用监控装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # 记录成功
                AI_CALLS_TOTAL.labels(model=model, status="success").inc()
                AI_CALL_DURATION.labels(model=model).observe(
                    time.time() - start_time
                )
                
                # 记录 token 使用（如果有）
                if hasattr(result, 'usage'):
                    AI_TOKENS_USED.labels(model=model, type="prompt").inc(
                        result.usage.prompt_tokens
                    )
                    AI_TOKENS_USED.labels(model=model, type="completion").inc(
                        result.usage.completion_tokens
                    )
                
                return result
            except Exception as e:
                # 记录失败
                AI_CALLS_TOTAL.labels(model=model, status="error").inc()
                logger.error("ai_call_failed", model=model, error=str(e))
                raise
        
        return wrapper
    return decorator


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.webhook_url = settings.monitoring.alert_webhook
        self.email = settings.monitoring.alert_email
        self.alert_history: Dict[str, float] = {}
        self.cooldown = 300  # 告警冷却时间（秒）
    
    def should_alert(self, alert_id: str) -> bool:
        """检查是否应该发送告警"""
        import time
        
        last_alert = self.alert_history.get(alert_id, 0)
        if time.time() - last_alert < self.cooldown:
            return False
        
        self.alert_history[alert_id] = time.time()
        return True
    
    async def send_alert(
        self,
        title: str,
        message: str,
        level: str = "warning",
        alert_id: Optional[str] = None,
    ):
        """发送告警"""
        if alert_id and not self.should_alert(alert_id):
            return
        
        logger.warning("alert_sent", title=title, message=message, level=level)
        
        # 发送到 Webhook
        if self.webhook_url:
            await self._send_webhook(title, message, level)
        
        # 发送到邮件
        if self.email:
            await self._send_email(title, message, level)
    
    async def _send_webhook(self, title: str, message: str, level: str):
        """发送到 Webhook"""
        try:
            import httpx
            
            payload = {
                "title": title,
                "message": message,
                "level": level,
                "timestamp": time.time(),
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(self.webhook_url, json=payload, timeout=10)
        
        except Exception as e:
            logger.error("webhook_send_failed", error=str(e))
    
    async def _send_email(self, title: str, message: str, level: str):
        """发送邮件"""
        # 这里简化处理，实际应该集成邮件服务
        pass
    
    async def check_parse_failure_rate(self):
        """检查解析失败率"""
        # 获取最近1小时的解析任务
        # 如果失败率超过阈值，发送告警
        pass
    
    async def check_ai_api_health(self):
        """检查 AI API 健康状态"""
        # 检查 AI API 调用成功率
        # 如果成功率低于阈值，发送告警
        pass
    
    async def check_queue_length(self):
        """检查队列长度"""
        # 检查 Celery 队列长度
        # 如果队列积压，发送告警
        pass


# 全局告警管理器
alert_manager = AlertManager()


def get_metrics() -> bytes:
    """获取 Prometheus 指标"""
    return generate_latest()


def get_metrics_content_type() -> str:
    """获取指标 Content-Type"""
    return CONTENT_TYPE_LATEST
