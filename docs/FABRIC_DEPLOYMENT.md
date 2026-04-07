# Microsoft Fabric Setup — Mirroring, Medallion Architecture & Pipelines

Sets up Microsoft Fabric to mirror your Azure SQL database and build a practical Bronze, Silver, and Gold analytics flow for dashboards, Data Agent scenarios, and optional Direct Lake semantic models.

> **No Fabric?** Skip this guide entirely. The app works without any Fabric configuration.

---

## Prerequisites

- Microsoft Fabric capacity assigned to your tenant.
- Azure SQL database deployed and seeded.
- Fabric workspace admin rights.
- Azure SQL access so you can enable change tracking.

---

## Phase 1 — Create a Fabric Workspace

1. Go to [app.fabric.microsoft.com](https://app.fabric.microsoft.com).
2. Create a new workspace.
3. Assign your Fabric capacity.
4. Copy the Workspace ID for later use.

---

## Phase 2 — Prepare Azure SQL for Mirroring

Enable SQL change tracking on the database and on the tables you want mirrored.

Use the same Azure SQL mirroring preparation approach as in your existing guide, then confirm change tracking is active before moving on.

---

## Phase 3 — Create the Mirrored Database

1. In the Fabric workspace, create a **Mirrored Azure SQL Database** item.
2. Add the Azure SQL connection.
3. Select the required source tables.
4. Start mirroring.
5. Wait until mirrored status shows healthy and running.

---

## Phase 4 — Create the Silver and Gold Lakehouses

Create:

- one Silver lakehouse for cleansed data,
- one Gold lakehouse for analytics-ready tables.

---

## Phase 5 — Build the Silver Layer

Use the repo notebook source files instead of embedding large notebook bodies directly in the doc:

- `notebooks/01_bronze_seed_demo_data.py`
- `notebooks/02_silver_transform.py`

Run the Silver transform logic and confirm the expected Silver tables are created.

---

## Phase 6 — Build the Gold Layer

Use:

- `notebooks/03_gold_aggregate.py`
- `notebooks/04_validate_gold.py`

Run the Gold notebook, then run the validation notebook to confirm the Gold layer is populated and queryable.

---

## Phase 7 — Semantic Model and Direct Lake

1. Build the semantic model over curated Gold data.
2. Use Direct Lake as the preferred mode when the Gold layer is already in Fabric.
3. Avoid unnecessary DirectQuery fallback.
4. Validate refresh and query behavior before app cutover.

---

## Phase 8 — Connect the App to Fabric

1. Get the Fabric SQL analytics endpoint or the agreed app connection path.
2. Set the required app settings.
3. Restart the app.
4. Validate that app analytics are reading from the expected Fabric Gold path.

---

## Verification

- Mirroring is healthy.
- Silver tables exist.
- Gold tables exist.
- Validation notebook passes.
- Semantic model works.
- Direct Lake behavior is validated if enabled.
- App reads from the intended Fabric path.

---

## Troubleshooting

- Mirroring stuck: recheck SQL change tracking.
- Empty Gold tables: rerun Silver, then Gold, then validation.
- App still using SQL path: verify app settings and restart.
- Direct Lake fallback issues: validate semantic model design and source path.
