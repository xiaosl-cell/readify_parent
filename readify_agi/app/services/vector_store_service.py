import asyncio
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

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


class Visibility(str, Enum):
    """Visibility level for stored vectors."""

    PRIVATE = "private"
    PROJECT = "project"
    PUBLIC = "public"


class UserRole(str, Enum):
    """User role used for permission filtering."""

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

    @property
    def collection_name(self) -> str:
        return settings.EMBEDDING_COLLECTION_NAME

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
        """Get the active collection or create it with the current embedding dimension."""
        if utility.has_collection(self.collection_name):
            collection = Collection(self.collection_name)
            existing_dim = self._get_embedding_dim(collection)
            if existing_dim is not None and existing_dim != dim:
                raise RuntimeError(
                    f"Milvus collection '{self.collection_name}' embedding dim mismatch: "
                    f"existing={existing_dim}, current_model={settings.EMBEDDING_MODEL}, current_dim={dim}. "
                    "Use a new EMBEDDING_COLLECTION_NAME or rebuild vectors with the new embedding model."
                )
            return collection

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
            FieldSchema(name="file_id", dtype=DataType.INT64),
            FieldSchema(name="user_id", dtype=DataType.INT64),
            FieldSchema(name="project_id", dtype=DataType.INT64),
            FieldSchema(name="visibility", dtype=DataType.VARCHAR, max_length=32),
        ]
        schema = CollectionSchema(fields, description="readify unified document vectors")
        collection = Collection(self.collection_name, schema)
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024},
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        collection.create_index(field_name="file_id", index_params={"index_type": "STL_SORT"})
        collection.create_index(field_name="user_id", index_params={"index_type": "STL_SORT"})
        collection.create_index(field_name="project_id", index_params={"index_type": "STL_SORT"})
        logger.info("[VectorStore] Created unified collection: %s", self.collection_name)
        return collection

    @staticmethod
    def _get_embedding_dim(collection: Collection) -> Optional[int]:
        for field in collection.schema.fields:
            if field.name != "embedding":
                continue
            params = getattr(field, "params", None) or {}
            dim = params.get("dim")
            if dim is None:
                dim = getattr(field, "dim", None)
            return int(dim) if dim is not None else None
        return None

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
        embeddings = await self._embed_documents_in_batches(texts)
        if not embeddings:
            return

        collection = await asyncio.to_thread(self._get_or_create_collection, len(embeddings[0]))

        insert_batch_size = 500
        total_docs = len(texts)
        visibility_str = visibility.value if isinstance(visibility, Visibility) else str(visibility)
        for i in range(0, total_docs, insert_batch_size):
            end_idx = min(i + insert_batch_size, total_docs)
            batch_texts = texts[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]
            batch_size_actual = len(batch_texts)
            data = [
                batch_embeddings,
                batch_texts,
                [file_id] * batch_size_actual,
                [user_id] * batch_size_actual,
                [project_id] * batch_size_actual,
                [visibility_str] * batch_size_actual,
            ]
            await asyncio.to_thread(collection.insert, data)
            logger.info(
                "[VectorStore] Inserted batch %d/%d (docs %d - %d) file_id=%d user_id=%d project_id=%d visibility=%s",
                i // insert_batch_size + 1,
                (total_docs + insert_batch_size - 1) // insert_batch_size,
                i,
                end_idx,
                file_id,
                user_id,
                project_id,
                visibility_str,
            )
        await asyncio.to_thread(collection.flush)

    async def _embed_documents_in_batches(self, texts: List[str]) -> List[List[float]]:
        request_batch_size = max(1, settings.EMBEDDING_REQUEST_BATCH_SIZE)
        total_docs = len(texts)
        all_embeddings: List[List[float]] = []

        for i in range(0, total_docs, request_batch_size):
            end_idx = min(i + request_batch_size, total_docs)
            batch_texts = texts[i:end_idx]
            try:
                batch_embeddings = await self.embeddings.aembed_documents(batch_texts)
            except AttributeError:
                batch_embeddings = await asyncio.to_thread(self.embeddings.embed_documents, batch_texts)
            all_embeddings.extend(batch_embeddings)
            logger.info(
                "[VectorStore] Embedded batch %d/%d (docs %d - %d) model=%s",
                i // request_batch_size + 1,
                (total_docs + request_batch_size - 1) // request_batch_size,
                i,
                end_idx,
                settings.EMBEDDING_MODEL,
            )

        return all_embeddings

    async def delete_by_file_id(self, file_id: int) -> None:
        """Delete all vectors for a file."""
        if not utility.has_collection(self.collection_name):
            return

        collection = Collection(self.collection_name)
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
        conditions = []

        if file_id is not None:
            conditions.append(f"file_id == {file_id}")
        elif file_ids:
            file_ids_str = ", ".join(str(fid) for fid in file_ids)
            conditions.append(f"file_id in [{file_ids_str}]")

        permission_conditions = []

        if user_role == UserRole.ADMIN or user_role == "admin":
            pass
        elif user_id is None:
            permission_conditions.append(f'visibility == "{Visibility.PUBLIC.value}"')
        else:
            user_perms = []
            user_perms.append(f"(user_id == {user_id})")
            if project_id is not None:
                user_perms.append(
                    f'(project_id == {project_id} && visibility == "{Visibility.PROJECT.value}")'
                )
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
        if not utility.has_collection(self.collection_name):
            return []

        collection = Collection(self.collection_name)
        await asyncio.to_thread(collection.load)
        try:
            query_embedding = await self.embeddings.aembed_query(query_text)
        except AttributeError:
            query_embedding = await asyncio.to_thread(self.embeddings.embed_query, query_text)

        filter_expr = self._build_permission_filter(user_id, user_role, project_id, file_id, file_ids)

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

        results = await asyncio.to_thread(collection.search, **search_kwargs)

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
        if hasattr(hit, "entity") and hit.entity is not None:
            try:
                return hit.entity.get(field_name)
            except (AttributeError, TypeError, KeyError):
                pass
        try:
            return hit.get(field_name)
        except (AttributeError, TypeError, KeyError):
            return None
