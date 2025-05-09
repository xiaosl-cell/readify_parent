# Readify WebSocket API 文档

## 概述

Readify WebSocket API 提供了实时通信功能，允许客户端与服务器建立持久连接，实现双向通信。通过 WebSocket，客户端可以接收服务器推送的消息，也可以向服务器发送消息。

## 连接信息

### WebSocket 端点

- **URL**: `ws://localhost:8080/api/v1/ws/readify`
- **协议**: `ws`, `wss`(安全连接)

### 认证

所有 WebSocket 连接都需要通过 JWT 令牌进行认证。令牌应作为 URL 查询参数 `token` 提供：

```
ws://localhost:8080/api/v1/ws/readify?token=your-jwt-token
```

## 消息格式

所有通过 WebSocket 传输的消息都使用 JSON 格式，并遵循以下结构：

```json
{
  "type": "消息类型",
  "data": 消息数据,
  "timestamp": 时间戳
}
```

- **type**: 字符串，表示消息的类型
- **data**: 任意类型，包含消息的具体内容
- **timestamp**: 长整型，表示消息创建的时间戳

## 消息类型

### 系统消息

#### 连接成功

当客户端成功连接到 WebSocket 服务器时，服务器会发送一条连接成功消息：

```json
{
  "type": "connected",
  "data": "Connection established successfully for user {userId}",
  "timestamp": 1740727657000
}
```

#### 错误消息

当发生错误时，服务器会发送一条错误消息：

```json
{
  "type": "error",
  "data": "错误信息",
  "timestamp": 1740727657000
}
```

### 客户端消息

#### Ping 消息

客户端可以发送 ping 消息来检查连接状态：

```json
{
  "type": "ping",
  "data": "任意数据",
  "timestamp": 1740727657000
}
```

服务器会响应一条 pong 消息：

```json
{
  "type": "pong",
  "data": "Server is alive",
  "timestamp": 1740727657000
}
```

#### 广播消息

客户端可以发送广播消息，服务器会将消息转发给所有连接的客户端：

```json
{
  "type": "broadcast",
  "data": "要广播的消息内容",
  "timestamp": 1740727657000
}
```

服务器会将消息转发给所有客户端，并添加发送者信息：

```json
{
  "type": "broadcast",
  "data": "Message from user {userId}: 要广播的消息内容",
  "timestamp": 1740727657000
}
```

#### 查询项目文件

客户端可以发送查询项目文件的消息：

```json
{
  "type": "queryProjectFiles",
  "data": {
    "projectId": "项目ID"
  },
  "timestamp": 1740727657000
}
```

服务器会响应一条包含项目文件列表的消息：

```json
{
  "type": "projectFiles",
  "data": {
    "projectId": "项目ID",
    "files": [
      {
        "name": "文件名",
        "path": "文件路径",
        "type": "文件类型",
        "size": 文件大小,
        "lastModified": 最后修改时间
      }
      // 更多文件...
    ]
  },
  "timestamp": 1740727657000
}
```

#### 发送消息到Agent

客户端可以发送查询消息给Agent，服务器会将消息转发给Agent服务，并通过流式响应返回结果：

```json
{
  "type": "sendMessage",
  "data": {
    "query": "查询内容",
    "projectId": "项目ID",
    "taskType": "任务模式",
    "vendor": "厂商",
    "mindMapId": "思维导图ID（可选）"
  },
  "timestamp": 1740727657000
}
```

服务器会向Agent服务发起请求，并通过WebSocket将流式响应返回给客户端：

```json
{
  "type": "agentMessage",
  "data": "Agent响应内容片段",
  "timestamp": 1740727657000
}
```

当Agent响应流结束时，服务器会发送一条完成消息：

```json
{
  "type": "agentComplete",
  "data": {
    "type": "[DONE]",
    "project_id": "项目ID"
  },
  "timestamp": 1740727657000
}
```

## 错误处理

### 常见错误

1. **认证失败**：如果提供的 token 无效或已过期，连接将被拒绝
2. **消息格式错误**：如果消息不符合预期格式，服务器将返回错误消息
3. **未知消息类型**：如果消息类型不受支持，服务器将返回错误消息

### 错误响应示例

```json
{
  "type": "error",
  "data": "Invalid message data format",
  "timestamp": 1740727657000
}
```

```json
{
  "type": "error",
  "data": "Unknown message type: invalidType",
  "timestamp": 1740727657000
}
```

## 连接生命周期

1. **建立连接**：客户端通过提供有效的 JWT 令牌连接到 WebSocket 端点
2. **认证**：服务器验证令牌并提取用户 ID
3. **连接成功**：服务器发送连接成功消息
4. **消息交换**：客户端和服务器可以自由交换消息
5. **连接关闭**：客户端断开连接或服务器关闭连接

## 客户端示例代码

### JavaScript

```javascript
// 建立连接
const token = "your-jwt-token";
const socket = new WebSocket(`ws://localhost:8080/api/v1/ws/readify?token=${token}`);

// 连接打开时的处理
socket.onopen = function(event) {
  console.log("WebSocket连接已建立");
  
  // 发送ping消息
  const pingMessage = {
    type: "ping",
    data: "Hello server",
    timestamp: Date.now()
  };
  socket.send(JSON.stringify(pingMessage));
};

// 接收消息的处理
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log("收到消息:", message);
  
  // 根据消息类型处理
  switch(message.type) {
    case "pong":
      console.log("服务器活跃中");
      break;
    case "error":
      console.error("错误:", message.data);
      break;
    case "projectFiles":
      console.log("项目文件:", message.data.files);
      break;
    case "agentMessage":
      console.log("Agent响应:", message.data);
      break;
    case "agentComplete":
      console.log("Agent响应完成");
      // 检查完成类型
      if (typeof message.data === 'object' && message.data.type === '[DONE]') {
        console.log("收到项目ID:", message.data.project_id);
      }
      break;
    // 处理其他消息类型...
  }
};

// 连接关闭时的处理
socket.onclose = function(event) {
  console.log("WebSocket连接已关闭:", event.code, event.reason);
};

// 连接错误时的处理
socket.onerror = function(error) {
  console.error("WebSocket错误:", error);
};

// 查询项目文件
function queryProjectFiles(projectId) {
  const message = {
    type: "queryProjectFiles",
    data: {
      projectId: projectId
    },
    timestamp: Date.now()
  };
  socket.send(JSON.stringify(message));
}

// 发送广播消息
function broadcastMessage(content) {
  const message = {
    type: "broadcast",
    data: content,
    timestamp: Date.now()
  };
  socket.send(JSON.stringify(message));
}

// 发送消息到Agent
function sendMessageToAgent(query, projectId, taskType, vendor, mindMapId) {
  const message = {
    type: "sendMessage",
    data: {
      query: query,
      projectId: projectId,
      taskType: taskType,
      vendor: vendor,
      mindMapId: mindMapId // 可选参数，思维导图ID
    },
    timestamp: Date.now()
  };
  socket.send(JSON.stringify(message));
}

// 关闭连接
function closeConnection() {
  socket.close();
}
```

## 安全考虑

1. **令牌验证**：所有连接都需要有效的 JWT 令牌
2. **消息验证**：服务器会验证消息格式和内容
3. **用户权限**：某些操作可能需要特定的用户权限
4. **连接限制**：服务器可能限制单个用户的连接数量

## 最佳实践

1. **保持连接活跃**：定期发送 ping 消息以保持连接
2. **错误处理**：妥善处理连接错误和消息错误
3. **重连机制**：实现自动重连机制以处理连接断开
4. **消息队列**：在连接断开期间，将消息存储在队列中，连接恢复后再发送

## 扩展功能

未来可能添加的功能：

1. **私聊消息**：允许用户之间发送私聊消息
2. **消息历史**：提供消息历史记录查询
3. **在线状态**：提供用户在线状态通知
4. **消息确认**：提供消息送达确认机制

## 技术支持

如有任何问题或需要帮助，请联系技术支持团队：

- 邮箱：support@readify.com
- 文档：https://docs.readify.com/websocket-api

## 实现细节

### 服务端处理流程

Readify WebSocket 服务使用 Spring WebSocket 框架实现，主要组件包括：

1. **ReadifyWebSocketHandler**：处理 WebSocket 连接和消息
2. **WebSocketAuthInterceptor**：处理连接认证
3. **WebSocketSessionManager**：管理 WebSocket 会话
4. **WebSocketMessageHandlerManager**：管理不同类型的消息处理器

消息处理采用策略模式，每种消息类型对应一个专门的处理器：

- **PingMessageHandler**：处理 ping 消息
- **BroadcastMessageHandler**：处理广播消息
- **QueryProjectFilesHandler**：处理查询项目文件消息
- **SendMessageHandler**：处理向Agent发送消息并接收流式响应

### 消息处理流程

1. 客户端发送消息到服务器
2. `ReadifyWebSocketHandler` 接收并解析消息
3. `WebSocketMessageHandlerManager` 根据消息类型找到对应的处理器
4. 处理器处理消息并生成响应
5. `WebSocketSessionManager` 将响应发送回客户端

### 连接管理

`WebSocketSessionManager` 负责管理所有活跃的 WebSocket 连接，提供以下功能：

- 添加和移除会话
- 发送消息给指定会话
- 广播消息给所有会话
- 获取在线用户列表
- 检查用户是否在线

## 版本历史

### v1.1.0 (2025-03-06)
- 添加了发送消息到Agent的功能
- 支持Agent流式响应处理

### v1.0.0 (2025-02-28)

- 初始版本
- 支持基本的连接管理
- 支持 ping/pong 消息
- 支持广播消息
- 支持查询项目文件 