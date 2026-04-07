# Phase 8 — Semantic Model and Direct Lake

Use these steps to make sure the app reports are using Fabric Gold data.

## Step 1 — Confirm Gold tables are ready

Before building the semantic model, confirm these are true:

- The Gold notebook completed successfully.
- The validation notebook completed successfully.
- Your target Gold tables are present in the Fabric item you plan to use.
- The table names and column names are stable enough for reporting.

Recommended minimum check:

- `gold_customer360`
- `gold_productperformance`
- `goldsalesbycategory`
- `goldsalestimeseries`
- `goldsupportmetrics`

## Step 2 — Create the semantic model

Choose one of these entry points in Fabric:

### Option A — From the Lakehouse

1. Open the Gold Lakehouse.
2. In the ribbon, select **New semantic model**.
3. Enter a model name such as `AgentDemo_Gold_Model`.
4. Select only the curated Gold tables you want reports to use.
5. Click **Confirm**.

### Option B — From the SQL analytics endpoint or Warehouse

1. Open the SQL analytics endpoint for the Gold item, or open the Warehouse.
2. Go to **Reporting**.
3. Select **New semantic model**.
4. Enter the model name.
5. Select the curated Gold tables.
6. Click **Confirm**.

## Step 3 — Clean up the model in web modeling

Once the semantic model opens:

1. Check relationships between fact and dimension-style Gold tables.
2. Set correct data types and formats.
3. Mark your date table if you have one.
4. Create a few basic measures that match what the app reports need, for example:
   - Total Revenue
   - Total Orders
   - Average Order Value
   - Active Customers
5. Hide technical columns that should not appear in reports.
6. Save the semantic model.

## Step 4 — Keep it Direct Lake friendly

To maximize the chance that the model stays in Direct Lake mode:

1. Build the model over Fabric Gold tables, not random mixed sources.
2. Avoid SQL endpoint views when possible.
3. Avoid forcing row-level security only at the SQL analytics endpoint for these report tables.
4. Keep the model simple during first validation.
5. Do not add unsupported patterns until the baseline works.

Important note:

- Queries can fall back to DirectQuery when the semantic model uses SQL endpoint views or tables that enforce RLS in the SQL analytics endpoint.
- For testing, keep the first version of the report model as clean as possible.

## Step 5 — Create a simple validation report in Fabric or Power BI

Build a quick report against the new semantic model before touching the app.

Suggested visuals:

1. Revenue by month using `goldsalestimeseries`.
2. Revenue by category using `goldsalesbycategory`.
3. Customer count or value using `gold_customer360`.
4. Support KPI using `goldsupportmetrics`.

This gives you a fast sanity check that the semantic model is usable and the numbers look right.

## Step 6 — Verify the model is reading Fabric data

Use at least two checks:

### Check A — Update source data

1. Insert or update a known test record in the Azure SQL source.
2. Let mirroring and notebook refresh complete.
3. Re-open the report or refresh visuals.
4. Confirm the new value appears in the semantic model results.

### Check B — Compare against Gold tables

1. Query the Gold table directly in Fabric.
2. Compare the returned values with the report visuals.
3. Confirm the totals match.

If report totals match Gold totals, the model is reading the Fabric-prepared data path correctly.

## Step 7 — Connect the app to the Fabric reporting path

After the semantic model is validated:

1. Open the Gold Lakehouse or SQL analytics endpoint.
2. Copy the server/endpoint details you use for the app reporting connection.
3. Set the required App Service environment variables.
4. Restart the app.
5. Open the app and load the report pages.

If your app embeds Power BI/Fabric-backed reports, make sure the embedded report is published from the semantic model you just validated.

## Step 8 — Prove the app is not using the old SQL-only path

Use one of these practical tests:

### Test 1 — Fabric-only metric

1. Add a metric or measure that exists only in the Gold semantic model.
2. Publish the report.
3. Open the app.
4. Confirm the metric appears there.

### Test 2 — Controlled value change

1. Change a known value in source data.
2. Run mirror and Gold refresh.
3. Confirm the Fabric report updates.
4. Confirm the app shows the same updated value.

### Test 3 — Temporary app setting swap check

1. Record current app report values.
2. Point the app to the validated Fabric reporting settings.
3. Restart the app.
4. Confirm values now match the Fabric report exactly.

## Step 9 — Final pre-cutover checklist

Before calling this complete, confirm all of these:

- Gold refresh works.
- Semantic model saves successfully.
- Validation report works.
- Direct Lake is the intended mode.
- No unnecessary DirectQuery fallback patterns were introduced.
- The app report pages match the Fabric report values.
- Restarted app loads without reporting errors.

## Step 10 — Recommended first production rollout pattern

Use this rollout order:

1. Validate Gold tables.
2. Validate semantic model.
3. Validate standalone report.
4. Point non-production app to Fabric.
5. Compare values with expected Gold outputs.
6. Promote to production after signoff.
