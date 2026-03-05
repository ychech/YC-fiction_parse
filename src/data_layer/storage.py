"""
文件存储层 - 支持本地/MinIO/OSS
"""
import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

import aiofiles

from src.common.exceptions import StorageException
from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def save(
        self,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """保存文件，返回文件路径/URL"""
        pass
    
    @abstractmethod
    async def read(self, file_path: str) -> bytes:
        """读取文件"""
        pass
    
    @abstractmethod
    async def delete(self, file_path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        pass
    
    @abstractmethod
    def get_url(self, file_path: str, expires: Optional[int] = None) -> str:
        """获取文件访问URL"""
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件存储"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, file_path: str) -> Path:
        """获取完整路径"""
        # 防止目录遍历攻击
        full_path = (self.base_path / file_path).resolve()
        if not str(full_path).startswith(str(self.base_path.resolve())):
            raise StorageException("Invalid file path: directory traversal detected")
        return full_path
    
    async def save(
        self,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """保存文件"""
        # 生成唯一文件名
        file_id = str(uuid4())
        ext = Path(filename).suffix
        relative_path = f"{file_id[:2]}/{file_id[2:4]}/{file_id}{ext}"
        full_path = self._get_full_path(relative_path)
        
        # 创建目录
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_data)
        
        logger.info("file_saved", path=str(relative_path), size=len(file_data))
        return str(relative_path)
    
    async def read(self, file_path: str) -> bytes:
        """读取文件"""
        full_path = self._get_full_path(file_path)
        if not full_path.exists():
            raise StorageException(f"File not found: {file_path}")
        
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()
    
    async def delete(self, file_path: str) -> bool:
        """删除文件"""
        full_path = self._get_full_path(file_path)
        if full_path.exists():
            full_path.unlink()
            logger.info("file_deleted", path=file_path)
            return True
        return False
    
    async def exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        full_path = self._get_full_path(file_path)
        return full_path.exists()
    
    def get_url(self, file_path: str, expires: Optional[int] = None) -> str:
        """获取本地文件路径"""
        full_path = self._get_full_path(file_path)
        return str(full_path)


class MinioStorageBackend(StorageBackend):
    """MinIO 对象存储"""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False
    ):
        try:
            from minio import Minio
        except ImportError:
            raise StorageException("minio package is required for MinIO storage")
        
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket = bucket
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保存储桶存在"""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
    
    async def save(
        self,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """保存文件到MinIO"""
        import io
        
        file_id = str(uuid4())
        ext = Path(filename).suffix
        object_name = f"{file_id[:2]}/{file_id[2:4]}/{file_id}{ext}"
        
        self.client.put_object(
            self.bucket,
            object_name,
            io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type or "application/octet-stream"
        )
        
        logger.info("file_saved_to_minio", object_name=object_name)
        return object_name
    
    async def read(self, file_path: str) -> bytes:
        """从MinIO读取文件"""
        import io
        
        response = self.client.get_object(self.bucket, file_path)
        data = response.read()
        response.close()
        return data
    
    async def delete(self, file_path: str) -> bool:
        """从MinIO删除文件"""
        self.client.remove_object(self.bucket, file_path)
        return True
    
    async def exists(self, file_path: str) -> bool:
        """检查MinIO对象是否存在"""
        try:
            self.client.stat_object(self.bucket, file_path)
            return True
        except Exception:
            return False
    
    def get_url(self, file_path: str, expires: Optional[int] = 3600) -> str:
        """获取MinIO预签名URL"""
        from datetime import timedelta
        
        return self.client.presigned_get_object(
            self.bucket,
            file_path,
            expires=timedelta(seconds=expires) if expires else timedelta(hours=1)
        )


class StorageManager:
    """存储管理器"""
    
    def __init__(self):
        self.backend = self._create_backend()
    
    def _create_backend(self) -> StorageBackend:
        """创建存储后端"""
        storage_type = settings.db.storage_type
        
        if storage_type == "local":
            return LocalStorageBackend(settings.db.local_storage_path)
        
        elif storage_type == "minio":
            return MinioStorageBackend(
                endpoint=settings.db.minio_endpoint,
                access_key=settings.db.minio_access_key,
                secret_key=settings.db.minio_secret_key,
                bucket=settings.db.minio_bucket
            )
        
        else:
            raise StorageException(f"Unsupported storage type: {storage_type}")
    
    async def save_upload(
        self,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> dict:
        """
        保存上传的文件
        返回: {"path": 存储路径, "hash": MD5哈希, "size": 文件大小}
        """
        # 计算文件hash
        file_hash = hashlib.md5(file_data).hexdigest()
        
        # 保存文件
        file_path = await self.backend.save(file_data, filename, content_type)
        
        return {
            "path": file_path,
            "hash": file_hash,
            "size": len(file_data)
        }
    
    async def read_file(self, file_path: str) -> bytes:
        """读取文件"""
        return await self.backend.read(file_path)
    
    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        return await self.backend.delete(file_path)
    
    async def file_exists(self, file_path: str) -> bool:
        """检查文件是否存在"""
        return await self.backend.exists(file_path)
    
    def get_file_url(self, file_path: str, expires: Optional[int] = None) -> str:
        """获取文件URL"""
        return self.backend.get_url(file_path, expires)


# 全局实例
storage_manager = StorageManager()


def get_storage_manager() -> StorageManager:
    """获取存储管理器"""
    return storage_manager
