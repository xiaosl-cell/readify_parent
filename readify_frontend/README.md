# 📚 Readify

<div align="center">
  <img src="public/readify-logo.png" alt="Readify Logo" width="180">
  <h3>智能阅读笔记助手</h3>
  <p>基于AI的智能阅读笔记和思维导图生成工具</p>
  
  ![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
  ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
  ![Element Plus](https://img.shields.io/badge/Element_Plus-409EFF?style=for-the-badge&logo=element&logoColor=white)
  ![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
</div>

## ✨ 功能特点

Readify是一个强大的阅读笔记助手，帮助用户轻松整理知识并生成直观的思维导图。

- 📝 **智能笔记生成** - 自动分析文档内容，生成结构化笔记
- 🧠 **思维导图可视化** - 直观展示知识结构和关系
- 💬 **多种AI模型支持** - 支持OpenAI、Qwen、DeepSeek等多种大语言模型
- 📄 **多格式文档支持** - 支持PDF、TXT、DOCX等多种文档格式
- 🔄 **实时交互反馈** - 思考过程实时展示，提供更好的用户体验
- 📱 **响应式设计** - 适配不同设备屏幕尺寸

## 🛠️ 技术栈

- **前端框架**: Vue 3, TypeScript
- **UI组件**: Element Plus
- **构建工具**: Vite
- **状态管理**: Vuex
- **路由管理**: Vue Router
- **HTTP客户端**: Axios
- **可视化**: D3.js, Markmap
- **Markdown处理**: Marked, Markdown-it

## 📋 前提条件

- Node.js 16.x 或更高版本
- NPM 7.x 或更高版本

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/readify.git
cd readify

# 安装依赖
npm install
```

### 运行开发服务器

```bash
npm run dev
```

服务将在 http://localhost:5173 运行

### 构建生产版本

```bash
npm run build
```

构建后的文件将生成在 `dist` 目录下

### 预览生产版本

```bash
npm run preview
```

## 🧩 项目结构

```
readify/
├── public/             # 静态资源
├── src/                # 源代码
│   ├── api/            # API请求
│   ├── assets/         # 资源文件
│   ├── components/     # 组件
│   ├── router/         # 路由配置
│   ├── store/          # Vuex状态管理
│   ├── types/          # TypeScript类型定义
│   ├── utils/          # 工具函数
│   ├── views/          # 页面视图
│   ├── App.vue         # 根组件
│   └── main.ts         # 入口文件
├── index.html          # HTML模板
├── package.json        # 项目依赖
├── tsconfig.json       # TypeScript配置
└── vite.config.ts      # Vite配置
```

## 📸 屏幕截图

<div align="center">
  <img src="public/screenshot-1.png" alt="主界面" width="80%">
  <p><i>Readify主界面</i></p>
  
  <img src="public/screenshot-2.png" alt="思维导图" width="80%">
  <p><i>思维导图视图</i></p>
</div>

## 🔧 配置

在 `.env` 文件中配置环境变量:

```
VITE_API_BASE_URL=http://your-api-url
```

## 📄 许可证

[MIT License](LICENSE)

## 🤝 贡献

欢迎贡献! 请查看 [贡献指南](CONTRIBUTING.md) 了解更多信息。

---

<div align="center">
  <p>Made with ❤️ by Your</p>
</div>
