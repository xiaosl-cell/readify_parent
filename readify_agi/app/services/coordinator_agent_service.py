import json
import logging
from pathlib import Path
from typing import Dict, Any, Callable, List

from langchain_core.tools import BaseTool, tool

from app.config.agent_names import AgentNames
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


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
        self._load_prompt_template()
        self.last_task_status: Dict[str, Any] = {
            "completed": False,
            "current_agent": None,
            "task_history": [],
            "final_output": None
        }

    def _load_prompt_template(self):
        """加载协调器专用的提示模板"""
        coordinator_prompt_path = Path("prompt/coordinator.prompt")
        try:
            with open(coordinator_prompt_path, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
                logger.info("成功加载协调器提示模板: %s", coordinator_prompt_path)
        except FileNotFoundError:
            logger.warning("未找到协调器提示模板: %s", coordinator_prompt_path)

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

    async def _load_tools(self) -> List[BaseTool]:
        """
        加载协调Agent专用工具

        Returns:
            List[BaseTool]: 工具列表
        """
        tools = await super()._load_tools()

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

        @tool
        async def delegate_task(input_str: str) -> str:
            """
            将任务委派给专业智能体，输出参数为纯json字符串，不需要被markdown格式包裹

            args：
            {
                "agent_name": "要使用的智能体名称",
                "task_type": 任务类型 ask/note
                "task": "要执行的具体任务描述",
            }


            Returns:
                str: 专业智能体的响应结果
            """
            try:
                params = json.loads(input_str) if isinstance(input_str, str) else input_str

                agent_name = params.get("agent_name")
                task = params.get("task")

                if not agent_name:
                    return "错误: 未指定智能体名称"
                if not task:
                    return "错误: 未提供任务描述"

                agent = None
                for key, value in self.specialized_agents.items():
                    key_str = str(key) if isinstance(key, tuple) else key
                    if key_str == agent_name or key == agent_name:
                        agent = value
                        break

                if not agent:
                    return f"错误: 未找到名为 '{agent_name}' 的智能体"

                self.last_task_status["current_agent"] = agent_name
                self.last_task_status["task_history"].append({
                    "agent": agent_name,
                    "task": task,
                    "completed": False
                })

                async def sub_agent_callback(data):
                    if hasattr(self, '_current_callback') and self._current_callback:
                        await self._current_callback(data)

                if hasattr(agent, 'generate_stream_response'):
                    collected_output = []
                    sub_agent_thoughts = []

                    async def collect_output_callback(data):
                        content_type = data.get('type', '')
                        content = data.get('content', '')

                        if content_type == "thought":
                            await sub_agent_callback(data)
                            sub_agent_thoughts.append(content)

                        if content_type == 'final_answer' and content:
                            collected_output.append(content)

                    await agent.generate_stream_response(
                        query=task,
                        callback=collect_output_callback,
                        should_save_thinking=False
                    )

                    if sub_agent_thoughts and hasattr(self, 'all_thoughts'):
                        sub_agent_thought_content = "".join(sub_agent_thoughts)
                        self.all_thoughts.append(f"\n{sub_agent_thought_content}\n")

                    result_output = "\n".join(collected_output) if collected_output else "子智能体未返回有效结果"
                    result = {"output": result_output}

                task_index = len(self.last_task_status["task_history"]) - 1
                self.last_task_status["task_history"][task_index]["completed"] = True
                self.last_task_status["task_history"][task_index]["result"] = result.get("output", "未返回结果")
                return json.dumps({
                    "agent": agent_name,
                    "task": task,
                    "result": result.get("output", "未返回结果")
                }, ensure_ascii=False)

            except json.JSONDecodeError:
                return "错误: 无效的JSON格式参数"
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
                except Exception as e:
                    logger.exception("初始化专业智能体 %s 失败", agent_name)
        except Exception as e:
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
        if tool_name == "delegate_task":
            content = "\n委派任务已处理完成....\n"
            await callback({
                'type': 'thought',
                'content': content,
                'project_id': self.project_id
            })
            self.all_thoughts.append(content)
        if tool_name in ignore_tools:
            return

        await super()._handle_tool_end(event, callback, project_id)
