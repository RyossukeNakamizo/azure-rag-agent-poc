# Decision Log

> 技術選定の判断履歴を時系列で記録します。
> 形式: ADR (Architecture Decision Records) 準拠

---

## 2024-12-19: AI Foundry Multi-Identity RBAC Architecture

**Status**: Accepted

**Context**
- AI Search接続で継続的な権限エラー発生
- 初期診断: User/AI Hub MIへのRBAC設定のみ実施済み
- エラーメッセージ: "Azure OpenAI resource system assigned managed identity miss the following roles to the Azure AI Search resource"
- AI Foundry Studio経由でのデータ接続作成が失敗
- Day 15で基本的なRBAC設定（User Identity中心）は完了していた

**Problem Analysis**
AI Foundryは単一のManaged Identityではなく、**複数のIdentity経路**でリソースアクセスを行う：
1. User Identity: ポータル/CLI操作用
2. AI Hub Identity: プロジェクト管理用
3. **Azure OpenAI Identity: RAG実行用**（見落としポイント）
4. Search Service Identity: Indexer用

加えて、Azure AI Search側の認証設定が不適切：
- `authOptions`: `apiKeyOnly`（Managed Identity認証が無効）
- この設定では、いくらIAMロールを付与してもManaged Identity認証が機能しない

**Decision**
AI Foundry環境における**包括的4-Identity RBAC戦略**を採用：

### Identity別ロール割り当て

#### 1. User Identity
```bash
# 手動操作（Portal/CLI）用
- Azure AI Search: Search Index Data Contributor
- AI Hub: Contributor
```

#### 2. AI Hub Managed Identity
```bash
# プロジェクト管理操作用
- Azure AI Search: Search Service Contributor
- Azure AI Search: Search Index Data Reader
```

#### 3. Azure OpenAI Managed Identity（重要な発見）
```bash
# RAG実行時のSearch接続用
- Azure AI Search: Search Service Contributor
- Azure AI Search: Search Index Data Reader
```

#### 4. Search Service Managed Identity
```bash
# Indexer自動データ取込用
- Storage Account: Storage Blob Data Reader
```

### Azure AI Search設定変更
```bicep
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  properties: {
    authOptions: {
      // apiKeyOnly → aadOrApiKey に変更
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}
```

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| API Key認証のみ | ・設定がシンプル<br>・即座に利用可能 | ・キー漏洩リスク<br>・手動ローテーション必要<br>・監査ログ不十分 | セキュリティポリシー違反 |
| 最小限RBAC（User MIのみ） | ・初期設定最速<br>・理解が容易 | ・AI Foundry内部動作で権限不足<br>・実行時エラー継続 | 根本的に動作しない |
| 手動ロール割り当て（Portal GUI） | ・即座解決（5分）<br>・検証が簡単 | ・IaC化なし<br>・再現性低<br>・ドキュメント化困難 | Day 17でBicep化予定のため一時的に許容 |
| Managed Identity完全分離 | ・責任分離明確<br>・最小権限原則 | ・複雑性増加<br>・トラブルシューティング困難 | AI Foundryアーキテクチャで必須のため採用 |

**Consequences**

### ポジティブな影響
- ✅ AI Foundry Studio完全動作、データ接続成功
- ✅ セキュアなManaged Identity認証確立
- ✅ API Key管理リスクの完全排除
- ✅ 複雑なIdentity構成の完全理解獲得
- ✅ 監査ログによるアクセス追跡可能
- ✅ 自動フィールドマッピング機能が有効化

### ネガティブな影響
- ❌ RBAC設定の複雑性増加（4 Identity × 2-3 Roles = 8-12割り当て）
- ❌ トラブルシューティング診断時間45分要
- ❌ 初期設定の学習コスト増加
- ❌ ドキュメント複雑化

### 将来のリスク
- ⚠️ Bicep IaC未実装のため、環境再構築時に手動作業必要（Day 17で解消予定）
- ⚠️ 新規メンバーへのオンボーディング時の説明コスト増
- ⚠️ Identity追加時の影響範囲分析が必要

**Validation**

### 機能検証
- ✅ AI Foundry Studio接続成功
- ✅ Index自動フィールドマッピング動作確認
- ✅ 権限エラー完全解消
- ✅ データ接続作成フロー完了

### 診断プロセス検証
```bash
# 1. エラーメッセージ分析（10分）
# → Azure OpenAI MIの関与を特定

# 2. Identity列挙（15分）
az ad sp list --filter "displayName eq '<resource-prefix>'" \
  --query "[].{name:displayName, id:id, appId:appId}" -o table
# → 4つのManaged Identity存在確認

# 3. Search Service設定確認（10分）
az search service show --name <search-name> --resource-group <rg-name> \
  --query authOptions -o json
# → authOptions=apiKeyOnly がボトルネックと判明

# 4. 段階的修正と検証（10分）
# → 設定変更後即座に接続成功
```

**Time Investment**
```
診断フェーズ: 45分
├─ エラーメッセージ分析: 10分
├─ Identity構成調査: 15分
├─ authOptions発見: 10分
└─ 仮説検証: 10分

実装フェーズ: 45分
├─ RBAC設定: 30分（4 Identity × 複数ロール）
├─ authOptions変更: 5分
└─ 接続検証: 10分

合計: 90分（予定80分から+10分、113%）
```

**Root Cause Analysis**
```
Why 1: なぜAI Search接続が失敗したのか？
→ Azure OpenAI MIに必要なRBACロールが未設定

Why 2: なぜAzure OpenAI MIへのロールが必要なのか？
→ AI Foundry内部でRAG実行時にこのIdentityを自動使用

Why 3: なぜこのIdentityの存在に気づかなかったのか？
→ AI Foundryのドキュメントで明示されていない内部アーキテクチャ

Why 4: なぜRBAC設定だけでは不十分だったのか？
→ Search ServiceのauthOptions=apiKeyOnlyがManaged Identity認証を無効化

Why 5: なぜこの設定がデフォルトなのか？
→ 後方互換性とAPI Key認証からの段階的移行を考慮
```

**Key Insights**

### 技術的洞察
1. **複数Identity経路の存在**
   - AI Foundryは単一Identityではなく、用途別に複数Identityを自動切り替え
   - エラーメッセージから利用Identityを逆算する必要あり

2. **二段階認証設定の必要性**
   - IAMロール割り当て（Identity側設定）
   - authOptions設定（リソース側設定）
   - **両方が正しく設定されて初めて機能する**

3. **Azure OpenAI MIの特殊性**
   - RAG実行時の「見えないIdentity」
   - ユーザー操作では直接使用しないため、見落としやすい
   - エラーメッセージで初めて存在が明確化

### 面接活用ポイント
**ストーリー構成案**：
```
Q: 複雑な技術問題をどう解決しますか？

A: Day 16のAI Foundry RBAC問題を例にお話しします。

1. 問題の明確化（10分）
   - エラーメッセージから「Azure OpenAI MI」というキーワードを抽出
   - 初期設定でこのIdentityが見落とされていた可能性を仮説化

2. 体系的な調査（15分）
   - az ad sp list で全Managed Identityを列挙
   - 4つのIdentity存在を確認し、役割を整理

3. 設定状態の完全可視化（10分）
   - Search ServiceのauthOptions確認
   - apiKeyOnlyがボトルネックと判明

4. 段階的修正と検証（10分）
   - authOptions変更 → 即座に接続成功
   - 根本原因の二段階構造を理解

結果: 90分で完全解決、かつ複雑なアーキテクチャの完全理解を獲得

学び: エラーメッセージを起点に、体系的な調査と段階的検証を行う
ことで、ドキュメント化されていない内部アーキテクチャも解明可能
```

**Future Improvements**
- [ ] Bicep IaC化（Day 17予定）
- [ ] RBAC設定の自動テストスクリプト作成
- [ ] トラブルシューティングプレイブック作成
- [ ] Identity構成図の視覚化ドキュメント作成

**References**
- [Azure AI Foundry RBAC Documentation](https://learn.microsoft.com/azure/ai-studio/concepts/rbac-ai-studio)
- [Azure AI Search Authentication](https://learn.microsoft.com/azure/search/search-security-rbac)
- [Managed Identity Best Practices](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/managed-identities-best-practice-recommendations)

---

## Template for Future Decisions

### YYYY-MM-DD: [Decision Title]

**Status**: Proposed / Accepted / Superseded / Deprecated

**Context**
- 解決すべき課題
- 制約条件
- 背景情報

**Decision**
- 選択した技術・設計
- 具体的な実装内容

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| A | ... | ... | ... |
| B | ... | ... | ... |

**Consequences**
- ポジティブな影響
- ネガティブな影響
- 将来のリスク

**Validation**
- 検証方法
- 検証結果
- メトリクス

**Time Investment**
- 調査時間
- 実装時間
- 合計時間

**References**
- 関連ドキュメント
- 参考記事
