# Readify Eval Flow

FastAPI应用程序，采用分层架构设计，使用SQLAlchemy作为ORM。

## 项目架构

本项目采用清晰的分层架构：

```
readify_eval_flow/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置管理
│   │   └── database.py         # 数据库连接
│   ├── models/                 # 数据库模型层
│   │   ├── __init__.py
│   │   └── example.py          # 示例模型
│   ├── schemas/                # Pydantic模型（请求/响应）
│   │   ├── __init__.py
│   │   └── example.py          # 示例Schema
│   ├── repositories/           # 数据访问层
│   │   ├── __init__.py
│   │   ├── base.py             # 基础Repository
│   │   └── example.py          # 示例Repository
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   └── example.py          # 示例Service
│   └── api/                    # API路由层
│       └── v1/
│           ├── __init__.py
│           └── endpoints/
│               ├── health.py   # 健康检查
│               └── example.py  # 示例API
├── config.yaml                 # 配置文件
├── requirements.txt            # Python依赖
└── README.md
```

## 架构说明

### 分层架构

1. **API层** (`app/api/`)
   - 处理HTTP请求和响应
   - 参数验证
   - 调用Service层

2. **Service层** (`app/services/`)
   - 业务逻辑处理
   - 事务管理
   - 调用Repository层

3. **Repository层** (`app/repositories/`)
   - 数据访问逻辑
   - 数据库CRUD操作
   - 查询封装

4. **Model层** (`app/models/`)
   - SQLAlchemy数据库模型
   - 表结构定义

5. **Schema层** (`app/schemas/`)
   - Pydantic数据验证模型
   - 请求/响应数据结构

6. **Core层** (`app/core/`)
   - 配置管理
   - 数据库连接
   - 全局依赖

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.yaml` 文件，配置数据库连接等参数：

```yaml
database:
  # SQLite (开发环境)
  url: "sqlite:///./app.db"
  
  # PostgreSQL
  # url: "postgresql+asyncpg://user:password@localhost:5432/dbname"
  
  # MySQL
  # url: "mysql+pymysql://user:password@localhost:3306/dbname"
```

### 3. 运行应用

```bash
cd backend
python run.py
```

### 4. 访问API文档

- Swagger UI: http://localhost:8082/docs
- ReDoc: http://localhost:8082/redoc
- OpenAPI JSON: http://localhost:8082/openapi.json

## 功能模块

### 核心模块

1. **AI 模型管理** (`/api/v1/ai-models`)
   - 管理 AI 模型配置
   - 支持多种模型类别（推理型/指令型）

2. **提示词模板管理** (`/api/v1/prompt-templates`)
   - 创建和管理提示词模板
   - 支持变量替换
   - 配置 LLM 参数

3. **提示词用例管理** (`/api/v1/prompt-use-cases`)
   - 为模板创建具体用例
   - 自动渲染提示词
   - 支持关键词搜索

4. **系统配置管理** (`/api/v1/system-configs`)
   - 键值对配置存储
   - 支持批量操作
   - 配置分组管理

5. **用例测试模块** (`/api/v1/test-tasks`) ⭐ 新功能
   - 批量执行提示词用例
   - 异步任务执行
   - 实时进度追踪
   - 完整的执行快照和结果记录
   - 详细文档：[测试模块 API 文档](docs/test-task-api.md)

## API端点示例

### 健康检查

```bash
# 健康检查
GET /api/v1/health

# 根路径
GET /api/v1/
```

### 用例测试模块（新功能）

```bash
# 创建测试任务
POST /api/v1/test-tasks
{
  "task_name": "客服场景测试",
  "task_description": "测试客服机器人表现",
  "use_case_ids": ["case-1", "case-2", "case-3"],
  "ai_model_id": "model-id"
}

# 启动任务执行
POST /api/v1/test-tasks/{task_id}/start

# 获取任务状态
GET /api/v1/test-tasks/{task_id}/status

# 获取任务详情
GET /api/v1/test-tasks/{task_id}

# 分页查询执行记录（推荐）
GET /api/v1/executions?task_id={task_id}&skip=0&limit=20

# 取消任务
POST /api/v1/test-tasks/{task_id}/cancel
```

**重要说明**：执行记录已移至独立的执行记录模块，支持分页查询。
详细使用示例请参考：
- [测试任务 API 文档](docs/test-task-api.md)
- [执行记录 API 文档](docs/test-execution-api.md)
- [用例测试使用示例](docs/test-task-examples.md)

## 数据库支持

本项目支持多种数据库：

- **SQLite** (默认，适合开发环境)
- **PostgreSQL** (推荐生产环境，支持异步)
- **MySQL** (支持同步访问)

### 切换数据库

在 `config.yaml` 中修改数据库URL：

```yaml
database:
  # PostgreSQL (异步)
  url: "postgresql+asyncpg://user:password@localhost:5432/dbname"
  
  # MySQL (同步)
  url: "mysql+pymysql://user:password@localhost:3306/dbname"
  
  # SQLite (同步)
  url: "sqlite:///./app.db"
```

**注意**: 使用PostgreSQL的异步驱动时，需要安装 `asyncpg`。

## 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 初始化Alembic
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回退迁移
alembic downgrade -1
```

## 开发指南

### 添加新功能

1. **创建数据库模型** (`app/models/your_model.py`)
2. **创建Schema** (`app/schemas/your_schema.py`)
3. **创建Repository** (`app/repositories/your_repository.py`)
4. **创建Service** (`app/services/your_service.py`)
5. **创建API端点** (`app/api/v1/endpoints/your_endpoint.py`)
6. **注册路由** (在 `app/api/v1/__init__.py` 中)

### 代码规范

- 使用类型提示
- 编写文档字符串
- 遵循PEP 8规范
- 使用有意义的变量名

### 测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest
```

## 配置说明

### 环境变量

可以通过环境变量覆盖配置：

```bash
export APP_DEBUG=true
export DATABASE_URL="postgresql://..."
```

### 配置优先级

1. 环境变量
2. config.yaml
3. 默认值

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t readify_eval_flow .

# 运行容器
docker run -p 8082:8082 readify_eval_flow
```

### 生产环境建议

- 使用PostgreSQL或MySQL作为数据库
- 设置 `debug: false`
- 配置适当的CORS策略
- 使用环境变量管理敏感信息
- 启用日志记录
- 使用反向代理（Nginx）
- 配置HTTPS

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

