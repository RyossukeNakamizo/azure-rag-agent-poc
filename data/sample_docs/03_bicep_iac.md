# Bicep Infrastructure as Code入門

BicepはAzure Resource Manager (ARM)テンプレートのDSLです。

## 特徴
- JSONより簡潔
- 型安全性
- ネイティブモジュール化

## 基本構文
```bicep
param location string = resourceGroup().location

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'mystorageaccount'
  location: location
}
```

## デプロイ
```bash
az deployment group create \
  --resource-group rg-demo \
  --template-file main.bicep
```

カテゴリ: Infrastructure
