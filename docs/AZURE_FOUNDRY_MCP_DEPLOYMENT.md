# Azure AI Foundry + MCP Server Deployment

> **Alternative architecture.** This deploys the application to **Azure Container Apps** instead of Azure App Service. Use this path if you want native Azure AI Foundry agents with a dedicated MCP (Model Context Protocol) server for centralized function calling. If you just need to connect Foundry agent IDs to an App Service deployment, use the `set-agent-ids.ps1` script from [QUICK_START.md](QUICK_START.md) instead.

---

## Architecture

```
Browser / API clients
        │
        ▼
Azure Container Apps — Main App (FastAPI)
        │
        ├── Azure AI Foundry (agents via AIProjectClient)
        │
        └── MCP Server (Container App, internal only)
             ├── POST /tools/sales/query
             ├── POST /tools/deals/detail
             ├── POST /tools/fabric/query
             └── POST /tools/user/scope
```

**Key files:**

| File | Purpose |
|------|---------|
| `app/app/azure_foundry_agent_manager.py` | Azure AI Foundry agent client |
| `app/mcp_server_app.py` | MCP server — exposes tool endpoints to agents |
| `app/Dockerfile.mcp` | Container image for MCP server |
| `bicep/main-foundry-mcp.bicep` | Infrastructure template (Container Apps) |

---

## Prerequisites

- Azure AI Foundry project with agents created at [ai.azure.com](https://ai.azure.com)
- Existing Azure Container Apps environment and Container Registry
  _(or set `createNewEnvironment = true` in `main-foundry-mcp.bicep` to create new ones — ~$80/month vs ~$30/month reusing existing)_
- `azd` CLI installed

---

## Deploy

**1. Create agents in Azure AI Foundry portal**

Navigate to [ai.azure.com](https://ai.azure.com) → your project → Agents → + New agent. Create one per required role and copy each agent ID (`asst_xxx...`).

**2. Configure the azd environment**

```powershell
azd env new production
azd env set AZURE_LOCATION eastus2
azd env set PROJECT_ENDPOINT            "<your-foundry-endpoint>"
azd env set PROJECT_CONNECTION_STRING   "<your-connection-string>"

# Agent IDs
azd env set FABRIC_ORCHESTRATOR_AGENT_ID    "asst_..."
azd env set FABRIC_SALES_AGENT_ID           "asst_..."
azd env set FABRIC_REALTIME_AGENT_ID        "asst_..."
azd env set FABRIC_ANALYTICS_AGENT_ID       "asst_..."
azd env set FABRIC_FINANCIAL_AGENT_ID       "asst_..."
azd env set FABRIC_SUPPORT_AGENT_ID         "asst_..."
azd env set FABRIC_OPERATIONS_AGENT_ID      "asst_..."
```

**3. Deploy**

```powershell
azd up
```

---

## Configuration reference

All can be set as Azure App Settings or in `.env`:

```env
# Azure AI Foundry
PROJECT_ENDPOINT=https://your-project.services.ai.azure.com/api/projects/your-project
PROJECT_CONNECTION_STRING=<your-connection-string>

# MCP Server (defaults — override only if needed)
ENABLE_MCP=true
MCP_SERVER_HOST=mcp-server
MCP_SERVER_PORT=3000
```

The MCP server defaults (`host=localhost`, `port=3000`, `enable_mcp=true`) work out of the box in the Container Apps environment where the MCP server is registered as an internal service named `mcp-server`.

---

## Verify the deployment

Check the MCP server is responding:

```powershell
# Get the main app URL from the deployment output, then:
curl https://<app-url>/health

# MCP server is internal-only — test via the app's agent call
# or tail Container App logs:
azd logs
azd logs mcp-server
```

---

## Troubleshooting

**MCP server not responding**

```powershell
# Check container is running
az containerapp show -n mcp-server -g <rg-name> --query "properties.runningStatus"

# Tail logs
azd logs mcp-server
```

Common causes: incorrect `MCP_SERVER_HOST` (must match the Container App name), or the MCP container failed to start (check for missing env vars).

**Agents not working**

- Verify agent IDs — copy from AI Foundry portal → Agents → select agent → ID field
- Confirm `PROJECT_CONNECTION_STRING` is set (required for `AIProjectClient` to authenticate)
- Ensure the managed identity has `Azure AI Developer` role on the AI Foundry project

**Container App won't start**

```powershell
az containerapp logs show -n <app-name> -g <rg-name> --follow
```

Check that the Container Registry is accessible and the image was pushed successfully during `azd up`.
