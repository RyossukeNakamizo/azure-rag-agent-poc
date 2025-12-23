---

## 2024-12-23: Azure AI Search Service Deployment

**Status**: Accepted

**Context**
- RAG システム構築にエンタープライズグレードの検索基盤が必要
- 既存インデックス（`rag-docs-index`, `rag-index`）が存在
- ベクトル検索（HNSW）+ キーワード検索のハイブリッド構成

**Decision**
- Azure AI Search Basic SKU を採用
- 既存インデックスを活用（新規作成不要）
- RBAC は既に設定済み（追加デプロイ不要）

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| 新規インデックス作成 | クリーンスタート | 既存データ喪失 | 既存構成で十分 |
| Standard SKU | セマンティック検索可能 | コスト3倍 | 開発環境では過剰 |

**Consequences**
- 月額コスト: 約 ¥8,000（Basic SKU）
- 既存インデックス: `rag-docs-index`（1536次元、日本語対応）
- RBAC 完備: 開発者 + Azure OpenAI MI

**Validation**
- ✅ Bicep デプロイ成功（provisioningState: Succeeded）
- ✅ Health Check 成功
- ✅ インデックス一覧取得成功（Managed Identity 認証）
- ✅ ベクトル検索設定確認（HNSW, efConstruction=400, m=4）

**既存インデックス詳細**:
- `rag-docs-index`: 6フィールド、セマンティック検索構成あり
- `rag-index`: 9フィールド、チャンキング情報保持