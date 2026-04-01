# Configuration Reference

All Bicep parameters and application environment variables for the Azure Intelligent Agent.

---

## `bicep/main.bicepparam` — Bicep Parameters

### General

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `location` | No | Resource group location | Azure region for all resources |
| `environment` | No | `prod` | Environment tag (`dev`, `staging`, `prod`) |

> `appName` and `sqlServerName` are **auto-generated** from the resource group ID — do not set them unless you need a custom name prefix.

---

### Azure OpenAI

| Parameter | Required | Description | Where to find |
|-----------|----------|-------------|---------------|
| `azureOpenAIEndpoint` | Yes* | Service endpoint URL | Portal → Azure OpenAI → Keys and Endpoint |
| `azureOpenAIApiKey` | Yes* | API key | Portal → Azure OpenAI → Keys and Endpoint |
| `azureOpenAIDeployment` | No (default: `gpt-4o`) | Model deployment name | Portal → Azure OpenAI → Model deployments |
| `azureOpenAIApiVersion` | No (default: `2024-08-01-preview`) | API version | — |
| `deployAzureOpenAI` | No (default: `false`) | Deploy a new OpenAI account via Bicep | — |
| `azureOpenAIModelName` | Only if `deployAzureOpenAI = true` | Model to deploy | — |
| `azureOpenAIModelVersion` | Only if `deployAzureOpenAI = true` | Model version (e.g. `2024-11-20`) | — |
| `azureOpenAIModelCapacity` | Only if `deployAzureOpenAI = true` | Tokens per minute (thousands) | — |

*Not required when `deployAzureOpenAI = true` — values are generated and injected automatically.

**Models supported:** `gpt-4o`, `gpt-4o-mini`, `gpt-4`, `gpt-35-turbo`

---

### Azure AI Foundry

| Parameter | Required | Description | Where to find |
|-----------|----------|-------------|---------------|
| `projectEndpoint` | No | AI Foundry project endpoint | AI Foundry Portal → Project → Settings → Endpoint |
| `connectionName` | No (default: `aoai-connection`) | Azure OpenAI connection name | AI Foundry Portal → Project → Connections |
| `modelDeploymentName` | No (default: `gpt-4o`) | Model deployment name used by agents | — |
| `deployAIFoundry` | No (default: `false`) | Deploy AI Foundry hub/project via Bicep (preview) | — |

> AI Foundry **agents** cannot be deployed via Bicep — they must be created manually in the portal (see [docs/QUICK_START.md — Phase 3](docs/QUICK_START.md#phase-3--configure-ai-services)).

---

### Microsoft Fabric

| Parameter | Required | Description | Where to find |
|-----------|----------|-------------|---------------|
| `fabricWorkspaceId` | No | Workspace GUID | Fabric portal → Workspace → Settings → Properties |
| `fabricOrchestratorAgentId` | No | Main routing agent ID | Fabric → Data Science → Agents |
| `fabricSalesAgentId` | No | Sales specialist agent ID | Fabric → Data Science → Agents |
| `fabricRealtimeAgentId` | No | Operations/real-time agent ID | Fabric → Data Science → Agents |
| `fabricDocumentAgentId` | No | Document processing agent ID | Fabric → Data Science → Agents |
| `fabricPowerBiAgentId` | No | Power BI query agent ID | Fabric → Data Science → Agents |
| `fabricChartAgentId` | No | Chart generation agent ID | Fabric → Data Science → Agents |

*Agent ID format:** The application uses the Responses API. You must provide the fully qualified Azure Resource Manager (ARM) ID of the **Published** Agent. 
*Example:* `/subscriptions/<sub-id>/resourceGroups/<rg-name>/providers/Microsoft.CognitiveServices/accounts/<account-name>/projects/<project-name>/applications/SalesAssistant`

Microsoft Fabric cannot be deployed via Bicep. See [docs/FABRIC_DEPLOYMENT.md](docs/FABRIC_DEPLOYMENT.md) for manual setup steps.

---

### Power BI

| Parameter | Required | Description | Where to find |
|-----------|----------|-------------|---------------|
| `powerbiWorkspaceId` | No | Workspace GUID | Power BI → Workspace → Settings |
| `powerbiReportId` | No | Report GUID to embed | Power BI → Report URL |
| `powerbiClientId` | No | Service principal client ID | Azure AD → App Registrations → Application ID |
| `powerbiTenantId` | No | Azure AD tenant ID | Azure Portal → Azure AD → Properties → Tenant ID |
| `powerbiClientSecret` | No | Service principal secret | Azure AD → App Registrations → Certificates & secrets |

For service principal setup instructions see [docs/QUICK_START.md](docs/QUICK_START.md) or the [Power BI Embedded docs](https://learn.microsoft.com/power-bi/developer/embedded/).

---

### SQL Database

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `sqlDatabaseName` | No | `aiagentsdb` | Database name |
| `sqlDatabaseSku` | No | `Basic` | Pricing tier (`Basic` ~$5/mo, `S0` ~$15/mo, `S2` ~$120/mo, `P1` ~$465/mo) |
| `sqlUseAzureAuth` | No | `true` | Use managed identity auth (recommended) |
| `sqlAzureAdAdminLogin` | **Yes** | — | Azure AD admin UPN — `az ad signed-in-user show --query userPrincipalName -o tsv` |
| `sqlAzureAdAdminSid` | **Yes** | — | Azure AD admin object ID — `az ad signed-in-user show --query id -o tsv` |
| `sqlAdminUsername` | Only if `sqlUseAzureAuth = false` | `sqladmin` | SQL login username |
| `sqlAdminPassword` | Only if `sqlUseAzureAuth = false` | — | SQL login password |

> ⚠️ `sqlAzureAdAdminLogin` and `sqlAzureAdAdminSid` **cannot be empty**. Azure Policy blocks deployment if the inline `administrators` block is missing from the SQL server resource.

> The App Service managed identity is granted database access (`CREATE USER ... FROM EXTERNAL PROVIDER`) **automatically on first startup** — no manual SQL step required. If auto-grant fails, see Phase 5 of [docs/QUICK_START.md](docs/QUICK_START.md#phase-5--sql-access) for the fallback manual steps.

---

### Authentication & Security

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `enableAuthentication` | No | `true` | Enable JWT auth and Row-Level Security |
| `jwtSecretKey` | No | **Auto-generated** | JWT signing secret — Bicep generates `uniqueString(...)` if left blank; stored in Key Vault automatically |
| `jwtAlgorithm` | No | `HS256` | JWT algorithm (`HS256`, `HS384`, `HS512`) |
| `jwtExpirationMinutes` | No | `43200` (30 days) | Token lifetime (60=1h, 1440=1d, 10080=7d) |

To use your own secret instead of the auto-generated one: `param jwtSecretKey = '<openssl rand -base64 32>'`

---

### Infrastructure

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `appServicePlanSku` | No | `B2` | App Service tier (`B1`=1c/1.75GB ~$13, `B2`=2c/3.5GB ~$26, `P1v2`=1c/3.5GB ~$145) |
| `enableVnetIntegration` | No | `true` | Deploy VNet + private endpoint for SQL (required in policy-enforced subscriptions) |
| `enableApplicationInsights` | No | `true` | Deploy Application Insights |
| `enableKeyVault` | No | `true` | Deploy Key Vault for secrets management |
| `enableContainerRegistry` | No | `false` | Deploy Azure Container Registry |

---

### Application Settings

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `logLevel` | No | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `enableTracing` | No | `true` | Enable OpenTelemetry distributed tracing |
| `appPort` | No | `8000` | Internal application port |

---

## Environment Variables (App Service Settings)

These are set in Azure App Service → Configuration → Application settings. For local development, set them in `app/.env`.

Set via CLI:

```powershell
az webapp config appsettings set --name <app-name> -g <rg-name> --settings KEY=VALUE
```

### Core (Required for chat to work)

| Variable | Description |
|----------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name (e.g. `gpt-4o`) |
| `AZURE_OPENAI_API_VERSION` | API version (e.g. `2024-08-01-preview`) |
| `JWT_SECRET` | JWT signing key |
| `SQL_SERVER` | SQL server FQDN (e.g. `myserver.database.windows.net`) |
| `SQL_DATABASE` | Database name |

### Optional

| Variable | Description |
|----------|-------------|
| `ENABLE_AUTHENTICATION` | `true` / `false` (default `true`) |
| `SQL_USE_AZURE_AUTH` | `true` to use managed identity (recommended) |
| `PROJECT_ENDPOINT` | Azure AI Foundry project endpoint |
| `PROJECT_CONNECTION_STRING` | AI Foundry project connection string (preferred over `PROJECT_ENDPOINT`) |
| `USE_FOUNDRY_AGENTS` | `true` to route chat through Azure AI Foundry agents (default `false`) |
| `FABRIC_WORKSPACE_ID` | Fabric workspace GUID |
| `FABRIC_ORCHESTRATOR_AGENT_ID` | Orchestrator agent ID (`asst_...`) |
| `FABRIC_SALES_AGENT_ID` | Sales agent ID |
| `FABRIC_REALTIME_AGENT_ID` | Operations/real-time agent ID |
| `POWERBI_WORKSPACE_ID` | Power BI workspace GUID |
| `POWERBI_REPORT_ID` | Power BI report GUID |
| `POWERBI_CLIENT_ID` | Service principal client ID |
| `POWERBI_CLIENT_SECRET` | Service principal secret |
| `POWERBI_TENANT_ID` | Azure AD tenant ID |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `WEBSITES_CONTAINER_START_TIME_LIMIT` | `1800` — increase container start timeout |

---

## Network Architecture

Azure Policy requires SQL servers to have `publicNetworkAccess` disabled. This template satisfies that requirement with a private network topology:

```
Azure Virtual Network (10.100.0.0/16)
├── appservice-subnet (10.100.1.0/24)    ← App Service outbound VNet integration
└── private-endpoint-subnet (10.100.2.0/24)
        └── SQL Private Endpoint
                ↕  private IP, no public internet
            Azure SQL Server (publicNetworkAccess: Disabled)
```

All four components are deployed together when `enableVnetIntegration = true`:

| Resource | Purpose |
|----------|---------|
| Virtual Network | Isolates SQL from the internet |
| App Service VNet Integration | Routes App Service outbound traffic through the VNet |
| SQL Private Endpoint | Assigns SQL a private IP inside the VNet |
| Private DNS Zone | Resolves `*.database.windows.net` to the private IP |

> Set `enableVnetIntegration = false` only in sandbox subscriptions without Azure Policy enforcement.

---

## Security Checklist

- [ ] `bicep/main.bicepparam` is in `.gitignore` — never commit secrets
- [ ] `app/.env` is in `.gitignore`
- [ ] JWT secret is a randomly generated 32+ character string
- [ ] `sqlUseAzureAuth = true` — SQL uses managed identity, no passwords
- [ ] `enableAuthentication = true` for all non-demo environments
- [ ] Key Vault enabled (`enableKeyVault = true`) for production
- [ ] Rotate JWT secret every 90 days
- [ ] Rotate Power BI service principal secret every 6 months

---

## Example Parameter Files

### Minimal development

```bicep
using './main.bicep'

param azureOpenAIEndpoint  = 'https://your-openai.openai.azure.com/'
param azureOpenAIApiKey    = '<key>'
param sqlAzureAdAdminLogin = 'dev@yourcompany.com'
param sqlAzureAdAdminSid   = '<object-id>'
param appServicePlanSku    = 'B1'
param sqlDatabaseSku       = 'Basic'
param enableAuthentication = false
param logLevel             = 'DEBUG'
```

### Production

```bicep
using './main.bicep'

param azureOpenAIEndpoint  = 'https://your-openai.openai.azure.com/'
param azureOpenAIApiKey    = '<key>'
param sqlAzureAdAdminLogin = 'admin@yourcompany.com'
param sqlAzureAdAdminSid   = '<object-id>'
param appServicePlanSku    = 'P1v2'
param sqlDatabaseSku       = 'S2'
param enableAuthentication = true
param enableKeyVault       = true
param sqlUseAzureAuth      = true
param logLevel             = 'INFO'
```
