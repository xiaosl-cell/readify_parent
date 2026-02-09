import asyncio
import json
import urllib.parse
from typing import Dict, Any
import logging

from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse

from app.core.user_context import UserContext, get_user_context
from app.repositories.conversation_repository import ConversationRepository
from app.services.coordinator_agent_service import CoordinatorAgentService
from app.config.agent_names import AgentNames
from app.services.ask_agent_service import AskAgentService
from app.services.note_agent_service import NoteAgentService

router = APIRouter()
logger = logging.getLogger(__name__)

# 创建依赖项函数，用于获取协调Agent服务
async def get_coordinator_service(
    project_id: int = Query(..., description="工程ID"),
    task_type:str = Query(..., description="任务类型"),
    context: str = Query("{}", description="其他信息"),
    user_ctx: UserContext = Depends(get_user_context),
) -> CoordinatorAgentService:
    """
    获取协调Agent服务实例

    Args:
        project_id: 项目ID
        task_type: 任务类型 ask/note
        context: 其他补充信息，uri编码的json字符串

    Returns:
        CoordinatorAgentService: 协调Agent服务实例
    """
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
        "Create coordinator context: project_id=%s, task_type=%s, user_id=%s, user_role=%s",
        project_id,
        task_type,
        context_dict.get("user_id"),
        context_dict.get("user_role"),
    )

    coordinator = CoordinatorAgentService(project_id=project_id, task_type=task_type, context=context_dict)

    # 注册专业智能体
    ask_agent = AskAgentService(project_id=project_id, context=context_dict)
    coordinator.register_agent(ask_agent.agent_name, ask_agent)

    note_agent = NoteAgentService(project_id=project_id, context=context_dict)
    coordinator.register_agent(note_agent.agent_name, note_agent)
    
    # 初始化服务
    await coordinator.initialize()
    return coordinator


@router.get("/stream")
async def stream_response(
    query: str = Query(..., description="用户查询"),
    project_id: int = Query(..., description="工程ID"),
    context: str = Query("{}", description="其他信息"),
    coordinator_service: CoordinatorAgentService = Depends(get_coordinator_service)
):
    """
    流式输出接口，实时显示智能体的思考过程
    """
    async def event_generator():
        # 先进行历史消息修剪，确保上下文不会过大
        try:
            conversation_repo = ConversationRepository()
            trimmed_count = await conversation_repo.trim_context_messages(project_id)
            if trimmed_count > 0:
                yield f"data: {json.dumps({'type': 'system', 'project_id': project_id, 'content': f'已修剪 {trimmed_count} 条历史消息'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'system', 'project_id': project_id, 'content': f'修剪历史消息时出错: {str(e)}'})}\n\n"
        
        # 直接发送智能体事件，不提前保存用户消息
        event_queue = asyncio.Queue()
        
        async def callback(data):
            await event_queue.put(data)
        
        # 启动智能体任务，不传递db对象
        agent_task = asyncio.create_task(
            coordinator_service.generate_stream_response(
                query=query, 
                callback=callback,
            )
        )
        
        # 持续从队列获取事件并发送
        while True:
            try:
                # 等待队列中的新事件，但添加超时以检查agent_task是否已完成
                try:
                    data = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    # 发送事件数据
                    yield f"data: {json.dumps(data)}\n\n"
                    event_queue.task_done()
                except asyncio.TimeoutError:
                    # 检查agent_task是否已完成
                    if agent_task.done():
                        # 如果队列为空且任务已完成，则退出循环
                        if event_queue.empty():
                            break
            except Exception as e:
                # 发送错误信息
                yield f"data: {json.dumps({'type': 'system', 'project_id': project_id, 'content': f'流式输出错误: {str(e)}'})}\n\n"
                break
        
        # 发送完成信号
        yield f"data: {json.dumps({'type': '[DONE]', 'project_id': project_id})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
