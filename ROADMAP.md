# Readify 项目演进规划

## 目录

1. [Eval 提示词模板版本管理](#1-eval-提示词模板版本管理)
2. [Eval 开放提示词模板管理接口](#2-eval-开放提示词模板管理接口)
3. [AGI 提示词模板迁移并接入](#3-agi-提示词模板迁移并接入)
4. [OCR / 查询改写 / 多路召回](#4-ocr--查询改写--多路召回)
5. [GraphRAG](#5-graphrag)
6. [A2A（Agent-to-Agent Protocol）](#6-a2aagent-to-agent-protocol)
7. [MCP（Model Context Protocol）](#7-mcpmodel-context-protocol)
8. [建议实施顺序](#建议实施顺序)

---

## 1. Eval 提示词模板版本管理(已完成)

**现状：** `eval_prompt_templates` 表支持模板 CRUD，但修改是原地覆盖，无版本历史。TestExecution 通过快照字段保留了历史状态，但无法回溯模板本身的变更轨迹。

**规划：**

- 新增 `eval_prompt_template_versions` 表，字段包括 `template_id`、`version`（自增）、`system_prompt`、`user_prompt`、`llm 参数`、`evaluation_strategies`、`change_log`、`created_by`、`created_at`
- 模板每次更新自动生成新版本记录，当前模板指向 `current_version`
- 支持版本对比（diff）、版本回滚、按版本创建测试用例
- TestTask / TestExecution 的快照增加 `template_version` 字段，建立精确溯源
- 前端增加版本历史列表、版本 diff 视图、一键回滚操作

---

## 2. Eval 开放提示词模板管理接口(已完成)

**现状：** `prompt_template.py` 有基础 CRUD 服务，但无对外 REST 接口暴露（`endpoints/` 目录下无 `prompt_template.py`）。模板管理只能通过内部服务调用。

**规划：**

- 新增 `app/api/v1/endpoints/prompt_template.py`，提供完整 RESTful 接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/prompt-templates` | 创建模板 |
| `GET` | `/prompt-templates` | 分页查询（支持按 `function_category`、`owner`、`prompt_source` 筛选） |
| `GET` | `/prompt-templates/{id}` | 获取详情（含版本历史） |
| `PUT` | `/prompt-templates/{id}` | 更新（自动生成新版本） |
| `DELETE` | `/prompt-templates/{id}` | 删除（级联删除关联用例） |
| `GET` | `/prompt-templates/{id}/versions` | 获取版本列表 |
| `POST` | `/prompt-templates/{id}/rollback/{version}` | 回滚到指定版本 |
| `POST` | `/prompt-templates/export` | 批量导出（JSON / YAML） |
| `POST` | `/prompt-templates/import` | 批量导入 |

- 接口鉴权：API Key 或 JWT Token
- 规范化错误码和响应格式，与现有 `BaseListResponse` 体系对齐

---

## 3. AGI 提示词模板迁移并接入(已完成)

**现状：** AGI 的提示词是磁盘上的纯文本文件（`prompt/*.prompt`），通过 `Path().read()` + Python `.format()` 加载，无版本管理、无动态更新能力，修改需重启服务。

**规划：**

### 阶段一：迁移到 Eval 平台

- 将 `ask_agent.prompt`、`coordinator.prompt`、`note_agent.prompt`、`label.prompt` 导入 Eval 的 `eval_prompt_templates` 表
- 模板变量语法从 `{variable}` 统一为 `<$variable>` 或双方兼容
- 设置 `prompt_source = 'agi'`、`function_category` 按 agent 类型分类

### 阶段二：AGI 接入 Eval 接口

- AGI 新增 `PromptTemplateClient`，启动时从 Eval API 拉取模板并缓存
- 支持定时刷新或 Nacos 配置变更通知触发热更新，无需重启
- `AgentService._load_prompt_template()` 改为先从远程获取，本地文件作为 fallback
- 保留本地文件作为离线降级方案

### 阶段三：闭环验证

- 在 Eval 平台修改提示词 → AGI 自动生效 → Eval 跑评测对比效果 → 确认后固化版本

---

## 4. OCR / 查询改写 / 多路召回

**现状：** 文档解析仅依赖 LlamaParse（云服务），无 OCR 能力。检索为单路向量召回（Milvus），无查询改写、无多路召回融合。

### OCR

- 集成 PaddleOCR 或 Surya，处理扫描件 PDF、图片中的文本
- 在文件上传流水线中增加 OCR 节点：

```
Upload → 格式检测 → 若为扫描件/图片 → OCR 提取 → 文本入库 → 向量化
```

- 支持表格 OCR（结构化输出为 Markdown 表格）

### 查询改写（Query Rewriting）

在 `ask_agent_service` 的检索前增加查询改写环节：

- **同义扩展**：LLM 生成 2-3 个语义等价的查询变体
- **HyDE**（Hypothetical Document Embedding）：LLM 生成假设性答案文档，用其 embedding 检索
- **意图识别**：区分事实查询、总结归纳、对比分析等类型，适配不同检索策略
- 实现为独立的 `QueryRewriteService`，可配置开关

### 多路召回（Multi-Route Retrieval）

| 路线 | 方法 | 说明 |
|------|------|------|
| 路线 1 | 向量语义召回 | Milvus（现有） |
| 路线 2 | 关键词召回 | BM25 / Elasticsearch |
| 路线 3 | 知识图谱召回 | GraphRAG（见第 5 点） |

- 召回结果融合：RRF（Reciprocal Rank Fusion）算法合并排序
- 实现 `MultiRouteRetriever`，各路线可独立开关，权重可配置

---

## 5. GraphRAG

**现状：** 不存在任何图谱相关代码。当前 RAG 完全依赖向量检索，缺乏实体关系和全局语义理解。

### 知识图谱构建

- 文档入库时，LLM 提取实体（人物、概念、事件）和关系三元组
- 存储选型：Neo4j 或直接用 Milvus 的标量字段 + 图结构表
- 增量更新：新文档入库时融合到现有图谱，处理实体消歧

### Graph 检索

- **社区检测**：对图谱做 Leiden 聚类，生成社区摘要
- **Local Search**：从查询实体出发，沿关系边扩展获取相关上下文
- **Global Search**：利用社区摘要进行全局语义检索
- 与向量召回结果融合（纳入多路召回体系）

### 技术选型

- 考虑使用 `nano-graphrag` 或 `graphrag`（微软）作为基础框架
- 图存储方案根据数据规模决定（小规模用 NetworkX 内存图，大规模用 Neo4j）

---

## 6. A2A（Agent-to-Agent Protocol）

**现状：** 当前多 Agent 协作是自定义的 `CoordinatorAgentService` + `delegate_task` 工具调用模式，Agent 间通过内部 Python 方法调用通信，无标准化协议。

### Agent Card 标准化

- 每个 Agent（Coordinator、AskAgent、NoteAgent）发布 `/.well-known/agent.json`
- 描述 Agent 能力、支持的输入/输出格式、认证要求

### A2A 通信层

- 实现 A2A Task 生命周期：`submitted → working → input-required → completed / failed`
- 支持流式响应（SSE）和推送通知（webhook）
- Agent 间通信从直接方法调用改为 HTTP / A2A Task 消息

### 收益

- Agent 可独立部署和扩缩容
- 支持跨语言 Agent（如 Java Agent 与 Python Agent 互调）
- 第三方 Agent 可通过标准协议接入
- 与 MCP 互补：MCP 管理工具/资源，A2A 管理 Agent 协作

---

## 7. MCP（Model Context Protocol）

**现状：** 不存在任何 MCP 相关代码。Agent 的工具（`search_files_tool`、`delegate_task` 等）是直接用 LangChain `@tool` 装饰器硬编码的。

### MCP Server 实现

- 将现有工具封装为 MCP Tools：

| 现有工具 | MCP Tool | 说明 |
|----------|----------|------|
| `search_files_tool` | `search_files` | 向量检索 |
| `delegate_task` | `delegate_task` | 任务委派 |
| （新增） | `read_document` | 读取文档内容 |
| （新增） | `list_project_files` | 列出项目文件 |
| （新增） | `get_mind_map` | 获取思维导图 |

- 将项目文档、对话历史封装为 MCP Resources
- 将提示词模板封装为 MCP Prompts

### MCP Client 集成

- `AgentService` 增加 MCP Client 能力，可发现和调用外部 MCP Server 提供的工具
- 支持动态工具发现：Agent 启动时从 MCP Server 拉取可用工具列表
- 替代现有的 `_load_tools()` 硬编码方式

### 扩展场景

- 接入外部 MCP Server（如浏览器搜索、代码执行沙箱、数据库查询）
- 前端可通过 MCP 协议直接查询 Agent 可用的工具和资源列表

---

## 建议实施顺序

```
第一阶段（基础设施）: 1 → 2 → 3
  提示词版本管理 → 开放 API → AGI 接入
  （形成提示词管理闭环，后续所有 Agent 改进都有评测基础）

第二阶段（检索增强）: 4
  OCR + 查询改写 + 多路召回
  （直接提升问答质量，用户感知最明显）

第三阶段（知识深度）: 5
  GraphRAG
  （依赖第二阶段的多路召回框架，作为新的召回路线接入）

第四阶段（架构升级）: 7 → 6
  MCP → A2A
  （标准化工具和协议，为多 Agent 扩展打基础）
```
