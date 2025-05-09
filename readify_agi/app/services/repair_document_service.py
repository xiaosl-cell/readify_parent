from typing import List
from app.models.repair_document import RepairDocumentCreate
from app.repositories.repair_document_repository import RepairDocumentRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.file_repository import FileRepository
from app.services.text_repair_service import TextRepairService
from app.core.database import async_session_maker
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import traceback

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
        self.thread_pool = ThreadPoolExecutor(max_workers=3)  # 创建线程池
        
    async def _repair_and_save_task(self, file_id: int) -> None:
        """
        实际执行文档修复的后台任务
        
        Args:
            file_id: 文件ID
        """
        start_time = time.time()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始处理文件 {file_id} 的修复任务")
        
        try:
            # 为后台任务创建新的数据库会话
            async with async_session_maker() as db:
                # 创建新的仓储实例
                file_repo = FileRepository(db)
                doc_repo = DocumentRepository(db)
                repair_doc_repo = RepairDocumentRepository(db)
                
                # 获取文件信息
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在获取文件信息...")
                file = await file_repo.get_file_by_id(file_id)
                if not file:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：文件不存在 (ID: {file_id})")
                    return
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 成功获取文件信息：{file.original_name}")
                    
                # 获取原始文档
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在获取文档块...")
                documents = await doc_repo.get_by_file_id(file_id)
                if not documents:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：未找到需要修复的文档 (文件ID: {file_id})")
                    return
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 获取到 {len(documents)} 个文档块")
                    
                # 按sequence排序
                documents.sort(key=lambda x: x.sequence)
                
                # 修复并保存每个文档
                repair_creates = []
                sequence = 0
                total_docs = len(documents)
                
                for index, doc in enumerate(documents, 1):
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在处理第 {index}/{total_docs} 个文档块")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文档ID: {doc.id}, 序号: {doc.sequence}")
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 原始内容: {doc.content[:100]}...")
                    
                    # 调用文本修复服务
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始修复文本...")
                    repair_result = await self.text_repair_service.repair_text(doc.content)
                    # 确保paragraphs是数组
                    if isinstance(repair_result, str):
                        try:
                            import json
                            paragraphs = json.loads(repair_result)
                            if not isinstance(paragraphs, list):
                                paragraphs = [repair_result]
                        except json.JSONDecodeError:
                            paragraphs = [repair_result]
                    else:
                        paragraphs = repair_result if isinstance(repair_result, list) else [repair_result]
                        
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文本修复完成，生成了 {len(paragraphs)} 个段落")
                    
                    # 创建修复文档记录
                    for p_index, paragraph in enumerate(paragraphs, 1):
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 处理第 {p_index}/{len(paragraphs)} 个段落")
                        repair_create = RepairDocumentCreate(
                            file_id=file_id,
                            content=paragraph,
                            sequence=sequence
                        )
                        repair_creates.append(repair_create)
                        sequence += 1
                    
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文档块 {index}/{total_docs} 处理完成")

                # 批量保存修复后的文档
                if repair_creates:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始保存 {len(repair_creates)} 个修复后的文档记录...")
                    await repair_doc_repo.create_many(repair_creates)
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 所有修复文档保存完成")
                    
                end_time = time.time()
                duration = end_time - start_time
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 文件 {file_id} 的修复任务完成")
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 总耗时: {duration:.2f} 秒")
            
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误：修复文档时发生异常")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 错误详情: {str(e)}")
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 堆栈信息:")
            print(traceback.format_exc())
        
    async def repair_and_save(self, file_id: int) -> None:
        """
        在后台启动文档修复任务
        
        Args:
            file_id: 文件ID
        """
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 正在启动文件 {file_id} 的修复任务...")
        # 在线程池中启动修复任务
        loop = asyncio.get_event_loop()
        loop.create_task(self._repair_and_save_task(file_id))
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 修复任务已进入后台处理队列")
            
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