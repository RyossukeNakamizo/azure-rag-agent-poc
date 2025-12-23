# Azure RBAC設定ガイド

Role-Based Access Control (RBAC)で最小権限を実現。

## 主要ロール

### Azure AI Search
- Search Index Data Reader: 検索実行
- Search Index Data Contributor: Index読み書き

### Azure OpenAI
- Cognitive Services OpenAI User: API呼び出し

### Storage
- Storage Blob Data Reader: Blob読み取り

## 割り当て方法
```bash
az role assignment create \
  --assignee <principal-id> \
  --role "Search Index Data Contributor" \
  --scope <resource-id>
```

カテゴリ: Security
