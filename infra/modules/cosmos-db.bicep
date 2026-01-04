// ============================================================================
// Azure Cosmos DB for NoSQL - Serverless Configuration
// Module: cosmos-db.bicep
// Purpose: 会話履歴管理用Cosmos DBリソース
// ============================================================================

@description('プロジェクト名（リソース名生成に使用）')
param projectName string

@description('環境名')
@allowed(['dev', 'stg', 'prod'])
param environment string = 'dev'

@description('リージョン')
param location string = resourceGroup().location

@description('タグ')
param tags object = {}

@description('Cosmos DBスループットモード')
@allowed(['Serverless', 'Provisioned'])
param throughputMode string = 'Serverless'

@description('プロビジョニングモード時の最小RU/s')
param minThroughput int = 400

@description('プロビジョニングモード時の最大RU/s（Autoscale）')
param maxThroughput int = 4000

@description('Managed IdentityのPrincipal ID（RBAC割り当て用）')
param principalId string = ''

// ============================================================================
// 変数
// ============================================================================

var accountName = 'cosmos-${projectName}-${environment}-${uniqueString(resourceGroup().id)}'
var databaseName = 'rag-conversations'
var containerName = 'conversations'

// Cosmos DB Data Contributor Role ID
var cosmosDataContributorRoleId = '00000000-0000-0000-0000-000000000002'

// ============================================================================
// Cosmos DB Account
// ============================================================================

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  tags: union(tags, {
    component: 'cosmos-db'
    purpose: 'conversation-history'
  })
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    // Serverless構成
    capabilities: throughputMode == 'Serverless' ? [
      { name: 'EnableServerless' }
    ] : []
    
    // セキュリティ設定
    disableLocalAuth: false  // 開発フェーズはローカル認証許可
    publicNetworkAccess: 'Enabled'  // 開発フェーズはパブリックアクセス
    
    // 一貫性レベル
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
      maxStalenessPrefix: 100
      maxIntervalInSeconds: 5
    }
    
    // バックアップ設定
    backupPolicy: {
      type: 'Periodic'
      periodicModeProperties: {
        backupIntervalInMinutes: 240
        backupRetentionIntervalInHours: 8
        backupStorageRedundancy: 'Local'
      }
    }
    
    // ネットワーク設定（本番はPrivate Endpoint移行）
    isVirtualNetworkFilterEnabled: false
    ipRules: []
  }
}

// ============================================================================
// Database
// ============================================================================

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    // Serverlessの場合はスループット設定不要
    options: throughputMode == 'Provisioned' ? {
      autoscaleSettings: {
        maxThroughput: maxThroughput
      }
    } : {}
  }
}

// ============================================================================
// Container: conversations
// ============================================================================

resource conversationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  parent: database
  name: containerName
  properties: {
    resource: {
      id: containerName
      partitionKey: {
        paths: ['/sessionId']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          { path: '/*' }
        ]
        excludedPaths: [
          { path: '/content/?' }  // 大きなテキストは除外
          { path: '/_etag/?' }
        ]
        compositeIndexes: [
          [
            { path: '/sessionId', order: 'ascending' }
            { path: '/createdAt', order: 'descending' }
          ]
        ]
      }
      defaultTtl: 2592000  // 30日
      uniqueKeyPolicy: {
        uniqueKeys: []
      }
    }
    // Serverlessの場合はスループット設定不要
    options: throughputMode == 'Provisioned' ? {
      throughput: minThroughput
    } : {}
  }
}

// ============================================================================
// RBAC Role Assignment
// ============================================================================

resource roleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = if (!empty(principalId)) {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, principalId, cosmosDataContributorRoleId)
  properties: {
    principalId: principalId
    roleDefinitionId: '/${subscription().id}/resourceGroups/${resourceGroup().name}/providers/Microsoft.DocumentDB/databaseAccounts/${cosmosAccount.name}/sqlRoleDefinitions/${cosmosDataContributorRoleId}'
    scope: cosmosAccount.id
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Cosmos DB Account Name')
output accountName string = cosmosAccount.name

@description('Cosmos DB Endpoint')
output endpoint string = cosmosAccount.properties.documentEndpoint

@description('Database Name')
output databaseName string = database.name

@description('Container Name')
output containerName string = conversationsContainer.name

@description('Cosmos DB Resource ID')
output resourceId string = cosmosAccount.id

@description('Connection String (for local development only)')
output connectionString string = cosmosAccount.listConnectionStrings().connectionStrings[0].connectionString
