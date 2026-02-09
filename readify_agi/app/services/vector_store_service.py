import asyncio
import logging
from enum import Enum
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.core.config import settings

load_dotenv()

logger = logging.getLogger(__name__)

# 统一的 collection 名称
COLLECTION_NAME = "rf_documents"


class Visibility(str, Enum):
    """向量数据可见性级别"""
    PRIVATE = "private"    # 仅创建者可见
    PROJECT = "project"    # 项目内成员可见
    PUBLIC = "public"      # 所有人可见


class UserRole(str, Enum):
    """用户角色"""
    USER = "user"
    ADMIN = "admin"


class VectorStoreService:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_API_BASE,
            check_embedding_ctx_length=False,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )
        self._connect()

    def _connect(self) -> None:
        if connections.has_connection("default"):
            return
        connection_args = {
            "host": settings.MILVUS_HOST,
            "port": settings.MILVUS_PORT,
            "db_name": settings.MILVUS_DB_NAME,
        }
        if settings.MILVUS_USER:
            connection_args["user"] = settings.MILVUS_USER
        if settings.MILVUS_PASSWORD:
            connection_args["password"] = settings.MILVUS_PASSWORD
        connections.connect(alias="default", **connection_args)

    def _get_or_create_collection(self, dim: int) -> Collection:
        """获取或创建统一的 collection"""
        if utility.has_collection(COLLECTION_NAME):
            return Collection(COLLECTION_NAME)

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
            # 文件标识
            FieldSchema(name="file_id", dtype=DataType.INT64),
            # 权限控制字段
            FieldSchema(name="user_id", dtype=DataType.INT64),
            FieldSchema(name="project_id", dtype=DataType.INT64),
            FieldSchema(name="visibility", dtype=DataType.VARCHAR, max_length=32),
        ]
        schema = CollectionSchema(fields, description="readify unified document vectors")
        collection = Collection(COLLECTION_NAME, schema)
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024},
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        # 为过滤字段创建索引以加速查询
        collection.create_index(field_name="file_id", index_params={"index_type": "STL_SORT"})
        collection.create_index(field_name="user_id", index_params={"index_type": "STL_SORT"})
        collection.create_index(field_name="project_id", index_params={"index_type": "STL_SORT"})
        logger.info("[VectorStore] Created unified collection: %s", COLLECTION_NAME)
        return collection

    async def vectorize_text(
        self,
        text: str,
        file_id: int,
        user_id: int = 0,
        project_id: int = 0,
        visibility: str = Visibility.PRIVATE,
    ) -> None:
        texts = self.text_splitter.split_text(text)
        if not texts:
            return
        await self._insert_texts(texts, file_id, user_id, project_id, visibility)

    async def batch_vectorize_texts(
        self,
        texts: List[str],
        file_id: int,
        user_id: int = 0,
        project_id: int = 0,
        visibility: str = Visibility.PRIVATE,
    ) -> None:
        all_texts: List[str] = []
        for text in texts:
            all_texts.extend(self.text_splitter.split_text(text))
        if not all_texts:
            return
        await self._insert_texts(all_texts, file_id, user_id, project_id, visibility)

    async def _insert_texts(
        self,
        texts: List[str],
        file_id: int,
        user_id: int = 0,
        project_id: int = 0,
        visibility: str = Visibility.PRIVATE,
    ) -> None:
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
        except AttributeError:
            embeddings = await asyncio.to_thread(self.embeddings.embed_documents, texts)
        if not embeddings:
            return

        collection = await asyncio.to_thread(
            self._get_or_create_collection,
            len(embeddings[0]),
        )

        batch_size = 500
        total_docs = len(texts)
        # 确保 visibility 是字符串值
        visibility_str = visibility.value if isinstance(visibility, Visibility) else str(visibility)
        for i in range(0, total_docs, batch_size):
            end_idx = min(i + batch_size, total_docs)
            batch_texts = texts[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]
            batch_size_actual = len(batch_texts)
            # 插入数据包含文件ID和权限字段
            data = [
                batch_embeddings,                          # embedding
                batch_texts,                               # content
                [file_id] * batch_size_actual,             # file_id
                [user_id] * batch_size_actual,             # user_id
                [project_id] * batch_size_actual,          # project_id
                [visibility_str] * batch_size_actual,      # visibility
            ]
            await asyncio.to_thread(collection.insert, data)
            logger.info(
                "[VectorStore] Inserted batch %d/%d (docs %d - %d) file_id=%d user_id=%d project_id=%d visibility=%s",
                i // batch_size + 1,
                (total_docs + batch_size - 1) // batch_size,
                i,
                end_idx,
                file_id,
                user_id,
                project_id,
                visibility_str,
            )
        await asyncio.to_thread(collection.flush)

    async def delete_by_file_id(self, file_id: int) -> None:
        """删除指定文件的所有向量数据"""
        if not utility.has_collection(COLLECTION_NAME):
            return

        collection = Collection(COLLECTION_NAME)
        await asyncio.to_thread(collection.load)
        expr = f"file_id == {file_id}"
        await asyncio.to_thread(collection.delete, expr)
        logger.info("[VectorStore] Deleted vectors for file_id=%d", file_id)

    def _build_permission_filter(
        self,
        user_id: Optional[int],
        user_role: str,
        project_id: Optional[int],
        file_id: Optional[int] = None,
        file_ids: Optional[List[int]] = None,
    ) -> str:
        """
        根据用户角色和文件范围构建 Milvus 过滤表达式

        Args:
            user_id: 当前用户ID
            user_role: 用户角色 (user/admin)
            project_id: 当前项目ID（可选）
            file_id: 单个文件ID（可选）
            file_ids: 多个文件ID（可选）

        Returns:
            str: Milvus 过滤表达式
        """
        conditions = []

        # 文件范围过滤
        if file_id is not None:
            conditions.append(f"file_id == {file_id}")
        elif file_ids:
            file_ids_str = ", ".join(str(fid) for fid in file_ids)
            conditions.append(f"file_id in [{file_ids_str}]")

        # 权限过滤
        permission_conditions = []

        # Admin 可以看所有数据
        if user_role == UserRole.ADMIN or user_role == "admin":
            pass  # 无权限过滤
        elif user_id is None:
            # 未登录用户只能看公开数据
            permission_conditions.append(f'visibility == "{Visibility.PUBLIC.value}"')
        else:
            # 普通用户的过滤逻辑
            user_perms = []
            # 1. 自己的所有数据（包括私有）
            user_perms.append(f"(user_id == {user_id})")
            # 2. 项目内可见的数据
            if project_id is not None:
                user_perms.append(
                    f'(project_id == {project_id} && visibility == "{Visibility.PROJECT.value}")'
                )
            # 3. 公开数据
            user_perms.append(f'(visibility == "{Visibility.PUBLIC.value}")')
            permission_conditions.append(f"({' || '.join(user_perms)})")

        if permission_conditions:
            conditions.extend(permission_conditions)

        return " && ".join(conditions) if conditions else ""

    async def search_similar_texts(
        self,
        query_text: str,
        top_k: int = 5,
        user_id: Optional[int] = None,
        user_role: str = UserRole.USER,
        project_id: Optional[int] = None,
        file_id: Optional[int] = None,
        file_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文本，支持权限过滤

        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            user_id: 当前用户ID（用于权限过滤）
            user_role: 用户角色 (user/admin)
            project_id: 当前项目ID（用于项目级权限过滤）
            file_id: 限定单个文件范围（可选）
            file_ids: 限定多个文件范围（可选）

        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        if not utility.has_collection(COLLECTION_NAME):
            return []

        collection = Collection(COLLECTION_NAME)
        await asyncio.to_thread(collection.load)
        try:
            query_embedding = await self.embeddings.aembed_query(query_text)
        except AttributeError:
            query_embedding = await asyncio.to_thread(self.embeddings.embed_query, query_text)

        # 构建过滤表达式（文件范围 + 权限）
        filter_expr = self._build_permission_filter(
            user_id, user_role, project_id, file_id, file_ids
        )

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        search_kwargs: Dict[str, Any] = {
            "data": [query_embedding],
            "anns_field": "embedding",
            "param": search_params,
            "limit": top_k,
            "output_fields": ["content", "file_id", "user_id", "project_id", "visibility"],
        }
        if filter_expr:
            search_kwargs["expr"] = filter_expr
            logger.debug("[VectorStore] Search with filter: %s", filter_expr)

        results = await asyncio.to_thread(
            collection.search,
            **search_kwargs,
        )

        formatted_results: List[Dict[str, Any]] = []
        for hit in results[0]:
            content = self._extract_field(hit, "content")
            formatted_results.append(
                {
                    "content": content or "",
                    "distance": float(hit.distance),
                    "file_id": self._extract_field(hit, "file_id"),
                    "user_id": self._extract_field(hit, "user_id"),
                    "project_id": self._extract_field(hit, "project_id"),
                    "visibility": self._extract_field(hit, "visibility"),
                    "metadata": {},
                }
            )
        formatted_results.sort(key=lambda x: x["distance"])
        return formatted_results

    @staticmethod
    def _extract_field(hit: Any, field_name: str) -> Optional[Any]:
        """从搜索结果中提取字段值"""
        if hasattr(hit, "entity") and hit.entity is not None:
            try:
                return hit.entity.get(field_name)
            except (AttributeError, TypeError, KeyError):
                pass
        try:
            return hit.get(field_name)
        except (AttributeError, TypeError, KeyError):
            return None
