# Readify - 智能阅读笔记助手

<div align="center">
  <h3>基于AI的智能阅读笔记和思维导图生成工具</h3>

  ![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
  ![Java](https://img.shields.io/badge/Java-17-007396?style=for-the-badge&logo=java&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2.2-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
</div>

## 项目概述

Readify是一个智能阅读笔记助手系统，通过AI技术帮助用户轻松整理知识并生成直观的思维导图。项目采用微服务架构，由五个核心模块组成：

- **readify_frontend** - 基于 Vue 3 + TypeScript 的前端应用
- **readify_server** - 基于 Spring Boot 3.2.2 的后端服务（DDD架构）
- **readify_agi** - 基于 FastAPI 的 AI 服务层（多Agent系统）
- **readify_admin** - 基于 Vue 3 + TypeScript 的管理后台（RBAC权限管理）
- **readify_eval** - 评测平台（包含 backend/frontend 两部分）

## 功能展示

<div align="center">
  <img src="img/1-首页.png" alt="首页" width="80%">
  <p><i>首页 - 项目管理和文档上传</i></p>

  <img src="img/2-对话-1.png" alt="对话界面1" width="80%">
  <p><i>对话界面 - 思考过程</i></p>

  <img src="img/3-对话-2.png" alt="对话界面2" width="80%">
  <p><i>对话界面 - 最终答案</i></p>

  <img src="img/4-笔记.png" alt="笔记界面" width="80%">
  <p><i>笔记界面 - 笔记管理</i></p>

  <img src="img/5-笔记生成.png" alt="笔记生成" width="80%">
  <p><i>笔记生成 - 自动分析</i></p>

  <img src="img/6-笔记生成.png" alt="笔记生成结果" width="80%">
  <p><i>笔记生成 - 结果展示</i></p>
</div>

## 核心功能

- **智能问答** - 基于RAG（检索增强生成）的文档问答，结合向量检索和LLM
- **智能笔记生成** - 支持多层级生成结构化笔记
- **思维导图可视化** - 直观展示知识结构和关系
- **多Agent协作** - Coordinator、Ask、Note等多智能体协作
- **多种AI模型支持** - 支持OpenAI、Qwen、DeepSeek等大语言模型
- **多格式文档支持** - 支持PDF、TXT、DOCX等文档格式（通过LlamaParse解析）
- **实时交互反馈** - 思考过程通过WebSocket实时展示

## 技术架构

```
readify_parent/
├── readify_frontend/    # Vue 3 前端项目
├── readify_server/      # Spring Boot 后端服务
├── readify_agi/         # FastAPI AI智能体服务
├── readify_admin/       # Vue 3 管理后台
├── readify_eval/        # 评测平台（backend/frontend）
└── infra/               # 基础设施配置（Docker Compose）
```

### 服务通信流程

```
前端 (5173) → 后端服务 (8080) → AGI 服务 (8081)
                    ↓                ↓
                 Nacos (8848) ← 服务发现与注册
                    ↓
                MySQL (共享数据库)
                    ↓
              Milvus (向量数据库)
                    ↓
              MinIO (对象存储)
```

### 技术栈详情

| 模块 | 技术栈 |
|------|--------|
| **Frontend** | Vue 3, TypeScript, Element Plus, Vite, markmap.js |
| **Server** | Java 17, Spring Boot 3.2.2, MyBatis-Plus, Spring Cloud |
| **AGI** | Python 3.9+, FastAPI, LangChain, OpenAI SDK |
| **数据库** | MySQL 8.0+ (业务数据), Milvus (向量存储) |
| **存储** | MinIO (对象存储) |
| **服务发现** | Nacos 2.x |

### 核心工作流

1. **文档处理**：上传 → Server存储到MinIO → AGI解析(LlamaParse) → 向量化 → 存储到Milvus
2. **智能问答**：提问 → Coordinator Agent → Ask Agent (RAG + LLM) → WebSocket流式响应
3. **笔记生成**：请求 → Note Agent → 结构化笔记/思维导图

## 快速开始

### 前提条件

**Docker 部署（推荐）**
- Docker >= 20.10
- Docker Compose >= 2.0

**本地开发（可选）**
- Node.js 16+
- JDK 17+
- Python 3.9+
- MySQL 8.0+

### Docker 启动（推荐）

以下步骤默认在仓库根目录 `readify_parent` 执行。

### 1. 启动基础设施

```bash
# 在项目根目录执行
docker compose -f infra/docker-compose.yml up -d

# 查看基础设施状态
docker compose -f infra/docker-compose.yml ps
```

这将启动以下服务：
- **Nacos** - 服务注册与配置中心 (端口: 8848)
- **MySQL** - 关系型数据库 (端口: 3306)
- **Milvus** - 向量数据库 (端口: 19530)
- **MinIO** - 对象存储 (端口: 9000, 控制台: 9001)

### 2. 初始化数据库

```bash
# 初始化业务库（readify）
mysql -h 127.0.0.1 -P 3307 -u root -proot -e "CREATE DATABASE IF NOT EXISTS readify DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot readify < readify_server/src/main/resources/db/migration/db.sql

# 初始化评测库（readify_eval）
mysql -h 127.0.0.1 -P 3307 -u root -proot -e "CREATE DATABASE IF NOT EXISTS readify_eval DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot readify_eval < readify_eval/sql/readify_eval_flow.sql
```

### 3. 配置后端服务 (readify_server)

```bash
cd readify_server
# 修改配置文件或通过Nacos配置中心管理
vim src/main/resources/application.yml
```

主要配置项：
- `spring.cloud.nacos.*` - Nacos连接配置

本地配置文件位置：`readify_server/src/main/resources/application.yml`

### 4. 配置AGI服务 (readify_agi)

```bash
cd readify_agi
vim .env
```

主要配置项：
```env
# Service / Nacos
SERVICE_NAME=readify-agi
SERVICE_PORT=8081

NACOS_ENABLED=true
NACOS_SERVER_ADDR=localhost:8848
NACOS_NAMESPACE=ca5b6af9-5336-42f7-b68c-515779f79a98
NACOS_GROUP=READIFY
NACOS_USERNAME=nacos
NACOS_PASSWORD=nacos2025
NACOS_CLUSTER=DEFAULT
NACOS_HEARTBEAT_INTERVAL=5
NACOS_CONFIG_DATA_ID=readify-agi.yaml
READIFY_SERVER_SERVICE_NAME=readify-server
```

### 补充：管理后台本地配置 (readify_admin)

管理后台不依赖 Nacos 配置中心，使用本地 `Vite` 代理配置：

```bash
cd readify_admin
vim vite.config.ts
```

主要配置项：
- `server.port`（默认 `5174`）
- `server.proxy['/api'].target`（默认 `http://localhost:8080`）

### Nacos 配置文件

- **Data ID：`readify-server.yaml`**

```yaml
server:
  port: 8080

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    # 如：jdbc:mysql://mysql8:3306/readify?useUnicode=true&characterEncoding=utf-8&useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
    url: {mysql数据库}
    username: root
    password: {数据库密码}
  mvc:
    servlet:
      path: /api/v1
  servlet:
    multipart:
      max-file-size: 100MB
      max-request-size: 100MB

logging:
  level:
    com.readify.server.infrastructure.security: INFO
    com.readify.server.domain.auth.service: INFO
    org.springframework.security: INFO

mybatis-plus:
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl
  global-config:
    db-config:
      id-type: auto
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0
  mapper-locations: classpath*:/mapper/**/*.xml
  type-aliases-package: com.readify.server.infrastructure.persistence.entity

jwt:
  secret: 8Zz5tw0Ionm3XPZZfN0NOml3z9FMfmpgXwovR9fp6ryDIoGRM8EPHAB6iHsc0fb
  validity-in-seconds: 86400

# 调用 AGI 服务用到的配置（代码里通过 @Value("${readify.agi-service.name}") 使用）
readify:
  file:
    storage-type: minio
    minio:
      # 容器内 http://minio:9000
      endpoint: http://milvus-minio:9000   
      access-key: minioadmin
      secret-key: minioadmin
      bucket: readify
  agi-service:
    name: readify-agi
```

- **Data ID：`readify-agi.yaml`**

```yaml
# 数据库配置
DB_HOST: mysql8
DB_PORT: 3306
DB_USER: root
DB_PASSWORD: {密码}
DB_NAME: readify

# 向量库 / 向量服务（按你的实际情况调整）
MILVUS_HOST: milvus-standalone
MILVUS_PORT: 19530
MILVUS_USER: ""
MILVUS_PASSWORD: ""
MILVUS_DB_NAME: default

# LlamaParse 配置 https://cloud.llamaindex.ai 自行申请
LLAMA_PARSE_API_KEY: {LLAMA_PARSE_API_KEY}

# LLM 配置
LLM_API_KEY: sk-57133487fa5548e1b9f06cfb9dee6506
# 如http://aaaa:10020/v1
LLM_API_BASE: {openai格式的地址}
LLM_MODEL_NAME: {模型名称}

# Embedding 配置
EMBEDDING_API_KEY: {your_embedding_key}
EMBEDDING_API_BASE: {your_embedding_url}
EMBEDDING_MODEL: {your_embedding_model}

# 文件处理回调到 readify-server 的配置
FILE_PROCESS_CALLBACK_URL: http://readify-server/file/vectorized-callback
FILE_PROCESS_CALLBACK_API_KEY: uFjMA2BAZ4xK1b-cfHyPJNF7lFkQ6CDZVk0p7--yGnQ

# 搜索服务
SERPAPI_API_KEY: {https://serpapi.com/申请}

# 服务自身 & Nacos 注册信息（也可以仅走环境变量）
SERVICE_NAME: readify-agi
SERVICE_HOST: ""
SERVICE_PORT: 8090

# 需要通过服务发现访问的 Java 服务名称
READIFY_SERVER_SERVICE_NAME: readify-server

MINIO_ENDPOINT: http://milvus-minio:9000
MINIO_ACCESS_KEY: minioadmin
MINIO_SECRET_KEY: minioadmin
MINIO_SECURE: false
```

- **Data ID：`readify-eval.yaml`**

```yaml
# readify-eval.yaml
app:
  name: "Readify Eval Flow"
  version: "1.0.0"
  description: "FastAPI Application with Layered Architecture"
  debug: false # 生产环境建议设为 false
  host: "0.0.0.0"
  port: 8000

database:
  # 建议使用环境变量替代硬编码
  url: {readify_eval_flow数据库地址}
  echo: false
  pool_size: 5
  max_overflow: 10
  pool_pre_ping: true

cors:
  # 生产环境请务必限制域名
  allow_origins: 
    - "*"
  allow_credentials: true
  allow_methods: ["*"]
  allow_headers: ["*"]

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  log_dir: "logs"
  log_file: "app.log"
  backup_count: 30
  console_output: true
  console_level: "DEBUG"
  file_level: "INFO"
```

### 5. 启动服务

```bash
# 首次或配置变更后，构建并启动全部应用服务
docker compose up -d --build

# 后续快速启动（无需重建）
docker compose up -d

# 查看应用服务状态
docker compose ps

# 查看应用服务日志
docker compose logs -f

# 查看单个服务日志
docker compose logs -f readify-server
docker compose logs -f readify-agi
docker compose logs -f readify-eval-backend
docker compose logs -f readify-nginx
```

### 6. 访问应用

- **前端应用**: http://localhost:5173
- **管理后台**: http://localhost:5174
- **评测平台**: http://localhost:5175
- **Server Swagger**: http://localhost:8080/swagger-ui.html
- **AGI OpenAPI**: http://localhost:8081/docs
- **Eval OpenAPI**: http://localhost:8082/docs
- **Nacos控制台**: http://localhost:8848/nacos (用户名/密码: nacos/nacos)
- **MinIO控制台**: http://localhost:9001 (用户名/密码: minioadmin/minioadmin)

### 7. Docker 常用运维命令

```bash
# 停止应用服务（保留数据）
docker compose down

# 停止基础设施（保留数据）
docker compose -f infra/docker-compose.yml down

# 停止基础设施并删除数据卷（谨慎）
docker compose -f infra/docker-compose.yml down -v

# 重建并启动单个应用服务
docker compose up -d --build readify-server

# 查看基础设施日志
docker compose -f infra/docker-compose.yml logs -f
```

## 开发命令

### 前端 (readify_frontend)
```bash
npm install          # 安装依赖
npm run dev          # 启动开发服务器 (端口 5173)
npm run build        # 生产环境构建
npm run preview      # 预览生产构建
```

### 后端 (readify_server)
```bash
./mvnw clean package                    # 构建项目
./mvnw spring-boot:run                  # 启动服务 (端口 8080)
./mvnw test                             # 运行测试
./mvnw test -Dtest=类名                  # 运行单个测试类
```

### AGI服务 (readify_agi)
```bash
pip install -r requirements.txt    # 安装依赖
python main.py                     # 启动服务 (端口 8081)
pytest tests/                      # 运行测试
```

## 项目结构

### readify_server (DDD架构)

```
com.readify.server/
├── domain/              # 领域层
│   ├── auth/            # 认证领域
│   ├── conversation/    # 对话领域
│   ├── file/            # 文件领域
│   ├── mind_map/        # 思维导图领域
│   ├── notetask/        # 笔记任务领域
│   ├── project/         # 项目领域
│   └── user/            # 用户领域
├── infrastructure/      # 基础设施层
│   ├── persistence/     # 持久化（entity, mapper, converter）
│   ├── security/        # 安全（JWT, 过滤器）
│   ├── common/          # 通用组件
│   └── utils/           # 工具类（文件存储等）
├── interfaces/          # 接口层
│   └── */               # REST控制器
└── websocket/           # WebSocket处理器
```

### readify_agi (多Agent架构)

```
app/
├── api/v1/           # FastAPI路由
├── core/             # 配置、数据库、Nacos客户端
├── models/           # SQLAlchemy模型
├── repositories/     # 数据访问层（异步）
├── services/         # 业务逻辑和Agent服务
│   ├── coordinator_agent_service.py  # 协调Agent
│   ├── ask_agent_service.py          # 问答Agent (RAG)
│   ├── note_agent_service.py         # 笔记Agent
│   ├── vector_store_service.py       # 向量存储服务
│   └── file_vectorize_service.py     # 文件向量化服务
└── prompts/          # LLM提示词模板
```

## 功能模块

### 前端模块
- **用户界面**: 登录注册、项目管理、文件上传
- **笔记系统**: 笔记查看、编辑和管理
- **思维导图**: 基于markmap.js的交互式知识图谱
- **对话界面**: WebSocket实时交互问答

### 后端模块
- **用户认证**: 基于JWT的认证和权限控制
- **项目管理**: 创建和管理读书项目
- **文件管理**: 支持MinIO和本地存储
- **对话历史**: 记录用户与AI的交互历史

### AGI模块
- **智能体协调**: 多Agent协作，动态任务分配
- **文档处理**: LlamaParse解析、向量化、语义理解
- **知识问答**: 基于Milvus的RAG问答系统
- **笔记生成**: 自动生成结构化文档笔记

## 开发指南

### 代码风格
- 前端: 遵循ESLint和Vue风格指南
- 后端: 遵循Google Java风格指南
- AGI: 遵循PEP 8，使用类型提示，优先异步函数

### 开发规范
- 控制器统一返回 `Result<T>` 对象
- 请求DTO使用 `*Req` 后缀，视图对象使用 `*VO` 后缀
- 使用MapStruct进行对象映射，Lombok简化样板代码

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

## 许可证

[MIT License](LICENSE)

---

<div align="center">
  <p>Made with ❤️ by Readify</p>
</div>
