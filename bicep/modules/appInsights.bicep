// Application Insights Module
// Deploys Azure Application Insights for monitoring and telemetry

targetScope = 'resourceGroup'

@description('Application Insights name')
param name string

@description('Location for the Application Insights resource')
param location string

@description('Resource tags')
param tags object = {}

@description('Retention period in days')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

@description('Application type')
@allowed([
  'web'
  'other'
])
param applicationType string = 'web'

@description('Ingestion mode')
@allowed([
  'ApplicationInsights'
  'ApplicationInsightsWithDiagnosticSettings'
  'LogAnalytics'
])
param ingestionMode string = 'ApplicationInsights'

// ========================================
// Resources
// ========================================

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  kind: applicationType
  tags: tags
  properties: {
    Application_Type: applicationType
    RetentionInDays: retentionInDays
    IngestionMode: ingestionMode
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ========================================
// Outputs
// ========================================

@description('Application Insights resource ID')
output resourceId string = applicationInsights.id

@description('Application Insights name')
output name string = applicationInsights.name

@description('Application Insights instrumentation key')
output instrumentationKey string = applicationInsights.properties.InstrumentationKey

@description('Application Insights connection string')
output connectionString string = applicationInsights.properties.ConnectionString

@description('Application ID')
output appId string = applicationInsights.properties.AppId
