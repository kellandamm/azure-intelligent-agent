# Deployment Scripts

This folder contains PowerShell scripts for deploying the Azure Agent Framework application.

## 📜 Available Scripts

### 1. **deploy-complete.ps1** ⭐ (RECOMMENDED - Turnkey Deployment)

**The master script that does everything in one command.**

```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"
```

**What it does:**
1. ✅ Validates prerequisites (Azure CLI, login, parameters file)
2. ✅ Prepares application code from source
3. ✅ Deploys Azure infrastructure (SQL, App Service, Key Vault, etc.)
4. ✅ Configures SQL database access
5. ✅ Deploys application code to App Service
6. ✅ Verifies deployment health

**Parameters:**
- `ResourceGroupName` (required): Azure resource group name
- `Location` (optional): Azure region (default: eastus2)
- `SourceAppDir` (optional): Source code location (auto-detected)
- `AutoConfirmSql` (optional): Skip SQL config prompt
- `SkipPreparation` (optional): Skip app preparation
- `SkipInfrastructure` (optional): Only deploy code
- `SkipAppCode` (optional): Only deploy infrastructure

**Example - Complete deployment:**
```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-agents-prod" -Location "eastus2"
```

**Example - Quick redeploy of code only:**
```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-agents-prod" -SkipInfrastructure
```

---

### 2. **prepare-app.ps1** (Application Preparation)

Prepares application code for deployment by copying essential files and excluding development artifacts.

```powershell
.\scripts\prepare-app.ps1
```

**What it does:**
- Copies application files from source directory
- Excludes unnecessary files (venv, cache, tests, etc.)
- Creates deployment configuration (.deployment, startup.sh)
- Validates the deployment package

**Parameters:**
- `SourceDir` (optional): Source application directory
- `DestinationDir` (optional): Destination directory (default: ./app)
- `Force` (optional): Overwrite existing files

**Files copied:**
- Root files: main.py, config.py, requirements.txt, etc.
- Folders: app/, agent_framework/, utils/, static/, demos/
- Excludes: venv/, __pycache__/, tests/, .env

---

### 3. **deploy.ps1** (Infrastructure & Code Deployment)

Deploys infrastructure and/or application code.

```powershell
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod"
```

**What it does:**
1. Creates/validates resource group
2. Deploys Bicep infrastructure templates
3. Prompts for SQL configuration
4. Deploys application code (if app folder exists)

**Parameters:**
- `ResourceGroupName` (required): Azure resource group name
- `Location` (optional): Azure region (default: eastus2)
- `ParametersFile` (optional): Bicep parameters file
- `SkipInfrastructure` (optional): Only deploy code
- `SkipAppCode` (optional): Only deploy infrastructure

---

## 🚀 Quick Start

### For First-Time Deployment (Turnkey):

```powershell
# 1. Update parameters file
code ..\bicep\main.bicepparam

# 2. Run complete deployment
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"

# That's it! ☕ Grab coffee while it deploys (10-15 minutes)
```

### For Code-Only Updates:

```powershell
# Redeploy just the application code
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -SkipInfrastructure
```

### For Manual Step-by-Step:

```powershell
# 1. Prepare application code
.\scripts\prepare-app.ps1

# 2. Deploy infrastructure
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod" -SkipAppCode

# 3. Configure SQL (follow prompts)

# 4. Deploy application code
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod" -SkipInfrastructure
```

---

## 📋 Prerequisites

Before running any deployment script:

1. **Azure CLI** installed and updated
   ```powershell
   az --version
   az upgrade
   ```

2. **Logged in to Azure**
   ```powershell
   az login
   az account show
   ```

3. **Parameters file configured**
   - Create `bicep/main.bicepparam` from the sample in [docs/QUICK_START.md](../docs/QUICK_START.md)
   - Update all `<REPLACE_WITH_*>` placeholders

4. **Application code available** (for first deployment)
   - Source code in parent directory: `<your-repo-path>`
   - Contains: main.py, config.py, requirements.txt, etc.

---

## 🔧 Script Details

### Directory Structure Created:

```
azure-deployment-template/
├── app/                          # Prepared application code (created by scripts)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .deployment
│   ├── startup.sh
│   ├── app/
│   ├── agent_framework/
│   ├── utils/
│   └── static/
├── bicep/
│   ├── main.bicep
│   └── main.bicepparam          # You must configure this
└── scripts/
    ├── deploy-complete.ps1      # ⭐ Use this
    ├── prepare-app.ps1
    └── deploy.ps1
```

### What Gets Deployed to Azure:

1. **Infrastructure** (via Bicep):
   - Resource Group
   - App Service Plan + Web App (Linux, Python 3.11)
   - Azure SQL Server + Database
   - Key Vault (optional)
   - Application Insights (optional)
   - Container Registry (optional)

2. **Application Code** (via ZIP deployment):
   - Python application files
   - Dependencies installed from requirements.txt
   - Environment variables configured
   - Startup command: `bash startup.sh`

---

## ⚠️ Common Issues

### Issue: "Parameters file not found"
**Solution:** Copy and configure the parameters file:
```powershell
Copy-Item ..\bicep\main.bicepparam ..\bicep\main.parameters.bicepparam
code ..\bicep\main.parameters.bicepparam
```

### Issue: "Source application directory not found"
**Solution:** Specify the source directory:
```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents" -SourceAppDir "C:\path\to\your\app"
```

### Issue: "Azure CLI not found"
**Solution:** Install Azure CLI:
- Windows: `winget install Microsoft.AzureCLI`
- Or download from: https://aka.ms/installazurecli

### Issue: "Not logged in to Azure"
**Solution:**
```powershell
az login
az account set --subscription "<subscription-id>"
```

### Issue: "Web app deployment failed"
**Solution:** Check logs:
```powershell
# View deployment logs
az webapp log tail --name <web-app-name> --resource-group <rg-name>

# View all logs
az webapp log download --name <web-app-name> --resource-group <rg-name>
```

---

## 📊 Deployment Timeline

**Complete first-time deployment (deploy-complete.ps1):**

| Step | Time | Description |
|------|------|-------------|
| Pre-flight checks | ~10s | Validate CLI, login, files |
| Prepare app code | ~30s | Copy files, create config |
| Deploy infrastructure | ~8min | Bicep deployment |
| Configure SQL | manual | Grant managed identity access |
| Deploy app code | ~3min | ZIP upload + dependency install |
| Verify deployment | ~30s | Health checks |
| **Smoke tests** | ~10s | **Optional: Comprehensive validation** |

**🧪 Post-Deployment Smoke Tests:**

After deployment completes, you'll be prompted to run smoke tests:
```powershell
🧪 Run smoke tests now? (Recommended)
Enter 'y' to run smoke tests, any other key to skip: y
```

Or run manually:
```powershell
# Auto-discover URL from Azure
.\tests\smoke-test.ps1 -ResourceGroupName "rg-myagents-prod"

# Test specific URL
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net"
```

**What smoke tests verify:**
- ✅ Health endpoints and application status
- ✅ Authentication system
- ✅ Chat and agent APIs
- ✅ Sales and Analytics dashboards
- ✅ Database connectivity
- ✅ Response times and performance

📖 **See [Smoke Test Guide](../tests/README.md) for full documentation**
| **Total** | **~12-15 min** | Including manual SQL step |

**Code-only redeployment:**
- ~3-5 minutes (just ZIP upload + restart)

---

## 🎯 Best Practices

1. **Use deploy-complete.ps1 for turnkey deployment**
   - It handles everything automatically
   - Includes validation and error handling
   - Shows progress and summary

2. **Keep parameters file secure**
   - Never commit secrets to source control
   - Use Azure Key Vault for production
   - Consider using managed identities

3. **Test in dev environment first**
   ```powershell
   .\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-dev"
   ```

4. **Monitor deployments**
   ```powershell
   # Watch logs in real-time
   az webapp log tail --name <app-name> --resource-group <rg-name>
   
   # Check deployment status
   az deployment group list --resource-group <rg-name>
   ```

5. **Use skip flags for efficiency**
   ```powershell
   # Just update application code
   .\scripts\deploy-complete.ps1 -ResourceGroupName "rg" -SkipInfrastructure -AutoConfirmSql
   ```

---

## 📚 Additional Resources

- Main README: [`../README.md`](../README.md)
- Quick Start Guide: [`../docs/QUICK_START.md`](../docs/QUICK_START.md)
- Configuration Reference: [`../CONFIGURATION.md`](../CONFIGURATION.md)
- Deployment Guide: [`../docs/QUICK_START.md`](../docs/QUICK_START.md)

---

## 🆘 Need Help?

1. Check script output for detailed error messages
2. Review the troubleshooting section in main README
3. Check Azure Portal for resource status
4. View application logs: `az webapp log tail --name <app> --resource-group <rg>`
5. Verify parameters file is correctly configured

---

**Made with ❤️ for Azure Agent Framework**
