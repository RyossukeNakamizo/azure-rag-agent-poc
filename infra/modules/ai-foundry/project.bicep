@description('Project名')
param projectName string

@description('デプロイリージョン')
param location string = resourceGroup().location

@description('親AI Foundry Hub名')
param hubName string

@description('タグ')
param tags object = {}

resource aiHub 'Microsoft.MachineLearningServices/workspaces@2024-04-01' existing = {
  name: hubName
}

resource aiProject 'Microsoft.MachineLearningServices/workspaces@2024-04-01' = {
  name: projectName
  location: location
  tags: tags
  kind: 'Project'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    friendlyName: projectName
    description: 'RAG Agent Development Project'
    hubResourceId: aiHub.id
    publicNetworkAccess: 'Enabled'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

output projectId string = aiProject.id
output projectName string = aiProject.name
output projectPrincipalId string = aiProject.identity.principalId
