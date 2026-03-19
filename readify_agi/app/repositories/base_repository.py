"""
基础仓库类文件
"""

import asyncio
from typing import Dict, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker


class BaseRepository:
    """
    基础仓库类，所有仓库类的父类，提供统一的数据库会话管理。

    关键约束：
    - 若外部显式传入 db，则整个仓库实例始终复用该会话；
    - 若未传入 db，则每个 asyncio Task 使用独立会话；
    - 同一 Task 内允许嵌套复用同一会话，并用引用计数保证只在最外层关闭。
    """

    def __init__(self, db: AsyncSession = None):
        """
        初始化仓库

        Args:
            db: 可选的数据库会话，如果提供则使用该会话，否则按 Task 延迟创建独立会话
        """
        self.db = db
        self._external_session = db is not None
        self._task_sessions: Dict[int, Tuple[AsyncSession, int]] = {}

    def _get_task_key(self) -> int:
        task = asyncio.current_task()
        if task is None:
            raise RuntimeError("当前不在有效的 asyncio Task 中，无法管理仓库会话")
        return id(task)

    async def _ensure_session(self) -> AsyncSession:
        """
        确保有可用的数据库会话

        Returns:
            AsyncSession: 数据库会话
        """
        if self._external_session:
            return self.db

        task_key = self._get_task_key()
        session_entry = self._task_sessions.get(task_key)
        if session_entry is None:
            session = async_session_maker()
            self._task_sessions[task_key] = (session, 1)
            return session

        session, ref_count = session_entry
        self._task_sessions[task_key] = (session, ref_count + 1)
        return session

    async def _cleanup_session(self):
        """
        清理当前 Task 使用的数据库会话。
        对外部传入的会话不做关闭。
        """
        if self._external_session:
            return

        task_key = self._get_task_key()
        session_entry = self._task_sessions.get(task_key)
        if session_entry is None:
            return

        session, ref_count = session_entry
        if ref_count <= 1:
            await session.close()
            self._task_sessions.pop(task_key, None)
        else:
            self._task_sessions[task_key] = (session, ref_count - 1)

    async def close(self):
        """显式关闭当前仓库持有的会话。"""
        if self._external_session:
            if self.db is not None:
                await self.db.close()
                self.db = None
            self._external_session = False
            return

        for task_key, (session, _) in list(self._task_sessions.items()):
            await session.close()
            self._task_sessions.pop(task_key, None)
