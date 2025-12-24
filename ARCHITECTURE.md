# System Architecture

> Azure RAG Agent POC - システムアーキテクチャ設計書

**最終更新**: 2024-12-24  
**バージョン**: 1.1  
**ステータス**: Active Development

---

## 設計原則

1. **Security First**: Managed Identity優先、API Keyは最終手段
2. **Cost Awareness**: 従量課金の影響を常に考慮
3. **Observability**: Application Insightsによる可視化を標準装備
4. **Simplicity**: 必要十分な構成、過度な抽象化を回避
5. **Azure Native**: 公式SDKとサービスを優先

---

## システムコンテキスト

### 高レベルアーキテクチャ

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
│                  ┌──────────────┐    ┌─────────────────┐   │
│                  │ Azure OpenAI │    │  Application    │   │
│                  │ (GPT-4o)     │    │  Insights       │   │
│                  └──────────────┘    └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### コンポーネント責任

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| API Layer | Request routing, Auth, Rate limiting | FastAPI |
| Agent Orchestration | Function calling, Tool execution | Azure AI Foundry Assistants API |
| Search | Hybrid retrieval (Vector + Keyword) | Azure AI Search |
| Embedding | Text vectorization | Azure OpenAI text-embedding-ada-002 |
| LLM | Response generation | Azure OpenAI GPT-4o |
| Monitoring | Metrics, Logs, Traces | Application Insights |
| Infrastructure | Resource provisioning | Bicep (planned) |

---

## データフロー

### RAG Pipeline

```
1. User Query (FastAPI Endpoint)
   │
   ▼
2. AI Foundry Assistant
   │
   ├──▶ 3a. Tool: search_documents
   │         │
   │         ├─▶ Generate Embedding (Azure OpenAI)
   │         │
   │         ├─▶ Hybrid Search (Azure AI Search)
   │         │
   │         └─▶ Return Top-K Documents
   │
   ├──▶ 3b. Tool: calculate
   │         └─▶ Execute calculation
   │
   ├──▶ 3c. Tool: get_current_datetime
   │         └─▶ Return current time
   │
   └──▶ 3d. Tool: get_equipment_status
             └─▶ Query equipment database
   │
   ▼
4. LLM Response Generation (GPT-4o)
   │
   ▼
5. Streaming Response to User
```

### Function Calling Flow

```
User Input
   │
   ▼
AI Foundry Assistant
   │
   ├─ Decide which tools to call
   │
   ├─ Execute tools (parallel if applicable)
   │  │
   │  ├─ search_documents → Azure AI Search
   │  ├─ calculate → Local computation
   │  ├─ get_current_datetime → System time
   │  └─ get_equipment_status → Mock data
   │
   ├─ Aggregate tool results
   │
   └─ Generate final response
      │
      ▼
Streaming SSE to client
```

---

## 技術スタック詳細

### フロントエンド（予定）
- **Framework**: FastAPI + Swagger UI
- **API Protocol**: REST + Server-Sent Events (SSE)
- **Authentication**: Azure AD (optional)

### バックエンド
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.109+
- **Async Runtime**: asyncio + uvicorn

### AI/ML Services
- **LLM**: Azure OpenAI GPT-4o (gpt-4o deployment)
- **Embedding**: text-embedding-ada-002 (1536 dimensions)
- **Agent**: Azure AI Foundry Assistants API
- **Search**: Azure AI Search (Standard tier)

### Infrastructure
- **Region**: Japan East
- **Authentication**: Managed Identity (System-assigned)
- **Monitoring**: Application Insights
- **IaC**: Bicep (planned)

---

## Evaluation Architecture (D21追加)

### 評価パイプライン構成

```
┌─────────────────────────────────────────────────────────────┐
│              Batch Evaluation Pipeline (v7)                 │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Test Data    │───▶│ RAG System   │───▶│ LLM Response │  │
│  │ (22 Q&As)    │    │ (Search+Gen) │    │              │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│                      ┌───────────────────────────┘          │
│                      ▼                                      │
│          ┌────────────────────────┐                         │
│          │  3-Metric Evaluation   │                         │
│          │  (LLM-as-Judge)        │                         │
│          └────────────────────────┘                         │
│                      │                                      │
│          ┌───────────┴───────────┐                          │
│          ▼           ▼           ▼                          │
│     ┌─────────┐ ┌─────────┐ ┌─────────┐                    │
│     │Coherence│ │Relevance│ │Grounded-│                    │
│     │  0.988  │ │  0.963  │ │  ness   │                    │
│     │         │ │         │ │  0.375  │                    │
│     └─────────┘ └─────────┘ └─────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### LLM-as-Judge 実装方式

| 評価指標 | プロンプト構造 | モデル | 認証 |
|----------|--------------|-------|------|
| Coherence | Few-shot (5 examples) + 5点スケール | gpt-4o | Managed Identity |
| Relevance | Few-shot (5 examples) + 5点スケール | gpt-4o | Managed Identity |
| Groundedness | Few-shot (3 examples) + Yes/No判定 | gpt-4o | Managed Identity |

**設計原則**:
1. **シンプルさ優先**: 外部フレームワーク依存を排除
2. **セキュリティ**: すべてManaged Identity認証
3. **再現性**: Few-shot examples固定、temperature=0
4. **拡張性**: 新規指標追加は独立モジュールとして実装

**制限事項**:
- データ不足時のGroundedness精度低下（22件→100件で改善見込み）
- プロンプト品質維持の手動管理必要
- RAGASのContext Precision等の高度指標は未実装

---

## セキュリティアーキテクチャ

### 認証フロー

```
┌─────────────────────────────────────────────────────────┐
│                 Authentication Flow                      │
│                                                         │
│  FastAPI App ──(Managed Identity)──▶ AI Foundry Project │
│      │                                                  │
│      ├──(Managed Identity)──▶ Azure AI Search           │
│      │                                                  │
│      ├──(Managed Identity)──▶ Azure OpenAI              │
│      │                                                  │
│      └──(Managed Identity)──▶ Key Vault (future)        │
│                                                         │
│  RBAC Roles Required:                                   │
│  - Azure AI Developer (AI Foundry)                      │
│  - Search Index Data Contributor (AI Search)            │
│  - Cognitive Services OpenAI User (Azure OpenAI)        │
└─────────────────────────────────────────────────────────┘
```

### ネットワークセキュリティ

**Current (Development)**:
- Public endpoints enabled
- IP filtering: Not configured
- Private Link: Not configured

**Future (Production)**:
- Private Endpoints for all services
- VNet integration
- Azure Firewall rules
- Application Gateway with WAF

---

## 制約条件

| Constraint | Reason | Impact |
|------------|--------|--------|
| Japan East region | データレジデンシー要件 | 一部サービスの制限あり |
| No API keys in code | セキュリティポリシー | Managed Identity必須 |
| Public endpoint | 開発フェーズ | 本番はPrivate Endpoint移行 |
| Standard tier | コスト最適化 | レプリカ数・パーティション数制限 |
| Single replica | 開発環境コスト削減 | SLA 99.5% |

---

## 品質属性 (D21更新)

### パフォーマンス目標

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| API Latency (P50) | < 1s | Application Insights |
| API Latency (P95) | < 3s | Application Insights |
| Search Latency (P95) | < 500ms | Azure AI Search metrics |
| Embedding Generation | < 200ms | OpenAI API metrics |

### 評価指標

| Attribute | Target | Current (D21) | Measurement |
|-----------|--------|--------------|-------------|
| **Coherence** | **0.85** | **0.988 ✅** | **Batch Evaluation** |
| **Relevance** | **0.85** | **0.963 ✅** | **Batch Evaluation** |
| **Groundedness** | **0.85** | **0.375 ❌** | **Batch Evaluation** |

### 可用性

| Service | Target SLA | Actual SLA (current) |
|---------|-----------|---------------------|
| FastAPI | 99.9% | N/A (local dev) |
| Azure AI Search | 99.9% | 99.5% (single replica) |
| Azure OpenAI | 99.9% | 99.9% |
| AI Foundry | 99.9% | 99.9% |

### コスト管理

| Resource | Monthly Budget | Usage Monitoring |
|----------|---------------|------------------|
| Azure OpenAI | ¥20,000 | Token usage tracking |
| Azure AI Search | ¥15,000 | Index size, query count |
| AI Foundry | ¥10,000 | Assistant API calls |
| **Total** | **¥50,000** | Cost Management + Alerts |

---

## スケーラビリティ戦略

### 水平スケーリング

**Current State**:
- Single FastAPI instance (local dev)
- Single AI Search replica
- Shared Azure OpenAI capacity

**Future State (if needed)**:
- Azure App Service (multiple instances)
- AI Search: 3 replicas + 2 partitions
- Dedicated OpenAI capacity

### データスケーリング

| Data Volume | Index Strategy | Expected Performance |
|-------------|---------------|---------------------|
| < 10K docs | Single index, single partition | < 100ms P95 |
| 10K - 100K | Single index, 2 partitions | < 200ms P95 |
| 100K - 1M | Multiple indices, 3+ partitions | < 500ms P95 |

---

## 運用考慮事項

### モニタリング

**Metrics to Track**:
- API request rate, latency, error rate
- Token consumption (input/output)
- Search query performance
- Tool execution success rate
- Cost per request

**Alerting Thresholds**:
- Error rate > 5%
- P95 latency > 5s
- Daily cost > ¥3,000

### ログ管理

**Log Levels**:
- INFO: Request/response metadata
- WARNING: Rate limiting, retries
- ERROR: Exception stack traces
- DEBUG: Tool execution details (dev only)

**Retention Policy**:
- Application Insights: 90 days
- Local logs: 7 days

---

## 将来的な拡張 (D21更新)

### 優先度: Critical

| Feature | Trigger Condition | Estimated Effort | Status |
|---------|------------------|------------------|--------|
| **Data Augmentation** | **D22開始時** | **2-3 days** | **Planned** |

### 優先度: High

| Feature | Trigger Condition | Estimated Effort |
|---------|------------------|------------------|
| Private Endpoints | 本番環境移行時 | 2 days |
| Bicep IaC | リソース再作成頻度増加時 | 3 days |
| CI/CD Pipeline | 複数環境管理が必要な時 | 2 days |

### 優先度: Medium

| Feature | Trigger Condition | Estimated Effort | Status |
|---------|------------------|------------------|--------|
| Multi-region | 可用性99.9%要件時 | 5 days | Pending |
| Code Interpreter | データ分析機能要求時 | 2 days | Pending |
| File Search | PDF/長文検索要求時 | 2 days | Pending |
| **Context Precision** | **評価指標拡大時** | **1-2 days** | **Deferred** |

### 優先度: Low

| Feature | Trigger Condition | Estimated Effort |
|---------|------------------|------------------|
| Semantic Ranker | 検索精度向上要求時 | 1 day |
| GPT-4o-mini | コスト削減要求時 | 0.5 day |
| Custom Embedding | 精度最適化要求時 | 3 days |

---

## 技術的負債

### 既知の問題

1. **Assistants API Deprecation Warning**
   - Status: 動作確認済みだが、将来的に新APIへ移行必要
   - Impact: Medium
   - Resolution: Monitor OpenAI announcements

2. **Mock Tool Implementations**
   - Status: `get_equipment_status` は現在モックデータ
   - Impact: Low (POC段階のため)
   - Resolution: Day 25-26で実装予定

3. **No Input Validation**
   - Status: FastAPI Pydantic validation未実装
   - Impact: Medium
   - Resolution: Day 23-24で実装予定

4. **Limited Evaluation Data (D21)**
   - Status: 22件のみ（目標100件以上）
   - Impact: High（Groundedness 0.375）
   - Resolution: D22-D24でデータ拡充

---

## 参考資料

### Azure Documentation
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-studio/)
- [Azure AI Search - RAG Pattern](https://learn.microsoft.com/azure/search/retrieval-augmented-generation-overview)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)

### Internal Documents
- [技術選定の判断履歴](DECISIONS.md)
- [却下オプション分析](TRADEOFFS.md)
- [開発ガイド](docs/guides/development/)
- [作業セッション記録](docs/sessions/README.md)

---

## 変更履歴

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-22 | Ryo Nakamizo | Initial architecture document |
| 1.1 | 2024-12-24 | Ryo Nakamizo | D21評価アーキテクチャ追加、品質属性更新 |

---

**次回更新予定**: D22-D24（データ拡充後）
