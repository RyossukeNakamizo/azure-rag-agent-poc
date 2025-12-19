# Architecture Overview

> システム設計の思想と制約条件を記録します。
> Day 16更新: AI Foundry複雑なIdentity構成の完全解明

---

## Design Principles

1. **Security First**: Managed Identity優先、API Keyは最終手段
2. **Identity Completeness**: すべてのIdentity経路にRBAC設定（Day 16学習）
3. **Configuration Duality**: IAM + リソース側設定の両方が必須（Day 16発見）
4. **Cost Awareness**: 従量課金の影響を常に考慮
5. **Observability**: Application Insightsによる可視化を標準装備
6. **Simplicity**: 必要十分な構成、過度な抽象化を回避
7. **Azure Native**: 公式SDKとサービスを優先

---

## System Context (Updated 2024-12-19)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Azure AI Foundry                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              4-Identity Architecture                   │     │
│  │                                                        │     │
│  │  1. User Identity                                      │     │
│  │     ↓ (手動操作)                                        │     │
│  │     Portal/CLI → AI Search, Hub Management            │     │
│  │                                                        │     │
│  │  2. AI Hub Managed Identity                           │     │
│  │     ↓ (プロジェクト管理)                                │     │
│  │     Project Resource Creation, Configuration          │     │
│  │                                                        │     │
│  │  3. Azure OpenAI Managed Identity ⚠️ Key Discovery    │     │
│  │     ↓ (RAG実行)                                        │     │
│  │     AI Search Query, Embedding Generation             │     │
│  │                                                        │     │
│  │  4. Search Service Managed Identity                   │     │
│  │     ↓ (Indexer自動処理)                                │     │
│  │     Blob Storage Data Ingestion                       │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Azure OpenAI │───▶│  AI Search   │───▶│ Blob Storage │      │
│  │  (GPT-4o)    │    │ (Hybrid RAG) │    │  (Data Lake) │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                            │                                     │
│                            ▼                                     │
│                   ┌──────────────────┐                          │
│                   │ Application      │                          │
│                   │ Insights         │                          │
│                   └──────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Identity Architecture (Day 16 Complete Discovery)

### 4-Identity RBAC Matrix

| Identity | 用途 | AI Search Roles | 追加 Roles |
|----------|------|----------------|-----------|
| **User Identity** | 手動操作 | • Search Index Data Contributor | • AI Hub: Contributor |
| **AI Hub MI** | プロジェクト管理 | • Search Service Contributor<br>• Search Index Data Reader | • Subscription: Reader |
| **Azure OpenAI MI** ⚠️ | RAG実行 | • Search Service Contributor<br>• Search Index Data Reader | - |
| **Search Service MI** | Indexer | - | • Storage: Blob Data Reader |

### Identity Discovery Timeline (Day 16)

```
Time 0:   初期想定: User + AI Hub MI の2つで十分
Time 15:  エラー発生: "Azure OpenAI MI lacks roles"
Time 30:  調査完了: 4つのIdentity存在を確認
Time 45:  設定完了: 包括的RBAC適用成功

Key Insight:
AI Foundryは用途別に自動的にIdentityを切り替える。
エラーメッセージから「どのIdentityが使われているか」を逆算する必要がある。
```

### Complete RBAC Configuration

```bicep
// 1. User Identity RBAC (手動操作用)
resource userSearchRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, 'SearchIndexDataContributor')
  scope: searchService
  properties: {
    principalId: principalId  // User Object ID
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '8ebe5a00-799e-43f5-93ac-243d3dce84a7'  // Search Index Data Contributor
    )
    principalType: 'User'
  }
}

// 2. AI Hub MI RBAC (プロジェクト管理用)
resource hubSearchServiceRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, hubPrincipalId, 'SearchServiceContributor')
  scope: searchService
  properties: {
    principalId: hubPrincipalId  // AI Hub System-assigned MI
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7ca78c08-252a-4471-8644-bb5ff32d4ba0'  // Search Service Contributor
    )
    principalType: 'ServicePrincipal'
  }
}

resource hubSearchIndexRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, hubPrincipalId, 'SearchIndexDataReader')
  scope: searchService
  properties: {
    principalId: hubPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '1407120a-92aa-4202-b7e9-c0e197c71c8f'  // Search Index Data Reader
    )
    principalType: 'ServicePrincipal'
  }
}

// 3. Azure OpenAI MI RBAC (RAG実行用) ⚠️ Day 16 Critical Discovery
resource openaiSearchServiceRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, openaiPrincipalId, 'SearchServiceContributor')
  scope: searchService
  properties: {
    principalId: openaiPrincipalId  // Azure OpenAI System-assigned MI
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7ca78c08-252a-4471-8644-bb5ff32d4ba0'  // Search Service Contributor
    )
    principalType: 'ServicePrincipal'
  }
}

resource openaiSearchIndexRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, openaiPrincipalId, 'SearchIndexDataReader')
  scope: searchService
  properties: {
    principalId: openaiPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '1407120a-92aa-4202-b7e9-c0e197c71c8f'  // Search Index Data Reader
    )
    principalType: 'ServicePrincipal'
  }
}

// 4. Search Service MI RBAC (Indexer用)
resource searchStorageRbac 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, searchPrincipalId, 'BlobDataReader')
  scope: storageAccount
  properties: {
    principalId: searchPrincipalId  // Search Service System-assigned MI
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'  // Storage Blob Data Reader
    )
    principalType: 'ServicePrincipal'
  }
}
```

---

## Critical Configuration Discovery (Day 16)

### Azure AI Search Authentication Settings

**Problem**: IAMロールを正しく設定してもManaged Identity認証が機能しない

**Root Cause**: Search Serviceの`authOptions`設定がManaged Identityを無効化

```bicep
// ❌ 誤った設定（デフォルト）
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  properties: {
    authOptions: {
      apiKeyOnly: {}  // Managed Identity認証が無効
    }
  }
}

// ✅ 正しい設定（Day 16修正）
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  properties: {
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    // 本番環境推奨（Managed Identityのみ）
    // authOptions: {
    //   aad: {
    //     aadAuthFailureMode: 'http401WithBearerChallenge'
    //   }
    // }
  }
}
```

### Two-Layer Authentication Model

AI Foundryでは認証が**2段階**で構成される：

```
Layer 1: IAM Role Assignment (Identity側設定)
├─ Azure Portal: Access Control (IAM)
├─ Bicep: Microsoft.Authorization/roleAssignments
└─ 効果: "このIdentityはこのリソースにアクセス可能"

Layer 2: Resource Authentication Options (リソース側設定)
├─ Azure Portal: Authentication Method
├─ Bicep: properties.authOptions
└─ 効果: "このリソースはどの認証方式を受け入れるか"

⚠️ 両方が正しく設定されて初めて機能する
```

**Day 16の失敗パターン**:
```
✅ Layer 1: IAM Role Assignment完了
❌ Layer 2: authOptions = apiKeyOnly
→ 結果: Managed Identity認証が機能しない
→ エラー: "Authentication failed"
```

---

## Component Responsibilities

| Component | Responsibility | Technology | Identity Used |
|-----------|---------------|------------|---------------|
| API Layer | Request routing, Auth | FastAPI | User Identity |
| AI Foundry Studio | プロジェクト管理 | Azure AI Foundry | AI Hub MI |
| RAG Execution | Hybrid retrieval | Azure AI Search | **Azure OpenAI MI** ⚠️ |
| Embedding | Text vectorization | Azure OpenAI ada-002 | Azure OpenAI MI |
| LLM | Response generation | Azure OpenAI GPT-4o | Azure OpenAI MI |
| Indexer | 自動データ取込 | Azure AI Search | Search Service MI |
| Monitoring | Metrics, Logs, Traces | Application Insights | All Identities |
| Infrastructure | Resource provisioning | Bicep | User Identity |

---

## Data Flow with Identity Context

```
1. User Query (User Identity)
   │
   ▼
2. AI Foundry Studio (AI Hub MI)
   │
   ├──▶ 3a. RAG Execution Request → Azure OpenAI (Azure OpenAI MI)
   │         │
   │         ├──▶ 3b. Generate Embedding (Azure OpenAI MI)
   │         │         │
   │         │         ▼
   │         │    3c. Hybrid Search (AI Search) ⚠️ Azure OpenAI MI使用
   │         │         │
   │         │         ▼
   │         │    3d. Retrieve Top-K Documents
   │         │
   │         ▼
   │    3e. Construct Prompt with Context
   │
   ▼
4. Generate Response (Azure OpenAI GPT-4o)
   │
   ▼
5. Return to User (with source citations)

並行処理:
- Indexer (Search Service MI)
  └─▶ Blob Storage → AI Search Index
```

---

## Constraints (Updated)

| Constraint | Reason | Impact | Day 16 Discovery |
|------------|--------|--------|------------------|
| Japan East region | データレジデンシー要件 | 一部サービス制限 | - |
| No API keys | セキュリティポリシー | 4-Identity RBAC必須 | authOptions設定も必須 |
| Public endpoint | 開発フェーズ | 本番はPrivate Endpoint | - |
| Single replica | コスト最適化 | 可用性99.5%で妥協 | - |
| 4-Identity RBAC | AI Foundryアーキテクチャ | 設定複雑性増加 | **新制約** |

---

## Quality Attributes

| Attribute | Target | Measurement | Day 16 Impact |
|-----------|--------|-------------|---------------|
| Latency (P50) | < 1s | Application Insights | - |
| Latency (P95) | < 3s | Application Insights | - |
| Availability | 99.5% | Azure Monitor | Identity障害で低下リスク |
| Error Rate | < 1% | Application Insights | RBAC不足で一時100% |
| RBAC Setup Time | < 30min | Manual tracking | Day 16: 90分（診断含む） |
| Monthly Cost | < ¥50,000 | Cost Management | RBAC設定は無料 |

---

## Security Architecture (Complete - Day 16)

```
┌───────────────────────────────────────────────────────────────┐
│              Complete Authentication Flow                      │
│                                                               │
│  Portal/CLI (User Identity)                                   │
│      │                                                        │
│      ├──(IAM + authOptions)──▶ AI Search ✅                   │
│      └──(IAM)──▶ AI Hub Management ✅                         │
│                                                               │
│  AI Hub MI                                                    │
│      │                                                        │
│      ├──(IAM + authOptions)──▶ AI Search ✅                   │
│      └──(IAM)──▶ Project Management ✅                        │
│                                                               │
│  Azure OpenAI MI ⚠️ Critical Path                             │
│      │                                                        │
│      ├──(IAM + authOptions)──▶ AI Search ✅                   │
│      └──(Internal)──▶ Embedding/LLM ✅                        │
│                                                               │
│  Search Service MI                                            │
│      │                                                        │
│      └──(IAM)──▶ Blob Storage ✅                              │
│                                                               │
│  Required Settings:                                           │
│  1. IAM Roles (4 Identities × 2-3 Roles)                     │
│  2. authOptions = aadOrApiKey (Search Service)                │
│  3. Managed Identity Enabled (All Resources)                  │
└───────────────────────────────────────────────────────────────┘
```

### RBAC Roles Reference

| Service | Role Name | Role ID | Assigned To |
|---------|-----------|---------|-------------|
| AI Search | Search Service Contributor | 7ca78c08-252a-4471-8644-bb5ff32d4ba0 | Hub MI, OpenAI MI |
| AI Search | Search Index Data Contributor | 8ebe5a00-799e-43f5-93ac-243d3dce84a7 | User Identity |
| AI Search | Search Index Data Reader | 1407120a-92aa-4202-b7e9-c0e197c71c8f | Hub MI, OpenAI MI |
| Storage | Storage Blob Data Reader | 2a2b9908-6ea1-4ae2-8e65-a410df84e7d1 | Search Service MI |
| AI Hub | Contributor | b24988ac-6180-42a0-ab88-20f7382dd24c | User Identity |

---

## Troubleshooting Playbook (Based on Day 16)

### Identity-Related Errors

#### Error: "Azure OpenAI MI lacks roles"

**診断手順**:
```bash
# 1. エラーメッセージから使用されているIdentityを特定
# → "Azure OpenAI resource system assigned managed identity"

# 2. 該当リソースのManaged Identity確認
az cognitiveservices account identity show \
  --name <openai-name> \
  --resource-group <rg-name> \
  --query principalId -o tsv

# 3. AI SearchへのRBAC確認
az role assignment list \
  --assignee <openai-principal-id> \
  --scope <search-resource-id> \
  --query "[].{Role:roleDefinitionName, Scope:scope}" -o table

# 4. authOptions確認
az search service show \
  --name <search-name> \
  --resource-group <rg-name> \
  --query authOptions -o json
```

**解決策**:
1. 不足しているRBACロールを追加
2. authOptions が Managed Identity対応か確認
3. 権限伝播を5-10分待機
4. 再テスト

**所要時間**: 15-20分（診断含む）

---

## Future Considerations

| Item | Priority | Trigger Condition | Day 16 Notes |
|------|----------|-------------------|--------------|
| Bicep IaC完全自動化 | **High** | Day 17実施予定 | 手動設定からの移行 |
| Private Endpoint | High | 本番環境移行時 | - |
| Multi-region | Medium | 可用性99.9%要件時 | Identity複製必要 |
| Semantic Ranker | Low | 検索精度向上要求時 | - |
| GPT-4o-mini | Medium | コスト削減要求時 | - |
| Identity監視 | **High** | Day 17実装推奨 | 権限エラー早期検知 |

---

## Day 16 Key Learnings

### 1. Multiple Identity Paths
AI Foundryは単一Identityではなく、用途別に複数Identityを自動使用。エラーメッセージから「どのIdentityか」を特定する診断力が重要。

### 2. Two-Layer Authentication
IAMロール割り当て（Identity側）だけでは不十分。リソース側の`authOptions`設定も必須。

### 3. Discovery Time Investment
45分の診断時間は「コスト」ではなく「投資」。複雑なアーキテクチャの完全理解により、将来の類似問題を数分で解決可能になる。

### 4. Documentation Value
実装だけでなく、判断過程（DECISIONS.md）と却下理由（TRADEOFFS.md）を記録することで、面接時の説得力が劇的に向上。

---

## References

- [Azure AI Foundry RBAC Documentation](https://learn.microsoft.com/azure/ai-studio/concepts/rbac-ai-studio)
- [Azure AI Search Authentication](https://learn.microsoft.com/azure/search/search-security-rbac)
- [Managed Identity Best Practices](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/managed-identities-best-practice-recommendations)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/)
- [Day 16 Session Summary](./SESSION_SUMMARY_DAY16.md)
- [Day 16 Decisions](./DECISIONS.md)
- [Day 16 Tradeoffs](./TRADEOFFS.md)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2024-12-15 | Initial architecture | Day 15 |
| 2.0 | 2024-12-19 | **Complete 4-Identity RBAC discovery** | Day 16 |
| | | - Azure OpenAI MI存在の発見 | |
| | | - authOptions設定の重要性 | |
| | | - Two-Layer認証モデルの確立 | |
| | | - トラブルシューティングプレイブック追加 | |
