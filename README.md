# Azure RAG Agent POC

RAG (Retrieval-Augmented Generation) システムの概念実証プロジェクト。
Azure AI Foundry Agents with Function Calling実装。

---

## プロジェクト概要

工場向けAIアシスタントの構築を目的とした、Azure AI FoundryベースのエンタープライズグレードRAGシステム。

**主要機能**：
- ✅ Function Calling（4ツール実装）
- ✅ Hybrid Search（Azure AI Search）
- ✅ Azure OpenAI統合（gpt-4o、text-embedding-ada-002）
- ✅ Managed Identity認証
- ✅ pytest完全カバレッジ（27テスト）

---

## アーキテクチャ

```
User Query
    │
    ▼
Azure AI Foundry Agent (Assistants API)
    │
    ├─▶ Function Calling Tools
    │   ├─ search_documents (Azure AI Search)
    │   ├─ calculate (Math evaluation)
    │   ├─ get_current_datetime (Timezone-aware)
    │   └─ get_equipment_status (Factory MES stub)
    │
    ▼
Azure OpenAI (gpt-4o)
    │
    ▼
Structured Response
```

---

## セットアップ

### 前提条件

- Python 3.11+
- Azure Subscription
- Azure CLI認証済み（`az login`）

### インストール

```bash
# リポジトリクローン
git clone https://github.com/RyossukeNakamizo/azure-rag-agent-poc.git
cd azure-rag-agent-poc

# 仮想環境作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envを編集してAzureリソース情報を設定
```

### 環境変数（.env）

```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<search-service>.search.windows.net
AZURE_SEARCH_INDEX=rag-docs-index

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<openai-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_CHAT=gpt-4o
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-10-01-preview

# Azure AI Foundry Assistant
AZURE_ASSISTANT_ID=asst_szAH6GUpXD17TQmoS4kY78Hx
```

---

## 使用方法

### 1. Mock Agent（Azure接続不要）

```bash
PYTHONPATH=$(pwd) python app/agents/function_calling_agent_mock.py
```

### 2. Azure AI Foundry Agent（実環境）

```bash
PYTHONPATH=$(pwd) python app/agents/foundry_agent_service.py
```

### 3. pytest実行

```bash
# 全テスト実行
PYTHONPATH=$(pwd) pytest tests/test_function_calling.py -v

# カバレッジ付き
PYTHONPATH=$(pwd) pytest tests/test_function_calling.py -v --cov=app/agents
```

---

## Function Calling Tools

### 1. search_documents

**用途**: Azure AI Searchでハイブリッド検索（ベクトル + キーワード）

**パラメータ**:
- `query` (str): 検索クエリ
- `top_k` (int): 取得件数（デフォルト: 5）

**例**:
```python
result = search_documents_impl(query="Azure AI Search", top_k=3)
```

### 2. calculate

**用途**: 数式評価（セキュリティ制限付き）

**パラメータ**:
- `expression` (str): 数式（例: `"sqrt(25)"`, `"100 ** 2"`）

**例**:
```python
result = calculate_impl(expression="25 * 4")
# => {"result": 100.0}
```

### 3. get_current_datetime

**用途**: タイムゾーン対応の日時取得

**パラメータ**:
- `timezone` (str): タイムゾーン（デフォルト: `"Asia/Tokyo"`）
- `format` (str): 出力形式（`"japanese"`, `"iso"`, `"unix"`）

**例**:
```python
result = get_current_datetime_impl(timezone="America/New_York", format="iso")
```

### 4. get_equipment_status

**用途**: 工場設備状態確認（MES APIスタブ）

**パラメータ**:
- `equipment_id` (str): 設備ID
- `include_history` (bool): 24時間履歴を含めるか

**例**:
```python
result = get_equipment_status_impl(equipment_id="LINE-A-01", include_history=True)
```

---

## ディレクトリ構造

```
azure-rag-agent-poc/
├── app/
│   └── agents/
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── tool_definitions.py      # JSON Schemaツール定義
│       │   └── implementations.py       # ツール実装
│       ├── function_calling_agent.py    # 本番用Agent
│       ├── function_calling_agent_mock.py  # Mock Agent
│       └── foundry_agent_service.py     # Azure AI Foundry統合
├── tests/
│   └── test_function_calling.py         # pytest（27テスト）
├── notebooks/
│   └── function_calling_demo.ipynb      # Jupyter検証
├── docs/
│   └── FUNCTION_CALLING.md              # 実装ガイド
├── .env                                 # 環境変数
├── .env.example                         # 環境変数テンプレート
├── requirements.txt                     # 依存関係
└── README.md                            # このファイル
```

---

## テスト結果

```bash
$ PYTHONPATH=$(pwd) pytest tests/test_function_calling.py -v

============================== 27 passed in 0.33s ==============================

Test Coverage:
  ✅ Tool Definitions: 4/4 tests
  ✅ Calculator Tool: 7/7 tests
  ✅ DateTime Tool: 6/6 tests
  ✅ Equipment Status Tool: 5/5 tests
  ✅ Mock Agent: 4/4 tests
  ✅ Integration: 1/1 test
```

---

## Azure リソース

| リソース | 名前 | 用途 |
|---------|------|------|
| Resource Group | `rg-rag-poc` | リソースコンテナ |
| AI Foundry Hub | `ai-hub-dev-ldt4idhueffoe` | AI開発環境 |
| AI Foundry Project | `rag-agent-project` | プロジェクト管理 |
| Azure OpenAI | `oai-ragpoc-dev-ldt4idhueffoe` | LLM/Embedding |
| Azure AI Search | `search-ragpoc-dev-ldt4idhueffoe` | ハイブリッド検索 |
| Assistant | `asst_szAH6GUpXD17TQmoS4kY78Hx` | Function Calling Agent |

---

## 開発履歴

### Day 17-18: Function Calling実装（2025-12-22）

**実装内容**:
- ✅ 4ツール定義（JSON Schema準拠）
- ✅ Mock Agent実装（検証用）
- ✅ Azure AI Foundry Agent実装
- ✅ pytest 27テスト（100% PASS）
- ✅ 並列Function Calling検証
- ✅ RBAC権限設定（Azure AI Developer）

**所要時間**: 4時間

**主要課題**:
1. RBAC権限エラー → `Azure AI Developer`ロール割り当てで解決
2. Azure Portal UI制限 → Python SDK直接実装で回避
3. Assistants API deprecation warning → 動作確認済み、将来移行予定

---

## 次のステップ

- [ ] Code Interpreter統合
- [ ] File Search統合
- [ ] ストリーミング応答実装
- [ ] FastAPI Webアプリ化
- [ ] 実MES API統合（設備状態ツール）
- [ ] Application Insights統合

---

## ライセンス

MIT License

---

## 参考リソース

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [OpenAI Assistants API](https://platform.openai.com/docs/assistants/overview)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
- [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
