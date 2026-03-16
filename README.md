# Azure Intelligent Agent Starter

Production-ready template for deploying an AI agent application to Azure App Service.

A FastAPI application backed by Azure OpenAI and Azure SQL, with optional Microsoft Fabric and Power BI integration. Deploys with a private network topology (VNet + private endpoint) that satisfies Azure Policy requirements out of the box.

---

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) — `az login`
- [Python 3.11+](https://python.org)
- Azure subscription with Contributor access
- Azure OpenAI resource with GPT-4o deployed _(or set `deployAzureOpenAI = true` to deploy one)_
- Your Azure AD object ID: `az ad signed-in-user show --query id -o tsv`

---

## Quick Deploy

**1. Fill in `bicep/main.bicepparam`**

```bicep
param azureOpenAIEndpoint  = 'https://your-openai.openai.azure.com/'
param azureOpenAIApiKey    = '<your-api-key>'
param sqlAzureAdAdminLogin = 'admin@yourcompany.com'
param sqlAzureAdAdminSid   = '<az ad signed-in-user show --query id -o tsv>'
```

**2. Create resource group and deploy**

```powershell
az group create --name rg-myagents-prod --location eastus2
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod"
```

Or with Azure Developer CLI:

```bash
azd init && azd up
```

**3. Grant SQL access to the app**

Open Azure Portal → SQL Database → Query Editor, then run:

```sql
CREATE USER [<your-webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<your-webapp-name>];
```

**4. Verify**

```bash
python tests/smoke_test.py --url https://<your-webapp-name>.azurewebsites.net --skip-auth
```

For the full step-by-step guide including AI services, authentication, Fabric, and troubleshooting see **[docs/QUICK_START.md](docs/QUICK_START.md)**.

---

## Documentation

| Guide | What it covers |
|-------|----------------|
| [docs/QUICK_START.md](docs/QUICK_START.md) | Full deployment walkthrough — infra → AI services → auth → SQL → Fabric → smoke tests |
| [CONFIGURATION.md](CONFIGURATION.md) | All Bicep parameters and environment variables reference |
| [CREATE_ADMIN_USER.md](CREATE_ADMIN_USER.md) | Create the first admin user after deployment |
| [docs/AZD_DEPLOYMENT_GUIDE.md](docs/AZD_DEPLOYMENT_GUIDE.md) | Azure Developer CLI commands and environment management |
| [docs/AZURE_FOUNDRY_MCP_DEPLOYMENT.md](docs/AZURE_FOUNDRY_MCP_DEPLOYMENT.md) | Alternative: AI Foundry + MCP server architecture |
| [docs/FABRIC_DEPLOYMENT.md](docs/FABRIC_DEPLOYMENT.md) | Optional: Fabric workspace, synthetic data, and Azure Functions |
| [docs/DEMO_QUESTIONS.md](docs/DEMO_QUESTIONS.md) | Sample prompts for demos and testing |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Version history |

---

## Architecture

```
Browser / API clients
        │
        ▼
Azure App Service (Python 3.11, FastAPI + Gunicorn)
        │
        ├── Azure OpenAI (GPT-4o)          ← AI chat and agent orchestration
        ├── Azure SQL Database             ← User data, sessions (private endpoint)
        ├── Application Insights           ← Logs, metrics, distributed tracing
        ├── Azure Key Vault                ← Secrets management
        │
        └── Optional integrations
             ├── Azure AI Foundry          ← Native agent experiences
             ├── Microsoft Fabric          ← Specialist agents and lakehouse data
             └── Power BI Embedded         ← Report embedding
```

Network topology: App Service → VNet integration → private endpoint → SQL (no public internet path to SQL).

---

## Cost Estimate

| Environment | Monthly cost |
|-------------|-------------|
| Development (B2 App Service + Basic SQL) | ~$31 |
| Production (P1v2 App Service + S2 SQL) | ~$410 |

_Excludes Azure OpenAI token costs, Fabric capacity, and Power BI Premium._

---

## Useful Commands

```powershell
# Tail startup logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Restart the app
az webapp restart --name <app-name> --resource-group <rg-name>

# Update a single app setting
az webapp config appsettings set --name <app-name> -g <rg-name> --settings KEY=VALUE

# Redeploy code only (no infra rebuild)
.\scripts\deploy.ps1 -ResourceGroupName <rg-name> -AppName <app-name> -SkipInfrastructure

# Delete everything
az group delete --name <rg-name> --yes --no-wait
```

---

## Support

- Check logs first: `az webapp log tail --name <app-name> -g <rg-name>`
- Detailed troubleshooting: [docs/QUICK_START.md — Troubleshooting](docs/QUICK_START.md#troubleshooting)
- Application Insights: Azure Portal → Application Insights → Failures
