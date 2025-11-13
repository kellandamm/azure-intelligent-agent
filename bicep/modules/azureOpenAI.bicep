// ============================================================================
// Azure OpenAI Module
// Deploys Azure OpenAI account with model deployment
// ============================================================================

@description('Name of the Azure OpenAI account')
param name string

@description('Location for the Azure OpenAI resource')
param location string = resourceGroup().location

@description('Tags for the resource')
param tags object = {}

@description('SKU name for Azure OpenAI')
@allowed([
  'S0'
  'S1'
])
param sku string = 'S0'

@description('Custom subdomain name for Azure OpenAI')
param customSubDomainName string = name

@description('Public network access setting')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string = 'Enabled'

@description('Model name to deploy (e.g., gpt-4o, gpt-4, gpt-35-turbo)')
param modelName string = 'gpt-4o'

@description('Model version to deploy')
param modelVersion string = '2024-11-20'

@description('Model format')
@allowed([
  'OpenAI'
])
param modelFormat string = 'OpenAI'

@description('Deployment name (defaults to model name if not specified)')
param deploymentName string = modelName

@description('Model deployment capacity (TPM in thousands)')
@minValue(1)
@maxValue(1000)
param deploymentCapacity int = 10

@description('Model deployment SKU')
@allowed([
  'Standard'
  'GlobalStandard'
])
param deploymentSkuName string = 'Standard'

// ============================================================================
// Azure OpenAI Account
// ============================================================================

resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: customSubDomainName
    publicNetworkAccess: publicNetworkAccess
    disableLocalAuth: false
    restrictOutboundNetworkAccess: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

// ============================================================================
// Model Deployment
// ============================================================================

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: azureOpenAI
  name: deploymentName
  sku: {
    name: deploymentSkuName
    capacity: deploymentCapacity
  }
  properties: {
    model: {
      format: modelFormat
      name: modelName
      version: modelVersion
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Resource ID of the Azure OpenAI account')
output resourceId string = azureOpenAI.id

@description('Name of the Azure OpenAI account')
output name string = azureOpenAI.name

@description('Endpoint URL for Azure OpenAI')
output endpoint string = azureOpenAI.properties.endpoint

@description('Name of the model deployment')
output deploymentName string = modelDeployment.name

@description('System-assigned managed identity principal ID')
output principalId string = azureOpenAI.identity.principalId

@description('Location of the resource')
output location string = azureOpenAI.location
