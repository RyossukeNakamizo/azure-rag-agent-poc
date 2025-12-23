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

---

## 2024-12-23: Python SDK Integration (Phase 2-2)

**Status**: Accepted

**Context**
- Azure AI Search との統合に Python SDK が必要
- キーワード検索とベクトル検索の両方をサポート
- 既存インデックス（rag-docs-index）を活用

**Decision**
- `azure-search-documents==11.6.0b7` を採用
- `SearchService` クラスで検索ロジックをカプセル化
- Managed Identity 認証（API Key 不使用）
- ハイブリッド検索（Vector + Keyword）実装

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| REST API 直接呼び出し | SDK不要 | エラーハンドリング複雑 | 公式SDK推奨 |
| LangChain Vector Store | 抽象化高 | 依存関係増、オーバーヘッド | Azure Native原則 |
| API Key 認証 | 実装簡単 | セキュリティリスク | Managed Identity優先 |

**Consequences**
- SDK バージョン: 11.6.0b7（ベータ版、最新機能対応）
- 検索性能: キーワード検索 0.70スコア、ハイブリッド検索 0.033スコア
- 認証: DefaultAzureCredential で自動認証

**Validation**
- ✅ キーワード検索: 3件取得成功（スコア 0.70-0.32）
- ✅ ハイブリッド検索: 3件取得成功（1536次元ベクトル）
- ✅ Embedding生成: Azure OpenAI text-embedding-ada-002
- ✅ Managed Identity 認証成功

**実装詳細**:
- `SearchService`: ハイブリッド検索・キーワード検索
- `config.py`: AZURE_SEARCH_* 環境変数サポート
- テストクエリ「Azure」で日本語ドキュメント正常取得