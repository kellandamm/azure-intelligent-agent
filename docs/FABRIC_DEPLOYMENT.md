# Microsoft Fabric Setup — Mirroring, Medallion Architecture & Pipelines

Sets up Microsoft Fabric to mirror your Azure SQL database and build a medallion analytics architecture that powers the AI agents and dashboards.

> **No Fabric?** Skip this guide entirely. Run `app/Fabric/synthetic_data.sql` against Azure SQL and the app works without any Fabric configuration. See [QUICK_START.md Phase 6](../docs/QUICK_START.md#phase-6--fabric).

---

## Architecture Overview

```
Azure SQL DB  ──Mirror──▶  Fabric OneLake (Bronze — live replica)
                                    │
                             Notebooks / Dataflows
                                    │
                           Fabric Lakehouse Silver  (cleansed)
                                    │
                             Notebooks / Pipeline
                                    │
                           Fabric Lakehouse Gold    (analytics-ready)
                                    │
                     App AI Agents + Analytics Dashboard
                      (via Fabric SQL Analytics Endpoint)
```

**Bronze** = raw mirrored tables from Azure SQL (automatic, no code)
**Silver** = cleansed, standardised views
**Gold**   = pre-aggregated tables matching the schema expected by the app's agent tools and API routes

---

## Prerequisites

- Microsoft Fabric capacity assigned to your tenant (F2 or higher, or a Fabric trial)
- Azure SQL database deployed and seeded (Phase 2 + Phase 5 of QUICK_START.md complete)
- Azure CLI logged in with Contributor access to the resource group
- Fabric workspace admin rights

---

## Phase 1 — Create a Fabric Workspace

1. Navigate to [app.fabric.microsoft.com](https://app.fabric.microsoft.com)
2. **Workspaces** (left sidebar) → **+ New workspace**
3. Name: `AgentDemo-Analytics` (or your preference)
4. **Advanced** → assign your Fabric capacity (F2+)
5. Click **Apply**

Copy the **Workspace ID** for use in Phase 5:
 copy the string after groups in the browser URL: https://app.fabric.microsoft.com/groups/59e21e68-643e-4497-8601-9asdfasdfasdf/list?experience=fabric-developer
    **WORKSPACE ID** = 59e21e68-643e-4497-8601-9asdfasdfasdf

---

## Phase 2 — Prepare Azure SQL for Mirroring

Fabric mirroring uses SQL Change Tracking to replicate rows as they change.
Run the following in **Azure Portal → SQL Database → Query Editor**
(authenticate with your Azure AD admin account):

```sql
-- Enable change tracking on the database (7-day retention)
ALTER DATABASE CURRENT
    SET CHANGE_TRACKING = ON
    (CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

-- Enable per-table tracking on the tables you want mirrored
ALTER TABLE dbo.Categories  ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.Products    ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.Customers   ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.Orders      ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.OrderItems  ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.CustomerDim ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.ProductDim  ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
ALTER TABLE dbo.SalesFact   ENABLE CHANGE_TRACKING WITH (TRACK_COLUMNS_UPDATED = ON);
```

> Existing gold tables (`gold_*`) do not need change tracking — they will be rebuilt by the Gold pipeline.

---

## Phase 3 — Create the Mirrored Database (Bronze)

1. In your Fabric workspace → **+ New item** → **Mirrored Azure SQL Database**
2. Click **+ New connection** and enter:
   - **Server**: `<your-server>.database.windows.net`
   - **Database**: `aiagentsdb`
   - **Authentication kind**: Organisational account (Azure AD interactive) — recommended for initial setup
3. Click **Connect**, then select these tables to mirror:
   - `dbo.Categories`, `dbo.Products`, `dbo.Customers`
   - `dbo.Orders`, `dbo.OrderItems`
   - `dbo.CustomerDim`, `dbo.ProductDim`, `dbo.SalesFact`
4. Click **Mirror database**

**What happens next:**
Fabric performs an initial snapshot (5–15 min depending on table size), then continuously replicates changes. Monitor progress under the **Mirroring** tab → **Monitor**.

All mirrored status should show **Running** before proceeding.

### Grant Fabric read access to Azure SQL

Fabric creates a service principal for the mirror. Its name appears in the connection details.
Run in Query Editor:

```sql
-- Replace <fabric-spn-name> with the name shown in the Fabric mirror connection settings
CREATE USER [<fabric-spn-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [<fabric-spn-name>];
```

---

## Phase 4 — Create the Silver and Gold Lakehouses

### Create two lakehouses

In your workspace → **+ New item** → **Lakehouse** (repeat twice):

| Name | Purpose |
|------|---------|
| `AgentDemo_Silver` | Cleansed, standardised tables |
| `AgentDemo_Gold` | Pre-aggregated analytics tables queried by the app |

---

## Phase 5 — Silver Layer — Cleansing Notebook

1. Workspace → **+ New item** → **Notebook**
2. Name: `Silver_Transform`
3. Click **Add lakehouse** → select `AgentDemo_Silver` → **Add**

Paste the following cells and **Run all**:

```python
# Cell 1 — Silver: Customers
from pyspark.sql.functions import col, upper, trim, coalesce, lit

mirrored_db = "<your-mirrored-db-name>"   # name of the Mirrored Database item in Fabric

customers = spark.sql(f"SELECT * FROM {mirrored_db}.dbo.Customers")
customers_silver = (
    customers
    .withColumn("State",   upper(trim(col("State"))))
    .withColumn("Country", coalesce(col("Country"), lit("USA")))
    .withColumn("Email",   trim(col("Email")))
    .dropDuplicates(["Email"])
)
customers_silver.write.mode("overwrite").saveAsTable("silver_customers")
print(f"silver_customers: {customers_silver.count()} rows")
```

```python
# Cell 2 — Silver: Orders
orders = spark.sql(f"SELECT * FROM {mirrored_db}.dbo.Orders WHERE OrderStatus != 'Cancelled'")
orders.write.mode("overwrite").saveAsTable("silver_orders")
print(f"silver_orders: {orders.count()} rows")
```

```python
# Cell 3 — Silver: OrderItems
order_items = spark.sql(f"SELECT * FROM {mirrored_db}.dbo.OrderItems")
order_items.write.mode("overwrite").saveAsTable("silver_order_items")
print(f"silver_order_items: {order_items.count()} rows")
```

```python
# Cell 4 — Silver: Products
products = spark.sql(f"""
    SELECT p.*, c.CategoryName
    FROM {mirrored_db}.dbo.Products p
    LEFT JOIN {mirrored_db}.dbo.Categories c ON p.CategoryID = c.CategoryID
    WHERE p.IsActive = 1
""")
products.write.mode("overwrite").saveAsTable("silver_products")
print(f"silver_products: {products.count()} rows")
```

---

## Phase 6 — Gold Layer — Aggregation Notebook

1. Workspace → **+ New item** → **Notebook**
2. Name: `Gold_Aggregate`
3. Click **Add lakehouse** → select `AgentDemo_Gold` → **Add**

Paste each cell and **Run all**:

```python
# Cell 1 — Gold: Monthly Sales Time Series
spark.sql("""
CREATE OR REPLACE TABLE gold_sales_time_series AS
SELECT
    DATE_TRUNC('month', o.OrderDate)              AS OrderDate,
    YEAR(o.OrderDate)                              AS year,
    QUARTER(o.OrderDate)                           AS quarter,
    MONTH(o.OrderDate)                             AS month,
    DATE_FORMAT(o.OrderDate, 'MMMM')               AS month_name,
    COUNT(DISTINCT o.OrderID)                      AS daily_orders,
    ROUND(SUM(oi.LineTotal), 2)                    AS daily_revenue,
    ROUND(SUM(oi.LineTotal) / COUNT(DISTINCT o.OrderID), 6) AS avg_order_value,
    COUNT(DISTINCT o.CustomerID)                   AS unique_customers
FROM silver_orders o
JOIN silver_order_items oi ON o.OrderID = oi.OrderID
GROUP BY 1, 2, 3, 4, 5
ORDER BY 1
""")
print("gold_sales_time_series created")
```

```python
# Cell 2 — Gold: Customer 360
spark.sql("""
CREATE OR REPLACE TABLE gold_customer_360 AS
SELECT
    c.CustomerID,
    c.FirstName,
    c.LastName,
    c.Email,
    c.City,
    c.State,
    c.Country,
    c.CustomerSince,
    COUNT(DISTINCT o.OrderID)                                         AS total_orders,
    ROUND(SUM(oi.LineTotal), 2)                                       AS lifetime_value,
    ROUND(SUM(oi.LineTotal) / NULLIF(COUNT(DISTINCT o.OrderID), 0), 6) AS avg_order_value,
    MAX(o.OrderDate)                                                  AS last_order_date,
    MIN(o.OrderDate)                                                  AS first_order_date,
    AVG(DATEDIFF(o.ShippedDate, o.OrderDate))                        AS avg_delivery_days,
    DATEDIFF(CURRENT_DATE, c.CustomerSince)                          AS customer_tenure_days,
    DATEDIFF(CURRENT_DATE, MAX(o.OrderDate))                         AS recency_days,
    CASE
        WHEN SUM(oi.LineTotal) >= 10000 THEN 'Premium'
        WHEN SUM(oi.LineTotal) >= 5000  THEN 'Standard'
        WHEN COUNT(DISTINCT o.OrderID) = 1 THEN 'New'
        ELSE 'At Risk'
    END AS customer_segment,
    CASE
        WHEN DATEDIFF(CURRENT_DATE, MAX(o.OrderDate)) > 365 THEN 'Churned'
        WHEN DATEDIFF(CURRENT_DATE, MAX(o.OrderDate)) > 180 THEN 'Inactive'
        ELSE 'Active'
    END AS customer_status
FROM silver_customers c
LEFT JOIN silver_orders o      ON c.CustomerID = o.CustomerID
LEFT JOIN silver_order_items oi ON o.OrderID   = oi.OrderID
GROUP BY 1,2,3,4,5,6,7,8
""")
print("gold_customer_360 created")
```

```python
# Cell 3 — Gold: Sales Performance KPIs
spark.sql("""
CREATE OR REPLACE TABLE gold_sales_performance AS
SELECT 'Total Revenue'     AS metric_name, ROUND(SUM(LineTotal), 2) AS metric_value FROM silver_order_items
UNION ALL
SELECT 'Total Orders',     CAST(COUNT(DISTINCT OrderID) AS DOUBLE)  FROM silver_orders
UNION ALL
SELECT 'Avg Order Value',  ROUND(AVG(TotalAmount), 2)               FROM silver_orders
UNION ALL
SELECT 'Win Rate',
    ROUND(COUNT(CASE WHEN OrderStatus = 'Delivered' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 2)
    FROM silver_orders
UNION ALL
SELECT 'Conversion Rate',
    ROUND(COUNT(DISTINCT CustomerID) * 100.0 / NULLIF((SELECT COUNT(*) FROM silver_customers), 0), 2)
    FROM silver_orders
UNION ALL
SELECT 'Avg Delivery Days',
    ROUND(AVG(DATEDIFF(ShippedDate, OrderDate)), 2)
    FROM silver_orders WHERE ShippedDate IS NOT NULL
""")
print("gold_sales_performance created")
```

```python
# Cell 4 — Gold: Geographic Sales
spark.sql("""
CREATE OR REPLACE TABLE gold_geographic_sales AS
SELECT
    c.State,
    c.City,
    YEAR(o.OrderDate)    AS year,
    QUARTER(o.OrderDate) AS quarter,
    MONTH(o.OrderDate)   AS month,
    COUNT(DISTINCT o.OrderID)   AS order_count,
    ROUND(SUM(oi.LineTotal), 2) AS total_revenue,
    COUNT(DISTINCT o.CustomerID) AS unique_customers
FROM silver_customers c
JOIN silver_orders      o  ON c.CustomerID = o.CustomerID
JOIN silver_order_items oi ON o.OrderID    = oi.OrderID
GROUP BY 1, 2, 3, 4, 5
""")
print("gold_geographic_sales created")
```

```python
# Cell 5 — Gold: Cohort Analysis
spark.sql("""
CREATE OR REPLACE TABLE gold_cohort_analysis AS
WITH cohorts AS (
    SELECT
        CustomerID,
        DATE_FORMAT(MIN(OrderDate), 'yyyy-MM') AS cohort_month,
        COUNT(DISTINCT OrderID)                AS order_count,
        SUM(total_revenue)                     AS cohort_revenue
    FROM (
        SELECT o.CustomerID, o.OrderID, o.OrderDate, SUM(oi.LineTotal) AS total_revenue
        FROM silver_orders o
        JOIN silver_order_items oi ON o.OrderID = oi.OrderID
        GROUP BY o.CustomerID, o.OrderID, o.OrderDate
    ) t
    GROUP BY CustomerID
)
SELECT
    cohort_month,
    COUNT(*)                               AS cohort_size,
    ROUND(SUM(cohort_revenue), 2)          AS cohort_revenue,
    ROUND(COUNT(CASE WHEN order_count > 1 THEN 1 END) * 100.0 / COUNT(*), 2) AS retention_rate
FROM cohorts
GROUP BY cohort_month
ORDER BY cohort_month DESC
""")
print("gold_cohort_analysis created")
```

```python
# Cell 6 — Gold: Inventory Analysis
spark.sql("""
CREATE OR REPLACE TABLE gold_inventory_analysis AS
SELECT
    cat.CategoryName     AS category,
    p.ProductName,
    p.StockQuantity      AS current_stock,
    COALESCE(sold.units_sold, 0) AS units_sold_30d,
    CASE
        WHEN p.StockQuantity = 0 THEN 'Out of Stock'
        WHEN p.StockQuantity < 10 THEN 'Low Stock'
        ELSE 'In Stock'
    END AS stock_status,
    ROUND(p.Price, 2) AS unit_price,
    ROUND(p.Price * p.StockQuantity, 2) AS inventory_value
FROM silver_products p
JOIN silver_orders o1 ON 1=0  -- placeholder join structure
LEFT JOIN (
    SELECT oi.ProductID, SUM(oi.Quantity) AS units_sold
    FROM silver_order_items oi
    JOIN silver_orders o ON oi.OrderID = o.OrderID
    WHERE o.OrderDate >= DATE_SUB(CURRENT_DATE, 30)
    GROUP BY oi.ProductID
) sold ON p.ProductID = sold.ProductID
JOIN (SELECT CategoryID, CategoryName FROM silver_products GROUP BY CategoryID, CategoryName) cat
    ON p.CategoryID = cat.CategoryID
""")
print("gold_inventory_analysis created")
```

> **Note:** The inventory notebook cell above uses a simplified join — adjust to match the actual `Categories` table structure in your Silver lakehouse.

---

## Phase 7 — Build the Refresh Pipeline

1. Workspace → **+ New item** → **Data pipeline**
2. Name: `Medallion_Refresh`

### Add activities

| # | Type | Name | Notebook |
|---|------|------|----------|
| 1 | Notebook | Run Silver | `Silver_Transform` |
| 2 | Notebook | Run Gold | `Gold_Aggregate` |

**Set dependency:** Click the green arrow on the `Run Silver` activity → drag it to `Run Gold`. This ensures Gold only runs after Silver completes successfully.

### Schedule the pipeline

1. Click **Schedule** in the pipeline toolbar → **+ New schedule**
2. Set: **Daily**, **Start time = 02:00 UTC**
3. Click **Apply**

### Test manually

Click **Run** → **Run now**. Monitor the run under the **Pipeline runs** tab in the workspace.

---

## Phase 8 — Connect the App to Fabric Gold

### Get the SQL Analytics Endpoint

1. Open the `AgentDemo_Gold` lakehouse in Fabric
2. Click the **SQL analytics endpoint** button in the top ribbon (or switch views in the top-right dropdown)
3. Copy the **Server** value — it looks like:
   `<workspace-name>-<guid>.datawarehouse.fabric.microsoft.com`

### Set App Service environment variables

```powershell
az webapp config appsettings set `
  --name <your-app-name> `
  --resource-group reg-admin `
  --settings `
    FABRIC_SQL_SERVER="<endpoint>.datawarehouse.fabric.microsoft.com" `
    FABRIC_SQL_DATABASE="AgentDemo_Gold" `
    FABRIC_WORKSPACE_ID="<workspace-guid>"
```

Or set them in **Azure Portal → App Service → Settings → Environment variables**.

### Restart the app

```powershell
az webapp restart --name <your-app-name> --resource-group reg-admin
```

Tail startup logs to confirm the Fabric connection initialises:

```powershell
az webapp log tail --name <your-app-name> --resource-group reg-admin
```

The AI agents and all analytics dashboards will now query Fabric Gold tables.

---

## Verification

### Check mirroring status

Fabric workspace → Mirrored database → **Monitor** tab
All tables should show **Running** with a recent sync timestamp.

### Check Gold tables exist

`AgentDemo_Gold` lakehouse → **Tables** pane
Expected tables: `gold_sales_time_series`, `gold_customer_360`, `gold_sales_performance`, `gold_geographic_sales`, `gold_cohort_analysis`, `gold_inventory_analysis`

### Verify app is hitting Fabric

In the app startup log, look for:
```
Fabric connection string set — agents will query Fabric
```

Or make a chat request asking about sales data and check that the agent returns data.

### Run the smoke test

```bash
python tests/smoke_test.py --url https://<app-name>.azurewebsites.net --skip-auth
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Mirroring stuck at "Initializing" | Run the `ALTER DATABASE ... SET CHANGE_TRACKING = ON` command in SQL Query Editor. |
| Mirror shows "Pending" for individual tables | Ensure each table has a primary key — Fabric mirroring requires PKs. |
| Permission denied creating mirror | Grant the Fabric service principal `db_datareader` on Azure SQL (see Phase 3). |
| Gold tables empty after pipeline run | Run `Gold_Aggregate` notebook manually; check the **Spark logs** for errors. |
| App still querying Azure SQL after env var change | Restart the app: `az webapp restart`. Check `FABRIC_SQL_SERVER` is set and not empty. |
| SQL analytics endpoint unreachable | Fabric capacity may be paused. Resume it in **Fabric Admin → Capacity settings**. |
| `Login failed` for Fabric SQL endpoint | The App Service managed identity needs access. In Fabric workspace → Access, add the managed identity as **Contributor**. |
| PySpark errors in Silver notebook | Check the mirrored DB name in the `mirrored_db` variable matches the item name in your workspace exactly. |

---

## Reference: Gold Table Schema

The following tables are expected by the app's API routes and AI agent tools.
They are created by the `Gold_Aggregate` notebook above.

| Table | Used by |
|-------|---------|
| `gold_sales_time_series` | Analytics timeseries, sales metrics, goals |
| `gold_customer_360` | Deals endpoint, deal detail, agent tools |
| `gold_upsell_opportunities` | Deals endpoint, deal detail |
| `gold_sales_performance` | Sales metrics win rate, predictive insights |
| `gold_geographic_sales` | Agent geographic queries |
| `gold_cohort_analysis` | Analytics cohort dashboard |
| `gold_inventory_analysis` | Agent inventory queries |

> `gold_upsell_opportunities` is not generated by the notebooks above — it requires an ML scoring model or can be seeded manually. For demos, the `synthetic_data.sql` script includes 15 sample rows.