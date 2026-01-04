# Cosmos DB Integration Design Document

> D24: 会話履歴管理のためのCosmos DB統合設計

**作成日**: 2026-01-04  
**ステータス**: In Progress  
**推定工数**: 8時間  

---

## 1. 目的と背景

### 1.1 ビジネス目的

- **マルチターン対話**: ユーザーが前の質問を参照しながら会話を継続
- **コンテキスト継続性**: セッション内での文脈維持
- **分析基盤**: 将来的なユーザー行動分析・品質改善

### 1.2 技術的要件

| 要件 | 詳細 | 優先度 |
|------|------|--------|
| 会話履歴保存 | セッション単位でメッセージ永続化 | ⭐⭐⭐⭐⭐ |
| 低レイテンシ | 履歴取得 < 100ms | ⭐⭐⭐⭐ |
| スケーラビリティ | 100K+ セッション対応 | ⭐⭐⭐ |
| コスト効率 | 開発フェーズは最小コスト | ⭐⭐⭐⭐⭐ |
| セキュリティ | Managed Identity認証 | ⭐⭐⭐⭐⭐ |

---

## 2. アーキテクチャ設計

### 2.1 高レベルアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        Azure Cloud                          │
│                                                             │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────┐   │
│  │ FastAPI  │───▶│ Cosmos DB   │    │ Azure AI Search  │   │
│  │ Web App  │    │ (会話履歴)   │    │ (ドキュメント)   │   │
│  └────┬─────┘    └─────────────┘    └──────────────────┘   │
│       │                                                     │
│       │         ┌─────────────────┐                        │
│       └────────▶│ Azure OpenAI    │                        │
│                 │ (GPT-4o)        │                        │
│                 └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 データフロー

```
1. User Request (with session_id)
   │
   ▼
2. FastAPI Endpoint
   │
   ├──▶ 3a. Fetch Conversation History (Cosmos DB)
   │         │
   │         └─▶ Last N messages for context
   │
   ├──▶ 3b. RAG Search (Azure AI Search)
   │
   └──▶ 3c. LLM Generation (Azure OpenAI)
             │
             └─▶ Context = History + Search Results
   │
   ▼
4. Save Message to Cosmos DB
   │
   ▼
5. Return Response
```

---

## 3. データモデル設計

### 3.1 コンテナ構成

| コンテナ | 目的 | パーティションキー |
|----------|------|-------------------|
| `conversations` | 会話履歴 | `/sessionId` |

### 3.2 ドキュメントスキーマ

#### Conversation Document

```json
{
  "id": "msg_uuid",
  "sessionId": "session_uuid",
  "userId": "user_uuid",
  "role": "user | assistant",
  "content": "メッセージ内容",
  "metadata": {
    "model": "gpt-4o",
    "tokensUsed": 150,
    "sourcesCount": 3,
    "latencyMs": 1200,
    "queryExpansion": false
  },
  "sources": [
    {
      "id": "doc_id",
      "title": "Document Title",
      "score": 0.95
    }
  ],
  "createdAt": "2026-01-04T10:30:00Z",
  "ttl": 2592000
}
```

#### Session Document (Optional - Phase 2)

```json
{
  "id": "session_uuid",
  "sessionId": "session_uuid",
  "userId": "user_uuid",
  "type": "session",
  "title": "Azure AI Search の設定について",
  "messageCount": 5,
  "createdAt": "2026-01-04T10:00:00Z",
  "updatedAt": "2026-01-04T10:30:00Z",
  "status": "active | archived",
  "ttl": -1
}
```

### 3.3 パーティション設計

**パーティションキー**: `/sessionId`

**理由**:
1. セッション単位でのクエリが最も頻繁
2. 履歴取得は常にsessionId指定
3. パーティション内でcreatedAtソート

**クエリパターン**:
```sql
-- 履歴取得（最も頻繁）
SELECT * FROM c 
WHERE c.sessionId = @sessionId 
ORDER BY c.createdAt DESC 
OFFSET 0 LIMIT 10

-- セッション一覧（低頻度）
SELECT * FROM c 
WHERE c.userId = @userId AND c.type = 'session'
ORDER BY c.updatedAt DESC
```

---

## 4. インフラ設計（Bicep）

### 4.1 リソース構成

```bicep
// 開発環境: Serverless
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: 'cosmos-${projectName}-${environment}'
  location: location
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [{ locationName: location, failoverPriority: 0 }]
    capabilities: [{ name: 'EnableServerless' }]
    // ... セキュリティ設定
  }
}

// 本番環境: Provisioned Throughput
// minThroughput: 400 RU/s
// autoscale: 400-4000 RU/s
```

### 4.2 コスト見積もり

| 構成 | 月額目安 | ユースケース |
|------|----------|-------------|
| Serverless | ~¥500-2,000 | 開発・検証 |
| Provisioned (400 RU/s) | ~¥3,000 | 低トラフィック本番 |
| Autoscale (400-4000) | ~¥3,000-30,000 | 本番（変動負荷） |

### 4.3 RBAC設計

| ロール | 対象 | GUID |
|--------|------|------|
| Cosmos DB Data Contributor | App Service MI | 00000000-0000-0000-0000-000000000002 |

---

## 5. 実装設計

### 5.1 ディレクトリ構造

```
app/
├── repositories/
│   ├── __init__.py
│   └── cosmos_repository.py    # NEW: Cosmos DB操作
├── models/
│   ├── __init__.py
│   ├── rag.py
│   └── conversation.py         # NEW: 会話データモデル
├── services/
│   ├── __init__.py
│   ├── search_service.py
│   └── conversation_service.py # NEW: 会話管理サービス
└── api/routes/
    ├── __init__.py
    ├── rag.py                  # MODIFY: session_id対応
    └── conversations.py        # NEW: 会話履歴API
```

### 5.2 クラス設計

```python
# repositories/cosmos_repository.py
class CosmosRepository:
    """Cosmos DB操作の抽象化層"""
    
    async def create_message(self, message: ConversationMessage) -> str
    async def get_session_history(self, session_id: str, limit: int = 10) -> List[ConversationMessage]
    async def delete_session(self, session_id: str) -> bool

# services/conversation_service.py
class ConversationService:
    """会話管理ビジネスロジック"""
    
    async def add_turn(self, session_id: str, user_msg: str, assistant_msg: str, metadata: dict)
    async def get_context_messages(self, session_id: str, max_turns: int = 5) -> List[dict]
    async def start_new_session(self, user_id: str = None) -> str
```

### 5.3 API変更

```python
# RAGChatRequest 拡張
class RAGChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # NEW: セッションID
    include_history: bool = True      # NEW: 履歴を含むか
    max_history_turns: int = 5        # NEW: 履歴の最大ターン数
    # ... 既存フィールド

# RAGChatResponse 拡張
class RAGChatResponse(BaseModel):
    answer: str
    session_id: str                   # NEW: セッションID（新規作成時含む）
    turn_number: int                  # NEW: 会話ターン番号
    # ... 既存フィールド
```

---

## 6. 実装ステップ

### Phase 1: 基盤構築（本セッション）

| Step | 内容 | 時間 |
|------|------|------|
| 1.1 | Bicepテンプレート作成 | 1h |
| 1.2 | データモデル実装 | 30min |
| 1.3 | Repositoryパターン実装 | 1.5h |
| 1.4 | API統合 | 2h |
| 1.5 | 動作検証 | 1h |

### Phase 2: 拡張機能（将来）

- セッション管理API
- 会話サマリー生成
- 分析ダッシュボード

---

## 7. 成功基準

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| 履歴取得レイテンシ | < 100ms | Application Insights |
| マルチターン成功率 | 100% | 手動テスト |
| コスト（開発） | < ¥2,000/月 | Cost Management |

---

## 8. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| コールドスタート | 初回アクセス遅延 | Warmup実装 |
| パーティションホットスポット | 性能劣化 | sessionId分散確認 |
| TTL設定ミス | データ消失 | デフォルト30日、要件確認 |

---

## 9. 参考資料

- [Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/)
- [Conversation History Pattern](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/rag-conversation-history)
- [Cosmos DB Python SDK](https://learn.microsoft.com/python/api/overview/azure/cosmos-readme)

---

## 10. 変更履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| 1.0 | 2026-01-04 | 初版作成 |
