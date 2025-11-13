# Parameters Reference Guide

Complete reference for all Bicep deployment parameters.

---

## 📖 Table of Contents

- [General Configuration](#general-configuration)
- [Azure OpenAI](#azure-openai)
- [Azure AI Foundry](#azure-ai-foundry)
- [Microsoft Fabric](#microsoft-fabric)
- [Power BI](#power-bi)
- [SQL Database](#sql-database)
- [Authentication & Security](#authentication--security)
- [Infrastructure](#infrastructure)
- [Application Settings](#application-settings)

---

## General Configuration

### `appName`
- **Type**: string
- **Required**: Yes
- **Constraints**: 3-20 characters, alphanumeric and hyphens
- **Description**: Prefix for all Azure resource names
- **Example**: `mycompany-agents`, `prod-ai-app`
- **Notes**: Used to generate unique names like `{appName}-{environment}-app`

### `location`
- **Type**: string
- **Required**: No
- **Default**: Resource group location
- **Description**: Azure region for all resources
- **Common Values**: `eastus2`, `westus2`, `westeurope`, `southeastasia`
- **Example**: `eastus2`

### `environment`
- **Type**: string
- **Required**: No
- **Default**: `prod`
- **Options**: `dev`, `staging`, `prod`
- **Description**: Environment tag added to all resources
- **Example**: `prod`

---

## Azure OpenAI

### `azureOpenAIEndpoint`
- **Type**: string
- **Required**: Yes
- **Format**: `https://<resource-name>.openai.azure.com/`
- **Description**: Your Azure OpenAI service endpoint URL
- **Where to Find**: Azure Portal → Azure OpenAI → Keys and Endpoint
- **Example**: `https://myopenai.openai.azure.com/`

### `azureOpenAIDeployment`
- **Type**: string
- **Required**: No
- **Default**: `gpt-4o`
- **Description**: Model deployment name in Azure OpenAI
- **Common Values**: `gpt-4o`, `gpt-4`, `gpt-35-turbo`, `gpt-4-turbo`
- **Example**: `gpt-4o`

### `azureOpenAIApiVersion`
- **Type**: string
- **Required**: No
- **Default**: `2024-08-01-preview`
- **Description**: Azure OpenAI API version
- **Example**: `2024-08-01-preview`
- **Notes**: See [API versions](https://learn.microsoft.com/azure/ai-services/openai/reference)

### `azureOpenAIApiKey`
- **Type**: string (secure)
- **Required**: Yes
- **Description**: Azure OpenAI API key for authentication
- **Where to Find**: Azure Portal → Azure OpenAI → Keys and Endpoint
- **Security**: ⚠️ Never commit to source control. Use Key Vault or secure parameter files.
- **Example**: `sk-...` (64 characters)

---

## Azure AI Foundry

### `projectEndpoint`
- **Type**: string
- **Required**: Yes
- **Format**: Long URL with subscription, resource group, and project IDs
- **Description**: Azure AI Foundry project endpoint for agents API
- **Where to Find**: AI Foundry Portal → Project → Settings → Endpoint
- **Example**: `https://eastus2.api.azureml.ms/agents/v1.0/subscriptions/xxx/resourceGroups/xxx/providers/Microsoft.MachineLearningServices/workspaces/xxx`

### `connectionName`
- **Type**: string
- **Required**: No
- **Default**: `aoai-connection`
- **Description**: Name of the Azure OpenAI connection in AI Foundry
- **Where to Find**: AI Foundry Portal → Project → Connections
- **Example**: `aoai-connection`

### `modelDeploymentName`
- **Type**: string
- **Required**: No
- **Default**: `gpt-4o`
- **Description**: Model deployment name used by AI Foundry agents
- **Example**: `gpt-4o`
- **Notes**: Usually matches `azureOpenAIDeployment`

---

## Microsoft Fabric

### `fabricWorkspaceId`
- **Type**: string (GUID)
- **Required**: Yes
- **Format**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Description**: Microsoft Fabric workspace ID
- **Where to Find**: Fabric → Workspace → Settings → Properties → Workspace ID
- **Example**: `8c9fe5d7-6b49-4191-a9fd-6deb8622a433`

### Fabric Agent IDs

All agent ID parameters follow the same pattern:

#### `fabricOrchestratorAgentId`
- **Type**: string
- **Required**: Yes
- **Format**: `asst_xxxxxxxxxxxxxxxxxxxxx`
- **Description**: Main orchestrator agent that routes requests
- **Where to Find**: Fabric → Data Science → Agents → Agent ID
- **Example**: `asst_YXmaCOM5JdgKQLhte0Xs2Yib`

#### `fabricDocumentAgentId`
- **Description**: Agent for document processing and analysis
- **Example**: `asst_CqY1VZC9w5dxlBGYjAUyqjv2`

#### `fabricPowerBiAgentId`
- **Description**: Agent for Power BI queries and insights
- **Example**: `asst_A9mJ7HEqWmYoVgBU89hxiJFc`

#### `fabricChartAgentId`
- **Description**: Agent for chart generation and visualization
- **Example**: `asst_qpB2TqtNvlYSoK1oSrXZVfNz`

#### `fabricSalesAgentId`
- **Description**: Agent for sales data analysis
- **Example**: `asst_dW0oVcgujQZQviiKN8fIHYjr`

#### `fabricRealtimeAgentId`
- **Description**: Agent for real-time data processing
- **Example**: `asst_Efk1OcPxVlWlQ4trfAWcvpPU`

---

## Power BI

### `powerbiWorkspaceId`
- **Type**: string (GUID)
- **Required**: Yes
- **Description**: Power BI workspace ID (often same as Fabric workspace)
- **Where to Find**: Power BI → Workspace → Settings → Workspace ID
- **Example**: `8c9fe5d7-6b49-4191-a9fd-6deb8622a433`

### `powerbiReportId`
- **Type**: string (GUID)
- **Required**: Yes
- **Description**: Power BI report ID to embed
- **Where to Find**: Power BI → Report → File → Embed Report → Report ID
- **Example**: `4d7508a9-73eb-492d-832c-9278d5d557fa`

### `powerbiClientId`
- **Type**: string (GUID)
- **Required**: Yes
- **Description**: Service principal (app registration) client ID
- **Where to Find**: Azure AD → App Registrations → Your App → Application ID
- **Example**: `3100ba38-10f7-4cbe-a646-841a956d18d5`
- **Notes**: Must have access to Power BI workspace

### `powerbiTenantId`
- **Type**: string (GUID)
- **Required**: Yes
- **Description**: Azure AD tenant ID
- **Where to Find**: Azure Portal → Azure Active Directory → Properties → Tenant ID
- **Example**: `4c585a33-3574-42d3-86a8-13d7b5c36f8e`

### `powerbiClientSecret`
- **Type**: string (secure)
- **Required**: Yes
- **Description**: Service principal client secret
- **Where to Find**: Azure AD → App Registrations → Your App → Certificates & secrets → New secret
- **Security**: ⚠️ Never commit to source control
- **Example**: `xxx~yyyyyy...` (varies in length)

---

## SQL Database

### `sqlServerName`
- **Type**: string
- **Required**: Yes
- **Constraints**: 3-63 characters, lowercase, alphanumeric and hyphens, globally unique
- **Description**: SQL Server name
- **Example**: `mycompany-sql-server`, `agents-db-prod`
- **Notes**: Must be globally unique across all Azure

### `sqlDatabaseName`
- **Type**: string
- **Required**: No
- **Default**: `aiagentsdb`
- **Description**: SQL Database name
- **Example**: `aiagentsdb`, `production-db`

### `sqlDatabaseSku`
- **Type**: string
- **Required**: No
- **Default**: `Basic`
- **Options**: `Basic`, `S0`, `S1`, `S2`, `S3`, `P1`, `P2`, `P4`, `P6`
- **Description**: SQL Database pricing tier
- **Cost Guide**:
  - `Basic`: ~$5/month (5 DTUs, 2GB)
  - `S0`: ~$15/month (10 DTUs, 250GB)
  - `S1`: ~$30/month (20 DTUs, 250GB)
  - `S2`: ~$120/month (50 DTUs, 250GB)
  - `P1`: ~$465/month (125 DTUs, 500GB)
- **Recommendation**: `Basic` for dev, `S1`/`S2` for production

### `sqlUseAzureAuth`
- **Type**: boolean
- **Required**: No
- **Default**: `true`
- **Description**: Use Azure AD authentication (managed identity)
- **Recommendation**: `true` for better security
- **If true**: Web App uses managed identity (no passwords)
- **If false**: Uses SQL username/password authentication

### `sqlAdminUsername`
- **Type**: string
- **Required**: Only if `sqlUseAzureAuth = false`
- **Default**: `sqladmin`
- **Description**: SQL admin username
- **Example**: `sqladmin`, `dbadmin`

### `sqlAdminPassword`
- **Type**: string (secure)
- **Required**: Only if `sqlUseAzureAuth = false`
- **Description**: SQL admin password
- **Constraints**: 8+ characters, uppercase, lowercase, number, special char
- **Security**: ⚠️ Never commit to source control

### `sqlAzureAdAdminLogin`
- **Type**: string
- **Required**: Only if `sqlUseAzureAuth = true`
- **Format**: Email address or UPN
- **Description**: Azure AD admin user/group for SQL
- **Where to Find**: Azure AD → Users → Select user → User Principal Name
- **Example**: `admin@mycompany.com`

### `sqlAzureAdAdminSid`
- **Type**: string (GUID)
- **Required**: Only if `sqlUseAzureAuth = true`
- **Description**: Azure AD Object ID of admin user/group
- **Where to Find**: Azure AD → Users → Select user → Object ID
- **Example**: `12345678-1234-1234-1234-123456789012`

---

## Authentication & Security

### `enableAuthentication`
- **Type**: boolean
- **Required**: No
- **Default**: `true`
- **Description**: Enable JWT authentication and Row-Level Security (RLS)
- **If true**: Users must log in, RLS enforced
- **If false**: Open access (not recommended for production)
- **Recommendation**: `true` for production, can be `false` for demos

### `jwtSecretKey`
- **Type**: string (secure)
- **Required**: No (auto-generated if empty)
- **Description**: Secret key for signing JWT tokens
- **Security**: ⚠️ Auto-generated secrets shown in deployment outputs
- **Recommendation**: Provide your own strong secret for production
- **Example**: Use `openssl rand -base64 32` to generate

### `jwtAlgorithm`
- **Type**: string
- **Required**: No
- **Default**: `HS256`
- **Options**: `HS256`, `HS384`, `HS512`
- **Description**: JWT signing algorithm
- **Recommendation**: `HS256` is sufficient for most use cases

### `jwtExpirationMinutes`
- **Type**: integer
- **Required**: No
- **Default**: `43200` (30 days)
- **Range**: 30 - 43200 minutes
- **Description**: JWT token expiration time
- **Common Values**:
  - `60` = 1 hour
  - `480` = 8 hours
  - `1440` = 1 day
  - `10080` = 7 days
  - `43200` = 30 days

---

## Infrastructure

### `appServicePlanSku`
- **Type**: string
- **Required**: No
- **Default**: `B2`
- **Options**: `B1`, `B2`, `B3`, `S1`, `S2`, `S3`, `P1v2`, `P2v2`, `P3v2`
- **Description**: App Service Plan pricing tier
- **Specifications**:
  - `B1`: 1 core, 1.75 GB RAM (~$13/month)
  - `B2`: 2 cores, 3.5 GB RAM (~$26/month)
  - `B3`: 4 cores, 7 GB RAM (~$52/month)
  - `S1`: 1 core, 1.75 GB RAM (~$70/month) + staging slots
  - `P1v2`: 1 core, 3.5 GB RAM (~$145/month) + auto-scale
  - `P2v2`: 2 cores, 7 GB RAM (~$290/month) + auto-scale
- **Recommendation**: `B2` minimum, `P1v2`+ for production

### `enableApplicationInsights`
- **Type**: boolean
- **Required**: No
- **Default**: `true`
- **Description**: Deploy Application Insights for monitoring
- **Features**: Logs, metrics, distributed tracing, alerts, live metrics
- **Cost**: ~$2-10/month depending on usage
- **Recommendation**: `true` for all environments

### `enableKeyVault`
- **Type**: boolean
- **Required**: No
- **Default**: `true`
- **Description**: Deploy Azure Key Vault for secrets management
- **Benefits**: Centralized secrets, access auditing, automatic rotation support
- **Cost**: ~$1/month
- **Recommendation**: `true` for production, can be `false` for dev/demos

### `enableContainerRegistry`
- **Type**: boolean
- **Required**: No
- **Default**: `false`
- **Description**: Deploy Azure Container Registry
- **When Needed**: If building Docker images in Azure
- **Cost**: Standard SKU ~$20/month
- **Recommendation**: `false` unless using containers

---

## Application Settings

### `appPort`
- **Type**: integer
- **Required**: No
- **Default**: `8000`
- **Description**: Port the FastAPI application listens on
- **Notes**: Internal port, external is always 80/443

### `enableTracing`
- **Type**: boolean
- **Required**: No
- **Default**: `true`
- **Description**: Enable OpenTelemetry distributed tracing
- **Benefits**: End-to-end request tracking, performance analysis
- **Recommendation**: `true` for production

### `logLevel`
- **Type**: string
- **Required**: No
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Application log level
- **Recommendations**:
  - Dev: `DEBUG`
  - Staging: `INFO`
  - Production: `INFO` or `WARNING`

---

## 📝 Example Configurations

### Minimal Development
```bicep
param appName = 'dev-agents'
param environment = 'dev'
param appServicePlanSku = 'B1'
param sqlDatabaseSku = 'Basic'
param enableKeyVault = false
param enableAuthentication = false
param logLevel = 'DEBUG'
```

### Production
```bicep
param appName = 'prod-agents'
param environment = 'prod'
param appServicePlanSku = 'P1v2'
param sqlDatabaseSku = 'S2'
param enableKeyVault = true
param enableAuthentication = true
param sqlUseAzureAuth = true
param logLevel = 'INFO'
```

---

## 🔒 Security Best Practices

1. **Never commit secrets** to source control
2. **Use Key Vault** (`enableKeyVault = true`) for production
3. **Enable Azure AD authentication** (`sqlUseAzureAuth = true`) for SQL
4. **Use managed identities** instead of passwords where possible
5. **Enable authentication** (`enableAuthentication = true`) for production
6. **Use strong JWT secrets** (auto-generate or provide your own)
7. **Configure appropriate token expiration** (`jwtExpirationMinutes`)

---

## 💡 Tips

- Use **parameter files** for different environments (dev, staging, prod)
- Store **secure parameters** in Azure Key Vault or use `--parameters @secure-params.json`
- Test with **minimal SKUs** (B1, Basic) before scaling up
- Use **Azure Cost Management** to monitor spending
- Enable **Application Insights** early for debugging

---

## 📚 Related Documentation

- [Main README](../README.md)
- [Quick Start Guide](QUICK_START.md)
- [Troubleshooting Guide](../README.md#-troubleshooting)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)

---

**Need help?** Check the [README](../README.md) or review [Azure documentation](https://learn.microsoft.com/azure/).
