# Tradeoff Analysis

> 却下した選択肢の詳細分析

---

## API側スキーマ変更（却下）

**Category**: Architecture

**Considered For**: filename/url vs title/source 不一致解決

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Impact Scope | High | 1/5 | 複数APIエンドポイント変更必要 |
| Consistency | High | 2/5 | Pydanticモデル全体見直し |
| Test Coverage | Medium | 2/5 | 全E2Eテスト再実行必要 |
| Breaking Change | High | 1/5 | 既存クライアント影響（将来） |

**Final Verdict**: スクリプト修正の方が影響範囲小、リスク低

**Revisit Trigger**: 複数データソース統合時のメタデータ標準化要求時

---

## 両フィールド保持（filename/url + title/source）

**Category**: Data Schema

**Considered For**: スキーマ不一致の互換性解決

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Storage Cost | High | 1/5 | ストレージコスト2倍 |
| Maintainability | High | 1/5 | データ同期保護が必要 |
| Clarity | Medium | 2/5 | どちらが正としいか不明瞠 |
| Technical Debt | High | 1/5 | 将来のリファクタ負債 |

**Final Verdict**: 冗長性が高く、保守性を劣化させる

**Revisit Trigger**: 複数バージョンのAPI互換性が必須になった場合

---

## Azure AI Projects SDK Assistants API

**Category**: API Pattern

**Considered For**: Azure AI Foundry Agent 統合

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Availability | High | 0/5 | API 完全廃止（530 エラー） |
| Documentation | Medium | 1/5 | DeprecationWarning のみ |
| Migration Path | High | 0/5 | Responses API 実装方法不明 |
| Production Ready | High | 0/5 | 技術的に使用不可能 |

**Final Verdict**: Azure 側で API 廃止済み、技術的に使用不可能

**Revisit Trigger**: Azure が Responses API の実装ガイドを公開した場合

---

## Azure AI Projects SDK Responses API

**Category**: API Pattern

**Considered For**: Assistants API の代替

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Documentation | High | 0/5 | 実装例・ガイドなし |
| SDK Support | High | 1/5 | メソッド存在不明 |
| Community | Medium | 0/5 | Stack Overflow に情報なし |
| Time to Implement | High | 0/5 | 調査に3時間費やすも実装方法特定できず |

**Final Verdict**: ドキュメント・実装例が完全に不足、実装不可能

**Revisit Trigger**: Azure が公式実装ガイド・サンプルコードを公開した場合

---

## Azure AI Projects SDK Connections

**Category**: Integration Pattern

**Considered For**: Azure OpenAI 接続情報の取得

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Authentication | High | 1/5 | "Unknown authentication type" エラー |
| Reliability | High | 1/5 | `client.inference.get_azure_openai_client()` 失敗 |
| Debugging | Medium | 1/5 | エラーメッセージが不明瞭 |
| Workaround | High | 0/5 | 回避方法が存在しない |

**Final Verdict**: 認証エラー解決不可、直接統合の方が確実

**Revisit Trigger**: azure-ai-projects SDK の安定版リリース（1.0.0 GA）

---

## LangChain

**Category**: Framework

**Considered For**: RAG オーケストレーション（将来）

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Abstraction | High | 2/5 | 過度な抽象化でデバッグ困難 |
| Stability | High | 2/5 | 頻繁な破壊的変更 |
| Azure Integration | Medium | 3/5 | 公式 SDK の方が安定 |
| Dependency Weight | Medium | 2/5 | 依存関係が重い |

**Final Verdict**: 現時点では Azure 公式 SDK で十分、複雑度に見合う価値なし

**Revisit Trigger**: 
- 複数 LLM プロバイダー対応が必要になった場合
- 複雑なマルチエージェントシステム実装時

---

## API Key Authentication

**Category**: Security Pattern

**Considered For**: Azure サービス認証

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Security | High | 1/5 | キー漏洩リスク |
| Rotation | High | 2/5 | 手動ローテーション必要 |
| Auditability | Medium | 2/5 | アクセス追跡困難 |
| Enterprise Grade | High | 1/5 | エンタープライズ非推奨 |

**Final Verdict**: Managed Identity でキーレス認証を実現、セキュリティ要件達成

**Revisit Trigger**: ローカル開発環境での限定使用のみ（本番では絶対に使用しない）

---

## Semantic Ranker (Azure AI Search)

**Category**: Service Feature

**Considered For**: 検索精度向上（将来）

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Cost | High | 2/5 | 追加課金が発生 |
| Latency | Medium | 3/5 | +200ms 程度 |
| Value | Medium | 3/5 | ハイブリッド検索で十分（仮説） |
| Implementation Phase | High | N/A | RAG 未実装のため評価不可 |

**Final Verdict**: RAG 実装後に精度評価してから判断

**Revisit Trigger**: 
- RAG 実装完了後
- ハイブリッド検索の精度が不足していることが判明した場合

---

## Exhaustive KNN (Vector Search)

**Category**: Algorithm

**Considered For**: ベクトル検索アルゴリズム（将来）

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Latency | High | 1/5 | 10万件で3秒超 |
| Accuracy | Low | 5/5 | 完全精度だが過剰 |
| Scalability | High | 1/5 | データ量に比例して劣化 |
| Cost | Medium | 2/5 | 計算コスト高 |

**Final Verdict**: 大規模データでレイテンシが許容不可、HNSW で十分

**Revisit Trigger**: 
- データ件数 1万件以下
- 精度最優先の要件が発生した場合

---

## RAGAS Framework (D21)

**Category**: Library

**Considered For**: RAG評価指標の高度化（D21 Phase）

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Installation | High | 1/5 | Azure AI Foundry環境で依存関係エラー |
| Security | High | 2/5 | API Key前提、Managed Identity統合不明 |
| Integration | High | 2/5 | 既存Promptflow形式との互換性問題 |
| Maintainability | Medium | 3/5 | ブラックボックス化、デバッグ困難 |
| Features | Low | 5/5 | 先進的評価指標（Context Precision等） |

**Final Verdict**: 環境制約とセキュリティポリシーにより統合困難。独自LLM-as-Judge実装で同等精度を達成可能と判断。

**Revisit Trigger**:
- Azure AI Foundry環境でRAGASの公式サポートが発表された場合
- Managed Identity認証の統合方法が公式ドキュメント化された場合
- 評価指標が10種類以上に拡大し、独自実装の保守コストが肥大化した場合

**Evidence**:
- D21独自実装での達成率: Coherence 0.988, Relevance 0.963（目標0.85突破）
- RAGAS導入試行時間: 約3時間（インストールエラー解決に失敗）

---

## DeepEval Framework (D21)

**Category**: Library

**Considered For**: RAGAS代替の評価フレームワーク

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Maturity | High | 3/5 | 比較的新しいフレームワーク |
| Documentation | Medium | 3/5 | Azure統合事例が少ない |
| Learning Curve | Medium | 2/5 | 独自概念の学習必要 |
| Azure Integration | High | 2/5 | RAGASと同様の懸念あり |

**Final Verdict**: RAGASと同等の統合課題を抱える上、学習コスト増加。独自実装の方が効率的。

**Revisit Trigger**:
- DeepEvalのAzure公式統合が発表された場合
- コミュニティでのAzure AI Foundry導入事例が確立された場合

---

## Azure AI Foundry Native Evaluators (D21)

**Category**: Service Feature

**Considered For**: プラットフォーム標準の評価機能

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Customizability | High | 2/5 | カスタム指標追加が困難 |
| Batch Processing | High | 2/5 | 大量データ処理に不向き |
| Pipeline Integration | High | 2/5 | 既存Pythonスクリプトとの統合複雑 |
| Flexibility | Medium | 2/5 | GUI操作中心、自動化困難 |

**Final Verdict**: GUI中心の設計のため、既存バッチ評価パイプラインとの統合が困難。Pythonスクリプトベースの柔軟性を優先。

**Revisit Trigger**:
- Azure AI FoundryのAPI経由バッチ評価機能が強化された場合
- プロジェクトがGUI中心の運用に移行した場合

**Evidence**:
- 既存パイプライン（run_batch_evaluation_v7.py）との統合コスト: 推定5-7日
- 独自実装での対応時間: 実質1日

---

## Immediate Data Augmentation (D21)

**Category**: Project Planning

**Considered For**: D21期限内での全指標目標達成

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Time Constraint | High | 1/5 | 残り時間でデータ拡充困難 |
| Quality Risk | High | 2/5 | 急速拡充は品質低下リスク |
| Priority | Medium | 2/5 | 評価フレームワーク確立が優先 |
| ROI | Medium | 2/5 | 不完全データより完全フレームワーク |

**Final Verdict**: D21はフレームワーク確立に集中し、データ拡充は計画的に次フェーズで実施する方が、全体的な品質と進捗管理が向上。

**Revisit Trigger**:
- なし（次フェーズD22-D24で必ず実施）

**Evidence**:
- 現状データ: 22件
- 目標データ: 100件以上
- 推定拡充時間: 2-3日（品質チェック込み）
- D21残り時間: 実質0.5日

---

### Query Expansion Pattern A

**Category**: Feature

**Considered For**: Relevance改善（0.780 → 0.850目標）

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Performance Impact | High | 1/5 | All metrics degraded (-3.2% to -4.8%) |
| Cost Efficiency | High | 2/5 | +$0.001/query with negative ROI |
| Implementation Complexity | Medium | 3/5 | QueryExpansionService + parallel search |
| Maintainability | High | 2/5 | Added failure points |
| Baseline Quality | High | 5/5 | Relevance 0.888 already exceeds 0.850 |

**Final Verdict**: 却下 - 全メトリクスで劣化、Baselineが既に高品質

**Revisit Trigger**: 
- Baseline Relevance drops below 0.850
- New expansion algorithms become available
- Cost drops to $0.0001/query or lower

---

### Query Expansion Pattern B (Intent Decomposition)

**Category**: Feature

**Considered For**: Pattern A代替案

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Potential Effectiveness | Medium | 2/5 | Pattern A failed, B likely similar |
| Implementation Cost | High | 1/5 | 2-3 days, high complexity |
| Risk | High | 1/5 | Uncertain benefit |
| Urgency | Low | N/A | Baseline meets requirements |

**Final Verdict**: 却下 - Pattern A失敗により正当化困難

**Revisit Trigger**: Research shows Pattern B >10% improvement

---

### Azure AI Search Semantic Ranker

**Category**: Service Feature

**Considered For**: Relevance & Groundedness改善

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Cost | High | 2/5 | $175/month fixed |
| Effectiveness | Medium | 4/5 | Typically +5-10% Relevance |
| Implementation | Low | 5/5 | Config-only, 15 minutes |
| Current Need | Low | N/A | Baseline sufficient |

**Final Verdict**: 保留 - 現状不要、将来の選択肢として維持

**Revisit Trigger**: 
- Monthly queries > 175,000
- Groundedness becomes critical (>0.850)
- Budget approval for $175/month

---

## D24: Cosmos DB Integration - Rejected Alternatives

### Azure Table Storage

**Category**: Data Storage

**Considered For**: 会話履歴の永続化

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Query Flexibility | High | 2/5 | PartitionKey/RowKeyのみ、セカンダリインデックスなし |
| Schema Flexibility | High | 2/5 | 固定スキーマ前提 |
| TTL Support | Medium | 3/5 | 手動実装必要 |
| Cost | Low | 5/5 | 非常に低コスト |
| Learning Curve | Low | 5/5 | シンプルAPI |

**Final Verdict**: 却下 - createdAt順ソートや柔軟なクエリが必要

**Revisit Trigger**: 
- コスト最小化が絶対優先になった場合
- クエリパターンがPartitionKey/RowKeyのみに単純化された場合

---

### Azure SQL Database

**Category**: Data Storage

**Considered For**: 会話履歴の永続化

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Cost | High | 1/5 | 最小構成でも¥帾2,000/月 |
| Schema Management | High | 2/5 | マイグレーション管理必要 |
| Scalability | High | 4/5 | 垂直スケールのみ |
| Query Power | Low | 5/5 | 強力なSQLサポート |
| Overkill | High | 1/5 | 単純なKVアクセスには過剰 |

**Final Verdict**: 却下 - オーバースペック、コスト高

**Revisit Trigger**: 
- 複雑なJOINクエリが必要になった場合
- トランザクション要件が発生した場合
- 既存SQL Serverの活用が求められた場合

---

### Azure Cache for Redis

**Category**: Data Storage

**Considered For**: 会話履歴の永続化

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Persistence | High | 2/5 | デフォルトはインメモリ、永続化オプションあり |
| Cost | High | 2/5 | Premium tierで¥帾15,000/月～ |
| Query Flexibility | High | 3/5 | Redisクエリは限定的 |
| Latency | Low | 5/5 | ミリ秒レベル |
| Data Integrity | High | 2/5 | 障害時のデータ損失リスク |

**Final Verdict**: 却下 - 永続化要件とコストのバランスが悪い

**Revisit Trigger**: 
- 履歴取得レイテンシが<10ms必須になった場合
- セッションキャッシュ（短期TTL）としての利用

---

### Cosmos DB Provisioned Throughput

**Category**: Service Tier

**Considered For**: 本番環境構成

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Cost Predictability | Medium | 4/5 | 固定費用で予測可能 |
| Development Cost | High | 2/5 | 開発フェーズには過剰 |
| Throughput Guarantee | Low | 5/5 | RU/s保証 |
| Autoscale | Medium | 4/5 | 400-4000 RU/s自動スケール |

**Final Verdict**: 開発フェーズでは却下、本番移行時に再評価

**Revisit Trigger**: 
- 本番環境デプロイ時
- リクエスト数が予測可能になった場合
- SLA要件が発生した場合

### Azure Table Storage (D24)

**Category**: Service

**Considered For**: 会話履歴データストア

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| TTL Support | High | 1/5 | ネイティブTTLなし |
| Query Flexibility | Medium | 2/5 | PartitionKey + RowKeyのみ |
| Cost | Low | 5/5 | 非常に安価 |

**Final Verdict**: TTL機能がなく、自動クリーンアップの実装が必要

**Revisit Trigger**: TTLが不要で、シンプルなKey-Valueアクセスのみの場合

---

### Azure SQL Database (D24)

**Category**: Service

**Considered For**: 会話履歴データストア

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Complexity | High | 2/5 | スキーマ設計・マイグレーション必要 |
| Cost | High | 2/5 | 固定コスト発生 |
| Features | Low | 5/5 | 強力なクエリ・トランザクション |

**Final Verdict**: 会話履歴にはオーバースペック、固定コストが不利

**Revisit Trigger**: 複雑な分析クエリ、トランザクション整合性が必要な場合

---

### Azure Cache for Redis (D24)

**Category**: Service

**Considered For**: 会話履歴データストア

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Persistence | High | 1/5 | 基本的に揮発性メモリ |
| Cost | High | 2/5 | 永続化オプションは高額 |
| Latency | Low | 5/5 | サブミリ秒レスポンス |

**Final Verdict**: 永続性要件を満たさない、コスト高

**Revisit Trigger**: キャッシュ層としての併用、超低レイテンシ要件

---

## D25: Health Check & E2E Test - Rejected Alternatives

### Separate Health Endpoint for Cosmos DB (D25-1)

**Category**: API Design

**Considered For**: Cosmos DBステータスの可視化

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Operational Simplicity | High | 2/5 | 複数エンドポイントの管理負荷 |
| Consistency | High | 2/5 | 他サービスとの統一感欠如 |
| Implementation Cost | Low | 4/5 | 実装は簡単 |

**Final Verdict**: 単一エンドポイントでの統合ビューが運用上望ましい

**Revisit Trigger**: Cosmos DB固有の詳細診断が必要になった場合

---

### Include Cosmos DB in Overall Health Status (D25-1)

**Category**: API Design

**Considered For**: ヘルスチェックの全体ステータス判定

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Graceful Degradation | High | 1/5 | Cosmos DB無効時も全体degraded |
| Optional Service | High | 1/5 | COSMOS_DB_ENABLED=falseで使用可能 |
| Strictness | Medium | 4/5 | 厳密な監視が可能 |

**Final Verdict**: Cosmos DBはオプショナル機能のため、全体ステータスには含めない

**Revisit Trigger**: Cosmos DBが必須機能になった場合

---

### Modify Existing Test Files (D25-2)

**Category**: Testing Strategy

**Considered For**: E2Eテスト整備

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Effort | High | 2/5 | 全面書き換えと同等の作業量 |
| Technical Debt | High | 1/5 | `src/`構造への依存が残る |
| Maintainability | High | 2/5 | 保守性低下 |

**Final Verdict**: 新規作成の方が保守性・可読性向上

**Revisit Trigger**: なし

---

### Integration Tests Only (D25-2)

**Category**: Testing Strategy

**Considered For**: E2Eテスト整備

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Coverage | High | 2/5 | マルチターン会話の検証不可 |
| Simplicity | Low | 5/5 | 実装シンプル |
| Regression Detection | High | 2/5 | 検出能力不足 |

**Final Verdict**: カバレッジ不足、特にCosmos DB統合部分の検証が不十分

**Revisit Trigger**: なし

---
# Tradeoff Analysis - D26 Update

> D26: Bicep RBAC自動化で却下したオプション

---

## Azure CLI スクリプト（シェルスクリプトのみ）

**Category**: Tooling

**Considered For**: RBAC自動割り当て

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Idempotency | High | 1/5 | 既存ロールで重複エラー |
| Error Handling | High | 2/5 | 手動でtry-catch相当の実装必要 |
| Maintainability | Medium | 3/5 | バージョン管理は可能だが変更追跡困難 |
| Azure Integration | High | 3/5 | ネイティブだがWhat-if機能なし |

**Final Verdict**: Bicepのべき等性とWhat-if機能がCLI単体より優れる

**Revisit Trigger**: 極めてシンプルな1回限りのスクリプトが必要な場合

---

## Terraform

**Category**: IaC Framework

**Considered For**: RBAC自動化およびインフラ全体

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Learning Curve | Medium | 2/5 | HCL学習コスト |
| State Management | High | 2/5 | tfstate管理が追加作業 |
| Azure Native | High | 3/5 | AzureRMプロバイダーは安定だが1-2週遅れ |
| Team Skill | High | 2/5 | チームにTerraform経験者少ない |

**Final Verdict**: Azure専用プロジェクトではBicepの方がシームレス

**Revisit Trigger**: マルチクラウド対応が必要な場合、またはTerraform経験者が多いチーム構成

---

## Azure Policy

**Category**: Governance

**Considered For**: RBAC自動適用

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Complexity | High | 1/5 | 設計・デバッグが困難 |
| Flexibility | Medium | 2/5 | 条件式の制約 |
| Development Phase | High | 1/5 | ガバナンスは本番移行後で十分 |
| Audit Trail | Low | 5/5 | 優秀だが現時点で過剰 |

**Final Verdict**: 開発フェーズにおいてオーバーエンジニアリング

**Revisit Trigger**: 本番環境でのコンプライアンス要件、大規模チームでの統制が必要な場合

---

## Azure RBAC (Cosmos DB Account Contributor)

**Category**: Security / Access Control

**Considered For**: Cosmos DBデータアクセス

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Data Plane Access | Critical | 0/5 | コントロールプレーンのみ、データ操作不可 |
| Managed Identity | High | 1/5 | データアクセスにはSQL Role必須 |
| Security | High | N/A | 根本的に目的を達成できない |

**Final Verdict**: Cosmos DBのデータアクセスには`sqlRoleAssignments`が必須

**Revisit Trigger**: なし（技術的に不可能なため）

---

## カスタムSQL Role Definition（Cosmos DB）

**Category**: Security / Access Control

**Considered For**: Cosmos DB細粒度アクセス制御

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Complexity | High | 2/5 | ロール定義の作成・管理が複雑 |
| Maintenance | Medium | 2/5 | 権限変更時の更新作業 |
| Value Add | Medium | 3/5 | 開発フェーズでは過剰な細分化 |
| Built-in Availability | High | 4/5 | Built-in Data Contributorで十分 |

**Final Verdict**: Built-in Roleで必要十分な権限が付与される

**Revisit Trigger**: 最小権限の原則を厳密に適用する本番環境、マルチテナント構成

---

## 単一Bicepファイル（モジュール分離なし）

**Category**: Architecture

**Considered For**: RBAC Bicep構成

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Reusability | High | 2/5 | 他プロジェクトへの転用困難 |
| Testability | Medium | 2/5 | 部分テストが困難 |
| File Size | Low | 3/5 | 許容範囲だが肥大化傾向 |
| Separation of Concerns | High | 2/5 | リソース作成とRBACが混在 |

**Final Verdict**: モジュール分離により再利用性と保守性を確保

**Revisit Trigger**: 極めて小規模なプロジェクト（リソース2-3個程度）

---

## Circuit Breakerパターン

**Category**: Architecture Pattern

**Considered For**: D27 エラーハンドリング

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Complexity | High | 2/5 | 状態管理、タイムアウト、半開状態が必要 |
| Library Dependency | Medium | 2/5 | resilience4j等の外部ライブラリ依存 |
| Testing | Medium | 2/5 | 状態遷移テストが複雑 |
| Value for POC | High | 2/5 | POC規模ではオーバーエンジニアリング |

**Final Verdict**: シンプルなグレースフルデグラデーションで十分

**Revisit Trigger**: 本番環境での高頻度な一時的エラー発生、マイクロサービスアーキテクチャへの移行

---

## Retry with Exponential Backoff

**Category**: Resilience Pattern

**Considered For**: D27 Cosmos DB接続エラーハンドリング

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Latency Impact | High | 2/5 | リトライごとにレスポンス時間増加 |
| Infinite Loop Risk | Medium | 1/5 | 永続的エラー時のリスク |
| Complexity | Low | 3/5 | 実装自体はシンプル |
| Value for Optional Service | High | 2/5 | オプショナルサービスには過剰 |

**Final Verdict**: オプショナルサービスにはスキップフォールバックが適切

**Revisit Trigger**: Cosmos DBがコアサービスに昇格した場合、ネットワーク不安定環境

---

## Fail Fast Pattern

**Category**: Error Handling Pattern

**Considered For**: D27 エラーハンドリング

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| User Experience | High | 1/5 | オプショナル機能で全体エラーはUX悪化 |
| Core Functionality | High | 1/5 | RAG検索・回答生成も停止してしまう |
| Simplicity | Low | 5/5 | 実装は最もシンプル |
| Debugging | Medium | 4/5 | エラー原因が明確 |

**Final Verdict**: オプショナルサービスのエラーでコア機能を停止させるのは不適切

**Revisit Trigger**: Cosmos DBがコアサービスに昇格した場合

---

## 単純Booleanフラグによる状態管理

**Category**: Implementation Pattern

**Considered For**: D27 接続状態管理

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| State Clarity | High | 2/5 | 「False」が未接続かエラーか不明 |
| Debugging | High | 2/5 | ログでの原因特定が困難 |
| Future Extension | Medium | 2/5 | 状態追加時に破綻的変更 |
| Simplicity | Low | 5/5 | 最もシンプル |

**Final Verdict**: Enumによる明示的な状態管理が保守性で優位

**Revisit Trigger**: 極めてシンプルなスクリプト・ツール用途

---

# 以下は既存のTradeoff Records（省略せず含める）

<!-- D25以前の記録は実際のファイルから継続 -->
