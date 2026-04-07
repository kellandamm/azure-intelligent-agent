# Deployment Guide

Deploy the Azure Intelligent Agent from zero to running in a practical step-by-step flow.

---

## Prerequisites

Have these ready before starting:

- [ ] **Azure CLI** installed and logged in (`az login`)
- [ ] **PowerShell 7.0+** installed (`pwsh` command available)
- [ ] **Azure subscription** with Contributor access to a resource group
- [ ] Your **Azure AD UPN**: `az ad signed-in-user show --query userPrincipalName -o tsv`
- [ ] Your **Azure AD object ID**: `az ad signed-in-user show --query id -o tsv`
- [ ] **Azure AI Foundry** project or **Azure OpenAI** deployment, depending on your chosen backend
- [ ] **Microsoft Fabric capacity** only if you plan to enable Fabric

---

## Phase 1 — Configure Parameters

Open the main Bicep parameter file and fill in the required values first.

### Required fields

- SQL Azure AD admin login.
- SQL Azure AD admin object ID.
- AI endpoint/project settings.
- Model deployment name.

### Optional integrations

Leave these blank unless you plan to enable them now:

- Fabric workspace and analytics settings.
- Foundry/Data Agent settings.
- RTI settings.
- Purview settings.

---

## Phase 2 — Deploy Infrastructure

Choose **one** method.

### Option A — Azure Developer CLI

```bash
azd init
azd env set AZURE_LOCATION westus3
azd up
```

### Option B — PowerShell

```powershell
az group create --name rg-myagents-prod --location westus3
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod"
```

To redeploy code only later:

```powershell
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod" `
                     -AppName "<your-app-name>" `
                     -SkipInfrastructure
```

---

## Phase 3 — Confirm a Healthy Start

Tail the startup logs:

```powershell
az webapp log tail --name <app-name> --resource-group rg-myagents-prod
```

A healthy start should show the application booting cleanly.

---

## Phase 4 — Configure Authentication and Seed Data

Run the required SQL schema and seed scripts in Azure SQL Query Editor.

Recommended order:

1. Authentication schema.
2. Security / RLS policies.
3. Synthetic or business seed data.
4. Create the first admin user if authentication is enabled.

---

## Phase 5 — Validate SQL Access

The application should be able to use its managed identity to access Azure SQL.

If automatic grant fails, run:

```sql
CREATE USER [<webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<webapp-name>];
```

Then restart the app.

---

## Phase 6 — Fabric

Microsoft Fabric is optional. The app can run fully against Azure SQL alone.

### Option A — No Fabric

Skip this phase entirely.

### Option B — Full Fabric

Use **[FABRIC_DEPLOYMENT.md](FABRIC_DEPLOYMENT.md)** for the step-by-step Fabric walkthrough.

That guide covers:

- Azure SQL mirroring.
- Bronze, Silver, and Gold setup.
- Repo notebook source files.
- Semantic model guidance.
- Direct Lake guidance.
- App connection to Fabric.

---

## Phase 7 — Optional Real-Time Intelligence

If you need near-real-time monitoring and actions:

1. Create Eventstream.
2. Add an event source.
3. Route data to Eventhouse.
4. Add Activator rules.
5. Validate one end-to-end event path.

See **[FABRIC_RTI_OPTIONAL_DEPLOYMENT.md](FABRIC_RTI_OPTIONAL_DEPLOYMENT.md)**.

---

## Phase 8 — Optional Foundry and Data Agent

If you need conversational analytics over curated Fabric data:

1. Create the Fabric Data Agent.
2. Expose only approved Gold data.
3. Connect it through Foundry.
4. Validate Fabric first, then Foundry, then the app.

See **[FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md](FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md)**.

---

## Phase 9 — Optional Purview

If you need governance and cataloging:

1. Deploy the Purview account.
2. Register the required sources.
3. Configure scans.
4. Validate catalog and lineage.

See **[PURVIEW_OPTIONAL_DEPLOYMENT.md](PURVIEW_OPTIONAL_DEPLOYMENT.md)**.

---

## Phase 10 — Smoke Tests

```bash
python tests/smoke_test.py   --url https://<your-app-name>.azurewebsites.net   --skip-auth
```

A healthy run shows the main endpoints returning successful responses.

---

## Common Commands

| Action | PowerShell / Azure CLI | azd |
|--------|------------------------|-----|
| Full deploy | `.\scripts\deploy.ps1 -ResourceGroupName rg-name` | `azd up` |
| Code only | `.\scripts\deploy.ps1 -ResourceGroupName rg-name -AppName app-name -SkipInfrastructure` | `azd deploy` |
| Tail logs | `az webapp log tail --name app-name -g rg-name` | `azd monitor --logs --follow` |
| Restart app | `az webapp restart --name app-name -g rg-name` | — |
| Delete everything | `az group delete --name rg-name --yes --no-wait` | `azd down` |

---

## Troubleshooting

- Startup issues: tail App Service logs.
- SQL issues: check identity, permissions, and networking.
- Fabric issues: validate mirroring and Gold tables before switching the app path.
- Foundry/Data Agent issues: validate each layer independently before testing the app route.
