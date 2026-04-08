# Phase 8 — Semantic Model and Direct Lake Setup Guide

This guide walks you through connecting your app's reports to **Microsoft Fabric Gold data** using a Direct Lake semantic model. Follow each step in order. Do not skip ahead — each step depends on the previous one being complete.

---

## Before You Start

**What you'll need:**
- Access to your Microsoft Fabric workspace
- The Gold Lakehouse or Warehouse already set up (from earlier phases)
- Power BI / Fabric reporting permissions in your workspace
- Your app's environment variables accessible (App Service settings)

**What you're trying to accomplish:**
You are creating a *semantic model* — think of it as a structured, optimized layer that sits between your raw Gold data tables and your reports/app. This is what makes your reports fast and reliable.

---

## Step 1 — Confirm Your Gold Tables Are Ready

Before you do anything else, verify that your data pipeline ran successfully.

1. Open your Fabric workspace.
2. Navigate to your **Gold Lakehouse** (or Warehouse).
3. Check that the following notebooks completed without errors:
   - The **Gold notebook** (transforms Silver → Gold data)
   - The **Validation notebook** (checks data quality)
4. Open the Lakehouse and browse the **Tables** section. Confirm these tables exist:

| Table Name | Purpose |
|---|---|
| `gold_customer360` | Customer data |
| `gold_productperformance` | Product metrics |
| `goldsalesbycategory` | Sales by category |
| `goldsalestimeseries` | Sales over time |
| `goldsupportmetrics` | Support KPIs |

> **Why this matters:** If any Gold table is missing or has stale data, your semantic model will either fail to build or show incorrect numbers downstream. Fix data issues here before proceeding.

---

## Step 2 — Create the Semantic Model

A semantic model tells Power BI/Fabric *which tables to use* and *how to interpret them*. You can create it from two places — choose the one that matches how your Gold data is stored.

### Option A — If your Gold data is in a Lakehouse

1. In your Fabric workspace, click to open your **Gold Lakehouse**.
2. In the top ribbon, click **New semantic model**.

   > If you don't see this button, make sure you're in the Lakehouse view (not a notebook or pipeline).

3. In the dialog that appears:
   - **Name**: Enter `AgentDemo_Gold_Model` (or a name that matches your project).
   - **Tables**: Check only the curated Gold tables listed in Step 1. Do not select raw or Silver tables.
4. Click **Confirm**.

### Option B — If your Gold data is in a SQL Analytics Endpoint or Warehouse

1. Open the **SQL analytics endpoint** for your Gold item, or open the **Warehouse** directly.
2. In the left navigation, click **Reporting**.
3. Click **New semantic model**.
4. Enter the same model name as above.
5. Select the curated Gold tables.
6. Click **Confirm**.

> **Result:** After confirming, Fabric will open the semantic model editor automatically. Leave it open — you'll use it in the next step.

---

## Step 3 — Clean Up the Model in the Web Editor

When the semantic model editor opens, you need to make a few adjustments before it's report-ready.

1. **Check relationships** — Look at the diagram view. Fabric may have auto-detected relationships between your Gold tables. Review them:
   - Fact tables (like sales) should connect to dimension tables (like customers, products) via matching ID columns.
   - If a relationship is wrong or missing, click the line between tables to edit it, or drag from one column to another to create one.

2. **Set data types** — Click each table and review the columns panel on the right:
   - Date columns should be set to **Date** or **Date/Time** type.
   - Revenue and numeric columns should be **Decimal Number** or **Whole Number**.
   - ID columns that should never be summed should be set to **Text** or have summarization disabled.

3. **Mark your date table** (if you have one) — If you have a dedicated calendar/date table:
   - Select the table.
   - Click **Mark as date table** in the toolbar.
   - Select the date column.

4. **Create basic measures** — In the left panel, right-click a table and choose **New measure**. Create these to start:

   ```
   Total Revenue = SUM(goldsalestimeseries[revenue])
   Total Orders = COUNTROWS(goldsalesbycategory)
   Average Order Value = DIVIDE([Total Revenue], [Total Orders])
   Active Customers = DISTINCTCOUNT(gold_customer360[customer_id])
   ```

   > Adjust column names to match your actual table schema.

5. **Hide technical columns** — Right-click any columns that are internal IDs or technical fields not needed in reports, and select **Hide**. This keeps your report fields list clean.

6. Click **Save** (top right or Ctrl+S).

---

## Step 4 — Keep the Model in Direct Lake Mode

Direct Lake is a Fabric-specific performance mode that reads data directly from the lakehouse without importing or querying through SQL. You want to stay in this mode.

**Do these things to stay in Direct Lake mode:**

- ✅ Build the model using only Fabric Gold tables (not external sources or mixed sources).
- ✅ Keep the first version of the model simple — no complex filters or security rules yet.
- ❌ Avoid using **SQL endpoint views** as table sources when possible.
- ❌ Avoid applying **Row-Level Security (RLS)** through the SQL analytics endpoint for these tables — it forces a fallback to DirectQuery mode.

> **What is DirectQuery fallback?** If Fabric can't serve a query through Direct Lake, it automatically falls back to DirectQuery, which is slower. For initial validation, you want to avoid this. You'll see a warning banner in the semantic model if this happens.

---

## Step 5 — Build a Validation Report

Before connecting your app, build a quick standalone report to verify the semantic model is working correctly.

1. From the semantic model editor, click **New report** in the ribbon (or go to the workspace and create a new **Power BI report**, pointing it to your new semantic model).
2. In the report canvas, add the following visuals:

   | Visual Type | Fields to Use | Table Source |
   |---|---|---|
   | Line chart | Revenue by Month | `goldsalestimeseries` |
   | Bar chart | Revenue by Category | `goldsalesbycategory` |
   | Card | Customer Count or Total Value | `gold_customer360` |
   | KPI or Card | Support metric (e.g., ticket count) | `goldsupportmetrics` |

3. Verify the numbers look reasonable (not zero, not obviously wrong).
4. Save the report as `AgentDemo_Validation_Report` (or similar).

> **This report is your safety net.** Before touching the app, confirm data looks correct here. It is much faster to debug in a standalone report than inside the app.

---

## Step 6 — Verify the Model Is Reading Live Fabric Data

You need to confirm that changes to source data actually flow through to your report. Run both checks below.

### Check A — End-to-End Refresh Test

1. Identify a record you can safely modify (a test customer, test order, etc.) in your **Azure SQL source database**.
2. Make a change — for example, update a revenue value or add a new row.
3. Trigger the mirroring process (or wait for the scheduled mirror sync to complete).
4. Run the Gold notebook to re-process the updated data.
5. Return to your validation report and click **Refresh visuals** (the circular arrow icon).
6. Confirm the updated value now shows in the report.

### Check B — Direct Comparison Against Gold Tables

1. In Fabric, open your Gold Lakehouse.
2. Click on a Gold table (e.g., `goldsalestimeseries`) and use **Preview data** or query it via the SQL analytics endpoint.
3. Note the total revenue value (or another easily comparable metric).
4. Compare that value to the same metric shown in your validation report.
5. They should match exactly (or within rounding).

> If the values match, your semantic model is correctly reading from Fabric-prepared data — not from an old SQL path.

---

## Step 7 — Connect the App to the Fabric Reporting Path

Now that the semantic model is validated, update your app to use it.

1. Open your **Gold Lakehouse** or **SQL analytics endpoint** in Fabric.
2. Click the **Settings** gear or find the **Connection string** / **Server endpoint** details. Copy the following:
   - Server / workspace endpoint URL
   - Dataset ID or semantic model name
3. Go to your **Azure App Service** in the Azure portal.
4. Click **Configuration** → **Application settings**.
5. Update (or add) the environment variables your app uses for its reporting connection. Common variables include:

   ```
   FABRIC_WORKSPACE_ID = <your workspace ID>
   FABRIC_DATASET_ID   = <your semantic model ID>
   POWERBI_REPORT_ID   = <your report ID, if embedding>
   ```

   > Your app may use different variable names. Check the app's `.env` or config documentation for the exact keys.

6. Click **Save**.
7. Click **Restart** to restart the app service.
8. Open the app and navigate to the report pages. Confirm they load without errors.

> **If your app embeds Power BI reports:** Make sure the embedded report is published from the semantic model you just validated — not from an older imported dataset.

---

## Step 8 — Prove the App Is Not Using the Old SQL-Only Path

Run at least one of these tests to confirm the app is using Fabric data, not the old direct-SQL path.

### Test 1 — Fabric-Only Metric Test

1. In your semantic model, create a new measure that **only exists in Fabric** — for example, a calculated field like `Fabric_Verified = 1`.
2. Add it to the validation report.
3. Publish the report.
4. Open the app and go to the report page.
5. If the metric appears, the app is pulling from Fabric. If it's missing, the app is still using an old data source.

### Test 2 — Controlled Value Change Test

1. Change a known value in your Azure SQL source (e.g., set a specific customer's revenue to a distinctive number like `99999`).
2. Run the mirror sync and Gold notebook.
3. Check the Fabric validation report — confirm the updated value appears.
4. Open the app — confirm the app shows the same updated value.

### Test 3 — Settings Swap Test

1. Record the current values shown in the app's report pages (screenshot them).
2. Confirm the app's environment variables now point to the Fabric semantic model (set in Step 7).
3. Restart the app.
4. Compare the new values with your Fabric validation report values — they should match.

---

## Step 9 — Final Pre-Cutover Checklist

Before marking this phase complete, verify every item below:

- [ ] Gold notebook runs and completes successfully
- [ ] Semantic model saves without errors
- [ ] Validation report builds and loads data correctly
- [ ] Direct Lake mode is active (no unexpected DirectQuery fallback warnings)
- [ ] No unnecessary SQL views or RLS patterns introduced in this phase
- [ ] App report pages match the Fabric validation report values
- [ ] App restarts cleanly with no reporting errors in logs

> **Do not proceed to production until all boxes are checked.**

---

## Step 10 — First Production Rollout Order

When you are ready to promote to production, follow this exact sequence:

1. ✅ Validate Gold tables (data is current and complete)
2. ✅ Validate semantic model (saves, loads, and Direct Lake is active)
3. ✅ Validate standalone report (visuals load, numbers look correct)
4. 🔄 Point a **non-production (staging) app instance** to the Fabric reporting path
5. 🔍 Compare staging app values against known Gold table outputs
6. ✅ Get signoff from a stakeholder or QA reviewer
7. 🚀 Promote the same configuration to the production app

> **Why this order?** Each step de-risks the next. You confirm the data path is correct before putting it in front of end users.

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | What to Try |
|---|---|---|
| Semantic model won't save | Missing required relationship or invalid column type | Check the error message in the editor; fix data types or remove the broken table |
| Report shows blank visuals | Semantic model not selected correctly, or tables have no data | Re-open the report, check the data source, confirm Gold tables have rows |
| Numbers don't match Gold tables | DirectQuery fallback is active, or wrong table selected | Check for SQL endpoint views; simplify the model |
| App shows old data after restart | Environment variables not updated, or old dataset still referenced | Double-check App Service config; confirm the correct `FABRIC_DATASET_ID` |
| Direct Lake fallback warning | RLS on SQL endpoint, or SQL views as sources | Remove views; move RLS to the semantic model layer instead |
