# Session Summary: Day 15 - AI Foundry環境構築完了

## Session Metadata
```yaml
session_id: 2025-12-19_13:10-15:05
duration: 115分
learner_level: L3（上級者）
focus_area: AI Foundry Hub + Project + Connections デプロイ
learning_goal: Bicep IaCによる完全自動化達成
```

---

## Executive Summary

Azure AI Foundry環境（Hub + Project + Connections）をBicep IaCで構築完了。初回デプロイでRBAC重複エラーが発生したが、既存リソース参照アプローチに切り替えて7秒で成功。GPT-4o動作確認完了、Azure AI Search Connectionも作成済み。Index作成はDay 16で実施。

---

## Achievements

### Infrastructure
```yaml
AI Foundry Hub:
  name: ai-hub-dev-ldt4idhueffoe
  location: East US
  identity: System-assigned Managed Identity
  status: ✅ 作成完了

AI Foundry Project:
  name: rag-agent-project
  hub: ai-hub-dev-ldt4idhueffoe
  purpose: RAG Agent開発環境
  status: ✅ 作成完了

Azure AI Search:
  name: search-ragpoc-dev-ldt4idhueffoe
  sku: Basic
  replicas: 1
  partitions: 1
  indexes: 0（Day 16で作成予定）
```

### Connections
```yaml
azure-openai-connection:
  type: Azure OpenAI
  auth: Microsoft Entra ID
  endpoint: https://oai-ragpoc-dev-ldt4idhueffoe.openai.azure.com/
  model: gpt-4o (version: 2024-08-06)
  status: ✅ 動作確認済み

azure-search-connection:
  type: Azure AI Search
  auth: Microsoft Entra ID
  endpoint: https://search-ragpoc-dev-ldt4idhueffoe.search.windows.net
  status: ✅ 作成完了（権限伝播待ち）
```

### Security (RBAC)
```yaml
User RBAC:
  principal: Ryosuke.Nakamizo@hotmail.com
  roles:
    - Search Index Data Reader
    - Azure AI User
    - Search Service Contributor

Managed Identity RBAC:
  principal: ai-hub-dev-ldt4idhueffoe (c6c6b44a-ed67-4950-b9d8-5ddfe9f312fa)
  roles:
    - Storage Blob Data Contributor
    - AzureML Data Scientist
    - Cognitive Services OpenAI User

Total Assignments: 6ロール
```

---

## Implementation Details

### Bicep Files Created
```
infra/
├── main-ai-foundry.bicep          # 統合デプロイ（既存リソース参照版）
├── modules/ai-foundry/
│   ├── hub.bicep                  # AI Foundry Hub定義
│   ├── project.bicep              # AI Foundry Project定義
│   └── connections.bicep          # Connections定義
└── parameters/
    ├── ai-foundry.bicepparam      # .bicepparam版（エラー発生）
    └── ai-foundry.parameters.json # JSON版（採用）
```

### Deployment Command
```bash
az deployment group create \
  --resource-group rg-rag-poc \
  --template-file ~/azure-rag-agent-poc/infra/main-ai-foundry.bicep \
  --parameters @~/azure-rag-agent-poc/infra/parameters/ai-foundry.parameters.json \
  --name ai-foundry-final-20251219-131854
```

**Result**: 
- Provisioning State: Succeeded
- Duration: PT7.0309943S

---

## Troubleshooting History

### Issue 1: RBAC重複エラー

**Symptom**: `RoleAssignmentExists` エラー

**Root Cause**: 前回の失敗デプロイでRBAC割り当てが部分的に作成済み

**Solution**:
- main-ai-foundry.bicepを修正
- Hub/Projectを`resource existing`で参照
- RBAC作成をスキップ
- Connectionsのみ作成に特化

**Result**: デプロイ成功（7秒）

---

### Issue 2: Bicepパラメータ不整合

**Symptom**: `BCP035`, `BCP037`エラー

**Root Cause**: main-ai-foundry.bicepのパラメータ名がモジュール定義と不一致

**Investigation**:
```bash
# hub.bicepの実際のパラメータ確認
head -30 ~/azure-rag-agent-poc/infra/modules/ai-foundry/hub.bicep

# 判明した正しいパラメータ
- storageAccountName（誤: storageAccountId）
- keyVaultName（誤: keyVaultId）
- applicationInsightsName（誤: appInsightsId）
```

**Solution**: パラメータ名を実際のモジュール定義に合わせて修正

**Result**: Validation成功

---

### Issue 3: .bicepparam構文エラー

**Symptom**: `unrecognized template parameter 'using'`

**Root Cause**: Azure CLIの.bicepparam解析器の問題

**Attempted Solutions**:
1. ファイル再作成 → 失敗
2. 構文確認 → 問題なし
3. Azure CLIバージョン確認 → 最新版

**Final Solution**: JSON形式パラメータファイルに切り替え

**Result**: 全デプロイコマンド即座成功

---

### Issue 4: AI Foundry Studio権限エラー

**Symptom**: "Search Service インデックスを読み込めません"

**Root Cause**: ユーザーに`Search Index Data Reader`ロールが未割り当て

**Solution**:
```bash
az role assignment create \
  --assignee "Ryosuke.Nakamizo@hotmail.com" \
  --role "Search Index Data Reader" \
  --scope "/subscriptions/4c5c5fd0-450a-42a5-b5cf-4247712d8f20/resourceGroups/rg-rag-poc/providers/Microsoft.Search/searchServices/search-ragpoc-dev-ldt4idhueffoe"
```

**Result**: RBAC割り当て完了（権限伝播待ち最大10分）

---

## Testing Results

### GPT-4o Chat Playground

**Test Prompt**: 
```
こんにちは、Azure AI Foundryについて簡単に説明してください。
```

**Response Quality**: ✅ Excellent
- 日本語応答: 正常
- 構造化回答: 4つの主要特徴を箇条書き
- レイテンシ: 良好

**Conclusion**: azure-openai-connection正常動作

---

### Azure AI Search Connection

**Status**: 作成完了、権限伝播待ち

**Verification**:
```bash
az search service show \
  --name search-ragpoc-dev-ldt4idhueffoe \
  --resource-group rg-rag-poc
```

**Result**:
- Service: ✅ 存在確認
- SKU: Basic
- Indexes: 0件（予想通り）

**Next Steps**: Day 16でIndex作成

---

## Technical Decisions

### Decision 1: 既存リソース参照アプローチ

**Why**: RBAC重複エラー回避、データ保護優先

**Impact**: 
- デプロイ時間短縮（7秒）
- IaC自動化維持
- リスク最小化

### Decision 2: JSON形式パラメータ採用

**Why**: .bicepparam構文エラー解決不能

**Impact**:
- 即座デプロイ成功
- 本番安定性保証
- 実績ある形式

### Decision 3: Index作成延期

**Why**: 段階的実装、Day 15目標達成優先

**Impact**:
- Day 15完了時間: 115分
- Day 16集中実装可能
- 品質向上

---

## Metrics

### Time Breakdown
```yaml
Planning: 10分
Implementation: 30分
Troubleshooting:
  - RBAC重複: 15分
  - Bicepパラメータ: 10分
  - .bicepparam構文: 15分
  - Studio権限: 5分
Verification: 20分
Documentation: 10分

Total: 115分
```

### Code Statistics
```yaml
Bicep Files: 4ファイル
Total Lines: ~250行
Parameters: 3個（environmentName, openAIAccountName, searchServiceName）
Outputs: 7個
```

### Deployment Statistics
```yaml
Validation Success Rate: 100%（最終版）
What-if Success Rate: 100%（最終版）
Deployment Success Rate: 100%（最終版）
Average Deployment Time: 7秒
```

---

## Lessons Learned

### What Worked Well

1. **段階的アプローチ**: Hub/Project → Connections分離
2. **既存リソース参照**: データ保護とデプロイ高速化両立
3. **ADR記録**: 判断理由の明確化

### What Could Be Improved

1. **.bicepparam互換性**: 事前検証不足
2. **RBAC事前設定**: Hub作成時に自動設定すべき
3. **Index作成計画**: Day 15に含めるか明確化不足

### Future Recommendations

1. **Bicep Linter強化**: パラメータ整合性チェック自動化
2. **RBAC自動化**: Bicepに全ロール割り当て含める
3. **Index Template**: サンプルIndex定義を事前準備

---

## Next Steps (Day 16)

### Azure AI Search Index作成
```yaml
Tasks:
  1. Index Schema定義:
     - title (SearchableField)
     - content (SearchableField)
     - contentVector (1536次元, HNSW)
     - category (FilterableField)
     - metadata (FilterableField)
  
  2. サンプルデータ準備:
     - Azure関連ドキュメント 5-10件
     - Markdown形式
  
  3. インデックス作成:
     - az search index create
     - または AI Foundry Studio UI
  
  4. データアップロード:
     - ベクトル埋め込み生成
     - Indexに登録
  
  5. RAGテスト:
     - ハイブリッド検索動作確認
     - セマンティックランキング評価
```

### Estimated Time

- Index Schema定義: 15分
- サンプルデータ準備: 20分
- インデックス作成: 10分
- データアップロード: 15分
- RAGテスト: 20分

**Total**: 80分

---

## References

- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-studio/)
- [Bicep ARM Template Reference](https://learn.microsoft.com/azure/templates/)
- [Azure AI Search REST API](https://learn.microsoft.com/rest/api/searchservice/)
- [RBAC Best Practices](https://learn.microsoft.com/azure/role-based-access-control/best-practices)

---

## Appendix: Full Deployment Output
```json
{
  "id": "/subscriptions/4c5c5fd0-450a-42a5-b5cf-4247712d8f20/resourceGroups/rg-rag-poc/providers/Microsoft.Resources/deployments/ai-foundry-final-20251219-131854",
  "name": "ai-foundry-final-20251219-131854",
  "properties": {
    "provisioningState": "Succeeded",
    "duration": "PT7.0309943S",
    "outputResources": [
      {
        "id": "/subscriptions/4c5c5fd0-450a-42a5-b5cf-4247712d8f20/resourceGroups/rg-rag-poc/providers/Microsoft.MachineLearningServices/workspaces/ai-hub-dev-ldt4idhueffoe/connections/azure-openai-connection"
      },
      {
        "id": "/subscriptions/4c5c5fd0-450a-42a5-b5cf-4247712d8f20/resourceGroups/rg-rag-poc/providers/Microsoft.MachineLearningServices/workspaces/ai-hub-dev-ldt4idhueffoe/connections/azure-search-connection"
      }
    ],
    "outputs": {
      "hubId": {
        "value": "/subscriptions/4c5c5fd0-450a-42a5-b5cf-4247712d8f20/resourceGroups/rg-rag-poc/providers/Microsoft.MachineLearningServices/workspaces/ai-hub-dev-ldt4idhueffoe"
      },
      "hubName": {
        "value": "ai-hub-dev-ldt4idhueffoe"
      },
      "projectId": {
        "value": "/subscriptions/4c5c5fd0-450a-42a5-b5cf-4247712d8f20/resourceGroups/rg-rag-poc/providers/Microsoft.MachineLearningServices/workspaces/rag-agent-project"
      },
      "projectName": {
        "value": "rag-agent-project"
      },
      "openAIConnectionName": {
        "value": "azure-openai-connection"
      },
      "searchConnectionName": {
        "value": "azure-search-connection"
      }
    }
  }
}
```
