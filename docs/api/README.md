# API Documentation

> Azure RAG Agent POC - REST API仕様書

**ステータス**: 🚧 開発予定（Day 23-24）  
**最終更新**: 2024-12-22

---

## 概要

このディレクトリには、FastAPI Web APIの仕様書が格納されます。

---

## 予定エンドポイント

### Chat Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/api/chat` | チャットメッセージ送信 | 🚧 Planned |
| POST | `/api/chat/stream` | ストリーミングチャット | 🚧 Planned |
| GET | `/api/chat/history/{thread_id}` | 会話履歴取得 | 🚧 Planned |

### Assistant Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/assistants/{assistant_id}` | Assistant情報取得 | 🚧 Planned |
| GET | `/api/assistants/{assistant_id}/tools` | 利用可能ツール一覧 | 🚧 Planned |

### Thread Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/api/threads` | スレッド作成 | 🚧 Planned |
| DELETE | `/api/threads/{thread_id}` | スレッド削除 | 🚧 Planned |

### Health Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| GET | `/api/health` | ヘルスチェック | 🚧 Planned |
| GET | `/api/health/azure` | Azure接続確認 | 🚧 Planned |

---

## API仕様フォーマット

Day 23-24実装時に、以下のフォーマットでドキュメントを作成予定：

- **OpenAPI Specification** (`openapi.yaml`)
- **Swagger UI** (自動生成)
- **Endpoint詳細** (`endpoints.md`)
- **認証ガイド** (`authentication.md`)

---

## Day 23-24実装計画

### Day 23: FastAPI基盤

1. **app/main.py**: FastAPIアプリケーション作成
2. **app/api/routes/**: エンドポイント実装
3. **app/models/**: Pydantic models定義
4. **Swagger UI**: 自動ドキュメント生成

### Day 24: ストリーミング & デプロイ

1. **Server-Sent Events**: ストリーミングエンドポイント
2. **認証**: Azure AD統合（オプション）
3. **Docker化**: Dockerfile + docker-compose.yml

---

## 関連ドキュメント

- [System Architecture](../../ARCHITECTURE.md)
- [Function Calling Guide](../guides/development/function-calling.md)
- [Deployment Guide](../guides/deployment/azure-resources.md)

---

**次回更新予定**: Day 23-24完了時
