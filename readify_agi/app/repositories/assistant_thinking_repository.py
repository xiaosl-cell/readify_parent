from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant_thinking import AssistantThinkingDB
from app.repositories import BaseRepository


class AssistantThinkingRepository(BaseRepository):
    """
    AI助手思考过程仓储层
    """

    async def create(
        self,
        project_id: int,
        user_message_id: int,
        content: str
    ) -> AssistantThinkingDB:
        """
        创建新的思考过程记录
        
        Args:
            project_id: 工程ID
            user_message_id: 对应的用户消息ID
            content: 思考过程内容
            
        Returns:
            新创建的思考过程记录
        """
        try:
            db = await self._ensure_session()
            
            new_thinking = AssistantThinkingDB(
                project_id=project_id,
                user_message_id=user_message_id,
                content=content
            )
            
            db.add(new_thinking)
            await db.commit()
            await db.refresh(new_thinking)
            
            return new_thinking
        finally:
            await self._cleanup_session()

    async def get_by_user_message(
        self,
        user_message_id: int
    ) -> Optional[AssistantThinkingDB]:
        """
        通过用户消息ID获取思考过程
        
        Args:
            user_message_id: 用户消息ID
            
        Returns:
            与用户消息关联的思考过程，如果不存在则返回None
        """
        try:
            db = await self._ensure_session()
            
            query = select(AssistantThinkingDB).where(
                AssistantThinkingDB.user_message_id == user_message_id
            )
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session() 