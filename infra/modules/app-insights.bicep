// =============================================================================
// Application Insights Module
// D28: OpenTelemetry監視用 Application Insights
// =============================================================================

@description('Application Insights リソース名')
param name string

@description('リソースのロケーション')
param location string = resourceGroup().location

@description('タグ')
param tags object = {}

@description('Log Analytics Workspace ID')
param workspaceId string

@description('Application種別')
@allowed(['web', 'other'])
param applicationType string = 'web'

@description('データ保持期間（日数）')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

@description('サンプリング比率（%）')
@minValue(0)
@maxValue(100)
param samplingPercentage int = 100

// =============================================================================
// Application Insights
// =============================================================================

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: applicationType
  properties: {
    Application_Type: applicationType
    WorkspaceResourceId: workspaceId
    RetentionInDays: retentionInDays
    SamplingPercentage: samplingPercentage
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// =============================================================================
// Outputs
// =============================================================================

output id string = appInsights.id
output name string = appInsights.name
output instrumentationKey string = appInsights.properties.InstrumentationKey
output connectionString string = appInsights.properties.ConnectionString

@description('Application Insights エンドポイント情報')
output endpoints object = {
  instrumentationKey: appInsights.properties.InstrumentationKey
  connectionString: appInsights.properties.ConnectionString
  ingestionEndpoint: 'https://${location}.in.applicationinsights.azure.com/'
}
