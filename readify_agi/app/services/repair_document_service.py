import asyncio
import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List

from app.core.database import async_session_maker
from app.models.repair_document import RepairDocumentCreate
from app.repositories.document_repository import DocumentRepository
from app.repositories.file_repository import FileRepository
from app.repositories.repair_document_repository import RepairDocumentRepository
from app.services.text_repair_service import TextRepairService

logger = logging.getLogger(__name__)


class RepairDocumentService:
    """文档修复服务层"""

    def __init__(
        self,
        repair_document_repository: RepairDocumentRepository,
        document_repository: DocumentRepository,
        file_repository: FileRepository,
        text_repair_service: TextRepairService
    ):
        self.repair_document_repository = repair_document_repository
        self.document_repository = document_repository
        self.file_repository = file_repository
        self.text_repair_service = text_repair_service
        self.thread_pool = ThreadPoolExecutor(max_workers=3)

    async def _repair_and_save_task(self, file_id: int) -> None:
        """
        实际执行文档修复的后台任务

        Args:
            file_id: 文件ID
        """
        start_time = time.time()
        logger.info("开始处理文件 %d 的修复任务", file_id)

        try:
            async with async_session_maker() as db:
                file_repo = FileRepository(db)
                doc_repo = DocumentRepository(db)
                repair_doc_repo = RepairDocumentRepository(db)

                logger.info("正在获取文件信息...")
                file = await file_repo.get_file_by_id(file_id)
                if not file:
                    logger.error("文件不存在 (ID: %d)", file_id)
                    return
                logger.info("成功获取文件信息：%s", file.original_name)

                logger.info("正在获取文档块...")
                documents = await doc_repo.get_by_file_id(file_id)
                if not documents:
                    logger.error("未找到需要修复的文档 (文件ID: %d)", file_id)
                    return
                logger.info("获取到 %d 个文档块", len(documents))

                documents.sort(key=lambda x: x.sequence)

                repair_creates = []
                sequence = 0
                total_docs = len(documents)

                for index, doc in enumerate(documents, 1):
                    logger.info("正在处理第 %d/%d 个文档块", index, total_docs)
                    logger.debug("文档ID: %d, 序号: %d", doc.id, doc.sequence)
                    logger.debug("原始内容: %s...", doc.content[:100])

                    logger.info("开始修复文本...")
                    repair_result = await self.text_repair_service.repair_text(doc.content)

                    if isinstance(repair_result, str):
                        try:
                            paragraphs = json.loads(repair_result)
                            if not isinstance(paragraphs, list):
                                paragraphs = [repair_result]
                        except json.JSONDecodeError:
                            paragraphs = [repair_result]
                    else:
                        paragraphs = repair_result if isinstance(repair_result, list) else [repair_result]

                    logger.info("文本修复完成，生成了 %d 个段落", len(paragraphs))

                    for p_index, paragraph in enumerate(paragraphs, 1):
                        logger.debug("处理第 %d/%d 个段落", p_index, len(paragraphs))
                        repair_create = RepairDocumentCreate(
                            file_id=file_id,
                            content=paragraph,
                            sequence=sequence
                        )
                        repair_creates.append(repair_create)
                        sequence += 1

                    logger.info("文档块 %d/%d 处理完成", index, total_docs)

                if repair_creates:
                    logger.info("开始保存 %d 个修复后的文档记录...", len(repair_creates))
                    await repair_doc_repo.create_many(repair_creates)
                    logger.info("所有修复文档保存完成")

                end_time = time.time()
                duration = end_time - start_time
                logger.info("文件 %d 的修复任务完成", file_id)
                logger.info("总耗时: %.2f 秒", duration)

        except Exception as e:
            logger.error("修复文档时发生异常")
            logger.error("错误详情: %s", str(e))
            logger.error("堆栈信息:\n%s", traceback.format_exc())

    async def repair_and_save(self, file_id: int) -> None:
        """
        在后台启动文档修复任务

        Args:
            file_id: 文件ID
        """
        logger.info("正在启动文件 %d 的修复任务...", file_id)
        loop = asyncio.get_event_loop()
        loop.create_task(self._repair_and_save_task(file_id))
        logger.info("修复任务已进入后台处理队列")

    async def get_file_repair_documents(self, file_id: int) -> List[str]:
        """
        获取文件的所有修复文档内容

        Args:
            file_id: 文件ID

        Returns:
            List[str]: 修复文档内容列表
        """
        documents = await self.repair_document_repository.get_by_file_id(file_id)
        return [doc.content for doc in documents]
