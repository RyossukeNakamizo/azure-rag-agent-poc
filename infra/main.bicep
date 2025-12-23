// ===================================================================
// Azure RAG Agent POC - Infrastructure
// ===================================================================
targetScope = 'resourceGroup'

@description('環境識別子（dev/stg/prod）')
@allowed(['dev', 'stg', 'prod'])
param environment string = 'dev'

@description('デプロイ先リージョン')
param location string = resourceGroup().location

@description('一意性確保用サフィックス（自動生成）')
param uniqueSuffix string = uniqueString(resourceGroup().id)

@description('既存 Azure OpenAI リソース名')
param existingOpenAIName string = 'oai-ragpoc-dev-ldt4idhueffoe'

// -------------------------------------------------------------------
// 共通タグ
// -------------------------------------------------------------------
var commonTags = {
  Environment: environment
  Project: 'azure-rag-agent-poc'
  ManagedBy: 'Bicep'
  CostCenter: 'Engineering'
}

// -------------------------------------------------------------------
// 既存リソース参照: Azure OpenAI
// -------------------------------------------------------------------
resource existingOpenAI 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: existingOpenAIName
}

// -------------------------------------------------------------------
// Module 1: Azure AI Search（既に存在する場合は更新のみ）
// -------------------------------------------------------------------
module search 'modules/search.bicep' = {
  name: 'search-deployment-${uniqueSuffix}'
  params: {
    searchServiceName: 'search-ragpoc-${environment}-${uniqueSuffix}'
    location: location
    sku: environment == 'prod' ? 'standard' : 'basic'
    replicaCount: 1
    partitionCount: 1
    enableSemanticSearch: environment == 'prod'
    tags: commonTags
  }
}

// -------------------------------------------------------------------
// 出力
// -------------------------------------------------------------------
output azureOpenAIEndpoint string = existingOpenAI.properties.endpoint
output azureOpenAIPrincipalId string = existingOpenAI.identity.principalId

output azureSearchEndpoint string = search.outputs.searchEndpoint
output azureSearchPrincipalId string = search.outputs.searchPrincipalId
output azureSearchServiceName string = search.outputs.searchServiceName

output resourceGroupName string = resourceGroup().name
output environment string = environment
