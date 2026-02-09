import asyncio
import logging
import time
import traceback
from typing import Dict, Any

from app.core.database import async_session_maker
from app.repositories.document_repository import DocumentRepository
from app.repositories.file_repository import FileRepository
from app.services.callback_service import CallbackService
from app.services.document_service import DocumentService
from app.services.file_vectorize_service import FileVectorizeService
from app.services.llama_parse_service import LlamaParseService
from app.services.vector_store_service import VectorStoreService, Visibility

logger = logging.getLogger(__name__)


class FileProcessService:
    """文件处理服务，集成解析和向量化功能"""

    def __init__(
        self,
        file_repository: FileRepository,
        document_repository: DocumentRepository,
        llama_parse_service: LlamaParseService,
        vector_store_service: VectorStoreService,
        callback_service: CallbackService
    ):
        self.file_repository = file_repository
        self.document_repository = document_repository
        self.llama_parse_service = llama_parse_service
        self.vector_store_service = vector_store_service
        self.callback_service = callback_service

    async def _process_task(
        self,
        file_id: int,
        user_id: int = 0,
        project_id: int = 0,
        visibility: str = Visibility.PRIVATE,
    ) -> bool:
        """
        实际执行文件处理的后台任务

        Args:
            file_id: 文件ID
            user_id: 用户ID（用于权限控制）
            project_id: 项目ID（用于权限控制）
            visibility: 可见性级别

        Returns:
            bool: 是否成功
        """
        start_time = time.time()
        logger.info("开始处理文件 %d 的解析和向量化任务 (user_id=%d, project_id=%d, visibility=%s)",
                    file_id, user_id, project_id, visibility)

        success = False
        message = ""
        additional_data = {}

        try:
            async with async_session_maker():
                file_repo = FileRepository()
                doc_repo = DocumentRepository()
                document_service = DocumentService(doc_repo, file_repo, self.llama_parse_service)
                file_vectorize_service = FileVectorizeService(
                    file_repo,
                    doc_repo,
                    self.vector_store_service
                )
                callback_service = CallbackService()

                logger.info("正在获取文件信息...")
                file = await file_repo.get_file_by_id(file_id)
                if not file:
                    logger.error("文件不存在 (ID: %d)", file_id)
                    message = f"文件不存在: {file_id}"
                    await callback_service.notify_file_processed(
                        file_id=file_id,
                        success=False,
                        message=message
                    )
                    return False
                logger.info("成功获取文件信息：%s", file.original_name)

                logger.info("清除现有文档...")
                await doc_repo.delete_by_file_id(file_id)

                logger.info("开始解析文件...")
                await document_service.parse_and_save(file_id)
                logger.info("文件解析完成")

                logger.info("开始向量化文件...")
                await file_vectorize_service._vectorize_task(
                    file_id,
                    user_id=user_id,
                    project_id=project_id,
                    visibility=visibility,
                )
                logger.info("文件向量化完成")

                logger.info("更新文件状态...")
                await file_repo.update_vectorized_status(file_id, True)

                end_time = time.time()
                duration = end_time - start_time

                success = True
                message = "文件处理成功"
                additional_data = {
                    "duration": f"{duration:.2f}秒",
                    "process_time": int(end_time),
                    "user_id": user_id,
                    "project_id": project_id,
                    "visibility": visibility,
                }

                logger.info("文件 %d 的处理任务完成", file_id)
                logger.info("总耗时: %.2f 秒", duration)

        except Exception as e:
            logger.error("文件处理时发生异常")
            logger.error("错误详情: %s", str(e))
            logger.error("堆栈信息:\n%s", traceback.format_exc())

            success = False
            message = f"处理失败: {str(e)}"

        logger.info("发送回调通知...")
        async with async_session_maker():
            callback_service = CallbackService()
            await callback_service.notify_file_processed(
                file_id=file_id,
                success=success,
                message=message,
                additional_data=additional_data
            )

        return success

    async def process_file(
        self,
        file_id: int,
        user_id: int = 0,
        project_id: int = 0,
        visibility: str = Visibility.PRIVATE,
    ) -> bool:
        """
        在后台启动文件处理任务

        Args:
            file_id: 文件ID
            user_id: 用户ID（用于权限控制）
            project_id: 项目ID（用于权限控制）
            visibility: 可见性级别

        Returns:
            bool: 是否成功启动任务
        """
        try:
            logger.info("正在启动文件 %d 的处理任务 (user_id=%d, project_id=%d)...",
                        file_id, user_id, project_id)

            file = await self.file_repository.get_file_by_id(file_id)
            if not file:
                logger.error("文件不存在 (ID: %d)", file_id)
                raise ValueError(f"文件不存在: {file_id}")

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            task = loop.create_task(
                self._process_task(file_id, user_id, project_id, visibility)
            )

            def handle_task_result(future):
                try:
                    future.result()
                except Exception as e:
                    logger.error("后台任务执行失败")
                    logger.error("错误详情: %s", str(e))
                    logger.error("堆栈信息:\n%s", traceback.format_exc())

            task.add_done_callback(handle_task_result)

            logger.info("文件处理任务已进入后台处理队列")
            return True

        except Exception as e:
            logger.error("启动处理任务失败")
            logger.error("错误详情: %s", str(e))
            logger.error("堆栈信息:\n%s", traceback.format_exc())
            raise
