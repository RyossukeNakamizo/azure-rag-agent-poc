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
