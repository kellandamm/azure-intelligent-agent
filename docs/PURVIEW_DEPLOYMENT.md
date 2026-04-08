# Purview Deployment — Microsoft Purview Setup Guide

This guide walks you through deploying **Microsoft Purview** in a way that is easier for a first-time operator to follow. It explains not just what to click, but also why each step matters and what to check before moving on.

---

## What You Are Setting Up

In this process, you are configuring Microsoft Purview so it can **scan, catalog, and govern** your SQL and Microsoft Fabric data assets.

At a high level, the flow is:

1. Create the Purview account.
2. Organize collections.
3. Register data sources.
4. Configure credentials.
5. Run scans.
6. Validate catalog, metadata, and lineage.
7. Add ownership and governance context.

---

## Before You Start

Before opening Purview, gather the following information and confirm you have the right access.

### Required access

- [ ] You have a **Microsoft Purview account** already created, or you have permission to create one.
- [ ] You know whether your target scope is:
  - **Fabric-only**
  - **SQL-only**
  - **Both Fabric and SQL**
- [ ] Your **Purview account** and **Fabric tenant** are in the same Entra tenant if you want the simplest setup.
- [ ] You have the right permissions in:
  - Microsoft Purview
  - Microsoft Fabric
  - Azure (if you need to create identities, Key Vault secrets, or Purview resources)
- [ ] You know your network pattern:
  - Public network access
  - Restricted/private network access

> **Why this matters:** Most Purview deployment failures are not caused by the Purview account itself. They usually happen because permissions, credentials, tenant alignment, or network access were not planned before the first scan.

---

## Step 1 — Create the Purview Account

If a Purview account does not already exist, create it first.

1. Open the **Azure portal**.
2. In the search bar, search for **Microsoft Purview Accounts**.
3. Click **Create**.
4. Fill in the required fields:
   - **Subscription**
   - **Resource group**
   - **Purview account name**
   - **Region**
5. Review the settings.
6. Click **Create**.
7. Wait for deployment to complete.

> **Important:** Creating the Purview account only provisions the service. It does **not** automatically discover, scan, or catalog anything yet.

---

## Step 2 — Open Purview and Create Collections

Collections are how you organize governance scope inside Purview. Think of them as management containers for groups of assets.

1. Open your new or existing **Microsoft Purview account**.
2. Launch the **Purview governance portal**.
3. Go to the area where **collections** are managed.
4. Create a simple structure to start with.

### Recommended starter structure

Use one of these simple options:

| Option | When to Use |
|---|---|
| One **Fabric** collection and one **SQL** collection | Best when you want clean separation by platform |
| One shared **Platform** collection | Best when the environment is small and you want less overhead |

> **Best practice:** Keep the first collection model simple. You can always add more granular collections later after scanning is working.

---

## Step 3 — Decide Which Sources to Register First

Do not register everything at once. Start with the smallest useful scope.

### Recommended rollout order

1. Register **Fabric** first if Fabric is already central to the solution.
2. Register **Azure SQL** next if SQL governance is also required.
3. Add other sources later only after your first scans succeed.

> **Why this matters:** If you register too many sources at once, troubleshooting becomes harder because you will not know whether the issue is permissions, credentials, source type, or scan configuration.

---

## Step 4 — Register the Fabric Tenant

If Fabric is in scope, register it in Purview before you attempt a scan.

1. In Purview, open **Data Map**.
2. Click **Register**.
3. From the list of source types, choose **Fabric**.
4. Enter a friendly source name, such as `Contoso-Fabric`.
5. Select the correct **collection** you created earlier.
6. Confirm the **tenant ID** shown is the correct one.
7. Click **Save**.

> For same-tenant deployments, Purview can discover the Fabric environment in the same Entra tenant more easily than in cross-tenant scenarios.

---

## Step 5 — Prepare Fabric for Scanning

Before you create a Fabric scan, verify that Fabric is actually ready for Purview to connect.

### Confirm these items

- [ ] **Fabric metadata scanning** is enabled.
- [ ] Required **Fabric admin API settings** are enabled.
- [ ] Purview has the required identity access, either through:
  - Purview managed identity, or
  - a service principal
- [ ] If you are using **Key Vault-backed credentials**, Purview can read the secret.

### What to do if you are unsure

1. Open your Fabric admin settings.
2. Review any settings related to metadata scanning and admin APIs.
3. Confirm the identity you plan to use has access to the Fabric environment.
4. If using Key Vault, confirm:
   - the secret exists,
   - the secret name is correct,
   - Purview can read it.

> **Important:** A source can look correctly registered in Purview and still fail to scan if Fabric-side settings or identity permissions are incomplete.

---

## Step 6 — Create Fabric Credentials (If Needed)

Depending on how your environment is set up, Purview may need credentials to scan Fabric.

### Two common options

| Credential type | When to Use |
|---|---|
| **Purview managed identity** | Best when the built-in Purview identity already has the required access |
| **Service principal** | Best when you want a dedicated app identity for scanning |

### If using a service principal

Follow these steps in order:

1. Create an **app registration** in Entra ID.
2. Create a **client secret** for that app registration.
3. Store the secret in **Azure Key Vault**.
4. In Purview, create the **Key Vault connection**.
5. In Purview, create the **credential** using:
   - tenant ID
   - client ID
   - the Key Vault secret reference

> **Best practice:** Use clear names for the app registration, Key Vault secret, and Purview credential so it is obvious which source and environment they belong to.

---

## Step 7 — Create the Fabric Scan

Now that the Fabric source is registered and credentials are ready, create the first scan.

1. In Purview, go to **Data Map** → **Sources**.
2. Open the registered **Fabric** source.
3. Click **+ New scan**.
4. Enter a scan name, such as `Fabric-Initial-Scan`.
5. Choose the credential you prepared earlier.
6. Decide whether to include **personal workspaces**.
   - Include them only if they are in governance scope.
   - Exclude them if you want to start with shared workspaces only.
7. Save the scan.
8. Run the scan.
9. Wait for it to finish before checking results.

> Do not assume the scan worked just because it started. Always wait for completion and then validate the results in the catalog.

---

## Step 8 — Validate the Fabric Catalog and Lineage

After the Fabric scan completes, confirm that Purview actually discovered useful metadata.

1. Open **Unified Catalog**.
2. Browse to **Microsoft Fabric** sources.
3. Open a known workspace.
4. Open a known Fabric item, such as a lakehouse, semantic model, or Power BI-related item.
5. Check that metadata is present, such as:
   - item name
   - workspace name
   - source type
   - timestamps or descriptions if available
6. Open the **Lineage** tab.
7. Confirm that upstream and downstream relationships appear where supported.

### Important limitation to understand

- Purview can bring in metadata and lineage for Fabric items, including Power BI assets.
- Some non-Power BI Fabric item support may still be limited to item-level detail in certain cases.
- Some sub-item lineage gaps may still exist depending on the item type.

> **What success looks like:** You can search for a Fabric asset, open it, and see meaningful metadata and at least the lineage that the source type currently supports.

---

## Step 9 — Register Azure SQL (If SQL Is in Scope)

If Azure SQL governance is part of the solution, register it after Fabric is working.

1. In Purview, go to **Data Map**.
2. Click **Register**.
3. Choose the **Azure SQL** source type.
4. Enter the SQL source details.
5. Assign the source to the correct collection.
6. Click **Save**.

> If both Fabric and SQL are in scope, doing Fabric first usually makes troubleshooting easier because you can validate one platform at a time.

---

## Step 10 — Create and Run the SQL Scan

After SQL is registered, create the scan.

1. Open the registered **Azure SQL** source.
2. Click **+ New scan**.
3. Choose the appropriate credential.
4. Enter a scan name.
5. Save the scan.
6. Run the scan.
7. Wait for completion.

After it finishes:

1. Search for a known SQL asset.
2. Confirm the asset appears in catalog results.
3. Open it and verify the metadata looks correct.

---

## Step 11 — Validate Governance Output

Once both source registration and scans are working, test the actual governance outcomes.

### Check A — Catalog Visibility

1. Search for a known Fabric asset by name.
2. Search for a known SQL asset by name.
3. Confirm both appear where expected.
4. Open them and confirm metadata looks correct.

### Check B — Collection Placement

1. Confirm each asset is stored under the expected collection.
2. Confirm that ownership and governance responsibility are clear based on that collection placement.

### Check C — Lineage

1. Open a known Fabric item used by reports or downstream consumption.
2. Open the lineage view.
3. Confirm expected upstream or downstream relationships are visible where supported.

> **Why this matters:** A successful scan is only part of the outcome. The real goal is discoverability, metadata quality, and useful lineage for governance teams and solution owners.

---

## Step 12 — Add Basic Governance Context

Once the technical scanning path works, add the minimum governance details that make the catalog useful.

1. Identify the **data owner** for each important source or domain.
2. Identify the **steward** or **curator** if your governance model uses those roles.
3. Add glossary terms or business context where it helps people understand the asset.
4. Review whether **sensitivity labels**, protection alignment, or compliance metadata should be part of the first rollout.

> **Best practice:** Keep the first governance pass practical. Start with ownership and basic business meaning before trying to build a perfect enterprise taxonomy.

---

## Step 13 — Prove Purview Is Supporting the Solution

Use at least one of these tests so you can show that Purview is providing real value to the solution, not just existing as a deployed service.

### Test A — Known Asset Lookup

1. Search for a known **Gold table** or **semantic model** asset.
2. Confirm it is discoverable.
3. Confirm metadata and ownership details are present.

### Test B — Lineage Check

1. Pick a Fabric item used by reporting.
2. Open the lineage view.
3. Confirm the governance team can trace the item path from source to downstream usage where supported.

### Test C — Multi-Source Governance Check

1. Search for one SQL asset.
2. Search for one Fabric asset.
3. Confirm both are visible in Purview.
4. Confirm both appear under the governance structure you expected.

---

## Step 14 — Final Go-Live Checklist

Before calling the Purview deployment complete, confirm every item below.

- [ ] Purview account exists.
- [ ] Collections are created and organized.
- [ ] Fabric source is registered if Fabric is in scope.
- [ ] Fabric scan completes successfully.
- [ ] SQL source is registered if SQL is in scope.
- [ ] SQL scan completes successfully.
- [ ] Known assets are searchable.
- [ ] Metadata is correct and usable.
- [ ] Lineage is visible where supported.
- [ ] Roles and governance ownership are documented.

> Do not move this into normal operations until the catalog is searchable and governance ownership is clearly assigned.

---

## Recommended Rollout Order

Use this order when deploying to a new environment:

1. Create the Purview account.
2. Create collections.
3. Register Fabric.
4. Configure credentials.
5. Run the Fabric scan.
6. Validate the catalog and lineage.
7. Register SQL if needed.
8. Run the SQL scan.
9. Add ownership and governance context.
10. Move the governance process into normal operations.

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | What to Check |
|---|---|---|
| Fabric source registers but scan fails | Fabric metadata scanning or admin API settings not enabled | Re-check Fabric admin settings and source permissions |
| Scan starts but finds little or no useful metadata | Wrong credential, missing permissions, or wrong scope | Re-check the credential, access rights, and scan settings |
| Key Vault-backed credential fails | Purview cannot read the secret | Confirm secret name, Key Vault access policy/RBAC, and tenant alignment |
| Assets do not appear in the catalog | Scan failed or has not completed yet | Check scan history and wait for full completion |
| Lineage is missing for some Fabric items | Source type limitations or unsupported sub-item lineage | Confirm whether that item type currently supports the lineage depth you expect |
| Governance ownership is unclear | Collections or role assignments were never formalized | Add owners, stewards, and collection structure before go-live |
