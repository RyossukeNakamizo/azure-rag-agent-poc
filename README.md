# Azure RAG Agent POC

> 工場向けAzure AI Foundry RAG/Agentシステムの実証実験プロジェクト

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Azure AI](https://img.shields.io/badge/Azure-AI%20Foundry-0078D4.svg)](https://azure.microsoft.com/products/ai-services/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 プロジェクト概要

日野コンピューターシステム株式会社の工場向けWebアプリケーション開発プロジェクト。Azure AI Foundryを活用したRAG（Retrieval-Augmented Generation）およびAgent機能を実装し、工場運用の効率化を目指します。

### 主要機能

- 🔍 **Hybrid Search RAG**: Azure AI Search（ベクトル＋キーワード検索）
- 🤖 **AI Agent**: Azure AI Foundry Assistants API + Function Calling
- 📊 **工場データ分析**: 設備状態監視、データ分析ツール統合
- 🌐 **Web API**: FastAPI による REST API（開発予定）

---

## 🏗️ システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        Azure Cloud                          │
│                                                             │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐   │
│  │ FastAPI  │───▶│ AI Foundry  │───▶│ Azure AI Search  │   │
│  │ Web App  │    │ Assistant   │    │ (Hybrid Search)  │   │
│  └──────────┘    └──────┬──────┘    └──────────────────┘   │
│                         │                                   │
│                         ▼                                   │
│                  ┌──────────────┐                           │
│                  │ Azure OpenAI │                           │
│                  │ (GPT-4o)     │                           │
│                  └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

詳細は [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) を参照。

---

## 🚀 クイックスタート

### 前提条件

- Python 3.11+
- Azure サブスクリプション
- Azure CLI
- Git

### セットアップ

```bash
# リポジトリクローン
git clone https://github.com/your-org/azure-rag-agent-poc.git
cd azure-rag-agent-poc

# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env を編集してAzure認証情報を設定
```

### Azure リソースのデプロイ

```bash
# Azureログイン
az login

# リソースグループ作成
az group create --name rg-rag-poc --location japaneast

# Bicepデプロイ（予定）
az deployment group create \
  --resource-group rg-rag-poc \
  --template-file infra/main.bicep
```

### ローカル実行

```bash
# RAGパイプラインテスト
python -m pytest tests/test_rag_pipeline.py -v

# Function Callingテスト
python -m pytest tests/test_function_calling.py -v

# Web API起動（Day 23-24実装予定）
uvicorn app.main:app --reload
```

---

## 📚 ドキュメント

### 開発ガイド
- [Function Calling実装ガイド](docs/guides/FUNCTION_CALLING.md)
- [Azure AI Foundryセットアップ](docs/setup/DAY15_AI_FOUNDRY_SETUP.md)

### アーキテクチャ設計
- [システムアーキテクチャ](docs/architecture/ARCHITECTURE.md)
- [技術選定の判断履歴](docs/architecture/DECISIONS.md)
- [トレードオフ分析](docs/architecture/TRADEOFFS.md)

### 作業記録
- [セッションサマリー一覧](docs/sessions/)
  - [Day 15: AI Foundry初期セットアップ](docs/sessions/SESSION_SUMMARY_DAY15.md)
  - [Day 17-18: Function Calling実装](docs/sessions/SESSION_SUMMARY_DAY17-18.md)

---

## 🧪 テスト

```bash
# 全テスト実行
pytest

# カバレッジレポート
pytest --cov=app --cov-report=html

# 特定テストのみ
pytest tests/test_function_calling.py::test_parallel_function_calls -v
```

---

## 🛠️ 技術スタック

| レイヤー | 技術 |
|---------|------|
| **フロントエンド** | FastAPI + Swagger UI（予定） |
| **バックエンド** | Python 3.11, FastAPI |
| **AI/ML** | Azure OpenAI (GPT-4o, text-embedding-ada-002) |
| **検索** | Azure AI Search (Hybrid Search) |
| **Agent** | Azure AI Foundry Assistants API |
| **認証** | Azure Managed Identity (RBAC) |
| **IaC** | Bicep（予定） |
| **テスト** | pytest, pytest-asyncio |

---

## 📈 開発ロードマップ

- [x] **Phase 1**: Azure AI Search RAGパイプライン構築
- [x] **Phase 2**: Azure AI Foundry環境セットアップ
- [x] **Phase 3**: Function Calling実装（4ツール）
- [ ] **Phase 4**: FastAPI Web化（Day 23-24）
- [ ] **Phase 5**: Code Interpreter統合（Day 19-20）
- [ ] **Phase 6**: File Search統合（Day 21-22）
- [ ] **Phase 7**: 本番環境デプロイ

---

## 🤝 貢献

プロジェクトへの貢献を歓迎します。

1. Fork this repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照。

---

## 📞 連絡先

**プロジェクト責任者**: Ryo Nakamizo  
**組織**: 日野コンピューターシステム株式会社  
**メール**: [your-email@example.com]

---

## 🙏 謝辞

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants/overview)
- [FastAPI Framework](https://fastapi.tiangolo.com/)
