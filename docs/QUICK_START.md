# Deployment Guide

Deploy the Azure Intelligent Agent from zero to running in approximately 20 minutes.

---

## Prerequisites

Have these ready before starting:

- [ ] **Azure CLI** installed and logged in (`az login`)
- [ ] **Python 3.11+** installed
- [ ] **Azure subscription** with Contributor access to a resource group
- [ ] **Azure OpenAI** resource with a GPT-4o model deployed
  - _Or set `deployAzureOpenAI = true` in parameters to deploy one as part of the Bicep template_
- [ ] Your **Azure AD UPN**: `az ad signed-in-user show --query userPrincipalName -o tsv`
- [ ] Your **Azure AD object ID**: `az ad signed-in-user show --query id -o tsv`

---

## Phase 1 — Configure Parameters (5 min)

Open `bicep/main.bicepparam` and fill in your values. Most fields are optional — start with the required ones.

### Required fields

```bicep
using './main.bicep'

// Azure OpenAI — Azure Portal → AI Services → Keys and Endpoint
param azureOpenAIEndpoint = 'https://your-openai.openai.azure.com/'
param azureOpenAIApiKey   = '<your-api-key>'

// SQL Azure AD admin — cannot be blank (Azure Policy enforces this)
param sqlAzureAdAdminLogin = 'admin@yourcompany.com'   // az ad signed-in-user show --query userPrincipalName -o tsv
param sqlAzureAdAdminSid   = '<your-object-id>'        // az ad signed-in-user show --query id -o tsv
```

### Deploy a new Azure OpenAI instead (optional)

If you do not have an existing Azure OpenAI resource, let Bicep deploy one:

```bicep
param deployAzureOpenAI        = true
param azureOpenAIModelName     = 'gpt-4o'
param azureOpenAIModelVersion  = '2024-11-20'
param azureOpenAIModelCapacity = 10   // tokens per minute (thousands)
```

Remove the `azureOpenAIEndpoint` and `azureOpenAIApiKey` lines — the endpoint and key are injected into App Settings automatically after deployment.

### Optional integrations

Fill these in now if you have them, or return to add them in Phase 3 (AI Foundry) and Phase 6 (Fabric):

```bicep
// Azure AI Foundry — AI Foundry Portal → Project → Settings → Endpoint
param projectEndpoint = 'https://<project>.<region>.api.azureml.ms/agents/v1.0/...'

// Microsoft Fabric
param fabricWorkspaceId         = '<workspace-GUID>'
param fabricOrchestratorAgentId = 'asst_...'
param fabricSalesAgentId        = 'asst_...'
param fabricRealtimeAgentId     = 'asst_...'

// Power BI embedding
param powerbiWorkspaceId    = '<GUID>'
param powerbiReportId       = '<GUID>'
param powerbiClientId       = '<GUID>'
param powerbiTenantId       = '<GUID>'
param powerbiClientSecret   = '<secret>'
```

> ⚠️ Never commit `bicep/main.bicepparam` to git — it contains secrets. It is already in `.gitignore`.

See [CONFIGURATION.md](../CONFIGURATION.md) for a complete reference of every parameter.

---

## Phase 2 — Deploy Infrastructure (8–15 min)

Choose **one** method:

### Option A: PowerShell (recommended)

```powershell
# Create resource group
az group create --name rg-myagents-prod --location eastus2

# Deploy infrastructure + app code
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod"
```

To update only the app code after changes (no infra rebuild):

```powershell
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod" `
                     -AppName "<your-app-name>" `
                     -SkipInfrastructure
```

### Option B: Azure Developer CLI

```bash
# Install azd if needed: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd
azd init
azd env set AZURE_LOCATION eastus2
azd up
```

For full azd details see [AZD_DEPLOYMENT_GUIDE.md](AZD_DEPLOYMENT_GUIDE.md).

### Confirm a healthy start

Note your app name from the deployment output (e.g. `agentjo5a6tek-prod-app`), then tail the startup logs:

```powershell
az webapp log tail --name <app-name> --resource-group rg-myagents-prod
```

A healthy start looks like:

```
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Booting worker with pid: ...
Application startup complete.
```

If you see errors, jump to [Troubleshooting](#troubleshooting) below.

---

## Phase 3 — Configure AI Services

### Using an existing Azure OpenAI

If you set `azureOpenAIEndpoint` and `azureOpenAIApiKey` in Phase 1, the Bicep template pushes those into App Settings automatically. Verify:

```powershell
az webapp config appsettings list \
  --name <app-name> --resource-group rg-myagents-prod \
  --query "[?name=='AZURE_OPENAI_ENDPOINT'].value" -o tsv
```

### Deploying a new Azure OpenAI (`deployAzureOpenAI = true`)

The endpoint is wired up automatically. The API key is written to Key Vault and referenced by App Settings. To retrieve the key if needed:

```powershell
az keyvault secret show \
  --vault-name <keyvault-name> \
  --name azureOpenAIApiKey \
  --query value -o tsv
```

### Azure AI Foundry agents

AI Foundry agents cannot be provisioned via Bicep — they must be created in the AI Foundry portal.
By default the app uses the **code-based agent backend** (no Foundry required). Follow Stage A + B below to switch to the Foundry backend.

#### Stage A — Create agents and store their IDs

1. Open [https://ai.azure.com](https://ai.azure.com) and navigate to your project
2. Go to **Agents** → **+ New agent**
3. Create one agent for each role: Orchestrator, Sales, Operations, Analytics, Financial, Support, Customer Success, Operations Excellence
4. Copy each agent ID (`asst_xxx...`) and the **Project connection string** from **Project** → **Settings** → **Connection string**
5. Run the helper script — it prompts for each ID and applies them all in one step:

```powershell
.\scripts\set-agent-ids.ps1 -ResourceGroupName "rg-myagents-prod" -AppName "<app-name>"
```

The script sets all App Settings, automatically sets `USE_FOUNDRY_AGENTS=true`, and restarts the app. Re-run at any time to add or update IDs.

#### Stage B — Activate the Foundry backend

The script above sets `USE_FOUNDRY_AGENTS=true` automatically when at least one agent ID is provided. If you need to toggle it manually:

```powershell
# Enable Foundry backend
az webapp config appsettings set `
  --name <app-name> --resource-group rg-myagents-prod `
  --settings USE_FOUNDRY_AGENTS=true
az webapp restart --name <app-name> --resource-group rg-myagents-prod

# Revert to code-based backend at any time (no data loss)
az webapp config appsettings set `
  --name <app-name> --resource-group rg-myagents-prod `
  --settings USE_FOUNDRY_AGENTS=false
az webapp restart --name <app-name> --resource-group rg-myagents-prod
```

Confirm the active backend in the startup log:
```
🤖 Agent backend: Azure AI Foundry        ← Foundry path active
🤖 Agent backend: AgentFramework (code-based)  ← default path
```

> **Note:** without `USE_FOUNDRY_AGENTS=true` the agent IDs are stored but the app continues using the code-based backend. All chat endpoints, auth logic, and UI remain identical regardless of which backend is active.

### Power BI service principal _(optional)_

> Skip this section if you don't need Power BI report embedding.

The Power BI **service principal** (Azure AD app registration) can be created automatically:

```powershell
# Creates the app registration + secret, prints all values, optionally applies them to App Service
.\scripts\setup-powerbi.ps1 -ResourceGroupName "rg-myagents-prod" -AppName "<app-name>"
```

Two steps remain in the portal after the script completes (they require tenant admin access):

1. **Power BI Admin portal** → Tenant settings → Developer settings → Enable _"Service principals can use Power BI APIs"_ → add the service principal
2. **Your Power BI workspace** → Access → add the service principal as **Member**

The script prints exactly where to go for each step.

---

## Phase 4 — Enable Authentication

### Deploy the security schema and seed data

Run these three SQL files **in order** via **Azure Portal → SQL Database → Query Editor**
(authenticate with your Azure AD account):

1. `app/Fabric/auth_schema.sql` — creates Users, Roles, Permissions tables and stored procedures
2. `app/Fabric/rls_security_policies.sql` — creates the Security schema, session context stored procs, and RLS predicate functions
3. `app/Fabric/synthetic_data.sql` — seeds all business data: operational tables, star-schema, and 9 Gold analytics tables used by the AI agents and dashboards

All three scripts are safe to re-run.

For full details on roles, RLS, and territory assignments see [SECURITY_SETUP.md](SECURITY_SETUP.md).
For the full list of tables created by `synthetic_data.sql` see [app/Fabric/QUICK_REFERENCE.md](../app/Fabric/QUICK_REFERENCE.md).

### JWT secret — automated

The Bicep template auto-generates a strong JWT secret if you leave `jwtSecretKey` blank in `main.bicepparam` (the default). The secret is stored in Key Vault and injected into App Settings as `JWT_SECRET` automatically. **No manual action required.**

To use your own secret instead, set it before deploying:

```bicep
param jwtSecretKey = '<openssl rand -base64 32>'
```

Authentication is enabled by default (`enableAuthentication = true`). To disable it for a development environment:

```bicep
param enableAuthentication = false
```

### Assign Managed Identity for Webapp to Azure OpenAI Resource

```powershell
# Get the App Service principal ID
$principalId = az webapp identity show `
  --name <app-name> `
  --resource-group <resource-group> `
  --query principalId -o tsv

# Get the OpenAI resource ID
$openaiId = az cognitiveservices account show `
  --name <your-openai-resource-name> `
  --resource-group <resource-group> `
  --query id -o tsv

# Assign Cognitive Services OpenAI User role
az role assignment create `
  --assignee $principalId `
  --role "Cognitive Services OpenAI User" `
  --scope $openaiId
```



### Create the first admin user

With authentication on, you need an initial admin account. See [CREATE_ADMIN_USER.md](../CREATE_ADMIN_USER.md) for full options.

In your terminal:

```bash
pip install bcrypt
# Change 'YourPassword123!' to your own password
py -c "import bcrypt; print(bcrypt.hashpw(b'YourPassword123!', bcrypt.gensalt()).decode())"
```

Copy the hash output and paste it in place of `<bcrypt-hash>` in the SQL query below

Quick path via Azure Portal → SQL Database → Query Editor:

```sql
-- Generate the bcrypt hash first (run locally):
-- py -c "import bcrypt; print(bcrypt.hashpw(b'YourPassword123!', bcrypt.gensalt()).decode())"

INSERT INTO dbo.Users (Username, Email, PasswordHash, FirstName, LastName)
VALUES ('admin', 'admin@yourcompany.com', '<bcrypt-hash>', 'Admin', 'User');

-- Assign SuperAdmin role (RoleID = 1)
INSERT INTO dbo.UserRoles (UserID, RoleID)
VALUES (SCOPE_IDENTITY(), 1);
```

> Change the password immediately after first login via Settings → Change Password.

---

## Phase 5 — SQL Access

### Automated — runs on first startup

The application grants its own managed identity database access (`CREATE USER ... FROM EXTERNAL PROVIDER`) on first startup. Watch for this in the startup log:

```
✅ Managed identity user [<app-name>] created and roles granted
```

**No manual action is required for a standard deployment.**

### Fallback (if auto-grant fails)

The auto-grant requires an Azure AD SQL administrator to already be configured on the server — set via `sqlAzureAdAdminLogin` and `sqlAzureAdAdminSid` in `main.bicepparam`. If the startup log shows a database access warning instead, grant access manually:

1. Open **Azure Portal → SQL Database → Query Editor**
2. Authenticate with your Azure AD account
3. Run (replace `<webapp-name>` with the actual App Service name):

```sql
CREATE USER [<webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<webapp-name>];
```

4. Restart: `az webapp restart --name <webapp-name> -g rg-myagents-prod`

### Verify VNet connectivity

If SQL connections fail after granting access, check the private network path:

| Check | Where to look |
|-------|--------------|
| VNet integration active | Portal → App Service → Networking → VNet Integration |
| Private endpoint provisioned | Portal → SQL Server → Private endpoint connections |
| DNS zone linked | Portal → Private DNS zone `privatelink.database.windows.net` → Virtual network links |

All three must be in place for the App Service to reach SQL through the private endpoint.

---

## Phase 6 — Fabric

Microsoft Fabric is optional. The app works fully against Azure SQL alone using the included
synthetic data. Choose the path that fits your needs:

### Option A — No Fabric (quick demo, SQL only)

`app/Fabric/synthetic_data.sql` was already run in Phase 4 — no further action needed.

The AI agents, Analytics dashboard, and Sales dashboard will all query those Gold tables directly against Azure SQL. No environment variable changes are required.

---

### Option B — Full Fabric (mirroring + medallion architecture)

Microsoft Fabric is a SaaS service that cannot be provisioned via Bicep — all setup is done in the Fabric portal.

**Step 1 — Workspace and agents**

1. Navigate to [app.fabric.microsoft.com](https://app.fabric.microsoft.com)
2. Create a **workspace**: Workspaces → + New workspace
3. Get the **workspace ID**: Settings → Properties → Workspace ID
4. Create **agents**: Data Science → + Create Agent (one per required role)
5. Copy each agent ID (`asst_xxx...`)
6. Apply all IDs using the helper script (prompts for anything not passed as a flag):

```powershell
.\scripts\set-agent-ids.ps1 -ResourceGroupName "rg-myagents-prod" `
                             -AppName "<app-name>" `
                             -FabricWorkspaceId "<workspace-GUID>"
```

The script applies all settings and restarts the app.

**Step 2 — Mirror SQL → Fabric and build medallion architecture**

See **[FABRIC_DEPLOYMENT.md](FABRIC_DEPLOYMENT.md)** for the complete guide covering:
- Enabling Change Tracking on Azure SQL
- Creating a Mirrored Database in Fabric (Bronze layer)
- Building Silver and Gold layers using Notebooks
- Scheduling a daily Pipeline
- Connecting the app to the Fabric SQL Analytics Endpoint

---

## Phase 7 — Smoke Tests

```bash
# Run from the repo root
python tests/smoke_test.py \
  --url https://<your-app-name>.azurewebsites.net \
  --skip-auth
```

A healthy run shows all endpoints returning 2xx. Open the browser to confirm the UI loads:

```
https://<your-app-name>.azurewebsites.net
```

---

## Common Commands

| Action | PowerShell / Azure CLI | azd |
|--------|------------------------|-----|
| Full deploy | `.\scripts\deploy.ps1 -ResourceGroupName rg-name` | `azd up` |
| Code only | `.\scripts\deploy.ps1 -ResourceGroupName rg-name -AppName app-name -SkipInfrastructure` | `azd deploy` |
| Tail logs | `az webapp log tail --name app-name -g rg-name` | `azd monitor --logs --follow` |
| View app status | `az webapp show --name app-name -g rg-name` | `azd show` |
| Restart app | `az webapp restart --name app-name -g rg-name` | — |
| Set app setting | `az webapp config appsettings set --name app-name -g rg-name --settings KEY=VALUE` | `azd env set KEY VALUE` then `azd deploy` |
| Delete everything | `az group delete --name rg-name --yes --no-wait` | `azd down` |

---

## Troubleshooting

**App crashes on startup**

```powershell
az webapp log tail --name <app-name> -g rg-name
```

Look for Python tracebacks. Common causes:

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Redeploy — Oryx build may not have run. Confirm `SCM_DO_BUILD_DURING_DEPLOYMENT=true` is in App Settings. |
| `pydantic ValidationError` | A required config field has no env var. Check `AZURE_OPENAI_ENDPOINT` is set. |
| `RuntimeError: Azure OpenAI endpoint is required` | Set `AZURE_OPENAI_ENDPOINT` in App Settings (Phase 3). |
| Container still starting after 5 min | Check `WEBSITES_CONTAINER_START_TIME_LIMIT=1800` is in App Settings. |

**SQL connection fails**

Verify all three network components (VNet integration, private endpoint, DNS zone) as described in Phase 5.

**Azure Policy blocks SQL deployment**

Ensure `enableVnetIntegration = true` in `main.bicepparam` (this is the default). The private endpoint satisfies the `publicNetworkAccess = Disabled` policy requirement. Do not set this to `false` in policy-enforced subscriptions.

**Chat returns 500 errors**

Verify `AZURE_OPENAI_ENDPOINT` is set and the model deployment name (`AZURE_OPENAI_DEPLOYMENT`) matches what's deployed in Azure OpenAI.

**Power BI not loading** _(optional integration)_

Verify the service principal (`powerbiClientId`) has at least Member access to the Power BI workspace, and that "Service principals can use Power BI APIs" is enabled in the Power BI Admin portal → Tenant settings.
