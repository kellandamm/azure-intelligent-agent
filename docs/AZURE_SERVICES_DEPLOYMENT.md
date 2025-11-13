# Azure Services Deployment Guide

This guide explains how to deploy or configure the Azure services required by the Agent Framework application.

## 📋 Service Deployment Matrix

| Service | Can Deploy with Bicep? | Status | Notes |
|---------|----------------------|--------|-------|
| **Azure OpenAI** | ✅ Yes | Supported | Deploy with GPT-4 model |
| **Azure AI Foundry** | ⚠️ Partial | Preview | Hub/Project only, agents manual |
| **Microsoft Fabric** | ❌ No | Manual Only | SaaS service, portal configuration |
| **Power BI** | ❌ No | Manual Only | SaaS service, portal configuration |
| **Azure SQL Database** | ✅ Yes | Supported | Included in main template |
| **App Service** | ✅ Yes | Supported | Included in main template |
| **Key Vault** | ✅ Yes | Optional | Included in main template |

---

## 🤖 Azure OpenAI Deployment

### Overview

Azure OpenAI can be fully deployed via Bicep, including the account and model deployments.

### Deployment Options

#### Option A: Use Existing Azure OpenAI (Recommended for Production)

**When to use**:
- You already have Azure OpenAI in another subscription/resource group
- You want to share OpenAI across multiple applications
- You have existing quota allocations

**Steps**:
1. Get your endpoint and API key:
   ```bash
   # Azure Portal → Azure OpenAI → Keys and Endpoint
   Endpoint: https://<your-resource>.openai.azure.com/
   API Key: <copy from Keys section>
   Deployment Name: <your-model-deployment-name>
   ```

2. Configure parameters:
   ```bicep
   // In main.parameters.bicepparam
   param deployAzureOpenAI = false
   param azureOpenAIEndpoint = 'https://your-openai.openai.azure.com/'
   param azureOpenAIApiKey = '<your-api-key>'
   param azureOpenAIDeployment = 'gpt-4o'
   param azureOpenAIApiVersion = '2024-08-01-preview'
   ```

#### Option B: Deploy New Azure OpenAI (Development/Testing)

**When to use**:
- You're creating a new environment from scratch
- You want isolated OpenAI resources per environment
- You're doing development/testing

**Steps**:
1. Configure parameters:
   ```bicep
   // In main.parameters.bicepparam
   param deployAzureOpenAI = true
   param azureOpenAIModelName = 'gpt-4o'
   param azureOpenAIModelVersion = '2024-11-20'
   param azureOpenAIModelCapacity = 10  // Tokens per minute (thousands)
   param azureOpenAIDeployment = 'gpt-4o'  // Optional, defaults to model name
   param azureOpenAISku = 'S0'  // Standard SKU
   ```

2. Deploy:
   ```powershell
   # PowerShell
   cd scripts
   ./deploy.ps1 -ResourceGroupName "rg-agents-dev" -Location "eastus2"
   ```

   The template will:
   - ✅ Create Azure OpenAI account (type: `AIServices`)
   - ✅ Deploy GPT-4o model with specified capacity
   - ✅ Generate and output endpoint URL
   - ✅ Store API key in Key Vault (if enabled)
   - ✅ Configure app settings automatically

3. Outputs:
   ```bash
   # After deployment, you'll receive:
   azureOpenAIEndpoint: "https://myagents-openai-prod.openai.azure.com/"
   azureOpenAIDeployment: "gpt-4o"
   # API key stored in Key Vault: "azureOpenAIApiKey"
   ```

### Supported Models

The template uses Azure Verified Modules patterns and supports:

| Model | Version | Format | Typical Capacity |
|-------|---------|--------|------------------|
| `gpt-4o` | 2024-11-20 | OpenAI | 10-100 TPM |
| `gpt-4o-mini` | 2024-07-18 | OpenAI | 10-100 TPM |
| `gpt-4` | 0613 | OpenAI | 10-50 TPM |
| `gpt-35-turbo` | 0613 | OpenAI | 10-240 TPM |

**Note**: Model availability varies by region. Use [Azure OpenAI Model Availability](https://learn.microsoft.com/azure/ai-services/openai/concepts/models) to check.

### Cost Estimation

**Model Pricing** (pay-as-you-go):
- GPT-4o: ~$0.03/1K prompt tokens, ~$0.06/1K completion tokens
- GPT-4o-mini: ~$0.15/1M prompt tokens, ~$0.60/1M completion tokens
- GPT-4: ~$0.03/1K prompt tokens, ~$0.06/1K completion tokens

**Capacity Pricing** (optional provisioned throughput):
- Not included by default (uses serverless API)
- Provisioned capacity: ~$1000-3000/month for 100K TPM

**Example Monthly Cost** (serverless):
- 1M tokens/day average: ~$30-90/month
- 10M tokens/day average: ~$300-900/month

---

## 🧠 Azure AI Foundry Deployment

### Overview

Azure AI Foundry (formerly Azure AI Studio) can be partially deployed via Bicep. The hub and project resources can be created, but agents must be configured manually.

### What Can Be Automated

✅ **Hub Resource**: `Microsoft.CognitiveServices/accounts` (kind: `AIServices`)
✅ **Project Resource**: `Microsoft.CognitiveServices/accounts/projects`
✅ **Connections**: Link to Azure OpenAI and other services
✅ **RBAC Assignments**: Grant access to managed identities

### What Requires Manual Setup

❌ **Agents**: Must be created in AI Foundry portal
❌ **Agent IDs**: Generated after agent creation (format: `asst_xxx...`)
❌ **Agent Configuration**: Skills, instructions, tools
❌ **Agent Testing**: Validation and refinement

### Deployment Approach

#### Option A: Use Existing AI Foundry Project (Recommended)

**When to use**:
- You have an existing AI Foundry project with agents
- You want to reuse agent configurations
- You're deploying to multiple environments with same agents

**Steps**:
1. Get AI Foundry project details:
   ```bash
   # AI Foundry Portal → Your Project → Settings
   Project Endpoint: https://<project>.<region>.api.azureml.ms/agents/v1.0/...
   Connection Name: aoai-connection  # Usually this
   ```

2. Get agent IDs:
   ```bash
   # AI Foundry Portal → Data Science → Agents
   # Copy ID for each agent (format: asst_xxx...)
   ```

3. Configure parameters:
   ```bicep
   // In main.parameters.bicepparam
   param deployAIFoundry = false
   param projectEndpoint = 'https://myproject.eastus.api.azureml.ms/agents/v1.0/...'
   param connectionName = 'aoai-connection'
   param fabricOrchestratorAgentId = 'asst_YXmaCOM5JdgKQLhte0Xs2Yib'
   param fabricDocumentAgentId = 'asst_CqY1VZC9w5dxlBGYjAUyqjv2'
   // ... other agent IDs
   ```

#### Option B: Deploy New AI Foundry Project (Preview)

⚠️ **Preview Feature**: Azure AI Foundry Bicep deployment is in preview. Some features may require manual configuration.

**When to use**:
- You're creating a brand new environment
- You want infrastructure-as-code for the entire stack
- You're comfortable with preview features

**Steps**:

1. Create AI Foundry deployment module:
   ```bash
   # This module is not included by default
   # Use the Azure AI Foundry quickstart template:
   git clone https://github.com/Azure-AI-Foundry/foundry-samples
   cd foundry-samples/samples/microsoft/infrastructure-setup/00-basic
   ```

2. Or use our optional module (if created):
   ```bicep
   // In main.parameters.bicepparam
   param deployAIFoundry = true
   param aiFoundryHubName = 'myagents-ai-hub'
   param aiFoundryProjectName = 'myagents-ai-project'
   param aiFoundryLocation = 'eastus2'
   ```

3. Deploy:
   ```powershell
   # PowerShell
   cd scripts
   ./deploy.ps1 -ResourceGroupName "rg-agents-dev" -Location "eastus2"
   ```

4. **Manual Post-Deployment** (Required):
   
   a. Open [AI Foundry Portal](https://ai.azure.com)
   
   b. Navigate to your project
   
   c. Create agents:
      - Go to **Data Science** → **Agents**
      - Click **+ New Agent**
      - Configure each agent (orchestrator, document, powerbi, chart, sales, realtime)
      - Save and note the agent ID (format: `asst_xxx...`)
   
   d. Update parameters file:
      ```bicep
      // Update main.parameters.bicepparam with generated agent IDs
      param fabricOrchestratorAgentId = 'asst_<YOUR_ID_HERE>'
      param fabricDocumentAgentId = 'asst_<YOUR_ID_HERE>'
      param fabricPowerBIAgentId = 'asst_<YOUR_ID_HERE>'
      param fabricChartAgentId = 'asst_<YOUR_ID_HERE>'
      param fabricSalesAgentId = 'asst_<YOUR_ID_HERE>'
      param fabricRealtimeAgentId = 'asst_<YOUR_ID_HERE>'
      ```
   
   e. Re-deploy to update app settings:
      ```powershell
      ./deploy.ps1 -ResourceGroupName "rg-agents-dev" -SkipInfrastructure
      ```

### AI Foundry Hub vs Project

**Hub**:
- Central resource for managing AI assets
- Contains connections to Azure services
- Provides shared compute and security settings
- Can have multiple projects

**Project**:
- Workspace for building AI applications
- Contains agents, deployments, and experiments
- Inherits settings from hub
- Isolated from other projects

### Example Bicep Template (Reference)

```bicep
// This is a reference example, not included in main template

// Hub
resource aiFoundryHub 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: 'myai-hub'
  location: 'eastus2'
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: 'myai-hub-subdomain'
    publicNetworkAccess: 'Enabled'
  }
}

// Project
resource aiFoundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: aiFoundryHub
  name: 'myai-project'
  location: 'eastus2'
  properties: {
    friendlyName: 'My AI Project'
    description: 'Agent Framework Application'
  }
}
```

See [Azure AI Foundry Bicep Documentation](https://learn.microsoft.com/azure/ai-foundry/how-to/create-resource-template) for more details.

---

## 📊 Microsoft Fabric Configuration

### Overview

❌ **Microsoft Fabric cannot be deployed via Bicep**. It is a SaaS service that must be configured through the Fabric portal.

### Manual Setup Steps

1. **Enable Fabric in your tenant**:
   - Navigate to [Microsoft Fabric Portal](https://app.fabric.microsoft.com/)
   - Ensure Fabric is enabled for your organization

2. **Create a workspace**:
   ```
   Fabric Portal → Workspaces → + New workspace
   - Name: <your-workspace-name>
   - License mode: Trial or Fabric capacity
   - Click Create
   ```

3. **Get workspace ID**:
   ```
   Your workspace → Settings → Properties
   Copy: Workspace ID (GUID format)
   ```

4. **Create agents** (if using Fabric for agents):
   ```
   Your workspace → Data Science → + Create Agent
   - Configure agent properties
   - Copy Agent ID (format: asst_xxx...)
   - Repeat for each agent type needed
   ```

5. **Update parameters**:
   ```bicep
   param fabricWorkspaceId = '<YOUR_WORKSPACE_ID>'
   param fabricOrchestratorAgentId = 'asst_<YOUR_AGENT_ID>'
   // ... other agent IDs
   ```

### Required Agent Types

The application expects these 6 agents:

1. **Orchestrator Agent** (`fabricOrchestratorAgentId`)
   - Routes requests to appropriate agents
   - Coordinates multi-agent workflows

2. **Document Agent** (`fabricDocumentAgentId`)
   - Processes and analyzes documents
   - Extracts information from files

3. **Power BI Agent** (`fabricPowerBIAgentId`)
   - Queries Power BI datasets
   - Generates reports and visualizations

4. **Chart Agent** (`fabricChartAgentId`)
   - Creates charts and graphs
   - Visualizes data insights

5. **Sales Agent** (`fabricSalesAgentId`)
   - Handles sales-related queries
   - Analyzes sales data

6. **Realtime Agent** (`fabricRealtimeAgentId`)
   - Provides real-time data analysis
   - Processes streaming data

---

## 📊 Power BI Configuration

### Overview

❌ **Power BI cannot be deployed via Bicep**. Power BI workspaces and reports must be configured through the Power BI portal.

### Manual Setup Steps

1. **Create Power BI workspace**:
   ```
   Power BI Portal → Workspaces → + New workspace
   - Name: <your-workspace-name>
   - Advanced → License mode: Premium per user or Premium capacity
   - Click Save
   ```

2. **Get workspace ID**:
   ```
   Your workspace → Settings → Workspace settings
   Copy: Workspace ID (from URL or settings)
   ```

3. **Create/upload reports**:
   ```
   Your workspace → + New → Upload a file
   - Upload your .pbix file
   - Note the Report ID (from URL after upload)
   ```

4. **Create service principal** (for embedding):
   
   a. Register app in Azure AD:
   ```
   Azure Portal → Azure Active Directory → App registrations
   → + New registration
   - Name: PowerBI-ServicePrincipal-<your-app-name>
   - Supported account types: Single tenant
   - Click Register
   ```
   
   b. Create client secret:
   ```
   Your app → Certificates & secrets → + New client secret
   - Description: PowerBI Access
   - Expires: Choose duration
   - Click Add
   - Copy the secret VALUE (not ID)
   ```
   
   c. Note the IDs:
   ```
   Overview tab:
   - Application (client) ID: <GUID>
   - Directory (tenant) ID: <GUID>
   ```

5. **Grant permissions**:
   
   a. Power BI Service:
   ```
   Power BI Portal → Settings → Admin portal → Tenant settings
   → Developer settings → Enable "Service principals can use Power BI APIs"
   ```
   
   b. Workspace access:
   ```
   Your workspace → Access → Add people or groups
   - Enter service principal name
   - Role: Member or Admin
   - Click Add
   ```

6. **Update parameters**:
   ```bicep
   param powerbiWorkspaceId = '<YOUR_WORKSPACE_ID>'
   param powerbiReportId = '<YOUR_REPORT_ID>'
   param powerbiClientId = '<YOUR_SERVICE_PRINCIPAL_CLIENT_ID>'
   param powerbiClientSecret = '<YOUR_CLIENT_SECRET>'
   param powerbiTenantId = '<YOUR_TENANT_ID>'
   ```

### Power BI Embedding Requirements

For the application to embed Power BI reports:

1. **Service Principal Setup** (as above)
2. **Report Permissions**: Service principal must have access to workspace
3. **Embedding Enabled**: "Embed for your customers" must be enabled
4. **API Permissions**: Service principal needs Power BI API access
5. **License**: Workspace must be on Premium capacity

---

## 🔄 Deployment Workflow

### Full Deployment Flow

```
┌──────────────────────────────────────────────────┐
│ 1. Choose Deployment Options                     │
│    • Existing vs. New Azure OpenAI              │
│    • Existing vs. New AI Foundry                │
│    • Always manual: Fabric & Power BI           │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│ 2. Manual Setup (if needed)                      │
│    • Create Fabric workspace & agents           │
│    • Create Power BI workspace & reports        │
│    • Create service principal                   │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│ 3. Configure Parameters                          │
│    • Update main.parameters.bicepparam          │
│    • Set deployment flags                       │
│    • Provide all service IDs                    │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│ 4. Run Bicep Deployment                          │
│    • Deploy infrastructure (Azure OpenAI, etc)  │
│    • Create SQL database                        │
│    • Deploy App Service                         │
│    • Configure Key Vault                        │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│ 5. Manual AI Foundry Setup (if new)             │
│    • Create agents in portal                    │
│    • Copy agent IDs                             │
│    • Update parameters                          │
│    • Re-deploy                                  │
└──────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────┐
│ 6. Test & Validate                               │
│    • Access web app URL                         │
│    • Test agent responses                       │
│    • Verify Power BI embedding                  │
└──────────────────────────────────────────────────┘
```

---

## 📝 Quick Decision Matrix

**Q: Should I deploy Azure OpenAI via Bicep?**
- ✅ **YES** if: New environment, isolated resources, full automation desired
- ❌ **NO** if: Existing OpenAI, shared across apps, quota management needed

**Q: Should I deploy AI Foundry via Bicep?**
- ⚠️ **MAYBE** if: New environment, comfortable with preview features, accept manual agent setup
- ❌ **NO** if: Existing project, complex agent configs, production-critical

**Q: Can I automate Fabric/Power BI?**
- ❌ **NO**: Must be created manually in their respective portals

---

## 🔗 Additional Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Azure AI Foundry Bicep Templates](https://github.com/Azure-AI-Foundry/foundry-samples)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [Power BI Embedded Documentation](https://learn.microsoft.com/power-bi/developer/embedded/)
- [Azure Verified Modules - Cognitive Services](https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/cognitive-services/account)

---

**Need Help?**
- Check [Troubleshooting Guide](../README.md#-troubleshooting)
- Review [Parameters Reference](PARAMETERS.md)
- See [Quick Start Guide](QUICK_START.md)
