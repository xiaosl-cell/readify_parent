import json
import os
from pathlib import Path
from typing import List, Dict, Any, Callable, Awaitable

from langchain_community.utilities import SerpAPIWrapper
from langchain_core.tools import tool, BaseTool

from app.config.agent_names import AgentNames
from app.core.config import settings
from app.repositories.project_file_repository import ProjectFileRepository
from app.services.agent_service import AgentService
from app.services.file_service import FileService


class AskAgentService(AgentService):
    """
    问答智能体服务，用于回答用户关于文档内容的问题
    """
    
    def __init__(
        self,
        project_id: int,
        vendor: str,
        context: Dict[str, Any] = None,
        temperature: float = 0.7,
        agent_name: str = AgentNames.QUESTIONER,
        description: str = "专注于回答用户问题，善于从文档中检索相关信息提供精准解答",
    ):
        """
        初始化问答Agent服务
        
        Args:
            project_id: 工程id
            vendor: 厂商
            temperature: 温度参数
            description: 智能体描述
            context: 其他信息
        """
        super().__init__(project_id, context, vendor, temperature, agent_name, description)
        
        # 初始化特定于问答Agent的仓库
        self.project_file_repo = ProjectFileRepository()
        
        # 设置问答Agent的提示模板
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """加载问答Agent的提示模板"""
        prompt_path = Path("prompt/ask_agent.prompt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()
            print(f"成功加载问答Agent提示模板: {prompt_path}")

    
    async def _load_tools(self) -> List[BaseTool]:
        """
        加载问答Agent所需的工具
        
        Returns:
            List[BaseTool]: 工具列表
        """
        
        # 获取父类的工具
        tools = await super()._load_tools()
        
        # 检查SerpAPI密钥是否存在
        serpapi_api_key = os.getenv('SERPAPI_API_KEY')
        if not serpapi_api_key:
            print("警告: 未设置SERPAPI_API_KEY环境变量，搜索工具将不可用")
        # 添加网络搜索工具
        search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)

        # 添加项目文件列表工具
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
                # 使用当前实例的项目ID
                project_id = self.project_id
                
                # 使用已初始化的项目文件仓库，不再传入db
                file_ids = await self.project_file_repo.get_file_ids_by_project_id(
                    project_id=project_id
                )
                
                if not file_ids:
                    return json.dumps({"files": [], "count": 0, "message": "该项目下没有关联的文件"})
                
                # 获取所有文件详情
                file_list = []
                for file_id in file_ids:
                    file = await self.file_repo.get_file_by_id(file_id=file_id)
                    if file:
                        # 将文件信息格式化为字典
                        file_info = {
                            "id": file.id,
                            "name": file.original_name,
                            "size": file.size,
                            "mime_type": file.mime_type,
                            "create_time": file.create_time
                        }
                        file_list.append(file_info)
                
                # 按ID排序
                file_list.sort(key=lambda x: x["id"])
                
                # 返回JSON格式的数据
                return json.dumps({
                    "files": file_list,
                    "count": len(file_list)
                }, default=str)
            except Exception as e:
                return json.dumps({"error": f"获取文件列表时发生错误: {str(e)}"})
        
        # 添加读取文件内容工具
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
                # 解析输入参数
                params = json.loads(input_str) if isinstance(input_str, str) else input_str
                
                # 获取参数
                file_id = params.get("file_id")
                
                # 验证参数
                if not file_id:
                    return json.dumps({"error": "缺少必要参数: file_id"}, ensure_ascii=False)
                
                # 尝试将参数转换为整数
                try:
                    file_id = int(file_id)
                except (ValueError, TypeError):
                    return json.dumps({"error": "参数类型错误，file_id必须为整数"}, ensure_ascii=False)
                
                # 使用父类已初始化的仓库
                # 检查文件是否存在
                file = await self.file_repo.get_file_by_id(file_id=file_id)
                if not file:
                    return json.dumps({"error": f"文件不存在 (ID: {file_id})"})
                
                # 检查文件大小
                if file.size > 1000000:
                    return json.dumps({"error": f"文件过大 (ID: {file_id})，请使用向量检索或分页阅读"})
                    
                # 获取文件所有文档块
                documents = await self.document_repo.get_by_file_id(file_id=file_id)
                
                if not documents:
                    return json.dumps({"error": f"文件存在但没有内容 (ID: {file_id})"})
                
                # documents已经按sequence排序，直接拼接内容
                content_parts = [doc.content for doc in documents if doc.content]
                
                # 将内容用换行符拼接
                full_content = "\n".join(content_parts)
                
                return full_content
            except json.JSONDecodeError:
                return json.dumps({"error": "无效的JSON格式参数"}, ensure_ascii=False)
            except Exception as e:
                return json.dumps({"error": f"读取文件内容时发生错误: {str(e)}"})

        # 导入asyncio以支持异步工具调用
        from langchain_core.tools import Tool

        # 修改工具列表，确保正确处理异步工具
        tools.extend([
            Tool.from_function(
                func=search.run,
                name="Search",
                description="搜索引擎接口，用于搜索互联网上的信息，当用户问题需要获取最新信息或项目文件中不包含的信息时使用"
            ),
            # 对于异步工具，正确使用AsyncTool或者保持原样（@tool装饰器会创建正确的AsyncTool）
            list_project_files,
            read_file_content,
        ]
        
        return self.tools

    # 根据需要重写特定的事件处理钩子
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
        
        # 发送工具输出
        await callback({
            'type': "thought",
            'content': tool_output,
            'project_id': project_id
        })
        
        # 收集工具输出
        self.all_thoughts.append(f"工具[{tool_name}]输出: {tool_output}\n")