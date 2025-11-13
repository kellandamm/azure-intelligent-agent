// ========================================
// Azure Intelligent Agent Starter - Main Bicep Template
// This template deploys a complete Azure infrastructure for intelligent AI agent applications
// using Azure Verified Modules (AVM) for production-ready, secure deployments
// ========================================

targetScope = 'resourceGroup'

// ========================================
// Parameters - General
// ========================================

@description('Name prefix for all resources (e.g., "myagentapp"). Resources will be named like {appName}-{resource}-{environment}')
@minLength(3)
@maxLength(20)
param appName string

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Environment tag (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'prod'

@description('Current deployment timestamp')
param deploymentTimestamp string = utcNow()

// ========================================
// Parameters - Azure OpenAI
// ========================================

@description('Deploy new Azure OpenAI resource (true) or use existing (false)')
param deployAzureOpenAI bool = false

@description('Azure OpenAI account name (used when deployAzureOpenAI=true)')
param azureOpenAIName string = '${appName}-openai-${environment}'

@description('Azure OpenAI model name to deploy (e.g., gpt-4o, gpt-4, gpt-35-turbo)')
param azureOpenAIModelName string = 'gpt-4o'

@description('Azure OpenAI model version')
param azureOpenAIModelVersion string = '2024-11-20'

@description('Azure OpenAI model deployment capacity (TPM in thousands, 1-1000)')
@minValue(1)
@maxValue(1000)
param azureOpenAIModelCapacity int = 10

@description('Azure OpenAI SKU')
@allowed([
  'S0'
  'S1'
])
param azureOpenAISku string = 'S0'

@description('Azure OpenAI service endpoint URL (required when deployAzureOpenAI=false)')
param azureOpenAIEndpoint string = deployAzureOpenAI ? '' : ''

@description('Azure OpenAI deployment/model name (e.g., gpt-4o, gpt-35-turbo)')
param azureOpenAIDeployment string = 'gpt-4o'

@description('Azure OpenAI API version')
param azureOpenAIApiVersion string = '2024-08-01-preview'

@description('Azure OpenAI API Key (required when deployAzureOpenAI=false, will be retrieved from deployed resource if deployAzureOpenAI=true)')
@secure()
param azureOpenAIApiKey string = ''

// ========================================
// Parameters - Azure AI Foundry
// ========================================

@description('Azure AI Foundry project endpoint URL')
param projectEndpoint string

@description('Azure AI Foundry connection name for OpenAI')
param connectionName string = 'aoai-connection'

@description('Model deployment name in AI Foundry')
param modelDeploymentName string = 'gpt-4o'

// ========================================
// Parameters - Microsoft Fabric
// ========================================

@description('Microsoft Fabric workspace ID')
param fabricWorkspaceId string

@description('Fabric Orchestrator Agent ID')
param fabricOrchestratorAgentId string

@description('Fabric Document Agent ID')
param fabricDocumentAgentId string

@description('Fabric Power BI Agent ID')
param fabricPowerBiAgentId string

@description('Fabric Chart Agent ID')
param fabricChartAgentId string

@description('Fabric Sales Agent ID')
param fabricSalesAgentId string

@description('Fabric Realtime Agent ID')
param fabricRealtimeAgentId string

// ========================================
// Parameters - Power BI
// ========================================

@description('Power BI workspace ID (often same as Fabric workspace)')
param powerbiWorkspaceId string

@description('Power BI report ID to embed')
param powerbiReportId string

@description('Power BI service principal client ID')
param powerbiClientId string

@description('Power BI service principal tenant ID')
param powerbiTenantId string

@description('Power BI service principal client secret')
@secure()
param powerbiClientSecret string

// ========================================
// Parameters - SQL Database
// ========================================

@description('SQL Server name (must be globally unique)')
@minLength(3)
@maxLength(63)
param sqlServerName string

@description('SQL Database name')
param sqlDatabaseName string = 'aiagentsdb'

@description('SQL Database SKU (Basic, S0, S1, P1, etc.)')
param sqlDatabaseSku string = 'Basic'

@description('Use Azure AD authentication for SQL (recommended)')
param sqlUseAzureAuth bool = true

@description('SQL admin username (required if not using Azure AD only)')
param sqlAdminUsername string = 'sqladmin'

@description('SQL admin password (required if not using Azure AD only)')
@secure()
param sqlAdminPassword string = ''

@description('Azure AD admin login name (e.g., admin@domain.com)')
param sqlAzureAdAdminLogin string = ''

@description('Azure AD admin object ID (SID)')
param sqlAzureAdAdminSid string = ''

// ========================================
// Parameters - Authentication & Security
// ========================================

@description('Enable JWT authentication for the application')
param enableAuthentication bool = true

@description('JWT secret key (leave empty to auto-generate)')
@secure()
param jwtSecretKey string = ''

@description('JWT algorithm')
@allowed([
  'HS256'
  'HS384'
  'HS512'
])
param jwtAlgorithm string = 'HS256'

@description('JWT token expiration in minutes')
@minValue(30)
@maxValue(43200)
param jwtExpirationMinutes int = 43200

// ========================================
// Parameters - Application Configuration
// ========================================

@description('App Service Plan SKU (B1, B2, S1, P1v2, P2v2, etc.)')
param appServicePlanSku string = 'B2'

@description('Enable Application Insights monitoring')
param enableApplicationInsights bool = true

@description('Application port')
param appPort int = 8000

@description('Enable OpenTelemetry tracing')
param enableTracing bool = true

@description('Log level')
@allowed([
  'DEBUG'
  'INFO'
  'WARNING'
  'ERROR'
  'CRITICAL'
])
param logLevel string = 'INFO'

@description('Enable Key Vault for secrets management')
param enableKeyVault bool = true

@description('Enable Container Registry for Docker images')
param enableContainerRegistry bool = false

// ========================================
// Variables
// ========================================

var resourceNamePrefix = '${appName}-${environment}'
var tags = {
  Application: 'Agent Framework Demo'
  Environment: environment
  ManagedBy: 'Bicep-AVM'
  DeployedDate: substring(deploymentTimestamp, 0, 10)
}

// Generate JWT secret if not provided
var generatedJwtSecret = uniqueString(resourceGroup().id, appName, deploymentTimestamp)
var finalJwtSecret = empty(jwtSecretKey) ? generatedJwtSecret : jwtSecretKey

// SQL Server FQDN
#disable-next-line no-hardcoded-env-urls
var sqlServerFqdn = '${sqlServerName}.database.windows.net'

// App Settings - consolidated configuration
var baseAppSettings = [
  // Azure OpenAI (use deployed module outputs if deployed, otherwise use provided values)
  { name: 'AZURE_OPENAI_ENDPOINT', value: deployAzureOpenAI ? azureOpenAIModule!.outputs.endpoint : azureOpenAIEndpoint }
  { name: 'AZURE_OPENAI_DEPLOYMENT', value: deployAzureOpenAI ? azureOpenAIModule!.outputs.deploymentName : azureOpenAIDeployment }
  { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenAIApiVersion }
  { name: 'AZURE_OPENAI_API_KEY', value: azureOpenAIApiKey }
  
  // Azure AI Foundry
  { name: 'PROJECT_ENDPOINT', value: projectEndpoint }
  { name: 'CONNECTION_NAME', value: connectionName }
  { name: 'MODEL_DEPLOYMENT_NAME', value: modelDeploymentName }
  
  // Microsoft Fabric
  { name: 'FABRIC_WORKSPACE_ID', value: fabricWorkspaceId }
  { name: 'FABRIC_ORCHESTRATOR_AGENT_ID', value: fabricOrchestratorAgentId }
  { name: 'FABRIC_DOCUMENT_AGENT_ID', value: fabricDocumentAgentId }
  { name: 'FABRIC_POWERBI_AGENT_ID', value: fabricPowerBiAgentId }
  { name: 'FABRIC_CHART_AGENT_ID', value: fabricChartAgentId }
  { name: 'FABRIC_SALES_AGENT_ID', value: fabricSalesAgentId }
  { name: 'FABRIC_REALTIME_AGENT_ID', value: fabricRealtimeAgentId }
  
  // Power BI
  { name: 'POWERBI_WORKSPACE_ID', value: powerbiWorkspaceId }
  { name: 'POWERBI_REPORT_ID', value: powerbiReportId }
  { name: 'POWERBI_CLIENT_ID', value: powerbiClientId }
  { name: 'POWERBI_TENANT_ID', value: powerbiTenantId }
  { name: 'POWERBI_CLIENT_SECRET', value: powerbiClientSecret }
  
  // SQL Database
  { name: 'SQL_SERVER', value: sqlServerFqdn }
  { name: 'SQL_DATABASE', value: sqlDatabaseName }
  { name: 'SQL_USE_AZURE_AUTH', value: string(sqlUseAzureAuth) }
  { name: 'SQL_USERNAME', value: sqlUseAzureAuth ? '' : sqlAdminUsername }
  { name: 'SQL_PASSWORD', value: sqlUseAzureAuth ? '' : sqlAdminPassword }
  
  // Authentication
  { name: 'ENABLE_AUTHENTICATION', value: string(enableAuthentication) }
  { name: 'JWT_SECRET_KEY', value: finalJwtSecret }
  { name: 'JWT_SECRET', value: finalJwtSecret }
  { name: 'JWT_ALGORITHM', value: jwtAlgorithm }
  { name: 'JWT_EXPIRATION_MINUTES', value: string(jwtExpirationMinutes) }
  { name: 'JWT_EXPIRY_HOURS', value: string(jwtExpirationMinutes / 60) }
  
  // Application Settings
  { name: 'APP_PORT', value: string(appPort) }
  { name: 'ENABLE_TRACING', value: string(enableTracing) }
  { name: 'LOG_LEVEL', value: logLevel }
  
  // Azure deployment settings
  { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
  { name: 'WEBSITE_HTTPLOGGING_RETENTION_DAYS', value: '7' }
]

// ========================================
// Module: Azure OpenAI (Optional)
// ========================================

module azureOpenAIModule 'modules/azureOpenAI.bicep' = if (deployAzureOpenAI) {
  name: 'azureOpenAI-deployment'
  params: {
    name: azureOpenAIName
    location: location
    tags: tags
    sku: azureOpenAISku
    modelName: azureOpenAIModelName
    modelVersion: azureOpenAIModelVersion
    deploymentName: azureOpenAIDeployment
    deploymentCapacity: azureOpenAIModelCapacity
  }
}

// ========================================
// Module: Application Insights (Optional)
// ========================================

module appInsightsModule 'modules/appInsights.bicep' = if (enableApplicationInsights) {
  name: 'appInsights-deployment'
  params: {
    name: '${resourceNamePrefix}-insights'
    location: location
    tags: tags
  }
}

// App Insights settings - conditional
var appInsightsSettings = enableApplicationInsights ? [
  { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsModule.outputs.connectionString }
  { name: 'ApplicationInsightsAgent_EXTENSION_VERSION', value: '~3' }
] : []

// Final app settings combining base and conditional
var appSettings = concat(baseAppSettings, appInsightsSettings)

// ========================================
// Module: Key Vault (Optional)
// ========================================

module keyVaultModule 'modules/keyVault.bicep' = if (enableKeyVault) {
  name: 'keyVault-deployment'
  params: {
    name: take('${replace(resourceNamePrefix, '-', '')}kv${uniqueString(resourceGroup().id)}', 24)
    location: location
    tags: tags
    enabledForTemplateDeployment: true
    enableRbacAuthorization: true
    secrets: [
      {
        name: 'azureOpenAIApiKey'
        value: azureOpenAIApiKey
      }
      {
        name: 'powerbiClientSecret'
        value: powerbiClientSecret
      }
      {
        name: 'jwtSecretKey'
        value: finalJwtSecret
      }
      {
        name: 'sqlAdminPassword'
        value: sqlAdminPassword
      }
    ]
  }
}

// ========================================
// Module: Container Registry (Optional)
// ========================================

module containerRegistryModule 'modules/containerRegistry.bicep' = if (enableContainerRegistry) {
  name: 'acr-deployment'
  params: {
    name: '${replace(appName, '-', '')}${environment}acr'
    location: location
    tags: tags
    acrSku: 'Standard'
  }
}

// ========================================
// Module: SQL Server & Database
// ========================================

module sqlServerModule 'modules/sqlServer.bicep' = {
  name: 'sql-deployment'
  params: {
    serverName: sqlServerName
    location: location
    tags: tags
    administratorLogin: sqlUseAzureAuth ? '' : sqlAdminUsername
    administratorLoginPassword: sqlUseAzureAuth ? '' : sqlAdminPassword
    azureAdAdminLogin: sqlAzureAdAdminLogin
    azureAdAdminSid: sqlAzureAdAdminSid
    azureADOnlyAuthentication: sqlUseAzureAuth
    databaseName: sqlDatabaseName
    databaseSku: sqlDatabaseSku
    enableAudit: true
    enableThreatDetection: true
  }
}

// ========================================
// Module: App Service Plan & Web App
// ========================================

module appServiceModule 'modules/appService.bicep' = {
  name: 'appService-deployment'
  params: {
    appServicePlanName: '${resourceNamePrefix}-plan'
    webAppName: '${resourceNamePrefix}-app'
    location: location
    tags: tags
    appServicePlanSku: appServicePlanSku
    pythonVersion: '3.11'
    alwaysOn: true
    appSettings: appSettings
    enableSystemManagedIdentity: true
  }
  dependsOn: [
    appInsightsModule
    sqlServerModule
  ]
}

// ========================================
// Module: Role Assignments
// ========================================

// Grant Web App access to Key Vault
module keyVaultRoleAssignment 'modules/roleAssignment.bicep' = if (enableKeyVault) {
  name: 'keyVault-roleAssignment'
  params: {
    principalId: appServiceModule.outputs.managedIdentityPrincipalId
    roleDefinitionId: '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User
    targetResourceId: enableKeyVault ? keyVaultModule.outputs.resourceId : ''
  }
  dependsOn: [
    keyVaultModule
    appServiceModule
  ]
}

// Grant Web App access to SQL Database
module sqlRoleAssignment 'modules/roleAssignment.bicep' = if (sqlUseAzureAuth) {
  name: 'sql-roleAssignment'
  params: {
    principalId: appServiceModule.outputs.managedIdentityPrincipalId
    roleDefinitionId: '00000000-0000-0000-0000-000000000000' // Placeholder - SQL roles handled separately
    targetResourceId: sqlServerModule.outputs.resourceId
  }
}

// ========================================
// Outputs
// ========================================

@description('Resource group name')
output resourceGroupName string = resourceGroup().name

@description('Web App name')
output webAppName string = appServiceModule.outputs.webAppName

@description('Web App URL')
output webAppUrl string = appServiceModule.outputs.webAppUrl

@description('Web App managed identity principal ID')
output managedIdentityPrincipalId string = appServiceModule.outputs.managedIdentityPrincipalId

@description('SQL Server name')
output sqlServerName string = sqlServerModule.outputs.serverName

@description('SQL Database name')
output sqlDatabaseName string = sqlServerModule.outputs.databaseName

@description('Key Vault name')
output keyVaultName string = enableKeyVault ? keyVaultModule!.outputs.name : ''

@description('Azure OpenAI endpoint (deployed or provided)')
output azureOpenAIEndpoint string = deployAzureOpenAI ? azureOpenAIModule!.outputs.endpoint : azureOpenAIEndpoint

@description('Azure OpenAI deployment name')
output azureOpenAIDeployment string = deployAzureOpenAI ? azureOpenAIModule!.outputs.deploymentName : azureOpenAIDeployment

@description('Azure OpenAI resource name (if deployed)')
output azureOpenAIName string = deployAzureOpenAI ? azureOpenAIModule!.outputs.name : ''

@description('Container Registry name')
output containerRegistryName string = enableContainerRegistry ? containerRegistryModule!.outputs.name : ''

@description('Container Registry login server')
output containerRegistryLoginServer string = enableContainerRegistry ? containerRegistryModule!.outputs.loginServer : ''

@description('Application Insights connection string')
output applicationInsightsConnectionString string = enableApplicationInsights ? appInsightsModule!.outputs.connectionString : ''

@description('Generated JWT secret (if auto-generated)')
@secure()
output jwtSecretKey string = finalJwtSecret

@description('Next steps for deployment')
output nextSteps string = '''
========================================
🎉 INFRASTRUCTURE DEPLOYMENT SUCCESSFUL!
========================================

📋 NEXT STEPS:

1️⃣  Grant SQL Database Access to Managed Identity
   ${sqlUseAzureAuth ? '   Run this in Azure Portal → SQL Query Editor:\n   \n   CREATE USER [${appServiceModule.outputs.webAppName}] FROM EXTERNAL PROVIDER;\n   ALTER ROLE db_owner ADD MEMBER [${appServiceModule.outputs.webAppName}];' : '   Skipped - Using SQL authentication'}

2️⃣  Deploy Application Code
   
   cd azure-deployment-template
   ./scripts/deploy-code.ps1 -AppName ${appServiceModule.outputs.webAppName} -ResourceGroup ${resourceGroup().name}

3️⃣  Verify Deployment
   
   🌐 App URL: ${appServiceModule.outputs.webAppUrl}
   🔐 Default Login: admin / Admin@123
   
   ⚠️  IMPORTANT: Change default admin password immediately!

4️⃣  Monitor Application
   
   📊 Application Insights: ${enableApplicationInsights ? 'Enabled' : 'Disabled'}
   📝 Logs: az webapp log tail --name ${appServiceModule.outputs.webAppName} -g ${resourceGroup().name}

========================================
'''
