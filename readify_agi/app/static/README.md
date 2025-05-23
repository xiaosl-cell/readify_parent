# Agent Stream API 测试页面

## 功能介绍

这是一个用于测试 `/api/v1/agent/stream` 接口的HTML测试页面。该页面提供了一个简单的表单界面，可以发送请求到流式API并实时显示响应结果。

## 使用方法

1. 启动Readify AGI服务器 (默认在 8090 端口)
2. 访问 http://localhost:8090/static/test_stream.html
3. 在表单中填写测试参数：
   - **工程ID**: 输入需要测试的工程ID
   - **模型厂商**: 选择使用的AI模型厂商 (OpenAI或Anthropic)
   - **任务类型**: 选择任务类型 (ask或note)
   - **上下文**: 输入额外的上下文信息 (JSON格式)
   - **用户问题**: 输入需要测试的用户查询内容
4. 点击"发送请求"按钮开始测试
5. 实时响应将显示在下方的响应区域

## 响应说明

不同类型的消息会以不同的颜色显示：
- **用户消息**: 蓝色背景
- **系统消息**: 红色背景
- **思考过程**: 黄色背景，斜体
- **AI回答**: 绿色背景

## 注意事项

- 确保API服务正常运行
- 上下文必须是有效的JSON格式
- 工程ID和用户问题是必填项 