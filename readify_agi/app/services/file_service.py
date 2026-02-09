import logging
from typing import List, Dict, Any, Optional

from fastapi import HTTPException

from app.models.file import FileCreate, FileResponse
from app.repositories.file_repository import FileRepository
from app.repositories.project_file_repository import ProjectFileRepository
from app.services.vector_store_service import VectorStoreService, UserRole

logger = logging.getLogger(__name__)


class FileService:
    """文件服务层"""

    def __init__(self, file_repository: FileRepository):
        self.file_repository = file_repository
        self.vector_store_service = VectorStoreService()

    async def create_file(self, file_data: FileCreate) -> FileResponse:
        """创建文件记录"""
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
        # 先删除向量数据
        await self.vector_store_service.delete_by_file_id(file_id)
        # 再删除文件记录
        result = await self.file_repository.delete_file(file_id)
        if not result:
            raise HTTPException(status_code=404, detail="File not found")
        return True

    async def search_files_by_vector(
        self,
        project_id: int,
        input_text: str,
        top_k: int = 5,
        user_id: Optional[int] = None,
        user_role: str = UserRole.USER,
    ) -> List[Dict[str, Any]]:
        """
        基于project_id的向量检索方法

        Args:
            project_id: 项目ID
            input_text: 输入文本
            top_k: 返回结果数量
            user_id: 当前用户ID（用于权限过滤）
            user_role: 用户角色 (user/admin)

        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        project_file_repository = ProjectFileRepository()

        file_ids = await project_file_repository.get_file_ids_by_project_id(project_id)
        if not file_ids:
            return []

        # 获取已向量化的文件ID列表
        vectorized_file_ids = []
        for file_id in file_ids:
            file = await self.file_repository.get_file_by_id(file_id)
            if file and file.vectorized:
                vectorized_file_ids.append(file_id)

        if not vectorized_file_ids:
            return []

        try:
            # 使用统一的向量搜索，通过 file_ids 过滤
            results = await self.vector_store_service.search_similar_texts(
                query_text=input_text,
                top_k=top_k,
                user_id=user_id,
                user_role=user_role,
                project_id=project_id,
                file_ids=vectorized_file_ids,
            )

            # 补充文件名信息
            for result in results:
                fid = result.get("file_id")
                if fid:
                    file = await self.file_repository.get_file_by_id(fid)
                    if file:
                        result["file_name"] = file.original_name

            return results
        except Exception as e:
            logger.warning("向量检索错误: %s", str(e))
            return []
