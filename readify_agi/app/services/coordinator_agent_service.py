import json
import logging

from typing import Dict, Any, Callable, List, Optional, Literal, Tuple

from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from app.config.agent_names import AgentNames
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class DelegateTaskInput(BaseModel):
    """delegate_task 的结构化参数定义。"""

    agent_name: Optional[str] = Field(
        default=None,
        description="要委派的专业智能体名称，例如 QUESTIONER 或 NOTE_AGENT。优先使用 list_available_agents 返回的名称。",
    )
    task_type: Optional[Literal["ask", "note"]] = Field(
        default=None,
        description="任务类型。可选值为 ask 或 note，可作为 agent_name 的辅助或回退选择。",
    )
    task: str = Field(
        ...,
        min_length=1,
        description="要执行的具体任务描述，必须包含完整上下文，不要传 JSON 字符串。",
    )


class CoordinatorAgentService(AgentService):
    """
    协调Agent服务，用于管理和协调多个专业Agent进行协作
    """

    def __init__(
        self,
        project_id: int,
        context: Dict[str, Any] = None,
        task_type: str = "ask",
        temperature: float = 0.7,
        agent_name: str = AgentNames.COORDINATOR,
        description: str = "负责分析用户需求并协调调度其他专业智能体，合理安排工作流程"
    ):
        """
        初始化协调Agent服务

        Args:
            project_id: 项目ID
            temperature: 温度参数
            agent_name: 智能体名称
            description: 智能体描述
        """
        super().__init__(project_id, context, temperature, agent_name, description)
        self.task_type = task_type
        self.specialized_agents: Dict[str, AgentService] = {}
        self.last_task_status: Dict[str, Any] = {
            "completed": False,
            "current_agent": None,
            "task_history": [],
            "final_output": None
        }

    async def _load_prompt_template_async(self):
        """从 eval API 加载协调器专用的提示模板"""
        self.prompt_template = await self._load_prompt_from_client("coordinator")
        logger.info("成功加载协调器提示模板")

    async def _load_system_prompt_async(self) -> Optional[str]:
        """从 eval API 加载协调器的系统提示词（tool_calling 模式使用）"""
        prompt = await self._load_system_prompt_from_client("coordinator")
        if prompt:
            logger.info("成功加载协调器系统提示词")
        return prompt

    def register_agent(self, agent_name: str, agent_service: AgentService) -> None:
        """
        注册一个专业Agent

        Args:
            agent_name: Agent名称
            agent_service: Agent服务实例
        """
        if not isinstance(agent_name, str):
            agent_name = str(agent_name)

        self.specialized_agents[agent_name] = agent_service
        logger.info("已注册专业智能体: %s", agent_name)

    def unregister_agent(self, agent_name: str) -> bool:
        """
        注销一个专业Agent

        Args:
            agent_name: Agent名称

        Returns:
            bool: 是否成功注销
        """
        if agent_name in self.specialized_agents:
            del self.specialized_agents[agent_name]
            logger.info("已注销专业智能体: %s", agent_name)
            return True

        for key in list(self.specialized_agents.keys()):
            if isinstance(key, tuple) and str(key) == agent_name:
                del self.specialized_agents[key]
                logger.info("已注销专业智能体: %s", agent_name)
                return True

        return False

    def _resolve_agent_name(self, agent_name: Optional[str], task_type: Optional[str]) -> Tuple[Optional[str], Optional[AgentService]]:
        """根据 agent_name 或 task_type 解析目标智能体。"""
        if agent_name:
            for key, value in self.specialized_agents.items():
                key_str = str(key) if isinstance(key, tuple) else key
                if key_str == agent_name or key == agent_name:
                    return key_str, value

        task_type_to_agent = {
            "ask": AgentNames.QUESTIONER,
            "note": AgentNames.NOTE_AGENT,
        }
        resolved_name = task_type_to_agent.get(task_type or "")
        if resolved_name:
            agent = self.specialized_agents.get(resolved_name)
            if agent:
                return resolved_name, agent

        return None, None

    async def _load_tools(self) -> List[BaseTool]:
        """
        加载协调Agent专用工具

        Returns:
            List[BaseTool]: 工具列表
        """
        tools = []

        @tool
        async def list_available_agents() -> str:
            """
            查询所有可用的专业智能体，在执行delegate_task前需要调用该API查询

            Returns:
                str: 所有可用智能体列表及其描述
            """
            if not self.specialized_agents:
                return "当前没有可用的专业智能体"

            agent_info = []
            for key, agent in self.specialized_agents.items():
                name = str(key) if isinstance(key, tuple) else key
                description = getattr(agent, "description", "无描述")
                agent_info.append(f"名称: {name}\n描述: {description}")

            return "可用的专业智能体:\n" + "\n\n".join(agent_info)

        @tool(args_schema=DelegateTaskInput)
        async def delegate_task(
            task: str,
            agent_name: Optional[str] = None,
            task_type: Optional[Literal["ask", "note"]] = None,
        ) -> str:
            """
            将任务委派给专业智能体。使用真正的结构化字段传参，不要再传 JSON 字符串。

            Returns:
                str: 专业智能体的响应结果
            """
            try:
                resolved_agent_name, agent = self._resolve_agent_name(agent_name=agent_name, task_type=task_type)

                if not resolved_agent_name:
                    if agent_name:
                        return f"错误: 未找到名为 '{agent_name}' 的智能体"
                    return "错误: 未指定可解析的智能体，请提供 agent_name 或可用的 task_type"
                if not agent:
                    return f"错误: 智能体 '{resolved_agent_name}' 当前不可用"

                self.last_task_status["current_agent"] = resolved_agent_name
                self.last_task_status["task_history"].append({
                    "agent": resolved_agent_name,
                    "task_type": task_type,
                    "task": task,
                    "completed": False
                })

                main_callback = self._current_callback

                if main_callback:
                    await main_callback({
                        'type': 'delegation_start',
                        'content': f'正在将任务委派给 {resolved_agent_name}...',
                        'delegate_to': resolved_agent_name,
                        'task_type': task_type,
                        'task': task[:200],
                        'project_id': self.project_id
                    })
                    self.all_thoughts.append(f"\n--- 委派任务给 {resolved_agent_name}: {task} ---\n")

                result = {"output": "子智能体未返回有效结果"}

                if hasattr(agent, 'generate_stream_response'):
                    collected_output = []
                    sub_agent_thoughts = []

                    async def forward_callback(data):
                        """转发子Agent事件到主SSE流，同时收集结果"""
                        content_type = data.get('type', '')
                        content = data.get('content', '')

                        if content_type == "thought":
                            sub_agent_thoughts.append(content)

                        if content_type == 'final_answer' and content:
                            collected_output.append(content)
                            return

                        if main_callback and content_type not in ('final_answer', '[DONE]', 'system', 'thought'):
                            await main_callback(data)

                    await agent.generate_stream_response(
                        query=task,
                        callback=forward_callback,
                        should_save_thinking=False
                    )

                    if sub_agent_thoughts and hasattr(self, 'all_thoughts'):
                        sub_agent_thought_content = "".join(sub_agent_thoughts)
                        self.all_thoughts.append(f"\n{sub_agent_thought_content}\n")

                    result_output = "\n".join(collected_output) if collected_output else "子智能体未返回有效结果"
                    result = {"output": result_output}

                if main_callback:
                    summary = result.get("output", "")[:200]
                    await main_callback({
                        'type': 'delegation_end',
                        'content': f'{resolved_agent_name} 已完成任务',
                        'delegate_to': resolved_agent_name,
                        'task_type': task_type,
                        'summary': summary,
                        'project_id': self.project_id
                    })
                    self.all_thoughts.append(f"\n--- {resolved_agent_name} 完成任务 ---\n")

                task_index = len(self.last_task_status["task_history"]) - 1
                self.last_task_status["task_history"][task_index]["completed"] = True
                self.last_task_status["task_history"][task_index]["result"] = result.get("output", "未返回结果")
                return json.dumps({
                    "agent": resolved_agent_name,
                    "task_type": task_type,
                    "task": task,
                    "result": result.get("output", "未返回结果")
                }, ensure_ascii=False)

            except KeyError as e:
                return f"委派任务时缺少必要参数: {str(e)}"
            except Exception as e:
                logger.exception("委派任务时发生未预期的错误")
                return f"委派任务时发生错误: {str(e)}"

        @tool
        async def get_task_status(query: str) -> str:
            """
            获取最后一次任务的执行状态

            Args:
                query: 查询参数，可以为空

            Returns:
                str: 任务状态信息
            """
            return json.dumps(self.last_task_status, ensure_ascii=False)

        tools.extend([
            list_available_agents,
            delegate_task,
            get_task_status
        ])
        self.tools = tools
        return tools

    async def initialize(self) -> None:
        """初始化协调Agent和所有注册的专业Agent"""
        await super().initialize()

        try:
            for agent_name, agent in self.specialized_agents.items():
                try:
                    await agent.initialize()
                    logger.info("已初始化专业智能体: %s", agent_name)
                except Exception:
                    logger.exception("初始化专业智能体 %s 失败", agent_name)
        except Exception:
            logger.exception("初始化专业智能体时发生错误")

    async def _before_generation(self, query: str, callback: Callable) -> Dict[str, Any]:
        """
        响应生成前的准备工作，添加可用智能体信息

        Args:
            query: 用户查询
            callback: 回调函数

        Returns:
            Dict[str, Any]: 传递给LLM的上下文数据
        """
        context = await super()._before_generation(query, callback)
        context["task_type"] = self.task_type
        context["available_tools"] = self._render_tools_for_prompt()

        available_agents = "无"
        if self.specialized_agents:
            agent_keys = []
            for key in self.specialized_agents.keys():
                if isinstance(key, tuple):
                    agent_keys.append(str(key))
                else:
                    agent_keys.append(key)

            available_agents = ", ".join(agent_keys)

        context["available_agents"] = available_agents

        return context

    async def _handle_tool_end(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        处理工具执行结束事件

        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        tool_name = event.get("name", "")
        ignore_tools = ["get_task_status", "execute_multi_agent_workflow", "delegate_task"]
        if tool_name in ignore_tools:
            return

        await super()._handle_tool_end(event, callback, project_id)

    async def aclose(self) -> None:
        """关闭协调器及其已注册子智能体持有的会话。"""
        await super().aclose()
        for agent in self.specialized_agents.values():
            close_method = getattr(agent, "aclose", None)
            if close_method is not None:
                await close_method()
