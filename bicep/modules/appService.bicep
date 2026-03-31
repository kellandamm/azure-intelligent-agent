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
param appCommandLine string = 'bash -c "if [ -f startup.sh ]; then bash startup.sh; elif [ -f app/startup.sh ]; then bash app/startup.sh; elif [ -f /home/site/wwwroot/startup.sh ]; then bash /home/site/wwwroot/startup.sh; elif [ -f /home/site/wwwroot/app/startup.sh ]; then bash /home/site/wwwroot/app/startup.sh; else echo startup.sh not found in working directory or /home/site/wwwroot; echo Working directory: $(pwd); echo Contents of working directory:; ls -la; echo Contents of /home/site/wwwroot:; ls -la /home/site/wwwroot; exit 1; fi"'

@description('Log Analytics Workspace resource ID for diagnostic settings. Leave empty to skip.')
param logAnalyticsWorkspaceId string = ''

@description('VNet subnet resource ID for regional VNet integration (outbound). Leave empty to skip.')
param vnetSubnetId string = ''

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

// Regional VNet integration — routes App Service outbound traffic through the VNet
// Required for private endpoint connectivity when SQL public access is disabled
resource vnetIntegration 'Microsoft.Web/sites/networkConfig@2023-01-01' = if (!empty(vnetSubnetId)) {
  parent: webApp
  name: 'virtualNetwork'
  properties: {
    subnetResourceId: vnetSubnetId
    swiftSupported: true
  }
}

// Diagnostic settings – sent to Log Analytics when workspace ID is provided (satisfies MCSB)
resource webAppDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'appservice-diagnostics'
  scope: webApp
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      { category: 'AppServiceHTTPLogs',       enabled: true, retentionPolicy: { enabled: false, days: 0 } }
      { category: 'AppServiceConsoleLogs',    enabled: true, retentionPolicy: { enabled: false, days: 0 } }
      { category: 'AppServiceAppLogs',        enabled: true, retentionPolicy: { enabled: false, days: 0 } }
      { category: 'AppServiceAuditLogs',      enabled: true, retentionPolicy: { enabled: false, days: 0 } }
      { category: 'AppServiceIPSecAuditLogs', enabled: true, retentionPolicy: { enabled: false, days: 0 } }
    ]
    metrics: [
      { category: 'AllMetrics', enabled: true, retentionPolicy: { enabled: false, days: 0 } }
    ]
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
