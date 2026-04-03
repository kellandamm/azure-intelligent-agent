# Microsoft Fabric Setup — Strict Step-by-Step Guide

This guide provides exact setup steps for the Fabric demo using a Bronze, Silver, and Gold pattern, with notebook source files stored in the repository and linked as raw files instead of pasting notebook code into the documentation.[web:259][web:263]

## Prerequisites

1. Confirm you have a Fabric-capable tenant and a workspace with Fabric capacity or trial enabled.
2. Confirm you can create Lakehouse, Notebook, Pipeline, and Semantic Model items in the target workspace.
3. Confirm the notebook source files are committed to the repository under `notebooks/`.
4. Prepare the raw GitHub URLs for these files:
- `notebooks/01_bronze_seed_demo_data.py`
- `notebooks/02_silver_transform.py`
- `notebooks/03_gold_aggregate.py`
- `notebooks/04_validate_gold.py` 

## Step 1: Create the workspace

1. Open the Fabric portal.
2. Go to **Workspaces**.
3. Select **New workspace**.
4. Enter a name such as `AgentDemo-Fabric`.
5. Assign Fabric capacity if prompted.
6. Open the workspace after it is created.

## Step 2: Create the Lakehouses

Create three Lakehouses in the same workspace.

### Bronze Lakehouse

1. In the workspace, select **New item**.
2. Select **Lakehouse**.
3. Name it `BronzeLakehouse`.
4. Select **Create**.

### Silver Lakehouse

1. Select **New item**.
2. Select **Lakehouse**.
3. Name it `SilverLakehouse`.
4. Select **Create**.

### Gold Lakehouse

1. Select **New item**.
2. Select **Lakehouse**.
3. Name it `GoldLakehouse`.
4. Select **Create**.
## Step 3: Create the notebooks

Create four notebooks in the workspace.

1. Select **New item**.
2. Select **Notebook**.
3. Create these notebooks one by one:
- `01 Bronze Seed Demo Data`
- `02 Silver Transform`
- `03 Gold Aggregate`
- `04 Validate Gold`

Repeat until all four exist.

## Step 4: Load notebook code from repository files

Use repository-linked source files instead of pasting notebook code from the documentation page.

### Option A: Paste from raw GitHub file

For each notebook:

1. Open the notebook in Fabric.
2. Open the matching raw GitHub URL in another browser tab.
3. Copy the notebook source.
4. Paste it into the Fabric notebook.
5. Save the notebook.

This keeps the docs small and makes the repo the source of truth.[web:263]

### Option B: Bootstrap from a small loader cell

If you prefer, create a single loader cell that pulls the repo file directly.

Example pattern:

```python
import requests
code = requests.get("https://raw.githubusercontent.com/<org>/<repo>/<branch>/notebooks/01_bronze_seed_demo_data.py", timeout=60).text
exec(code)
```

This pattern is commonly used to execute code from GitHub-hosted source files in Fabric notebooks.[web:263]

## Step 5: Attach the correct default Lakehouse to each notebook

Each notebook should run with the correct Lakehouse context.

### Bronze notebook

1. Open `01 Bronze Seed Demo Data`.
2. In the notebook Lakehouse selector, attach `BronzeLakehouse` as the default Lakehouse.
3. Save the notebook.

### Silver notebook

1. Open `02 Silver Transform`.
2. Attach `SilverLakehouse` as the default Lakehouse.
3. Save the notebook.

### Gold notebook

1. Open `03 Gold Aggregate`.
2. Attach `GoldLakehouse` as the default Lakehouse, or attach the target Gold workspace item you want to write into.
3. Save the notebook.

### Validation notebook

1. Open `04 Validate Gold`.
2. Attach `GoldLakehouse` as the default Lakehouse.
3. Save the notebook.

Fabric notebooks support explicit lakehouse association and item-scoped execution metadata.[web:269]

## Step 6: Run the Bronze notebook

1. Open `01 Bronze Seed Demo Data`.
2. Select **Run all**.
3. Wait for completion.
4. Open `BronzeLakehouse`.
5. Verify these raw tables exist:
- `bronze_geography_raw`
- `bronze_categories_raw`
- `bronze_products_raw`
- `bronze_customers_raw`
- `bronze_orders_raw`
- `bronze_order_items_raw`
- `bronze_opportunities_raw`
- `bronze_customer_interactions_raw`
- `bronze_support_tickets_raw`
- `bronze_customer_metrics_raw`
- `bronze_inventory_snapshots_raw`
- `bronze_demo_metadata`

## Step 7: Run the Silver notebook

1. Open `02 Silver Transform`.
2. Select **Run all**.
3. Wait for completion.
4. Open `SilverLakehouse`.
5. Verify these tables exist:
- `dim_date`
- `dim_geography`
- `dim_category`
- `dim_product`
- `dim_customer`
- `fact_orders`
- `fact_order_items`
- `fact_opportunities`
- `fact_customer_interactions`
- `fact_support_tickets`
- `fact_customer_metrics`
- `fact_product_inventory`

## Step 8: Run the Gold notebook

1. Open `03 Gold Aggregate`.
2. Select **Run all**.
3. Wait for completion.
4. Open `GoldLakehouse`.
5. Verify these tables exist:
- `gold_customer_360`
- `gold_product_performance`
- `gold_sales_by_category`
- `gold_sales_time_series`
- `gold_geographic_sales`
- `gold_sales_pipeline`
- `gold_customer_rfm`
- `gold_support_metrics`
- `metadata_catalog`

## Step 9: Run the validation notebook

1. Open `04 Validate Gold`.
2. Select **Run all**.
3. Wait for completion.
4. Verify the table `gold_validation_results` exists.
5. Confirm all checks show `PASS`.

If any check fails, fix the upstream notebook and rerun Silver, Gold, and validation.

## Step 10: Create the semantic model

Once the Gold tables are ready, create a semantic model from the Gold Lakehouse.

1. Open `GoldLakehouse`.
2. Select **New semantic model**.
3. Select the Gold tables you want to include.
4. Select **Confirm**.
5. Open the model and define any required relationships or measures.

Fabric can generate a Direct Lake semantic model from Lakehouse tables directly in the workspace.

## Step 11: Create the pipeline

1. In the workspace, select **New item**.
2. Select **Pipeline**.
3. Name it `Medallion_Refresh`.
4. Open the pipeline canvas.

Add these activities in order:

1. **Notebook** activity named `Run Silver`.
2. **Notebook** activity named `Run Gold`.
3. **Notebook** activity named `Validate Gold`.
4. **Semantic model refresh** activity named `Refresh Semantic Model`.
5. Optional notification or alert step named `Notify Outcome`.

## Step 12: Configure notebook activities in the pipeline

For each Notebook activity:

1. Select the activity.
2. Choose the matching notebook.
3. Save the activity.

Set the dependency chain:

- `Run Gold` depends on `Run Silver` success.
- `Validate Gold` depends on `Run Gold` success.
- `Refresh Semantic Model` depends on `Validate Gold` success.
- `Notify Outcome` depends on final success or failure behavior you choose.

## Step 13: Configure semantic model refresh

1. Add **Semantic model refresh** to the pipeline.
2. Select the workspace that contains the semantic model.
3. Select the semantic model created from `GoldLakehouse`.
4. Leave **Wait on completion** enabled unless you have a reason not to.
5. Save the activity.

Fabric supports a dedicated semantic model refresh activity in pipelines, including workspace and dataset selection plus wait-on-completion behavior.

## Step 14: Test the pipeline

1. Run `Medallion_Refresh` manually.
2. Watch each activity complete in sequence.
3. Verify semantic model refresh completes after validation.
4. Open the semantic model or report and confirm data is fresh.

## Step 15: Optional report creation

1. Open the semantic model.
2. Select **Create report** or **Auto-create a report** if available.
3. Validate visuals using Gold tables such as customer 360, sales trends, pipeline, and geography outputs.

## Step 16: Recommended documentation update

Update `docs/FABRIC_DEPLOYMENT.md` so it:

- Explains the Bronze, Silver, Gold pattern.
- Lists the exact Fabric items to create.
- References notebook source files in the repo.
- Uses raw GitHub links instead of pasted notebook bodies.
- Includes the step-by-step setup and execution order.
- Includes pipeline and semantic model steps.

## Raw file section to paste into repo docs

```text
Notebook source files:
- notebooks/01_bronze_seed_demo_data.py
- notebooks/02_silver_transform.py
- notebooks/03_gold_aggregate.py
- notebooks/04_validate_gold.py

Raw URLs:
- https://raw.githubusercontent.com/<org>/<repo>/<branch>/notebooks/01_bronze_seed_demo_data.py
- https://raw.githubusercontent.com/<org>/<repo>/<branch>/notebooks/02_silver_transform.py
- https://raw.githubusercontent.com/<org>/<repo>/<branch>/notebooks/03_gold_aggregate.py
- https://raw.githubusercontent.com/<org>/<repo>/<branch>/notebooks/04_validate_gold.py
```

## Expected end state

At the end of setup, you should have:

- A Fabric workspace.
- Bronze, Silver, and Gold Lakehouses.
- Four notebooks.
- A `Medallion_Refresh` pipeline.
- A semantic model built from Gold tables.
- A demo flow that can be run manually or through the admin-triggered pipeline.
