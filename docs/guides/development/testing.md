# Testing Guide

> Azure RAG Agent POC - テスト戦略とベストプラクティス

**対象**: 開発者全員  
**最終更新**: 2024-12-22

---

## 📋 テスト戦略

### テストピラミッド

```
        ┌─────────────┐
        │   E2E Tests │  ← 少数（手動 + 自動）
        │   (5-10%)   │
        ├─────────────┤
        │ Integration │  ← 中規模（Azure統合）
        │   (20-30%)  │
        ├─────────────┤
        │ Unit Tests  │  ← 大規模（ロジック検証）
        │   (60-70%)  │
        └─────────────┘
```

### テストの種類

| Type | Purpose | Example |
|------|---------|---------|
| **Unit** | 単一関数/クラスの動作検証 | `test_calculate()` |
| **Integration** | Azure サービス統合検証 | `test_search_documents()` |
| **E2E** | エンドツーエンドフロー検証 | `test_rag_pipeline()` |

---

## 🧪 ユニットテスト

### 基本パターン

```python
import pytest
from app.agents.tools.implementations import calculate

def test_calculate_addition():
    """加算の基本動作を検証"""
    result = calculate("2 + 3")
    assert result == 5.0

def test_calculate_complex():
    """複雑な式の計算を検証"""
    result = calculate("(10 + 5) * 2 - 3")
    assert result == 27.0

def test_calculate_invalid_expression():
    """不正な式の例外処理を検証"""
    with pytest.raises(ValueError):
        calculate("invalid expression")
```

### モックの活用

```python
from unittest.mock import Mock, patch
from app.agents.foundry_agent_service import FoundryAgentService

@patch('app.agents.foundry_agent_service.AzureOpenAI')
def test_create_thread(mock_openai):
    """スレッド作成のモック検証"""
    # モック設定
    mock_client = Mock()
    mock_client.beta.threads.create.return_value = Mock(id="thread_123")
    mock_openai.return_value = mock_client
    
    # テスト実行
    service = FoundryAgentService()
    thread_id = service.create_thread()
    
    # 検証
    assert thread_id == "thread_123"
    mock_client.beta.threads.create.assert_called_once()
```

---

## 🔌 統合テスト

### Azure サービステスト

```python
import pytest
from azure.core.exceptions import ResourceNotFoundError
from app.agents.tools.implementations import search_documents

@pytest.mark.integration
def test_search_documents_real_azure():
    """Azure AI Search統合テスト（実際のサービス）"""
    query = "Azure AI Search"
    results = search_documents(query, top_k=3)
    
    # 検証
    assert len(results) > 0
    assert all("title" in r for r in results)
    assert all("content" in r for r in results)

@pytest.mark.integration
def test_search_nonexistent_index():
    """存在しないインデックスのエラーハンドリング検証"""
    with pytest.raises(ResourceNotFoundError):
        search_documents("query", index_name="nonexistent-index")
```

### 統合テストの実行

```bash
# 統合テストのみ実行
pytest -m integration

# 統合テストを除外
pytest -m "not integration"
```

---

## 🌐 E2Eテスト

### RAGパイプラインE2E

```python
import pytest
from app.agents.foundry_agent_service import FoundryAgentService

@pytest.mark.e2e
def test_rag_pipeline_end_to_end():
    """RAGパイプライン完全フロー検証"""
    # Setup
    service = FoundryAgentService()
    thread_id = service.create_thread()
    
    # Execute
    query = "Azure AI Searchでベクトル検索を実行する方法は？"
    response_parts = []
    
    for chunk in service.run_streaming(thread_id, query):
        response_parts.append(chunk)
    
    response = "".join(response_parts)
    
    # Verify
    assert len(response) > 100  # 十分な長さの回答
    assert "Azure AI Search" in response
    assert "ベクトル検索" in response or "vector" in response.lower()
    
    # Cleanup
    service.delete_thread(thread_id)
```

### E2E並列Function Calling

```python
@pytest.mark.e2e
def test_parallel_function_calling():
    """並列ツール実行の検証"""
    service = FoundryAgentService()
    thread_id = service.create_thread()
    
    # 複数ツールを必要とするクエリ
    query = "現在時刻を教えて、そして10+20を計算して"
    
    response_parts = []
    for chunk in service.run_streaming(thread_id, query):
        response_parts.append(chunk)
    
    response = "".join(response_parts)
    
    # 両方のツールが実行されたことを確認
    assert any(str(i) in response for i in range(24))  # 時刻
    assert "30" in response  # 計算結果
    
    service.delete_thread(thread_id)
```

---

## 📊 テストカバレッジ

### カバレッジ測定

```bash
# HTMLレポート生成
pytest --cov=app --cov-report=html

# ターミナル出力
pytest --cov=app --cov-report=term-missing

# 特定の閾値を強制
pytest --cov=app --cov-fail-under=80
```

### カバレッジ目標

| Module | Target | Current |
|--------|--------|---------|
| `app/agents/tools/` | 90% | 95% ✅ |
| `app/agents/` | 80% | 85% ✅ |
| `app/api/` | 70% | - (未実装) |

---

## 🏷️ テストマーカー

### 定義（`pytest.ini`）

```ini
[pytest]
markers =
    unit: Unit tests (fast)
    integration: Integration tests (requires Azure)
    e2e: End-to-end tests (slow)
    slow: Slow tests (>5s)
```

### 使用例

```python
@pytest.mark.unit
def test_fast_unit():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_azure_integration():
    pass
```

### マーカー別実行

```bash
# ユニットテストのみ
pytest -m unit

# 統合テスト除外
pytest -m "not integration"

# 遅いテスト除外
pytest -m "not slow"

# 複数マーカー
pytest -m "unit or integration"
```

---

## 🔧 テストフィクスチャ

### 共通フィクスチャ（`conftest.py`）

```python
import pytest
from app.agents.foundry_agent_service import FoundryAgentService

@pytest.fixture
def agent_service():
    """FoundryAgentService インスタンスを提供"""
    return FoundryAgentService()

@pytest.fixture
def thread_id(agent_service):
    """テスト用スレッドを作成・削除"""
    thread = agent_service.create_thread()
    yield thread
    agent_service.delete_thread(thread)

@pytest.fixture
def mock_search_results():
    """モック検索結果を提供"""
    return [
        {
            "title": "Azure AI Search Overview",
            "content": "Azure AI Search is...",
            "source": "https://learn.microsoft.com/...",
            "score": 0.95
        },
        {
            "title": "Vector Search Guide",
            "content": "Vector search enables...",
            "source": "https://learn.microsoft.com/...",
            "score": 0.87
        }
    ]
```

### フィクスチャの使用

```python
def test_with_fixtures(agent_service, thread_id):
    """フィクスチャを活用したテスト"""
    response = agent_service.run_streaming(thread_id, "test query")
    assert response is not None
```

---

## 🐛 デバッグ技術

### pytest デバッグオプション

```bash
# 詳細出力
pytest -vv

# 最初の失敗で停止
pytest -x

# 失敗したテストのみ再実行
pytest --lf

# stdout/stderrを表示
pytest -s

# 特定のテストのみ実行
pytest tests/test_function_calling.py::test_calculate -v
```

### ブレークポイント

```python
def test_with_breakpoint():
    result = some_function()
    breakpoint()  # Python 3.7+
    assert result == expected
```

### ログ出力

```python
import logging

def test_with_logging(caplog):
    """ログ出力をキャプチャ"""
    with caplog.at_level(logging.INFO):
        function_that_logs()
    
    assert "Expected log message" in caplog.text
```

---

## 🚀 CI/CD統合

### GitHub Actions（例）

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run unit tests
        run: pytest -m unit --cov=app
      
      - name: Run integration tests
        run: pytest -m integration
        env:
          AZURE_SEARCH_ENDPOINT: ${{ secrets.AZURE_SEARCH_ENDPOINT }}
          AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
```

---

## 📝 テスト作成チェックリスト

新しい機能を実装する際のテスト作成ガイド：

- [ ] ユニットテストを作成（関数単位）
- [ ] エッジケースをテスト（空入力、極端な値）
- [ ] エラーハンドリングをテスト（例外処理）
- [ ] 統合テストを作成（Azure接続が必要な場合）
- [ ] E2Eテストを検討（重要なフローのみ）
- [ ] テストカバレッジ80%以上を維持
- [ ] CI/CDで自動実行されることを確認

---

## 🔗 関連リソース

### 内部ドキュメント
- [Local Development Setup](local-setup.md)
- [Function Calling Guide](function-calling.md)

### 外部リンク
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

**質問・提案**: [GitHub Issues](https://github.com/your-org/azure-rag-agent-poc/issues)
