from app.repositories.file_repository import FileRepository
from app.repositories.document_repository import DocumentRepository
from app.services.vector_store_service import VectorStoreService
from app.core.database import async_session_maker
import os
import time
import traceback
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
        self.thread_pool = ThreadPoolExecutor(max_workers=3)  # 创建线程池
        
    async def _vectorize_task(self, file_id: int) -> bool:
        """
        实际执行向量化的后台任务
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否成功
        """
        start_time = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始处理文件 {file_id} 的向量化任务")
        
        try:
            # 为后台任务创建新的数据库会话
            async with async_session_maker():
                # 创建新的仓储实例
                file_repo = FileRepository()
                doc_repo = DocumentRepository()
                
                # 1. 检查文件是否存在
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在获取文件信息...")
                file = await file_repo.get_file_by_id(file_id)
                if not file:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：文件不存在 (ID: {file_id})")
                    raise ValueError(f"文件不存在: {file_id}")
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 成功获取文件信息：{file.original_name}")
                
                # 2. 获取原始文档
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在获取文档块...")
                documents = await doc_repo.get_by_file_id(file_id)
                if not documents:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：未找到文件的文档内容 (文件ID: {file_id})")
                    raise ValueError(f"未找到文件的文档内容: {file_id}")
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 获取到 {len(documents)} 个文档块")
                
                # 3. 获取所有文档内容
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在准备文档内容...")
                texts = [doc.content for doc in documents]
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文档内容准备完成，共 {len(texts)} 段")
                
                # 4. 使用文件storage_key（去除扩展名）作为collection名称
                collection_name = os.path.splitext(file.storage_key)[0]
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 使用collection名称: {collection_name}")
                
                # 5. 向量化并存储
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始向量化处理...")
                await self.vector_store_service.batch_vectorize_texts(
                    texts=texts,
                    collection_name=collection_name
                )
                
                end_time = time.time()
                duration = end_time - start_time
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件 {file_id} 的向量化任务完成")
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 总耗时: {duration:.2f} 秒")
                return True
            
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：向量化处理时发生异常")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {str(e)}")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 堆栈信息:")
            print(traceback.format_exc())
            raise
        
    async def vectorize_file(self, file_id: int) -> bool:
        """
        在后台启动向量化任务
        
        Args:
            file_id: 文件ID
            
        Returns:
            bool: 是否成功启动任务
        """
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在启动文件 {file_id} 的向量化任务...")
        # 在线程池中启动任务
        loop = asyncio.get_event_loop()
        loop.create_task(self._vectorize_task(file_id))
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 向量化任务已进入后台处理队列")
        return True 
