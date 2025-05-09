from typing import List, Optional, Dict, Any
import os
from fastapi import HTTPException
from app.models.file import FileCreate, FileResponse, FileDB
from app.repositories.file_repository import FileRepository
from app.repositories.project_file_repository import ProjectFileRepository
from app.services.vector_store_service import VectorStoreService

class FileService:
    """文件服务层"""
    
    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository
        self.vector_store_service = VectorStoreService()
        
    async def create_file(self, file_data: FileCreate) -> FileResponse:
        """创建文件记录"""
        # 检查MD5是否存在
        if file_data.md5:
            existing_file = await self.file_repository.get_file_by_md5(file_data.md5)
            if existing_file:
                raise HTTPException(status_code=400, detail="File with this MD5 already exists")
                
        file = await self.file_repository.create_file(file_data)
        return FileResponse.model_validate(file)
        
    async def get_file(self, file_id: int) -> FileResponse:
        """获取文件信息"""
        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse.model_validate(file)
        
    async def get_files(self, skip: int = 0, limit: int = 100) -> List[FileResponse]:
        """获取文件列表"""
        files = await self.file_repository.get_all_files(skip, limit)
        return [FileResponse.model_validate(file) for file in files]
        
    async def delete_file(self, file_id: int) -> bool:
        """删除文件"""
        result = await self.file_repository.delete_file(file_id)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        return True
        
    async def search_files_by_vector(
        self, 
        project_id: int,
        input_text: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于project_id的向量检索方法
        
        Args:
            project_id: 项目ID
            input_text: 输入文本
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        # 创建项目文件仓库
        project_file_repository = ProjectFileRepository()
        
        # 获取项目相关的文件ID列表
        file_ids = await project_file_repository.get_file_ids_by_project_id(project_id)
        if not file_ids:
            return []
        
        # 获取所有文件详情
        all_results = []
        for file_id in file_ids:
            file = await self.file_repository.get_file_by_id(file_id)
            if not file or not file.vectorized:
                continue
                
            # 计算collection_name
            collection_name = os.path.splitext(file.storage_name)[0]
            
            try:
                # 执行向量检索
                results = await self.vector_store_service.search_similar_texts(
                    query_text=input_text,
                    collection_name=collection_name,
                    top_k=top_k
                )
                
                # 为每个结果添加文件信息
                for result in results:
                    result["file_id"] = file.id
                    result["file_name"] = file.original_name
                
                all_results.extend(results)
            except Exception as e:
                # 如果某个文件的检索出错，继续检索其他文件
                print(f"向量检索错误 - 文件ID {file_id}: {str(e)}")
                continue
        
        # 按相似度排序并返回前top_k个结果
        all_results.sort(key=lambda x: x["distance"])
        return all_results[:top_k] 