from typing import List, Dict, Any, Optional
import asyncio
import re

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


class VectorStoreService:
    def __init__(self) -> None:
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_API_BASE,
            # 禁用 token 级别的长度检查，直接使用文本字符串
            # 因为我们已经用 text_splitter 处理了文本分割
            # 这样可以避免 langchain 将文本转换为 token IDs（Qwen API 不支持）
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

    def _get_or_create_collection(self, collection_name: str, dim: int) -> Collection:
        # Milvus collection 名称只能包含字母、数字和下划线，且必须以字母或下划线开头
        # 添加固定前缀确保名称合法
        collection_name = f"rf_{collection_name}"
        collection_name = collection_name.replace("-", "_").replace(".", "_")
        # 移除其他非法字符，只保留字母、数字和下划线
        collection_name = re.sub(r'[^a-zA-Z0-9_]', '_', collection_name)
        
        if utility.has_collection(collection_name):
            return Collection(collection_name)

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
        ]
        schema = CollectionSchema(fields, description="readify vectors")
        collection = Collection(collection_name, schema)
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024},
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        return collection

    async def vectorize_text(self, text: str, collection_name: str) -> None:
        texts = self.text_splitter.split_text(text)
        if not texts:
            return
        await self._insert_texts(texts, collection_name)

    async def batch_vectorize_texts(self, texts: List[str], collection_name: str) -> None:
        all_texts: List[str] = []
        for text in texts:
            all_texts.extend(self.text_splitter.split_text(text))
        if not all_texts:
            return
        await self._insert_texts(all_texts, collection_name)

    async def _insert_texts(self, texts: List[str], collection_name: str) -> None:
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
        except AttributeError:
            embeddings = await asyncio.to_thread(self.embeddings.embed_documents, texts)
        if not embeddings:
            return

        collection = await asyncio.to_thread(
            self._get_or_create_collection,
            collection_name,
            len(embeddings[0]),
        )

        batch_size = 500
        total_docs = len(texts)
        for i in range(0, total_docs, batch_size):
            end_idx = min(i + batch_size, total_docs)
            batch_texts = texts[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]
            await asyncio.to_thread(collection.insert, [batch_embeddings, batch_texts])
            print(
                f"[VectorStore] Inserted batch {i // batch_size + 1}"
                f"/{(total_docs + batch_size - 1) // batch_size}"
                f" (docs {i} - {end_idx})"
            )
        await asyncio.to_thread(collection.flush)

    async def search_similar_texts(
        self,
        query_text: str,
        collection_name: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        # Milvus collection 名称规范化，与创建时保持一致
        collection_name = f"rf_{collection_name}"
        collection_name = collection_name.replace("-", "_").replace(".", "_")
        collection_name = re.sub(r'[^a-zA-Z0-9_]', '_', collection_name)
        
        if not utility.has_collection(collection_name):
            return []

        collection = Collection(collection_name)
        await asyncio.to_thread(collection.load)
        try:
            query_embedding = await self.embeddings.aembed_query(query_text)
        except AttributeError:
            query_embedding = await asyncio.to_thread(self.embeddings.embed_query, query_text)
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = await asyncio.to_thread(
            collection.search,
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["content"],
        )

        formatted_results: List[Dict[str, Any]] = []
        for hit in results[0]:
            content = self._extract_content(hit)
            formatted_results.append(
                {
                    "content": content or "",
                    "distance": float(hit.distance),
                    "metadata": {},
                }
            )
        formatted_results.sort(key=lambda x: x["distance"])
        return formatted_results

    @staticmethod
    def _extract_content(hit: Any) -> Optional[str]:
        if hasattr(hit, "entity") and hit.entity is not None:
            try:
                return hit.entity.get("content")
            except Exception:
                pass
        try:
            return hit.get("content")
        except Exception:
            return None



