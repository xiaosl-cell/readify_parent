# Readify - AIを活用したリーディング＆ノートアシスタント

<div align="center">

[English](README.md) | [中文](README_zh.md)

  ![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
  ![Java](https://img.shields.io/badge/Java-17-007396?style=for-the-badge&logo=java&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3.9-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.2.2-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0+-009688?style=for-the-badge&logo=fastapi&logoColor=white)

  <h3>AIによるインテリジェントな読書ノートおよびマインドマップ生成ツール</h3>
</div>

## 概要

Readifyは、AIを活用してユーザーが知識を整理し、直感的なマインドマップを生成できるインテリジェントな読書アシスタントです。マイクロサービスアーキテクチャを採用し、5つのコアモジュールで構成されています。

- **readify_frontend** — Vue 3 + TypeScript ユーザー向けアプリ
- **readify_server** — Spring Boot 3.2.2 バックエンド（DDDアーキテクチャ）
- **readify_agi** — FastAPI AIエージェント層（マルチエージェントシステム）
- **readify_admin** — Vue 3 + TypeScript 管理パネル（RBAC）
- **readify_eval** — 評価プラットフォーム（バックエンド＋フロントエンド）

## スクリーンショット

<div align="center">
  <img src="img/1-首页.png" alt="ホーム" width="80%">
  <p><i>ホーム — プロジェクト管理とドキュメントアップロード</i></p>

  <img src="img/2-对话-1.png" alt="チャット1" width="80%">
  <p><i>チャット — 思考プロセス</i></p>

  <img src="img/3-对话-2.png" alt="チャット2" width="80%">
  <p><i>チャット — 最終回答</i></p>

  <img src="img/4-笔记.png" alt="ノート" width="80%">
  <p><i>ノート — ノート管理</i></p>

  <img src="img/5-笔记生成.png" alt="ノート生成" width="80%">
  <p><i>ノート生成 — 自動分析</i></p>

  <img src="img/6-笔记生成.png" alt="ノート結果" width="80%">
  <p><i>ノート生成 — 結果表示</i></p>
</div>

## 主な機能

- **インテリジェントQ&A** — ベクター検索とLLMを組み合わせたRAGベースのドキュメントQ&A
- **スマートノート生成** — 多階層の構造化ノート自動生成
- **マインドマップ可視化** — markmap.jsによるインタラクティブな知識グラフ
- **マルチエージェント協調** — Coordinator、Ask、Noteエージェントの連携
- **複数LLM対応** — OpenAI、Qwen、DeepSeekなどOpenAI互換モデルをサポート
- **マルチフォーマット対応** — PDF、TXT、DOCXなど（LlamaParse経由）
- **リアルタイムストリーミング** — WebSocket/SSEで思考プロセスをリアルタイム表示

## アーキテクチャ

```
readify_parent/
├── readify_frontend/    # Vue 3 フロントエンド
├── readify_server/      # Spring Boot バックエンド
├── readify_agi/         # FastAPI AIエージェントサービス
├── readify_admin/       # Vue 3 管理パネル
├── readify_eval/        # 評価プラットフォーム
└── infra/               # インフラ（Docker Compose）
```

### サービス通信

```
フロントエンド (5173) → サーバー (8080) → AGI (8081)
                             ↕                ↕
                         Nacos (8848) — サービス検出＆設定
                             ↓
                         MySQL — 共有ビジネスDB
                         Milvus — ベクターDB
                         MinIO — オブジェクトストレージ
```

### 技術スタック

| モジュール | スタック |
|-----------|---------|
| **Frontend** | Vue 3, TypeScript, Element Plus, Vite, markmap.js |
| **Server** | Java 17, Spring Boot 3.2.2, MyBatis-Plus, Spring Cloud |
| **AGI** | Python 3.9+, FastAPI, LangChain, OpenAI SDK |
| **データベース** | MySQL 8.0+（業務データ）、Milvus（ベクターストア） |
| **ストレージ** | MinIO |
| **サービス検出** | Nacos 2.x |

## クイックスタート

### 前提条件

**Docker（推奨）**
- Docker >= 20.10
- Docker Compose >= 2.0

**ローカル開発**
- Node.js 16+、JDK 17+、Python 3.9+、MySQL 8.0+

### 1. インフラ起動

```bash
docker compose -f infra/docker-compose.yml up -d
```

起動サービス：Nacos (8848)、MySQL (3307)、Milvus (19530)、MinIO (9000/9001)。

### 2. データベース初期化

```bash
mysql -h 127.0.0.1 -P 3307 -u root -proot -e "CREATE DATABASE IF NOT EXISTS readify DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot readify < readify_server/src/main/resources/db/migration/db.sql

mysql -h 127.0.0.1 -P 3307 -u root -proot -e "CREATE DATABASE IF NOT EXISTS readify_eval DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -h 127.0.0.1 -P 3307 -u root -proot readify_eval < readify_eval/sql/readify_eval_flow.sql
```

### 3. AGIサービスの設定

```bash
cd readify_agi
cp .env.example .env
vim .env
```

主要な設定：
```env
LLM_API_KEY=your_key
LLM_API_BASE=http://your-openai-compatible-endpoint/v1
LLM_MODEL_NAME=your_model
EMBEDDING_API_KEY=your_embedding_key
EMBEDDING_API_BASE=your_embedding_url
EMBEDDING_MODEL=your_embedding_model
LLAMA_PARSE_API_KEY=your_llamaparse_key   # またはPARSER_PROVIDER=localを設定
NACOS_NAMESPACE=ca5b6af9-5336-42f7-b68c-515779f79a98
```

### 4. Nacos設定

Nacosに以下のData IDを追加（namespace: `NACOS_NAMESPACE`と同じ、group: `READIFY`）：
- `readify-server.yaml` — DB接続、JWTシークレット、MinIOエンドポイント
- `readify-agi.yaml` — DB、Milvus、MinIO、LLM、Embedding設定
- `readify-eval.yaml` — 評価DB接続、CORS

詳細な設定例は[中文README](README_zh.md)を参照してください。

### 5. アプリケーションサービス起動

```bash
docker compose up -d --build
docker compose logs -f
```

### 6. アクセス

| サービス | URL |
|---------|-----|
| フロントエンド | http://localhost:5173 |
| 管理パネル | http://localhost:5174 |
| 評価プラットフォーム | http://localhost:5175 |
| Server Swagger | http://localhost:8080/swagger-ui.html |
| AGI OpenAPI | http://localhost:8081/docs |
| Eval OpenAPI | http://localhost:8082/docs |
| Nacosコンソール | http://localhost:8848/nacos (nacos/nacos) |
| MinIOコンソール | http://localhost:9001 (minioadmin/minioadmin) |

## 開発コマンド

### フロントエンド
```bash
npm install && npm run dev      # ポート 5173
npm run build
```

### バックエンド
```bash
./mvnw spring-boot:run          # ポート 8080
./mvnw test
```

### AGIサービス
```bash
pip install -r requirements.txt
python main.py                  # ポート 8081
pytest tests/
```

### 評価バックエンド
```bash
cd readify_eval/backend
pip install -r requirements.txt
alembic upgrade head
python run.py                   # ポート 8082
```

## コントリビューション

1. リポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

[MIT License](LICENSE)

---

<div align="center">
  <p>Made with ❤️ by Readify</p>
</div>
