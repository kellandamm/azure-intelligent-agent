# Microsoft Fabric Setup — Mirroring, Medallion Architecture & Pipelines

Sets up Microsoft Fabric to mirror your Azure SQL database and build a medallion analytics architecture that powers dashboards, curated analytics, and optional Data Agent scenarios.

> **No Fabric?** Skip this guide entirely. The app works without Fabric configuration.

---

## Architecture Overview

```text
Azure SQL DB  ->  Fabric OneLake Bronze
                     |
              Notebooks / Dataflows
                     |
               Silver Lakehouse
                     |
              Notebooks / Pipeline
                     |
                Gold Lakehouse
                     |
      Semantic model / App analytics / Data Agent
```

**Bronze** = mirrored raw data.
**Silver** = cleansed and standardized data.
**Gold** = analytics-ready curated tables.

---

## Prerequisites

- Microsoft Fabric capacity assigned to your tenant.
- Azure SQL database deployed and seeded.
- Fabric workspace admin rights.
- Azure SQL access to enable change tracking.

---

## Phase 1 — Create a Fabric Workspace

1. Go to [app.fabric.microsoft.com](https://app.fabric.microsoft.com).
2. Create a workspace.
3. Assign capacity.
4. Copy the Workspace ID.

---

## Phase 2 — Prepare Azure SQL for Mirroring

Enable SQL change tracking on the database and on the required source tables before creating the mirror.

---

## Phase 3 — Create the Mirrored Database (Bronze)

1. In the Fabric workspace, create a **Mirrored Azure SQL Database** item.
2. Add the Azure SQL connection.
3. Select the required source tables.
4. Start mirroring.
5. Wait for healthy running status.

---

## Phase 4 — Create the Silver and Gold Lakehouses

Create two lakehouses:

| Name | Purpose |
|------|---------|
| `AgentDemo_Silver` | Cleansed, standardized tables |
| `AgentDemo_Gold` | Analytics-ready curated tables |

---

## Phase 5 — Silver Layer

Use the repo notebook source files instead of embedding large notebook bodies in this guide.

Notebook sources:

- `notebooks/01_bronze_seed_demo_data.py`
- `notebooks/02_silver_transform.py`

Run the Silver transformation flow and confirm the expected Silver tables are created.

---

## Phase 6 — Gold Layer

Notebook sources:

- `notebooks/03_gold_aggregate.py`
- `notebooks/04_validate_gold.py`

Run the Gold aggregation notebook, then run the validation notebook.

---

## Phase 7 — Build the Refresh Pipeline

1. Create a Fabric data pipeline.
2. Add the Silver notebook step.
3. Add the Gold notebook step.
4. Set Gold to depend on Silver.
5. Add a schedule.
6. Test a manual run.

---

## Phase 8 — Semantic Model and Direct Lake

1. Build the semantic model over curated Gold data.
2. Prefer Direct Lake when the Gold data already lives in Fabric.
3. Avoid unnecessary DirectQuery fallback.
4. Validate behavior before cutover.

---

## Phase 9 — Connect the App to Fabric Gold

1. Get the Fabric SQL analytics endpoint or agreed app connection target.
2. Set the required app settings.
3. Restart the app.
4. Validate that app analytics use the expected Fabric Gold path.

---

## Verification

- Mirroring is healthy.
- Silver tables exist.
- Gold tables exist.
- Validation notebook passes.
- Semantic model works.
- App reads from the intended Fabric path.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Mirroring stuck | Recheck SQL change tracking. |
| Gold tables empty | Rerun Silver, then Gold, then validation. |
| App still using SQL | Verify app settings and restart. |
| Direct Lake issues | Recheck semantic model design and fallback behavior. |
