# 📚 Readify Server

<div align="center">
  <h3>Readify智能读书助手的服务端引擎</h3>
  <p>基于领域驱动设计的智能读书助理后端服务</p>
  
  ![Java](https://img.shields.io/badge/Java-17-007396?style=for-the-badge&logo=java&logoColor=white)
  ![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2.2-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white)
  ![MyBatis](https://img.shields.io/badge/MyBatis_Plus-3.5.5-FF0000?style=for-the-badge&logo=mybatis&logoColor=white)
  ![MySQL](https://img.shields.io/badge/MySQL-8.3.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
</div>

## ✨ 功能特点

Readify Server 是一个基于Java Spring Boot的智能阅读助手后端服务，专注于提供强大的读书笔记管理功能和智能分析能力。

- 📚 **智能笔记管理** - 自动整理和组织阅读笔记，支持多种笔记类型
- 🧠 **思维导图生成** - 通过AI分析文本内容，自动生成结构化的思维导图
- 💬 **对话历史记录** - 保存用户与AI的交流历史，包含思考过程和上下文
- 🔄 **实时流式输出** - 通过WebSocket提供AI响应的实时流式输出
- 🛡️ **安全认证授权** - 完善的JWT认证和Spring Security保护
- 📄 **文件处理** - 支持多种文档格式的上传、解析和管理
- 👥 **多用户支持** - 完整的用户管理和项目隔离机制

## 🛠️ 技术栈

- **后端框架**: Spring Boot 3.2.2
- **持久化**: MyBatis-Plus 3.5.5, MySQL 8.3.0
- **安全认证**: Spring Security, JWT
- **API文档**: SpringDoc OpenAPI (Swagger)
- **实时通信**: WebSocket、SSE
- **对象映射**: MapStruct 1.5.5
- **构建工具**: Maven

## 📋 前提条件

- JDK 17 或更高版本
- MySQL 8.0+
- Maven 3.6+

## 🚀 快速开始

### 环境配置

1. 克隆仓库：

```bash
git clone https://github.com/your-organization/readify-server.git
cd readify-server
```

2. 配置数据库：

修改 `src/main/resources/application.yml` 文件中的数据库连接信息。

### 构建项目

使用Maven构建项目：

```bash
./mvnw clean package
```

### 启动服务

```bash
# Linux/Unix
./start.sh

# Windows
start.bat
```

服务默认在 `http://localhost:8080` 启动

## 🧩 项目结构

```
readify-server/
├── src/
│   ├── main/
│   │   ├── java/com/readify/server/
│   │   │   ├── config/                # 配置类
│   │   │   ├── domain/                # 领域模型和服务
│   │   │   │   ├── auth/              # 认证授权领域
│   │   │   │   ├── conversation/      # 会话管理领域
│   │   │   │   ├── file/              # 文件管理领域
│   │   │   │   ├── mind_map/          # 思维导图领域
│   │   │   │   ├── notetask/          # 笔记任务领域
│   │   │   │   ├── project/           # 项目管理领域
│   │   │   │   └── user/              # 用户管理领域
│   │   │   ├── infrastructure/        # 基础设施层
│   │   │   │   ├── common/            # 通用组件
│   │   │   │   ├── persistence/       # 持久化实现
│   │   │   │   ├── security/          # 安全相关实现
│   │   │   │   └── utils/             # 工具类
│   │   │   ├── interfaces/            # 接口层
│   │   │   │   ├── auth/              # 认证接口
│   │   │   │   ├── conversation/      # 会话接口
│   │   │   │   ├── file/              # 文件接口
│   │   │   │   ├── mind_map/          # 思维导图接口
│   │   │   │   ├── project/           # 项目接口
│   │   │   │   └── user/              # 用户接口
│   │   │   └── websocket/             # WebSocket实现
│   │   └── resources/                 # 配置文件和静态资源
│   └── test/                          # 测试代码
├── .mvn/                              # Maven包装器配置
├── pom.xml                            # Maven依赖配置
└── README.md                          # 项目文档
```

## 💻 开发指南

### 领域驱动设计

项目采用领域驱动设计(DDD)架构，组织结构如下：

- **领域层(Domain)**: 包含领域模型、领域服务和仓库接口
- **接口层(Interfaces)**: 负责处理外部请求和响应转换
- **基础设施层(Infrastructure)**: 提供技术实现和支持

### 实现笔记任务服务

创建一个笔记任务服务：

```java
@Service
@RequiredArgsConstructor
public class NoteTaskServiceImpl implements NoteTaskService {
    
    private final NoteTaskRepository noteTaskRepository;
    
    @Override
    public NoteTask createNoteTask(NoteTask noteTask) {
        noteTask.setStatus(NoteTaskStatus.CREATED.name());
        noteTask.setCreateTime(LocalDateTime.now());
        noteTask.setUpdateTime(LocalDateTime.now());
        return noteTaskRepository.save(noteTask);
    }
    
    @Override
    public Optional<NoteTask> getNoteTaskById(Long id) {
        return noteTaskRepository.findById(id);
    }
    
    // 其他实现...
}
```

### 实现WebSocket处理器

配置并使用WebSocket实现实时通信：

```java
@Component
@Slf4j
public class ReadifyWebSocketHandler extends TextWebSocketHandler {

    private final WebSocketSessionManager sessionManager;
    
    // 处理文本消息
    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        try {
            String payload = message.getPayload();
            // 处理消息逻辑
            
            // 发送响应
            session.sendMessage(new TextMessage("处理结果"));
        } catch (Exception e) {
            log.error("处理WebSocket消息时发生错误", e);
        }
    }
}
```

## 🔧 主要功能

- **用户认证授权**: 基于JWT令牌的用户认证和权限控制
- **项目管理**: 支持创建和管理多个读书项目
- **文件管理**: 上传、存储和处理文档文件
- **对话历史**: 记录和查询用户与AI的交互历史
- **思维导图**: 生成和管理文档内容的思维导图
- **笔记任务**: 处理和管理笔记生成任务
- **WebSocket通信**: 实现实时响应和状态更新

## 📡 API 接口

访问 `http://localhost:8080/swagger-ui.html` 查看完整的API文档

## 🤝 贡献指南

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 📄 许可证

## RBAC

- Tables: `sys_role`, `sys_permission`, `sys_user_role`, `sys_role_permission`.
- Default role: `ROLE_USER` (assigned after user registration).
- Admin role: `ROLE_ADMIN` (seeded with all permissions).
- Permission examples: `PROJECT:READ`, `PROJECT:WRITE`, `FILE:READ`, `FILE:WRITE`, `MIND_MAP:READ`, `MIND_MAP:WRITE`, `CONVERSATION:READ`, `API_KEY:MANAGE`, `USER:READ`, `USER:WRITE`.
- Method-level authorization uses `@PreAuthorize`.

[MIT License](LICENSE)

---

<div align="center">
  <p>Made with ❤️ by Readify</p>
</div> 
