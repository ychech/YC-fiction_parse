"""
数据访问层 - Repository 模式
封装所有数据库操作，提供统一的 CRUD 接口
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, List, Optional, Type, TypeVar
from uuid import uuid4

from sqlalchemy.orm import Session

from src.common.schemas import (
    NovelCreate,
    NovelMeta,
    NovelResponse,
    ParseTask,
    ParseTaskCreate,
    RuleSet,
)
from src.data_layer.models import (
    NovelORM,
    NovelStatus,
    ParseTaskORM,
    RuleSetORM,
    TaskStatus,
)

T = TypeVar("T")
ORMType = TypeVar("ORMType")


class BaseRepository(Generic[T, ORMType], ABC):
    """基础仓储类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def _to_schema(self, orm_obj: ORMType) -> T:
        """ORM 对象转 Schema"""
        pass
    
    @abstractmethod
    def _to_orm(self, schema: T) -> ORMType:
        """Schema 转 ORM 对象"""
        pass
    
    def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取"""
        orm_obj = self.db.query(self._get_orm_class()).filter_by(id=id).first()
        return self._to_schema(orm_obj) if orm_obj else None
    
    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[T]:
        """列表查询"""
        query = self.db.query(self._get_orm_class())
        for key, value in filters.items():
            if value is not None:
                query = query.filter(getattr(self._get_orm_class(), key) == value)
        orm_objs = query.offset(skip).limit(limit).all()
        return [self._to_schema(obj) for obj in orm_objs]
    
    def create(self, schema: T) -> T:
        """创建"""
        orm_obj = self._to_orm(schema)
        if not orm_obj.id:
            orm_obj.id = str(uuid4())
        self.db.add(orm_obj)
        self.db.commit()
        self.db.refresh(orm_obj)
        return self._to_schema(orm_obj)
    
    def update(self, id: str, schema: T) -> Optional[T]:
        """更新"""
        orm_class = self._get_orm_class()
        orm_obj = self.db.query(orm_class).filter_by(id=id).first()
        if not orm_obj:
            return None
        
        for key, value in schema.dict(exclude_unset=True).items():
            if hasattr(orm_obj, key):
                setattr(orm_obj, key, value)
        
        orm_obj.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(orm_obj)
        return self._to_schema(orm_obj)
    
    def delete(self, id: str) -> bool:
        """删除"""
        orm_class = self._get_orm_class()
        result = self.db.query(orm_class).filter_by(id=id).delete()
        self.db.commit()
        return result > 0
    
    @abstractmethod
    def _get_orm_class(self) -> Type[ORMType]:
        """获取 ORM 类"""
        pass


class NovelRepository(BaseRepository[NovelResponse, NovelORM]):
    """小说仓储"""
    
    def _get_orm_class(self) -> Type[NovelORM]:
        return NovelORM
    
    def _to_schema(self, orm_obj: NovelORM) -> NovelResponse:
        return NovelResponse(
            id=orm_obj.id,
            title=orm_obj.title,
            author=orm_obj.author,
            genre=orm_obj.genre,
            word_count=orm_obj.word_count,
            description=orm_obj.description,
            cover_url=orm_obj.cover_url,
            format=orm_obj.format,
            file_path=orm_obj.file_path,
            file_size=orm_obj.file_size,
            status=orm_obj.status.value,
            created_at=orm_obj.created_at,
            updated_at=orm_obj.updated_at,
        )
    
    def _to_orm(self, schema: NovelResponse) -> NovelORM:
        return NovelORM(
            id=schema.id,
            title=schema.title,
            author=schema.author,
            genre=schema.genre.value if schema.genre else None,
            word_count=schema.word_count,
            description=schema.description,
            cover_url=schema.cover_url,
            format=schema.format.value,
            file_path=schema.file_path,
            file_size=schema.file_size,
            status=NovelStatus(schema.status) if schema.status else NovelStatus.ACTIVE,
        )
    
    def create_from_meta(self, create_data: NovelCreate, file_info: dict) -> NovelResponse:
        """从元信息创建小说"""
        novel = NovelORM(
            id=str(uuid4()),
            title=create_data.title,
            author=create_data.author,
            genre=create_data.genre.value if create_data.genre else None,
            description=create_data.description,
            format=file_info.get("format"),
            file_path=file_info.get("file_path"),
            file_size=file_info.get("file_size"),
            status=NovelStatus.ACTIVE,
        )
        self.db.add(novel)
        self.db.commit()
        self.db.refresh(novel)
        return self._to_schema(novel)
    
    def get_by_file_hash(self, file_hash: str) -> Optional[NovelResponse]:
        """根据文件hash查询"""
        orm_obj = self.db.query(NovelORM).filter_by(file_hash=file_hash).first()
        return self._to_schema(orm_obj) if orm_obj else None
    
    def update_status(self, novel_id: str, status: NovelStatus) -> bool:
        """更新状态"""
        result = self.db.query(NovelORM).filter_by(id=novel_id).update({
            "status": status,
            "updated_at": datetime.utcnow()
        })
        self.db.commit()
        return result > 0
    
    def update_parse_info(self, novel_id: str, chapter_count: int) -> bool:
        """更新解析信息"""
        result = self.db.query(NovelORM).filter_by(id=novel_id).update({
            "chapter_count": chapter_count,
            "parse_count": NovelORM.parse_count + 1,
            "last_parsed_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        self.db.commit()
        return result > 0


class ParseTaskRepository(BaseRepository[ParseTask, ParseTaskORM]):
    """解析任务仓储"""
    
    def _get_orm_class(self) -> Type[ParseTaskORM]:
        return ParseTaskORM
    
    def _to_schema(self, orm_obj: ParseTaskORM) -> ParseTask:
        return ParseTask(
            id=orm_obj.id,
            novel_id=orm_obj.novel_id,
            status=TaskStatus(orm_obj.status.value),
            priority=orm_obj.priority,
            progress=orm_obj.progress,
            current_stage=orm_obj.current_stage,
            stage_progress=orm_obj.stage_progress or {},
            config=orm_obj.config or {},
            result=None,  # 结果从MongoDB获取
            error_message=orm_obj.error_message,
            started_at=orm_obj.started_at,
            completed_at=orm_obj.completed_at,
        )
    
    def _to_orm(self, schema: ParseTask) -> ParseTaskORM:
        return ParseTaskORM(
            id=schema.id,
            novel_id=schema.novel_id,
            status=TaskStatus(schema.status.value),
            priority=schema.priority,
            progress=schema.progress,
            current_stage=schema.current_stage,
            stage_progress=schema.stage_progress,
            config=schema.config,
            error_message=schema.error_message,
            started_at=schema.started_at,
            completed_at=schema.completed_at,
        )
    
    def create_task(self, create_data: ParseTaskCreate) -> ParseTask:
        """创建任务"""
        task = ParseTaskORM(
            id=str(uuid4()),
            novel_id=create_data.novel_id,
            status=TaskStatus.PENDING,
            priority=create_data.priority,
            config=create_data.config or {},
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return self._to_schema(task)
    
    def get_pending_tasks(self, limit: int = 10) -> List[ParseTask]:
        """获取待处理任务（按优先级排序）"""
        orm_objs = self.db.query(ParseTaskORM).filter_by(
            status=TaskStatus.PENDING
        ).order_by(
            ParseTaskORM.priority.desc(),
            ParseTaskORM.created_at.asc()
        ).limit(limit).all()
        return [self._to_schema(obj) for obj in orm_objs]
    
    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        stage: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        updates = {"status": status, "updated_at": datetime.utcnow()}
        
        if progress is not None:
            updates["progress"] = progress
        if stage is not None:
            updates["current_stage"] = stage
        if error_message is not None:
            updates["error_message"] = error_message
        
        if status == TaskStatus.COMPLETED:
            updates["completed_at"] = datetime.utcnow()
        elif status == TaskStatus.PREPROCESSING and progress == 0:
            updates["started_at"] = datetime.utcnow()
        
        result = self.db.query(ParseTaskORM).filter_by(id=task_id).update(updates)
        self.db.commit()
        return result > 0
    
    def update_stage_progress(self, task_id: str, stage: str, progress: float) -> bool:
        """更新阶段进度"""
        task = self.db.query(ParseTaskORM).filter_by(id=task_id).first()
        if not task:
            return False
        
        stage_progress = task.stage_progress or {}
        stage_progress[stage] = progress
        task.stage_progress = stage_progress
        task.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True


class RuleSetRepository(BaseRepository[RuleSet, RuleSetORM]):
    """规则集仓储"""
    
    def _get_orm_class(self) -> Type[RuleSetORM]:
        return RuleSetORM
    
    def _to_schema(self, orm_obj: RuleSetORM) -> RuleSet:
        from src.common.schemas import Rule
        return RuleSet(
            id=orm_obj.id,
            name=orm_obj.name,
            description=orm_obj.description,
            genre=orm_obj.genre,
            rules=[Rule(**r) for r in (orm_obj.rules or [])],
            version=orm_obj.version,
            enabled=orm_obj.enabled,
        )
    
    def _to_orm(self, schema: RuleSet) -> RuleSetORM:
        return RuleSetORM(
            id=schema.id,
            name=schema.name,
            description=schema.description,
            genre=schema.genre.value if schema.genre else None,
            rules=[r.dict() for r in schema.rules],
            version=schema.version,
            enabled=schema.enabled,
        )
    
    def get_enabled_by_genre(self, genre: Optional[str] = None) -> List[RuleSet]:
        """获取启用的规则集"""
        query = self.db.query(RuleSetORM).filter_by(enabled=True)
        if genre:
            query = query.filter(
                (RuleSetORM.genre == genre) | (RuleSetORM.genre.is_(None))
            )
        orm_objs = query.all()
        return [self._to_schema(obj) for obj in orm_objs]
