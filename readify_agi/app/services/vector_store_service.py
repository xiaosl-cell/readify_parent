from typing import List, Dict, Any

import chromadb
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

# 加载环境变量
load_dotenv()


class VectorStoreService:
    def __init__(self):
        """
        初始化向量存储服务
        """
        self.embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY_CHINA,
            base_url=settings.OPENAI_API_BASE_CHINA
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True
        )

        # 初始化 ChromaDB 客户端（使用本地持久化存储）
        self.client = chromadb.PersistentClient(
            path=settings.VECTOR_STORE_DIR
        )

    async def vectorize_text(
        self,
        text: str,
        collection_name: str
    ) -> None:
        """
        将文本向量化并存储
        
        Args:
            text: 要向量化的文本
            collection_name: 集合名称
            
        Returns:
            Chroma: 向量数据库实例
        """
        # 分割文本
        texts = self.text_splitter.split_text(text)
        
        # 获取或创建集合
        collection = self.client.get_or_create_collection(collection_name)
        
        # 生成嵌入向量
        embeddings = self.embeddings.embed_documents(texts)
        
        # 生成文档ID
        ids = [f"doc_{i}" for i in range(len(texts))]
        
        # 添加文档到集合
        collection.add(
            documents=texts,
            embeddings=embeddings,
            ids=ids
        )


    async def batch_vectorize_texts(
        self,
        texts: List[str],
        collection_name: str
    ) -> None:
        """
        批量向量化多个文本
        
        Args:
            texts: 文本列表
            collection_name: 集合名称
            
        Returns:
            Chroma: 向量数据库实例
        """
        # 分割所有文本
        all_texts = []
        for text in texts:
            chunks = self.text_splitter.split_text(text)
            all_texts.extend(chunks)
            
        # 获取或创建集合
        collection = self.client.get_or_create_collection(collection_name)
        
        # 生成文档ID
        ids = [f"doc_{i}" for i in range(len(all_texts))]
        
        # 批量添加文档到集合（分批处理以避免超过最大批次限制）
        batch_size = 500
        total_docs = len(all_texts)
        
        for i in range(0, total_docs, batch_size):
            end_idx = min(i + batch_size, total_docs)
            batch_texts = all_texts[i:end_idx]
            
            # 生成当前批次的嵌入向量
            batch_embeddings = self.embeddings.embed_documents(batch_texts)
            batch_ids = ids[i:end_idx]
            
            collection.add(
                documents=batch_texts,
                embeddings=batch_embeddings,
                ids=batch_ids
            )
            print(f"[向量检索] 已添加批次 {i // batch_size + 1}/{(total_docs + batch_size - 1) // batch_size} (文档 {i} - {end_idx})")


    async def search_similar_texts(
        self,
        query_text: str,
        collection_name: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在指定集合中搜索相似文本
        
        Args:
            query_text: 查询文本
            collection_name: 集合名称
            top_k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        print(f"[向量检索] 开始检索，集合：{collection_name}，查询：{query_text[:50]}...")
        
        try:
            # 获取集合
            collection = self.client.get_collection(collection_name)
            print(f"[向量检索] 成功连接到集合")
            
            # 生成查询向量
            query_embedding = self.embeddings.embed_query(query_text)
            
            # 执行相似度搜索
            print(f"[向量检索] 执行相似度搜索...")
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
            )
            
            # 格式化结果
            formatted_results = []
            for doc, distance in zip(results["documents"][0], results["distances"][0]):
                # 将距离转换为相似度分数 (1 - 归一化距离)
                print(f"[向量检索] 找到结果 - 距离：{distance:.4f}，内容预览：{doc[:50]}...")
                formatted_results.append({
                    "content": doc,
                    "distance": float(distance),
                    "metadata": {}  # ChromaDB 原生客户端的查询结果中如果需要元数据，可以在 include 中添加 "metadatas"
                })
            # 距离升序排序
            formatted_results.sort(key=lambda x: x["distance"])
            
            print(f"[向量检索] 检索完成，返回 {len(formatted_results)} 条结果")
            return formatted_results
            
        except Exception as e:
            print(f"[向量检索] 错误：{str(e)}")
            raise ValueError(f"向量检索失败: {str(e)}")

    async def _get_vector_store(self, collection_name: str) -> Chroma:
        """
        获取向量存储实例
        
        Args:
            collection_name: 集合名称
            
        Returns:
            Chroma: 向量存储实例
        """
        return Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )