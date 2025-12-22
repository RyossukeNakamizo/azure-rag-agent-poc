# Local Development Setup

> Azure RAG Agent POC - ローカル開発環境セットアップガイド

**対象**: 新規開発者、環境再構築時  
**所要時間**: 30分  
**最終更新**: 2024-12-22

---

## 📋 前提条件

### 必須

- ✅ Python 3.11 以上
- ✅ Git
- ✅ Azure CLI
- ✅ Azureサブスクリプション（開発者アクセス権限）

### 推奨

- VS Code または Cursor IDE
- GitHub CLI (`gh`)
- Docker Desktop（将来的に使用予定）

---

## 🚀 セットアップ手順

### 1. リポジトリクローン

```bash
# HTTPSクローン
git clone https://github.com/your-org/azure-rag-agent-poc.git
cd azure-rag-agent-poc

# SSHクローン（推奨）
git clone git@github.com:your-org/azure-rag-agent-poc.git
cd azure-rag-agent-poc
```

### 2. 仮想環境作成

```bash
# 仮想環境作成
python3.11 -m venv .venv

# 有効化（Mac/Linux）
source .venv/bin/activate

# 有効化（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 有効化（Windows CMD）
.venv\Scripts\activate.bat
```

### 3. 依存関係インストール

```bash
# 本番依存関係
pip install -r requirements.txt

# 開発依存関係（テスト、リント等）
pip install -r requirements-dev.txt
```

**requirements.txt（抜粋）**:
```
azure-identity>=1.15.0
azure-search-documents>=11.6.0
openai>=1.12.0
python-dotenv>=1.0.0
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
```

### 4. 環境変数設定

```bash
# .env.exampleをコピー
cp .env.example .env

# エディタで編集
vim .env  # または code .env
```

**.env テンプレート**:
```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<search-service>.search.windows.net
AZURE_SEARCH_INDEX=rag-docs-index

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<openai-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_CHAT=gpt-4o
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-ada-002

# Azure AI Foundry
AZURE_AI_PROJECT_CONNECTION_STRING=<connection-string>
AZURE_ASSISTANT_ID=<assistant-id>

# Development
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 5. Azure認証設定

```bash
# Azureログイン
az login

# サブスクリプション確認
az account show

# 必要に応じてサブスクリプション切り替え
az account set --subscription "<subscription-id>"
```

### 6. RBAC権限確認

以下のロールが割り当てられていることを確認：

```bash
# 自分のプリンシパルID取得
az ad signed-in-user show --query id -o tsv

# ロール割り当て確認
az role assignment list \
  --assignee <your-principal-id> \
  --resource-group rg-rag-poc \
  --output table
```

**必要なロール**:
- `Azure AI Developer`
- `Search Index Data Contributor`
- `Cognitive Services OpenAI User`

---

## 🧪 動作確認

### 1. Azure接続テスト

```bash
# Azure AI Searchテスト
python -m scripts.test_search

# Azure OpenAIテスト
python -c "from openai import AzureOpenAI; from azure.identity import DefaultAzureCredential; print('OK')"
```

### 2. 単体テスト実行

```bash
# 全テスト実行
pytest

# 特定モジュールのみ
pytest tests/test_function_calling.py -v

# カバレッジ付き
pytest --cov=app --cov-report=html
```

**期待される出力**:
```
collected 27 items

tests/test_function_calling.py::test_tool_definitions PASSED
tests/test_function_calling.py::test_search_documents PASSED
tests/test_function_calling.py::test_calculate PASSED
...
========================= 27 passed in 0.33s =========================
```

### 3. ローカルサーバー起動（Day 23-24実装後）

```bash
# FastAPI起動
uvicorn app.main:app --reload --port 8000

# 別ターミナルでヘルスチェック
curl http://localhost:8000/api/health
```

---

## 🔧 トラブルシューティング

### Issue 1: `ModuleNotFoundError: No module named 'xxx'`

**原因**: 依存関係がインストールされていない

**解決策**:
```bash
# 仮想環境が有効化されているか確認
which python  # -> /path/to/.venv/bin/python

# 依存関係を再インストール
pip install -r requirements.txt
```

### Issue 2: `DefaultAzureCredentialError`

**原因**: Azure認証が失敗している

**解決策**:
```bash
# Azureに再ログイン
az logout
az login

# 認証情報をクリア（Mac/Linux）
rm -rf ~/.azure

# 認証情報をクリア（Windows）
Remove-Item -Recurse -Force "$env:USERPROFILE\.azure"
```

### Issue 3: `403 Forbidden` (RBAC権限エラー)

**原因**: 必要なRBACロールが割り当てられていない

**解決策**:
```bash
# 管理者に連絡し、以下のロールを付与してもらう
# - Azure AI Developer
# - Search Index Data Contributor
# - Cognitive Services OpenAI User
```

### Issue 4: `AssistantNotFoundError`

**原因**: `.env` の `AZURE_ASSISTANT_ID` が正しくない

**解決策**:
```bash
# Azure Portal で Assistant ID を確認
# または、新規作成
python -m scripts.create_assistant
```

---

## 🛠️ 開発ツール設定

### VS Code 推奨拡張機能

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-azuretools.vscode-azureresourcegroups",
    "charliermarsh.ruff",
    "ms-python.black-formatter"
  ]
}
```

### Ruff設定（`.ruff.toml`）

```toml
line-length = 100
target-version = "py311"

[lint]
select = ["E", "F", "I"]
ignore = ["E501"]
```

### pytest設定（`pytest.ini`）

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
```

---

## 📚 次のステップ

セットアップ完了後、以下のガイドを参照してください：

1. [Function Calling実装ガイド](function-calling.md)
2. [テストガイド](testing.md)
3. [Azure Resources Setup](../deployment/azure-resources.md)

---

## 🔗 関連リンク

- [Python公式ドキュメント](https://docs.python.org/3.11/)
- [Azure CLI リファレンス](https://learn.microsoft.com/cli/azure/)
- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)

---

**トラブル時の連絡先**: [your-email@example.com]
