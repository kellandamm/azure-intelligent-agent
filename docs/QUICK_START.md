# Quick Deployment Guide

## 🚀 Deploy in 15 Minutes

### Prerequisites Checklist
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Azure CLI installed (`az --version`)
- [ ] Azure Developer CLI (azd) installed (`azd version`)
- [ ] Logged in to Azure (`az login`)
- [ ] Azure OpenAI resource with GPT-4 model deployed
- [ ] Azure AI Foundry project created
- [ ] Microsoft Fabric workspace with agents
- [ ] Power BI service principal configured

---

## Step 1: Initialize and Configure (5 minutes)

### Option A: Using azd (Recommended)

```bash
# Initialize your environment
azd init
# When prompted, enter an environment name (e.g. prod, dev)

# Set location
azd env set AZURE_LOCATION eastus2
```

Then open `bicep/main.bicepparam` and fill in **only your external service credentials** (`appName` and `sqlServerName` are auto-generated and do not need to be set):

```bicep
// Azure OpenAI (from Azure Portal)
param azureOpenAIEndpoint = 'https://your-openai.openai.azure.com/'
param azureOpenAIApiKey = '<from Azure Portal → Keys>'

// AI Foundry (from AI Foundry Portal)
param projectEndpoint = '<from project settings>'

// Fabric (from Fabric Workspace)
param fabricWorkspaceId = '<workspace GUID>'
param fabricOrchestratorAgentId = '<asst_xxx...>'
param fabricDocumentAgentId = '<asst_xxx...>'
param fabricPowerBiAgentId = '<asst_xxx...>'
param fabricChartAgentId = '<asst_xxx...>'
param fabricSalesAgentId = '<asst_xxx...>'
param fabricRealtimeAgentId = '<asst_xxx...>'

// Power BI (from Power BI Portal)
param powerbiWorkspaceId = '<workspace GUID>'
param powerbiReportId = '<report GUID>'
param powerbiClientId = '<service principal client ID>'
param powerbiTenantId = '<your tenant ID>'
param powerbiClientSecret = '<service principal secret>'

// SQL AD Admin (get SID with: az ad user show --id <UPN> --query id -o tsv)
param sqlAzureAdAdminLogin = 'admin@yourdomain.com'
param sqlAzureAdAdminSid = '<Azure AD object ID GUID>'
```

### Option B: Manual (PowerShell)

Open `bicep/main.bicepparam` and fill in the same values as above.

---

## Step 2: Deploy Infrastructure (8 minutes)

### Option A: azd (Recommended)

```bash
azd up
```

### Option B: PowerShell Script

```bash
# 1. Create resource group
az group create --name rg-myagents-prod --location eastus2

# 2. Deploy infrastructure
cd bicep
az deployment group create \
  --name agent-deployment \
  --resource-group rg-myagents-prod \
  --template-file main.bicep \
  --parameters main.bicepparam

# 3. Get outputs
az deployment group show \
  --name agent-deployment \
  --resource-group rg-myagents-prod \
  --query properties.outputs
```

---

## Step 3: Configure SQL Database (2 minutes)

```bash
# Get web app name
$webAppName = "<from deployment outputs>"

# Open Azure Portal → SQL Database → Query Editor
# Run these commands:
```

```sql
CREATE USER [<your-webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<your-webapp-name>];
```

---

## Step 4: Verify Deployment (2 minutes)

1. **Open Application**:
   ```
   https://<your-webapp-name>.azurewebsites.net
   ```

2. **Login** (if authentication enabled):
   - Username: `admin`
   - Password: `Admin@123`

3. **Change Password**: Navigate to Settings → Change Password

4. **Test Features**:
   - [ ] Create a chat session
   - [ ] Upload a document
   - [ ] View Power BI reports
   - [ ] Check agent responses

---

## ✅ Deployment Complete!

### Next Steps:

1. **Monitor Application**:
   ```bash
   az webapp log tail --name <webapp-name> -g rg-myagents-prod
   ```

2. **View Metrics**:
   - Azure Portal → Application Insights → Live Metrics

3. **Configure Users** (if RLS enabled):
   - Add users via application UI or SQL
   - Assign roles and permissions

4. **Customize**:
   - Modify agent prompts in Fabric
   - Update Power BI reports
   - Add custom routes/endpoints

---

## 🐛 Common Issues

**Issue**: Web app shows error page  
**Fix**: Check logs with `az webapp log tail`

**Issue**: Power BI not loading  
**Fix**: Verify service principal has workspace access

**Issue**: SQL connection failed  
**Fix**: Ensure managed identity was granted access (Step 3)

**Issue**: Agents not responding  
**Fix**: Verify Fabric agent IDs and workspace ID

---

## 📞 Need Help?

- Review full [README.md](README.md) for detailed documentation
- Check [Troubleshooting section](README.md#-troubleshooting)
- Review Azure Portal → Resource Health
- Check Application Insights for errors

---

## 💰 Estimated Costs

**Development**: ~$21/month (B1 App Service + Basic SQL)  
**Production**: ~$276/month (P1v2 App Service + S2 SQL)

*Excludes Azure OpenAI, Fabric, and Power BI usage costs*

---

**Deployment Time**: 15 minutes total  
**Complexity**: Medium (requires Azure services pre-setup)  
**Skill Level**: Intermediate Azure knowledge

---

## 📖 Next Steps

After successful deployment:

1. **Test Your Agents** - Try the [Enterprise Use Cases](DEMO_QUESTIONS.md)
   - Executive dashboards and strategic analysis
   - Sales operations and pipeline forecasting
   - Financial planning and budget analysis
   - Customer success and retention scenarios

2. **Run Smoke Tests** - Verify deployment health
   ```powershell
   .\tests\smoke-test.ps1 -ResourceGroupName "rg-myagents-prod"
   ```

3. **Review Documentation**
   - [Documentation Index](DOCUMENTATION_INDEX.md) - Complete guide
   - [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues

---

## 🎯 Quick Commands Reference

```bash
# Deploy
./scripts/deploy.ps1 -ResourceGroupName "rg-name" -Location "eastus2"

# Check status
az webapp show --name <app-name> -g <rg-name>

# View logs
az webapp log tail --name <app-name> -g <rg-name>

# Restart app
az webapp restart --name <app-name> -g <rg-name>

# Update settings
az webapp config appsettings set --name <app-name> -g <rg-name> --settings KEY=VALUE

# Delete deployment
az group delete --name <rg-name> --yes --no-wait
```

---

**Ready to deploy?** → Run `./scripts/deploy.ps1` 🚀
