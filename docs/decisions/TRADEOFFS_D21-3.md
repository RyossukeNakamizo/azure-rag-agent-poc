# Tradeoff Analysis - D21-3

## Chunk Splitting (391 chars)

**Category**: Data Preprocessing Strategy

**Considered For**: Groundedness改善（0.67 → 0.85目標）

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Search Accuracy | High | 2/5 | Top-5で4.7%カバレッジ、情報損失 |
| Context Preservation | High | 2/5 | 391文字では文脈断片化 |
| Implementation Cost | Medium | 4/5 | 実装は簡単だが効果なし |
| Groundedness Impact | High | 1/5 | -12%悪化（0.67→0.59） |

**Final Verdict**: 文脈の連続性喪失により検索精度が低下。チャンク分割は現状では逆効果。

**Detailed Analysis**

### 期待vs現実
```
期待: TF-IDFスコア向上 → 検索精度up → Groundedness up
現実: 文脈断片化 → 検索精度down → Groundedness down
```

### 数値比較

| メトリクス | D21-2 (1,698文字) | D21-3 (391文字) | 変化 |
|-----------|------------------|----------------|------|
| Groundedness | 0.67 | 0.59 | -12% ❌ |
| チャンク数 | 22 | 106 | +382% |
| Top-5カバレッジ | 22.7% | 4.7% | -79% |
| 平均文字数 | 1,698 | 391 | -77% |

### 失敗の本質

1. **検索カバレッジの崩壊**
   - 22チャンク時: Top-5 = 22.7%カバー
   - 106チャンク時: Top-5 = 4.7%カバー
   - 結果: 重要情報がTop-5に入らない

2. **文脈の断片化**
   - 例: 「Azure AI Searchの設定方法」
   - 1,698文字: 完全な手順が1チャンクに収まる
   - 391文字: 手順がChunk 1-4に分散、Top-5で一部のみヒット

3. **オーバーラップ不足**
   - 50文字のオーバーラップでは文の途中で切断
   - 最低でも100-150文字必要

**Revisit Trigger**
- Top-Kを10-20に増やせる場合
- チャンクサイズを700-1000文字に調整する場合
- Hybrid Searchのweightを調整できる場合

---

## Alternative: Semantic Ranker

**Category**: Search Enhancement

**Considered For**: 同じくGroundedness改善

**Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Search Accuracy | High | 4/5 | BM25 + セマンティックで精度向上 |
| Implementation Cost | High | 5/5 | 設定変更のみ |
| Latency Impact | Medium | 3/5 | +200ms程度 |
| Cost | Medium | 3/5 | 追加課金あり |

**Status**: 次フェーズで検証

**Expected Impact**: Groundedness 0.67 → 0.75-0.80

---

## Alternative: RAGAS Evaluation Framework

**Category**: Evaluation Methodology

**Considered For**: より詳細な問題分析

**Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Evaluation Depth | High | 5/5 | 7種類のメトリクス |
| Setup Complexity | High | 2/5 | Managed Identity統合課題 |
| Actionability | High | 4/5 | 改善箇所を明確に特定 |
| Time Cost | Medium | 2/5 | 60-90分のセットアップ |

**Status**: Semantic Ranker後に検討

**Condition**: Semantic Rankerで0.85未達の場合のみ
