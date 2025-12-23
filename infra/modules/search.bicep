// ===================================================================
// Azure AI Search Service
// ===================================================================
@description('Search Service 名（グローバル一意）')
param searchServiceName string

@description('デプロイ先リージョン')
param location string = resourceGroup().location

@description('Search Service SKU')
@allowed(['basic', 'standard', 'standard2', 'standard3'])
param sku string = 'basic'

@description('レプリカ数')
@minValue(1)
@maxValue(12)
param replicaCount int = 1

@description('パーティション数')
@minValue(1)
@maxValue(12)
param partitionCount int = 1

@description('セマンティック検索有効化（Basic では無効）')
param enableSemanticSearch bool = false

@description('タグ')
param tags object = {}

// -------------------------------------------------------------------
// Azure AI Search Service
// -------------------------------------------------------------------
resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: replicaCount
    partitionCount: partitionCount
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: enableSemanticSearch && sku != 'basic' ? 'free' : 'disabled'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

// -------------------------------------------------------------------
// 出力
// -------------------------------------------------------------------
output searchServiceId string = searchService.id
output searchServiceName string = searchService.name
output searchEndpoint string = 'https://${searchService.name}.search.windows.net'
output searchPrincipalId string = searchService.identity.principalId
