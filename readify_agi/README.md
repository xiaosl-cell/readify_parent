# 📚 Readify AGI

<div align="center">
  <h3>Readify智能读书助手的AGI底座</h3>
  <p>基于多智能体协作的复杂任务解决方案</p>
  
  ![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
  ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
  ![LangChain](https://img.shields.io/badge/LangChain-2C2D72?style=for-the-badge&logo=chainlink&logoColor=white)
</div>

## ✨ 功能特点

Readify AGI 是 Readify 智能读书助手的 AGI 底座，主要有如下能力:

- 🧠 **智能任务分发** - 基于用户查询自动选择最合适的专业 Agent
- 🤝 **多Agent协作** - 将复杂任务分解为子任务，由不同专业 Agent 协同完成
- 🔄 **工作流管理** - 定义和执行复杂的多 Agent 协作工作流
- 📝 **流式输出** - 实时展示思考过程和工具执行结果
- 💬 **会话记忆** - 保存对话历史和思考过程，支持上下文理解和长期记忆
- 📄 **文档处理** - 支持文档解析、向量化和语义搜索
- ✏️ **文本修复** - 智能识别和修复文本问题

## 🛠️ 技术栈

- **后端框架**: FastAPI, Python 3.11
- **大语言模型**: OpenAI, Qwen, Deepseek...
- **Agent框架**: LangChain
- **数据库**: SQLAlchemy, MySQL
- **向量数据库**: ChromaDB
- **文档处理**: Local Parser + OCR, PyPDF
- **异步处理**: Uvicorn, ASGI

## 📋 前提条件

- Python 3.11
- Conda 或 pip 包管理工具

## 🚀 快速开始

1. 确保本地conda环境已安装并能够正常工作

2. 创建、激活conda环境，安装依赖

```bash
# 1. 创建新的conda环境
conda create -n readify_agi python=3.11 -y

# 2. 激活环境
conda activate readify_agi

# 3. 配置pip镜像源（可选）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# 4. 安装依赖
pip install -r requirements.txt
```

3. 启动服务

```bash
python main.py
```

服务默认在 `http://localhost:8081` 启动

## 🧩 项目结构

```
readify_agi/
├── app/                    # 应用核心代码
│   ├── api/                # API 接口定义
│   ├── core/               # 核心功能模块
│   ├── models/             # 数据模型
│   ├── repositories/       # 数据访问层
│   ├── services/           # 业务逻辑服务
│   ├── static/             # 静态资源
│   └── utils/              # 工具函数
├── prompt/                 # 提示词模板
├── static/                 # 全局静态资源
├── test/                   # 测试代码
├── main.py                 # 应用入口
├── environment.yml         # Conda 环境配置
└── README.md               # 项目文档
```

## 💻 开发指南

### 创建专业 Agent

继承基础的 `AgentService` 类来创建专业 Agent：

```python
from app.services.agent_service import AgentService

class CustomAgentService(AgentService):
    """自定义专业 Agent"""
    
    def __init__(self, db, project_id, model_name="gpt-4o", temperature=0.5):
        super().__init__(db, project_id, model_name, temperature)
        self.description = "专门处理特定领域任务的智能体"
        # 设置专用的提示模板
        self.prompt_template = "..."
```

### 配置并使用协调 Agent

```python
from app.services.coordinator_agent_service import CoordinatorAgentService

# 创建协调 Agent
coordinator = CoordinatorAgentService(db, project_id)

# 注册专业 Agent
coordinator.register_agent("custom", CustomAgentService(db, project_id))

# 处理用户查询
async def handle_response(response):
    print(response)

await coordinator.generate_stream_response(
    query="执行特定任务的指令",
    callback=handle_response,
    db=db,
    project_id=project_id
)
```

## 🤖 现有专业 Agent

- **Agent Service**: 基础智能体服务
- **Coordinator Agent**: 智能体调度器
- **Note Agent**: 笔记生成智能体
- **Ask Agent**: 知识问答智能体

## 🔧 提供能力

- **智能体协调**: 支持多智能体协作，动态分配和管理任务
- **文档处理**: 支持多种格式文档的解析、向量化和语义理解
- **知识问答**: 基于文档内容的智能问答和知识推理
- **笔记管理**: 自动生成和组织文档笔记
- **实时反馈**: 提供流式输出，实时展示智能体思考过程

## 📡 API 接口

访问 `http://localhost:8081/docs` 查看完整的 API 文档

## 🤝 贡献指南

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">
  <p>Made with ❤️ by Readify AGI</p>
</div> 
