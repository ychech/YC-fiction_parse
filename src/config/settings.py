"""
系统配置管理
支持环境变量、配置文件、默认值的多层配置
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    # PostgreSQL - 元信息存储
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "novel_parser"
    postgres_password: str = "password"
    postgres_db: str = "novel_parser"
    postgres_pool_size: int = 20
    
    # MongoDB - 解析结果存储
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "novel_parser"
    mongodb_max_pool_size: int = 50
    
    # Redis - 缓存
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_pool_size: int = 100
    
    # MinIO/OSS - 文件存储
    storage_type: str = "local"  # local/minio/oss
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "novels"
    local_storage_path: str = "./storage"


class AISettings(BaseSettings):
    """AI/大模型配置"""
    model_config = SettingsConfigDict(env_prefix="AI_")
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.3
    
    # 本地模型
    local_model_path: Optional[str] = None
    local_model_device: str = "cuda"  # cuda/cpu
    use_local_model: bool = False
    
    # 向量模型
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    vector_dimension: int = 384
    
    # 并发控制
    max_concurrent_calls: int = 5
    request_timeout: int = 120
    retry_attempts: int = 3


class ProcessingSettings(BaseSettings):
    """处理层配置"""
    model_config = SettingsConfigDict(env_prefix="PROC_")
    
    # 文本切分
    chunk_size: int = 2000  # 每块字符数
    chunk_overlap: int = 200  # 重叠字符数
    max_chapters_per_batch: int = 50
    
    # 性能控制
    max_workers: int = 4
    batch_size: int = 10
    
    # 解析策略
    enable_rule_engine: bool = True
    enable_ai_engine: bool = True
    enable_fusion: bool = True
    
    # 增量解析
    enable_incremental: bool = True
    chapter_hash_ttl: int = 86400 * 30  # 30天


class CelerySettings(BaseSettings):
    """Celery任务队列配置"""
    model_config = SettingsConfigDict(env_prefix="CELERY_")
    
    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/2"
    task_serializer: str = "json"
    accept_content: List[str] = Field(default=["json"])
    result_serializer: str = "json"
    timezone: str = "Asia/Shanghai"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 3600  # 1小时
    worker_prefetch_multiplier: int = 1
    worker_max_tasks_per_child: int = 1000


class VectorDBSettings(BaseSettings):
    """向量数据库配置"""
    model_config = SettingsConfigDict(env_prefix="VECTOR_")
    
    backend: str = "faiss"  # faiss/milvus
    
    # Milvus配置
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "novel_vectors"
    
    # FAISS配置
    faiss_index_path: str = "./data/faiss_index"


class MonitoringSettings(BaseSettings):
    """监控告警配置"""
    model_config = SettingsConfigDict(env_prefix="MONITOR_")
    
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    
    # Sentry
    sentry_dsn: Optional[str] = None
    
    # 告警
    alert_webhook: Optional[str] = None
    alert_email: Optional[str] = None
    
    # 日志
    log_level: str = "INFO"
    log_format: str = "json"  # json/text


class SecuritySettings(BaseSettings):
    """安全配置"""
    model_config = SettingsConfigDict(env_prefix="SECURITY_")
    
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # 限流
    rate_limit_per_minute: int = 60
    
    # 文件上传
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: List[str] = Field(default=[".txt", ".epub", ".mobi"])


class Settings(BaseSettings):
    """全局配置"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    app_name: str = "novel-parser"
    app_version: str = "0.1.0"
    debug: bool = False
    env: str = "development"  # development/staging/production
    
    # 子配置
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    ai: AISettings = Field(default_factory=AISettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    vector: VectorDBSettings = Field(default_factory=VectorDBSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    
    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"env must be one of {allowed}")
        return v


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 全局配置实例
settings = get_settings()
