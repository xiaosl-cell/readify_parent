# Readify - AI-Powered Reading & Note Assistant

<div align="center">

[中文](README_zh.md) | [日本語](README_ja.md)

  ![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
  ![Java](https://img.shields.io/badge/Java-17-007396?style=for-the-badge&logo=java&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2.2-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)

  <h3>AI-driven intelligent reading notes and mind map generation</h3>
</div>

## Overview

Readify is an AI-powered reading assistant that helps users organize knowledge and generate intuitive mind maps. It follows a microservices architecture with five core modules:

- **readify_frontend** — Vue 3 + TypeScript user-facing application
- **readify_server** — Spring Boot 3.2.2 backend (DDD architecture)
- **readify_agi** — FastAPI AI agent layer (multi-agent system)
- **readify_admin** — Vue 3 + TypeScript admin panel (RBAC)
- **readify_eval** — Evaluation platform (backend + frontend)

## Screenshots

<div align="center">
  <img src="img/1-首页.png" alt="Home" width="80%">
  <p><i>Home — Project management and document upload</i></p>

  <img src="img/2-对话-1.png" alt="Chat 1" width="80%">
  <p><i>Chat — Thought process</i></p>

  <img src="img/3-对话-2.png" alt="Chat 2" width="80%">
  <p><i>Chat — Final answer</i></p>

  <img src="img/4-笔记.png" alt="Notes" width="80%">
  <p><i>Notes — Note management</i></p>

  <img src="img/5-笔记生成.png" alt="Note generation" width="80%">
  <p><i>Note generation — Auto analysis</i></p>

  <img src="img/6-笔记生成.png" alt="Note result" width="80%">
  <p><i>Note generation — Result</i></p>
</div>

## Features

- **Intelligent Q&A** — RAG-based document Q&A with vector search and LLM
- **Smart Note Generation** — Multi-level structured note generation
- **Mind Map Visualization** — Interactive knowledge graph via markmap.js
- **Multi-Agent Collaboration** — Coordinator, Ask, and Note agents
- **Multiple LLM Support** — OpenAI, Qwen, DeepSeek, and other OpenAI-compatible models
- **Multi-format Document Support** — PDF, TXT, DOCX via LlamaParse
- **Real-time Streaming** — Thought process streamed via WebSocket/SSE

## Architecture

```
readify_parent/
├── readify_frontend/    # Vue 3 frontend
├── readify_server/      # Spring Boot backend
├── readify_agi/         # FastAPI AI agent service
├── readify_admin/       # Vue 3 admin panel
├── readify_eval/        # Evaluation platform
└── infra/               # Infrastructure (Docker Compose)
```

### Service Communication

```
Frontend (5173) → Server (8080) → AGI (8081)
                      ↕                ↕
                  Nacos (8848) — Service discovery & config
                      ↓
                  MySQL — Shared business database
                  Milvus — Vector database
                  MinIO — Object storage
```

### Tech Stack

| Module | Stack |
|--------|-------|
| **Frontend** | Vue 3, TypeScript, Element Plus, Vite, markmap.js |
| **Server** | Java 17, Spring Boot 3.2.2, MyBatis-Plus, Spring Cloud |
| **AGI** | Python 3.9+, FastAPI, LangChain, OpenAI SDK |
| **Database** | MySQL 8.0+ (business data), Milvus (vector store) |
| **Storage** | MinIO |
| **Service Discovery** | Nacos 2.x |

## Quick Start

### Prerequisites

**Docker (recommended)**
- Docker >= 20.10
- Docker Compose >= 2.0

**Local development**
- Node.js 16+, JDK 17+, Python 3.9+, MySQL 8.0+

### 1. Start Infrastructure

```bash
docker compose -f infra/docker-compose.yml up -d
```

Starts: Nacos (8848), MySQL (3307), Milvus (19530), MinIO (9000/9001).

### 2. Initialize Database

```bash
mysql -h 127.0.0.1 -P 3307 -u root -proot -e "CREATE DATABASE IF NOT EXISTS readify DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot readify < readify_server/src/main/resources/db/migration/db.sql

mysql -h 127.0.0.1 -P 3307 -u root -proot -e "CREATE DATABASE IF NOT EXISTS readify_eval DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot readify_eval < readify_eval/sql/readify_eval_flow.sql
```

### 3. Configure AGI Service

```bash
cd readify_agi
cp .env.example .env
vim .env
```

Key variables:
```env
LLM_API_KEY=your_key
LLM_API_BASE=http://your-openai-compatible-endpoint/v1
LLM_MODEL_NAME=your_model
EMBEDDING_API_KEY=your_embedding_key
EMBEDDING_API_BASE=your_embedding_url
EMBEDDING_MODEL=your_embedding_model
LLAMA_PARSE_API_KEY=your_llamaparse_key   # or set PARSER_PROVIDER=local
NACOS_NAMESPACE=ca5b6af9-5336-42f7-b68c-515779f79a98
```

### 4. Configure Nacos

Add the following Data IDs to Nacos (namespace: same as `NACOS_NAMESPACE`, group: `READIFY`):

- `readify-server.yaml` — DB connection, JWT secret, MinIO endpoint
- `readify-agi.yaml` — DB, Milvus, MinIO, LLM, Embedding config
- `readify-eval.yaml` — Eval DB connection, CORS

> See the [Chinese README](README_zh.md#nacos-配置文件) for full Nacos config examples.

### 5. Start Application Services

```bash
# Build and start all application services
docker compose up -d --build

# View logs
docker compose logs -f
docker compose logs -f readify-server
```

### 6. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Admin Panel | http://localhost:5174 |
| Eval Platform | http://localhost:5175 |
| Server Swagger | http://localhost:8080/swagger-ui.html |
| AGI OpenAPI | http://localhost:8081/docs |
| Eval OpenAPI | http://localhost:8082/docs |
| Nacos Console | http://localhost:8848/nacos (nacos/nacos) |
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin) |

## Development Commands

### Frontend
```bash
npm install && npm run dev      # port 5173
npm run build
```

### Backend
```bash
./mvnw spring-boot:run          # port 8080
./mvnw test
```

### AGI Service
```bash
pip install -r requirements.txt
python main.py                  # port 8081
pytest tests/
```

### Eval Backend
```bash
cd readify_eval/backend
pip install -r requirements.txt
alembic upgrade head
python run.py                   # port 8082
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[MIT License](LICENSE)

---

<div align="center">
  <p>Made with ❤️ by Readify</p>
</div>
