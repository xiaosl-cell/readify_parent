from pathlib import Path
from typing import Dict, Callable, List, Any
import json

from langchain_core.tools import BaseTool, tool

from app.repositories.mind_map_node_repository import MindMapNodeRepository
from app.repositories.mind_map_repository import MindMapRepository
from app.repositories.document_repository import DocumentRepository
from app.models.mind_map_node import MindMapNodeCreate
from app.models.document import DocumentResponse
from app.services.agent_service import AgentService
from app.config.agent_names import AgentNames

class NoteAgentService(AgentService):
    """
    笔记智能体服务，用于处理用户笔记和文档摘要
    具有创建笔记、更新笔记、生成摘要等功能
    """
    
    def __init__(
        self,
        project_id: int,
        vendor: str,
        context:  Dict[str, Any] = None,
        temperature: float = 0.7,
        agent_name: str = AgentNames.NOTE_AGENT,  # 可以在AgentNames类中添加对应的常量
        description: str = "专注于处理文档笔记和内容摘要，提供智能笔记管理和关键信息提取服务"
    ):
        """
        初始化笔记Agent服务
        
        Args:
            project_id: 项目ID
            vendor: 厂商名称
            temperature: 温度参数
            agent_name: 智能体名称
            description: 智能体描述
        """
        super().__init__(project_id, context, vendor, temperature, agent_name, description)
        self.mind_map_repo = MindMapRepository()
        self.mind_map_node_repo = MindMapNodeRepository()
        self.document_repo = DocumentRepository()
        
        # 设置笔记Agent的提示模板
        self._load_prompt_template()
        
    def _load_prompt_template(self):
        """加载笔记Agent的提示模板"""
        prompt_path = Path("prompt/note_agent.prompt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()
            print(f"成功加载笔记Agent提示模板: {prompt_path}")

    async def _load_tools(self) -> List[BaseTool]:
        """
        加载笔记Agent的工具列表

        Returns:
            List[BaseTool]: 工具列表
        """
        tools = await super()._load_tools()
        
        @tool
        async def query_mind_map_tree(input_str: str) -> str:
            """
            查询思维导图的完整树形结构，返回以JSON格式表示的思维导图树。
            
            参数:
                input_str: 输入参数JSON字符串，格式为 {"mind_map_id": 思维导图ID}
                
            返回:
                思维导图的JSON树形结构
            """
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            mind_map_id = params.get("mind_map_id")

            # 获取思维导图信息
            mind_map = await self.mind_map_repo.get_by_id(mind_map_id)
            if not mind_map:
                return f"找不到ID为{mind_map_id}的思维导图"
                
            # 获取思维导图树形结构
            tree = await self.mind_map_node_repo.get_mind_map_tree(mind_map_id)
            
            # 将树结构转换为字典，然后序列化为JSON字符串
            tree_dict = tree.model_dump()
            return json.dumps(tree_dict, ensure_ascii=False, indent=2)
            
        @tool
        async def batch_add_child_nodes(input_str: str) -> str:
            """
            向指定节点批量添加子节点
            
            参数:
                input_str: 输入参数JSON字符串，格式为 {"parent_node_id": 父节点ID, "contents": [子节点内容列表，每个元素将创建为一个子节点]}

            返回:
                创建结果说明，包含成功创建的节点ID列表
            """
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            parent_node_id = params.get("parent_node_id")
            contents = params.get("contents")
            # 获取父节点信息
            parent_node = await self.mind_map_node_repo.get_by_id(parent_node_id)
            if not parent_node:
                return f"找不到ID为{parent_node_id}的父节点"
                
            # 获取思维导图信息
            mind_map = await self.mind_map_repo.get_by_id(parent_node.mind_map_id)
            if not mind_map:
                return f"找不到ID为{parent_node.mind_map_id}的思维导图"
                
            # 批量创建子节点
            created_nodes = []
            for content in contents:
                # 创建节点数据
                node_create = MindMapNodeCreate(
                    project_id=parent_node.project_id,
                    mind_map_id=parent_node.mind_map_id,
                    file_id=parent_node.file_id,
                    parent_id=parent_node_id,
                    content=content
                )
                
                # 创建节点
                try:
                    new_node = await self.mind_map_node_repo.create_node(node_create)
                    created_nodes.append({
                        "id": new_node.id,
                        "content": new_node.content
                    })
                except Exception as e:
                    return f"创建子节点失败: {str(e)}"
            
            # 返回创建结果
            result = {
                "success": True,
                "parent_node_id": parent_node_id,
                "created_nodes": created_nodes,
                "total_created": len(created_nodes)
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        @tool
        async def query_file_documents(input_str: str) -> str:
            """
            查询指定文件ID的所有文档概览信息，包含文档ID和标签信息。
            
            参数:
                input_str: 输入参数JSON字符串，格式为 {"file_id": 文件ID}
                
            返回:
                该文件的所有文档ID和标签列表，JSON格式
            """
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            file_id = params.get("file_id")
            # 获取文件的所有文档
            documents = await self.document_repo.get_by_file_id(file_id)
            
            if not documents:
                return f"找不到文件ID为{file_id}的文档记录"
                
            # 提取文档概览信息（ID和标签）
            document_overviews = []
            for doc in documents:
                document_overviews.append({
                    "id": doc.id,
                    "label": doc.label if doc.label else "未标记",
                    "sequence": doc.sequence
                })
                
            # 按sequence排序
            document_overviews.sort(key=lambda x: x["sequence"])
                
            # 返回文档概览信息
            result = {
                "file_id": file_id,
                "total_documents": len(document_overviews),
                "documents": document_overviews
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        @tool
        async def get_document_by_id(input_str: str) -> str:
            """
            根据文档ID查询完整的文档信息，包括内容、元数据等。
            
            参数:
                input_str: 输入参数JSON字符串，格式为 {"document_id": 文档ID}
                
            返回:
                完整的文档信息，JSON格式
            """
            params = json.loads(input_str) if isinstance(input_str, str) else input_str
            document_id = params.get("document_id")
            
            # 获取文档信息
            document = await self.document_repo.get_by_id(document_id)
            if not document:
                return f"找不到ID为{document_id}的文档"
                
            # 将文档对象转换为字典，然后序列化为JSON字符串
            document_dict = {
                "id": document.id,
                "file_id": document.file_id,
                "content": document.content,
                "sequence": document.sequence,
                "created_at": document.created_at.isoformat() if document.created_at else None,
                "updated_at": document.updated_at.isoformat() if document.updated_at else None
            }
            
            return json.dumps(document_dict, ensure_ascii=False, indent=2)

        tools.extend([
            query_mind_map_tree,
            batch_add_child_nodes,
            query_file_documents,
            get_document_by_id
        ])
        self.tools = tools
        return tools

    async def _before_generation(self, query: str, callback: Callable) -> Dict[str, Any]:
        """
        响应生成前的准备工作，子类可以重写以添加自定义逻辑

        Args:
            query: 用户查询
            callback: 回调函数

        Returns:
            Dict[str, Any]: 传递给LLM的上下文数据
        """
        # 重置思考过程
        context = await super()._before_generation(query, callback)
        mind_map = await self.mind_map_repo.get_by_id(self.context.get('mind_map_id'))
        context["mind_map_id"] = mind_map.id
        context["mind_map_title"] = mind_map.title
        context['mind_map_description'] = mind_map.description
        context['file_id'] = mind_map.file_id
        return context

    async def validation(self):
        await super().validation()
        if  not self.context.get('mind_map_id'):
            raise Exception("思维导图ID不能为空")


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

