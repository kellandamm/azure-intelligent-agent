# Azure Intelligent Agent Starter

Production-ready template for deploying an AI agent application to Azure App Service.

A FastAPI application backed by Azure SQL and Azure AI services, with optional Microsoft Fabric, Foundry, RTI, Direct Lake, and Purview integration. The base deployment works without Fabric, and the optional add-ons can be enabled later as needed.

---

## Prerequisites

- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) — `az login`
- [Python 3.11+](https://python.org)
- Azure subscription with Contributor access
- Azure AD object ID: `az ad signed-in-user show --query id -o tsv`
- Azure AD UPN: `az ad signed-in-user show --query userPrincipalName -o tsv`
- Azure AI Foundry project or Azure OpenAI deployment, depending on your chosen backend

---

## Quick Deploy

**1. Fill in your deployment parameters**

Update the main Bicep parameter file with the required Azure AD, SQL, and AI settings.

**2. Create the resource group and deploy**

```powershell
az group create --name rg-myagents-prod --location westus3
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod"
```

Or with Azure Developer CLI:

```bash
azd init && azd up
```

**3. Grant SQL access if required**

Open Azure Portal → SQL Database → Query Editor, then run:

```sql
CREATE USER [<your-webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<your-webapp-name>];
```

**4. Verify the deployment**

```bash
python tests/smoke_test.py --url https://<your-webapp-name>.azurewebsites.net --skip-auth
```

For the full step-by-step guide see **[docs/QUICK_START.md](docs/QUICK_START.md)**.

---

## Documentation

| Guide | What it covers |
|-------|----------------|
| [docs/QUICK_START.md](docs/QUICK_START.md) | Full deployment walkthrough from parameters to validation |
| [docs/FABRIC_DEPLOYMENT.md](docs/FABRIC_DEPLOYMENT.md) | Optional Fabric setup: mirroring, Silver/Gold notebooks, Direct Lake guidance |
| [docs/FABRIC_RTI_OPTIONAL_DEPLOYMENT.md](docs/FABRIC_RTI_OPTIONAL_DEPLOYMENT.md) | Optional Fabric RTI setup |
| [docs/FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md](docs/FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md) | Optional Fabric Data Agent + Foundry setup |
| [docs/PURVIEW_OPTIONAL_DEPLOYMENT.md](docs/PURVIEW_OPTIONAL_DEPLOYMENT.md) | Optional Purview governance setup |
| [CONFIGURATION.md](CONFIGURATION.md) | Bicep parameters and environment variables |
| [CREATE_ADMIN_USER.md](CREATE_ADMIN_USER.md) | Create the first admin user |

---

## Architecture

```
Browser / API clients
        │
        ▼
Azure App Service (FastAPI)
        │
        ├── Azure SQL Database
        ├── Azure AI Foundry or Azure OpenAI
        ├── Application Insights
        ├── Key Vault
        │
        └── Optional integrations
             ├── Microsoft Fabric
             ├── Fabric Real-Time Intelligence
             ├── Fabric Data Agent
             └── Microsoft Purview
```

The base application runs against Azure SQL. Fabric and the other integrations are optional add-ons.
