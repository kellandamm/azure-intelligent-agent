# Synthetic Data Setup

Sets up an Azure SQL database with realistic demo data and an optional Azure Function that adds new records daily. Use this when you need sample data for demos or development.

---

## Prerequisites

- Azure SQL Database deployed (via main Bicep template)
- Python 3.9+ with ODBC Driver 18 installed locally
- Azure CLI logged in with SQL database access
- PowerShell 7.0+ (for the helper scripts)

---

## Deploy

### Option A: As part of complete deployment

```powershell
# From repo root
.\scripts\deploy-complete.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -DeployFabric `
    -GenerateInitialData
```

### Option B: Standalone (database only, no Azure Function)

```powershell
$env:SQL_SERVER   = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"

.\fabric\scripts\setup-database.ps1 -GenerateData
```

### Option C: Manual

```powershell
$env:SQL_SERVER   = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"

cd fabric\database
pip install -r requirements.txt

python deploy_schema.py          # creates tables and seeds categories
python generate_initial_data.py  # generates products, customers, orders
python view_tables.py            # verify results
```

---

## Grant the Azure Function SQL access

After deploying the function, grant its managed identity database access (replace with your actual function app name):

```sql
-- Azure Portal → SQL Database → Query Editor
CREATE USER [func-fabric-myagents] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [func-fabric-myagents];
ALTER ROLE db_datawriter ADD MEMBER [func-fabric-myagents];
```

---

## Database Schema

`deploy_schema.py` runs `schema.sql` which drops and recreates all tables — safe to re-run.

### Tables

#### Categories (seeded, not generated)
| Column | Type |
|--------|------|
| CategoryID | int PK |
| CategoryName | nvarchar(100) |
| Description | nvarchar(500) |

Pre-seeded: Electronics, Clothing, Home & Garden, Sports & Outdoors, Books, Toys & Games, Health & Beauty, Food & Beverage, Automotive, Office Supplies

#### Products
| Column | Type |
|--------|------|
| ProductID | int PK |
| ProductName | nvarchar(200) |
| CategoryID | int FK |
| Price | decimal(10,2) |
| StockQuantity | int |
| Description | nvarchar(1000) |
| SKU | nvarchar(50) unique |

#### Customers
| Column | Type |
|--------|------|
| CustomerID | int PK |
| FirstName / LastName | nvarchar(100) |
| Email | nvarchar(255) unique |
| PhoneNumber | nvarchar(20) |
| Address, City, State, ZipCode | nvarchar |
| Country | nvarchar(100) default 'USA' |
| CustomerSince | datetime2 |

#### Orders
| Column | Type |
|--------|------|
| OrderID | int PK |
| CustomerID | int FK |
| OrderDate / ShippedDate | datetime2 |
| OrderStatus | nvarchar(50) — Pending/Processing/Shipped/Delivered/Cancelled |
| TotalAmount | decimal(12,2) |
| ShippingAddress, ShippingCity, ShippingState, ShippingZipCode | nvarchar |
| PaymentMethod | nvarchar(50) |

#### OrderItems
| Column | Type |
|--------|------|
| OrderItemID | int PK |
| OrderID | int FK |
| ProductID | int FK |
| Quantity | int |
| UnitPrice | decimal(10,2) |
| Discount | decimal(5,2) |
| LineTotal | computed (persisted) |

---

## Customizing data volumes

Edit the constants at the top of `fabric/database/generate_initial_data.py`:

```python
NUM_PRODUCTS  = 100   # default
NUM_CUSTOMERS = 200   # default
NUM_ORDERS    = 300   # default
```

Default run generates approximately: **100 products / 200 customers / 300 orders / 600+ order items**

---

## Azure Function (daily data generation)

The function `daily_data_generator` in `fabric/function/function_app.py` runs on a timer trigger — by default every day at midnight UTC (`0 0 0 * * *`).

### Change the schedule

Edit `fabric/function/function_app.py`:

```python
@app.timer_trigger(
    schedule="0 0 * * * *",   # every hour  (was: "0 0 0 * * *" = daily midnight)
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=True
)
def daily_data_generator(myTimer: func.TimerRequest) -> None:
```

**Cron format:** `seconds minutes hours day month dayOfWeek`

| Schedule | Expression |
|----------|-----------|
| Daily at midnight | `0 0 0 * * *` |
| Every hour | `0 0 * * * *` |
| Every 5 minutes | `0 */5 * * * *` |
| Weekdays at 9am | `0 0 9 * * 1-5` |

### Monitor the function

```powershell
# Tail live logs
az functionapp log tail -g rg-myagents-prod -n func-fabric-myagents

# Trigger manually
az functionapp function invoke `
    -g rg-myagents-prod `
    -n func-fabric-myagents `
    --function-name daily_data_generator

# Disable / enable
az functionapp function disable -g rg-myagents-prod -n func-fabric-myagents --function-name daily_data_generator
az functionapp function enable  -g rg-myagents-prod -n func-fabric-myagents --function-name daily_data_generator
```

---

## Verify data

```powershell
cd fabric\database
python test_connection.py   # confirm connectivity
python view_tables.py       # show row counts per table
```

Expected output after a default run:

```
Categories:   10
Products:     100
Customers:    200
Orders:       300
Order Items:  600+
```

---

## Troubleshooting

**`pyodbc.Error: Can't open lib 'ODBC Driver 18 for SQL Server'`**
Install the driver: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

**`Login failed for user '<token-identified principal>'`**
```powershell
az login   # re-authenticate
# Then run in SQL Query Editor:
# CREATE USER [your-email@domain.com] FROM EXTERNAL PROVIDER;
# ALTER ROLE db_owner ADD MEMBER [your-email@domain.com];
```

**`There is already an object named 'Categories' in the database`**
Re-run `deploy_schema.py` — `schema.sql` drops all tables before recreating them, so this shouldn't happen. If it does, the script is running against an unexpected schema; check your `SQL_SERVER` / `SQL_DATABASE` env vars.

**Function logs show `Login failed for user 'NT AUTHORITY\ANONYMOUS LOGON'`**
The function's managed identity hasn't been granted SQL access. Run the `CREATE USER` / `ALTER ROLE` commands from the [Grant SQL access](#grant-the-azure-function-sql-access) section above.

**`ModuleNotFoundError: No module named 'pyodbc'`**
```powershell
cd fabric\database && pip install -r requirements.txt
```
