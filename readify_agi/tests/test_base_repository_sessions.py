import asyncio

import pytest

from app.repositories.base_repository import BaseRepository
import app.repositories.base_repository as base_repository_module


class DummySession:
    def __init__(self, name):
        self.name = name
        self.close_count = 0

    async def close(self):
        self.close_count += 1


class DummyRepo(BaseRepository):
    async def nested_inner(self):
        session = await self._ensure_session()
        try:
            return session
        finally:
            await self._cleanup_session()

    async def nested_outer(self):
        session = await self._ensure_session()
        try:
            inner_session = await self.nested_inner()
            return session, inner_session, session.close_count
        finally:
            close_count_before_cleanup = session.close_count
            await self._cleanup_session()
            self._last_close_count_before_outer_cleanup = close_count_before_cleanup

    async def concurrent_use(self, start_event, release_event):
        session = await self._ensure_session()
        try:
            start_event.set()
            await release_event.wait()
            return session
        finally:
            await self._cleanup_session()


@pytest.mark.asyncio
async def test_base_repository_reuses_same_session_within_same_task(monkeypatch):
    created_sessions = []

    def fake_session_maker():
        session = DummySession(f"s{len(created_sessions)}")
        created_sessions.append(session)
        return session

    monkeypatch.setattr(base_repository_module, "async_session_maker", fake_session_maker)

    repo = DummyRepo()
    outer_session, inner_session, close_count_during_nested = await repo.nested_outer()

    assert outer_session is inner_session
    assert len(created_sessions) == 1
    assert close_count_during_nested == 0
    assert repo._last_close_count_before_outer_cleanup == 0
    assert created_sessions[0].close_count == 1


@pytest.mark.asyncio
async def test_base_repository_isolates_sessions_between_concurrent_tasks(monkeypatch):
    created_sessions = []

    def fake_session_maker():
        session = DummySession(f"s{len(created_sessions)}")
        created_sessions.append(session)
        return session

    monkeypatch.setattr(base_repository_module, "async_session_maker", fake_session_maker)

    repo = DummyRepo()
    start_event_1 = asyncio.Event()
    start_event_2 = asyncio.Event()
    release_event = asyncio.Event()

    task_1 = asyncio.create_task(repo.concurrent_use(start_event_1, release_event))
    task_2 = asyncio.create_task(repo.concurrent_use(start_event_2, release_event))

    await asyncio.gather(start_event_1.wait(), start_event_2.wait())
    release_event.set()
    session_1, session_2 = await asyncio.gather(task_1, task_2)

    assert session_1 is not session_2
    assert len(created_sessions) == 2
    assert all(session.close_count == 1 for session in created_sessions)
