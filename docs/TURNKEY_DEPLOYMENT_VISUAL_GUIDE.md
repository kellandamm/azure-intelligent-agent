# 🚀 Turnkey Deployment - Quick Visual Guide

**Deploy your entire Azure Agent Framework application with ONE command!**

---

## 📸 Visual Walkthrough

### Step 1: Configure Parameters (One-Time Setup)

```powershell
# Navigate to template directory
cd c:\code\agentsdemos\azure-deployment-template

# Copy template to create your parameters file
Copy-Item bicep\main.bicepparam.template bicep\main.bicepparam

# Open in VS Code to edit
code bicep\main.bicepparam
```

**What to update:**
```bicep
// Find and replace these values:
using './main.bicep'

param appName = 'myagents'                    // Your app name
param environment = 'prod'                    // dev, staging, or prod
param location = 'eastus2'                    // Azure region

// SQL Server settings
param sqlAdministratorLogin = 'sqladmin'                          // ✏️ CHANGE THIS
param sqlAdministratorPassword = 'YourSecureP@ssw0rd123!'         // ✏️ CHANGE THIS

// Azure OpenAI (if using existing instance)
param azureOpenAIEndpoint = 'https://your-openai.openai.azure.com/' // ✏️ UPDATE THIS
param azureOpenAIDeployment = 'gpt-4'                                // ✏️ UPDATE THIS
param azureOpenAIApiKey = ''                                         // ✏️ ADD KEY

// Fabric & Power BI (manual setup required)
param fabricCapacityId = ''              // Leave empty, configure later
param powerBIWorkspaceId = ''            // Leave empty, configure later
```

💾 **Save the file** (Ctrl+S)

---

### Step 2: Run Turnkey Deployment

```powershell
# Navigate to scripts directory
cd scripts

# Run the master deployment script
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"
```

---

### 📺 What You'll See

```
╔══════════════════════════════════════════════════════════════╗
║    AZURE AGENT FRAMEWORK - COMPLETE DEPLOYMENT              ║
╚══════════════════════════════════════════════════════════════╝

🔍 Checking prerequisites...
  ✓ Azure CLI version 2.57.0 detected
  ✓ Logged in as user@domain.com
  ✓ Using subscription: Azure Subscription 1 (12345678-1234-1234-1234-123456789abc)
  ✓ Parameters file found: ..\bicep\main.bicepparam
  ✓ Source application directory: C:\code\agentsdemos

═══════════════════════════════════════════════════════════════
STEP 1/5: Preparing Application Code
═══════════════════════════════════════════════════════════════
📦 Preparing application code for deployment...
  ✓ Source directory validated
  ✓ Copying root files (8 files)...
    • main.py
    • config.py
    • requirements.txt
    • agent_framework_manager.py
    • agent_tools.py
    • routes_sales.py
    • host.json
    • .env.template
  ✓ Copying application folders...
    • app/ (42 files)
    • agent_framework/ (28 files)
    • utils/ (15 files)
    • static/ (38 files)
    • demos/ (22 files)
  ✓ Creating deployment configuration (.deployment)
  ✓ Creating startup script (startup.sh)
  ✓ Validating deployment package...

📊 Application Package Summary:
  • Total files: 153
  • Total size: 2.4 MB
  • Package structure validated ✓

═══════════════════════════════════════════════════════════════
STEP 2/5: Deploying Infrastructure
═══════════════════════════════════════════════════════════════
🏗️ Deploying Azure infrastructure...
  ✓ Resource group 'rg-myagents-prod' created in eastus2
  ✓ Starting Bicep deployment...
    This will take approximately 8-10 minutes...

  Deploying resources:
    ⏳ App Service Plan...
    ⏳ App Service (Web App)...
    ⏳ SQL Server...
    ⏳ SQL Database...
    ⏳ Key Vault...
    ⏳ Application Insights...

  [████████████████████████████████] 100% Complete

  ✓ Infrastructure deployment completed successfully!

  Deployed resources:
    • App Service: webapp-myagents-prod.azurewebsites.net
    • SQL Server: sql-myagents-prod.database.windows.net
    • SQL Database: sqldb-myagents-prod
    • Key Vault: kv-myagents-prod-abc123

═══════════════════════════════════════════════════════════════
STEP 3/5: Configuring SQL Database Access
═══════════════════════════════════════════════════════════════
📋 SQL Database Configuration Required

The managed identity needs access to the SQL database.
Please run these commands in Azure Portal (SQL Database → Query editor):

  ┌─────────────────────────────────────────────────────────┐
  │ CREATE USER [webapp-myagents-prod] FROM EXTERNAL PROVIDER│
  │ ALTER ROLE db_datareader ADD MEMBER [webapp-myagents-prod]│
  │ ALTER ROLE db_datawriter ADD MEMBER [webapp-myagents-prod]│
  └─────────────────────────────────────────────────────────┘

📖 Quick steps:
  1. Go to Azure Portal → SQL Database: sqldb-myagents-prod
  2. Click "Query editor" in left menu
  3. Authenticate with your credentials
  4. Copy/paste the commands above
  5. Click "Run"

Press Enter to continue once completed... █
```

👉 **Go to Azure Portal and run the SQL commands, then press Enter**

```
✓ SQL configuration acknowledged

═══════════════════════════════════════════════════════════════
STEP 4/5: Deploying Application Code
═══════════════════════════════════════════════════════════════
📤 Deploying application code to App Service...
  ✓ Web app detected: webapp-myagents-prod
  ✓ Creating deployment package...
  ✓ Package created: app_20240115120345.zip (2.4 MB)
  ✓ Uploading to Azure...
    [████████████████████████████████] 100% (2.4 MB / 2.4 MB)
  ✓ Installing dependencies from requirements.txt...
    This may take 2-3 minutes...
  ✓ Application deployed successfully
  ✓ Restarting web app...
  ✓ Cleanup: Removed temporary ZIP file

═══════════════════════════════════════════════════════════════
STEP 5/5: Verifying Deployment
═══════════════════════════════════════════════════════════════
🔍 Performing deployment health check...
  ⏳ Waiting for application to start (may take 30 seconds)...
  ✓ Application is responding
  ✓ Health check passed: HTTP 200 OK

╔══════════════════════════════════════════════════════════════╗
║                   DEPLOYMENT COMPLETE! 🎉                    ║
╚══════════════════════════════════════════════════════════════╝

⏱️ Total deployment time: 12 minutes 34 seconds

🌐 Application URL:
   https://webapp-myagents-prod.azurewebsites.net

📊 Deployed Resources:
   ┌─────────────────────────────────────────────────────────┐
   │ Resource Type     │ Resource Name                       │
   ├─────────────────────────────────────────────────────────┤
   │ Web App           │ webapp-myagents-prod                │
   │ SQL Server        │ sql-myagents-prod                   │
   │ SQL Database      │ sqldb-myagents-prod                 │
   │ Key Vault         │ kv-myagents-prod-abc123             │
   │ App Insights      │ appi-myagents-prod                  │
   └─────────────────────────────────────────────────────────┘

📖 Next Steps:
   1. 🌐 Open your application:
      Start-Process https://webapp-myagents-prod.azurewebsites.net

   2. 📚 View API documentation:
      Start-Process https://webapp-myagents-prod.azurewebsites.net/docs

   3. 📊 Test endpoints:
      Start-Process https://webapp-myagents-prod.azurewebsites.net/api/health

   4. 📝 View application logs:
      az webapp log tail --name webapp-myagents-prod --resource-group rg-myagents-prod

   5. 📈 Monitor in Azure Portal:
      Start-Process https://portal.azure.com/#resource/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/rg-myagents-prod/overview

📚 Documentation:
   • Main README: ..\README.md
   • Scripts Guide: .\README.md
   • Quick Start: ..\docs\QUICK_START.md
   • Troubleshooting: ..\docs\TROUBLESHOOTING.md

🎊 Your Azure Agent Framework application is now live!
```

---

## ✅ That's It!

You just deployed:
- ✅ Azure App Service with Python 3.11
- ✅ Azure SQL Database
- ✅ Azure Key Vault
- ✅ Application Insights
- ✅ Your application code
- ✅ All dependencies installed
- ✅ Health checks verified

**All with ONE command!** 🎉

---

## 🔄 Need to Update Your Code?

Already deployed and just want to push code changes?

```powershell
# Quick redeploy (3-5 minutes)
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -SkipInfrastructure
```

**Output:**
```
╔══════════════════════════════════════════════════════════════╗
║    AZURE AGENT FRAMEWORK - CODE UPDATE                      ║
╚══════════════════════════════════════════════════════════════╝

⏩ Skipping infrastructure deployment

═══════════════════════════════════════════════════════════════
STEP 1/2: Preparing Application Code
═══════════════════════════════════════════════════════════════
📦 Preparing updated application code...
  ✓ Package prepared (153 files, 2.4 MB)

═══════════════════════════════════════════════════════════════
STEP 2/2: Deploying Application Code
═══════════════════════════════════════════════════════════════
📤 Deploying to App Service...
  [████████████████████████████████] 100%
  ✓ Code deployed successfully

╔══════════════════════════════════════════════════════════════╗
║                   CODE UPDATE COMPLETE! 🎉                   ║
╚══════════════════════════════════════════════════════════════╝

⏱️ Update time: 3 minutes 42 seconds
🌐 Application URL: https://webapp-myagents-prod.azurewebsites.net
```

---

## 🎨 Color Guide

The scripts use colored output for clarity:

- 🟢 **Green** - Success messages
- 🔵 **Cyan** - Informational messages  
- 🟡 **Yellow** - Warnings or actions needed
- 🔴 **Red** - Errors
- ⚪ **White** - Regular text

---

## 🚦 Common Scenarios

### Scenario 1: First-Time Production Deployment

```powershell
# Deploy to production
.\deploy-complete.ps1 -ResourceGroupName "rg-agents-prod" -Location "eastus2"

# Time: 12-15 minutes
# Result: Fully configured production environment
```

---

### Scenario 2: Deploy to Multiple Environments

```powershell
# Development
.\deploy-complete.ps1 -ResourceGroupName "rg-agents-dev" -ParametersFile "..\bicep\dev.bicepparam"

# Staging
.\deploy-complete.ps1 -ResourceGroupName "rg-agents-staging" -ParametersFile "..\bicep\staging.bicepparam"

# Production
.\deploy-complete.ps1 -ResourceGroupName "rg-agents-prod" -ParametersFile "..\bicep\prod.bicepparam"
```

---

### Scenario 3: CI/CD Pipeline Deployment

```powershell
# Automated deployment (no prompts)
.\deploy-complete.ps1 `
  -ResourceGroupName "rg-agents-prod" `
  -AutoConfirmSql `
  -ErrorAction Stop

# Perfect for Azure DevOps, GitHub Actions, etc.
```

---

### Scenario 4: Troubleshooting Deployment

```powershell
# Deploy with verbose output
.\deploy-complete.ps1 -ResourceGroupName "rg-test" -Verbose

# Check logs if issues
az webapp log tail --name webapp-test --resource-group rg-test

# View deployment history
az deployment group list --resource-group rg-test --output table
```

---

## ⚠️ Troubleshooting Quick Reference

### Issue: "Azure CLI not found"

**Solution:**
```powershell
# Install Azure CLI
winget install Microsoft.AzureCLI

# Or download from: https://aka.ms/installazurecli
```

---

### Issue: "Not logged in to Azure"

**Solution:**
```powershell
az login
az account show  # Verify correct subscription
```

---

### Issue: "Parameters file not found"

**Solution:**
```powershell
# Copy template and configure
Copy-Item bicep\main.bicepparam.template bicep\main.bicepparam
code bicep\main.bicepparam
```

---

### Issue: "Source directory not detected"

**Solution:**
```powershell
# Specify source directory explicitly
.\deploy-complete.ps1 `
  -ResourceGroupName "rg-name" `
  -SourceAppDir "C:\path\to\your\app"
```

---

### Issue: "Deployment failed"

**Solution:**
```powershell
# Check detailed logs
az deployment group show `
  --resource-group rg-name `
  --name main `
  --query properties.error

# View web app logs
az webapp log tail --name webapp-name --resource-group rg-name
```

---

## 📊 Deployment Timeline Breakdown

| Phase | Time | What's Happening |
|-------|------|------------------|
| Pre-flight checks | 10s | Validating CLI, login, files |
| Prepare app code | 30s | Copying files, creating config |
| Deploy infrastructure | 8min | Creating Azure resources |
| SQL configuration | 2min | Manual step in Portal |
| Deploy app code | 3min | ZIP upload + pip install |
| Health check | 30s | Verifying deployment |
| **Total** | **~15min** | Complete deployment |

---

## 🎯 Success Checklist

After deployment, verify:

- ✅ Application URL loads
- ✅ API documentation accessible at /docs
- ✅ Health endpoint returns 200 OK
- ✅ Can access Azure Portal resources
- ✅ Application Insights receiving telemetry
- ✅ SQL database connection working

---

## 📚 Additional Resources

- 📖 [Full README](../README.md)
- 📖 [Scripts Documentation](./README.md)
- 📖 [Deployment Comparison](../docs/DEPLOYMENT_COMPARISON.md)
- 📖 [Azure Services Guide](../docs/AZURE_SERVICES_DEPLOYMENT.md)
- 📖 [Parameters Reference](../docs/PARAMETERS.md)
- 📖 [Quick Start Guide](../docs/QUICK_START.md)

---

## 🆘 Need Help?

1. **Check the output** - Scripts provide detailed error messages
2. **Review logs** - `az webapp log tail --name <app> --resource-group <rg>`
3. **Verify parameters** - Ensure all values are correct in bicepparam file
4. **Check Azure Portal** - View resource status and errors
5. **Read documentation** - Comprehensive guides available

---

## 🎓 Pro Tips

💡 **Tip 1:** Use meaningful resource group names
```powershell
# Good
.\deploy-complete.ps1 -ResourceGroupName "rg-agents-prod-eastus2"

# Better for tracking costs and organization
```

💡 **Tip 2:** Create separate parameter files for each environment
```powershell
bicep/
  ├── dev.bicepparam      # Development settings
  ├── staging.bicepparam  # Staging settings
  └── prod.bicepparam     # Production settings
```

💡 **Tip 3:** Use AutoConfirmSql for CI/CD
```powershell
# No manual interaction needed
.\deploy-complete.ps1 -ResourceGroupName "rg-agents" -AutoConfirmSql
```

💡 **Tip 4:** Skip infrastructure to save time on code updates
```powershell
# Just redeploy code (3 minutes vs 15 minutes)
.\deploy-complete.ps1 -ResourceGroupName "rg-agents" -SkipInfrastructure
```

💡 **Tip 5:** Clean up test deployments
```powershell
# Delete entire resource group when done testing
az group delete --name "rg-test-deployment" --yes --no-wait
```

---

## 🎉 Congratulations!

You've mastered turnkey deployment! 🚀

**From 15+ manual steps to 1 command.**  
**From 30+ minutes to 15 minutes.**  
**From error-prone to automated.**

Now go build amazing AI agents! 🤖✨

---

**Made with ❤️ for Azure Agent Framework**
