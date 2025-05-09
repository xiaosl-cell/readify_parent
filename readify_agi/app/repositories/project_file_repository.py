from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import and_
import time

from app.models.project_file import ProjectFileDB, ProjectFileCreate
from app.repositories import BaseRepository


class ProjectFileRepository(BaseRepository):
    """项目文件关联仓储层"""
    
    async def create_project_file(self, project_file: ProjectFileCreate) -> ProjectFileDB:
        """创建项目文件关联记录"""
        try:
            db = await self._ensure_session()
            
            now = int(time.time())
            db_project_file = ProjectFileDB(
                **project_file.model_dump(),
                create_time=now,
                update_time=now
            )
            db.add(db_project_file)
            await db.commit()
            await db.refresh(db_project_file)
            return db_project_file
        finally:
            await self._cleanup_session()
    
    async def get_file_ids_by_project_id(self, project_id: int) -> List[int]:
        """通过项目ID获取文件ID列表"""
        try:
            db = await self._ensure_session()
            
            query = select(ProjectFileDB.file_id).where(
                and_(
                    ProjectFileDB.project_id == project_id,
                    ProjectFileDB.deleted == False
                )
            )
            result = await db.execute(query)
            return [row[0] for row in result.all()]
        finally:
            await self._cleanup_session()
    
    async def get_project_file_by_ids(self, project_id: int, file_id: int) -> ProjectFileDB:
        """通过项目ID和文件ID获取关联记录"""
        try:
            db = await self._ensure_session()
            
            query = select(ProjectFileDB).where(
                and_(
                    ProjectFileDB.project_id == project_id,
                    ProjectFileDB.file_id == file_id,
                    ProjectFileDB.deleted == False
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session() 