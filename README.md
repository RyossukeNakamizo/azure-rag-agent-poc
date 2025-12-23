# Azure RAG Agent POC

Azure AI Foundry + Azure OpenAI による RAG (Retrieval-Augmented Generation) システムの PoC 実装

## 🎯 実装状況

### ✅ Phase 1: Chat Completions API（完了）

- **FastAPI サーバー**: 完全稼働
- **Azure OpenAI 統合**: 直接統合（Managed Identity 認証）
- **Chat API**: ストリーミング・非ストリーミング両対応
- **エンドポイント**: Health, Tools, Chat

### 🚧 Phase 2: RAG System（進行中）

#### ✅ Phase 2-1: Azure AI Search Infrastructure（完了）
- **Bicep デプロイ**: 成功（2024-12-23）
- **Search Service**: search-ragpoc-dev-ldt4idhueffoe (Basic SKU)
- **RBAC**: User (Contributor) + OpenAI MI (Reader) 設定済み
- **既存インデックス**: 2つ検出（rag-docs-index, rag-index）
- **認証**: Managed Identity（キーレス）

#### ✅ Phase 2-2: Python SDK Integration（完了）
- **SDK**: azure-search-documents 11.6.0b7
- **SearchService**: ハイブリッド検索（Vector + Keyword）実装
- **認証**: Managed Identity（DefaultAzureCredential）
- **テスト**: キーワード検索・ハイブリッド検索 両方成功
- **インデックス**: rag-docs-index（既存、6フィールド）

#### 🔜 Phase 2-3: RAG API Endpoints（次回）
- `/api/v1/rag/search` エンドポイント実装
- `/api/v1/rag/chat` エンドポイント実装
- FastAPI 統合
- セマンティックランキング

---

## 🚀 Quick Start

### 前提条件

- Python 3.13+
- Azure サブスクリプション
- Azure OpenAI リソース（gpt-4o デプロイ済み）
- Azure CLI ログイン済み

### インストール
```bash
# リポジトリクローン
git clone https://github.com/your-repo/azure-rag-agent-poc.git
cd azure-rag-agent-poc

# 仮想環境作成
python3 -m venv .venv
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env を編集して Azure OpenAI 情報を設定
```

### 起動
```bash
# 環境変数読み込み
set -a
source .env
set +a

# サーバー起動
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### テスト
```bash
# Health Check
curl http://127.0.0.1:8000/api/health

# Chat（非ストリーミング）
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Hello","stream":false}'

# Chat（ストリーミング）
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Count to 5","stream":true}'
```

### Swagger UI

http://127.0.0.1:8000/docs

---

## 🏗️ アーキテクチャ
```
┌─────────────────────────────────────────────────┐
│                 FastAPI Server                  │
│  ┌──────────────────────────────────────────┐   │
│  │         API Routes                       │   │
│  │  /api/health  /api/tools  /api/chat     │   │
│  └──────────────┬───────────────────────────┘   │
│                 │                               │
│  ┌──────────────▼───────────────────────────┐   │
│  │      FoundryAgentService                 │   │
│  │  ┌────────────────────────────────────┐  │   │
│  │  │   Azure OpenAI Client (openai SDK) │  │   │
│  │  │   - Managed Identity 認証          │  │   │
│  │  │   - Chat Completions API           │  │   │
│  │  └────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│            Azure OpenAI Service                 │
│  Endpoint: oai-ragpoc-dev-ldt4idhueffoe        │
│  Deployment: gpt-4o (2024-08-06)               │
│  Authentication: Azure AD                       │
└─────────────────────────────────────────────────┘
```

---

## 📦 技術スタック

| カテゴリ | 技術 | バージョン |
|---------|------|-----------|
| **API Framework** | FastAPI | 0.125.0 |
| **Azure OpenAI** | openai | 2.13.0 |
| **認証** | azure-identity | 1.25.1 |
| **設定管理** | pydantic-settings | 2.12.5 |
| **ASGI Server** | uvicorn | 0.38.0 |

---

## 🔐 セキュリティ

- **認証方式**: Azure AD Managed Identity（キーレス）
- **API Key**: 不使用
- **RBAC**: Cognitive Services OpenAI User ロール
- **TLS**: HTTPS 通信（Azure 標準）
- **Azure AI Search** | azure-search-documents | 11.6.0b7 |
---

## 📊 パフォーマンス

| メトリクス | 目標 | 実測値 | 状態 |
|----------|------|--------|------|
| Latency (P50) | < 1s | ~500ms | ✅ |
| Latency (P95) | < 3s | ~1.2s | ✅ |
| Throughput | 10 req/s | 未測定 | - |
| Error Rate | < 1% | 0% | ✅ |

---

## 📝 判断ログ

実装における重要な技術選定の記録:

- [DECISIONS.md](DECISIONS.md) - 採用した技術の判断理由
- [TRADEOFFS.md](TRADEOFFS.md) - 却下した選択肢の分析
- [ARCHITECTURE.md](ARCHITECTURE.md) - システム設計思想

---

## 🐛 トラブルシューティング

### エラー: "Application startup failed"
```bash
# Azure CLI ログイン確認
az account show

# 環境変数確認
echo $AZURE_OPENAI_ENDPOINT
```

### エラー: "Port 8000 already in use"
```bash
# プロセス停止
lsof -ti:8000 | xargs kill -9
```

---

## 📚 参考資料

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Identity SDK](https://learn.microsoft.com/en-us/python/api/azure-identity/)

---

## 📄 ライセンス

MIT License
