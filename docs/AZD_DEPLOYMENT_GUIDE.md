# Azure Developer CLI (azd) Guide

Reference for deploying and managing the application with `azd`.

For the full step-by-step deployment walkthrough (which covers both `azd` and PowerShell) see [QUICK_START.md](QUICK_START.md).

---

## Install azd

**Windows:**
```powershell
winget install microsoft.azd
```

**macOS:**
```bash
brew tap azure/azd && brew install azd
```

**Linux:**
```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

**Verify:**
```bash
azd version
```

---

## Login

```bash
azd auth login    # azd authentication
az login          # Azure CLI (also required)
```

---

## Core Deployment Commands

| Command | What it does |
|---------|-------------|
| `azd up` | Initialize + provision infrastructure + deploy code (first-time or full redeploy) |
| `azd provision` | Provision / update Azure infrastructure only (runs Bicep) |
| `azd deploy` | Deploy application code only — no infra changes (~3 min) |
| `azd deploy web` | Deploy only the `web` service |
| `azd down` | Delete all Azure resources |
| `azd down --purge` | Delete resources and remove local environment config |
| `azd browse` | Open the deployed app in a browser |
| `azd show` | Show deployment status and service endpoints |

---

## Environment Management

`azd` supports isolated environments (dev, staging, prod) using environment files stored in `.azure/`.

```bash
# Create environments
azd env new dev
azd env new staging
azd env new prod

# Switch active environment
azd env select dev

# List all environments
azd env list

# Set a variable in the active environment
azd env set AZURE_LOCATION westus2

# View all variables
azd env get-values

# Refresh variables from deployed resources
azd env refresh
```

### Deploy to multiple environments

```bash
azd env select dev    && azd up
azd env select staging && azd up
azd env select prod   && azd up
```

### Key azd environment variables

| Variable | Description |
|----------|-------------|
| `AZURE_LOCATION` | Azure region (e.g. `westus2`) |
| `AZURE_ENVIRONMENT_NAME` | Environment label (`dev`, `staging`, `prod`) |
| `AZURE_APP_NAME` | Optional custom app name prefix |

> **SQL admin** is not an azd env var — set `sqlAzureAdAdminLogin` and `sqlAzureAdAdminSid` directly in `bicep/main.bicepparam`. Both fields are required; empty values cause `RequestDisallowedByPolicy` at provision time.

---

## Monitoring

```bash
# Live log stream
azd monitor --logs --follow

# View recent logs
azd monitor --logs

# Open Application Insights in the portal
azd monitor --overview
```

---

## Pre-Deployment Validation (Recommended)

Run before `azd provision` to catch Azure Policy violations before they fail mid-deployment:

```powershell
.\scripts\validate-policy-compliance.ps1 -ResourceGroup <rg-name>
```

Checks: SQL security properties, VNet integration, Azure AD admin parameters, active deny policies.

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Login to Azure
  run: |
    azd auth login \
      --client-id ${{ secrets.AZURE_CLIENT_ID }} \
      --tenant-id ${{ secrets.AZURE_TENANT_ID }} \
      --client-secret ${{ secrets.AZURE_CLIENT_SECRET }}

- name: Deploy
  run: |
    azd env select prod
    azd up --no-prompt
```

### Azure DevOps

```yaml
- task: AzureCLI@2
  inputs:
    azureSubscription: 'Production'
    scriptType: bash
    scriptLocation: inlineScript
    inlineScript: |
      azd env select prod
      azd up --no-prompt
```

### Required secrets / service principal

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "my-agent-cicd" \
  --role Contributor \
  --scopes /subscriptions/<subscription-id>

# Store output as GitHub secrets:
#   AZURE_CLIENT_ID
#   AZURE_TENANT_ID
#   AZURE_CLIENT_SECRET
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `azd: command not found` | Run `winget install microsoft.azd` and restart the shell |
| Authentication failed | Run `azd auth login` and `az login` |
| Environment not found | `azd env list` then `azd env new <name>` |
| Deployment failed | `azd show` for summary; `azd provision --debug` for verbose output |
| Missing variable error | `azd env get-values` to check; `azd env set KEY VALUE` to fix |

---

## Resources

- [azd documentation](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- [azd GitHub](https://github.com/Azure/azure-dev)
- [azd template gallery](https://azure.github.io/awesome-azd/)
