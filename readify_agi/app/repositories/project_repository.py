from typing import Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.project import ProjectDB, ProjectCreate
from app.repositories import BaseRepository
import time

class ProjectRepository(BaseRepository):
    """项目仓储层"""
    
    async def create_project(self, project: ProjectCreate) -> ProjectDB:
        """创建项目"""
        try:
            db = await self._ensure_session()
            
            now = int(time.time())
            db_project = ProjectDB(
                **project.model_dump(),
                create_time=now,
                update_time=now
            )
            db.add(db_project)
            await db.commit()
            await db.refresh(db_project)
            return db_project
        finally:
            await self._cleanup_session()
    
    async def get_project_by_id(self, project_id: int) -> Optional[ProjectDB]:
        """通过ID获取项目"""
        try:
            db = await self._ensure_session()
            
            query = select(ProjectDB).where(
                ProjectDB.id == project_id,
                ProjectDB.deleted == False
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session()
    
    async def get_project_info(self, project_id: int) -> Optional[Dict]:
        """获取项目基本信息"""
        try:
            db = await self._ensure_session()
            
            project = await self.get_project_by_id(project_id)
            if not project:
                return None
                
            return {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "create_time": project.create_time,
                "update_time": project.update_time
            }
        finally:
            await self._cleanup_session()
    
    async def get_all_projects(self, skip: int = 0, limit: int = 100) -> List[ProjectDB]:
        """获取所有项目"""
        try:
            db = await self._ensure_session()
            
            query = select(ProjectDB).where(
                ProjectDB.deleted == False
            ).offset(skip).limit(limit)
            result = await db.execute(query)
            return list(result.scalars().all())
        finally:
            await self._cleanup_session()
    
    async def update_project(self, project_id: int, project_update: Dict) -> bool:
        """更新项目信息"""
        try:
            db = await self._ensure_session()
            
            # 添加更新时间
            project_update["update_time"] = int(time.time())
            
            # 执行更新
            stmt = update(ProjectDB).where(
                ProjectDB.id == project_id,
                ProjectDB.deleted == False
            ).values(**project_update)
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        finally:
            await self._cleanup_session()
    
    async def delete_project(self, project_id: int) -> bool:
        """删除项目（软删除）"""
        try:
            db = await self._ensure_session()
            
            stmt = update(ProjectDB).where(
                ProjectDB.id == project_id,
                ProjectDB.deleted == False
            ).values(
                deleted=True,
                update_time=int(time.time())
            )
            result = await db.execute(stmt)
            await db.commit()
            return result.rowcount > 0
        finally:
            await self._cleanup_session() 