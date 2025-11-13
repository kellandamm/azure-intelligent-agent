// App Service Module
// Deploys App Service Plan and Web App for Python application

targetScope = 'resourceGroup'

@description('App Service Plan name')
param appServicePlanName string

@description('Web App name')
param webAppName string

@description('Location for resources')
param location string

@description('Resource tags')
param tags object = {}

@description('App Service Plan SKU')
param appServicePlanSku string = 'B2'

@description('Python version')
@allowed([
  '3.8'
  '3.9'
  '3.10'
  '3.11'
  '3.12'
])
param pythonVersion string = '3.11'

@description('Enable always on')
param alwaysOn bool = true

@description('App settings array')
param appSettings array = []

@description('Enable system-assigned managed identity')
param enableSystemManagedIdentity bool = true

@description('Health check path')
param healthCheckPath string = '/health'

@description('App command line (startup script)')
param appCommandLine string = 'gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 600'

// ========================================
// Variables
// ========================================

// Determine tier from SKU
var tier = contains(appServicePlanSku, 'B') ? 'Basic' : contains(appServicePlanSku, 'S') ? 'Standard' : contains(appServicePlanSku, 'P') ? 'PremiumV2' : 'Free'

// ========================================
// Resources
// ========================================

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: appServicePlanSku
    tier: tier
    capacity: 1
  }
  properties: {
    reserved: true // Required for Linux
    zoneRedundant: false
  }
}

resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: webAppName
  location: location
  tags: tags
  kind: 'app,linux'
  identity: enableSystemManagedIdentity ? {
    type: 'SystemAssigned'
  } : null
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    reserved: true
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'PYTHON|${pythonVersion}'
      alwaysOn: alwaysOn
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
      appCommandLine: appCommandLine
      healthCheckPath: healthCheckPath
      appSettings: appSettings
      pythonVersion: pythonVersion
    }
  }
}

// Basic publishing credentials policy - separate resource
resource ftpPublishingPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-01-01' = {
  parent: webApp
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource scmPublishingPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2023-01-01' = {
  parent: webApp
  name: 'scm'
  properties: {
    allow: true // Required for zip deploy
  }
}

// ========================================
// Outputs
// ========================================

@description('App Service Plan resource ID')
output appServicePlanResourceId string = appServicePlan.id

@description('App Service Plan name')
output appServicePlanName string = appServicePlan.name

@description('Web App resource ID')
output resourceId string = webApp.id

@description('Web App name')
output webAppName string = webApp.name

@description('Web App default hostname')
output defaultHostName string = webApp.properties.defaultHostName

@description('Web App URL')
output webAppUrl string = 'https://${webApp.properties.defaultHostName}'

@description('Web App system-assigned managed identity principal ID')
output managedIdentityPrincipalId string = enableSystemManagedIdentity ? webApp.identity.principalId : ''

@description('Web App system-assigned managed identity tenant ID')
output managedIdentityTenantId string = enableSystemManagedIdentity ? webApp.identity.tenantId : ''
