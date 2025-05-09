from typing import Dict, Any, Optional
import time
import traceback
import asyncio
from app.repositories.file_repository import FileRepository
from app.repositories.document_repository import DocumentRepository
from app.services.document_service import DocumentService
from app.services.file_vectorize_service import FileVectorizeService
from app.services.callback_service import CallbackService
from app.services.llama_parse_service import LlamaParseService
from app.services.vector_store_service import VectorStoreService
from app.core.database import async_session_maker

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
        
    async def _process_task(self, file_id: int) -> bool:
        """
        实际执行文件处理的后台任务
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否成功
        """
        start_time = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始处理文件 {file_id} 的解析和向量化任务")
        
        success = False
        message = ""
        additional_data = {}
        
        try:
            # 为后台任务创建新的数据库会话
            async with async_session_maker():
                # 创建新的仓储和服务实例
                file_repo = FileRepository()
                doc_repo = DocumentRepository()
                document_service = DocumentService(doc_repo, file_repo, self.llama_parse_service)
                file_vectorize_service = FileVectorizeService(
                    file_repo, 
                    doc_repo, 
                    self.vector_store_service
                )
                callback_service = CallbackService()
                
                # 1. 检查文件是否存在
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在获取文件信息...")
                file = await file_repo.get_file_by_id(file_id)
                if not file:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：文件不存在 (ID: {file_id})")
                    message = f"文件不存在: {file_id}"
                    await callback_service.notify_file_processed(
                        file_id=file_id,
                        success=False,
                        message=message
                    )
                    return False
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 成功获取文件信息：{file.original_name}")
                
                # 2. 清除现有文档（如果有）
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 清除现有文档...")
                await doc_repo.delete_by_file_id(file_id)
                
                # 3. 解析文件
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始解析文件...")
                await document_service.parse_and_save(file_id)
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件解析完成")
                
                # 4. 向量化文件
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始向量化文件...")
                await file_vectorize_service._vectorize_task(file_id)
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件向量化完成")
                
                # 5. 更新文件状态
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 更新文件状态...")
                await file_repo.update_vectorized_status(file_id, True)
                
                end_time = time.time()
                duration = end_time - start_time
                
                success = True
                message = "文件处理成功"
                additional_data = {
                    "duration": f"{duration:.2f}秒",
                    "process_time": int(end_time)
                }
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件 {file_id} 的处理任务完成")
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 总耗时: {duration:.2f} 秒")
                
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：文件处理时发生异常")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {str(e)}")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 堆栈信息:")
            print(traceback.format_exc())
            
            success = False
            message = f"处理失败: {str(e)}"
        
        # 6. 回调通知
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 发送回调通知...")
        async with async_session_maker():
            callback_service = CallbackService()
            await callback_service.notify_file_processed(
                file_id=file_id,
                success=success,
                message=message,
                additional_data=additional_data
            )
            
        return success
        
    async def process_file(self, file_id: int) -> bool:
        """
        在后台启动文件处理任务
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否成功启动任务
        """
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在启动文件 {file_id} 的处理任务...")
            
            # 检查文件是否存在
            file = await self.file_repository.get_file_by_id(file_id)
            if not file:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：文件不存在 (ID: {file_id})")
                raise ValueError(f"文件不存在: {file_id}")
                
            # 在事件循环中启动任务
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
                
            task = loop.create_task(self._process_task(file_id))
            
            # 添加任务完成回调，用于记录任何未捕获的异常
            def handle_task_result(future):
                try:
                    future.result()
                except Exception as e:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：后台任务执行失败")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {str(e)}")
                    print(traceback.format_exc())
                    
            task.add_done_callback(handle_task_result)
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件处理任务已进入后台处理队列")
            return True
            
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：启动处理任务失败")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {str(e)}")
            print(traceback.format_exc())
            raise 