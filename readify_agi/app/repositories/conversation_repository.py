from typing import List

from sqlalchemy import select, desc, func, update

from app.models.conversation import ConversationHistoryDB
from app.repositories import BaseRepository


class ConversationRepository(BaseRepository):
    """
    对话历史仓储层
    """

    async def create(
        self,
        project_id: int,
        message_type: str,
        content: str,
        priority: int = 1,
        is_included_in_context: bool = True
    ) -> ConversationHistoryDB:
        """
        创建新的对话记录
        
        Args:
            project_id: 工程ID
            message_type: 消息类型
            content: 消息内容
            priority: 优先级
            is_included_in_context: 是否包含在上下文中
            
        Returns:
            新创建的对话记录
        """
        try:
            db = await self._ensure_session()
            
            # 获取当前工程的最大序号
            stmt = select(func.max(ConversationHistoryDB.sequence)).where(
                ConversationHistoryDB.project_id == project_id
            )
            result = await db.execute(stmt)
            max_sequence = result.scalar() or 0
            
            # 创建新消息记录
            new_message = ConversationHistoryDB(
                project_id=project_id,
                message_type=message_type,
                content=content,
                priority=priority,
                is_included_in_context=is_included_in_context,
                sequence=max_sequence + 1
            )
            
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            
            return new_message
        finally:
            await self._cleanup_session()

    async def get_project_history(
        self,
        project_id: int,
        limit: int = 100,
        only_context: bool = True
    ) -> List[ConversationHistoryDB]:
        """
        获取项目对话历史
        
        Args:
            project_id: 工程ID
            limit: 返回的最大记录数
            only_context: 是否只返回被标记为包含在上下文中的消息
            
        Returns:
            对话历史记录列表
        """
        try:
            db = await self._ensure_session()
            
            query = select(ConversationHistoryDB).where(
                ConversationHistoryDB.project_id == project_id
            )
            
            if only_context:
                query = query.where(ConversationHistoryDB.is_included_in_context == True)
                
            query = query.order_by(desc(ConversationHistoryDB.sequence)).limit(limit)
            
            result = await db.execute(query)
            return list(result.scalars().all())
        finally:
            await self._cleanup_session()

    async def trim_context_messages(
        self,
        project_id: int,
        max_context_messages: int = 50
    ) -> int:
        """
        修剪项目的上下文消息数量，保留最新的N条记录在上下文中
        
        Args:
            project_id: 工程ID
            max_context_messages: 保留在上下文中的最大消息数
            
        Returns:
            int: 从上下文中移除的记录数
        """
        try:
            db = await self._ensure_session()
            
            # 获取项目中所有包含在上下文中的消息ID，按序号排序
            context_query = select(
                ConversationHistoryDB.id,
                ConversationHistoryDB.sequence
            ).where(
                ConversationHistoryDB.project_id == project_id,
                ConversationHistoryDB.is_included_in_context == True
            ).order_by(desc(ConversationHistoryDB.sequence))
            
            context_result = await db.execute(context_query)
            context_messages = context_result.all()
            
            # 如果消息数量没有超过限制，不需要修剪
            if len(context_messages) <= max_context_messages:
                return 0
            
            # 获取需要从上下文中移除的消息ID
            messages_to_remove = context_messages[max_context_messages:]
            ids_to_remove = [msg.id for msg in messages_to_remove]
            
            # 更新这些消息，将它们从上下文中移除
            if ids_to_remove:
                update_stmt = update(ConversationHistoryDB).where(
                    ConversationHistoryDB.id.in_(ids_to_remove)
                ).values(
                    is_included_in_context=False
                )
                
                result = await db.execute(update_stmt)
                await db.commit()
                
                return result.rowcount
            
            return 0
        finally:
            await self._cleanup_session()

    async def exclude_from_context(
        self,
        message_id: int
    ) -> bool:
        """
        将指定消息从上下文中排除
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            db = await self._ensure_session()
            
            # 更新消息状态，将其从上下文中排除
            update_stmt = update(ConversationHistoryDB).where(
                ConversationHistoryDB.id == message_id
            ).values(
                is_included_in_context=False
            )
            
            result = await db.execute(update_stmt)
            await db.commit()
            
            return result.rowcount > 0
        finally:
            await self._cleanup_session()

    async def include_in_context(
        self,
        message_id: int
    ) -> bool:
        """
        将指定消息添加到上下文中
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 操作是否成功
        """
        try:
            db = await self._ensure_session()
            
            # 更新消息状态，将其添加到上下文中
            update_stmt = update(ConversationHistoryDB).where(
                ConversationHistoryDB.id == message_id
            ).values(
                is_included_in_context=True
            )
            
            result = await db.execute(update_stmt)
            await db.commit()
            
            return result.rowcount > 0
        finally:
            await self._cleanup_session() 