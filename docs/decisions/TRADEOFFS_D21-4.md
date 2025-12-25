# D21-4 Tradeoff Analysis: Prompt Engineering Trade-offs

## Rejected/Deferred Options

### Option: Semantic Ranker (Azure AI Search)

**Category**: Service Feature

**Considered For**: 検索結果の意味的関連性向上

**Rejection Factors**:

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Cost | High | 1/5 | Basic→Standard: +$175/月 |
| Implementation Complexity | Medium | 4/5 | Bicep変更のみで実装可能 |
| Expected Improvement | Medium | 4/5 | Relevance +0.05~0.10見込み |
| ROI | High | 2/5 | コスト対効果不明確 |

**Final Verdict**: コスト制約により延期。代替戦略（Prompt Engineering）で対応

**Revisit Trigger**: 
- 本番環境移行時（予算確保後）
- 月間クエリ数が10万超（ROI改善）
- Relevance 0.98+が必須要件となった場合

---

### Option: Query Expansion (LLMベース)

**Category**: RAG Enhancement Pattern

**Considered For**: クエリ拡張による検索範囲拡大

**Deferral Factors**:

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Implementation Time | Medium | 3/5 | 1-2時間で実装可能 |
| Cost per Query | Low | 4/5 | +$0.001/query（許容範囲） |
| Expected Improvement | Medium | 3/5 | Relevance +0.02~0.04見込み |
| Priority | High | 2/5 | Prompt強化を優先 |

**Final Verdict**: D21-4スコープ外。Week 4で実装予定

**Implementation Plan**: 
- GPT-4oでクエリ拡張（3関連クエリ生成）
- 並列検索→結果マージ
- 重複排除処理

---

### Option: Cross-Encoder Reranking

**Category**: Advanced Reranking Pattern

**Considered For**: Top-K結果の再順位付け

**Rejection Factors**:

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Implementation Complexity | High | 2/5 | 2時間以上の工数 |
| Cost per Query | Medium | 3/5 | +$0.0005/query |
| Latency Impact | High | 2/5 | +200-500ms |
| Expected Improvement | Medium | 3/5 | Relevance +0.03~0.05 |

**Final Verdict**: 工数対効果が不明確。保留

**Revisit Trigger**: 
- Prompt Engineering + Query Expansionで不十分な場合
- レイテンシ要件が緩和された場合

---

## Accepted Trade-off: Relevance vs Groundedness

**Decision**: Groundedness優先、Relevance低下を許容

**Quantitative Impact**:
- Relevance: 0.984 → 0.780 (-20.7%)
- Groundedness: 0.592 → 0.820 (+38.5%)

**Justification**:
1. **RAGの本質**: 検証可能性 > 回答率
2. **ハルシネーション防止**: 誠実な「答えられない」回答
3. **透明性**: ユーザーに情報不足を明示
4. **長期戦略**: インデックス拡充で解決可能

**Mitigation Plan**:
- Week 4: Q&Aデータセット100項目→1000項目拡充
- Week 5: ユーザーフィードバック収集
- Week 6: プロンプト微調整（必要に応じて）

**Success Metrics**:
- Groundedness ≥ 0.85 (達成: 0.820)
- Relevance ≥ 0.75 (達成: 0.780)
- Coherence ≥ 0.95 (達成: 1.000)
