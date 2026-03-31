# Deployment Guide

Deploy the Azure Intelligent Agent from zero to running in approximately 20 minutes.

---

## Prerequisites

Have these ready before starting:

- [ ] **Azure CLI** installed and logged in (`az login`)
- [ ] **PowerShell 7.0+** installed (`pwsh` command available)
- [ ] **Azure subscription** with Contributor access to a resource group
- [ ] **Microsoft AI Foundry** project with agents deployed
  - Navigate to [https://ai.azure.com](https://ai.azure.com) and create a project
  - Deploy a GPT-4.1 or GPT-5.2 model in your Foundry project
  - Note: Azure OpenAI endpoint and API key will be retrieved from Foundry project settings
- [ ] Your **Azure AD UPN**: `az ad signed-in-user show --query userPrincipalName -o tsv`
- [ ] Your **Azure AD object ID**: `az ad signed-in-user show --query id -o tsv`

---

## Phase 1 — Configure Parameters (5 min)

Open `bicep/main.bicepparam` and fill in your values. Most fields are optional — start with the required ones.

### Required fields

```bicep
using './main.bicep'

// Microsoft AI Foundry Project — Required for default agent backend
// Find in Azure AI Foundry portal → Project → Settings → Endpoint
param projectEndpoint = 'https://<your-resource>.services.ai.azure.com/api/projects/<your-project>'

// Model deployment name in your Foundry project
param modelDeploymentName = 'gpt-5.2'  // or 'gpt-5.2'

// SQL Azure AD admin — cannot be blank (Azure Policy enforces this)
param sqlAzureAdAdminLogin = 'admin@yourcompany.com'   // az ad signed-in-user show --query userPrincipalName -o tsv
param sqlAzureAdAdminSid   = '<your-object-id>'        // az ad signed-in-user show --query id -o tsv
```

### Optional: Deploy Azure OpenAI (not recommended)

If you want to deploy a separate Azure OpenAI resource instead of using Foundry's built-in models:

```bicep
param deployAzureOpenAI        = true
param azureOpenAIModelName     = 'gpt-5.2'
param azureOpenAIModelVersion  = '2024-11-20'
param azureOpenAIModelCapacity = 10   // tokens per minute (thousands)
```

> ⚠️ **Recommended**: Use Microsoft AI Foundry models directly. Only deploy Azure OpenAI if you have specific requirements for a separate endpoint.

### Optional integrations

Fill these in now if you have additional services, or return to add them later:

```bicep
// Microsoft Fabric (optional - for advanced analytics)
param fabricWorkspaceId = '<workspace-GUID>'

// Power BI embedding (optional)
param powerbiWorkspaceId    = '<GUID>'
param powerbiReportId       = '<GUID>'
param powerbiClientId       = '<GUID>'
param powerbiTenantId       = '<GUID>'
param powerbiClientSecret   = '<secret>'
```

---

## Phase 2 — Deploy Infrastructure (8–15 min)

Choose **one** method:

### Option A: PowerShell (recommended)

```powershell
# Create resource group
az group create --name rg-myagents-prod --location westus2

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
azd env set AZURE_LOCATION westus2
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

## Phase 3 — Configure Microsoft AI Foundry Agents

This application uses **Microsoft AI Foundry native agents** by default for enterprise-grade AI capabilities with built-in governance, monitoring, and deployment workflows.

### Verify Foundry Configuration

The deployment automatically configures your app to use Microsoft AI Foundry. Verify the settings:

```powershell
az webapp config appsettings list \
  --name <app-name> --resource-group rg-myagents-prod \
  --query "[?name=='PROJECT_ENDPOINT'].value" -o tsv
```

You should see your Foundry project endpoint. If not set, add it:

```powershell
az webapp config appsettings set \
  --name <app-name> --resource-group rg-myagents-prod \
  --settings PROJECT_ENDPOINT="https://<your-resource>.services.ai.azure.com/api/projects/<your-project>"
```

#### Create Agents in Microsoft AI Foundry

**Step 1: Access Microsoft AI Foundry Portal**

1. Navigate to [https://ai.azure.com](https://ai.azure.com)
2. Sign in with your Azure account
3. Select your AI Foundry project (or create one if needed)
4. Click **"Agents"** in the left navigation menu

**Step 2: Create All 9 Required Agents**

Click **"+ New agent"** and create each agent below **using the exact names** (case-sensitive). For each agent:
- **Model**: Select `gpt-4.1` or `gpt-5-mini` (or `gpt-5.2` if available)
- **Instructions**: Copy the system prompt provided below
- Click **"Save"** after entering the instructions

---

**Agent 1: RetailAssistantOrchestrator**

```
You are a retail business orchestrator. Your job is to understand the user's question and
route it to the correct specialist. You have access to specialists for: sales data, operations
metrics, analytics, financial planning, customer support, logistics, customer success, and
operations excellence. Respond concisely and delegate complex questions to the right expert.
```

---

**Agent 2: SalesAssistant**

```
You are a sales specialist. You provide deep insights into sales data, revenue trends,
product performance, and customer purchasing patterns. Use data to answer questions about
sales metrics, top products, regional performance, and growth opportunities. Be specific
and quantitative when presenting findings.
```

---

**Agent 3: OperationsAssistant**

```
You are a real-time operations specialist. You monitor operational KPIs, track inventory
levels, analyze supply chain metrics, and provide alerts on operational issues. Focus on
current state and immediate issues requiring attention.
```

---

**Agent 4: AnalyticsAssistant**

```
You are a business intelligence analyst. You perform advanced analytics, identify trends,
create forecasts, and provide data-driven recommendations. Use statistical analysis and
visualization suggestions to help users understand complex business patterns.
```

---

**Agent 5: FinancialAdvisor**

```
You are a financial analyst specializing in retail business finance. You analyze profitability,
ROI, cost structures, pricing strategies, and financial forecasts. Provide actionable financial
insights and recommendations backed by data.
```

---

**Agent 6: CustomerSupportAssistant**

```
You are a customer support specialist. You analyze customer inquiries, complaints, satisfaction
scores, and support ticket trends. Provide insights on common issues, resolution times, and
recommendations for improving customer experience.
```

---

**Agent 7: OperationsCoordinator**

```
You are an operations coordinator focused on logistics, fulfillment, and supply chain efficiency.
You analyze delivery performance, warehouse operations, vendor relationships, and identify
bottlenecks in the operational flow.
```

---

**Agent 8: CustomerSuccessAgent**

```
You are a customer success specialist. You analyse customer satisfaction data, churn signals,
retention strategies, and growth opportunities. Provide proactive recommendations to improve
customer lifetime value and loyalty.
```

---

**Agent 9: OperationsExcellenceAgent**

```
You are an operations excellence specialist. You identify inefficiencies, analyse process
metrics, and recommend improvements. Apply continuous-improvement frameworks (Lean, Six Sigma)
where relevant and quantify the expected impact of changes.
```

---

**Step 3: Retrieve Agent IDs and Configure App**

After creating all 9 agents, run this script to automatically retrieve their IDs and configure your App Service:

```powershell
.\scripts\get-agent-ids.ps1 `
  -ProjectEndpoint "https://<your-resource>.services.ai.azure.com/api/projects/<your-project>" `
  -ResourceGroupName "rg-myagents-prod" `
  -AppName "<app-name>" `
  -Apply
```

**What this script does:**
- ✅ Retrieves all 9 agent IDs by name from Microsoft AI Foundry
- ✅ Maps them to the correct environment variables
- ✅ Configures App Service settings with all agent IDs
- ✅ Sets `USE_FOUNDRY_AGENTS=true`
- ✅ Restarts the app

**To find your PROJECT_ENDPOINT:**
1. In AI Foundry portal, navigate to your project
2. Click **"Settings"** in the left menu
3. Copy the **"Project endpoint"** URL
4. Format: `https://<resource>.services.ai.azure.com/api/projects/<project-name>`

> ⚠️ **Important**: Agent names must match **exactly** (case-sensitive) for the script to find them. If the script cannot find an agent, double-check the spelling and capitalization in the portal.

**Troubleshooting**
- If script reports "Not found" for agents, verify you created them with the exact names listed above
- If authentication fails, ensure you're logged in: `az login`
- If you get 404 errors, confirm your PROJECT_ENDPOINT is correct by copying it from Settings in the portal

---

#### Verify Active Backend

Check the startup log to confirm which backend is active:

```bash
az webapp log tail --name <app-name> --resource-group rg-myagents-prod
```

Look for:
```
🤖 Agent backend: Azure AI Foundry        ← Foundry agents active (default)
```

#### Optional: Switch to Code-Based Backend

To use the built-in code-based agent backend instead of Foundry (not recommended):

```powershell
az webapp config appsettings set `
  --name <app-name> --resource-group rg-myagents-prod `
  --settings USE_FOUNDRY_AGENTS=false
az webapp restart --name <app-name> --resource-group rg-myagents-prod
```

> **Note:** The app seamlessly switches between backends without data loss. All chat endpoints, auth logic, and UI remain identical.

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
