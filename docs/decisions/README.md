# Architecture Decision Records (ADR)

> 技術選定の判断履歴を時系列で記録します。

このディレクトリには、プロジェクトの重要な技術的意思決定を記録したADR（Architecture Decision Records）が格納されています。

---

## ADRとは

ADRは以下の要素を含む軽量な設計ドキュメントです：

- **Context**: 解決すべき課題、制約条件
- **Decision**: 選択した技術・設計
- **Alternatives**: 検討したが却下した選択肢
- **Consequences**: この決定による影響、将来のリスク
- **Validation**: 検証方法と結果

---

## 決定履歴一覧

| ID | Date | Title | Status |
|----|------|-------|--------|
| 001 | 2024-12-18 | [Embedding Model Selection](001-2024-12-18-embedding-model.md) | ✅ Accepted |
| 002 | 2024-12-18 | [Search Algorithm Selection](002-2024-12-18-search-algorithm.md) | ✅ Accepted |
| 003 | 2024-12-22 | [Function Calling Design](003-2024-12-22-function-calling.md) | ✅ Accepted |

---

## ADRテンプレート

新しいADRを作成する際は、以下のテンプレートを使用してください。

### ファイル命名規則

```
{序号}-YYYY-MM-DD-{decision-title}.md

例:
004-2024-12-23-fastapi-authentication.md
```

### テンプレート

```markdown
# {序号}. {Decision Title}

**日付**: YYYY-MM-DD  
**ステータス**: Proposed / Accepted / Superseded / Deprecated  
**決定者**: Name  

---

## Context

解決すべき課題と制約条件を記述します。

**課題**:
- 

**制約条件**:
- 

**前提条件**:
- 

---

## Decision

選択した技術・設計を記述します。

**選択内容**:


**理由**:
1. 
2. 
3. 

---

## Alternatives Considered

検討したが却下した選択肢を記述します。

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Option A |  |  |  |
| Option B |  |  |  |

---

## Consequences

### Positive

- 

### Negative

- 

### Risks

- 

---

## Validation

**検証方法**:


**検証結果**:


**成功基準**:
- [ ] 
- [ ] 

---

## Related Decisions

- [ADR-XXX: Related Decision](XXX-YYYY-MM-DD-related.md)

---

## References

- [External Documentation](https://example.com)
- [Internal Document](../guides/development/example.md)
```

---

## ステータス定義

| Status | 意味 |
|--------|------|
| **Proposed** | 提案中、レビュー待ち |
| **Accepted** | 承認済み、実装中または実装完了 |
| **Superseded** | 新しい決定により置き換えられた |
| **Deprecated** | 廃止予定または廃止済み |

---

## 作成ガイドライン

### いつADRを作成するか

以下のような場合にADRを作成します：

1. **技術スタックの選定** (例: Python vs. Node.js)
2. **アーキテクチャパターンの選択** (例: Monolith vs. Microservices)
3. **セキュリティ設計** (例: API Key vs. Managed Identity)
4. **データモデリング** (例: SQL vs. NoSQL)
5. **外部サービスの選定** (例: Azure vs. AWS)

### ADRに含めるべき内容

✅ **含めるべき**:
- 技術的な理由
- ビジネス的な理由
- 定量的な評価（可能な場合）
- 検証結果
- 将来的なリスク

❌ **含めるべきでない**:
- 実装の詳細（→ guides/ に記載）
- 日々の作業ログ（→ sessions/ に記載）
- 変更不可能な決定（→ 制約条件として記載）

---

## レビュープロセス

1. **Draft作成**: 提案者がADRを作成（Status: Proposed）
2. **レビュー**: チームメンバーがレビュー
3. **議論**: 必要に応じて代替案を追加
4. **承認**: 合意が得られたら Status を Accepted に変更
5. **実装**: 決定に基づいて実装を進める

---

## 関連ドキュメント

- [System Architecture](../../ARCHITECTURE.md)
- [Development Guides](../guides/development/)
- [Session Summaries](../sessions/)

---

**次回ADR作成予定**: Day 23-24（FastAPI認証設計）
