# Tradeoff Analysis

> 選択しなかった技術・設計の却下理由を記録します。
> 「なぜやらなかったか」は「なぜやったか」と同等に重要です。

---

## 長いチャンク（1,698文字）による拡充

**Category**: Data Strategy

**Considered For**: インデックス品質改善によるGroundedness向上

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Groundedness改善 | High | 3/5 | 0.67達成も目標0.85未達 |
| 情報密度 | High | 2/5 | TF-IDFスコア希薄化 |
| 実装効率 | Medium | 5/5 | GPT-4oで5分完了 |
| 検索精度 | High | 2/5 | Keywordマッチ低下 |
| スケーラビリティ | Low | 4/5 | 22件なら許容範囲 |

**Total Weighted Score**: 2.8/5.0

**Final Verdict**: 
インデックス拡充は実施したが、期待された効果（0.85+）未達成。コンテンツの「長さ」より「密度」が重要と判明。チャンク分割戦略への切替を推奨。

**Technical Analysis**

```
問題点1: TF-IDFスコアの希薄化
--------
91文字チャンク:
"Azure AI Searchはベクトル検索とキーワード検索を統合"
→ "ベクトル検索" のTF: 1/14トークン = 7.1%

1,698文字チャンク:
"Azure AI Searchは...（500文字の背景）...ベクトル検索と...（800文字）"
→ "ベクトル検索" のTF: 2/250トークン = 0.8%

結果: Keyword類似度スコア -89%低下

問題点2: 情報の間接性
--------
質問: "Azure AI Searchのベクトル検索とは？"

91文字チャンク:
[直接的回答] → LLMが即座に引用可能

1,698文字チャンク:
[背景説明500文字] + [核心100文字] + [詳細800文字]
→ LLMがノイズとシグナルを分離する負荷増
→ Groundedness判定が厳格化

問題点3: Hybrid Searchのバランス崩れ
--------
Vector類似度: 0.85（維持）
Keyword類似度: 0.45（低下）
総合スコア: 0.65（やや低下）
```

**Revisit Trigger**: 
- チャンク分割後もGroundedness 0.70未満の場合
- 質問の複雑度が極端に高い場合（1,698文字の詳細が必要）
- セマンティック検索のみ使用（Keywordマッチ不要）

**Recommended Alternative**: 
チャンク分割戦略（1,698文字 → 425文字×4）で情報密度とカバレッジを両立

---

## 全カテゴリ混在での評価

**Category**: Evaluation Strategy

**Considered For**: RAGシステムの総合的性能評価

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| 包括性 | Medium | 5/5 | 全カテゴリカバー |
| 正確性 | High | 1/5 | インデックスと不整合 |
| 解釈性 | High | 1/5 | ノイズ大、誤解招く |
| 実装コスト | Low | 5/5 | データセット既存 |
| 実用性 | High | 1/5 | 改善指針不明確 |

**Total Weighted Score**: 1.8/5.0

**Final Verdict**: 
インデックスが1カテゴリ（Azure AI Search）のみをカバーする状況で、5カテゴリ混在評価は不正確。Groundedness 0.150という誤解を招く値を生成。カテゴリ別評価を標準化。

**Impact Analysis**

```
100件混在評価の結果:
-------------------------
全体Groundedness: 0.150

内訳:
- Azure AI Search (25件): 0.580
- Security (25件): 0.020  ← インデックス範囲外
- Infrastructure (20件): 0.000  ← インデックス範囲外
- Python SDK (15件): 0.000  ← インデックス範囲外
- Architecture (15件): 0.000  ← インデックス範囲外

問題点:
1. 全体平均0.150は「システム失敗」と誤解
2. 実際は75件が「正常なスコア0」（範囲外検出）
3. 真の性能0.58が埋没

正しい解釈:
- インデックス内カテゴリ: 0.58（合格）
- カテゴリ外検出: 正常動作
```

**Revisit Trigger**: 
全カテゴリのインデックス拡充が完了した場合のみ

**Recommended Alternative**: 
カテゴリ別評価を標準プロセス化し、各カテゴリ独立にベンチマーク

---

## D21実績0.76の追求

**Category**: Benchmark Strategy

**Considered For**: 過去の成功指標への回帰

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| 再現性 | High | 1/5 | 評価条件不明 |
| 信頼性 | High | 2/5 | 出所未確認 |
| 実装コスト | Medium | 1/5 | 条件特定に時間 |
| 学習価値 | Medium | 4/5 | 差異分析は有益 |
| 目標適合性 | High | 3/5 | 0.76 < 0.85目標 |

**Total Weighted Score**: 2.2/5.0

**Final Verdict**: 
D21実績0.76の評価条件が不明（ファイル未発見、Azure AI Foundry UI可能性）。再現より新たなベースライン0.67確立を優先。

**Investigation Summary**

```
調査実施項目:
-------------
✅ ローカル評価ファイル検索
   → 12月24-25日のファイルのみ（D21該当なし）

✅ タイムスタンプ分析
   - evaluation_with_context: 12/25 14:46
   - evaluation_test: 12/25 14:42
   → どちらもD21後の作成

❓ 未確認項目:
   - Azure AI Foundry UIの評価履歴
   - 過去のGitログ（メタプロンプトの出所）
   - D21のデータセット内容

仮説:
1. D21は Azure AI Foundry UI で実施
   - ローカルファイル非保存
   - より寛容な評価基準の可能性

2. D21は少数件（3-5件）の厳選データ
   - 簡単な質問で高スコア達成
   - 25件の多様な質問で低下

3. 評価関数の違い
   - D21: 異なる評価プロンプト
   - D21-2: batch_evaluation_v8.py（厳格）
```

**Revisit Trigger**: 
- Azure AI Foundry UIで過去の評価履歴を発見
- D21のデータセットが特定可能
- 0.76再現の実用的価値が明確化

**Recommended Alternative**: 
現状のベースライン0.67を起点に、0.85+達成の新戦略を構築

---

## Semantic Rankerの有効化

**Category**: Service Feature

**Considered For**: 検索精度向上によるGroundedness改善

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| 効果期待値 | High | 3/5 | +5-10%改善見込み |
| コスト | High | 2/5 | 追加課金発生 |
| 実装容易性 | Medium | 5/5 | 設定変更のみ |
| 根本解決性 | High | 2/5 | チャンク問題は未解決 |
| 可逆性 | Low | 5/5 | 簡単に無効化可能 |

**Total Weighted Score**: 2.8/5.0

**Final Verdict**: 
Semantic Rankerは対症療法であり、チャンクサイズの根本問題を解決しない。コスト増を伴うため、無料での改善策（チャンク分割）を優先。

**Cost-Benefit Analysis**

```
Semantic Ranker 有効化:
-----------------------
推定月額コスト: ¥5,000-¥10,000
期待改善: Groundedness 0.67 → 0.72 (+7%)
ROI: 低（0.85目標に未達）

チャンク分割戦略:
-----------------
追加コスト: ¥0（実装工数のみ）
期待改善: Groundedness 0.67 → 0.78 (+16%)
ROI: 高

結論: チャンク分割を先行実施
```

**Revisit Trigger**: 
- チャンク分割後も0.75未満
- コスト予算に余裕がある
- セマンティック検索特化の要件

---

## 新規ドキュメント追加による拡充

**Category**: Data Strategy

**Considered For**: インデックスカバレッジの拡大

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| カバレッジ向上 | Medium | 5/5 | 全カテゴリ対応可能 |
| 実装工数 | High | 1/5 | 100件×30分=50時間 |
| 品質保証 | High | 2/5 | レビュー負荷大 |
| 優先度 | High | 2/5 | AI Search改善が先 |
| 保守性 | Medium | 2/5 | 継続的更新必要 |

**Total Weighted Score**: 2.2/5.0

**Final Verdict**: 
現状の優先度はAzure AI Searchカテゴリの0.85+達成。他カテゴリの拡充は成功後に実施。

**Scope Analysis**

```
必要なドキュメント数:
--------------------
Security & Identity: 25件 × 1,500文字
Infrastructure: 20件 × 1,500文字
Python SDK: 15件 × 1,500文字
Architecture: 15件 × 1,500文字

合計: 75件の新規作成

工数見積:
- ドキュメント作成: 75件 × 20分 = 25時間
- ベクトル生成: 75件 × 2分 = 2.5時間
- レビュー: 75件 × 10分 = 12.5時間
--------------------------
総工数: 40時間
```

**Revisit Trigger**: 
- Azure AI Searchで0.85+達成
- 他カテゴリの性能評価が必要
- 包括的RAGシステム構築フェーズ

**Recommended Alternative**: 
段階的拡充（Azure AI Search → 次点カテゴリ → ...）

---

## 評価プロンプトの緩和

**Category**: Evaluation Strategy

**Considered For**: Groundednessスコアの向上

**Rejection Factors**

| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| スコア向上 | Low | 5/5 | 確実に上昇 |
| 誠実性 | High | 1/5 | 見せかけの改善 |
| 学習価値 | High | 1/5 | 真の問題隠蔽 |
| 実装容易性 | Medium | 5/5 | プロンプト編集のみ |
| 長期的価値 | High | 1/5 | 本質的改善なし |

**Total Weighted Score**: 1.6/5.0

**Final Verdict**: 
評価基準の緩和は、真の性能改善ではなく自己欺瞞。厳格な評価を維持し、実質的改善を追求。

**Ethical Consideration**

```
誘惑: "Groundedness 0.5以上なら合格" に基準変更
     → 即座に目標達成

問題点:
1. ステークホルダーへの誤情報
2. 本質的課題の放置
3. 将来的な品質劣化リスク

原則: "Measure what matters, don't game the metrics"
```

**Revisit Trigger**: 
絶対に実施しない（倫理的理由）

---

## Template（次回用）

### [Rejected Option Name]

**Category**: Architecture / Library / Service / Pattern

**Considered For**: 検討目的

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Cost | High/Medium/Low | 1-5 | ... |
| Performance | High/Medium/Low | 1-5 | ... |
| Maintainability | High/Medium/Low | 1-5 | ... |

**Final Verdict**: 却下理由（1-2文）

**Revisit Trigger**: 再検討条件
