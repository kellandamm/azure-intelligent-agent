# ⚡ Azure Intelligent Agent Starter - Quick Reference

**Print or bookmark this page for quick deployment commands!**

---

## 🚀 First-Time Deployment

> **Resource names are auto-generated** — `appName` and `sqlServerName` are derived from your
> resource group ID. You only need to fill in **external service credentials** in `bicep/main.bicepparam`.

### Using azd (Simplest):

```bash
# 1. Edit bicep/main.bicepparam and fill in your credentials
#    (only OpenAI, Fabric, Power BI, SQL AD admin fields are required)
# 2. Deploy:
azd up
```

### Using PowerShell:

```powershell
# Edit bicep/main.bicepparam with your external service credentials
code bicep\main.bicepparam
cd scripts
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"
```

---

## 🔄 Update Code Only

### Using azd:

```bash
azd deploy
```

### Using PowerShell:

```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -SkipInfrastructure
```

---

## 🌍 Environment Management

### Using azd:

```bash
# Create environments
azd env new dev
azd env new staging
azd env new prod

# Switch environments
azd env select dev

# Override auto-generated app name (optional)
azd env set AZURE_APP_NAME "myagents"

# SQL AD admin credentials (if using Azure AD auth)
azd env set AZURE_SQL_ADMINISTRATOR_LOGIN "sqladmin"
azd env set AZURE_SQL_ADMINISTRATOR_PASSWORD "SecurePass123!"

# View variables
azd env get-values
```

### Using PowerShell:

```powershell
# Create parameter files
bicep/dev.bicepparam
bicep/staging.bicepparam
bicep/prod.bicepparam

# Deploy to specific environment
.\deploy-complete.ps1 -ResourceGroupName "rg-dev" -ParametersFile "..\bicep\dev.bicepparam"
```

---

## 📊 Monitoring

### Using azd:

```bash
# View status
azd show

# View logs
azd monitor --logs

# Live logs
azd monitor --logs --follow

# Open dashboard
azd monitor --overview

# Open app in browser
azd browse
```

### Using PowerShell:

```bash
# View logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Open portal
Start-Process "https://portal.azure.com"
```

---

## 🗑️ Cleanup

### Using azd:

```bash
azd down
```

### Using PowerShell:

```bash
az group delete --name "rg-myagents-dev" --yes --no-wait
```

---

## 🆘 Troubleshooting

### Check Prerequisites:

```bash
# Check azd
azd version

# Check Azure CLI
az --version

# Check login
az account show
```

### Common Fixes:

```bash
# Re-login
azd auth login
az login

# View deployment errors
azd show
az deployment group list --resource-group <rg-name>

# View app logs
az webapp log tail --name <app-name> --resource-group <rg-name>
```

### Policy Violation — SQL Server Blocked by MCAPS

If `azd provision` fails with **"Resource was disallowed by policy"** on the SQL server:
- This is the MCAPS deny policy blocking `publicNetworkAccess = Enabled`
- Ensure `enableVnetIntegration = true` in `bicep/main.bicepparam` (the default)
- That parameter deploys the VNet + private endpoint and sets `publicNetworkAccess = Disabled`

### SQL Connection Failing After Deployment

If the App Service cannot reach SQL:
1. Verify VNet integration is active: Portal → App Service → Networking → VNet Integration
2. Confirm the private endpoint is provisioned: Portal → SQL Server → Private endpoint connections
3. Check private DNS zone `privatelink.database.windows.net` has a VNet link to your VNet

---

## 📚 Documentation Links

| Topic | Link |
|-------|------|
| **azd Guide** | [docs/AZD_DEPLOYMENT_GUIDE.md](docs/AZD_DEPLOYMENT_GUIDE.md) |
| **PowerShell Guide** | [scripts/README.md](scripts/README.md) |
| **Visual Guide** | [docs/TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md](docs/TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md) |
| **Comparison** | [docs/DEPLOYMENT_METHODS_COMPARISON.md](docs/DEPLOYMENT_METHODS_COMPARISON.md) |
| **Parameters** | [docs/PARAMETERS.md](docs/PARAMETERS.md) |
| **Azure Services** | [docs/AZURE_SERVICES_DEPLOYMENT.md](docs/AZURE_SERVICES_DEPLOYMENT.md) |

---

## 🎯 Most Common Commands

```bash
# Deploy everything (azd)
azd up

# Deploy everything (PowerShell)
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"

# Update code only (azd)
azd deploy

# Update code only (PowerShell)
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -SkipInfrastructure

# View status (azd)
azd show

# View logs (azd)
azd monitor --logs --follow

# Delete everything (azd)
azd down
```

---

## ⚙️ Required Environment Variables (azd)

```bash
AZURE_RESOURCE_GROUP         # Required: Target resource group
# appName, sqlServerName are AUTO-GENERATED from the resource group ID — no manual setting needed
AZURE_APP_NAME               # Optional override: custom application name prefix
AZURE_LOCATION               # Optional: Azure region (default: eastus2)
AZURE_ENVIRONMENT_NAME       # Optional: Environment tag (default: dev)
```

> SQL uses Azure AD authentication with the App Service managed identity.
> No SQL username/password environment variables are required.
## 📝 Required Parameters (PowerShell)

Edit `bicep/main.bicepparam` — only external service credentials need to be set:

```bicep
// appName, sqlServerName are AUTO-GENERATED — no need to set them
param azureOpenAIEndpoint = 'https://...'         // Required
param azureOpenAIApiKey   = '<key>'               // Required
param projectEndpoint     = 'https://...'         // Required
// Fabric, Power BI params ...
// Azure AD SQL admin (required for sqlUseAzureAuth = true):
param sqlAzureAdAdminLogin = 'admin@yourorg.com'  // Required
param sqlAzureAdAdminSid   = '<object-id>'         // Required
```

---

## 🚦 Deployment Timeline

| Phase | Time |
|-------|------|
| **First deployment** | 15-20 minutes (includes VNet + private endpoint provisioning) |
| **Code update** | 3-5 minutes |
| **Infrastructure only** | 10-15 minutes |

---

## 💡 Pro Tips

1. **Use azd for simplicity** - One command does everything
2. **Use PowerShell for control** - See every step
3. **Create multiple environments** - Test before production
4. **VNet integration is on by default** - Required for MCAPS compliance; SQL has no public internet access
5. **Monitor with Application Insights** - Included by default
6. **Use Key Vault for secrets** - Production best practice

---

**🎉 You're ready to deploy!**

```bash
azd up  # Simplest way!
```

or

```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"  # Maximum control!
```

---

**Made with ❤️ for Azure Agent Framework**
