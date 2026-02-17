# 🚀 Azure Developer CLI (azd) Deployment Guide

This guide shows you how to deploy the Azure Agent Framework application using **Azure Developer CLI (`azd`)** commands.

---

## 📋 Table of Contents

- [What is Azure Developer CLI?](#what-is-azure-developer-cli)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Deployment Steps](#detailed-deployment-steps)
- [Environment Configuration](#environment-configuration)
- [Common azd Commands](#common-azd-commands)
- [Comparison: azd vs PowerShell Scripts](#comparison-azd-vs-powershell-scripts)
- [Troubleshooting](#troubleshooting)

---

## 🎯 What is Azure Developer CLI?

**Azure Developer CLI (`azd`)** is a developer-centric command-line tool that makes it easy to build, deploy, and monitor cloud applications on Azure. It provides:

- 🚀 **Simple commands** - `azd up` deploys everything
- 🔄 **Environment management** - Easy dev/staging/prod workflows
- 📦 **Infrastructure as Code** - Uses your existing Bicep templates
- 🔧 **Developer workflow** - Provision, deploy, monitor in one tool
- 🌐 **Cross-platform** - Works on Windows, macOS, Linux

---

## ✅ Prerequisites

### 1. Install Azure Developer CLI

**Windows (PowerShell):**
```powershell
winget install microsoft.azd
```

**macOS (Homebrew):**
```bash
brew tap azure/azd && brew install azd
```

**Linux:**
```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

**Verify installation:**
```bash
azd version
```

### 2. Install Azure CLI (Required)

```powershell
# Windows
winget install Microsoft.AzureCLI

# macOS
brew install azure-cli

# Verify
az --version
```

### 3. Login to Azure

```bash
# Login with azd
azd auth login

# Also login with Azure CLI (required for some operations)
az login
```

### 4. Application Code

Ensure your application code is in the `app/` folder with:
- `main.py`
- `config.py`
- `requirements.txt`
- Application folders (`app/`, `agent_framework/`, `utils/`, etc.)

---

## 🚀 Quick Start

### One-Command Deployment:

```bash
# Initialize, provision infrastructure, and deploy application
azd up
```

That's it! This single command:
1. ✅ Creates a new environment
2. ✅ Prompts for required configuration
3. ✅ Provisions all Azure resources
4. ✅ Deploys your application code
5. ✅ Shows deployment summary

**Time: ~12-15 minutes for first deployment**

---

## 📖 Detailed Deployment Steps

### Step 1: Initialize Environment

```bash
# Navigate to template directory
cd <your-repo-path>

# Initialize azd (first time only)
azd init
```

**You'll be prompted for:**
- Environment name (e.g., `dev`, `staging`, `prod`)
- Azure subscription
- Azure region (default: `eastus2`)

---

### Step 2: Configure Environment Variables

```bash
# Set required variables
azd env set AZURE_APP_NAME "myagents"
azd env set AZURE_SQL_ADMINISTRATOR_LOGIN "sqladmin"
azd env set AZURE_SQL_ADMINISTRATOR_PASSWORD "YourSecureP@ssw0rd123!"

# Optional: Deploy new Azure OpenAI
azd env set AZURE_OPENAI_DEPLOY "true"
azd env set AZURE_OPENAI_MODEL_NAME "gpt-4o"

# Or: Use existing Azure OpenAI
azd env set AZURE_OPENAI_ENDPOINT "https://your-openai.openai.azure.com/"
azd env set AZURE_OPENAI_DEPLOYMENT_NAME "gpt-4o"
azd env set AZURE_OPENAI_API_KEY "your-api-key"

# Azure AI Foundry (if using)
azd env set AZURE_AI_FOUNDRY_ENDPOINT "https://your-aifoundry.cognitiveservices.azure.com/"
azd env set AZURE_AI_PROJECT_NAME "your-project"

# View current configuration
azd env get-values
```

---

### Step 3: Provision Infrastructure

```bash
# Provision all Azure resources (Bicep deployment)
azd provision
```

This deploys:
- App Service Plan & Web App
- Azure SQL Server & Database
- Key Vault
- Application Insights
- (Optional) Azure OpenAI
- (Optional) Container Registry

**Time: ~8-10 minutes**

---

### Step 4: Configure SQL Database (Manual Step)

After provisioning, you'll see instructions to configure SQL database access:

```sql
-- Run these commands in Azure Portal → SQL Database → Query editor:
CREATE USER [webapp-myagents-dev] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [webapp-myagents-dev];
ALTER ROLE db_datawriter ADD MEMBER [webapp-myagents-dev];
```

---

### Step 5: Deploy Application Code

```bash
# Deploy application to App Service
azd deploy
```

This:
- Packages your application code
- Uploads to Azure App Service
- Installs dependencies from `requirements.txt`
- Restarts the web app

**Time: ~3-5 minutes**

---

### Step 6: Verify Deployment

```bash
# Open application in browser
azd browse

# View deployment status
azd show

# Monitor logs
azd monitor --overview
```

---

## 🔧 Environment Configuration

### Using Environment Files

Create environment-specific configuration files:

```bash
# Create dev environment
azd env new dev

# Configure dev settings
azd env set AZURE_APP_NAME "myagents"
azd env set AZURE_ENVIRONMENT_NAME "dev"
azd env set AZURE_LOCATION "eastus2"

# Create staging environment
azd env new staging

# Switch between environments
azd env select dev
azd env select staging
```

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_APP_NAME` | ✅ | Application name prefix |
| `AZURE_ENVIRONMENT_NAME` | ✅ | Environment (dev/staging/prod) |
| `AZURE_LOCATION` | ✅ | Azure region |
| `AZURE_SQL_ADMINISTRATOR_LOGIN` | ✅ | SQL admin username |
| `AZURE_SQL_ADMINISTRATOR_PASSWORD` | ✅ | SQL admin password |
| `AZURE_OPENAI_DEPLOY` | ❌ | Deploy new OpenAI (true/false) |
| `AZURE_OPENAI_ENDPOINT` | ❌ | Existing OpenAI endpoint |
| `AZURE_OPENAI_API_KEY` | ❌ | Existing OpenAI API key |
| `AZURE_AI_FOUNDRY_ENDPOINT` | ❌ | AI Foundry endpoint |
| `AZURE_FABRIC_CAPACITY_ID` | ❌ | Fabric capacity ID |
| `AZURE_POWERBI_WORKSPACE_ID` | ❌ | Power BI workspace ID |

---

## 📚 Common azd Commands

### Deployment Commands

```bash
# Complete deployment (provision + deploy)
azd up

# Provision infrastructure only
azd provision

# Deploy application code only
azd deploy

# Deploy specific service
azd deploy web
```

### Environment Management

```bash
# Create new environment
azd env new <environment-name>

# List all environments
azd env list

# Select active environment
azd env select <environment-name>

# Set environment variable
azd env set <KEY> <value>

# Get environment variable
azd env get <KEY>

# View all environment variables
azd env get-values

# Refresh environment variables
azd env refresh
```

### Monitoring & Management

```bash
# Open application in browser
azd browse

# Show deployment status and resources
azd show

# View monitoring dashboard
azd monitor --overview

# View logs
azd monitor --logs

# View live log stream
azd monitor --logs --follow
```

### Cleanup

```bash
# Delete all Azure resources (keeps environment config)
azd down

# Delete resources and remove environment
azd down --purge

# Force deletion without confirmation
azd down --force
```

---

## ⚖️ Comparison: azd vs PowerShell Scripts

Both deployment methods are available. Choose based on your needs:

| Aspect | azd Commands | PowerShell Scripts |
|--------|--------------|-------------------|
| **Installation** | Requires azd CLI | Built-in PowerShell |
| **Simplicity** | `azd up` (simplest) | `deploy-complete.ps1` |
| **Environment mgmt** | Built-in (`azd env`) | Manual parameter files |
| **Multi-environment** | Easy switching | Multiple param files |
| **Customization** | Limited to hooks | Full script control |
| **CI/CD integration** | Excellent | Excellent |
| **Learning curve** | Learn azd commands | Familiar PowerShell |
| **Cross-platform** | Windows/Mac/Linux | PowerShell Core |

### When to Use azd:

✅ **Use `azd` if you:**
- Want the simplest deployment experience
- Need to manage multiple environments (dev/staging/prod)
- Prefer standardized Azure developer workflow
- Are building multiple Azure applications
- Want built-in monitoring integration

### When to Use PowerShell Scripts:

✅ **Use PowerShell scripts if you:**
- Need maximum customization and control
- Already familiar with PowerShell
- Want to see exactly what's happening
- Need to integrate with existing PowerShell workflows
- Prefer detailed progress output and validation

### Using Both:

You can use both methods interchangeably:
- Use `azd` for quick deployments and environment management
- Use PowerShell scripts for custom workflows or detailed control

---

## 🎯 Common Workflows

### Workflow 1: First-Time Deployment

```bash
# 1. Navigate to template
cd <your-repo-path>

# 2. Initialize and deploy everything
azd up

# Follow prompts to configure environment
# Time: ~15 minutes
```

---

### Workflow 2: Update Application Code

```bash
# Make code changes in app/ folder

# Redeploy just the application (fast)
azd deploy

# Time: ~3 minutes
```

---

### Workflow 3: Multiple Environments

```bash
# Deploy to development
azd env select dev
azd up

# Deploy to staging
azd env select staging
azd up

# Deploy to production
azd env select prod
azd up
```

---

### Workflow 4: Infrastructure Changes

```bash
# Modify Bicep templates in bicep/ folder

# Provision updated infrastructure
azd provision

# Infrastructure changes applied
```

---

### Workflow 5: Complete Teardown

```bash
# Delete all resources
azd down

# Confirm deletion when prompted
# Time: ~5 minutes
```

---

## 🔍 Monitoring with azd

### View Application Status

```bash
# Show deployment overview
azd show

# Output:
# Services:
#   web (App Service)
#     Endpoint: https://webapp-myagents-dev.azurewebsites.net
#     Status: Running
```

### Monitor Logs

```bash
# View recent logs
azd monitor --logs

# Live log streaming
azd monitor --logs --follow

# View specific service logs
azd monitor --logs --service web
```

### Open Monitoring Dashboard

```bash
# Open Application Insights
azd monitor --overview

# Opens Azure Portal monitoring dashboard
```

---

## 🚦 Troubleshooting

### Issue: "azd: command not found"

**Solution:**
```bash
# Install azd
winget install microsoft.azd

# Verify installation
azd version
```

---

### Issue: "Authentication failed"

**Solution:**
```bash
# Re-login with azd
azd auth login

# Also ensure Azure CLI is logged in
az login

# Verify authentication
azd auth login --check-status
```

---

### Issue: "Environment not found"

**Solution:**
```bash
# List available environments
azd env list

# Create new environment
azd env new dev

# Select environment
azd env select dev
```

---

### Issue: "Missing required environment variables"

**Solution:**
```bash
# Check current variables
azd env get-values

# Set missing variables
azd env set AZURE_APP_NAME "myagents"
azd env set AZURE_SQL_ADMINISTRATOR_LOGIN "sqladmin"
azd env set AZURE_SQL_ADMINISTRATOR_PASSWORD "SecurePassword123!"
```

---

### Issue: "Deployment failed"

**Solution:**
```bash
# View detailed error
azd show

# Check logs
azd monitor --logs

# View Azure Portal for resource status
azd monitor --overview

# Try provisioning again
azd provision --debug
```

---

### Issue: "SQL configuration not working"

**Solution:**
The SQL managed identity configuration is a manual step:

1. Go to Azure Portal
2. Navigate to your SQL Database
3. Click "Query editor"
4. Run the provided SQL commands
5. Retry deployment: `azd deploy`

---

## 🎓 Advanced Usage

### Custom Hooks

The `azure.yaml` file includes hooks for custom logic:

```yaml
hooks:
  preprovision:
    shell: pwsh
    run: |
      Write-Host "Running pre-provision validation..."
  
  postprovision:
    shell: pwsh
    run: |
      Write-Host "Infrastructure deployed!"
  
  postdeploy:
    shell: pwsh
    run: |
      Write-Host "Application deployed!"
```

### Using azd in CI/CD

**GitHub Actions:**
```yaml
- name: Deploy with azd
  run: |
    azd auth login --client-id ${{ secrets.AZURE_CLIENT_ID }} \
      --tenant-id ${{ secrets.AZURE_TENANT_ID }} \
      --client-secret ${{ secrets.AZURE_CLIENT_SECRET }}
    azd env select prod
    azd up --no-prompt
```

**Azure DevOps:**
```yaml
- task: AzureCLI@2
  inputs:
    azureSubscription: 'Production'
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      azd env select prod
      azd up --no-prompt
```

---

## 📚 Additional Resources

- **azd Documentation:** https://learn.microsoft.com/azure/developer/azure-developer-cli/
- **azd GitHub:** https://github.com/Azure/azure-dev
- **azd Templates:** https://azure.github.io/awesome-azd/
- **Main README:** [../README.md](../README.md)
- **PowerShell Deployment:** [../scripts/README.md](../scripts/README.md)

---

## 🎉 Quick Reference

### Essential Commands

```bash
# First deployment
azd up

# Update code only
azd deploy

# View application
azd browse

# View status
azd show

# View logs
azd monitor --logs

# Teardown
azd down
```

### Environment Management

```bash
# Create environment
azd env new <name>

# Switch environment
azd env select <name>

# Set variable
azd env set <KEY> <value>

# View variables
azd env get-values
```

---

**Made with ❤️ for Azure Agent Framework**  
*Deploying to Azure, the developer way* 🚀
