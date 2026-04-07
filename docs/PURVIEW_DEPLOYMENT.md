# Purview Deployment — Step by Step

Use these steps to deploy Microsoft Purview and prove that governance scanning and cataloging are working for your SQL and Fabric data paths.

## Step 1 — Confirm prerequisites

Before starting, confirm these:

- You have a Microsoft Purview account deployed or are ready to create one.
- You know whether your target scenario is SQL-only, Fabric-only, or both.
- Your Purview account and Fabric tenant are in the same tenant if you want the simpler same-tenant setup.
- You have the required permissions in Purview and Fabric.
- You know whether you are using public network access or a more restricted network pattern.

## Step 2 — Create the Purview account

If the account does not already exist:

1. Go to the Azure portal.
2. Open **Microsoft Purview Accounts**.
3. Select **Create**.
4. Enter the subscription, resource group, name, and region.
5. Complete the configuration and create the account.

Important note:

- Creating the account is only the provisioning step.
- Governance value comes after collections, registration, credentials, and scans are configured.

## Step 3 — Open Purview and create collections

1. Open Microsoft Purview.
2. Go to the governance portal or studio experience.
3. Create or organize collections that match your governance model.

Recommended simple starting point:

- one collection for Fabric,
- one collection for SQL,
- or a shared platform collection if your scope is still small.

## Step 4 — Decide what sources to register first

Keep the first rollout simple.

Recommended order:

1. Register Fabric if Fabric is already part of the solution.
2. Register Azure SQL if SQL governance is in scope.
3. Add more sources later.

## Step 5 — Register the Fabric tenant

If Fabric is in scope:

1. In Purview, go to **Data Map**.
2. Select **Register**.
3. Choose **Fabric** as the source type.
4. Enter a friendly source name.
5. Select the correct collection.
6. Confirm the tenant ID is correct.
7. Save the registration.

For same-tenant setup, Purview can discover the Fabric tenant in the same Entra tenant.

## Step 6 — Prepare Fabric for scanning

Before scanning Fabric, confirm these settings:

1. Fabric metadata scanning is enabled.
2. Required Fabric admin API settings are enabled.
3. Purview has the required identity or service principal access.
4. If using Key Vault-backed credentials, Purview can read the secret.

If these are not configured, scans often fail even when the source registration looks correct.

## Step 7 — Create Fabric credentials if needed

Depending on your setup:

- use the Purview managed identity, or
- create a service principal credential.

If using a service principal:

1. Create the app registration.
2. Create the secret.
3. Store the secret in Key Vault.
4. Create the Key Vault connection in Purview.
5. Create the Purview credential using tenant ID, client ID, and Key Vault secret.

## Step 8 — Create the Fabric scan

1. In Purview, go to **Data Map** -> **Sources**.
2. Open the registered Fabric source.
3. Select **+ New scan**.
4. Enter a scan name.
5. Choose the credential.
6. Choose whether to include personal workspaces.
7. Save and run the scan.

Wait for the scan to complete before checking catalog or lineage.

## Step 9 — Validate Fabric catalog and lineage

After the scan completes:

1. Open **Unified Catalog**.
2. Browse to **Microsoft Fabric** sources.
3. Open the workspace.
4. Open a known Fabric item.
5. Confirm metadata is present.
6. Open the **Lineage** tab and confirm upstream/downstream relationships appear where supported.

Important note:

- Purview brings in metadata and lineage for Fabric items including Power BI.
- For non-Power BI Fabric items, support may still be item-level only in some cases, and some sub-item lineage limitations remain.

## Step 10 — Register Azure SQL if SQL governance is needed

If SQL is in scope:

1. Go to **Data Map**.
2. Select **Register**.
3. Choose the Azure SQL source type.
4. Enter the source details.
5. Assign the source to the correct collection.
6. Save the registration.

## Step 11 — Create and run the SQL scan

1. Open the registered SQL source.
2. Select **+ New scan**.
3. Choose the right credential.
4. Enter the scan name.
5. Save and run the scan.

After the scan completes, confirm the SQL assets appear in catalog results.

## Step 12 — Validate governance output

Use these checks:

### Check A — Catalog visibility

1. Search for a known Fabric or SQL asset by name.
2. Confirm it appears in the catalog.
3. Confirm the metadata looks correct.

### Check B — Collection placement

1. Confirm the asset is stored under the expected collection.
2. Confirm governance ownership is clear.

### Check C — Lineage

1. Open a known Fabric item.
2. Open the lineage view.
3. Confirm the expected upstream or downstream relationships are visible where supported.

## Step 13 — Add governance basics

Once scanning works, add the first governance controls:

1. Confirm data owners.
2. Confirm stewards or curators.
3. Add glossary or business context where useful.
4. Review sensitivity and protection alignment if in scope.

Keep the first governance rollout focused and practical.

## Step 14 — Prove Purview is supporting the solution

Use one or more of these practical tests:

### Test A — Known asset lookup

1. Search for a known Gold table or semantic model asset.
2. Confirm it is discoverable in Purview.
3. Confirm metadata and ownership details are present.

### Test B — Lineage check

1. Pick a known Fabric item used by reports.
2. Open lineage.
3. Confirm the governance team can trace the item path.

### Test C — Multi-source governance check

1. Search for both a SQL asset and a Fabric asset.
2. Confirm both appear under the governance model you expected.

## Step 15 — Final go-live checklist

Before calling Purview complete, confirm:

- Purview account exists.
- Collections are organized.
- Fabric source is registered if Fabric is in scope.
- Fabric scan runs successfully.
- SQL source is registered if SQL is in scope.
- SQL scan runs successfully.
- Known assets are searchable.
- Metadata looks correct.
- Lineage is visible where supported.
- Roles and governance ownership are documented.

## Recommended rollout order

Use this order:

1. Create the Purview account.
2. Create collections.
3. Register Fabric.
4. Configure credentials.
5. Run Fabric scan.
6. Validate catalog and lineage.
7. Register SQL if needed.
8. Run SQL scan.
9. Add ownership and governance context.
10. Promote the governance process into normal operations.
