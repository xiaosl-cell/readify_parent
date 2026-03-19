import asyncio
import json
import logging
import urllib.parse
from contextlib import suppress
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.core.user_context import UserContext, get_user_context
from app.repositories.conversation_repository import ConversationRepository
from app.services.ask_agent_service import AskAgentService
from app.services.coordinator_agent_service import CoordinatorAgentService
from app.services.note_agent_service import NoteAgentService

router = APIRouter()
logger = logging.getLogger(__name__)


async def get_coordinator_service(
    project_id: int = Query(..., description="工程ID"),
    task_type: str = Query(..., description="任务类型"),
    context: str = Query("{}", description="其他信息"),
    user_ctx: UserContext = Depends(get_user_context),
) -> CoordinatorAgentService:
    """Build the coordinator agent with the allowed specialized agents."""
    try:
        decoded_context = urllib.parse.unquote(context)
        context_dict = json.loads(decoded_context) if decoded_context else {}
        if not isinstance(context_dict, dict):
            context_dict = {}
    except Exception:
        logger.warning("Invalid context payload, fallback to empty context: %s", context)
        context_dict = {}

    if user_ctx.user_id is not None:
        context_dict["user_id"] = user_ctx.user_id
    if user_ctx.user_role:
        context_dict["user_role"] = user_ctx.user_role

    logger.info(
        "Create coordinator context: project_id=%s, task_type=%s, user_id=%s, user_role=%s, mind_map_id=%s",
        project_id,
        task_type,
        context_dict.get("user_id"),
        context_dict.get("user_role"),
        context_dict.get("mind_map_id"),
    )

    coordinator = CoordinatorAgentService(project_id=project_id, task_type=task_type, context=context_dict)

    ask_agent = AskAgentService(project_id=project_id, context=context_dict)
    coordinator.register_agent(ask_agent.agent_name, ask_agent)

    if context_dict.get("mind_map_id"):
        note_agent = NoteAgentService(project_id=project_id, context=context_dict)
        coordinator.register_agent(note_agent.agent_name, note_agent)
    else:
        logger.info("Skip NOTE_AGENT registration because mind_map_id is missing")

    await coordinator.initialize()
    return coordinator


@router.get("/stream")
async def stream_response(
    query: str = Query(..., description="用户查询"),
    project_id: int = Query(..., description="工程ID"),
    context: str = Query("{}", description="其他信息"),
    coordinator_service: CoordinatorAgentService = Depends(get_coordinator_service),
):
    """Stream agent events to the frontend."""

    async def event_generator():
        agent_task = None
        conversation_repo = ConversationRepository()
        try:
            try:
                trimmed_count = await conversation_repo.trim_context_messages(project_id)
                if trimmed_count > 0:
                    yield f"data: {json.dumps({'type': 'system', 'project_id': project_id, 'content': f'已修剪 {trimmed_count} 条历史消息'})}\n\n"
            except Exception as exc:
                yield f"data: {json.dumps({'type': 'system', 'project_id': project_id, 'content': f'修剪历史消息时出错: {str(exc)}'})}\n\n"
            finally:
                await conversation_repo.close()

            event_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

            async def callback(data: Dict[str, Any]):
                await event_queue.put(data)

            agent_task = asyncio.create_task(
                coordinator_service.generate_stream_response(
                    query=query,
                    callback=callback,
                )
            )

            while True:
                try:
                    data = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield f"data: {json.dumps(data)}\n\n"
                    event_queue.task_done()
                except asyncio.TimeoutError:
                    if agent_task.done() and event_queue.empty():
                        break
                except Exception as exc:
                    yield f"data: {json.dumps({'type': 'system', 'project_id': project_id, 'content': f'流式输出错误: {str(exc)}'})}\n\n"
                    break

            yield f"data: {json.dumps({'type': '[DONE]', 'project_id': project_id})}\n\n"
        finally:
            if agent_task is not None and not agent_task.done():
                agent_task.cancel()
                with suppress(asyncio.CancelledError):
                    await agent_task
            await coordinator_service.aclose()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
