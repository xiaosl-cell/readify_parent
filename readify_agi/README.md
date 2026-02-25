# Readify AGI

Readify AGI 是 Readify 智能阅读系统的后端 Agent 服务，基于 FastAPI + LangChain，提供多智能体协作、流式输出、文档检索与问答能力。

## 当前架构

### 架构类型

- 多智能体层级架构（Manager-Worker）
- 子 Agent 内核为单智能体 Tool Calling（Function Calling）

### 核心组件

- `CoordinatorAgentService`
  - 负责统一接收任务、选择/委派子 Agent、整合结果。
- `AskAgentService`
  - 面向文档问答，包含向量检索、项目文件查询、文件全文读取、可选联网搜索工具。
- `NoteAgentService`
  - 面向笔记与思维导图相关任务。
- `AgentService`
  - 所有 Agent 的基类，负责 LLM 初始化、工具加载、事件流处理、会话与思考过程存储。

### 执行链路

1. 客户端调用 `GET /api/v1/agent/stream`
2. 路由构建 `CoordinatorAgentService` 并注册 `AskAgentService`、`NoteAgentService`
3. Coordinator 按任务类型与上下文决定是否调用 `delegate_task`
4. 子 Agent 通过 Tool Calling 执行工具并流式返回
5. 最终答案和中间事件通过 SSE 持续输出

对应代码：

- `app/api/v1/agent_router.py`
- `app/services/coordinator_agent_service.py`
- `app/services/ask_agent_service.py`
- `app/services/note_agent_service.py`
- `app/services/agent_service.py`

## 重要说明

- 当前仅支持 Tool Calling 路径。
- 已移除 `AGENT_MODE` 配置，README 与配置文件均不再包含 ReAct 模式切换。

## 核心能力

- 多智能体任务拆解与协作
- 文档向量检索与上下文问答
- 思维导图相关结构化操作（Note Agent）
- 流式事件输出（thought/tool/final_answer）
- 对话与思考过程持久化

## 快速开始

### 1. 环境准备

- Python 3.11
- pip 或 conda

### 2. 安装依赖

```bash
cd readify_agi
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

至少需要配置：

- `LLM_PROVIDER`
- `LLM_API_KEY`
- `LLM_API_BASE`
- `LLM_MODEL_NAME`
- 数据库连接相关配置

### 4. 启动服务

```bash
python main.py
```

默认地址：

- `http://localhost:8081`
- Swagger: `http://localhost:8081/docs`

## Agent 相关配置

以下配置与当前 Agent 架构直接相关：

- `LLM_PROVIDER`：`openai` 或 `anthropic`
- `LLM_API_KEY`：LLM 访问密钥
- `LLM_API_BASE`：LLM API 基础地址
- `LLM_MODEL_NAME`：模型名
- `LLM_DEFAULT_HEADERS`：可选，自定义请求头（JSON 字符串）
- `QUERY_REWRITE_ENABLED`：是否启用检索前查询改写
- `SERPAPI_API_KEY`：可选，Ask Agent 联网搜索能力

## 如何新增专业 Agent

继承 `AgentService` 并实现三个扩展点：

- `_load_prompt_template_async`
- `_load_system_prompt_async`
- `_load_tools`

示例：

```python
from typing import Any, Dict, List, Optional
from langchain_core.tools import BaseTool, tool
from app.services.agent_service import AgentService


class CustomAgentService(AgentService):
    def __init__(self, project_id: int, context: Dict[str, Any] | None = None):
        super().__init__(project_id=project_id, context=context)

    async def _load_prompt_template_async(self):
        self.prompt_template = await self._load_prompt_from_client("custom_agent")

    async def _load_system_prompt_async(self) -> Optional[str]:
        return await self._load_system_prompt_from_client("custom_agent")

    async def _load_tools(self) -> List[BaseTool]:
        tools = await super()._load_tools()

        @tool
        async def custom_tool(input_str: str) -> str:
            return f"custom result: {input_str}"

        tools.append(custom_tool)
        self.tools = tools
        return tools
```

然后在协调器初始化处注册该 Agent（参考 `app/api/v1/agent_router.py`）。

## 主要接口

### `GET /api/v1/agent/stream`

关键参数：

- `query`：用户输入
- `project_id`：项目 ID
- `task_type`：任务类型（由依赖注入读取，常用 `ask` / `note`）
- `context`：JSON 字符串（可 URL 编码）

返回：SSE 流，事件类型示例：

- `thought`
- `tool_error`
- `final_answer`
- `[DONE]`

## 项目结构

```text
readify_agi/
  app/
    api/
    core/
    models/
    repositories/
    services/
    static/
    utils/
  data/
  migrations/
  scripts/
  tests/
  .env.example
  main.py
  requirements.txt
```
