// Key Vault Module
// Deploys Azure Key Vault for secure secrets management

targetScope = 'resourceGroup'

@description('Key Vault name (must be globally unique, 3-24 characters)')
@minLength(3)
@maxLength(24)
param name string

@description('Location for the Key Vault')
param location string

@description('Resource tags')
param tags object = {}

@description('Enable Key Vault for template deployment')
param enabledForTemplateDeployment bool = true

@description('Enable Key Vault for disk encryption')
param enabledForDiskEncryption bool = false

@description('Enable Key Vault for deployment')
param enabledForDeployment bool = false

@description('Enable RBAC authorization (recommended over access policies)')
param enableRbacAuthorization bool = true

@description('SKU name')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'

@description('Secrets to store in Key Vault')
param secrets array = []

@description('Enable soft delete')
param enableSoftDelete bool = true

@description('Soft delete retention days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 90

// ========================================
// Resources
// ========================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: skuName
    }
    enabledForTemplateDeployment: enabledForTemplateDeployment
    enabledForDiskEncryption: enabledForDiskEncryption
    enabledForDeployment: enabledForDeployment
    enableRbacAuthorization: enableRbacAuthorization
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: null
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Create secrets
resource keyVaultSecrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = [for secret in secrets: if (!empty(secret.value)) {
  parent: keyVault
  name: secret.name
  properties: {
    value: secret.value
    contentType: 'text/plain'
  }
}]

// ========================================
// Outputs
// ========================================

@description('Key Vault resource ID')
output resourceId string = keyVault.id

@description('Key Vault name')
output name string = keyVault.name

@description('Key Vault URI')
output vaultUri string = keyVault.properties.vaultUri

@description('Secret URIs for app settings reference')
output secretUris object = {
  azureOpenAIApiKey: '${keyVault.properties.vaultUri}secrets/azureOpenAIApiKey'
  powerbiClientSecret: '${keyVault.properties.vaultUri}secrets/powerbiClientSecret'
  jwtSecretKey: '${keyVault.properties.vaultUri}secrets/jwtSecretKey'
  sqlAdminPassword: '${keyVault.properties.vaultUri}secrets/sqlAdminPassword'
}
