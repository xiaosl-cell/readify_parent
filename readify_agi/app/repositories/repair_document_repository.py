from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.repair_document import RepairDocumentDB, RepairDocumentCreate
import time

class RepairDocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create(self, document: RepairDocumentCreate) -> RepairDocumentDB:
        """创建修复文档记录"""
        current_time = int(time.time())
        db_document = RepairDocumentDB(
            **document.model_dump(),
            create_time=current_time,
            update_time=current_time
        )
        self.db.add(db_document)
        await self.db.commit()
        await self.db.refresh(db_document)
        return db_document
        
    async def create_many(self, documents: List[RepairDocumentCreate]) -> List[RepairDocumentDB]:
        """批量创建修复文档记录"""
        current_time = int(time.time())
        db_documents = [
            RepairDocumentDB(
                **doc.model_dump(),
                create_time=current_time,
                update_time=current_time
            )
            for doc in documents
        ]
        self.db.add_all(db_documents)
        await self.db.commit()
        for doc in db_documents:
            await self.db.refresh(doc)
        return db_documents
        
    async def get_by_file_id(self, file_id: int) -> List[RepairDocumentDB]:
        """获取指定文件的所有修复文档块"""
        query = select(RepairDocumentDB).where(
            RepairDocumentDB.file_id == file_id,
            RepairDocumentDB.deleted == False
        ).order_by(RepairDocumentDB.sequence)
        result = await self.db.execute(query)
        return list(result.scalars().all())
        
    async def get_by_id(self, document_id: int) -> Optional[RepairDocumentDB]:
        """获取指定ID的修复文档"""
        query = select(RepairDocumentDB).where(
            RepairDocumentDB.id == document_id,
            RepairDocumentDB.deleted == False
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
        
    async def delete(self, document_id: int) -> bool:
        """删除修复文档（软删除）"""
        document = await self.get_by_id(document_id)
        if not document:
            return False
            
        document.deleted = True
        document.update_time = int(time.time())
        await self.db.commit()
        return True 