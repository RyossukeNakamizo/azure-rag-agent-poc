# Decision Log - D21-3

## 2025-12-25: Chunk Splitting Strategy (REJECTED)

**Status**: Rejected

**Context**
- 課題: Groundedness 0.67 → 0.85への改善
- 仮説: 長いチャンク（1,698文字）→ TF-IDFスコア希薄化
- 戦略: 425文字×4チャンクに分割で情報密度最適化

**Decision**
- チャンクサイズ: 425文字
- オーバーラップ: 50文字
- 実装: split_chunks_v1.py

**Alternatives Considered**

| Option | Pros | Cons | Result |
|--------|------|------|--------|
| 391文字チャンク | TF-IDF改善期待 | 文脈断片化 | Groundedness 0.59 (-12%) ❌ |
| 700文字チャンク | バランス型 | 未検証 | 保留 |
| 1,698文字維持 | 安定性 | 低密度 | 0.67（現ベスト） ✅ |

**Consequences**
- Groundedness: 0.67 → 0.59 (-12%悪化)
- チャンク数: 22 → 106 (+4.8倍)
- 検索カバレッジ: Top-5で4.7%のみ（106中5）

**Root Cause Analysis**
1. **文脈の連続性喪失**: 391文字では完全な説明が単一チャンクに収まらない
2. **検索精度低下**: 重要情報が複数チャンクに分散、Top-5でヒットせず
3. **最適値の誤算**: Azure推奨500-1000文字を下回る

**Validation**
- 評価データ: test_qa_ai_search_only.json（25件）
- 評価方法: LLM-as-Judge（gpt-4o）
- 再現性: 3回測定で±0.02以内

**Lessons Learned**
1. チャンクサイズは「短い＝良い」ではない
2. 情報密度と文脈保持はトレードオフ
3. 検索システムではTop-Kとチャンク総数のバランスが重要

**Next Actions**
1. **Immediate**: 1,698文字版インデックスに復帰（ロールバック）
2. **Phase 1**: Semantic Ranker有効化（検索精度向上）
3. **Phase 2**: RAGAS評価（詳細分析）

**References**
- D21-2: 1,698文字版で0.67達成
- Azure AI Search推奨: 500-1000文字/チャンク
- RAGAS Framework: https://github.com/explodinggradients/ragas
