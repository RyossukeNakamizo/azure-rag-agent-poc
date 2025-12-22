# Decision Log

> 技術選定の判断履歴を時系列で記録

---

## 2024-12-22: Azure AI Projects SDK 1.0.0b1 → Azure OpenAI 直接統合

**Status**: Accepted

**Context**
- Azure AI Projects SDK 1.0.0b1 の Assistants API が完全廃止
- DeprecationWarning: "The Assistants API is deprecated in favor of the Responses API"
- 530 エラー: "No backend service has been configured to receive requests for this URI"
- `client.inference.get_azure_openai_client()` 認証エラー: "Unknown authentication type"
- Azure AI Foundry Connections 経由での接続が不可能

**Decision**
- **Azure OpenAI SDK を直接使用**（Standard OpenAI 互換 API）
- Managed Identity（DefaultAzureCredential）による認証
- Assistants API 完全回避
- Azure AI Foundry Projects SDK は使用しない

**Alternatives Considered**

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Assistants API 継続 | 既存コード流用可能 | API 廃止済み（530 エラー） | 技術的に不可能 |
| Responses API 実装 | 公式推奨（理論上） | 実装方法不明、ドキュメント不足 | 実装不可能 |
| Azure AI Projects SDK Connections | AI Foundry 統合 | 認証エラー解決不可 | 技術的に不可能 |
| **Azure OpenAI 直接統合** | 安定・ドキュメント充実 | AI Foundry 機能未使用 | **採用** |

**Consequences**
- **技術的影響**:
  - 実装時間: 約4時間（調査 + 実装 + テスト）
  - 既存コード廃棄: foundry_agent.py 全体（~200行）
  - 依存関係: azure-ai-projects 1.0.0b1 は残存（将来使用可能性あり）
  
- **機能的影響**:
  - Azure AI Foundry Agent 機能（Tools, Retrieval等）は未実装
  - Standard Chat Completions のみ利用可能
  - Function Calling は将来実装可能

- **運用的影響**:
  - Azure AD 認証（Managed Identity）による高セキュリティ
  - API Key 不要
  - Azure OpenAI の全機能利用可能

**Validation**
- ✅ Health Check: 200 OK
- ✅ Tools Endpoint: 200 OK（空配列）
- ✅ Chat Non-Streaming: 200 OK、日本語レスポンス正常
- ✅ Chat Streaming: 200 OK、SSE ストリーム正常
- ✅ Azure AD 認証: DefaultAzureCredential 動作確認済み
- ✅ レイテンシ: P50 < 1s（目標達成）

**Technical Stack (Final)**
```
FastAPI 0.125.0
├── Azure OpenAI (openai 2.13.0)
│   ├── Endpoint: https://oai-ragpoc-dev-ldt4idhueffoe.openai.azure.com/
│   ├── Deployment: gpt-4o (2024-08-06)
│   └── Authentication: Azure AD (Managed Identity)
├── Azure Identity (azure-identity 1.25.1)
│   └── DefaultAzureCredential
└── Pydantic (pydantic 2.12.5)
```

**Lessons Learned**
1. **Beta SDK のリスク**: azure-ai-projects 1.0.0b1 は急速に変化中
2. **公式ドキュメント不足**: Responses API の実装例が存在しない
3. **直接統合の安定性**: Standard Azure OpenAI SDK は最も安定
4. **段階的アプローチの有効性**: FastAPI 基盤を先に完成させたことで問題切り分けが容易

---

## 2024-12-22: Embedding Model Selection

**Status**: Deferred（将来実装時に決定）

**Context**
- Azure AI Search RAG 実装は将来フェーズ
- 現在は Chat Completions のみ実装

**Decision**
- text-embedding-ada-002 をデプロイメント済み（10 capacity）
- 実装は将来フェーズで判断

**Next Steps**
- RAG 実装時に再検討
- text-embedding-3-small/large との比較評価

---

## 2024-12-22: FastAPI Architecture

**Status**: Accepted

**Context**
- エンタープライズグレードの API 設計が必要
- 依存性注入、ミドルウェア、ライフサイクル管理

**Decision**
- FastAPI + Pydantic Settings
- 依存性注入パターン（Depends）
- CORS ミドルウェア有効化
- Lifespan 管理（startup/shutdown）

**Consequences**
- テスタビリティ向上
- 拡張性確保
- Swagger UI 自動生成

**Validation**
- ✅ Swagger UI: http://127.0.0.1:8000/docs
- ✅ ReDoc: http://127.0.0.1:8000/redoc
- ✅ 依存性注入: AgentServiceDep 動作確認
