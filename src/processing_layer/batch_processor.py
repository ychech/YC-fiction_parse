"""
批量解析处理器
优化大规模小说批量解析性能
"""
import asyncio
from typing import AsyncGenerator, Callable, Dict, List, Optional

from src.common.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


class BatchProcessor:
    """
    批量处理器
    
    特性：
    - 动态批次大小调整
    - 失败重试机制
    - 进度追踪
    - 并发控制
    - 结果聚合
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_concurrent: int = 5,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.results: Dict[str, any] = {}
        self.errors: Dict[str, str] = {}
    
    async def process_batch(
        self,
        items: List[Dict],
        processor: Callable,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, any]:
        """
        批量处理
        
        Args:
            items: 待处理项列表
            processor: 处理函数
            progress_callback: 进度回调函数
        
        Returns:
            处理结果
        """
        total = len(items)
        processed = 0
        failed = 0
        
        logger.info("batch_processing_started", total=total, batch_size=self.batch_size)
        
        # 分批处理
        for i in range(0, total, self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # 处理批次
            tasks = [
                self._process_with_retry(item, processor)
                for item in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 收集结果
            for item, result in zip(batch, batch_results):
                item_id = item.get("id", str(id(item)))
                
                if isinstance(result, Exception):
                    self.errors[item_id] = str(result)
                    failed += 1
                    logger.error("batch_item_failed", id=item_id, error=str(result))
                else:
                    self.results[item_id] = result
                    processed += 1
            
            # 进度回调
            if progress_callback:
                await progress_callback(
                    processed=processed,
                    failed=failed,
                    total=total,
                    percentage=processed / total * 100,
                )
            
            logger.info(
                "batch_progress",
                processed=processed,
                failed=failed,
                total=total,
                percentage=f"{processed/total*100:.1f}%"
            )
        
        logger.info(
            "batch_processing_completed",
            processed=processed,
            failed=failed,
            total=total,
        )
        
        return {
            "results": self.results,
            "errors": self.errors,
            "processed": processed,
            "failed": failed,
            "total": total,
        }
    
    async def _process_with_retry(
        self,
        item: Dict,
        processor: Callable,
    ) -> any:
        """带重试的处理"""
        async with self.semaphore:
            for attempt in range(self.retry_attempts):
                try:
                    return await processor(item)
                except Exception as e:
                    if attempt < self.retry_attempts - 1:
                        logger.warning(
                            "retry_attempt",
                            item_id=item.get("id"),
                            attempt=attempt + 1,
                            error=str(e),
                        )
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        raise
    
    async def process_stream(
        self,
        items: List[Dict],
        processor: Callable,
    ) -> AsyncGenerator[Dict, None]:
        """
        流式批量处理
        
        实时返回处理结果
        """
        total = len(items)
        
        for i in range(0, total, self.batch_size):
            batch = items[i:i + self.batch_size]
            
            tasks = [
                self._process_with_semaphore(item, processor)
                for item in batch
            ]
            
            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    yield {
                        "status": "success",
                        "data": result,
                    }
                except Exception as e:
                    yield {
                        "status": "error",
                        "error": str(e),
                    }
    
    async def _process_with_semaphore(
        self,
        item: Dict,
        processor: Callable,
    ) -> any:
        """带信号量的处理"""
        async with self.semaphore:
            return await processor(item)


class NovelBatchProcessor:
    """
    小说批量解析处理器
    
    专门用于小说解析的批量处理优化
    """
    
    def __init__(self):
        self.processor = BatchProcessor(
            batch_size=settings.processing.batch_size,
            max_concurrent=settings.processing.max_workers,
        )
    
    async def parse_novels_batch(
        self,
        novel_ids: List[str],
        parse_type: str = "deep",  # basic 或 deep
        priority: int = 2,
    ) -> Dict:
        """
        批量解析小说
        
        Args:
            novel_ids: 小说ID列表
            parse_type: 解析类型
            priority: 优先级
        
        Returns:
            解析结果
        """
        from src.data_layer.models import get_db
        from src.data_layer.repositories import NovelRepository
        from src.data_layer.storage import get_storage_manager
        
        db = next(get_db())
        
        try:
            # 获取小说信息
            novel_repo = NovelRepository(db)
            novels = []
            
            for novel_id in novel_ids:
                novel = novel_repo.get_by_id(novel_id)
                if novel:
                    novels.append({
                        "id": novel_id,
                        "novel": novel,
                    })
            
            # 定义处理函数
            async def process_novel(item: Dict) -> Dict:
                novel = item["novel"]
                
                # 读取文件
                storage = get_storage_manager()
                file_data = await storage.read_file(novel.file_path)
                
                # 解析
                if parse_type == "deep":
                    from src.processing_layer.deep_pipeline import DeepProcessingPipeline
                    
                    # 先进行基础解析
                    from src.processing_layer.parsers import get_parser
                    parser = get_parser(novel.format)
                    parse_result = await parser.parse(file_data)
                    
                    # 深度解析
                    chapters = [
                        {
                            "chapter_number": ch.chapter_number,
                            "title": ch.title,
                            "content": ch.content,
                            "is_core": ch.is_core,
                        }
                        for ch in parse_result.chapters
                    ]
                    
                    full_text = "\n\n".join(ch.get("content", "") for ch in chapters)
                    
                    pipeline = DeepProcessingPipeline()
                    features = await pipeline.process(
                        novel_id=item["id"],
                        text=full_text,
                        chapters=chapters,
                    )
                    
                    return {
                        "novel_id": item["id"],
                        "features": features,
                        "type": "deep",
                    }
                else:
                    # 基础解析
                    from src.processing_layer.parsers import get_parser
                    parser = get_parser(novel.format)
                    result = await parser.parse(file_data)
                    
                    return {
                        "novel_id": item["id"],
                        "result": result,
                        "type": "basic",
                    }
            
            # 批量处理
            results = await self.processor.process_batch(
                items=novels,
                processor=process_novel,
            )
            
            return results
            
        finally:
            db.close()
    
    async def parse_directory(
        self,
        directory: str,
        pattern: str = "*.txt",
        auto_upload: bool = True,
    ) -> Dict:
        """
        批量解析目录中的小说
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            auto_upload: 是否自动上传
        
        Returns:
            解析结果
        """
        import glob
        from pathlib import Path
        
        # 查找文件
        files = glob.glob(f"{directory}/{pattern}")
        
        if auto_upload:
            # 先上传所有文件
            from src.data_layer.models import get_db
            from src.data_layer.repositories import NovelRepository
            from src.data_layer.storage import get_storage_manager
            
            db = next(get_db())
            novel_repo = NovelRepository(db)
            storage = get_storage_manager()
            
            novel_ids = []
            
            for file_path in files:
                try:
                    # 读取文件
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                    
                    # 保存文件
                    file_info = await storage.save_upload(
                        file_data,
                        Path(file_path).name,
                    )
                    
                    # 创建小说记录
                    from src.common.schemas import NovelCreate, NovelFormat
                    
                    ext = Path(file_path).suffix[1:].lower()
                    if ext not in [f.value for f in NovelFormat]:
                        continue
                    
                    novel_data = NovelCreate(
                        title=Path(file_path).stem,
                    )
                    
                    novel = novel_repo.create_from_meta(novel_data, {
                        "format": ext,
                        "file_path": file_info["path"],
                        "file_size": file_info["size"],
                        "file_hash": file_info["hash"],
                    })
                    
                    novel_ids.append(novel.id)
                    
                except Exception as e:
                    logger.error("file_upload_failed", path=file_path, error=str(e))
            
            db.close()
            
            # 批量解析
            if novel_ids:
                return await self.parse_novels_batch(novel_ids)
            else:
                return {"results": {}, "errors": {}, "processed": 0, "failed": 0, "total": 0}
        
        else:
            # 直接解析不上传
            items = [{"id": str(i), "path": path} for i, path in enumerate(files)]
            
            async def process_file(item: Dict) -> Dict:
                from src.processing_layer.parsers import get_parser
                
                ext = Path(item["path"]).suffix[1:].lower()
                parser = get_parser(ext)
                
                with open(item["path"], "rb") as f:
                    file_data = f.read()
                
                result = await parser.parse(file_data)
                
                return {
                    "path": item["path"],
                    "result": result,
                }
            
            return await self.processor.process_batch(
                items=items,
                processor=process_file,
            )
