# Deployment Guide

Deploy the Azure Intelligent Agent from zero to running in a simple step-by-step flow.

---

## Prerequisites

Have these ready before starting:

- [ ] Azure CLI installed and logged in.
- [ ] PowerShell 7.0+ installed.
- [ ] Azure subscription with Contributor access.
- [ ] Azure AD UPN and object ID.
- [ ] Azure AI Foundry project or Azure OpenAI deployment.
- [ ] Fabric capacity only if you plan to enable Microsoft Fabric.

---

## Phase 1 — Configure Parameters

1. Open the main Bicep parameter file.
2. Fill in the required SQL Azure AD admin values.
3. Fill in the required AI endpoint or Foundry project settings.
4. Leave Fabric, RTI, Direct Lake, Foundry/Data Agent, and Purview settings blank unless you plan to enable them now.

---

## Phase 2 — Deploy Infrastructure

Choose one method.

### Azure Developer CLI

```bash
azd init
azd env set AZURE_LOCATION westus3
azd up
```

### PowerShell

```powershell
az group create --name rg-myagents-prod --location westus3
.\scripts\deploy.ps1 -ResourceGroupName "rg-myagents-prod"
```

After deployment, note the app name from the output.

---

## Phase 3 — Confirm the App Starts

```powershell
az webapp log tail --name <app-name> --resource-group rg-myagents-prod
```

A healthy start should show the application booting without configuration errors.

---

## Phase 4 — Configure Authentication and Seed Data

1. Open Azure Portal → SQL Database → Query Editor.
2. Run the required schema and seed SQL scripts in order.
3. Create the first admin user if authentication is enabled.
4. Confirm you can sign in successfully.

---

## Phase 5 — Validate SQL Access

1. Confirm the app can reach Azure SQL.
2. If the managed identity grant did not work automatically, run:

```sql
CREATE USER [<webapp-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<webapp-name>];
```

3. Restart the app if needed.

---

## Phase 6 — Optional Fabric Setup

If you do not need Fabric, skip this section.

If you do need Fabric:

1. Create the Fabric workspace.
2. Enable SQL mirroring.
3. Build the Silver and Gold layers.
4. Create the semantic model.
5. Prefer Direct Lake over curated Gold data.
6. Point the app to Fabric only after validation.

See **[FABRIC_DEPLOYMENT.md](FABRIC_DEPLOYMENT.md)** for the full walkthrough.

---

## Phase 7 — Optional RTI Setup

If you need near-real-time monitoring:

1. Create Eventstream.
2. Route data to Eventhouse.
3. Add Activator rules.
4. Test one end-to-end event path.

See **[FABRIC_RTI_OPTIONAL_DEPLOYMENT.md](FABRIC_RTI_OPTIONAL_DEPLOYMENT.md)**.

---

## Phase 8 — Optional Foundry and Data Agent Setup

If you need conversational analytics over Fabric:

1. Create the Fabric Data Agent.
2. Expose only curated Gold data.
3. Connect it through Foundry.
4. Validate Fabric first, then Foundry, then the app.

See **[FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md](FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md)**.

---

## Phase 9 — Optional Purview Setup

If you need governance:

1. Deploy the Purview account.
2. Register sources.
3. Configure scans.
4. Validate catalog and lineage.

See **[PURVIEW_OPTIONAL_DEPLOYMENT.md](PURVIEW_OPTIONAL_DEPLOYMENT.md)**.

---

## Phase 10 — Smoke Test

```bash
python tests/smoke_test.py --url https://<your-app-name>.azurewebsites.net --skip-auth
```

Confirm the app loads and the main endpoints return healthy responses.

---

## Troubleshooting

- App startup issues: tail App Service logs.
- SQL connection issues: verify identity, networking, and SQL permissions.
- Fabric issues: validate mirroring and Gold table creation before app cutover.
- Foundry/Data Agent issues: validate Fabric and Foundry independently before using the app path.
