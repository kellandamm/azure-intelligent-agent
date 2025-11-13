# ⚡ Azure Intelligent Agent Starter - Quick Reference

**Print or bookmark this page for quick deployment commands!**

---

## 🚀 First-Time Deployment

### Using azd (Simplest):

```bash
azd up
```

### Using PowerShell:

```powershell
Copy-Item bicep\main.bicepparam.template bicep\main.bicepparam
code bicep\main.bicepparam  # Edit parameters
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

# Set variables
azd env set AZURE_APP_NAME "myagents"
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
AZURE_APP_NAME                    # Required: Application name
AZURE_SQL_ADMINISTRATOR_LOGIN     # Required: SQL admin username
AZURE_SQL_ADMINISTRATOR_PASSWORD  # Required: SQL admin password
AZURE_LOCATION                    # Optional: Azure region (default: eastus2)
AZURE_ENVIRONMENT_NAME            # Optional: Environment (default: dev)
```

---

## 📝 Required Parameters (PowerShell)

Edit `bicep/main.bicepparam`:

```bicep
param appName = 'myagents'                              // Required
param sqlAdministratorLogin = 'sqladmin'                // Required
param sqlAdministratorPassword = 'SecurePass123!'       // Required
param azureOpenAIEndpoint = 'https://...'              // Required
param azureOpenAIDeployment = 'gpt-4o'                 // Required
param projectEndpoint = 'https://...'                  // Required
```

---

## 🚦 Deployment Timeline

| Phase | Time |
|-------|------|
| **First deployment** | 12-15 minutes |
| **Code update** | 3-5 minutes |
| **Infrastructure only** | 8-10 minutes |

---

## 💡 Pro Tips

1. **Use azd for simplicity** - One command does everything
2. **Use PowerShell for control** - See every step
3. **Create multiple environments** - Test before production
4. **Always configure SQL manually** - Required security step
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
