# D21-4 Decision Log: Prompt Engineering強化

## 2024-12-26: Prompt Engineering Implementation

**Status**: Accepted with Trade-offs

**Context**:
- Semantic Ranker実装を延期（Basic SKU制約、コスト+$175/月）
- 代替戦略としてPrompt Engineering強化を採用
- 現在のHybrid Search性能: Coherence 1.000, Relevance 0.984, Groundedness 0.592

**Decision**: 
改善版システムプロンプトを採用（app/api/routes/rag.py）

**主要変更**:
1. コンテキスト評価基準を3項目で明文化
   - 質問との直接的関連性（最重要）
   - 情報の新しさ・正確性
   - 具体的実装例の有無

2. 回答ルールを7項目に拡張
   - コンテキスト不足時の明示的対応
   - 矛盾情報の両論併記
   - ソース引用の必須化
   - 技術的正確性の担保
   - 実用性重視

3. 回答フォーマット統一
   - 簡潔な要約（1-2文）
   - 詳細な説明
   - 実装例（該当する場合）
   - 参照元の明記

**Evaluation Results** (25項目データセット):

| Metric | D21-3 | D21-4 | Change | Interpretation |
|--------|-------|-------|--------|----------------|
| Coherence | 1.000 | 1.000 | ±0.0% | 論理的一貫性維持 |
| Relevance | 0.984 | 0.780 | -20.7% | 過度に厳格な回答基準 |
| Groundedness | 0.592 | 0.820 | +38.5% | コンテキスト遵守度向上 |

**Trade-off Analysis**:

✅ **成功した改善**:
- Groundedness +38.5%: 「提供されたコンテキストのみを使用」ルールが効果的
- 推測や一般知識での補完を排除
- 検証可能な情報提供という本来目標を達成

⚠️ **意図しないトレードオフ**:
- Relevance -20.7%: プロンプトが過度に厳格
- コンテキスト不足時に「答えられない」と正直に回答
- D21-3では一般知識で補完していたが、D21-4では誠実性を優先

**Acceptance Rationale**:
1. RAGシステムの本質は「検証可能な情報提供」
2. Groundedness向上はシステム信頼性の核心
3. Relevance低下は「誠実な回答」の結果であり、ハルシネーション防止の証
4. 本番環境では**正確性 > 回答率**の原則を採用
5. ユーザーに「コンテキスト不足」を明示することで透明性確保

**Alternatives Considered**:

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| プロンプトロールバック | Relevance回復 | Groundedness低下 | 信頼性を犠牲にできない |
| バランス調整版プロンプト | 両立の可能性 | 追加工数・不確実性 | D21-4スコープ外 |

**Consequences**:
- 短期: 一部クエリで「情報不足」回答が増加（想定内）
- 中期: ユーザーフィードバックに基づきプロンプト微調整
- 長期: インデックス拡充（100項目→1000項目）によりカバレッジ向上で解決

**Validation**:
- 25項目評価データセットで定量測定完了
- トレードオフを数値化し、意思決定の透明性を確保
- 簡易テスト（3項目）で改善効果を事前確認

**Cost Impact**:
- プロンプト変更: $0（既存リソース活用）
- 評価実行: 約$0.50（LLM API呼び出し）
- Total: Semantic Rankerの1/350のコスト

**Revisit Trigger**:
- Relevanceが0.7を下回った場合
- ユーザーから「回答不足」フィードバックが月10件超
- インデックス拡充（Week 4）完了後に再評価
