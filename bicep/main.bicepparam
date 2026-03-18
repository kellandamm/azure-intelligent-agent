using './main.bicep'

// ========================================
// PARAMETERS FILE - Azure Agent Framework Application
// ========================================
// This file configures the deployment. Many resource names are AUTO-GENERATED and
// do not need editing. Only external service credentials (OpenAI, Fabric, Power BI,
// SQL AD admin) must be provided.
//
// AUTO-GENERATED (no edits required):
//   - appName        → unique 13-char prefix derived from resource group ID
//   - sqlServerName  → '{appName}-sql'
//
// REQUIRED (must be set before deployment):
//   - azureOpenAIEndpoint, azureOpenAIApiKey
//   - projectEndpoint
//   - fabricWorkspaceId, fabricOrchestratorAgentId, fabricDocumentAgentId,
//     fabricPowerBiAgentId, fabricChartAgentId, fabricSalesAgentId, fabricRealtimeAgentId
//   - powerbiWorkspaceId, powerbiReportId, powerbiClientId, powerbiTenantId, powerbiClientSecret
//   - sqlAzureAdAdminLogin, sqlAzureAdAdminSid  (if sqlUseAzureAuth = true)
//
// DEPLOY:
//   az deployment group create --template-file main.bicep --parameters main.bicepparam
//   OR: azd up
//
// IMPORTANT: Never commit this file with actual secrets to source control!
// ========================================

// ========================================
// General Configuration
// ========================================

// Prefix for all resource names (3-20 characters, alphanumeric and hyphens only)
// AUTO-GENERATED: If not provided, a unique name is generated from the resource group ID
//   e.g. 'agent3f8a1b2c' - unique per resource group
// OPTIONAL OVERRIDE: Uncomment and set your own value below:
// param appName = 'mycompany-agents'

// Azure region for deployment
// Example: 'eastus2', 'westus2', 'westeurope'
param location = 'westus2'

// Environment (dev/staging/prod) - affects resource names and tags
param environment = 'prod'

// ========================================
// Azure OpenAI Configuration
// ========================================
// Get these values from your Azure OpenAI resource in Azure Portal

// Azure OpenAI service endpoint
// Format: https://<your-resource-name>.openai.azure.com/
param azureOpenAIEndpoint = 'https://demosaifoundry9257402771.services.ai.azure.com/'

// Model deployment name in Azure OpenAI
// Example: 'gpt-4o', 'gpt-35-turbo', 'gpt-4'
param azureOpenAIDeployment = 'gpt-5.2'

// Azure OpenAI API version
param azureOpenAIApiVersion = '2024-08-01-preview'

// Azure OpenAI API Key (from Azure Portal → Keys and Endpoint)
// ⚠️ SENSITIVE: Store in Azure Key Vault or use --parameters @secure-params.json
param azureOpenAIApiKey = ''

// ========================================
// Azure AI Foundry Configuration
// ========================================
// Get these from your Azure AI Foundry project

// Azure AI Foundry project endpoint URL
// Format: https://<project-name>.<region>.api.azureml.ms/agents/v1.0/subscriptions/<sub-id>/...
param projectEndpoint = ''

// Connection name for Azure OpenAI in AI Foundry
param connectionName = 'aoai-connection'

// Model deployment name in AI Foundry (usually same as Azure OpenAI deployment)
param modelDeploymentName = 'gpt-5.2'

// ========================================
// Microsoft Fabric Configuration
// ========================================
// Get these from your Microsoft Fabric workspace

// Fabric workspace ID (GUID)
// Find in Fabric: Workspace Settings → Properties
param fabricWorkspaceId = '<REPLACE_WITH_YOUR_FABRIC_WORKSPACE_ID>'

// Fabric Agent IDs - Create these agents in your Fabric workspace
// Each agent handles specific functionality in the application
param fabricOrchestratorAgentId = '<REPLACE_WITH_ORCHESTRATOR_AGENT_ID>'
param fabricDocumentAgentId = '<REPLACE_WITH_DOCUMENT_AGENT_ID>'
param fabricPowerBiAgentId = '<REPLACE_WITH_POWERBI_AGENT_ID>'
param fabricChartAgentId = '<REPLACE_WITH_CHART_AGENT_ID>'
param fabricSalesAgentId = '<REPLACE_WITH_SALES_AGENT_ID>'
param fabricRealtimeAgentId = '<REPLACE_WITH_REALTIME_AGENT_ID>'

// ========================================
// Power BI Configuration
// ========================================
// Configure Power BI service principal for embedded reports

// Power BI workspace ID (usually same as Fabric workspace ID)
param powerbiWorkspaceId = '<REPLACE_WITH_YOUR_POWERBI_WORKSPACE_ID>'

// Power BI report ID to embed in the application
// Find in Power BI: Report → Settings → Report ID
param powerbiReportId = '<REPLACE_WITH_YOUR_POWERBI_REPORT_ID>'

// Service Principal for Power BI authentication
// Create in Azure AD: App Registrations → New Registration
param powerbiClientId = '<REPLACE_WITH_SERVICE_PRINCIPAL_CLIENT_ID>'
param powerbiTenantId = '<REPLACE_WITH_YOUR_AZURE_TENANT_ID>'

// Service Principal client secret
// ⚠️ SENSITIVE: Store in Azure Key Vault
param powerbiClientSecret = '<REPLACE_WITH_SERVICE_PRINCIPAL_CLIENT_SECRET>'

// ========================================
// SQL Database Configuration
// ========================================

// SQL Server name (must be globally unique, alphanumeric and hyphens only)
// AUTO-GENERATED: Defaults to '{appName}-sql' (e.g. 'agent3f8a1b2c-sql')
// OPTIONAL OVERRIDE: Uncomment and set your own globally-unique name:
// param sqlServerName = 'mycompany-sql-server'

// SQL Database name
param sqlDatabaseName = 'aiagentsdb'

// SQL Database SKU (pricing tier)
// Options: 'Basic', 'S0', 'S1', 'S2', 'P1', 'P2'
// See: https://azure.microsoft.com/pricing/details/sql-database/single/
param sqlDatabaseSku = 'Basic'

// Use Azure AD authentication (recommended for security)
// If true: Web App uses managed identity to connect
// If false: Uses SQL username/password authentication
param sqlUseAzureAuth = true

// SQL admin credentials (only required if sqlUseAzureAuth = false)
param sqlAdminUsername = 'sqladmin'
// ⚠️ SENSITIVE: Store in Azure Key Vault
param sqlAdminPassword = ''

// Azure AD admin configuration (required if sqlUseAzureAuth = true)
// This user/group will have admin access to the SQL database
// Get from Azure AD: Users/Groups → Object ID
// Run: az ad signed-in-user show --query id -o tsv
param sqlAzureAdAdminLogin = 'admin@MngEnv180378.onmicrosoft.com'
param sqlAzureAdAdminSid = '0230cab2-5323-49cd-a9c8-c5a7a51ca9ff'

// ========================================
// Authentication & Security
// ========================================

// Enable JWT authentication for the application
// If true: Requires login, implements Row-Level Security (RLS)
// If false: Open access (not recommended for production)
param enableAuthentication = true

// JWT secret key (leave empty to auto-generate)
// ⚠️ SENSITIVE: Auto-generated secrets are stored in deployment outputs
// For production, provide your own strong secret
param jwtSecretKey = ''

// JWT algorithm (default HS256 is recommended)
param jwtAlgorithm = 'HS256'

// JWT token expiration in minutes
// 43200 = 30 days, 1440 = 1 day, 60 = 1 hour
param jwtExpirationMinutes = 43200

// ========================================
// Infrastructure Configuration
// ========================================

// App Service Plan SKU (pricing tier)
// Options: 'B1', 'B2', 'B3', 'S1', 'S2', 'P1v2', 'P2v2'
// B2 recommended minimum (2 cores, 3.5 GB RAM)
// See: https://azure.microsoft.com/pricing/details/app-service/linux/
param appServicePlanSku = 'B2'

// Enable Application Insights for monitoring, logging, and diagnostics
param enableApplicationInsights = true

// Enable Azure Key Vault for secure secrets management (recommended)
// If true: All secrets stored in Key Vault, Web App accesses via managed identity
// If false: Secrets stored as app settings (less secure)
param enableKeyVault = true

// Enable Azure Container Registry (only needed if building/storing Docker images in Azure)
// If false: Deploy code directly from local/GitHub
param enableContainerRegistry = false

// ========================================
// Policy Compliance Settings
// ========================================
// These settings address the Azure Policy assignments on this subscription.

// Enable Log Analytics Workspace for centralised diagnostic logs.
// Required by MCSB (SecurityCenterBuiltIn): App Service diagnostic logs, Key Vault logs.
// Also switches App Insights to workspace-based mode.
param enableLogAnalyticsWorkspace = true

// Enable SQL Vulnerability Assessment (Express config, no storage account needed).
// Required by MCSB (SecurityCenterBuiltIn): SQL servers should have vulnerability assessment enabled.
param enableSqlVulnerabilityAssessment = true

// Enable VNet integration: deploys a VNet, routes App Service outbound traffic via VNet integration,
// and places SQL behind a private endpoint with public network access disabled.
// REQUIRED for MCAPS compliance — MCAPS deny policy blocks SQL servers with publicNetworkAccess = Enabled.
// Set false only in non-MCAPS environments where a private endpoint is not required.
param enableVnetIntegration = true

// Disable API-key (local) auth on Azure OpenAI — require managed identity only.
// Set true for production to satisfy MCSB identity controls.
// Only applies when deployAzureOpenAI = true.
// NOTE: If true, remove azureOpenAIApiKey from app settings and use managed identity instead.
param disableOpenAILocalAuth = false

// ========================================
// Application Settings
// ========================================

// Application port (default 8000 for FastAPI/uvicorn)
param appPort = 8000

// Enable OpenTelemetry tracing for distributed tracing and diagnostics
param enableTracing = true

// Log level
// Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
param logLevel = 'INFO'

// ========================================
// EXAMPLE CONFIGURATIONS
// ========================================
/*
EXAMPLE 1 - Minimal Development Environment:
-------------------------------------------
param appName = 'dev-agents'
param environment = 'dev'
param appServicePlanSku = 'B1'
param sqlDatabaseSku = 'Basic'
param enableKeyVault = false
param enableContainerRegistry = false
param enableAuthentication = false
param logLevel = 'DEBUG'

EXAMPLE 2 - Production Environment:
----------------------------------
param appName = 'prod-agents'
param environment = 'prod'
param appServicePlanSku = 'P1v2'
param sqlDatabaseSku = 'S2'
param enableKeyVault = true
param enableContainerRegistry = true
param enableAuthentication = true
param logLevel = 'INFO'
param sqlUseAzureAuth = true

EXAMPLE 3 - Staging/Test Environment:
------------------------------------
param appName = 'staging-agents'
param environment = 'staging'
param appServicePlanSku = 'B2'
param sqlDatabaseSku = 'S0'
param enableKeyVault = true
param enableContainerRegistry = false
param enableAuthentication = true
param logLevel = 'INFO'
*/
