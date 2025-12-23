// ===================================================================
// RBAC Assignments for Azure AI Search
// ===================================================================
@description('Search Service リソース ID')
param searchServiceId string

@description('Azure OpenAI の Managed Identity Principal ID')
param openaiPrincipalId string

@description('ユーザー/サービスプリンシパルの Principal ID（開発用）')
param userPrincipalId string = ''

// -------------------------------------------------------------------
// 既存リソース参照
// -------------------------------------------------------------------
resource searchService 'Microsoft.Search/searchServices@2023-11-01' existing = {
  name: split(searchServiceId, '/')[8]
}

// -------------------------------------------------------------------
// Azure OpenAI → Search: Search Index Data Reader
// LLM が検索結果を読み取るために必要
// -------------------------------------------------------------------
resource openaiSearchReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchServiceId, openaiPrincipalId, 'SearchIndexDataReader')
  scope: searchService
  properties: {
    principalId: openaiPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    )
    principalType: 'ServicePrincipal'
  }
}

// -------------------------------------------------------------------
// ユーザー → Search: Search Index Data Contributor（開発用）
// インデックス作成・ドキュメント投入に必要
// -------------------------------------------------------------------
resource userSearchContributorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (userPrincipalId != '') {
  name: guid(searchServiceId, userPrincipalId, 'SearchIndexDataContributor')
  scope: searchService
  properties: {
    principalId: userPrincipalId
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    )
    principalType: 'User'
  }
}

// -------------------------------------------------------------------
// 出力
// -------------------------------------------------------------------
output openaiReaderRoleId string = openaiSearchReaderRole.id
output userContributorRoleId string = userPrincipalId != '' ? userSearchContributorRole.id : ''
