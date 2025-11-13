# Azure Intelligent Agent Starter

🚀 **Production-ready deployment template for intelligent AI agent applications on Azure**

This comprehensive starter template enables anyone to deploy intelligent AI agent applications to Azure using Infrastructure as Code (Bicep) and Azure Developer CLI (azd). Perfect for building production-ready, secure, and scalable AI agent solutions.

Supports **optional Azure OpenAI deployment**! You can deploy Azure OpenAI with your app or use an existing instance. See [Azure Services Deployment Guide](docs/AZURE_SERVICES_DEPLOYMENT.md).

🎯 **TURNKEY DEPLOYMENT**: Deploy everything with one command - choose your preferred method!

---

## 📋 Table of Contents

- [🚀 Deployment Options](#-deployment-options)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Post-Deployment](#-post-deployment)
- [Troubleshooting](#-troubleshooting)
- [Cost Estimation](#-cost-estimation)

---

## 🚀 Deployment Options

Choose your preferred deployment method:

### Option 1: Azure Developer CLI (azd) - Recommended ⭐

**The simplest way to deploy** - perfect for developers:

```bash
# One command deploys everything!
azd up
```

- ✅ **Simplest** - Just `azd up`
- ✅ **Environment management** - Easy dev/staging/prod workflows
- ✅ **Cross-platform** - Windows, macOS, Linux
- ✅ **Built-in monitoring** - `azd monitor`

📖 **[Full azd Guide](docs/AZD_DEPLOYMENT_GUIDE.md)**

---

### Option 2: PowerShell Scripts - Maximum Control

**For detailed control and customization**:

**For detailed control and customization**:

```powershell
# 1. Configure parameters (one-time setup)
Copy-Item bicep\main.bicepparam.template bicep\main.bicepparam
code bicep\main.bicepparam  # Update <REPLACE_WITH_*> values

# 2. Run complete deployment (10-15 minutes)
cd scripts
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"
```

- ✅ **Detailed progress** - See every step
- ✅ **Maximum control** - Full customization
- ✅ **Familiar** - PowerShell scripting
- ✅ **Skip flags** - Partial deployments

📖 **[PowerShell Scripts Guide](scripts/README.md)**

---

### Quick Comparison

| Feature | azd | PowerShell Scripts |
|---------|-----|-------------------|
| **Simplicity** | `azd up` ⭐ | `deploy-complete.ps1` |
| **Environment mgmt** | Built-in | Manual param files |
| **Cross-platform** | ✅ Yes | PowerShell Core |
| **Customization** | Hooks | Full control |
| **Learning curve** | Minimal | PowerShell knowledge |

**Choose azd for simplicity, PowerShell for control.** Both are fully supported!

---

## ⚡ Quick Redeploy (Code Only)

### Using azd:

### Using azd:
```bash
azd deploy  # 3 minutes
```

### Using PowerShell:
```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -SkipInfrastructure  # 3-5 minutes
```

---

## ✨ Features

- **Infrastructure as Code**: Complete Azure infrastructure defined in Bicep templates
- **Modular Architecture**: Separate Bicep modules for each Azure service (App Service, SQL, Key Vault, etc.)
- **Security Best Practices**: 
  - Azure Key Vault for secrets management
  - Managed identities for Azure AD authentication
  - HTTPS-only endpoints with TLS 1.2+
  - Row-Level Security (RLS) for SQL
- **Production Ready**: Application Insights monitoring, health checks, auto-scaling support
- **Flexible Configuration**: Support for dev/staging/prod environments
- **Automated Deployment**: PowerShell and Bash scripts for end-to-end deployment
- **📊 Optional Fabric Data Management**: Synthetic data generation for testing and demos
  - Database schema deployment (Categories, Products, Customers, Orders, OrderItems)
  - Automated data generation using Faker library
  - Azure Function for ongoing data maintenance
  - Management tools for viewing and testing database content
  - Deploy with `-DeployFabric` flag (see [Fabric Deployment Guide](docs/FABRIC_DEPLOYMENT.md))

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Azure Subscription                     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Resource Group (rg-agents-prod)            │ │
│  │                                                          │ │
│  │  ┌─────────────┐      ┌──────────────┐                 │ │
│  │  │  App Service│◄────►│   Key Vault  │                 │ │
│  │  │  (Linux)    │      │   (Secrets)  │                 │ │
│  │  │  Python 3.11│      └──────────────┘                 │ │
│  │  └──────┬──────┘                                        │ │
│  │         │                                                │ │
│  │         ▼                                                │ │
│  │  ┌──────────────┐     ┌──────────────┐                 │ │
│  │  │ SQL Database │     │ App Insights │                 │ │
│  │  │   (Azure AD) │     │ (Monitoring) │                 │ │
│  │  └──────────────┘     └──────────────┘                 │ │
│  │                                                          │ │
│  │  External Dependencies:                                 │ │
│  │  • Azure OpenAI (GPT-4)                                │ │
│  │  • Azure AI Foundry (Agents API)                       │ │
│  │  • Microsoft Fabric (Workspace & Agents)               │ │
│  │  • Power BI (Embedded Reports)                         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Azure Resources Deployed

| Resource | Purpose | Optional |
|----------|---------|----------|
| **App Service Plan** | Hosts the web application (Linux, Python 3.11) | No |
| **App Service** | FastAPI application with Agent Framework | No |
| **SQL Server** | Stores application data with RLS | No |
| **SQL Database** | Agent data, user authentication, analytics | No |
| **Key Vault** | Secure secrets management | Yes |
| **Application Insights** | Monitoring, logging, diagnostics | Yes |
| **Container Registry** | Docker image storage (if using containers) | Yes |

---

## 📦 Prerequisites

Before deploying, ensure you have:

### 1. Azure Account & CLI
- Active Azure subscription
- Azure CLI 2.50+ installed ([Install](https://aka.ms/installazurecli))
- Logged in: `az login`

### 2. Azure Services Configuration

This template can **optionally deploy** some Azure services, or you can use existing ones:

#### ✅ Can Be Deployed by This Template:
- **Azure OpenAI**: Optional deployment with GPT-4 model (set `deployAzureOpenAI=true`)
  - See [Azure Services Deployment Guide](docs/AZURE_SERVICES_DEPLOYMENT.md#-azure-openai-deployment)

#### ⚠️ Partially Supported:
- **Azure AI Foundry**: Hub/Project deployment supported (preview), agents require manual setup
  - See [Azure Services Deployment Guide](docs/AZURE_SERVICES_DEPLOYMENT.md#-azure-ai-foundry-deployment)

#### ❌ Manual Setup Required:
- **Microsoft Fabric**: Workspace with configured agents (SaaS service, portal-only)
- **Power BI**: Workspace with reports and service principal (SaaS service, portal-only)

👉 **See [Azure Services Deployment Guide](docs/AZURE_SERVICES_DEPLOYMENT.md) for detailed instructions on each service.**

---

#### How to Get Configuration Values:

**Azure OpenAI:**
```bash
# Azure Portal → Azure OpenAI → Keys and Endpoint
Endpoint: https://<your-resource>.openai.azure.com/
API Key: <copy from portal>
Deployment: gpt-4o (or your model deployment name)
```

**Azure AI Foundry:**
```bash
# AI Foundry Portal → Project → Settings
Project Endpoint: https://<project>.<region>.api.azureml.ms/agents/v1.0/...
Connection Name: aoai-connection (your OpenAI connection name)
```

**Microsoft Fabric:**
```bash
# Fabric → Workspace → Settings → Properties
Workspace ID: <GUID>
# Fabric → Data Science → Create Agent (for each agent type)
Agent IDs: <asst_xxx...> (6 agents: orchestrator, document, powerbi, chart, sales, realtime)
```

**Power BI:**
```bash
# Power BI → Workspace Settings → Properties
Workspace ID: <GUID>
Report ID: <GUID> (from report URL or settings)

# Azure AD → App Registrations → New Registration
Service Principal Client ID: <GUID>
Tenant ID: <GUID>
Client Secret: <create in Certificates & secrets>
```

### 3. Permissions
- **Contributor** role on Azure subscription or resource group
- **Application Administrator** in Azure AD (for service principal creation)

### 4. Local Tools
- PowerShell 7.0+ (Windows/Mac/Linux) OR Bash 4.0+
- Git (optional, for cloning)

---

## 🚀 Quick Start

### Step 1: Get the Template

```bash
# Option A: Clone the repository
git clone <repository-url>
cd azure-deployment-template

# Option B: Download ZIP and extract
# (Use this if you received the template as a package)
```

### Step 2: Configure Parameters

1. Copy the parameters template:
```bash
cd bicep
cp main.bicepparam main.parameters.bicepparam
```

2. Edit `main.parameters.bicepparam` and replace all `<REPLACE_WITH_*>` placeholders:

```bicep
// Example minimal configuration
param appName = 'myagents'  // Your app name (3-20 chars)
param location = 'eastus2'
param environment = 'prod'

// Azure OpenAI
param azureOpenAIEndpoint = 'https://myopenai.openai.azure.com/'
param azureOpenAIApiKey = '<your-key>'
param azureOpenAIDeployment = 'gpt-4o'

// AI Foundry
param projectEndpoint = '<your-ai-foundry-endpoint>'

// Fabric & Power BI
param fabricWorkspaceId = '<your-fabric-workspace-id>'
param fabricOrchestratorAgentId = '<agent-id>'
// ... (fill in all agent IDs)

param powerbiWorkspaceId = '<workspace-id>'
param powerbiReportId = '<report-id>'
param powerbiClientId = '<service-principal-client-id>'
param powerbiClientSecret = '<service-principal-secret>'

// SQL
param sqlServerName = 'myagents-sql-server'  // Must be globally unique!
param sqlAzureAdAdminLogin = 'admin@yourdomain.com'
param sqlAzureAdAdminSid = '<your-azure-ad-object-id>'
```

⚠️ **Security Warning**: Never commit secrets to source control!

### Step 3: Deploy

```powershell
# PowerShell (Windows/Mac/Linux)
cd scripts
./deploy.ps1 -ResourceGroupName "rg-agents-prod" -Location "eastus2"
```

```bash
# Bash (Linux/Mac)
cd scripts
chmod +x deploy.sh
./deploy.sh --resource-group "rg-agents-prod" --location "eastus2"
```

The script will:
1. ✅ Create Azure resource group
2. ✅ Deploy all infrastructure (5-10 minutes)
3. ✅ Configure SQL database access
4. ✅ Deploy application code
5. ✅ Display your application URL

---

### Step 3b: Deploy with Fabric Data Management (Optional)

Add synthetic data generation for testing and demos:

```powershell
# Deploy everything including Fabric
cd scripts
.\deploy-complete.ps1 `
    -ResourceGroupName "rg-agents-prod" `
    -DeployFabric `
    -GenerateInitialData
```

This additionally:
- ✅ Deploys database schema (Categories, Products, Customers, Orders, OrderItems)
- ✅ Generates initial synthetic data (~100 customers, ~50 products, ~200 orders)
- ✅ Deploys Azure Function for ongoing data generation
- 📖 See [Fabric Deployment Guide](docs/FABRIC_DEPLOYMENT.md) for details

---

## ⚙️ Configuration

### Environment-Specific Configurations

**Development:**
```bicep
param environment = 'dev'
param appServicePlanSku = 'B1'  // Cheaper tier
param sqlDatabaseSku = 'Basic'
param enableKeyVault = false
param enableAuthentication = false
param logLevel = 'DEBUG'
```

**Production:**
```bicep
param environment = 'prod'
param appServicePlanSku = 'P1v2'  // Production tier
param sqlDatabaseSku = 'S2'
param enableKeyVault = true
param enableAuthentication = true
param logLevel = 'INFO'
```

### Key Configuration Options

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `appServicePlanSku` | App Service pricing tier | `B2` | `B1`, `B2`, `S1`, `P1v2`, `P2v2` |
| `sqlDatabaseSku` | SQL Database pricing tier | `Basic` | `Basic`, `S0`, `S1`, `S2`, `P1` |
| `enableKeyVault` | Use Key Vault for secrets | `true` | `true`, `false` |
| `enableAuthentication` | JWT auth & RLS | `true` | `true`, `false` |
| `sqlUseAzureAuth` | Managed identity for SQL | `true` | `true`, `false` |
| `enableApplicationInsights` | Monitoring & diagnostics | `true` | `true`, `false` |
| `logLevel` | Application log level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## 📦 Deployment

### Manual Step-by-Step Deployment

If you prefer manual control:

#### 1. Create Resource Group
```bash
az group create --name rg-agents-prod --location eastus2
```

#### 2. Deploy Infrastructure
```bash
cd bicep
az deployment group create \
  --name agent-framework-deployment \
  --resource-group rg-agents-prod \
  --template-file main.bicep \
  --parameters main.parameters.bicepparam
```

#### 3. Configure SQL Database
```bash
# Get the web app name from deployment outputs
$webAppName = az deployment group show \
  --name agent-framework-deployment \
  --resource-group rg-agents-prod \
  --query properties.outputs.webAppName.value -o tsv

# Open Azure Portal → SQL Database → Query Editor
# Run these SQL commands:
CREATE USER [$webAppName] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [$webAppName];
```

#### 4. Deploy Application Code
```bash
cd ../app

# Create ZIP deployment package
zip -r ../deploy.zip .

# Deploy to App Service
az webapp deployment source config-zip \
  --resource-group rg-agents-prod \
  --name $webAppName \
  --src ../deploy.zip

# Restart the app
az webapp restart --name $webAppName --resource-group rg-agents-prod
```

---

## 🔧 Post-Deployment

### 1. Verify Deployment

```bash
# Get deployment outputs
az deployment group show \
  --name agent-framework-deployment \
  --resource-group rg-agents-prod \
  --query properties.outputs

# Expected outputs:
{
  "webAppName": "myagents-prod-app",
  "webAppUrl": "https://myagents-prod-app.azurewebsites.net",
  "sqlServerName": "myagents-sql-server",
  "sqlDatabaseName": "aiagentsdb"
}
```

### 2. Test Application

Open your browser to the `webAppUrl`:

```
https://myagents-prod-app.azurewebsites.net
```

**Default Login** (if authentication enabled):
- Username: `admin`
- Password: `Admin@123`

⚠️ **CRITICAL**: Change the default password immediately!

### 3. Monitor Application

```bash
# Stream live logs
az webapp log tail \
  --name myagents-prod-app \
  --resource-group rg-agents-prod

# View Application Insights
# Azure Portal → Application Insights → Live Metrics
```

### 4. Initial Configuration

Navigate to the application settings page and configure:
- ✅ Change default admin password
- ✅ Create additional users (if RLS enabled)
- ✅ Test agent functionality
- ✅ Verify Power BI embeddings
- ✅ Check SQL database connectivity

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: Deployment fails with "SQL Server name already exists"
**Solution**: Change `sqlServerName` parameter to a globally unique value

#### Issue: Web app shows "Application Error"
**Solution**: Check logs
```bash
az webapp log tail --name <app-name> -g <resource-group>
```

Common causes:
- Missing secrets in Key Vault
- SQL connection issues
- Invalid Azure OpenAI endpoint

#### Issue: Cannot connect to SQL Database
**Solution**: Ensure managed identity has access
```sql
-- Run in SQL Query Editor
CREATE USER [<webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<webapp-name>];
```

#### Issue: Power BI reports not loading
**Solution**: Verify service principal permissions
- Add service principal to Power BI workspace
- Grant "Member" or "Admin" role
- Enable service principal in Power BI admin portal

#### Issue: "Authentication failed" errors
**Solution**: Check JWT configuration
```bash
# Verify JWT secret is set
az webapp config appsettings list \
  --name <app-name> \
  --resource-group <resource-group> \
  --query "[?name=='JWT_SECRET_KEY']"
```

### Debug Mode

Enable detailed logging:

```bash
# Update app settings
az webapp config appsettings set \
  --name <app-name> \
  --resource-group <resource-group> \
  --settings LOG_LEVEL=DEBUG
```

### Get Help

```bash
# Check deployment logs
az deployment group show \
  --name agent-framework-deployment \
  --resource-group rg-agents-prod \
  --query properties.error

# View resource health
az resource list \
  --resource-group rg-agents-prod \
  --output table
```

---

## 💰 Cost Estimation

### Monthly Cost Breakdown (USD)

**Minimal Development** (~$50-75/month):
- App Service B1: ~$13
- SQL Database Basic: ~$5
- Application Insights: ~$2
- Key Vault: ~$1
- **Total: ~$21/month** + External services

**Production** (~$200-300/month):
- App Service P1v2: ~$145
- SQL Database S2: ~$120
- Application Insights: ~$10
- Key Vault: ~$1
- **Total: ~$276/month** + External services

**External Services** (not included):
- Azure OpenAI: ~$0.03-0.12 per 1K tokens
- Azure AI Foundry: Based on usage
- Microsoft Fabric: Based on capacity/usage
- Power BI: Depends on licensing

💡 **Cost Optimization Tips**:
- Use B-series App Service for development
- Enable auto-shutdown for dev environments
- Use Basic SQL tier for testing
- Monitor usage with Azure Cost Management

---

## 📚 Additional Resources

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/azure/ai-services/agents/)
- [Azure App Service Documentation](https://learn.microsoft.com/azure/app-service/)
- [Azure SQL Database Best Practices](https://learn.microsoft.com/azure/azure-sql/database/best-practices-overview)
- [Azure Key Vault Secrets Management](https://learn.microsoft.com/azure/key-vault/secrets/)
- [Bicep Language Reference](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)

---

## 📄 License

[Add your license information here]

---

## 🤝 Contributing

[Add contribution guidelines here]

---

## ✉️ Support

For issues or questions:
- 📧 Email: [your-email]
- 🐛 Issues: [GitHub Issues]
- 📖 Docs: [Documentation Link]

---

**Made with ❤️ using Microsoft Agent Framework**
