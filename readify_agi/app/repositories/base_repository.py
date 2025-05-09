"""
基础仓库类文件
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker


class BaseRepository:
    """
    基础仓库类，所有仓库类的父类，提供统一的数据库会话管理
    """
    
    def __init__(self, db: AsyncSession = None):
        """
        初始化仓库
        
        Args:
            db: 可选的数据库会话，如果提供则使用该会话，否则使用会话工厂创建新会话
        """
        self.db = db
        self._own_session = db is None  # 标记是否拥有自己的会话
        
    async def _ensure_session(self) -> AsyncSession:
        """
        确保有可用的数据库会话
        
        Returns:
            AsyncSession: 数据库会话
        """
        if self.db is None:
            self.db = async_session_maker()
            self._own_session = True
        return self.db
    
    async def _cleanup_session(self):
        """
        如果使用自己创建的会话，则在操作完成后关闭会话
        """
        if self._own_session and self.db is not None:
            await self.db.close()
            self.db = None
            self._own_session = False 