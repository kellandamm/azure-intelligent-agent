# Fabric / Database Quick Reference

## Files in this directory

| File | Purpose |
|------|---------|
| `synthetic_data.sql` | **Recommended** — Complete synthetic dataset for all tables. Run once in SQL Query Editor. Safe to re-run. |
| `rls_security_policies.sql` | Row-Level Security schema, predicate functions, and session-context stored procedures. Run after `auth_schema.sql`. |
| `auth_schema.sql` | Authentication tables (Users, Roles, Permissions) and stored procedures. Run first. |
| `schema.sql` | Original operational table schema (Categories, Products, Customers, Orders, OrderItems). |
| `generate_initial_data.py` | Python script to generate larger volumes of synthetic data (100+ products, 200+ customers). |
| `deploy_schema.py` | Deploys `schema.sql` via Python + pyodbc. |
| `function_app.py` | Azure Function that adds new records daily on a timer trigger. |
| `view_tables.py` | Prints row counts for all tables — useful for verification. |
| `test_connection.py` | Tests ODBC connectivity to Azure SQL. |
| `requirements.txt` | Python dependencies for the scripts above. |

---

## Quick Start — No Fabric Required

Load all synthetic data into Azure SQL in one step:

1. **Azure Portal → SQL Database → Query Editor** (sign in with Azure AD)
2. Paste and run `auth_schema.sql`
3. Paste and run `rls_security_policies.sql`
4. Paste and run `synthetic_data.sql`

Tables created by `synthetic_data.sql`:

| Layer | Tables |
|-------|--------|
| Operational | Categories, Products, Customers, Orders, OrderItems |
| Star schema | CustomerDim, ProductDim, SalesFact |
| Gold analytics | gold_sales_time_series, gold_geographic_sales, gold_customer_360, gold_inventory_analysis, gold_sales_performance, gold_shipping_performance, gold_support_metrics, gold_cohort_analysis, gold_upsell_opportunities |

No environment variables need to change — the app automatically uses the main SQL database
when `FABRIC_SQL_SERVER` is not set.

---

## Verify data loaded

```sql
-- Check all tables have rows
SELECT 'Categories'             , COUNT(*) FROM dbo.Categories             UNION ALL
SELECT 'Products'               , COUNT(*) FROM dbo.Products               UNION ALL
SELECT 'Customers'              , COUNT(*) FROM dbo.Customers              UNION ALL
SELECT 'Orders'                 , COUNT(*) FROM dbo.Orders                 UNION ALL
SELECT 'OrderItems'             , COUNT(*) FROM dbo.OrderItems             UNION ALL
SELECT 'gold_sales_time_series' , COUNT(*) FROM dbo.gold_sales_time_series UNION ALL
SELECT 'gold_customer_360'      , COUNT(*) FROM dbo.gold_customer_360      UNION ALL
SELECT 'gold_upsell_opportunities',COUNT(*) FROM dbo.gold_upsell_opportunities;
```

Expected results: 6–15 rows per operational table, 9–27 rows per gold table.

---

## Generate larger volumes (optional)

Use the Python scripts to generate hundreds of customers and orders:

```powershell
# Set connection details
$env:SQL_SERVER   = "your-server.database.windows.net"
$env:SQL_DATABASE = "aiagentsdb"

cd app/Fabric
pip install -r requirements.txt

python deploy_schema.py         # create tables
python generate_initial_data.py # 100 products / 200 customers / 300 orders
python view_tables.py           # verify row counts
```

Adjust volumes at the top of `generate_initial_data.py`:

```python
NUM_PRODUCTS  = 100   # default
NUM_CUSTOMERS = 200
NUM_ORDERS    = 300
```

---

## Full Fabric Setup (mirroring + medallion architecture)

For production use with Microsoft Fabric mirroring, Silver/Gold lakehouses, and a scheduled data pipeline, see the full guide:

**[docs/FABRIC_DEPLOYMENT.md](../../docs/FABRIC_DEPLOYMENT.md)**

---

## Useful SQL Queries

### Recent orders

```sql
SELECT TOP 10
    o.OrderID,
    c.FirstName + ' ' + c.LastName AS Customer,
    o.OrderDate, o.OrderStatus, o.TotalAmount
FROM dbo.Orders o
JOIN dbo.Customers c ON o.CustomerID = c.CustomerID
ORDER BY o.OrderDate DESC;
```

### Revenue by category

```sql
SELECT
    cat.CategoryName,
    COUNT(DISTINCT o.OrderID)  AS Orders,
    SUM(oi.Quantity)           AS UnitsSold,
    ROUND(SUM(oi.LineTotal),2) AS Revenue
FROM dbo.Categories cat
JOIN dbo.Products   p  ON cat.CategoryID = p.CategoryID
JOIN dbo.OrderItems oi ON p.ProductID    = oi.ProductID
JOIN dbo.Orders     o  ON oi.OrderID     = o.OrderID
GROUP BY cat.CategoryName
ORDER BY Revenue DESC;
```

### Top customers

```sql
SELECT TOP 10
    c.FirstName + ' ' + c.LastName AS Customer,
    COUNT(o.OrderID)               AS Orders,
    ROUND(SUM(o.TotalAmount), 2)   AS TotalSpent
FROM dbo.Customers c
JOIN dbo.Orders o ON c.CustomerID = o.CustomerID
GROUP BY c.CustomerID, c.FirstName, c.LastName
ORDER BY TotalSpent DESC;
```

### Gold table spot-check

```sql
-- Monthly revenue trend
SELECT TOP 6 OrderDate, daily_revenue, unique_customers
FROM dbo.gold_sales_time_series
ORDER BY OrderDate DESC;

-- Top upsell opportunities
SELECT TOP 5 c.FirstName + ' ' + c.LastName AS Customer,
       u.recommended_action, u.upsell_score
FROM dbo.gold_upsell_opportunities u
JOIN dbo.gold_customer_360 c ON u.CustomerID = c.CustomerID
ORDER BY u.upsell_score DESC;
```
