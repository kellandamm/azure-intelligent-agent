// ========================================
// Azure Intelligent Agent Starter - Main Bicep Template
// This template deploys a complete Azure infrastructure for intelligent AI agent applications
// using Azure Verified Modules (AVM) for production-ready, secure deployments
// ========================================

targetScope = 'resourceGroup'

// ========================================
// Parameters - General
// ========================================

@description('Name prefix for all resources (e.g., "myagentapp"). Resources will be named like {appName}-{resource}-{environment}. Auto-generated from the resource group ID if not provided.')
@minLength(3)
@maxLength(20)
param appName string = 'agent${take(uniqueString(resourceGroup().id), 8)}'

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
// Parameters - Azure AI Foundry (Required)
// ========================================

@description('Azure AI Foundry project endpoint URL (Required). Find in AI Foundry portal → Project → Settings → Endpoint. Format: https://<resource>.services.ai.azure.com/api/projects/<project-name>')
param projectEndpoint string

@description('Azure AI Foundry connection name for OpenAI')
param connectionName string = 'aoai-connection'

@description('Model deployment name in AI Foundry (e.g., gpt-4o, gpt-5.2)')
param modelDeploymentName string = 'gpt-5.2'

// ========================================
// Parameters - Azure OpenAI (Optional - only if not using Foundry models)
// ========================================

@description('Deploy new Azure OpenAI resource (true) or use existing (false). Leave false to use Foundry models (recommended).')
param deployAzureOpenAI bool = false

@description('Azure OpenAI account name (used when deployAzureOpenAI=true)')
param azureOpenAIName string = '${appName}-openai-${environment}'

@description('Azure OpenAI model name to deploy (e.g., gpt-4o, gpt-4, gpt-35-turbo)')
param azureOpenAIModelName string = 'gpt-5.2'

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

@description('Azure OpenAI service endpoint URL (optional - only needed when deployAzureOpenAI=false and using separate Azure OpenAI)')
param azureOpenAIEndpoint string = ''

@description('Azure OpenAI deployment/model name (e.g., gpt-4o, gpt-35-turbo)')
param azureOpenAIDeployment string = 'gpt-4o'

@description('Azure OpenAI API version')
param azureOpenAIApiVersion string = '2024-08-01-preview'

@description('Azure OpenAI API Key (optional - only needed when using separate Azure OpenAI)')
@secure()
param azureOpenAIApiKey string = ''

// ========================================
// Parameters - Agent IDs (Azure AI Foundry) & Data Platform (Microsoft Fabric)
// ========================================

@description('Microsoft Fabric workspace ID (data platform)')
param fabricWorkspaceId string

@description('Azure AI Foundry Orchestrator Agent ID (Required)')
param orchestratorAgentId string

@description('Azure AI Foundry Sales Agent ID (Required)')
param salesAgentId string

@description('Azure AI Foundry Realtime Agent ID (Required)')
param realtimeAgentId string

@description('Azure AI Foundry Analytics Agent ID (Required)')
param analyticsAgentId string

@description('Azure AI Foundry Financial Agent ID (Required)')
param financialAgentId string

@description('Azure AI Foundry Support Agent ID (Required)')
param supportAgentId string

@description('Azure AI Foundry Operations Coordinator Agent ID (Required)')
param operationsAgentId string

@description('Azure AI Foundry Customer Success Agent ID (Required)')
param customerSuccessAgentId string

@description('Azure AI Foundry Operations Excellence Agent ID (Required)')
param operationsExcellenceAgentId string

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

@description('SQL Server name (must be globally unique). Auto-generated from appName if not provided.')
@minLength(3)
@maxLength(63)
param sqlServerName string = '${appName}-sql'

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

@description('Web App startup command. Uses fallback paths for startup.sh in common zip layouts.')
param appCommandLine string = 'bash -c "if [ -f /home/site/wwwroot/startup.sh ]; then bash /home/site/wwwroot/startup.sh; elif [ -f /home/site/wwwroot/app/startup.sh ]; then bash /home/site/wwwroot/app/startup.sh; else echo startup.sh not found under /home/site/wwwroot; ls -la /home/site/wwwroot; exit 1; fi"'

@description('Enable Key Vault for secrets management')
param enableKeyVault bool = true

@description('Enable Container Registry for Docker images')
param enableContainerRegistry bool = false

@description('Enable Log Analytics Workspace (required for workspace-based App Insights and diagnostic logs). Recommended by MCSB.')
param enableLogAnalyticsWorkspace bool = true

@description('Enable SQL Vulnerability Assessment (Express configuration). Recommended by MCSB.')
param enableSqlVulnerabilityAssessment bool = true

@description('Disable API-key (local) auth on Azure OpenAI and require managed identity. Set true for production to comply with MCSB. Only applies when deployAzureOpenAI = true.')
param disableOpenAILocalAuth bool = false

@description('Enable VNet integration: deploys a VNet, adds App Service outbound integration, and places SQL behind a private endpoint. Required to satisfy the MCAPS deny policy that blocks SQL servers with public network access enabled.')
param enableVnetIntegration bool = true

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

// azd requires this tag on the Web App resource to locate it during 'azd deploy'
var webAppTags = union(tags, { 'azd-service-name': 'web' })

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

  // Microsoft Fabric (data platform)
  { name: 'FABRIC_WORKSPACE_ID', value: fabricWorkspaceId }

  // Azure AI Foundry Agent IDs
  { name: 'ORCHESTRATOR_AGENT_ID', value: orchestratorAgentId }
  { name: 'SALES_AGENT_ID', value: salesAgentId }
  { name: 'REALTIME_AGENT_ID', value: realtimeAgentId }
  { name: 'ANALYTICS_AGENT_ID', value: analyticsAgentId }
  { name: 'FINANCIAL_AGENT_ID', value: financialAgentId }
  { name: 'SUPPORT_AGENT_ID', value: supportAgentId }
  { name: 'OPERATIONS_AGENT_ID', value: operationsAgentId }
  { name: 'CUSTOMER_SUCCESS_AGENT_ID', value: customerSuccessAgentId }
  { name: 'OPERATIONS_EXCELLENCE_AGENT_ID', value: operationsExcellenceAgentId }

  // Agent Backend Selection (Default: Microsoft AI Foundry)
  { name: 'USE_FOUNDRY_AGENTS', value: 'true' }

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
  { name: 'ENABLE_ORYX_BUILD', value: 'true' }
  { name: 'WEBSITES_CONTAINER_START_TIME_LIMIT', value: '1800' }
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
    disableLocalAuth: disableOpenAILocalAuth
  }
}

// ========================================
// Module: Virtual Network
// MCAPS compliance: SQL Server public network access must be disabled.
// A VNet with App Service subnet integration + SQL private endpoint provides
// secure connectivity without public internet exposure.
// ========================================

module networkModule 'modules/network.bicep' = if (enableVnetIntegration) {
  name: 'network-deployment'
  params: {
    vnetName: '${resourceNamePrefix}-vnet'
    location: location
    tags: tags
  }
}

// ========================================
// Module: Log Analytics Workspace (MCSB: centralised diagnostic logs)
// ========================================

module logAnalyticsModule 'modules/logAnalyticsWorkspace.bicep' = if (enableLogAnalyticsWorkspace) {
  name: 'logAnalytics-deployment'
  params: {
    name: '${resourceNamePrefix}-law'
    location: location
    tags: tags
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
    // Pass workspace ID so App Insights switches to workspace-based mode (MCSB recommended)
    logAnalyticsWorkspaceId: enableLogAnalyticsWorkspace ? logAnalyticsModule!.outputs.resourceId : ''
  }
}

// App Insights settings - conditional
var appInsightsSettings = enableApplicationInsights ? [
  { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsModule!.outputs.connectionString }
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
    enableVulnerabilityAssessment: enableSqlVulnerabilityAssessment
    // MCAPS deny policy: SQL public network access must be Disabled; use private endpoint for connectivity.
    publicNetworkAccess: 'Disabled'
    // MCAPS deny policy: SQL outbound network access must be restricted.
    restrictOutboundNetworkAccess: 'Enabled'
  }
}

// ========================================
// Module: SQL Private Endpoint
// Required when SQL publicNetworkAccess is Disabled—gives App Service a private
// IP path to SQL through the VNet without traversing the public internet.
// ========================================

module sqlPrivateEndpointModule 'modules/sqlPrivateEndpoint.bicep' = if (enableVnetIntegration) {
  name: 'sql-private-endpoint-deployment'
  params: {
    privateEndpointName: '${resourceNamePrefix}-sql-pe'
    sqlServerResourceId: sqlServerModule.outputs.resourceId
    subnetId: enableVnetIntegration ? networkModule!.outputs.privateEndpointSubnetId : ''
    vnetId: enableVnetIntegration ? networkModule!.outputs.vnetId : ''
    location: location
    tags: tags
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
    tags: webAppTags
    appServicePlanSku: appServicePlanSku
    pythonVersion: '3.11'
    alwaysOn: true
    appCommandLine: appCommandLine
    enableSystemManagedIdentity: true
    // Pass workspace ID so diagnostic logs are sent to Log Analytics (MCSB)
    logAnalyticsWorkspaceId: enableLogAnalyticsWorkspace ? logAnalyticsModule!.outputs.resourceId : ''
    // Route outbound SQL traffic through VNet to reach private endpoint
    vnetSubnetId: enableVnetIntegration ? networkModule!.outputs.appServiceSubnetId : ''
  }
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
    targetResourceId: enableKeyVault ? keyVaultModule!.outputs.resourceId : ''
  }
}

// NOTE: SQL managed identity user creation (CREATE USER ... FROM EXTERNAL PROVIDER)
// is an in-database DDL operation and cannot be done through an ARM/Bicep role assignment.
// It is handled automatically by setup_mi_user.py on first application startup.

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

@description('Log Analytics Workspace resource ID')
output logAnalyticsWorkspaceId string = enableLogAnalyticsWorkspace ? logAnalyticsModule!.outputs.resourceId : ''

@description('Log Analytics Workspace name')
output logAnalyticsWorkspaceName string = enableLogAnalyticsWorkspace ? logAnalyticsModule!.outputs.name : ''

@description('VNet name (deployed when enableVnetIntegration = true)')
output vnetName string = enableVnetIntegration ? networkModule!.outputs.vnetName : ''

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
