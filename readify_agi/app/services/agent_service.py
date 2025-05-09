import json
from typing import Dict, Any, List, Optional, Union, Callable, Awaitable

import dotenv
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_core.agents import AgentFinish
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.repositories.assistant_thinking_repository import AssistantThinkingRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.file_repository import FileRepository
from app.repositories.project_repository import ProjectRepository


def get_llm_config(vendor: str):
    if vendor == "OpenAI":
        return {
            "model_name": "gpt-4o",
            "api_key": settings.OPENAI_API_KEY,
            "base_url": settings.OPENAI_API_BASE
        }
    elif vendor == "DeepSeek":
        return {
            "model_name": "deepseek-reasoner",
            "api_key": settings.DEEPSEEK_API_KEY,
            "base_url": settings.DEEPSEEK_API_BASE
        }
    elif vendor == "Qwen":
        return {
            "model_name": "qwq-plus-latest",
            "api_key": settings.QWEN_API_KEY,
            "base_url": settings.QWEN_API_BASE
        }
    elif vendor == "OpenAI-China":
        return {
            "model_name": "gpt-4o",
            "api_key": settings.OPENAI_API_KEY_CHINA,
            "base_url": settings.OPENAI_API_BASE_CHINA
        }
    else:
        raise ValueError(f"不支持的厂商: {vendor}")


class AgentService:
    """
    Agent服务基类，作为所有具体Agent实现的父类
    提供流式响应、事件处理和通用逻辑
    """
    
    def __init__(
        self,
        project_id: int,
        context: Dict[str, Any] = None,
        vendor: str = "OpenAI",
        temperature: float = 0.7,
        agent_name: str = "Agent",
        description: str = "基础智能体服务，提供智能对话和工具调用能力",
    ):
        """
        初始化Agent服务
        
        Args:
            project_id: 项目ID
            vendor: 厂商名称
            temperature: 温度参数
            agent_name: 智能体名称
            description: 智能体描述
            context: 上下文信息，包含项目ID、思维导图ID等数据的JSON对象
        """
        self.project_id = project_id
        self.vendor = vendor
        self.temperature = temperature
        self.agent_name = agent_name
        self.description = description
        self.context = context or {}
        self.llm = None
        self.agent_executor = None
        self.tools = []
        self.prompt_template = None
        self.last_kind = None
        
        # 是否保存思考过程到数据库
        self.should_save_thinking = True
        
        # 加载环境变量
        dotenv.load_dotenv()
        
        # 初始化仓库，如果提供了db则传入，否则让仓库自己管理
        self.conversation_repo = ConversationRepository()
        self.thinking_repo = AssistantThinkingRepository()
        self.document_repo = DocumentRepository()
        self.file_repo = FileRepository()
        self.project_repo = ProjectRepository()
        
        # 用于保存当前回调函数
        self._current_callback = None
        
        # 用于保存思考过程
        self.all_thoughts = []

    async def validation(self):
        if not self.project_id:
            raise ValueError("工程ID不能为空")
    
    async def initialize(self) -> None:
        """
        初始化Agent，加载必要的组件
        """
        # 初始化LLM
        self.llm = self._create_llm()
        
        # 加载工具
        self.tools = await self._load_tools()
        
        # 创建Agent执行器
        if self.prompt_template:
            self.agent_executor = self._create_agent_executor()
    
    def _create_llm(self) -> ChatOpenAI:
        """
        创建语言模型实例
        
        Returns:
            ChatOpenAI: 语言模型实例
        """
        config = get_llm_config(self.vendor)
        return ChatOpenAI(
            base_url=config["base_url"],
            api_key=config["api_key"],
            model=config["model_name"],
            temperature=self.temperature
        )
    
    async def _load_tools(self) -> List[BaseTool]:
        """
        加载Agent所需的工具
        
        Returns:
            List[BaseTool]: 工具列表
        """
        # 默认工具集为空，子类需要重写此方法以添加特定工具
        return []
    
    def _create_agent_executor(self) -> Runnable[dict[str, Any], dict[str, Any]]:
        """
        创建Agent执行器
        
        Returns:
            AgentExecutor: Agent执行器
        """
        if not self.prompt_template:
            raise ValueError("未设置提示模板")
            
        prompt = PromptTemplate.from_template(self.prompt_template)
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 定义中间步骤裁剪函数 - 最多保留最后5个步骤
        def trim_steps(steps):
            """只保留最近的5个步骤，防止上下文过大"""
            if len(steps) > 5:
                return steps[-5:]
            return steps

        # 使用与demo相同的构造方式：先创建AgentExecutor实例，然后链式调用with_config
        # 确保使用self.agent_name作为run_name，避免传递None
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            # 添加以下配置以支持更详细的中间步骤追踪
            return_intermediate_steps=True,  # 返回中间步骤
            trim_intermediate_steps=trim_steps,  # 裁剪中间步骤，防止过长
            max_iterations=10  # 限制最大迭代次数
        ).with_config({
            "run_name": self.agent_name,  # 使用实例中的agent_name
            "tags": ["streaming"]  # 添加标签以便于识别
        })

    async def run(self, input_text: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        运行Agent处理输入
        
        Args:
            input_text: 用户输入文本或包含更多上下文信息的字典
            
        Returns:
            Dict[str, Any]: Agent的响应结果
        """
        await self.validation()

        if not self.agent_executor:
            await self.initialize()
            
        if not self.agent_executor:
            raise ValueError("Agent执行器未初始化")
            
        # 记录用户输入到对话历史
        task_content = input_text if isinstance(input_text, str) else input_text.get("input", "")
        await self.conversation_repo.create(
            project_id=self.project_id,
            message_type="user",
            content=task_content
        )
        
        # 执行Agent
        if isinstance(input_text, dict):
            result = await self.agent_executor.ainvoke(input_text)
        else:
            result = await self.agent_executor.ainvoke({"input": input_text})
        
        # 记录助手回复到对话历史
        if "output" in result:
            await self.conversation_repo.create(
                project_id=self.project_id,
                message_type="assistant",
                content=result["output"]
            )
            
        return result
    
    async def save_thinking(self, thinking: str) -> None:
        """
        保存Agent的思考过程
        
        Args:
            thinking: 思考过程文本
        """
        await self.thinking_repo.create(
            project_id=self.project_id,
            user_message_id=0,  # 需要提供一个有效的用户消息ID
            content=thinking
        )
    
    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Args:
            limit: 返回的历史记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 对话历史记录
        """
        history = await self.conversation_repo.get_project_history(
            project_id=self.project_id,
            limit=limit
        )
        
        return [
            {
                "id": item.id,
                "message_type": item.message_type,
                "content": item.content,
                "created_at": item.created_at.isoformat()
            }
            for item in history
        ]

    async def _get_conversation_context(
        self,
        project_id: int,
        max_tokens: int = 8000,
        max_messages: int = 20
    ) -> List[Dict[str, str]]:
        """
        获取对话上下文，并根据token限制和优先级进行修剪

        Args:
            project_id: 工程ID
            max_tokens: 最大允许的token数量
            max_messages: 最大消息数量限制

        Returns:
            格式化的上下文消息列表，可直接用于大模型输入
        """
        # 从数据库获取标记为包含在上下文中的历史消息
        # 注意：只包含system、user和assistant类型的消息，不包含assistant_thinking
        messages = await self.conversation_repo.get_project_history(
            project_id=project_id,
            limit=max_messages * 2,  # 获取足够多的消息，以便后续筛选
            only_context=True  # 仅获取标记为包含在上下文中的消息
        )

        # 按照序号排序，确保对话顺序正确
        messages.sort(key=lambda x: x.sequence)

        # 开始构建上下文，从最新的消息开始处理
        context = []
        current_tokens = 0
        message_count = 0

        # 首先添加高优先级消息
        high_priority_messages = [m for m in messages if m.priority > 1]
        high_priority_messages.sort(key=lambda x: x.sequence)

        for msg in high_priority_messages:
            # 粗略估计token数量：按照每个字符大约对应0.5个token
            estimated_tokens = len(msg.content) // 2

            if current_tokens + estimated_tokens <= max_tokens and message_count < max_messages:
                message_type = msg.message_type
                role = "system"
                if message_type == "user":
                    role = "user"
                elif message_type == "assistant":
                    role = "assistant"

                context.append({
                    "role": role,
                    "content": msg.content
                })

                current_tokens += estimated_tokens
                message_count += 1
            else:
                # 如果添加该消息会超出限制，则跳过
                continue
        return context
    
    # 以下是新增的流式响应和事件处理方法

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
        self.all_thoughts = []
        self._current_callback = callback
        
        # 获取项目信息
        project_info = await self.project_repo.get_project_info(self.project_id)
        if not project_info:
            raise ValueError("找不到指定的工程")
        project_name = project_info["name"]
        project_description = project_info["description"]

        # 获取历史上下文
        history_text = ""
        context_messages = await self._get_conversation_context(
            self.project_id, max_tokens=8000, max_messages=20
        )
        if context_messages:
            history_text = "对话历史：\n"
            for msg in context_messages:
                role_name = "系统"
                if msg["role"] == "user":
                    role_name = "用户"
                elif msg["role"] == "assistant":
                    role_name = "助手"
                history_text += f"{role_name}: {msg['content']}\n"

        # 返回LLM输入上下文
        return {
            "input": query,
            "history": history_text,
            "project_id": self.project_id,
            "project_name": project_name,
            "project_description": project_description,
            "context": json.dumps(self.context)
        }
    
    async def _handle_chain_end(self, event: Dict, callback: Callable, project_id: int, query: str) -> bool:
        """
        处理链结束事件，子类可以重写以添加自定义逻辑
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
            query: 用户查询
            
        Returns:
            bool: 是否处理完成
        """
        output = event["data"].get("output", {})
        if isinstance(output, AgentFinish):
            # 获取最终输出
            final_answer = output.return_values["output"]
            # 发送最终答案
            await callback({
                'type': 'final_answer',
                'content': f'{final_answer}',
                'project_id': project_id
            })
            
            # 只有当should_save_thinking为True时才保存对话记录和思考过程
            if self.should_save_thinking:
                # 保存用户问题和助手回答
                try:
                    # 保存用户问题
                    await self.conversation_repo.create(
                        project_id=project_id,
                        message_type="user",
                        content=query,
                        priority=2,
                        is_included_in_context=True
                    )
                    
                    # 保存助手回答
                    assist_message = await self.conversation_repo.create(
                        project_id=project_id,
                        message_type='assistant',
                        content=final_answer,
                        priority=2,
                        is_included_in_context=True
                    )
                    
                    # 保存思考过程
                    if self.all_thoughts:
                        complete_thinking = "".join(self.all_thoughts)
                        
                        await self.thinking_repo.create(
                            project_id=project_id,
                            user_message_id=assist_message.id,
                            content=complete_thinking
                        )
                except Exception as e:
                    await callback({
                        'type': 'system',
                        'content': f'保存对话记录时出错: {str(e)}',
                        'project_id': project_id
                    })
            
            return True
        
        return False
    
    async def _handle_chat_model_stream(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        处理聊天模型流事件，子类可以重写以添加自定义逻辑
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        content = event["data"]["chunk"].content
        # 直接发出
        await callback({
            'type': 'thought',
            'content': content,
            'project_id': project_id
        })
        # 收集思考内容
        self.all_thoughts.append(content)
    
    async def _handle_tool_start(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        处理工具开始事件，子类可以重写以添加自定义逻辑
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        pass
    
    async def _handle_tool_end(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        处理工具结束事件，子类可以重写以添加自定义逻辑
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        tool_name = event["name"]
        tool_output = event["data"]["output"]
        # 发送工具输出
        content = f"工具[{tool_name}]输出: {tool_output}\n"
        await callback({
            'type': 'thought',
            'content': content,
            'project_id': project_id
        })
        # 收集工具输出
        self.all_thoughts.append(content)
    
    async def _handle_tool_error(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        处理工具错误事件，子类可以重写以添加自定义逻辑
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        tool_name = event["data"]["name"]
        tool_input = event["data"]["input"]
        error_message = event["data"]["error"]
        error_content = f'{tool_name} 工具执行失败，输入: {tool_input}, 错误信息: {error_message}'
        # 发送错误信息
        await callback({
            'type': 'tool_error',
            'content': error_content,
            'tool_name': tool_name,
            'input': tool_input,
            'error': error_message,
            'project_id': project_id
        })
        # 收集错误信息
        self.all_thoughts.append(f"\n{error_content}\n")
    
    async def _handle_agent_action(self, event: Dict, callback: Callable, project_id: int) -> None:
        """
        处理智能体动作事件，子类可以重写以添加自定义逻辑
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
        """
        action = event["data"].get("action", {})
        action_input = action.get("action_input", "")
        tool_name = action.get("tool", "未知工具")
        await callback({
            'type': 'thought',
            'content': f'智能体计划使用工具: {tool_name}，输入: {action_input}',
            'project_id': project_id
        })
    
    async def _handle_error(self, e: Exception, callback: Callable, project_id: int, query: str) -> None:
        """
        处理错误，子类可以重写以添加自定义逻辑
        
        Args:
            e: 异常
            callback: 回调函数
            project_id: 项目ID
            query: 用户查询
        """
        error_message = f'处理查询时出错: {str(e)}'
        await callback({
            'type': 'system',
            'content': error_message,
            'project_id': project_id
        })
        print(f"[错误] {error_message}")

        # 记录错误
        self.all_thoughts.append(f"\n处理出错: {error_message}\n")

        # 出错情况下也保存用户问题和错误信息
        try:
            # 保存用户问题
            user_message = await self.conversation_repo.create(
                project_id=project_id,
                message_type="user",
                content=query,
                priority=2,
                is_included_in_context=True
            )

            # 保存错误信息作为系统消息
            await self.conversation_repo.create(
                project_id=project_id,
                message_type="system",
                content=f"错误: {error_message}",
                priority=1,
                is_included_in_context=False
            )

            # 保存思考过程
            if self.all_thoughts:
                complete_thinking = "".join(self.all_thoughts)

                await self.thinking_repo.create(
                    project_id=project_id,
                    user_message_id=user_message.id,
                    content=complete_thinking
                )
        except Exception as e:
            await callback({
                'type': 'system',
                'content': f'保存错误记录时出错: {str(e)}',
                'project_id': project_id
            })
    
    async def _handle_event(self, event: Dict, callback: Callable, project_id: int, query: str) -> Optional[bool]:
        """
        处理事件，判断事件类型并调用相应的处理方法
        
        Args:
            event: 事件数据
            callback: 回调函数
            project_id: 项目ID
            query: 用户查询
            
        Returns:
            Optional[bool]: 如果返回True表示处理完成，返回None表示继续处理
        """
        kind = event["event"]
        if self.last_kind is not None and self.last_kind != kind and len(self.all_thoughts) > 0:
            await callback({
                'type': 'thought',
                'content': "\n",
                'project_id': project_id
            })
            self.all_thoughts.append("\n")
        if kind == "on_chain_end":
            return await self._handle_chain_end(event, callback, project_id, query)
        elif kind == "on_chat_model_stream":
            await self._handle_chat_model_stream(event, callback, project_id)
        elif kind == "on_tool_start":
            await self._handle_tool_start(event, callback, project_id)
        elif kind == "on_tool_end":
            await self._handle_tool_end(event, callback, project_id)
        elif kind == "on_tool_error":
            await self._handle_tool_error(event, callback, project_id)
        elif kind == "on_agent_action":
            await self._handle_agent_action(event, callback, project_id)
        
        self.last_kind = kind
        return None
    
    async def generate_stream_response(
        self,
        query: str,
        callback: Callable[[Dict[str, Any]], Awaitable[None]] = None,
        should_save_thinking: bool = None
    ):
        """
        生成流式响应，处理各种事件
        
        Args:
            query: 用户查询
            callback: 回调函数，用于发送响应给客户端
            should_save_thinking: 是否保存思考过程，如果为None则使用初始化时的should_save_thinking
        """
        if not callback:
            return
        
        if not self.agent_executor:
            await callback({
                'type': 'system',
                'content': f'智能体未正确初始化',
                'project_id': self.project_id
            })
            return
        
        # 使用参数传入的project_id，如果为None则使用初始化时的project_id
            
        # 设置是否保存思考过程
        if should_save_thinking is not None:
            self.should_save_thinking = should_save_thinking
        
        try:
            await self.validation()
            # 响应生成前的准备工作
            context = await self._before_generation(query, callback)
            
            # 开始生成响应
            async for event in self.agent_executor.astream_events(context, version="v1"):
                # 处理事件
                completed = await self._handle_event(event, callback, self.project_id, query)
                
                # 如果已完成，退出循环
                if completed:
                    break
                    
        except Exception as e:
            # 处理错误
            await self._handle_error(e, callback, self.project_id, query)
            
            
            
            
            