import logging
import os
from pathlib import Path
from typing import List

from fastapi import HTTPException
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.models.document import DocumentCreate
from app.repositories.document_repository import DocumentRepository
from app.repositories.file_repository import FileRepository
from app.services.llama_parse_service import LlamaParseService
from app.services.object_storage_service import ObjectStorageService

logger = logging.getLogger(__name__)


class DocumentService:
    """文档服务层"""

    def __init__(
        self,
        document_repository: DocumentRepository,
        file_repository: FileRepository,
        llama_parse_service: LlamaParseService
    ):
        self.document_repository = document_repository
        self.file_repository = file_repository
        self.llama_parse_service = llama_parse_service
        self.object_storage_service = ObjectStorageService()

    async def parse_and_save(self, file_id: int) -> None:
        """
        解析文件并保存到数据库

        Args:
            file_id: 文件ID
        """
        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="文件不存在")

        if file.storage_type != "minio":
            raise HTTPException(status_code=400, detail="Unsupported storage type")

        temp_path = await self.object_storage_service.download_to_temp(
            file.storage_bucket,
            file.storage_key
        )
        try:
            documents = await self.llama_parse_service.parse_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        logger.info("解析文件 '%s' (ID:%d) 得到 %d 个文档块", file.original_name, file_id, len(documents))

        doc_creates = []
        for i, doc in enumerate(documents):
            content = doc.get_content()
            if not content:
                continue

            logger.info("为文档块 %d/%d 生成标签...", i + 1, len(documents))
            label = await self._generate_label_with_4o_mini(content)

            doc_create = DocumentCreate(
                file_id=file_id,
                content=content,
                sequence=i,
                label=label
            )
            doc_creates.append(doc_create)

        if doc_creates:
            docs = await self.document_repository.create_many(doc_creates)
            logger.info("成功保存 %d 个文档块到数据库，并生成了标签", len(docs))
        else:
            logger.info("没有有效的文档内容需要保存")

    async def get_file_documents(self, file_id: int) -> List[str]:
        """
        获取文件的所有文档内容

        Args:
            file_id: 文件ID

        Returns:
            List[str]: 文档内容列表
        """
        documents = await self.document_repository.get_by_file_id(file_id)
        return [doc.content for doc in documents]

    async def generate_label(self, document_id: int) -> str:
        """
        为文档生成标签

        Args:
            document_id: 文档ID

        Returns:
            str: 生成的标签
        """
        document = await self.document_repository.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        label = await self._generate_label_with_4o_mini(document.content)
        await self.document_repository.update_label(document_id, label)
        return label

    async def generate_labels_for_file(self, file_id: int, force_regenerate: bool = False) -> int:
        """
        为文件的所有文档生成标签

        Args:
            file_id: 文件ID
            force_regenerate: 是否强制重新生成已有标签

        Returns:
            int: 成功生成标签的文档数量
        """
        file = await self.file_repository.get_file_by_id(file_id)
        if not file:
            logger.warning("文件ID:%d 不存在", file_id)
            return 0

        logger.info("开始处理文件: '%s' (ID:%d)", file.original_name, file_id)

        documents = await self.document_repository.get_by_file_id(file_id)
        if not documents:
            logger.warning("文件ID:%d 没有找到文档", file_id)
            return 0

        total_docs = len(documents)
        logger.info("开始为文件 '%s' (ID:%d)的%d个文档生成标签", file.original_name, file_id, total_docs)

        document_ids = []
        labels = []

        for idx, doc in enumerate(documents, 1):
            try:
                if doc.label and not force_regenerate:
                    logger.debug("文档 [%d/%d] ID:%d 已有标签: %s...", idx, total_docs, doc.id, doc.label[:30])
                    continue

                logger.info("处理文档 [%d/%d] ID:%d", idx, total_docs, doc.id)
                label = await self._generate_label_with_4o_mini(doc.content)
                if label:
                    document_ids.append(doc.id)
                    labels.append(label)
                else:
                    logger.warning("文档ID:%d 生成的标签为空", doc.id)

                if idx % 10 == 0 or idx == total_docs:
                    logger.info("进度: %d/%d (%.1f%%)", idx, total_docs, idx / total_docs * 100)

            except Exception as e:
                logger.error("处理文档ID:%d时出错: %s", doc.id, str(e))
                continue

        if document_ids:
            updated_count = await self.document_repository.update_many_labels(document_ids, labels)
            logger.info("成功更新%d个文档的标签", updated_count)
            return updated_count
        else:
            logger.info("没有文档需要更新标签")
            return 0

    async def _generate_label_with_4o_mini(self, content: str) -> str:
        """
        使用4o-mini模型生成标签

        Args:
            content: 文档内容

        Returns:
            str: 生成的标签
        """
        from app.core.prompt_template_client import get_prompt_client
        client = get_prompt_client()
        prompt_template = (await client.get_template("label")).strip()

        try:
            chat = ChatOpenAI(
                model=settings.LLM_MODEL_NAME,
                temperature=0.5,
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE,
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个文本标签生成助手，请生成简短的标签来概括文本内容。"),
                ("human", prompt_template)
            ])

            chain = prompt | chat
            response = await chain.ainvoke({"content": content})

            label = response.content.strip()

            if len(label) > 50:
                label = label[:50]

            return label

        except Exception as e:
            logger.error("生成标签时发生错误: %s", str(e), exc_info=True)
            return ""
