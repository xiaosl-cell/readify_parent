import logging
import os
import time
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.repositories.file_repository import FileRepository
from app.repositories.document_repository import DocumentRepository
from app.services.vector_store_service import VectorStoreService
from app.core.database import async_session_maker

logger = logging.getLogger(__name__)


class FileVectorizeService:
    """文件向量化服务"""

    def __init__(
        self,
        file_repository: FileRepository,
        document_repository: DocumentRepository,
        vector_store_service: VectorStoreService
    ):
        self.file_repository = file_repository
        self.document_repository = document_repository
        self.vector_store_service = vector_store_service
        self.thread_pool = ThreadPoolExecutor(max_workers=3)

    async def _vectorize_task(self, file_id: int) -> bool:
        """
        实际执行向量化的后台任务

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否成功
        """
        start_time = time.time()
        logger.info("开始处理文件 %d 的向量化任务", file_id)

        try:
            async with async_session_maker():
                file_repo = FileRepository()
                doc_repo = DocumentRepository()

                logger.info("正在获取文件信息...")
                file = await file_repo.get_file_by_id(file_id)
                if not file:
                    logger.error("文件不存在 (ID: %d)", file_id)
                    raise ValueError(f"文件不存在: {file_id}")
                logger.info("成功获取文件信息：%s", file.original_name)

                logger.info("正在获取文档块...")
                documents = await doc_repo.get_by_file_id(file_id)
                if not documents:
                    logger.error("未找到文件的文档内容 (文件ID: %d)", file_id)
                    raise ValueError(f"未找到文件的文档内容: {file_id}")
                logger.info("获取到 %d 个文档块", len(documents))

                logger.info("正在准备文档内容...")
                texts = [doc.content for doc in documents]
                logger.info("文档内容准备完成，共 %d 段", len(texts))

                collection_name = os.path.splitext(file.storage_key)[0]
                logger.info("使用collection名称: %s", collection_name)

                logger.info("开始向量化处理...")
                await self.vector_store_service.batch_vectorize_texts(
                    texts=texts,
                    collection_name=collection_name
                )

                end_time = time.time()
                duration = end_time - start_time
                logger.info("文件 %d 的向量化任务完成", file_id)
                logger.info("总耗时: %.2f 秒", duration)
                return True

        except Exception as e:
            logger.error("向量化处理时发生异常")
            logger.error("错误详情: %s", str(e))
            logger.error("堆栈信息:\n%s", traceback.format_exc())
            raise

    async def vectorize_file(self, file_id: int) -> bool:
        """
        在后台启动向量化任务

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否成功启动任务
        """
        logger.info("正在启动文件 %d 的向量化任务...", file_id)
        loop = asyncio.get_event_loop()
        loop.create_task(self._vectorize_task(file_id))
        logger.info("向量化任务已进入后台处理队列")
        return True
