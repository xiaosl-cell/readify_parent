from typing import List, Optional, Tuple
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import DocumentDB, DocumentCreate
from app.repositories import BaseRepository
import time

class DocumentRepository(BaseRepository):
    """文档仓库，处理文档块的CRUD操作"""

    async def create(self, document: DocumentCreate) -> DocumentDB:
        """创建文档记录"""
        try:
            db = await self._ensure_session()
            
            current_time = int(time.time())
            db_document = DocumentDB(
                **document.model_dump(),
                create_time=current_time,
                update_time=current_time
            )
            db.add(db_document)
            await db.commit()
            await db.refresh(db_document)
            return db_document
        finally:
            await self._cleanup_session()
        
    async def create_many(self, documents: List[DocumentCreate]) -> List[DocumentDB]:
        """批量创建文档记录"""
        try:
            db = await self._ensure_session()
            
            current_time = int(time.time())
            db_documents = [
                DocumentDB(
                    **doc.model_dump(),
                    create_time=current_time,
                    update_time=current_time
                )
                for doc in documents
            ]
            db.add_all(db_documents)
            await db.commit()
            for doc in db_documents:
                await db.refresh(doc)
            return db_documents
        finally:
            await self._cleanup_session()
        
    async def get_by_file_id(self, file_id: int) -> List[DocumentDB]:
        """获取指定文件的所有文档块"""
        try:
            db = await self._ensure_session()
            
            query = select(DocumentDB).where(
                DocumentDB.file_id == file_id,
                DocumentDB.deleted == False
            ).order_by(DocumentDB.sequence)
            result = await db.execute(query)
            return list(result.scalars().all())
        finally:
            await self._cleanup_session()
        
    async def get_by_file_id_paginated(self, file_id: int, page: int = 1, page_size: int = 10) -> Tuple[List[DocumentDB], int]:
        """分页获取指定文件的文档块"""
        try:
            db = await self._ensure_session()
            
            # 计算总记录数
            count_query = select(func.count()).where(
                DocumentDB.file_id == file_id,
                DocumentDB.deleted == False
            )
            total_count = await db.execute(count_query)
            total_count = total_count.scalar() or 0
            
            # 如果没有记录，直接返回
            if total_count == 0:
                return [], 0
                
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询分页数据
            query = select(DocumentDB).where(
                DocumentDB.file_id == file_id,
                DocumentDB.deleted == False
            ).order_by(DocumentDB.sequence).offset(offset).limit(page_size)
            
            result = await db.execute(query)
            documents = list(result.scalars().all())
            
            return documents, total_count
        finally:
            await self._cleanup_session()
            
    async def get_by_id(self, document_id: int) -> Optional[DocumentDB]:
        """通过ID获取文档"""
        try:
            db = await self._ensure_session()
            
            query = select(DocumentDB).where(
                DocumentDB.id == document_id,
                DocumentDB.deleted == False
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session()
            
    async def delete(self, document_id: int) -> bool:
        """软删除指定文档"""
        try:
            db = await self._ensure_session()
            
            current_time = int(time.time())
            stmt = update(DocumentDB).where(
                DocumentDB.id == document_id,
                DocumentDB.deleted == False
            ).values(
                deleted=True,
                update_time=current_time
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        finally:
            await self._cleanup_session()
            
    async def delete_by_file_id(self, file_id: int) -> int:
        """删除指定文件的所有文档块"""
        try:
            db = await self._ensure_session()
            
            # 获取要更新的文档ID集合
            query = select(DocumentDB.id).where(
                DocumentDB.file_id == file_id,
                DocumentDB.deleted == False
            )
            result = await db.execute(query)
            document_ids = [row[0] for row in result.all()]
            
            # 如果没有记录，直接返回
            if not document_ids:
                return 0
                
            # 批量软删除
            current_time = int(time.time())
            stmt = update(DocumentDB).where(
                DocumentDB.id.in_(document_ids)
            ).values(
                deleted=True,
                update_time=current_time
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount
        finally:
            await self._cleanup_session()
            
    async def update_label(self, document_id: int, label: str) -> bool:
        """更新文档标签"""
        try:
            db = await self._ensure_session()
            
            current_time = int(time.time())
            stmt = update(DocumentDB).where(
                DocumentDB.id == document_id,
                DocumentDB.deleted == False
            ).values(
                label=label,
                update_time=current_time
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        finally:
            await self._cleanup_session()
            
    async def update_many_labels(self, document_ids: List[int], labels: List[str]) -> int:
        """批量更新文档标签"""
        try:
            db = await self._ensure_session()
            
            if len(document_ids) != len(labels):
                raise ValueError("文档ID列表和标签列表长度必须相同")
                
            if not document_ids:
                return 0
                
            current_time = int(time.time())
            updated_count = 0
            
            # 逐个更新标签
            for doc_id, label in zip(document_ids, labels):
                stmt = update(DocumentDB).where(
                    DocumentDB.id == doc_id,
                    DocumentDB.deleted == False
                ).values(
                    label=label,
                    update_time=current_time
                )
                result = await db.execute(stmt)
                updated_count += result.rowcount
                
            await db.commit()
            return updated_count
        finally:
            await self._cleanup_session() 