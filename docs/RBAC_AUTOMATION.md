# RBAC自動化ガイド

## 概要

D26で実装したBicep RBAC自動化モジュールにより、新規開発者へのアクセス権限付与をコマンド1つで実行できます。

## ファイル構成

```
infra/
├── assign-rbac.bicep              # メインデプロイファイル
└── modules/
    └── rbac-assignments.bicep     # RBACモジュール（再利用可能）

scripts/
└── assign-rbac.sh                 # 簡易実行ラッパー
```

## 付与されるロール

| リソース | ロール名 | 権限 |
|----------|----------|------|
| Azure AI Search | Search Index Data Contributor | インデックスの読み書き |
| Azure OpenAI | Cognitive Services OpenAI User | API呼び出し |
| Cosmos DB | Cosmos DB Built-in Data Contributor | データ読み書き |

## 使用方法

### 方法1: シェルスクリプト（推奨）

```bash
# 自分自身に権限を付与
./scripts/assign-rbac.sh --self

# 特定ユーザーに権限を付与（メールアドレス指定）
./scripts/assign-rbac.sh user@example.com

# 特定ユーザーに権限を付与（Object ID指定）
./scripts/assign-rbac.sh 12345678-1234-1234-1234-123456789012
```

### 方法2: Azure CLI直接実行

```bash
# ユーザーのObject IDを取得
USER_ID=$(az ad user show --id user@example.com --query id -o tsv)

# または自分のObject IDを取得
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# デプロイ実行
az deployment group create \
  --resource-group rg-rag-poc \
  --template-file infra/assign-rbac.bicep \
  --parameters userPrincipalId=$USER_ID
```

### 方法3: パラメータファイル使用

```bash
# パラメータファイル作成
cat > infra/rbac-params.json << EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "userPrincipalId": {
      "value": "<USER_OBJECT_ID>"
    },
    "environment": {
      "value": "dev"
    },
    "enableCosmosDbRbac": {
      "value": true
    }
  }
}
EOF

# デプロイ
az deployment group create \
  --resource-group rg-rag-poc \
  --template-file infra/assign-rbac.bicep \
  --parameters @infra/rbac-params.json
```

## 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|--------------|------|
| RESOURCE_GROUP | rg-rag-poc | 対象リソースグループ |
| ENVIRONMENT | dev | 環境（dev/stg/prod） |
| ENABLE_COSMOS_DB | true | Cosmos DB RBAC有効化 |

## オンボーディングフロー

```
1. 新規開発者がチームに参加
   │
   ▼
2. リード開発者が以下を実行:
   ./scripts/assign-rbac.sh new-developer@company.com
   │
   ▼
3. What-if結果を確認
   │
   ▼
4. 'y'で承認してデプロイ
   │
   ▼
5. 開発者がAzure CLIでログイン:
   az login
   │
   ▼
6. 開発者がアプリケーション実行:
   cd azure-rag-agent-poc
   python -m uvicorn app.main:app --reload
```

## トラブルシューティング

### "ResourceNotFound" エラー

リソース名が環境と一致していることを確認:

```bash
# 実際のリソース名を確認
az search service list -g rg-rag-poc --query "[].name" -o tsv
az cognitiveservices account list -g rg-rag-poc --query "[].name" -o tsv
az cosmosdb list -g rg-rag-poc --query "[].name" -o tsv
```

### "AuthorizationFailed" エラー

RBAC割り当て権限が必要です:

```bash
# 自分の権限を確認
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) \
  --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-rag-poc \
  --output table
```

必要な権限: `User Access Administrator` または `Owner`

### 既存ロール割り当ての重複

同一ユーザーへの再実行は安全です（べき等性）。
Bicepは既存ロールをスキップします。

## セキュリティ考慮事項

1. **最小権限の原則**: 必要なロールのみ付与
2. **定期的な監査**: `az role assignment list`で確認
3. **退職時の削除**: 手動またはスクリプトで権限削除

```bash
# ユーザーの全ロール割り当てを削除
az role assignment delete --assignee <USER_OBJECT_ID> --scope /subscriptions/<SUB_ID>/resourceGroups/rg-rag-poc
```

## 関連ドキュメント

- [Azure RBAC Documentation](https://learn.microsoft.com/en-us/azure/role-based-access-control/)
- [Cosmos DB RBAC](https://learn.microsoft.com/en-us/azure/cosmos-db/how-to-setup-rbac)
- [Azure AI Search RBAC](https://learn.microsoft.com/en-us/azure/search/search-security-rbac)
