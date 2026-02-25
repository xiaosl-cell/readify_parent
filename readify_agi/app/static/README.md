# AGI Static 目录说明

`readify_agi/app/static/` 当前仅用于放置静态资源与说明文档。

## 当前状态

- 目录中目前没有 `test_stream.html` 测试页面文件。
- 若需要验证流式接口，请使用以下方式：
  - Swagger: `http://localhost:8081/docs`
  - 直接调用: `GET /api/v1/agent/stream`（SSE）

## 备注

如后续恢复前端测试页，请在本目录补充页面文件，并同步更新本 README。
