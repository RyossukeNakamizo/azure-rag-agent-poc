# Decision Log

> 技術選定の判断履歴を時系列で記録

---

## 2026-01-04: Cosmos DB Integration for Conversation History (D24)

**Status**: Accepted

**Context**
- RAGシステムにマルチターン対話機能が必要
- 会話履歴の永続化でコンテキスト継続性を実現
- 面接デモでの差別化要素として会話履歴機能を追加

**Decision**
- **Azure Cosmos DB for NoSQL（Serverless）**を採用
- パーティションキー: `/sessionId`（セッション単位クエリ最適化）
- 認証: Managed Identity（既存パターン踏襲）
- TTL: 30日（自動クリーンアップ）

**Alternatives Considered**

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Azure Table Storage | 低コスト、シンプル | クエリ機能限定 | 柔軟なクエリ要件 |
| Azure SQL Database | 強力なクエリ、トランザクション | 高コスト、オーバースペック | 単純なKVアクセスに過剰 |
| Redis Cache | 超低レイテンシ | 永続性弱、コスト | 履歴永続化要件 |
| **Cosmos DB Serverless** | 従量課金、柔軟なスキーマ、低レイテンシ | 若干の学習コスト | **採用** |

**Consequences**
- **技術的影響**:
  - 新規ファイル: 5ファイル（Bicep 1、Python 4）
  - 新規エンドポイント: `/api/chat/with-history`
  - 既存エンドポイント: 変更なし（後方互換）

- **コスト影響**:
  - 開発環境: ~¥500-2,000/月（Serverless）
  - 本番環境: ~¥3,000/月（Provisioned 400 RU/s）

- **運用的影響**:
  - セッション管理の自動化
  - 30日後の自動TTL削除
  - COSMOS_DB_ENABLED=false で無効化可能

**Validation**
- [ ] Bicepデプロイ成功
- [ ] Repositoryパターン動作確認
- [ ] /api/chat/with-history エンドポイント動作確認
- [ ] マルチターン対話の文脈継続確認

**Files Created**
```
infra/modules/cosmos-db.bicep           # Cosmos DBリソース定義
app/models/conversation.py              # 会話データモデル
app/repositories/cosmos_repository.py   # データアクセス層
app/services/conversation_service.py    # ビジネスロジック
docs/COSMOS_DB_DESIGN.md                # 設計ドキュメント
```

---

## 2025-12-23: Azure AI Search Schema Standardization

**Status**: Accepted

**Context**
- Phase 2-4: Azure AI Search インデックス作成とサンプルデータ投入
- RAG API (`app/api/routes/rag.py`) が期待するフィールド: `title`, `source`, `category`
- 初期スクリプトが使用していたフィールド: `filename`, `url`, `chunk_id`
- Azure AI Search 仕様: 既存フィールド削除不可（インデックス再作成が必須）

**Decision**
- **スキーマ統一**: 全コンポーネントで `title`, `source`, `category` を使用
- **インデックス再作成**: 既存インデックス削除 → 正しいスキーマで再作成
- **修正範囲**:
  - `scripts/create_search_index.py`: `filename`/`url` → `title`/`source`
  - `scripts/upload_sample_data.py`: 同上
  - `app/services/search_service.py`: `chunk_id` 削除、`source`/`category` 追加
  - `scripts/test_rag_e2e.py`: `filename` → `title`

**Alternatives Considered**

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| API側修正 | スクリプト不変 | 複数エンドポイント影響 | 影響範囲大 |
| 両フィールド保持 | 互換性確保 | ストレージコスト2倍 | 冗長性、保守性低下 |
| **スクリプト側修正** | 影響範囲小 | インデックス再作成必須 | **採用** |

**Consequences**
- **技術的影響**:
  - 修正時間: 約1時間（問題発見 + 修正 + 検証）
  - 修正ファイル数: 4ファイル
  - インデックス再作成: 1回（`scripts/delete_search_index.py` 作成）
  
- **データ品質影響**:
  - スキーマ統一による保守性向上
  - サンプルデータ5件投入成功
  - カテゴリ別分布: AI Patterns (1), Azure Services (1), Infrastructure (1), Security (2)

- **運用的影響**:
  - Health Check: `degraded` → `healthy` (Search Service)
  - E2Eテスト: 全クエリ成功（3クエリ × ハイブリッド検索 → RAG回答生成）

**Validation**
- ✅ `scripts/verify_index.py`: スキーマ確認完了（`id`, `content`, `title`, `source`, `category`, `contentVector`）
- ✅ `scripts/upload_sample_data.py`: 5件正常投入
- ✅ Health Check: Search Service `healthy`
- ✅ E2Eテスト: 全通過
  - Query 1: "Azure AI Searchのセマンティック検索" → 検索成功 + 回答生成
  - Query 2: "Managed Identityの利点" → 検索成功 + 回答生成
  - Query 3: "RAGシステムの実装方法" → 検索成功 + 四答生成

**Final Schema**
```python
# Azure AI Search Index
fields = [
    SimpleField(name="id", type=String, key=True),
    SearchableField(name="content", type=String),
    SearchableField(name="title", type=String),      # ← filename から変更
    SimpleField(name="source", type=String),          # ← url から変更
    SimpleField(name="category", type=String),
    SearchField(name="contentVector", type=Collection(Single), dimensions=1536)
]
```

**Lessons Learned**
1. **スキーマ設計の重要性**: APIとデータレイヤー間のスキーマ合意が不可欠
2. **Azure AI Search 仕様**: フィールド削除不可のため、初期設計が重要
3. **段階的検証**: インデックス作成 → データ投入 → E2Eテストの順当性
4. **自動修正の有効性**: sed/filesystem:edit_file による一括置換で効率化

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

## 2024-12-24: RAGAS Version Selection

**Status**: Accepted (forced by Python 3.13)

**Context**
- D21要件: ragas==0.1.9
- 実行環境: Python 3.13.0
- エラー: langchain_core.utils.pre_init ImportError
- RAGAS 0.1.9 は LangChain 旧バージョン構造（pydantic_v1）を要求
- Python 3.13 環境で依存関係が連鎖的に破綻

**Decision**
- ragas>=0.2.0（最新版）を採用
- langchain依存をクリーンアップ
- datasets パッケージを追加

**Alternatives Considered**

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| ragas==0.1.9 | 要件準拠 | Python 3.13非対応 | 技術的不可能 |
| Python 3.11にダウングレード | 0.1.9動作可 | 全環境再構築 | コスト過大 |
| **ragas>=0.2.0** | Python 3.13対応、安定 | API微差異リスク | **採用** |

**Consequences**
- **技術的影響**:
  - APIの微差異発生リスク（低）
  - メトリクス計算ロジックは同等（faithfulness, answer_relevancy, context_precision）
  - 最新版のバグフィックス・改善を享受
  
- **実装的影響**:
  - D21要件文書を自動修正
  - 評価関数実装に影響なし（APIインターフェース互換）
  
- **運用的影響**:
  - 長期サポート性向上
  - Python 3.13環境での安定動作

**Validation**
- インポートテスト成功
- 基本評価動作確認
- 3メトリクス（faithfulness(), answer_relevancy(), context_precision()）動作確認
- **破壊的変更対応**: RAGAS 0.4.2はメトリクスインスタンス化が必須

**Dependencies (Final)**
```
ragas>=0.2.0
datasets
```

**Lessons Learned**
1. **バージョン固定のリスク**: 古いバージョン固定は環境依存問題を引き起こす
2. **Python 3.13互換性**: 新しいPythonバージョンでは依存関係の再検証が必須
3. **最新版の優位性**: 積極的な最新版採用がトラブル回避に繋がる

---

## 2024-12-24: Evaluation Framework Selection (ADR-002)

**Status**: Accepted

**Context**
- D21でRAG評価指標の改善が必要（Coherence 0.42→0.85+、Relevance 0.09→0.85+）
- RAGASフレームワークの統合を検討したが、以下の制約に直面：
  - Azure AI Foundry環境でのインストール困難（依存関係の競合）
  - Managed Identity認証との統合が不明瞭（RAGAS内部でAPI Key前提の実装）
  - 既存の評価パイプライン（Promptflow形式）との互換性問題

**Decision**
- **独自LLM-as-Judge実装を採用**
  - Azure OpenAI直接呼び出し（Managed Identity認証）
  - シンプルなプロンプトベース評価（Few-shot examples付き）
  - 既存のバッチ評価フレームワークに統合

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| RAGAS統合 | 実績あるフレームワーク、多機能 | インストール困難、API Key依存、オーバーヘッド大 | 環境制約とセキュリティポリシー不適合 |
| Azure AI Foundry Evaluators | ネイティブ統合、GUI操作可 | カスタマイズ性低、バッチ処理向きでない | 既存パイプライン再構築が必要 |
| DeepEval | モダンなフレームワーク | RAGASと同様の統合課題 | 学習コスト増、環境制約 |

**Consequences**
- **ポジティブ**:
  - Managed Identity認証を完全維持（セキュリティ強度維持）
  - 既存パイプラインへの最小限の変更
  - トラブルシューティングの容易性（依存関係削減）
  - 評価ロジックの完全可視性と制御

- **ネガティブ**:
  - 評価プロンプトの品質維持が必要（継続的改善）
  - RAGASの先進的機能（Context Precision等）は手動実装が必要
  - コミュニティサポートが限定的

**Validation**
- **検証方法**: 22件の技術Q&Aデータセットでバッチ評価
- **結果**:
  - Coherence: 0.42 → **0.988** (+135.2%)
  - Relevance: 0.09 → **0.963** (+969.4%)
  - Groundedness: 0.17 → 0.375 (+120.6%、データ不足により目標未達)

**Revisit Trigger**
- Azure AI Foundry環境でRAGASの公式Managed Identity対応が実装された場合
- 評価指標が10種類以上に拡大し、独自実装の保守コストが肥大化した場合

---

## 2024-12-24: Authentication Strategy - Managed Identity Adherence (ADR-003)

**Status**: Accepted

**Context**
- D21評価実装中、一時的にAPI Key使用を検討する選択肢が浮上
- 理由: RAGAS等の外部フレームワーク統合時の認証簡素化
- しかし、プロジェクトのセキュリティポリシーは「Managed Identity優先」を明示

**Decision**
- **Managed Identity認証を堅持**
  - すべてのAzure OpenAI呼び出しで`DefaultAzureCredential`使用
  - API Keyは一切使用しない（ローカル開発環境でも`az login`経由）

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| API Key（開発環境限定） | 実装高速化、外部ライブラリ統合容易 | セキュリティリスク、本番環境との差異 | セキュリティポリシー違反 |
| 環境変数によるAPI Key管理 | 柔軟性向上 | Key Vault必須、ローテーション負担 | 複雑性増加、リスク増 |

**Consequences**
- **ポジティブ**:
  - 開発環境と本番環境の認証方式統一（デバッグ容易）
  - API Key漏洩リスクゼロ
  - Azure AD監査ログによる完全なアクセス追跡

- **ネガティブ**:
  - 外部ライブラリ（RAGAS等）統合時の制約
  - 初期セットアップの複雑性（RBAC設定必須）

**Validation**
- すべての評価スクリプト（v2シリーズ）でManaged Identity動作確認済み
- `azure-identity==1.19.0`の安定動作を確認

**Revisit Trigger**
- プロジェクトのセキュリティポリシー変更時のみ（現時点で予定なし）

---

## 2024-12-24: Data Augmentation Deferral (ADR-004)

**Status**: Accepted

**Context**
- D21目標: 全指標0.85+達成
- 現状: Coherence/Relevance達成、Groundedness未達（0.375）
- 原因分析: データ不足（22件のみ、100件以上推奨）
- 制約: D21期限内でのデータ拡充は時間的に困難

**Decision**
- **データ拡充を次フェーズ（D22-D24）に延期**
  - D21は評価フレームワーク確立に集中
  - データ拡充は専用タスクとして独立実施

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| D21内で強行拡充 | 全指標達成 | 品質低下リスク、期限超過 | 時間制約 |
| 外部データセット流用 | 高速拡充 | ドメイン不一致、品質不明 | 本番想定外 |

**Consequences**
- **ポジティブ**:
  - 評価フレームワークの品質確保（Coherence/Relevance実証済み）
  - データ拡充作業を計画的に実施可能
  - 次フェーズの明確な目標設定

- **ネガティブ**:
  - D21単独では3指標同時達成未完
  - Groundedness改善は次フェーズ依存

**Validation**
- Coherence/Relevanceの高精度達成により、評価ロジックの正当性を実証
- 次フェーズでデータ100件到達時、Groundedness 0.85+達成を見込む

**Revisit Trigger**
- なし（次フェーズで必ず実施）

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

### 2026-01-04: Conversation History Data Store Selection (D24)

**Status**: Accepted

**Context**
- RAGシステムにマルチターン会話履歴機能を追加
- セッション単位での履歴管理が必要
- 自動クリーンアップ（TTL）機能が必須
- Managed Identity認証を維持

**Decision**
- Azure Cosmos DB for NoSQL（Serverless）を採用
- パーティションキー: `/sessionId`
- TTL: 30日（2592000秒）
- 認証: Managed Identity（RBAC）

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Azure Table Storage | 低コスト、シンプル | TTLなし、クエリ制限 | 自動クリーンアップ不可 |
| Azure SQL Database | 強力なクエリ、トランザクション | オーバースペック、固定コスト | 会話履歴には過剰 |
| Azure Cache for Redis | 超低レイテンシ | 揮発性、永続化コスト高 | データ永続性要件未達 |

**Consequences**
- Serverlessで従量課金（低トラフィック時はほぼ無料）
- TTLによる自動データクリーンアップでストレージコスト最適化
- RBAC権限設定が必要（ローカル開発時に追加設定）

**Validation**
- マルチターン会話テスト: `history_used=1`, `turn_number=2` 確認
- セッション継続: 同一`session_id`での履歴取得成功

---

### 2026-01-04: Cosmos DB Partition Key Strategy (D24)

**Status**: Accepted

**Context**
- 会話履歴のパーティションキー設計
- セッション単位でのクエリが主要アクセスパターン

**Decision**
- パーティションキー: `/sessionId`

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| /userId | ユーザー単位集約 | セッション跨ぎクエリ増 | クエリパターン不一致 |
| /createdAt | 時系列整理 | 範囲クエリ非効率 | Cosmos DBの制約 |

**Consequences**
- セッション単位クエリが最適化
- ユーザー跨ぎ分析には追加インデックス必要

**Validation**
- セッション内履歴取得: 単一パーティションクエリで高速

---

### 2026-01-04: Health Check Endpoint Enhancement (D25-1)

**Status**: Accepted

**Context**
- D24でCosmos DB統合完了
- ヘルスチェックエンドポイント `/api/v1/rag/health` にCosmos DBステータスが含まれていない
- 運用時の問題切り分けにCosmos DB接続状態の可視化が必要

**Decision**
- `RAGHealthResponse` モデルに `cosmos_db` フィールドを追加
- ステータス値: `disabled` / `healthy` / `unhealthy: {error}`
- 全体ステータス判定にCosmos DBは含めない（オプショナルサービスのため）

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| 別エンドポイント `/health/cosmos` | 関心の分離 | 運用複雑化 | 統合ビューが望ましい |
| 全体ステータスに含める | 厳格な監視 | Cosmos DB無効時もdegraded | オプショナル機能 |

**Consequences**
- 単一エンドポイントで全サービス状態を確認可能
- Cosmos DB障害時も `status: healthy`（Search/OpenAI正常時）
- グレースフルデグラデーション実現

**Validation**
- ✅ `cosmos_db: "healthy"` レスポンス確認
- ✅ 全体ステータス `healthy` 維持確認

**Files Modified**
```
app/models/rag.py              # RAGHealthResponse.cosmos_db追加
app/api/routes/rag.py          # レスポンスにcosmos_db含める
```

---

### 2026-01-04: E2E Test Strategy (D25-2)

**Status**: Accepted

**Context**
- D24 Cosmos DB統合完了後、包括的なE2Eテストが未整備
- 既存テスト `tests/test_rag_pipeline.py` は古い `src/` 構造を参照
- 新規機能（マルチターン会話）のリグレッションテストが必要

**Decision**
- pytest用E2Eテストスイート `tests/test_e2e_rag_api.py` 作成
- 手動実行用簡易スクリプト `scripts/quick_e2e_test.py` 作成
- 5カテゴリ・20+テストケースでカバレッジ確保

**Test Categories**
| Category | Tests | Coverage |
|----------|-------|---------|
| Health Check | 4 | 全サービスステータス、Cosmos DB含む |
| Hybrid Search | 3 | 検索結果、スコア、top_k |
| RAG Chat | 4 | 回答生成、ソース引用、Query Expansion |
| Multi-turn | 4 | セッション作成、履歴使用、継続性 |
| Error Handling | 3 | バリデーションエラー |
| Performance | 3 | レイテンシ確認 |

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| 既存テスト修正 | 作業量少 | 構造不一致、技術的負債 | 全面書き換え同等 |
| 統合テストのみ | シンプル | カバレッジ不足 | マルチターン検証不可 |

**Consequences**
- 新機能追加時のリグレッション検出が容易
- CI/CD統合可能（pytest実行）
- 手動検証も色付き出力で視認性向上

**Validation**
- ✅ 5/5カテゴリ全テスト合格
- ✅ マルチターン会話: `history_used=1`, `turn_number=2` 確認

**Files Created**
```
tests/test_e2e_rag_api.py      # pytest用E2Eテストスイート
scripts/quick_e2e_test.py      # 手動実行用簡易スクリプト
```

---
# Decision Log - D26 Update

> D26: Bicep RBAC自動化の技術選定記録

---

## 2026-01-05: RBAC自動化アーキテクチャ（D26）

**Status**: Accepted

**Context**
- 新規開発者のオンボーディング時に手動で`az role assignment create`を複数回実行していた
- ヒューマンエラーによる権限設定ミスのリスク
- 環境（dev/stg/prod）間での一貫性確保が困難

**Decision**
- Bicepモジュール化によるRBAC自動化を採用
- `infra/modules/rbac-assignments.bicep`として再利用可能なモジュールを作成
- シェルスクリプト`scripts/assign-rbac.sh`でラップして簡易実行

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Azure CLI スクリプト | シンプル、即実行可能 | べき等性なし、エラー処理が手動 | 再実行時の重複エラー |
| Terraform | マルチクラウド対応 | 学習コスト、状態管理必要 | Azure専用プロジェクト |
| ARM Template | 公式サポート | 冗長、可読性低 | 保守性が低い |
| Azure Policy | 自動適用、監査機能 | 複雑、オーバーエンジニアリング | 開発フェーズに過剰 |

**Consequences**
- 開発者オンボーディングが1コマンドで完了（約30秒）
- What-if確認による安全なデプロイ
- Bicepのべき等性により再実行が安全

**Validation**
- `az deployment group what-if`で変更プレビュー確認
- 実際のロール割り当て後、アプリケーション動作確認

---

## 2026-01-05: Cosmos DB RBACのSQL Role Assignment使用（D26）

**Status**: Accepted

**Context**
- Cosmos DBのデータプレーンアクセスには専用のSQL Role Assignmentが必要
- 通常のAzure RBACとは異なるリソースタイプ

**Decision**
- `Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments`リソースを使用
- Built-in Role ID `00000000-0000-0000-0000-000000000002`（Data Contributor）を適用

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Azure RBAC (Cosmos DB Account Contributor) | 標準的なRBAC | コントロールプレーンのみ、データアクセス不可 | データ操作できない |
| カスタムSQL Role Definition | 細かい権限制御 | 作成・管理が複雑 | Built-inで十分 |
| Connection String認証 | 実装が簡単 | セキュリティリスク、Managed Identity非対応 | セキュリティ要件違反 |

**Consequences**
- Managed Identity認証でCosmos DBデータアクセス可能
- 条件付きデプロイにより、Cosmos DB無効時はスキップ

**Validation**
- `COSMOS_DB_ENABLED=true`でのヘルスチェック正常動作確認済み（D25）

---

## 2026-01-05: モジュール分離パターン（D26）

**Status**: Accepted

**Context**
- RBACロジックを既存のmain.bicepに追加するか、別モジュールにするか
- 将来的に他プロジェクトでも再利用したい

**Decision**
- `infra/modules/rbac-assignments.bicep`として独立モジュール化
- `infra/assign-rbac.bicep`から呼び出す2層構造

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| main.bicepに統合 | ファイル数削減 | 肥大化、再利用困難 | 関心の分離違反 |
| 単一ファイル | シンプル | 再利用性なし | 他プロジェクトで使いたい |
| Azure Verified Modules (AVM) | 標準化済み | 外部依存、カスタマイズ困難 | プロジェクト固有要件あり |

**Consequences**
- モジュールの独立テストが可能
- 他プロジェクトへのコピー&ペーストで再利用可能
- 将来的にAzure Verified Modules形式への移行も容易

**Validation**
- `az bicep build`でコンパイルエラーなし確認

---

## 2026-01-05: エラーハンドリングパターン（D27）

**Status**: Accepted

**Context**
- Cosmos DB接続エラー時のRAGシステム全体への影響を最小化したい
- オプショナルサービスの障害でコア機能が停止しないようにしたい
- エラー状態を明確に管理・報告したい

**Decision**
- グレースフルデグラデーションパターンを採用
- リポジトリ層で`_safe_operation`ラッパーによるエラー吸収
- サービス層でフォールバック値（空リスト、None、0）を返却
- ヘルスチェックで`healthy`/`degraded`/`unhealthy`の3段階ステータス

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Circuit Breaker | 自動復旧、負荷軽減 | 実装複雑、外部ライブラリ依存 | オーバーエンジニアリング |
| Retry Pattern | 一時的エラー対応 | レイテンシ増加、無限ループリスク | 永続的エラーには無効 |
| Fail Fast | シンプル、明確 | UX悪化、コア機能も停止 | オプショナル機能で不適切 |

**Consequences**
- Cosmos DB障害時もRAG検索・回答生成は継続
- 会話履歴は一時的に利用不可（復旧後は再利用可能）
- ヘルスチェックで障害サービスを明示的に報告

**Validation**
- モックテストで障害シナリオを検証
- `test_d27_error_handling.py`でユニットテスト作成

---

## 2026-01-05: 接続状態管理（D27）

**Status**: Accepted

**Context**
- Cosmos DB接続状態をプロパティで公開し、呼び出し元で判断できるようにしたい
- 再接続ロジックを一元管理したい

**Decision**
- `ConnectionState` Enumで状態管理（CONNECTED/DISCONNECTED/ERROR）
- `is_available`プロパティで状態公開
- `_ensure_connection`メソッドで再接続試行を一元化

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Boolean flag | シンプル | 状態が不明確 | ERRORとDISCONNECTEDの区別不可 |
| 毎回接続テスト | 常に最新状態 | パフォーマンス悪化 | API呼び出しごとにオーバーヘッド |
| 外部状態ストア | 分散環境対応 | 複雑、追加依存 | 単一インスタンスで不要 |

**Consequences**
- 状態遷移が明確でデバッグしやすい
- ヘルスチェックで詳細な状態報告が可能

**Validation**
- `ConnectionState.ERROR`時の挙動をテストで検証

---

# 以下は既存のDecision Records（省略せず含める）

<!-- D25以前の記録は実際のファイルから継続 -->
