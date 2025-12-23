// AI Foundry Connections デプロイ（既存Hub/Project用）
targetScope = 'resourceGroup'

@description('Environment name')
param environmentName string

@description('Azure OpenAI account name')
param openAIAccountName string

@description('Azure AI Search service name')
param searchServiceName string

@description('Location for all resources')
param location string = resourceGroup().location

// 既存リソース参照
resource openAIAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAIAccountName
}

resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

// 変数
var hubName = 'ai-hub-${environmentName}-ldt4idhueffoe'
var projectName = 'rag-agent-project'

// 既存AI Foundry Hub参照
resource existingHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: hubName
}

// 既存AI Foundry Project参照
resource existingProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: projectName
}

// Connections作成
module connections 'modules/ai-foundry/connections.bicep' = {
  name: 'ai-foundry-connections-deployment'
  params: {
    hubName: hubName
    openAIEndpoint: openAIAccount.properties.endpoint
    openAIResourceId: openAIAccount.id
    searchEndpoint: 'https://${searchService.name}.search.windows.net'
    searchResourceId: searchService.id
    searchIndexName: 'rag-index'
  }
}

// Outputs
output hubId string = existingHub.id
output hubName string = existingHub.name
output projectId string = existingProject.id
output projectName string = existingProject.name
output hubPrincipalId string = existingHub.identity.principalId
output openAIConnectionName string = connections.outputs.openAIConnectionName
output searchConnectionName string = connections.outputs.searchConnectionName

// ================================================================
// Azure AI Search Index Module
// ================================================================
module searchIndex 'modules/search/index.bicep' = {
  name: 'searchIndexDeployment'
  params: {
    searchServiceName: searchServiceName
    indexName: 'rag-docs-index'
  }
  dependsOn: [
    searchService
  ]
}

// ================================================================
// Outputs - Index情報追加
// ================================================================
output searchIndexName string = searchIndex.outputs.indexName
output searchServiceEndpoint string = searchIndex.outputs.searchServiceEndpoint
