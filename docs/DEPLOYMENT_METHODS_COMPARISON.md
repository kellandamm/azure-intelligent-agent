# 🔄 Deployment Methods Comparison

This guide helps you choose between **Azure Developer CLI (azd)** and **PowerShell scripts** for deploying your Azure Agent Framework application.

---

## 🎯 Quick Decision Matrix

| You should use... | If you... |
|------------------|-----------|
| **azd** ⭐ | Want the simplest experience with `azd up` |
| **azd** ⭐ | Need to manage multiple environments (dev/staging/prod) |
| **azd** ⭐ | Prefer industry-standard Azure developer workflow |
| **azd** ⭐ | Are comfortable learning new CLI tools |
| **azd** ⭐ | Want built-in monitoring integration |
| **PowerShell** | Need maximum customization and control |
| **PowerShell** | Already familiar with PowerShell scripting |
| **PowerShell** | Want detailed progress output at each step |
| **PowerShell** | Prefer seeing exactly what's happening |
| **PowerShell** | Have existing PowerShell workflows to integrate with |

**TL;DR:** Use `azd` for simplicity, use PowerShell scripts for control. Both are excellent choices!

---

## 📊 Detailed Comparison

### Deployment Experience

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **Initial command** | `azd up` | `.\deploy-complete.ps1 -ResourceGroupName "rg-name"` |
| **Lines of code** | 1 command | 1 command |
| **Time to deploy** | ~15 min | ~15 min |
| **Configuration** | Interactive prompts or env vars | Parameter file + command args |
| **Progress visibility** | Standard azd output | Detailed colored output with steps |
| **Error messages** | azd standard errors | Custom detailed error messages |

### Environment Management

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **Create environment** | `azd env new dev` | Create new parameters file |
| **Switch environment** | `azd env select dev` | Use different `-ParametersFile` |
| **Set variables** | `azd env set KEY value` | Edit parameters file manually |
| **View variables** | `azd env get-values` | Open parameters file |
| **Environment isolation** | Automatic (`.azure/` folder) | Manual (separate param files) |

### Deployment Operations

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **Full deployment** | `azd up` | `.\deploy-complete.ps1 -ResourceGroupName "rg"` |
| **Infrastructure only** | `azd provision` | `.\deploy.ps1 -ResourceGroupName "rg" -SkipAppCode` |
| **Code only** | `azd deploy` | `.\deploy-complete.ps1 -ResourceGroupName "rg" -SkipInfrastructure` |
| **Partial deployment** | Limited | Full skip flag control |

### Monitoring & Debugging

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **View logs** | `azd monitor --logs` | `az webapp log tail` (manual) |
| **Live logs** | `azd monitor --logs --follow` | `az webapp log tail` (manual) |
| **Dashboard** | `azd monitor --overview` | Open Azure Portal manually |
| **Status** | `azd show` | Check Azure Portal |
| **Built-in monitoring** | ✅ Yes | ❌ Manual |

### CI/CD Integration

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **GitHub Actions** | Native `azure/azd-action` | Custom script step |
| **Azure DevOps** | Native task | PowerShell task |
| **Complexity** | Simple | Simple |
| **Flexibility** | Standard workflow | Full customization |

### Customization

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **Hooks** | `azure.yaml` hooks (limited) | Full script editing |
| **Custom logic** | Shell commands in hooks | Any PowerShell code |
| **Validation** | Basic | Comprehensive built-in |
| **Error handling** | Standard azd | Custom try/catch blocks |
| **Output formatting** | Standard azd | Custom colors/formatting |

### Learning Curve

| Aspect | azd | PowerShell Scripts |
|--------|-----|-------------------|
| **Time to learn** | 30 minutes | 1 hour |
| **Prerequisites** | Learn azd commands | Know PowerShell |
| **Documentation** | Microsoft Learn + azd docs | Inline comments + READMEs |
| **Complexity** | Low | Medium |

---

## 🚀 Side-by-Side Examples

### First-Time Deployment

#### Using azd:

```bash
# 1. Navigate to template
cd c:\code\azure-deployment-template

# 2. Deploy everything
azd up

# Follow interactive prompts for:
# - Environment name (e.g., "dev")
# - Subscription
# - Location (e.g., "eastus2")
# - Set required variables:
azd env set AZURE_APP_NAME "myagents"
azd env set AZURE_SQL_ADMINISTRATOR_LOGIN "sqladmin"
azd env set AZURE_SQL_ADMINISTRATOR_PASSWORD "SecurePass123!"

# Total: 2 commands + prompts = ~15 minutes
```

**Output:**
```
Provisioning Azure resources (azd provision)
Provisioning Azure resources can take some time

  You can view detailed progress in the Azure Portal:
  https://portal.azure.com

  (✓) Done: Resource group: rg-myagents-dev
  (✓) Done: App Service: webapp-myagents-dev
  (✓) Done: SQL Server: sql-myagents-dev
  ...

SUCCESS: Your application was provisioned in Azure in 8 minutes 32 seconds.
You can view the resources created under the resource group rg-myagents-dev in Azure Portal.

Deploying services (azd deploy)

  (✓) Done: Deploying service web
  - Endpoint: https://webapp-myagents-dev.azurewebsites.net

SUCCESS: Your application was deployed to Azure in 3 minutes 12 seconds.
```

---

#### Using PowerShell:

```powershell
# 1. Navigate to template
cd c:\code\azure-deployment-template

# 2. Configure parameters (one-time)
Copy-Item bicep\main.bicepparam.template bicep\main.bicepparam
code bicep\main.bicepparam
# Edit: appName, sqlAdministratorLogin, sqlAdministratorPassword, etc.

# 3. Deploy
cd scripts
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-dev"

# Total: 3 steps = ~15 minutes
```

**Output:**
```
╔══════════════════════════════════════════════════════════════╗
║    AZURE AGENT FRAMEWORK - COMPLETE DEPLOYMENT              ║
╚══════════════════════════════════════════════════════════════╝

🔍 Checking prerequisites...
  ✓ Azure CLI version 2.57.0 detected
  ✓ Logged in as user@domain.com
  ✓ Parameters file found
  ✓ Source application directory detected

═══════════════════════════════════════════════════════════════
STEP 1/5: Preparing Application Code
═══════════════════════════════════════════════════════════════
📦 Preparing application code...
  ✓ Copying 8 root files
  ✓ Copying 6 folders
  ✓ Package validated successfully

═══════════════════════════════════════════════════════════════
STEP 2/5: Deploying Infrastructure
═══════════════════════════════════════════════════════════════
🏗️ Deploying Azure infrastructure...
  [... detailed progress ...]

╔══════════════════════════════════════════════════════════════╗
║                   DEPLOYMENT COMPLETE! 🎉                    ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Code-Only Update

#### Using azd:

```bash
# Make code changes in app/ folder

# Deploy updated code
azd deploy

# Time: ~3 minutes
```

---

#### Using PowerShell:

```powershell
# Make code changes

# Deploy updated code
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-dev" -SkipInfrastructure

# Time: ~3-5 minutes
```

---

### Multiple Environments

#### Using azd:

```bash
# Create and deploy dev environment
azd env new dev
azd env set AZURE_APP_NAME "myagents"
azd up

# Create and deploy staging environment
azd env new staging
azd env set AZURE_APP_NAME "myagents"
azd up

# Create and deploy prod environment
azd env new prod
azd env set AZURE_APP_NAME "myagents"
azd up

# Switch between environments
azd env select dev    # Work with dev
azd env select prod   # Switch to prod
```

**Benefits:**
- ✅ Isolated environment configurations
- ✅ Easy switching with `azd env select`
- ✅ Consistent deployment workflow

---

#### Using PowerShell:

```powershell
# Create separate parameter files
bicep/
  ├── dev.bicepparam      # Development settings
  ├── staging.bicepparam  # Staging settings
  └── prod.bicepparam     # Production settings

# Deploy to each environment
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-dev" -ParametersFile "..\bicep\dev.bicepparam"
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-staging" -ParametersFile "..\bicep\staging.bicepparam"
.\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -ParametersFile "..\bicep\prod.bicepparam"
```

**Benefits:**
- ✅ Full control over each environment
- ✅ Version control parameter files
- ✅ Clear separation of configurations

---

### Monitoring

#### Using azd:

```bash
# View application status
azd show

# View logs
azd monitor --logs

# Live log stream
azd monitor --logs --follow

# Open monitoring dashboard
azd monitor --overview
```

---

#### Using PowerShell:

```powershell
# View logs (manual Azure CLI)
az webapp log tail --name webapp-myagents-dev --resource-group rg-myagents-dev

# Open Azure Portal (manual)
Start-Process "https://portal.azure.com"
```

**Note:** PowerShell scripts focus on deployment; monitoring is manual via Azure CLI/Portal.

---

### Cleanup

#### Using azd:

```bash
# Delete all resources
azd down

# Confirm deletion when prompted
# Time: ~5 minutes
```

---

#### Using PowerShell:

```powershell
# Delete resource group (includes all resources)
az group delete --name "rg-myagents-dev" --yes --no-wait

# Time: ~5 minutes
```

---

## 🎓 Which Should You Choose?

### Choose azd if:

✅ You want the **absolute simplest** deployment experience  
✅ You need to manage **multiple environments** frequently  
✅ You want **built-in monitoring** integration  
✅ You prefer **industry-standard** Azure workflows  
✅ You're **comfortable learning** a new CLI tool  
✅ You want **cross-platform** support (Windows/Mac/Linux)  
✅ You like the idea of `azd up` just working  

**Best for:** Developers who want simplicity and standard workflows

---

### Choose PowerShell Scripts if:

✅ You need **maximum control** and customization  
✅ You're already **familiar with PowerShell**  
✅ You want **detailed progress** output at each step  
✅ You need to **integrate** with existing PowerShell workflows  
✅ You want to **see exactly** what's happening  
✅ You need **custom validation** logic  
✅ You prefer **explicit control** over automation  

**Best for:** DevOps engineers who want full control and visibility

---

## 💡 Can I Use Both?

**Yes!** You can use both methods interchangeably:

```bash
# Use azd for quick deployments
azd up

# Use PowerShell when you need control
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-name" -SkipInfrastructure
```

Both methods:
- ✅ Use the same Bicep templates
- ✅ Deploy the same infrastructure
- ✅ Create identical Azure resources
- ✅ Support all features

**Recommendation:** Learn both, use what feels natural for each task!

---

## 📚 Getting Started Guides

### For azd:
📖 **[Complete azd Deployment Guide](AZD_DEPLOYMENT_GUIDE.md)**

Quick start:
```bash
azd up
```

---

### For PowerShell:
📖 **[PowerShell Scripts Guide](../scripts/README.md)**  
📖 **[Visual Deployment Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md)**

Quick start:
```powershell
.\scripts\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"
```

---

## 🎯 Summary Table

| Criteria | Winner | Reason |
|----------|--------|--------|
| **Simplicity** | azd ⭐ | One command: `azd up` |
| **Environment Management** | azd ⭐ | Built-in env switching |
| **Customization** | PowerShell ⭐ | Full script control |
| **Progress Visibility** | PowerShell ⭐ | Detailed step-by-step output |
| **Learning Curve** | azd ⭐ | Minimal learning required |
| **Cross-Platform** | azd ⭐ | Native Windows/Mac/Linux |
| **Monitoring Integration** | azd ⭐ | Built-in `azd monitor` |
| **CI/CD Integration** | Tie 🤝 | Both excellent |
| **Error Messages** | PowerShell ⭐ | More detailed context |
| **Community Standard** | azd ⭐ | Microsoft-recommended approach |

---

## 🎉 Conclusion

Both deployment methods are **excellent choices**:

- **azd** is the **simplest and most modern** approach
- **PowerShell scripts** provide **maximum control and visibility**

**Our recommendation:**
1. **Start with azd** - See how easy it is
2. **Try PowerShell scripts** - When you need more control
3. **Use both** - Pick the right tool for each task

You can't go wrong with either choice! 🚀

---

**Made with ❤️ for Azure Agent Framework**  
*Two great ways to deploy to Azure* 🎯
