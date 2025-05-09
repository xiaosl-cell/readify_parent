from typing import List, Dict, Any
import os
from app.repositories.file_repository import FileRepository
from app.services.vector_store_service import VectorStoreService

class FileSearchService:
    """文件搜索服务"""
    
    def __init__(
        self,
        file_repository: FileRepository,
        vector_store_service: VectorStoreService
    ):
        self.file_repository = file_repository
        self.vector_store_service = vector_store_service
        
    async def search_in_file(
        self,
        file_id: int,
        query_text: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        在指定文件中搜索相似文本
        
        Args:
            file_id: 文件ID
            query_text: 查询文本
            top_k: 返回结果数量

        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        print(f"[文件搜索] 开始搜索文件 {file_id}")
        
        # 1. 检查文件是否存在
        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            print(f"[文件搜索] 错误：文件不存在 (ID: {file_id})")
            raise ValueError(f"文件不存在: {file_id}")
        print(f"[文件搜索] 找到文件：{file.original_name}")
            
        # 2. 获取collection名称
        collection_name = os.path.splitext(file.storage_name)[0]
        print(f"[文件搜索] 使用集合名称：{collection_name}")
        
        # 3. 执行向量检索
        try:
            print(f"[文件搜索] 开始向量检索...")
            results = await self.vector_store_service.search_similar_texts(
                query_text=query_text,
                collection_name=collection_name,
                top_k=top_k,
            )
            print(f"[文件搜索] 检索完成，返回 {len(results)} 条结果")
            return results
        except Exception as e:
            print(f"[文件搜索] 搜索失败：{str(e)}")
            raise ValueError(f"搜索失败: {str(e)}") 