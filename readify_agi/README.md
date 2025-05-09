# 协调Agent服务

## 项目简介

协调Agent服务是一个能够管理和协调多个专业Agent协作完成复杂任务的框架。通过将不同的专业Agent注册到协调器中，可以根据任务性质自动选择或组合合适的Agent来处理用户请求。

## 主要特性

- **智能任务分发**: 根据用户查询自动选择合适的专业Agent
- **多Agent协作**: 支持将复杂任务分解为子任务，并交由不同的Agent协作完成
- **工作流管理**: 支持定义和执行多Agent协作的工作流
- **流式输出**: 支持实时显示思考过程和工具执行结果
- **会话记忆**: 保存对话历史和思考过程，支持长期记忆

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 创建专业Agent

首先，继承基础的`AgentService`类来创建专业Agent:

```python
from app.services.agent_service import AgentService

class CodeAgentService(AgentService):
    """代码专业Agent"""
    
    def __init__(self, db, project_id, model_name="gpt-4o", temperature=0.5):
        super().__init__(db, project_id, model_name, temperature)
        self.description = "专门用于代码分析、生成和优化的智能体"
        # 设置专用的提示模板
        self.prompt_template = "..."
```

### 2. 创建并配置协调Agent

使用工厂方法创建协调Agent并注册专业Agent:

```python
from app.services.coordinator_agent_service import CoordinatorAgentService

# 创建协调Agent

```

### 3. 使用协调Agent处理用户查询

```python
# 定义回调函数处理输出
async def handle_response(response):
    # 处理Agent的响应...
    pass

# 处理用户查询
await coordinator.generate_stream_response(
    query="帮我分析这段代码并优化性能",
    callback=handle_response,
    db=db,
    project_id=project_id
)
```

## 示例

参考`examples/coordinator_agent_example.py`查看完整示例。

## 定制协调器

你可以通过以下方式定制协调器的行为:

1. 创建自定义的提示模板文件(`prompt/coordinator.prompt`)
2. 添加自定义工具到协调器
3. 实现特定领域的专业Agent
4. 调整协调策略和工作流设计

## 工具说明

协调Agent包含以下核心工具:

- `list_available_agents`: 列出所有可用的专业Agent
- `delegate_task`: 将任务委派给指定的专业Agent
- `execute_multi_agent_workflow`: 执行预定义的多Agent工作流
- `get_task_status`: 获取任务执行状态

## 许可证

MIT 