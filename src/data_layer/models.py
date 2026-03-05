"""
SQLAlchemy 数据库模型定义
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool

from src.config.settings import settings

Base = declarative_base()


class NovelStatus(str, PyEnum):
    """小说状态"""
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class TaskStatus(str, PyEnum):
    """任务状态"""
    PENDING = "pending"
    PREPROCESSING = "preprocessing"
    EXTRACTING = "extracting"
    FUSING = "fusing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NovelORM(Base):
    """小说元信息表"""
    __tablename__ = "novels"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(100), nullable=True, index=True)
    genre = Column(String(50), nullable=True, index=True)
    word_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    format = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # MD5
    status = Column(Enum(NovelStatus), default=NovelStatus.ACTIVE, index=True)
    
    # 统计信息
    chapter_count = Column(Integer, default=0)
    parse_count = Column(Integer, default=0)
    last_parsed_at = Column(DateTime, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    tasks = relationship("ParseTaskORM", back_populates="novel", lazy="dynamic")
    
    __table_args__ = (
        Index('idx_novel_title_author', 'title', 'author'),
        Index('idx_novel_genre_status', 'genre', 'status'),
    )


class ParseTaskORM(Base):
    """解析任务表"""
    __tablename__ = "parse_tasks"
    
    id = Column(String(36), primary_key=True)
    novel_id = Column(String(36), ForeignKey("novels.id"), nullable=False, index=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Integer, default=2, index=True)  # 1-4
    
    # 进度信息
    progress = Column(Float, default=0.0)
    current_stage = Column(String(50), nullable=True)
    stage_progress = Column(JSON, default=dict)
    
    # 配置
    config = Column(JSON, default=dict)
    
    # 结果引用（实际结果存在MongoDB）
    result_id = Column(String(36), nullable=True, index=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_detail = Column(JSON, nullable=True)
    
    # 时间
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 性能指标
    duration_seconds = Column(Integer, nullable=True)
    
    # 关系
    novel = relationship("NovelORM", back_populates="tasks")
    
    __table_args__ = (
        Index('idx_task_status_priority', 'status', 'priority'),
        Index('idx_task_novel_status', 'novel_id', 'status'),
    )


class RuleSetORM(Base):
    """规则集表"""
    __tablename__ = "rule_sets"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    genre = Column(String(50), nullable=True, index=True)
    rules = Column(JSON, default=list)  # 规则列表
    version = Column(String(20), default="1.0")
    enabled = Column(Boolean, default=True)
    
    # 统计
    hit_count = Column(Integer, default=0)
    accuracy_rate = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserORM(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 配额
    daily_quota = Column(Integer, default=10)
    used_quota_today = Column(Integer, default=0)
    quota_reset_at = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemConfigORM(Base):
    """系统配置表"""
    __tablename__ = "system_configs"
    
    id = Column(String(36), primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 数据库引擎和会话
engine = create_engine(
    f"postgresql://{settings.db.postgres_user}:{settings.db.postgres_password}"
    f"@{settings.db.postgres_host}:{settings.db.postgres_port}/{settings.db.postgres_db}",
    poolclass=QueuePool,
    pool_size=settings.db.postgres_pool_size,
    max_overflow=10,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
