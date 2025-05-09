from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import and_
import time
from app.models.mind_map import MindMapDB, MindMapCreate
from app.repositories import BaseRepository

class MindMapRepository(BaseRepository):
    """思维导图仓储层"""
    
    async def get_by_id(self, mind_map_id: int) -> Optional[MindMapDB]:
        """根据ID获取思维导图
        
        Args:
            mind_map_id: 思维导图ID
            
        Returns:
            思维导图对象，如果不存在则返回None
        """
        try:
            db = await self._ensure_session()
            query = select(MindMapDB).where(
                and_(
                    MindMapDB.id == mind_map_id,
                    MindMapDB.is_deleted == False
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session() 