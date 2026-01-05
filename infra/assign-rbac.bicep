// =============================================================================
// RBAC Assignment Deployment - Developer Onboarding
// =============================================================================
// Usage: 新規開発者にRAG POCプロジェクトへのアクセス権限を付与
// 
// デプロイコマンド:
//   az deployment group create \
//     --resource-group rg-rag-poc \
//     --template-file infra/assign-rbac.bicep \
//     --parameters userPrincipalId=<USER_OBJECT_ID>
//
// ユーザーObject IDの取得:
//   az ad user show --id <email@domain.com> --query id -o tsv
//   az ad signed-in-user show --query id -o tsv  # 自分のID
// =============================================================================

targetScope = 'resourceGroup'

// =============================================================================
// Parameters
// =============================================================================

@description('権限を付与するユーザーのObject ID（Azure AD）')
param userPrincipalId string

@description('プリンシパルのタイプ（通常はUser）')
@allowed(['User', 'ServicePrincipal', 'Group'])
param principalType string = 'User'

@description('環境識別子')
@allowed(['dev', 'stg', 'prod'])
param environment string = 'dev'

@description('Cosmos DB RBAC割り当てを有効化')
param enableCosmosDbRbac bool = true

// =============================================================================
// Variables - Resource Names
// =============================================================================

// 命名規則: {service}-{project}-{env}-{suffix}
var nameSuffix = uniqueString(resourceGroup().id)
var searchServiceName = 'search-ragpoc-${environment}-${nameSuffix}'
var openAiAccountName = 'oai-ragpoc-${environment}-${nameSuffix}'
var cosmosDbAccountName = 'cosmos-ragpoc-${environment}-${nameSuffix}'

// =============================================================================
// Module - RBAC Assignments
// =============================================================================

module rbacAssignments 'modules/rbac-assignments.bicep' = {
  name: 'rbac-${userPrincipalId}-${uniqueString(deployment().name)}'
  params: {
    principalId: userPrincipalId
    principalType: principalType
    searchServiceName: searchServiceName
    openAiAccountName: openAiAccountName
    cosmosDbAccountName: enableCosmosDbRbac ? cosmosDbAccountName : ''
    enableCosmosDbRbac: enableCosmosDbRbac
  }
}

// =============================================================================
// Outputs
// =============================================================================

output message string = 'RBAC assignments completed for principal: ${userPrincipalId}'
output assignedRoles array = rbacAssignments.outputs.assignedRoles
output searchRoleId string = rbacAssignments.outputs.searchRoleAssignmentId
output openAiRoleId string = rbacAssignments.outputs.openAiRoleAssignmentId
output cosmosDbRoleId string = rbacAssignments.outputs.cosmosDbRoleAssignmentId
