# Azure AI Foundry Agents — Deployment Guide

This guide explains how to create agents in the **Azure AI Foundry portal** and activate the
Foundry backend in the App Service. By default the app uses a local code-based agent loop.
Setting `USE_FOUNDRY_AGENTS=true` switches all chat traffic to your Foundry-hosted agents.

---

## How the two backends compare

| | Code-based (default) | Azure AI Foundry |
|---|---|---|
| System prompts | Defined in `agent_framework_manager.py` | Defined per agent in the Foundry portal |
| Thread state | In-memory (lost on restart) | Server-side (persists across restarts) |
| Tool routing | Local Python functions in `agent_tools.py` | Tool calls managed by Foundry |
| Requires Foundry project | No | Yes |
| Feature flag | `USE_FOUNDRY_AGENTS=false` (default) | `USE_FOUNDRY_AGENTS=true` |

The `/api/chat` endpoint, authentication, RLS, and the entire UI are **identical on both paths**.

---

## Prerequisites

- App Service deployment complete (see [QUICK_START.md](QUICK_START.md))
- Azure subscription with an **Azure AI Foundry** resource
- Your App Service managed identity has the **Azure AI Developer** role on the Foundry project

---

## Step 1 — Create an Azure AI Foundry project

1. Open [https://ai.azure.com](https://ai.azure.com) and sign in
2. Select **+ Create project** if you do not already have one
3. Choose an existing **AI Hub** or create a new one, then name your project
4. Once the project is created, navigate to **Project settings** (gear icon, bottom-left)
5. Copy the **Endpoint** — it looks like:
   ```
   https://<resource-name>.services.ai.azure.com/api/projects/<project-name>
   ```
   This is your `PROJECT_ENDPOINT`.

---

## Step 2 — Create the agents

In your Foundry project, go to **Agents** (left sidebar) → **+ New agent**.

Create one agent for each role in the table below. For each agent:
- Set the **Name** as shown
- Paste the **Instructions** (system prompt) for that role
- Choose your **Model** deployment (e.g. `gpt-4o`)
- Save the agent, then copy its **Agent ID** (format: `asst_...`)

| # | Agent name | Role key in config | Role description |
|---|---|---|---|
| 1 | `RetailAssistantOrchestrator` | orchestrator | Routes questions to the correct specialist |
| 2 | `SalesAssistant` | sales | Revenue, top products, and sales trends |
| 3 | `OperationsAssistant` | operations | Real-time metrics and system health |
| 4 | `AnalyticsAssistant` | analytics | KPI analysis and business intelligence |
| 5 | `FinancialAdvisor` | financial | ROI, forecasting, and profitability |
| 6 | `CustomerSupportAssistant` | support | Customer support and troubleshooting |
| 7 | `OperationsCoordinator` | coordinator | Logistics, supply chain, and coordination |
| 8 | `CustomerSuccessAgent` | customer\_success | Retention, satisfaction, and growth |
| 9 | `OperationsExcellenceAgent` | operations\_excellence | Process efficiency and optimisation |

### Suggested system prompts

Below are starting points. Customise them to match your business scenario.

**RetailAssistantOrchestrator**
```
You are a retail business orchestrator. Your job is to understand the user's question and
route it to the correct specialist. You have access to specialists for: sales data, operations
metrics, analytics, financial planning, customer support, logistics, customer success, and
operations excellence. Respond concisely and delegate complex questions to the right expert.
```

**SalesAssistant**
```
You are a sales intelligence specialist for a retail business. You answer questions about
revenue, top-performing products, sales trends, regional performance, and customer purchasing
behaviour. Provide data-driven insights and actionable recommendations. Be concise and precise.
```

**OperationsAssistant**
```
You are an operations monitoring specialist. You answer questions about real-time system
health, uptime, order processing status, fulfilment rates, and operational KPIs.
Highlight anomalies and surface actionable findings.
```

**AnalyticsAssistant**
```
You are a business intelligence analyst. You answer questions about customer demographics,
cohort analysis, conversion funnels, seasonal patterns, and performance benchmarking.
Provide clear, data-backed conclusions.
```

**FinancialAdvisor**
```
You are a financial planning specialist. You answer questions about ROI calculations, revenue
forecasting, margin analysis, cost optimisation, and profitability. Apply sound financial
reasoning and present findings clearly.
```

**CustomerSupportAssistant**
```
You are a customer support specialist. You help customers with product questions, order
issues, returns, and general troubleshooting. Be empathetic, concise, and solution-focused.
Escalate complex cases when appropriate.
```

**OperationsCoordinator**
```
You are a logistics and supply chain coordinator. You answer questions about inventory levels,
supplier lead times, shipping status, and supply chain optimisation. Identify bottlenecks and
recommend practical solutions.
```

**CustomerSuccessAgent**
```
You are a customer success specialist. You analyse customer satisfaction data, churn signals,
retention strategies, and growth opportunities. Provide proactive recommendations to improve
customer lifetime value and loyalty.
```

**OperationsExcellenceAgent**
```
You are an operations excellence specialist. You identify inefficiencies, analyse process
metrics, and recommend improvements. Apply continuous-improvement frameworks (Lean, Six Sigma)
where relevant and quantify the expected impact of changes.
```

---

## Step 3 — Apply IDs and activate the Foundry backend

Run the helper script — it prompts for each ID, stores them as App Settings, and sets
`USE_FOUNDRY_AGENTS=true` automatically:

```powershell
.\scripts\set-agent-ids.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -AppName "<app-name>" `
    -ProjectEndpoint "https://<resource>.services.ai.azure.com/api/projects/<project>" `
    -OrchestratorAgentId "asst_..." `
    -SalesAgentId "asst_..." `
    -RealtimeAgentId "asst_..." `
    -AnalyticsAgentId "asst_..." `
    -FinancialAgentId "asst_..." `
    -SupportAgentId "asst_..." `
    -OperationsCoordinatorAgentId "asst_..." `
    -CustomerSuccessAgentId "asst_..." `
    -OperationsExcellenceAgentId "asst_..."
```

Run it without parameters to be prompted interactively for each value.

To enable published Agent Applications (Responses protocol) during apply, use:

```powershell
.\scripts\get-agent-ids.ps1 `
  -ProjectEndpoint "https://<resource>.services.ai.azure.com/api/projects/<project>" `
  -ResourceGroupName "rg-myagents-prod" `
  -AppName "<app-name>" `
  -Apply `
  -EnablePublishedMode
```

### What gets written to App Settings

| App Setting | Description |
|---|---|
| `PROJECT_ENDPOINT` | Foundry project endpoint URL |
| `ORCHESTRATOR_AGENT_ID` | Orchestrator agent ID |
| `SALES_AGENT_ID` | Sales agent ID |
| `REALTIME_AGENT_ID` | Operations / real-time agent ID |
| `ANALYTICS_AGENT_ID` | Analytics agent ID |
| `FINANCIAL_AGENT_ID` | Financial agent ID |
| `SUPPORT_AGENT_ID` | Customer support agent ID |
| `OPERATIONS_AGENT_ID` | Operations coordinator agent ID |
| `CUSTOMER_SUCCESS_AGENT_ID` | Customer success agent ID |
| `OPERATIONS_EXCELLENCE_AGENT_ID` | Operations excellence agent ID |
| `ORCHESTRATOR_AGENT_APP_NAME` | Orchestrator published application name |
| `SALES_AGENT_APP_NAME` | Sales published application name |
| `REALTIME_AGENT_APP_NAME` | Operations / real-time published application name |
| `ANALYTICS_AGENT_APP_NAME` | Analytics published application name |
| `FINANCIAL_AGENT_APP_NAME` | Financial published application name |
| `SUPPORT_AGENT_APP_NAME` | Customer support published application name |
| `OPERATIONS_AGENT_APP_NAME` | Operations coordinator published application name |
| `CUSTOMER_SUCCESS_AGENT_APP_NAME` | Customer success published application name |
| `OPERATIONS_EXCELLENCE_AGENT_APP_NAME` | Operations excellence published application name |
| `USE_FOUNDRY_AGENTS` | `true` — activates the Foundry backend |
| `USE_PUBLISHED_AGENT_APPLICATIONS` | `true` when `-EnablePublishedMode` is used; otherwise unchanged |

---

## Step 4 — Grant the managed identity access

The App Service managed identity must be able to call the Foundry project APIs.

In the Azure portal → your **AI Hub resource** → **Access control (IAM)** → **+ Add role assignment**:
- Role: **Azure AI Developer**
- Assign access to: **Managed Identity**
- Select the App Service's system-assigned managed identity

---

## Step 5 — Verify

Check the App Service startup log:

```powershell
az webapp log tail --name <app-name> --resource-group rg-myagents-prod
```

Look for:
```
🤖 Agent backend: Azure AI Foundry
```

Test a chat request:

```bash
curl -X POST https://<app-url>/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me total revenue", "agent_type": "orchestrator"}'
```

---

## Rollback

Switch back to the code-based backend instantly — no data loss, no code change:

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
| `ValueError: PROJECT_ENDPOINT is required` | `PROJECT_ENDPOINT` is missing or blank in App Settings. |
| `USE_FOUNDRY_AGENTS=true but ... failed to initialise` | Check `PROJECT_ENDPOINT` is the full URL from Foundry project settings. |
| 401 / authentication error from Foundry | The managed identity is missing **Azure AI Developer** role on the AI Hub. |
| Agent returns empty response | Verify the agent ID in App Settings matches the `asst_...` ID shown in the Foundry portal. |
| App crashes on startup | Run `az webapp log tail`. If `AzureAIFoundryAgentManager unavailable` appears, fall back to `USE_FOUNDRY_AGENTS=false` and fix the reported error. |
| Threads don't persist after restart (code-based path) | Expected — code-based backend stores threads in memory only. Use the Foundry backend for persistent threads. |

---

## Key files

| File | Purpose |
|---|---|
| `app/app/azure_foundry_agent_manager.py` | Foundry agent client (`AzureAIFoundryAgentManager`) |
| `app/app/config.py` | Agent ID settings fields |
| `app/main.py` | Conditional backend import at startup |
| `scripts/set-agent-ids.ps1` | Helper script to push agent IDs to App Settings |
| `.env.example` | Local development template with all env var names |
