import json
import logging

from typing import List, Dict, Any, Callable

from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import tool, BaseTool, Tool

from app.config.agent_names import AgentNames
from app.core.config import settings
from app.repositories.project_file_repository import ProjectFileRepository
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class AskAgentService(AgentService):
    """
    问答智能体服务，用于回答用户关于文档内容的问题
    """

    def __init__(
        self,
        project_id: int,
        context: Dict[str, Any] = None,
        temperature: float = 0.7,
        agent_name: str = AgentNames.QUESTIONER,
        description: str = "专注于回答用户问题，善于从文档中检索相关信息提供精准解答",
    ):
        """
        初始化问答Agent服务

        Args:
            project_id: 工程id
            temperature: 温度参数
            description: 智能体描述
            context: 其他信息
        """
        super().__init__(project_id, context, temperature, agent_name, description)

        self.project_file_repo = ProjectFileRepository()

    async def _load_prompt_template_async(self):
        """从 eval API 加载问答Agent的提示模板"""
        self.prompt_template = await self._load_prompt_from_client("ask_agent")
        logger.info("成功加载问答Agent提示模板")

    async def _load_tools(self) -> List[BaseTool]:
        """
        加载问答Agent所需的工具

        Returns:
            List[BaseTool]: 工具列表
        """
        tools = await super()._load_tools()

        serpapi_api_key = settings.SERPAPI_API_KEY
        search_tool = None
        if serpapi_api_key:
            search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)
            search_tool = search
        else:
            logger.warning("未设置 SERPAPI_API_KEY，搜索工具将不可用（Nacos 配置或环境变量缺失）")

        @tool
        async def list_project_files(input_str: str = "{}") -> str:
            """
            获取项目相关的所有文件信息

            Args:
                input_str: 可选的JSON参数字符串

            Returns:
                str: JSON格式的文件列表信息
            """
            try:
                project_id = self.project_id

                file_ids = await self.project_file_repo.get_file_ids_by_project_id(
                    project_id=project_id
                )

                if not file_ids:
                    return json.dumps({"files": [], "count": 0, "message": "该项目下没有关联的文件"})

                file_list = []
                for file_id in file_ids:
                    file = await self.file_repo.get_file_by_id(file_id=file_id)
                    if file:
                        file_info = {
                            "id": file.id,
                            "name": file.original_name,
                            "size": file.size,
                            "mime_type": file.mime_type,
                            "create_time": file.create_time
                        }
                        file_list.append(file_info)

                file_list.sort(key=lambda x: x["id"])

                return json.dumps({
                    "files": file_list,
                    "count": len(file_list)
                }, default=str)
            except Exception as e:
                return json.dumps({"error": f"获取文件列表时发生错误: {str(e)}"})

        @tool
        async def read_file_content(input_str: str) -> str:
            """
            读取指定文件的全文内容，仅当文件小于1M时可用

            Args:
                input_str: 输入参数JSON字符串，格式为 {"file_id": 文件ID}

            Returns:
                str: 文件的完整内容
            """
            try:
                params = json.loads(input_str) if isinstance(input_str, str) else input_str

                file_id = params.get("file_id")

                if not file_id:
                    return json.dumps({"error": "缺少必要参数: file_id"}, ensure_ascii=False)

                try:
                    file_id = int(file_id)
                except (ValueError, TypeError):
                    return json.dumps({"error": "参数类型错误，file_id必须为整数"}, ensure_ascii=False)

                file = await self.file_repo.get_file_by_id(file_id=file_id)
                if not file:
                    return json.dumps({"error": f"文件不存在 (ID: {file_id})"})

                if file.size > 1000000:
                    return json.dumps({"error": f"文件过大 (ID: {file_id})，请使用向量检索或分页阅读"})

                documents = await self.document_repo.get_by_file_id(file_id=file_id)

                if not documents:
                    return json.dumps({"error": f"文件存在但没有内容 (ID: {file_id})"})

                content_parts = [doc.content for doc in documents if doc.content]

                full_content = "\n".join(content_parts)

                return full_content
            except json.JSONDecodeError:
                return json.dumps({"error": "无效的JSON格式参数"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": f"读取文件内容时发生错误: {str(e)}"})

        if search_tool:
            tools.append(
                Tool.from_function(
                    func=search_tool.run,
                    name="Search",
                    description="搜索引擎接口，用于搜索互联网上的信息，当用户问题需要获取最新信息或项目文件中不包含的信息时使用"
                )
            )

        tools.extend([
            list_project_files,
            read_file_content,
        ])

        return self.tools

    async def _handle_tool_end(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        重写工具结束事件处理方法，使其适应问答Agent特有的行为

        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        tool_name = event["name"]
        tool_output = event["data"]["output"]

        await callback({
            'type': "thought",
            'content': tool_output,
            'project_id': project_id
        })

        self.all_thoughts.append(f"工具[{tool_name}]输出: {tool_output}\n")
