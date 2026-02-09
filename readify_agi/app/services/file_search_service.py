import logging
from typing import List, Dict, Any, Optional

from app.repositories.file_repository import FileRepository
from app.services.vector_store_service import VectorStoreService, UserRole

logger = logging.getLogger(__name__)


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
        user_id: Optional[int] = None,
        user_role: str = UserRole.USER,
        project_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        在指定文件中搜索相似文本

        Args:
            file_id: 文件ID
            query_text: 查询文本
            top_k: 返回结果数量
            user_id: 当前用户ID（用于权限过滤）
            user_role: 用户角色 (user/admin)
            project_id: 当前项目ID（用于项目级权限过滤）

        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        logger.info("[文件搜索] 开始搜索文件 %d (user_id=%s, role=%s)", file_id, user_id, user_role)

        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            logger.error("[文件搜索] 文件不存在 (ID: %d)", file_id)
            raise ValueError(f"文件不存在: {file_id}")
        logger.info("[文件搜索] 找到文件：%s", file.original_name)

        try:
            logger.info("[文件搜索] 开始向量检索...")
            results = await self.vector_store_service.search_similar_texts(
                query_text=query_text,
                top_k=top_k,
                user_id=user_id,
                user_role=user_role,
                project_id=project_id,
                file_id=file_id,
            )
            logger.info("[文件搜索] 检索完成，返回 %d 条结果", len(results))
            return results
        except Exception as e:
            logger.error("[文件搜索] 搜索失败：%s", str(e))
            raise ValueError(f"搜索失败: {str(e)}")
