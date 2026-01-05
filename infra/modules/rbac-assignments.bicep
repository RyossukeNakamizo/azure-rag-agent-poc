// =============================================================================
// RBAC Assignments Module for RAG POC
// =============================================================================
// Purpose: ユーザープリンシパルへのRBACロール自動割り当て
// Created: D26 - Bicep RBAC自動化
// =============================================================================

@description('権限を付与するユーザーまたはサービスプリンシパルのObject ID')
param principalId string

@description('プリンシパルのタイプ')
@allowed(['User', 'ServicePrincipal', 'Group'])
param principalType string = 'User'

@description('Azure AI Searchサービス名')
param searchServiceName string

@description('Azure OpenAIアカウント名')
param openAiAccountName string

@description('Cosmos DBアカウント名（オプション）')
param cosmosDbAccountName string = ''

@description('Cosmos DBロール割り当てを有効化')
param enableCosmosDbRbac bool = false

// =============================================================================
// Role Definition IDs (Built-in Roles)
// =============================================================================

var roleDefinitions = {
  // Azure AI Search
  searchIndexDataContributor: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  searchIndexDataReader: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
  searchServiceContributor: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
  
  // Azure OpenAI / Cognitive Services
  cognitiveServicesOpenAiUser: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
  cognitiveServicesOpenAiContributor: 'a001fd3d-188f-4b5d-821b-7da978bf7442'
  cognitiveServicesUser: 'a97b65f3-24c7-4388-baec-2e87135dc908'
  
  // Cosmos DB (Data Plane)
  cosmosDbDataContributor: '00000000-0000-0000-0000-000000000002'
  cosmosDbDataReader: '00000000-0000-0000-0000-000000000001'
}

// =============================================================================
// Existing Resources (Reference)
// =============================================================================

resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: searchServiceName
}

resource openAiAccount 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: openAiAccountName
}

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = if (enableCosmosDbRbac && !empty(cosmosDbAccountName)) {
  name: cosmosDbAccountName
}

// =============================================================================
// RBAC Assignments - Azure AI Search
// =============================================================================

@description('Search Index Data Contributor - インデックスの読み書き権限')
resource searchIndexDataContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, principalId, 'SearchIndexDataContributor')
  scope: searchService
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.searchIndexDataContributor
    )
    principalType: principalType
    description: 'RAG POC - Search Index Data Contributor for ${principalType}'
  }
}

// =============================================================================
// RBAC Assignments - Azure OpenAI
// =============================================================================

@description('Cognitive Services OpenAI User - API呼び出し権限')
resource openAiUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAiAccount.id, principalId, 'CognitiveServicesOpenAIUser')
  scope: openAiAccount
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      roleDefinitions.cognitiveServicesOpenAiUser
    )
    principalType: principalType
    description: 'RAG POC - Cognitive Services OpenAI User for ${principalType}'
  }
}

// =============================================================================
// RBAC Assignments - Cosmos DB (Conditional)
// =============================================================================

@description('Cosmos DB Data Contributor - データ読み書き権限（SQL RoleAssignment）')
resource cosmosDbDataContributorRole 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = if (enableCosmosDbRbac && !empty(cosmosDbAccountName)) {
  parent: cosmosDbAccount
  name: guid(cosmosDbAccount.id, principalId, 'CosmosDBDataContributor')
  properties: {
    principalId: principalId
    roleDefinitionId: '${cosmosDbAccount.id}/sqlRoleDefinitions/${roleDefinitions.cosmosDbDataContributor}'
    scope: cosmosDbAccount.id
  }
}

// =============================================================================
// Outputs
// =============================================================================

output searchRoleAssignmentId string = searchIndexDataContributorRole.id
output openAiRoleAssignmentId string = openAiUserRole.id
output cosmosDbRoleAssignmentId string = enableCosmosDbRbac && !empty(cosmosDbAccountName) ? cosmosDbDataContributorRole.id : ''

output assignedRoles array = [
  {
    resource: 'Azure AI Search'
    role: 'Search Index Data Contributor'
    principalId: principalId
  }
  {
    resource: 'Azure OpenAI'
    role: 'Cognitive Services OpenAI User'
    principalId: principalId
  }
  enableCosmosDbRbac && !empty(cosmosDbAccountName) ? {
    resource: 'Cosmos DB'
    role: 'Cosmos DB Built-in Data Contributor'
    principalId: principalId
  } : {}
]
