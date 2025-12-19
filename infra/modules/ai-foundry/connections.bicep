@description('AI Foundry Hub名')
param hubName string

@description('Azure OpenAI Endpoint')
param openAIEndpoint string

@description('Azure OpenAI Resource ID')
param openAIResourceId string

@description('Azure AI Search Endpoint')
param searchEndpoint string

@description('Azure AI Search Resource ID')
param searchResourceId string

@description('Azure AI Search Index名')
param searchIndexName string = 'rag-index'

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: hubName
}

resource openAIConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: aiHub
  name: 'azure-openai-connection'
  properties: {
    category: 'AzureOpenAI'
    target: openAIEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiVersion: '2024-10-01-preview'
      ApiType: 'Azure'
      ResourceId: openAIResourceId
    }
  }
}

resource searchConnection 'Microsoft.MachineLearningServices/workspaces/connections@2024-04-01' = {
  parent: aiHub
  name: 'azure-search-connection'
  properties: {
    category: 'CognitiveSearch'
    target: searchEndpoint
    authType: 'AAD'
    isSharedToAll: true
    metadata: {
      ApiVersion: '2023-11-01'
      IndexName: searchIndexName
      ResourceId: searchResourceId
    }
  }
}

output openAIConnectionId string = openAIConnection.id
output searchConnectionId string = searchConnection.id

// Outputs
output openAIConnectionName string = openAIConnection.name
output searchConnectionName string = searchConnection.name
