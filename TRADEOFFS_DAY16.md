# Tradeoff Analysis

> 選択しなかった技術・設計の却下理由を記録します。
> 「なぜやらなかったか」は「なぜやったか」と同等に重要です。

---

## Day 16: AI Foundry RBAC Configuration

### API Key Authentication (Azure AI Search)

**Category**: Security Pattern

**Considered For**: AI Foundry - AI Search接続認証方式

**Context**
AI Foundry StudioからAzure AI Searchへの接続時に、認証方式として以下2つが選択可能：
1. API Key認証（従来方式）
2. Managed Identity認証（推奨方式）

Day 16では当初、Managed Identity設定だけで接続できると想定していたが、実際には複数の見落としがあった。

**Rejection Factors**
| Factor | Weight | Score (1-5) | Notes |
|--------|--------|-------------|-------|
| Security | High | 1/5 | ・キー漏洩リスク常時存在<br>・コードやログへの誤記録リスク<br>・手動ローテーション必要（運用負荷）<br>・キー共有による責任追跡困難 |
| Auditability | High | 2/5 | ・アクセス元の詳細特定困難<br>・IAMログと統合されない<br>・監査証跡が不完全 |
| Scalability | Medium | 2/5 | ・複数Identity管理で煩雑化<br>・環境別キー管理の複雑性<br>・チーム拡大時の配布問題 |
| Cost | Low | 5/5 | ・追加コストなし |
| Setup Speed | Low | 5/5 | ・即座利用可能（唯一の明確な利点）<br>・5分で設定完了 |
| **Total** | - | **2.2/5** | **総合評価: 不採用** |

**Technical Deep Dive**

#### API Key認証の動作フロー
```
Application → [API Key in Header] → AI Search
                                        ↓
                                   [Key Validation]
                                        ↓
                                   [Access Granted]

問題点:
1. API Keyは静的な認証情報
2. 誰が使っても同じキー = 個別追跡不可
3. 漏洩時の影響範囲が広い
```

#### Managed Identity認証の動作フロー
```
Application (MI) → [Azure AD Token Request] → Azure AD
                                                  ↓
                                        [Identity Verification]
                                                  ↓
                                        [Short-lived Token]
                                                  ↓
Application → [Token in Header] → AI Search
                                      ↓
                                [RBAC Check]
                                      ↓
                                [Access Granted]

利点:
1. トークンは短期（1時間程度）で自動更新
2. Identityごとに個別追跡可能
3. RBACで細かい権限制御
```

**Final Verdict**
AI Foundry内部で複数Managed Identityが自動利用されるアーキテクチャのため、API Key認証では一部Identity経路で権限不足が発生する可能性が高い。

加えて、`authOptions=apiKeyOnly`設定では、いくらIAMロールを付与してもManaged Identity認証が機能しない（Day 16で発見）。

**Rejection Summary**:
```
❌ セキュリティリスク（キー管理）
❌ 監査要件を満たさない
❌ AI Foundryの複数Identity構成に不適合
✅ 唯一の利点は初期設定速度のみ
```

**Revisit Trigger**
以下の条件下でのみ、限定的に使用を許容：
- ローカル開発環境での一時的なテスト
- プロトタイプ検証（24時間以内）
- **本番環境では絶対にManaged Identity専用**（`authOptions=aad`）を使用

**Cost of Failure (If Selected)**
- セキュリティ監査で指摘対象
- キー漏洩時のインシデント対応コスト
- コンプライアンス違反リスク

**Discovery Process (Day 16)**
45分の診断で以下を発見：
```
Time 0分: RBAC設定しても接続失敗
Time 15分: エラーメッセージ分析 → Azure OpenAI MIの関与判明
Time 30分: authOptions=apiKeyOnly を発見
Time 40分: authOptions → aadOrApiKey に変更
Time 45分: 接続成功
```

**Key Learning**
> Managed Identity認証は、IAMロール割り当てだけでは不十分。
> リソース側の `authOptions` 設定も必須。

---

### Minimal RBAC Strategy (User Identity Only)

**Category**: Security Architecture Pattern

**Considered For**: AI Foundry RBAC設計

**Context**
Day 15で基本的なRBAC設定を実施した際、User Identityへのロール割り当てのみを行った。これは以下の想定に基づく：
- ユーザーがPortal/CLI経由で操作するため、User Identity権限で十分
- Managed Identityは内部的に自動処理されるため明示的設定不要

**Rejection Factors**
| Factor | Weight | Score (1-5) | Notes |
|--------|--------|-------------|-------|
| Completeness | High | 1/5 | ・AI Foundry内部動作で権限不足頻発<br>・RAG実行時にAzure OpenAI MIが自動使用される<br>・エラーメッセージで初めて不足が判明 |
| Troubleshooting | High | 2/5 | ・実行時エラーで原因特定困難<br>・「権限はあるはずなのに失敗」状態<br>・45分の診断時間が必要 |
| Development Speed | Medium | 4/5 | ・初期設定は最速（15分）<br>・理解が容易 |
| Maintainability | Medium | 2/5 | ・将来の機能追加で追加Identity必要<br>・段階的修正が困難 |
| **Total** | - | **2.0/5** | **総合評価: 不採用** |

**Technical Architecture Comparison**

#### 採用されなかった構成（Minimal RBAC）
```
┌─────────────────────────────────────┐
│         AI Foundry                  │
│                                     │
│  User Identity (RBAC ✅)            │
│    ↓                                │
│  Portal/CLI操作 → AI Search ✅      │
│                                     │
│  AI Hub MI (RBAC ❌)                │
│    ↓                                │
│  内部処理 → AI Search ❌ 権限不足    │
│                                     │
│  Azure OpenAI MI (RBAC ❌)          │
│    ↓                                │
│  RAG実行 → AI Search ❌ 権限不足     │
└─────────────────────────────────────┘

問題点:
- ユーザー操作は成功するが、AI内部処理で失敗
- エラーメッセージが「Azure OpenAI MI lacks roles」
- User Identity権限は無関係
```

#### 採用された構成（Comprehensive 4-Identity RBAC）
```
┌─────────────────────────────────────┐
│         AI Foundry                  │
│                                     │
│  User Identity (RBAC ✅)            │
│  AI Hub MI (RBAC ✅)                │
│  Azure OpenAI MI (RBAC ✅)          │
│  Search Service MI (RBAC ✅)        │
│    ↓                                │
│  すべての経路で AI Search アクセス可 │
└─────────────────────────────────────┘

利点:
- 全機能が正常動作
- Identity別に監査ログで追跡可能
- 将来の機能追加にも対応
```

**Final Verdict**
AI Foundry Studioは内部で複数Managed Identityを自動利用する設計。User Identityのみの設定では、AI内部処理（RAG実行、データ接続作成等）で権限不足エラーが継続発生する。

**Rejection Summary**:
```
❌ AI内部処理で権限不足頻発
❌ エラー原因の特定が困難（45分要）
❌ 段階的修正が必要になり結局時間増
✅ 初期設定速度は最速（唯一の利点）
```

**Revisit Trigger**
なし。AI Foundry利用時は必ず包括的4-Identity RBAC設計が必須。

例外的に、以下の場合のみ段階的設定を許容：
- 学習目的での段階的理解（最終的には完全構成必須）
- 権限エスカレーション攻撃のリスク評価

**Cost of Failure (Day 16 Actual Experience)**
```
診断時間: 45分
├─ エラーメッセージ分析: 10分
├─ Identity構成調査: 15分
├─ 仮説検証: 10分
└─ 追加RBAC設定: 10分

見落とし要因:
- Azure OpenAI MIの存在が非自明
- AI Foundryドキュメントに明記なし
- エラーメッセージで初めて判明

学習価値: 高
- 複雑なIdentity構成の完全理解獲得
- 体系的トラブルシューティング手法の確立
```

**Root Cause of Underestimation**
```
想定: AI Foundry = 単一Identityで動作
現実: AI Foundry = 用途別に複数Identityを自動切り替え

Gap:
- ドキュメントでの明示不足
- 内部アーキテクチャの複雑性
- RAG実行時のIdentity切り替えが不可視
```

---

### Manual Portal Configuration (vs Bicep IaC)

**Category**: Infrastructure Management Pattern

**Considered For**: RBAC設定の実装方法

**Context**
Day 16で複雑なRBAC問題が発覚した際、以下2つのアプローチが考えられた：
1. Portal GUIで手動設定（即座解決）
2. Bicep IaCで自動化（再現性確保）

時間制約（Day 16残り時間30分）を考慮し、一旦Portal手動設定を採用。

**Rejection Factors**
| Factor | Weight | Score (1-5) | Notes |
|--------|--------|-------------|-------|
| Speed | High | 5/5 | ・5-10分で完了<br>・即座に動作検証可能 |
| Reproducibility | High | 1/5 | ・環境再構築時に手動作業必要<br>・手順書なしでは再現困難<br>・人為ミスのリスク |
| Documentation | High | 2/5 | ・実施内容の記録が必要<br>・スクリーンショットベース<br>・コードレビュー不可 |
| Testing | Medium | 1/5 | ・自動テスト不可<br>・手動検証のみ |
| Collaboration | Medium | 2/5 | ・Git管理外<br>・変更履歴なし<br>・レビュープロセスなし |
| **Total** | - | **2.2/5** | **総合評価: 暫定採用** |

**Decision Matrix**

| シナリオ | Portal手動 | Bicep IaC | 選択 |
|---------|-----------|-----------|------|
| 緊急トラブルシューティング | 5分 | 30分 | Portal ✅ |
| 初期環境構築 | 20分 | 40分（初回）→10分（2回目以降） | Bicep ✅ |
| 環境複製 | 20分×N環境 | 10分×N環境 | Bicep ✅ |
| 変更管理 | 記録困難 | Git履歴自動 | Bicep ✅ |

**Final Verdict**
Day 16では時間制約により**一時的に**Portal手動設定を採用。ただし、以下の条件付き：
- Day 17でBicep IaC化を実施（必須）
- 手動設定内容を詳細ドキュメント化
- 次回環境構築時の自動化を保証

**Temporary Acceptance Conditions**:
```
✅ Day 16: Portal手動設定（緊急対応）
⏳ Day 17: Bicep IaC化（再現性確保）
❌ 本番環境: 手動設定は絶対禁止
```

**Revisit Trigger (Day 17 Task)**
以下の条件でBicep IaC化を実施：
- 4-Identity RBAC完全自動化
- authOptions設定の自動化
- 環境変数による柔軟な設定
- CI/CDパイプラインへの統合

**Transition Plan (Day 16 → Day 17)**
```bash
# Day 16 完了状態（手動設定）
Portal: 4 Identities × 2-3 Roles = 手動設定完了
Documentation: DECISIONS.md に記録

# Day 17 移行タスク
1. Bicep RBAC module作成（20分）
2. 既存設定の検証（10分）
3. Bicep再デプロイテスト（15分）
4. ドキュメント更新（5分）

合計: 50分
```

**Cost-Benefit Analysis**
```
Portal手動設定:
- 初期: 10分節約
- 2回目以降: 20分×回数 の時間損失
- ドキュメント作成: 15分
- 総コスト: 10 + 20N + 15 = 25 + 20N 分

Bicep IaC:
- 初期: 30分投資
- 2回目以降: 5分×回数（デプロイ実行のみ）
- ドキュメント自動: 0分（コードが仕様）
- 総コスト: 30 + 5N 分

Break-even point: N = 0.33 (1回目で既にIaCが有利)
```

---

## Key Insights from Day 16 Tradeoffs

### 1. Security > Speed の原則
API Key認証は即座に使えるが、セキュリティリスクが高い。
→ **初期設定に時間をかけてもManaged Identity優先**

### 2. 完全性の重要性
Minimal RBAC は設定が簡単だが、実行時エラーで結局時間増。
→ **最初から包括的設計を採用すべき**

### 3. 自動化への投資
Portal手動設定は即座解決だが、長期的には非効率。
→ **1回でもBicep IaCが有利、2回目以降は圧倒的**

### 4. 失敗からの学習価値
Day 16の45分診断は「コスト」ではなく「投資」。
→ **複雑なアーキテクチャの完全理解 = 将来の高速化**

---

## Template for Future Tradeoffs

### [Rejected Option Name]

**Category**: Architecture / Library / Service / Pattern

**Considered For**: 検討目的

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| ... | High/Medium/Low | 1-5 | ... |

**Final Verdict**: 却下理由（1-2文）

**Revisit Trigger**: 再検討条件

**Cost of Failure**: もし選択していた場合の影響
