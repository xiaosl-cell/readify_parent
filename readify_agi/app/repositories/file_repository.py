from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import and_
import time
from app.models.file import FileDB, FileCreate
from app.repositories import BaseRepository

class FileRepository(BaseRepository):
    """文件仓储层"""
    
    async def create_file(self, file: FileCreate) -> FileDB:
        """创建文件记录"""
        try:
            db = await self._ensure_session()
            now = int(time.time())
            db_file = FileDB(
                **file.dict(),
                create_time=now,
                update_time=now
            )
            db.add(db_file)
            await db.commit()
            await db.refresh(db_file)
            return db_file
        finally:
            await self._cleanup_session()
        
    async def get_file_by_id(self, file_id: int) -> Optional[FileDB]:
        """通过ID获取文件"""
        try:
            db = await self._ensure_session()
            query = select(FileDB).where(
                and_(
                    FileDB.id == file_id,
                    FileDB.deleted == False
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session()
        
    async def get_file_by_md5(self, md5: str) -> Optional[FileDB]:
        """通过MD5获取文件"""
        try:
            db = await self._ensure_session()
            query = select(FileDB).where(
                and_(
                    FileDB.md5 == md5,
                    FileDB.deleted == False
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session()
        
    async def get_all_files(self, skip: int = 0, limit: int = 100) -> List[FileDB]:
        """获取所有文件"""
        try:
            db = await self._ensure_session()
            query = select(FileDB).where(FileDB.deleted == False).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        finally:
            await self._cleanup_session()
            
    async def delete_file(self, file_id: int) -> bool:
        """标记删除文件"""
        try:
            db = await self._ensure_session()
            now = int(time.time())
            stmt = update(FileDB).where(
                and_(
                    FileDB.id == file_id,
                    FileDB.deleted == False
                )
            ).values(
                deleted=True,
                update_time=now
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        finally:
            await self._cleanup_session()
            
    async def update_vectorized_status(self, file_id: int, vectorized: bool = True) -> bool:
        """更新文件向量化状态"""
        try:
            db = await self._ensure_session()
            now = int(time.time())
            stmt = update(FileDB).where(
                and_(
                    FileDB.id == file_id,
                    FileDB.deleted == False
                )
            ).values(
                vectorized=vectorized,
                update_time=now
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        finally:
            await self._cleanup_session() 