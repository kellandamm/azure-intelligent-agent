# Azure Intelligent Agent Starter

🚀 **Production-ready deployment template for intelligent AI agent applications on Azure**

[![Security](https://img.shields.io/badge/Security-Hardened-green)](SECURITY_REVIEW_REPORT.md)
[![Score](https://img.shields.io/badge/Security_Score-75%2F100-yellow)](SECURITY_FIXES_APPLIED.md)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen)](docs/AZURE_FOUNDRY_MCP_DEPLOYMENT.md)
[![Version](https://img.shields.io/badge/Version-1.2.0-blue)](docs/CHANGELOG.md)

This comprehensive starter template enables you to deploy intelligent AI agent applications to Azure using Infrastructure as Code (Bicep) and Azure Developer CLI (azd). Perfect for building production-ready, secure, and scalable AI agent solutions.

Supports **optional Azure OpenAI deployment**! You can deploy Azure OpenAI with your app or use an existing instance. See [Azure Services Deployment Guide](docs/AZURE_SERVICES_DEPLOYMENT.md).

🎯 **TURNKEY DEPLOYMENT**: Deploy everything with one command - choose your preferred method!

---

## 🆕 What's New in v1.2.0

**Three-Factor Architecture Implementation** - Major architectural improvement for maintainability and testability!

✨ **New Services Layer**:
- `AuthService` - Authentication & authorization logic
- `ChatService` - Chat processing with RLS context
- `AdminService` - Configuration & health checks
- `AnalyticsService` - Metrics & insights

✨ **New Route Modules**:
- `routes_pages.py` - HTML page routes
- `routes_chat.py` - Chat API endpoints
- `routes_admin_api.py` - Admin API endpoints
- `routes_analytics_api.py` - Analytics API endpoints

✨ **Testing & Quality**:
- 14 unit tests for services layer
- Improved code maintainability (47% reduction in main.py size)
- Azure App Service compatibility verified

📖 **See [CHANGELOG.md](docs/CHANGELOG.md) for complete version history**

---

## 🔐 Security First

**Last Security Audit:** January 30, 2026 |

### ✅ Security Features Implemented
- ✅ **Authentication:** JWT with HttpOnly cookies, dependency injection enforcement
- ✅ **Rate Limiting:** Prevents brute force attacks (5 login attempts/minute)
- ✅ **Input Validation:** Prompt injection detection, length limits, sanitization
- ✅ **CORS Protection:** Restricted to configured domains only
- ✅ **Security Headers:** XSS, clickjacking, MIME-sniffing protection
- ✅ **RLS Infrastructure:** Database-level Row-Level Security ready to activate
- ✅ **Audit Logging:** All data access logged for compliance
- ✅ **No Default Credentials:** Secure admin setup required (see [guide](CREATE_ADMIN_USER.md))

### 📋 Before Production Deployment
- [ ] Generate unique `JWT_SECRET` - never use defaults!
- [ ] Configure production domains in CORS settings
- [ ] Create admin user with strong password
- [ ] Activate RLS policies on your tables
- [ ] Review [Security Checklist](SECURITY_FIXES_APPLIED.md#deployment-checklist)

**⚠️ CRITICAL:** The default admin credentials have been **removed** for security. You must create your admin user following [CREATE_ADMIN_USER.md](CREATE_ADMIN_USER.md).

---

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have:

1. **Azure Subscription** with contributor access
2. **Azure CLI** installed ([Install](https://docs.microsoft.com/cli/azure/install-azure-cli))
3. **Azure Developer CLI (azd)** installed ([Install](https://aka.ms/azure-dev/install))
4. **Docker Desktop** (for local builds and deployments)
5. **Python 3.10+** (for local development)

### First-Time Setup

1. **Clone this repository:**
   ```bash
   git clone <your-repo-url>
   cd azure-intelligent-agent
   ```

2. **Configure your environment:**
   ```bash
   # Copy environment template
   cd app
   cp .env.example .env
   
   # Edit .env with your Azure resource details
   # See CONFIGURATION.md for detailed instructions
   ```

3. **Set deployment variables:**
   ```powershell
   # PowerShell
   $env:AZURE_RESOURCE_GROUP = "rg-myagent-prod"
   $env:AZURE_APP_NAME = "myagent-app"
   $env:AZURE_CONTAINER_REGISTRY = "myagentacr"
   ```
   
   ```bash
   # Bash/Linux
   export AZURE_RESOURCE_GROUP="rg-myagent-prod"
   export AZURE_APP_NAME="myagent-app"
   export AZURE_CONTAINER_REGISTRY="myagentacr"
   ```

4. **Deploy to Azure:**
   ```bash
   azd up
   ```

📖 **For detailed configuration instructions, see [CONFIGURATION.md](CONFIGURATION.md)**

---

## 📋 Table of Contents

- [Deployment Options](#-deployment-options)
- [Features](#-features)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Local Development](#-local-development)
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
# 1. Configure parameters (one-time setup)
bicep\main.bicepparam

# 2.Then one command deploys everything!
azd up
```

- ✅ **Simplest** - Just `azd up`
- ✅ **Environment management** - Easy dev/staging/prod workflows
- ✅ **Cross-platform** - Windows, macOS, Linux
- ✅ **Built-in monitoring** - `azd monitor`

📖 **[Full azd Guide](docs/AZD_DEPLOYMENT_GUIDE.md)**

### Option 2: Azure AI Foundry + MCP Server 🆕

**Advanced architecture** with Azure AI Foundry native agents and centralized function calling:

```bash
# Uses Azure AI Foundry agents instead of Agent Framework
# Includes MCP (Model Context Protocol) server for function calling
azd up
```

- ✅ **Native Azure AI Foundry** - Uses Azure's native agent platform
- ✅ **Centralized function calling** - MCP server for all tools
- ✅ **Better scalability** - Container Apps architecture
- ✅ **Existing infrastructure** - Can reuse existing Container Apps environment

📖 **[Azure AI Foundry + MCP Deployment Guide](docs/AZURE_FOUNDRY_MCP_DEPLOYMENT.md)**

---

### Option 3: PowerShell Scripts - Maximum Control

**For detailed control and customization**:

```powershell
# 1. Set environment variables
$env:AZURE_RESOURCE_GROUP = "rg-myagents-prod"
$env:AZURE_APP_NAME = "myagent-app"
$env:AZURE_CONTAINER_REGISTRY = "myagentacr"

# 2. Run deployment script
.\deploy.ps1
```

- ✅ **Detailed progress** - See every step
- ✅ **Maximum control** - Full customization
- ✅ **Familiar** - PowerShell scripting
- ✅ **Environment variables** - Easy configuration

📖 **[Deployment Guide](DEPLOYMENT.md)** | **[Configuration Guide](CONFIGURATION.md)**

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
- **🏛️ Three-Factor Architecture (v1.2.0)**: Clean separation of concerns for maintainability
  - **Factor 1: Routes** - HTTP layer handling requests/responses (4 route modules)
  - **Factor 2: Services** - Business logic layer (4 service classes)
  - **Factor 3: Configuration** - Startup and registration (minimal main.py)
  - **Benefits**: Improved testability, maintainability, and Azure App Service compatibility

---

## 🏛️ Application Architecture (v1.2.0)

### Three-Factor Pattern

This application follows a **Three-Factor Architecture** pattern for clean separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                      │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Factor 1: Routes (HTTP Layer)                         │ │
│  │  ─────────────────────────────────────────────────────  │ │
│  │  • routes_pages.py      - HTML page routes            │ │
│  │  • routes_chat.py       - Chat API endpoints          │ │
│  │  • routes_admin_api.py  - Admin API endpoints         │ │
│  │  • routes_analytics_api.py - Analytics API endpoints  │ │
│  └────────────┬───────────────────────────────────────────┘ │
│               │ calls                                         │
│               ▼                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Factor 2: Services (Business Logic Layer)            │ │
│  │  ─────────────────────────────────────────────────────  │ │
│  │  • AuthService      - Authentication & authorization   │ │
│  │  • ChatService      - Chat processing with RLS context │ │
│  │  • AdminService     - Configuration & health checks    │ │
│  │  • AnalyticsService - Metrics & insights              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Factor 3: Configuration (main.py)                     │ │
│  │  ─────────────────────────────────────────────────────  │ │
│  │  • FastAPI app initialization                          │ │
│  │  • Router registration                                 │ │
│  │  • Middleware setup (CORS, RLS, rate limiting)        │ │
│  │  • Startup configuration                               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Services Layer

The application includes four core services for business logic:

| Service | Purpose | Key Methods |
|---------|---------|-------------|
| **AuthService** | Authentication & authorization | `verify_token()`, `check_user_access()`, `authenticate_user()` |
| **ChatService** | Chat processing with RLS | `process_message()`, `get_rls_context()`, `log_interaction()` |
| **AdminService** | Admin operations | `get_system_stats()`, `get_health_status()`, `get_configuration()` |
| **AnalyticsService** | Analytics & insights | `get_metrics()`, `get_cohort_analysis()`, `get_insights()` |

**Benefits**:
- ✅ **Testable**: Services are plain Python classes (no HTTP dependencies)
- ✅ **Maintainable**: Business logic isolated from HTTP framework
- ✅ **Azure-Ready**: Absolute imports for App Service compatibility
- ✅ **14 Unit Tests**: Comprehensive test coverage for all services

📖 **See [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for detailed architecture documentation**

---

## 🏗️ Azure Infrastructure Architecture

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

### 2. Verify Deployment with Smoke Tests

**Recommended**: Run comprehensive smoke tests to verify all functionality:

```powershell
# PowerShell - Auto-discover URL from Azure
.\tests\smoke-test.ps1 -ResourceGroupName "rg-agents-prod"

# Or test specific URL
.\tests\smoke-test.ps1 -Url "https://myagents-prod-app.azurewebsites.net"
```

```bash
# Python - Cross-platform
python tests/smoke_test.py --url https://myagents-prod-app.azurewebsites.net

# Local development
python tests/smoke_test.py --url http://localhost:8000 --skip-auth
```

**What Smoke Tests Verify:**
- ✅ Health endpoints and application status
- ✅ Authentication system
- ✅ Chat and agent APIs
- ✅ Sales and Analytics dashboards
- ✅ Database connectivity
- ✅ Response times and performance
- ✅ Row-Level Security (RLS) filtering

**Example Output:**
```
✅ PASS - Health Endpoint (145ms)
✅ PASS - Chat Endpoint (234ms)
✅ PASS - Sales Dashboard (189ms)
✅ PASS - Database Connectivity (98ms)
========================================
📊 TEST SUMMARY
Total Tests: 15
✅ Passed: 15
⏱️  Duration: 3.42s

✅ ALL TESTS PASSED - APPLICATION IS HEALTHY
```

📖 **See [Smoke Test Guide](tests/README.md) for detailed documentation**

### 3. Test Application

Open your browser to the `webAppUrl`:

```
https://myagents-prod-app.azurewebsites.net
```

**Default Login** (if authentication enabled):
- Username: `admin`
- Password: `Admin@123`

⚠️ **CRITICAL**: Change the default password immediately!

### 4. Monitor Application

```bash
# Stream live logs
az webapp log tail \
  --name myagents-prod-app \
  --resource-group rg-agents-prod

# View Application Insights
# Azure Portal → Application Insights → Live Metrics
```

### 5. Initial Configuration

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

### Documentation
- [Documentation Index](docs/DOCUMENTATION_INDEX.md) - Complete documentation guide
- [Enterprise Use Cases](docs/DEMO_QUESTIONS.md) - Business scenarios and sample queries
- [Deployment Guide](docs/QUICK_START.md) - Step-by-step instructions
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Smoke Test Guide](tests/README.md) - Testing and verification

### Microsoft Resources
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
