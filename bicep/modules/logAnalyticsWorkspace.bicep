// Log Analytics Workspace Module
// Deploys a Log Analytics workspace for centralized logging and diagnostics.
// Required for:
//   - MCSB: centralised diagnostic log collection (SecurityCenterBuiltIn policy)
//   - Workspace-based Application Insights (recommended over classic mode)

targetScope = 'resourceGroup'

@description('Log Analytics workspace name')
param name string

@description('Location for the workspace')
param location string

@description('Resource tags')
param tags object = {}

@description('Retention period in days (30-730)')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

@description('SKU name')
@allowed([
  'PerGB2018'
  'CapacityReservation'
])
param skuName string = 'PerGB2018'

// ========================================
// Resources
// ========================================

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: skuName
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

// ========================================
// Outputs
// ========================================

@description('Log Analytics workspace resource ID')
output resourceId string = logAnalyticsWorkspace.id

@description('Log Analytics workspace name')
output name string = logAnalyticsWorkspace.name

@description('Log Analytics workspace customer ID (used for queries)')
output customerId string = logAnalyticsWorkspace.properties.customerId
