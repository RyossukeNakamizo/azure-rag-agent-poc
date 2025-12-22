# Function Calling Implementation Guide

Azure AI Foundry Agents with Function Calling実装の完全ガイド。

---

## 目次

1. [概要](#概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [ツール定義](#ツール定義)
4. [ツール実装](#ツール実装)
5. [Agent実装](#agent実装)
6. [テスト戦略](#テスト戦略)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### Function Callingとは

LLMが外部ツール（関数）を呼び出して、リアルタイムデータ取得や計算を実行できる仕組み。

**メリット**:
- LLMの知識カットオフを超えた情報取得
- 正確な計算実行
- 外部システム統合（API、データベース、MES等）

**本実装の特徴**:
- Azure AI Foundry Assistants API使用
- 4ツール実装（検索、計算、日時、設備状態）
- 並列実行対応
- セキュリティ対策済み

---

## アーキテクチャ

### 全体フロー

```
User Query
    │
    ▼
Azure AI Foundry Assistant
    │
    ├─ Analyze Query → Tool Selection
    │
    ▼
Tool Execution (Parallel if needed)
    │
    ├─ search_documents → Azure AI Search
    ├─ calculate → Math.eval (restricted)
    ├─ get_current_datetime → pytz
    └─ get_equipment_status → MES API stub
    │
    ▼
Result Synthesis
    │
    ▼
Structured Response
```

### コンポーネント構成

| コンポーネント | ファイル | 責務 |
|---------------|---------|------|
| Tool Definitions | `tool_definitions.py` | JSON Schemaツールスキーマ |
| Tool Implementations | `implementations.py` | ツール実行ロジック |
| Mock Agent | `function_calling_agent_mock.py` | 検証用Agent |
| Foundry Agent | `foundry_agent_service.py` | 本番用Agent（Assistants API） |
| Tests | `test_function_calling.py` | 単体/統合テスト |

---

## ツール定義

### JSON Schema形式

```python
# tool_definitions.py
from typing import Dict, Any, List

class ToolRegistry:
    """ツール定義レジストリ"""
    
    def __init__(self):
        self.tools = {}
    
    def register(self, name: str, schema: Dict[str, Any]):
        """ツール登録"""
        self.tools[name] = schema
    
    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """全ツールスキーマ取得（Assistants API形式）"""
        return [
            {
                "type": "function",
                "function": schema
            }
            for schema in self.tools.values()
        ]
```

### ツールスキーマ例

```python
# search_documentsツール
search_documents_schema = {
    "name": "search_documents",
    "description": "社内ドキュメントを検索し、関連情報を取得します",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "検索クエリ"
            },
            "top_k": {
                "type": "integer",
                "description": "取得件数",
                "default": 5
            }
        },
        "required": ["query"]
    }
}
```

### 重要なスキーマ設計原則

1. **`description`は詳細に**: LLMがツール選択に使用
2. **`required`を明確に**: 必須/オプション区別
3. **`default`値を設定**: よく使う値を推奨
4. **`enum`で制約**: 選択肢を限定（例: タイムゾーン）

---

## ツール実装

### 基本パターン

```python
# implementations.py
from typing import Dict, Any

def tool_impl(**kwargs) -> Dict[str, Any]:
    """
    ツール実装テンプレート
    
    Args:
        **kwargs: ツールパラメータ
    
    Returns:
        結果辞書（JSON serializable）
    """
    try:
        # 1. パラメータ検証
        validate_params(kwargs)
        
        # 2. ビジネスロジック実行
        result = execute_logic(kwargs)
        
        # 3. 結果返却
        return {
            "status": "success",
            "data": result
        }
    
    except Exception as e:
        # エラーハンドリング
        return {
            "status": "error",
            "error": str(e)
        }
```

### セキュリティ対策例（calculateツール）

```python
def calculate_impl(expression: str) -> Dict[str, Any]:
    """数式評価（セキュリティ制限付き）"""
    
    # 許可関数リスト
    allowed_functions = {
        'abs': abs,
        'sqrt': lambda x: x ** 0.5,
        'pow': pow,
        'round': round
    }
    
    # 危険な関数をブロック
    if any(danger in expression for danger in ['__', 'import', 'eval', 'exec']):
        return {
            "status": "error",
            "error": "Security: Forbidden operation"
        }
    
    # 制限付きeval実行
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_functions)
        return {
            "status": "success",
            "result": float(result),
            "expression": expression
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

---

## Agent実装

### Mock Agent（検証用）

**用途**: Azure接続不要で開発・テスト

```python
# function_calling_agent_mock.py
class MockFunctionCallingAgent:
    """Mock版Function Calling Agent"""
    
    def chat(self, query: str) -> str:
        # 1. ツール選択（ルールベース）
        tools_to_call = self._select_tools(query)
        
        # 2. ツール実行（並列）
        results = [
            self.tool_implementations[tool](**args)
            for tool, args in tools_to_call
        ]
        
        # 3. 回答生成（テンプレート）
        return self._synthesize_response(query, results)
```

### Foundry Agent（本番用）

**用途**: Azure AI Foundry Assistants API統合

```python
# foundry_agent_service.py
class FoundryAgentService:
    """Azure AI Foundry Agent サービス"""
    
    def __init__(self):
        self.client = AzureOpenAI(...)
        self.assistant_id = None
        self.thread_id = None
    
    def create_assistant(self, name: str) -> str:
        """Assistant作成"""
        tools = tool_registry.get_all_tool_schemas()
        
        assistant = self.client.beta.assistants.create(
            name=name,
            instructions="工場向けAIアシスタント...",
            model="gpt-4o",
            tools=tools
        )
        
        return assistant.id
    
    def chat(self, user_message: str) -> str:
        """チャット実行"""
        # 1. Thread作成（初回のみ）
        if not self.thread_id:
            self.create_thread()
        
        # 2. メッセージ追加
        self.add_message(user_message)
        
        # 3. Run実行
        run_id = self.run_assistant()
        
        # 4. 完了待機（Function Calling処理含む）
        self.wait_for_run_completion(run_id)
        
        # 5. 回答取得
        messages = self.get_messages(limit=1)
        return messages[0]["content"]
    
    def _handle_required_actions(self, run):
        """Function Calling処理"""
        tool_outputs = []
        
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            # ツール実行
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            result = self.tool_implementations[function_name](**function_args)
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result, ensure_ascii=False)
            })
        
        # ツール結果送信
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
```

---

## テスト戦略

### テスト階層

```
Unit Tests (単体テスト)
  ├─ Tool Definitions (4 tests)
  ├─ Calculator Tool (7 tests)
  ├─ DateTime Tool (6 tests)
  └─ Equipment Status Tool (5 tests)

Integration Tests (統合テスト)
  ├─ Mock Agent (4 tests)
  └─ End-to-End (1 test)

Total: 27 tests
```

### pytest実装例

```python
# test_function_calling.py
import pytest
from app.agents.tools.implementations import calculate_impl

class TestCalculatorTool:
    """Calculatorツールテスト"""
    
    def test_basic_arithmetic(self):
        """基本四則演算"""
        result = calculate_impl(expression="2 + 2")
        assert result["status"] == "success"
        assert result["result"] == 4.0
    
    def test_security_blocked(self):
        """セキュリティ: __import__ブロック"""
        result = calculate_impl(expression="__import__('os').system('ls')")
        assert result["status"] == "error"
        assert "Forbidden" in result["error"]
    
    @pytest.mark.parametrize("expr,expected", [
        ("sqrt(25)", 5.0),
        ("pow(2, 3)", 8.0),
        ("abs(-10)", 10.0)
    ])
    def test_math_functions(self, expr, expected):
        """数学関数テスト"""
        result = calculate_impl(expression=expr)
        assert result["result"] == expected
```

---

## トラブルシューティング

### 1. RBAC権限エラー

**症状**:
```
エージェントにアクセスできません
Azure OpenAI リソースにアクセスするための権限がありません
```

**解決策**:
```bash
# Azure AI Developer ロール割り当て
az role assignment create \
  --assignee <PROJECT_PRINCIPAL_ID> \
  --role "Azure AI Developer" \
  --scope /subscriptions/.../Microsoft.CognitiveServices/accounts/<OPENAI_NAME>

# 15分待機（ロール伝播）
```

### 2. Assistants API Deprecation Warning

**症状**:
```
DeprecationWarning: The Assistants API is deprecated in favor of the Responses API
```

**対処**:
- 現在は動作するため無視可能
- 将来的にResponses APIへ移行予定
- コード変更は不要

### 3. Index名不一致

**症状**:
```
Azure AI Search接続失敗
```

**解決策**:
```bash
# .envのIndex名確認
cat .env | grep AZURE_SEARCH_INDEX

# 正しいIndex名に修正
AZURE_SEARCH_INDEX=rag-docs-index  # rag-indexではない
```

---

## ベストプラクティス

### ツール設計

1. **単一責任**: 1ツール = 1機能
2. **冪等性**: 同じ入力 → 同じ出力
3. **エラーハンドリング**: 常に`status`フィールド返却
4. **型安全性**: JSON serializable型のみ使用

### セキュリティ

1. **入力検証**: `eval()`等の危険関数は制限実行
2. **ホワイトリスト**: 許可関数リストで制御
3. **Managed Identity**: API Key使用禁止
4. **ログ記録**: 実行履歴を監査可能に

### パフォーマンス

1. **並列実行**: 独立ツールは同時呼び出し
2. **タイムアウト**: Run完了待機に制限設定
3. **キャッシング**: 頻繁に使うデータはキャッシュ
4. **非同期処理**: 長時間処理は非同期化検討

---

## 参考リソース

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [JSON Schema Specification](https://json-schema.org/)
- [pytest Documentation](https://docs.pytest.org/)

---

## 更新履歴

- **2025-12-22**: 初版作成（Day 17-18実装完了）
