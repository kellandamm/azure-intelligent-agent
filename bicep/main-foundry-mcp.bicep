// ============================================================================
// Azure AI Foundry + MCP Server - Reuse Existing Resources
// Uses existing: Container Apps Environment, ACR, Log Analytics
// ============================================================================

targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment used for resource naming')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Existing resource group name - REQUIRED: Provide your resource group name')
param resourceGroupName string

@description('Existing Container Apps Environment name - REQUIRED: Provide your Container Apps environment name')
param existingContainerEnvName string

@description('Existing Container Registry name (without .azurecr.io) - REQUIRED: Provide your ACR name')
param existingAcrName string

@description('Existing Log Analytics Workspace name - REQUIRED: Provide your Log Analytics workspace name')
param existingLogAnalyticsName string

@description('Existing Application Insights name - Optional: Provide if you have existing App Insights')
param existingAppInsightsName string = ''

// ============================================================================
// Azure AI Foundry Configuration
// ============================================================================

@description('Azure AI Foundry Project Endpoint')
param projectEndpoint string

@secure()
@description('Azure AI Foundry Project Connection String')
param projectConnectionString string

// ============================================================================
// Agent IDs
// ============================================================================

@description('Fabric Orchestrator Agent ID')
param fabricOrchestratorAgentId string

@description('Fabric Sales Agent ID')
param fabricSalesAgentId string

@description('Fabric Realtime Agent ID')
param fabricRealtimeAgentId string

@description('Fabric Analytics Agent ID')
param fabricAnalyticsAgentId string = ''

@description('Fabric Financial Agent ID')
param fabricFinancialAgentId string = ''

@description('Fabric Support Agent ID')
param fabricSupportAgentId string = ''

@description('Fabric Operations Agent ID')
param fabricOperationsAgentId string = ''

@description('Fabric Customer Success Agent ID')
param fabricCustomerSuccessAgentId string = ''

@description('Fabric Operations Excellence Agent ID')
param fabricOperationsExcellenceAgentId string = ''

// ============================================================================
// Fabric & Power BI Configuration
// ============================================================================

@description('Microsoft Fabric Workspace ID')
param fabricWorkspaceId string

@description('Power BI Tenant ID')
param powerbiTenantId string

@description('Power BI Workspace ID')
param powerbiWorkspaceId string = ''

// ============================================================================
// SQL Database Configuration
// ============================================================================

@description('Enable SQL Database connection')
param enableSqlDatabase bool = false

@secure()
@description('SQL Database connection string (if enabled)')
param sqlConnectionString string = ''

// ============================================================================
// Container Images
// ============================================================================

@description('Main application container image')
param mainContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('MCP server container image')
param mcpContainerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ============================================================================
// App Configuration
// ============================================================================

@description('Log level for applications')
param logLevel string = 'INFO'

// ============================================================================
// Get Existing Resource Group
// ============================================================================

resource existingResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = {
  name: resourceGroupName
}

// ============================================================================
// Deploy Resources Using Existing Infrastructure
// ============================================================================

module resources 'resources-reuse-existing.bicep' = {
  name: 'resources-deployment'
  scope: existingResourceGroup
  params: {
    location: location
    environmentName: environmentName
    resourceToken: uniqueString(existingResourceGroup.id)
    existingContainerEnvName: existingContainerEnvName
    existingAcrName: existingAcrName
    existingLogAnalyticsName: existingLogAnalyticsName
    existingAppInsightsName: existingAppInsightsName
    projectEndpoint: projectEndpoint
    projectConnectionString: projectConnectionString
    fabricOrchestratorAgentId: fabricOrchestratorAgentId
    fabricSalesAgentId: fabricSalesAgentId
    fabricRealtimeAgentId: fabricRealtimeAgentId
    fabricAnalyticsAgentId: fabricAnalyticsAgentId
    fabricFinancialAgentId: fabricFinancialAgentId
    fabricSupportAgentId: fabricSupportAgentId
    fabricOperationsAgentId: fabricOperationsAgentId
    fabricCustomerSuccessAgentId: fabricCustomerSuccessAgentId
    fabricOperationsExcellenceAgentId: fabricOperationsExcellenceAgentId
    fabricWorkspaceId: fabricWorkspaceId
    powerbiTenantId: powerbiTenantId
    powerbiWorkspaceId: powerbiWorkspaceId
    enableSqlDatabase: enableSqlDatabase
    sqlConnectionString: sqlConnectionString
    mainContainerImage: mainContainerImage
    mcpContainerImage: mcpContainerImage
    logLevel: logLevel
  }
}

// ============================================================================
// Outputs
// ============================================================================

output resourceGroupId string = existingResourceGroup.id
output resourceGroupName string = existingResourceGroup.name
output mainAppUrl string = resources.outputs.mainAppUrl
output mcpServerUrl string = resources.outputs.mcpServerUrl
output containerRegistryName string = existingAcrName
output containerRegistryEndpoint string = 'https://${existingAcrName}.azurecr.io'
