# Managed Identity ベストプラクティス

Managed Identityは、Azureリソース間の認証を簡素化します。

## 種類
1. System-assigned: リソースと1:1
2. User-assigned: 複数リソースで共有可能

## 利点
- API Key不要
- 自動ローテーション
- 監査ログ統合

## 使用例
- Azure AI Search ⇔ Azure OpenAI
- App Service ⇔ Key Vault
- Azure Functions ⇔ Storage

カテゴリ: Security
