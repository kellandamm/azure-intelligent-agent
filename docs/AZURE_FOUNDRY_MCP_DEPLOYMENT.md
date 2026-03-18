# Azure AI Foundry Agents — App Service Deployment Guide

Explains how to activate the Azure AI Foundry agent backend on the standard **App Service** deployment.
By default the app uses a code-based agent loop (`AgentFrameworkManager`). Setting `USE_FOUNDRY_AGENTS=true` switches all chat traffic to pre-created Foundry agents without any code change.

---

## How the two backends compare

| | Code-based (default) | Azure AI Foundry |
|---|---|---|
| System prompts | Defined in `agent_framework_manager.py` | Defined in AI Foundry portal per agent |
| Thread state | In-memory (lost on restart) | Server-side (persists across restarts) |
| Tool routing | Local Python functions in `agent_tools.py` | Foundry tool calls or MCP server |
| Requires Foundry project | No | Yes |
| Feature flag | `USE_FOUNDRY_AGENTS=false` (default) | `USE_FOUNDRY_AGENTS=true` |

The `/api/chat` endpoint, authentication, RLS, and the entire UI are **identical on both paths**.

---

## Prerequisites

- App Service deployment complete (see [QUICK_START.md](QUICK_START.md))
- Azure AI Foundry project created ([ai.azure.com](https://ai.azure.com))
- Your managed identity (or service principal) has the **Azure AI Developer** role on the Foundry project

---

## Step 1 — Create agents in the AI Foundry portal

1. Open [https://ai.azure.com](https://ai.azure.com) and select your project
2. Go to **Agents** → **+ New agent** and create one agent for each role:

| Agent name (suggested) | Role |
|---|---|
| `RetailAssistantOrchestrator` | Orchestrator — routes to specialists |
| `SalesAssistant` | Revenue, top products, sales trends |
| `OperationsAssistant` | Real-time metrics, system health |
| `AnalyticsAssistant` | KPI analysis, business intelligence |
| `FinancialAdvisor` | ROI, forecasting, profitability |
| `CustomerSupportAssistant` | Support and troubleshooting |
| `CustomerSuccessAgent` | Retention, satisfaction, growth |
| `OperationsExcellenceAgent` | Process efficiency and optimisation |

3. For each agent, configure the system prompt in the **Instructions** field (see the role descriptions above)
4. Copy each agent's **ID** (format: `asst_xxx...`)
5. Copy the **Project connection string** from **Project** → **Settings** → **Connection string**

---

## Step 2 — Apply IDs and activate the Foundry backend

Run the helper script — it prompts for all IDs, stores them as App Settings, and sets `USE_FOUNDRY_AGENTS=true` automatically:

```powershell
.\scripts\set-agent-ids.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -AppName "<app-name>" `
    -ProjectConnectionString "<connection-string>" `
    -OrchestratorAgentId "asst_..." `
    -SalesAgentId "asst_..." `
    -RealtimeAgentId "asst_..." `
    -AnalyticsAgentId "asst_..." `
    -FinancialAgentId "asst_..." `
    -SupportAgentId "asst_..." `
    -CustomerSuccessAgentId "asst_..." `
    -OperationsExcellenceAgentId "asst_..."
```

The script applies all settings and restarts the app automatically. Run it interactively (omit the flags) to be prompted for each value.

### What gets set in App Settings

| Setting | Value |
|---|---|
| `PROJECT_CONNECTION_STRING` | Foundry project connection string |
| `PROJECT_ENDPOINT` | Foundry project endpoint (alternative to connection string) |
| `FABRIC_ORCHESTRATOR_AGENT_ID` | Orchestrator `asst_xxx` ID |
| `FABRIC_SALES_AGENT_ID` | Sales agent ID |
| `FABRIC_REALTIME_AGENT_ID` | Operations / real-time agent ID |
| `FABRIC_ANALYTICS_AGENT_ID` | Analytics agent ID |
| `FABRIC_FINANCIAL_AGENT_ID` | Financial agent ID |
| `FABRIC_SUPPORT_AGENT_ID` | Support agent ID |
| `FABRIC_CUSTOMER_SUCCESS_AGENT_ID` | Customer success agent ID |
| `FABRIC_OPERATIONS_EXCELLENCE_AGENT_ID` | Operations excellence agent ID |
| `USE_FOUNDRY_AGENTS` | `true` — activates the Foundry backend |

---

## Step 3 — Grant the managed identity access

The App Service managed identity must be able to call the Foundry project APIs.

In the Foundry workspace → **Access control (IAM)** → **+ Add role assignment**:
- Role: **Azure AI Developer**
- Assign access to: **Managed Identity**
- Select the App Service's managed identity

---

## Step 4 — Verify

Check the App Service startup log:

```powershell
az webapp log tail --name <app-name> --resource-group rg-myagents-prod
```

Look for:
```
🤖 Agent backend: Azure AI Foundry
```

Make a chat request from the UI or via API:

```bash
curl -X POST https://<app-url>/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me total revenue", "agent_type": "orchestrator"}'
```

If the response is returned successfully, the Foundry backend is active.

---

## Rollback

Revert to the code-based backend instantly — no data loss, no code change:

```powershell
az webapp config appsettings set `
  --name <app-name> --resource-group rg-myagents-prod `
  --settings USE_FOUNDRY_AGENTS=false
az webapp restart --name <app-name> --resource-group rg-myagents-prod
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `RuntimeError: USE_FOUNDRY_AGENTS=true but ... failed to initialise` | `PROJECT_CONNECTION_STRING` or `PROJECT_ENDPOINT` is missing or malformed. Verify in App Settings. |
| `Login failed` / 401 from Foundry | The managed identity is missing the **Azure AI Developer** role on the Foundry project. |
| Agent returns empty response | Check the agent ID in App Settings matches the `asst_xxx` ID shown in the Foundry portal. |
| App crashes on startup | Check `az webapp log tail`. If `AzureAIFoundryAgentManager unavailable` appears, fall back to `USE_FOUNDRY_AGENTS=false` and investigate the error. |
| Threads don't persist after restart (code-based path) | Expected — the code-based backend stores threads in memory. Use the Foundry backend for persistent thread state. |

---

## Key files

| File | Purpose |
|---|---|
| `app/app/azure_foundry_agent_manager.py` | Foundry agent client (`AzureAIFoundryAgentManager`) |
| `app/app/config.py` | `use_foundry_agents` feature flag field |
| `app/main.py` | Conditional backend import at startup |
| `app/mcp_server_app.py` | MCP server — exposes tool endpoints |
| `scripts/set-agent-ids.ps1` | Helper to apply agent IDs + activate Foundry |

---

## Container Apps alternative

If you need the MCP server running as a separate container alongside the main app (for advanced scenarios), a Container Apps deployment template exists. This is a non-standard path — most deployments use App Service. See the `bicep/` directory for infrastructure templates if you need this path.
