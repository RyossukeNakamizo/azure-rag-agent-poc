// ===================================================================
// Azure OpenAI Service
// ===================================================================
@description('Azure OpenAI リソース名（グローバル一意）')
param openaiName string

@description('デプロイ先リージョン')
param location string = resourceGroup().location

@description('タグ')
param tags object = {}

@description('デプロイメント設定')
param deployments array = []

// -------------------------------------------------------------------
// Azure OpenAI Service
// -------------------------------------------------------------------
resource openaiAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openaiName
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: openaiName
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// -------------------------------------------------------------------
// モデルデプロイメント
// -------------------------------------------------------------------
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = [for item in deployments: {
  parent: openaiAccount
  name: item.name
  sku: item.sku
  properties: {
    model: item.model
  }
}]

// -------------------------------------------------------------------
// 出力
// -------------------------------------------------------------------
output openaiId string = openaiAccount.id
output openaiName string = openaiAccount.name
output openaiEndpoint string = openaiAccount.properties.endpoint
output openaiPrincipalId string = openaiAccount.identity.principalId
