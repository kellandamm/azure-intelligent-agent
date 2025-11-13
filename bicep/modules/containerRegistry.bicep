// Container Registry Module (uses standard Bicep, can be replaced with AVM)
// Deploys Azure Container Registry for Docker images

targetScope = 'resourceGroup'

@description('Container Registry name (alphanumeric only, globally unique)')
@minLength(5)
@maxLength(50)
param name string

@description('Location for the Container Registry')
param location string

@description('Resource tags')
param tags object = {}

@description('Container Registry SKU')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param acrSku string = 'Standard'

@description('Enable admin user (not recommended for production)')
param adminUserEnabled bool = false

// ========================================
// Resources
// ========================================

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: acrSku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    adminUserEnabled: adminUserEnabled
    publicNetworkAccess: 'Enabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      retentionPolicy: {
        status: 'enabled'
        days: 30
      }
      trustPolicy: {
        status: 'disabled'
      }
    }
  }
}

// ========================================
// Outputs
// ========================================

@description('Container Registry resource ID')
output resourceId string = containerRegistry.id

@description('Container Registry name')
output name string = containerRegistry.name

@description('Container Registry login server')
output loginServer string = containerRegistry.properties.loginServer

@description('Container Registry system-assigned managed identity principal ID')
output managedIdentityPrincipalId string = containerRegistry.identity.principalId
