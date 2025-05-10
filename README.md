# 📚 Readify - 智能阅读笔记助手

<div align="center">
  <h3>基于AI的智能阅读笔记和思维导图生成工具</h3>
  
  ![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
  ![Java](https://img.shields.io/badge/Java-17-007396?style=for-the-badge&logo=java&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2.2-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
</div>

## 📋 项目概述

Readify是一个智能阅读笔记助手系统，通过AI技术帮助用户轻松整理知识并生成直观的思维导图。项目由三个部分组成：

- **Readify Frontend** - 基于Vue 3的用户界面
- **Readify Server** - 基于Spring Boot的后端服务
- **Readify AGI** - 基于Python FastAPI的智能服务底座

## 📸 功能展示

<div align="center">
  <img src="img/1-首页.png" alt="首页" width="80%">
  <p><i>首页 - 项目管理和文档上传</i></p>
  
  <img src="img/2-对话-1.png" alt="对话界面1" width="80%">
  <p><i>对话界面 - 智能问答</i></p>
  
  <img src="img/3-对话-2.png" alt="对话界面2" width="80%">
  <p><i>对话界面 - 实时交互</i></p>
  
  <img src="img/4-笔记.png" alt="笔记界面" width="80%">
  <p><i>笔记界面 - 笔记管理</i></p>
  
  <img src="img/5-笔记生成.png" alt="笔记生成" width="80%">
  <p><i>笔记生成 - 自动分析</i></p>
  
  <img src="img/6-笔记生成.png" alt="笔记生成结果" width="80%">
  <p><i>笔记生成 - 结果展示</i></p>
</div>

## ✨ 核心功能
- 🤖 **智能问答** - 自动分析文档内容，结合搜索引擎回答用户问题
- 📝 **智能笔记生成** - 自动分析文档内容，支持多层级展示构化笔记
- 🧠 **思维导图可视化** - 直观展示知识结构和关系
- 🤝 **多Agent协作** - 基于多智能体协作的复杂任务解决方案
- 💬 **多种AI模型支持** - 支持OpenAI、Qwen、DeepSeek等多种大语言模型
- 📄 **多格式文档支持** - 支持PDF、TXT、DOCX等多种文档格式
- 🔄 **实时交互反馈** - 思考过程实时展示，提供更好的用户体验

## 🛠️ 技术架构

```
readify_parent/
├── readify_frontend/    # 前端项目
├── readify_server/      # 后端服务
└── readify_agi/         # AI智能体底座
```

### Readify Frontend

- **技术栈**: Vue 3, TypeScript, Element Plus, Vite, markmap.js
- **功能**: 用户界面

### Readify Server

- **技术栈**: Java 17, Spring Boot 3.2.2, MyBatis-Plus, MySQL
- **功能**: 业务端代码实现

### Readify AGI

- **技术栈**: Python 3.9, FastAPI, LangChain, OpenAI
- **功能**: AI服务底座，多智能体协调, 文档分析, 知识提取, 思维导图生成

## 🚀 快速开始

### 前提条件

- Node.js 16+
- JDK 17+
- Python 3.9+
- MySQL 8.0+

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/xiaosl-cell/readify_parent.git
cd readify
```

2. **配置后端服务 (Readify Server)**
```bash
cd readify_server
# 修改数据库配置
vim src/main/resources/application.yml
# 修改以下配置项：
# - spring.datasource.url: 数据库连接地址
# - spring.datasource.username: 数据库用户名
# - spring.datasource.password: 数据库密码
# - jwt.secret: JWT密钥
# - readify.agi.base-url: AGI服务地址
```

3. **配置AGI服务 (Readify AGI)**
```bash
cd readify_agi
# 修改环境配置
copy .env.example .env
vim .env
# 修改相关api密钥和地址

cd /readify_server
# 修改数据库配置
vim src/main/resources/application.yml
# 修改数据库、agi服务等相关配置
```

4. **启动后端服务 (Readify Server)**
```bash
cd readify_server
./mvnw spring-boot:run
```

5. **启动AGI服务 (Readify AGI)**
```bash
cd readify_agi
pip install -r requirements.txt
python main.py
```

6. **启动前端应用 (Readify Frontend)**
```bash
cd readify_frontend
npm install
npm run dev
```

## 🧩 功能模块

### 前端模块

- **用户界面**: 登录注册、项目管理、文件上传
- **笔记系统**: 笔记查看、编辑和管理
- **思维导图**: 交互式知识图谱可视化
- **对话界面**: 与AI进行实时交互问答

### 后端模块

- **用户认证**: 基于JWT的用户认证和权限控制
- **项目管理**: 支持创建和管理多个读书项目
- **文件管理**: 上传、存储和处理文档文件
- **对话历史**: 记录和查询用户与AI的交互历史

### AGI模块

- **智能体协调**: 支持多智能体协作，动态分配任务
- **文档处理**: 文档解析、向量化和语义理解
- **知识问答**: 基于文档内容的智能问答和知识推理
- **笔记生成**: 自动生成和组织文档笔记

## 📡 接口文档

- Readify Server API: http://localhost:8080/swagger-ui.html
- Readify AGI API: http://localhost:8090/docs

## 📋 开发指南

### 代码风格

- 前端: 遵循ESLint和Vue风格指南
- 后端: 遵循Google Java风格指南
- AGI: 遵循PEP 8 Python风格指南

### 开发流程

1. 从主分支创建特性分支
2. 开发并测试新功能
3. 提交Pull Request进行代码审查
4. 合并到主分支

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
  <p>Made with ❤️ by Readify</p>
</div> 