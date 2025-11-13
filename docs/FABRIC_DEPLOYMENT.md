# 📊 Fabric Data Management - Deployment Guide

Complete guide for deploying and managing the Fabric synthetic data generation component.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Step-by-Step Deployment](#step-by-step-deployment)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Testing & Verification](#testing--verification)
- [Management](#management)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The **Fabric Data Management** component provides:

- **Synthetic data generation** for Azure SQL Database
- **Database schema management** (Categories, Products, Customers, Orders, OrderItems)
- **Azure Function** for automated ongoing data generation
- **Management tools** for viewing and testing database content

### When to Use Fabric

✅ **Use Fabric when:**
- You need realistic test data for demos
- You want automated data generation
- You're building a proof-of-concept
- You need sample data for development

❌ **Don't use Fabric when:**
- You have production data to migrate
- You need specific data formats
- You're deploying to production environments

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Azure SQL Database                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tables: Categories, Products, Customers,        │  │
│  │          Orders, OrderItems                      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────┬───────────────────┘
                  │                   │
         ┌────────▼────────┐  ┌──────▼──────────┐
         │  Web App        │  │  Azure Function  │
         │  (Main Agent)   │  │  (Data Gen)      │
         │                 │  │                  │
         │  - Query data   │  │  - Timer trigger │
         │  - Use in demos │  │  - Generate data │
         └─────────────────┘  └──────────────────┘
```

### Components

1. **Database Scripts** (`fabric/database/`)
   - `deploy_schema.py` - Deploy SQL schema
   - `generate_initial_data.py` - Create seed data
   - `view_tables.py` - View table contents
   - `view_schemas.py` - View schema details
   - `test_connection.py` - Test connectivity

2. **Azure Function** (`fabric/function/`)
   - `function_app.py` - Timer-triggered data generation
   - Runs every 5 minutes (configurable)
   - Uses managed identity for SQL access

3. **Deployment Scripts** (`fabric/scripts/`)
   - `setup-database.ps1` - Deploy schema and data
   - `deploy-fabric-function.ps1` - Deploy Azure Function

---

## ✅ Prerequisites

### Required

1. **Azure Resources**
   - Azure SQL Database (deployed via main template)
   - Azure CLI installed and logged in
   - Resource group created

2. **Local Development Tools**
   - Python 3.9+ installed
   - ODBC Driver 18 for SQL Server
   - PowerShell 7.0+

3. **Permissions**
   - Azure SQL Database access (Azure AD)
   - Contributor role on resource group
   - SQL Database permissions (CREATE USER, ALTER ROLE)

### Install ODBC Driver 18

#### Windows
```powershell
# Download and run installer from:
https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
```

#### macOS
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18
```

#### Linux (Ubuntu/Debian)
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | \
    sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Install Azure Functions Core Tools

#### Windows
```powershell
winget install Microsoft.Azure.FunctionsCoreTools
```

#### macOS
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

#### Linux
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

---

## 🚀 Deployment Options

### Option 1: Integrated Deployment (Recommended)

Deploy Fabric as part of complete deployment:

```powershell
cd scripts
.\deploy-complete.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -DeployFabric `
    -GenerateInitialData
```

**Advantages:**
- ✅ Everything in one command
- ✅ Automatic configuration
- ✅ Coordinated deployment

---

### Option 2: Standalone Deployment

Deploy Fabric separately after main deployment:

#### Step 1: Set Environment Variables
```powershell
$env:SQL_SERVER = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"
```

#### Step 2: Deploy Database Schema
```powershell
cd fabric\scripts
.\setup-database.ps1 -GenerateData
```

#### Step 3: Deploy Azure Function
```powershell
.\deploy-fabric-function.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -SqlServerName "sql-myagents-prod" `
    -SqlDatabaseName "sqldb-myagents-prod"
```

**Advantages:**
- ✅ Deploy only what you need
- ✅ Test database setup first
- ✅ Deploy function later

---

### Option 3: Manual Deployment

For maximum control:

#### 1. Install Python Dependencies
```powershell
cd fabric\database
pip install -r requirements.txt
```

#### 2. Deploy Schema
```powershell
$env:SQL_SERVER = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"

python deploy_schema.py
```

#### 3. Generate Data
```powershell
python generate_initial_data.py
```

#### 4. Verify
```powershell
python test_connection.py
python view_tables.py
```

---

## 📖 Step-by-Step Deployment

### Complete Walkthrough (Integrated Deployment)

#### 1. Ensure Prerequisites

```powershell
# Check Python
python --version  # Should be 3.9+

# Check Azure CLI
az --version
az account show

# Check ODBC Driver
# Windows: Control Panel → Administrative Tools → ODBC Data Sources
# macOS/Linux: odbcinst -q -d
```

#### 2. Deploy Main Infrastructure

If not already deployed:

```powershell
cd scripts
.\deploy-complete.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -Location "eastus2"
```

#### 3. Deploy Fabric

```powershell
# With initial data generation
.\deploy-complete.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -DeployFabric `
    -GenerateInitialData `
    -SkipInfrastructure `
    -SkipAppCode
```

#### 4. Grant Function SQL Access

Open Azure Portal:

1. Navigate to: **SQL Databases** → **your-database** → **Query Editor**
2. Authenticate with Azure AD
3. Run these commands:

```sql
-- Replace with your actual function app name from deployment output
CREATE USER [func-fabric-myagents] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [func-fabric-myagents];
ALTER ROLE db_datawriter ADD MEMBER [func-fabric-myagents];
```

#### 5. Verify Deployment

```powershell
# View table data
cd fabric\database
python view_tables.py

# Expected output:
# Categories: 10 records
# Products: ~50 records
# Customers: ~100 records
# Orders: ~200 records
# OrderItems: ~450 records
```

---

## 🗄️ Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐
│   Categories    │
│─────────────────│
│ CategoryID (PK) │      ┌──────────────────┐
│ CategoryName    │◄────┐│    Products       │
│ Description     │     ││──────────────────│
└─────────────────┘     ││ ProductID (PK)   │
                        ││ ProductName      │
                        ││ CategoryID (FK)  │───┐
┌─────────────────┐     ││ Price            │   │
│   Customers     │     ││ StockQuantity    │   │
│─────────────────│     │└──────────────────┘   │
│ CustomerID (PK) │     │                       │
│ FirstName       │     │                       │
│ LastName        │     │  ┌──────────────────┐ │
│ Email           │     │  │   OrderItems     │ │
│ Phone           │     │  │──────────────────│ │
│ Address         │     │  │ OrderItemID (PK) │ │
└────────┬────────┘     │  │ OrderID (FK)     │ │
         │              │  │ ProductID (FK)   │─┘
         │              │  │ Quantity         │
         │              │  │ UnitPrice        │
         │  ┌───────────▼──▼──────────────┐   │
         │  │       Orders               │   │
         │  │────────────────────────────│   │
         └─►│ OrderID (PK)               │   │
            │ CustomerID (FK)            │   │
            │ OrderDate                  │   │
            │ TotalAmount                │   │
            └────────────────────────────┘
```

### Table Definitions

#### Categories
| Column | Type | Description |
|--------|------|-------------|
| CategoryID | int (PK, Identity) | Unique category identifier |
| CategoryName | nvarchar(100) | Category name |
| Description | nvarchar(500) | Category description |

**Pre-seeded Categories:**
Electronics, Clothing, Books, Home & Garden, Sports, Toys, Health & Beauty, Automotive, Food & Beverage, Office Supplies

#### Products
| Column | Type | Description |
|--------|------|-------------|
| ProductID | int (PK, Identity) | Unique product identifier |
| ProductName | nvarchar(200) | Product name |
| CategoryID | int (FK) | Reference to Categories |
| Price | decimal(10,2) | Product price |
| StockQuantity | int | Available inventory |
| CreatedDate | datetime | Creation timestamp |

#### Customers
| Column | Type | Description |
|--------|------|-------------|
| CustomerID | int (PK, Identity) | Unique customer identifier |
| FirstName | nvarchar(100) | Customer first name |
| LastName | nvarchar(100) | Customer last name |
| Email | nvarchar(200) | Email address (unique) |
| Phone | nvarchar(20) | Phone number |
| Address | nvarchar(500) | Mailing address |
| City | nvarchar(100) | City |
| Country | nvarchar(100) | Country |
| CreatedDate | datetime | Registration date |

#### Orders
| Column | Type | Description |
|--------|------|-------------|
| OrderID | int (PK, Identity) | Unique order identifier |
| CustomerID | int (FK) | Reference to Customers |
| OrderDate | datetime | Order timestamp |
| TotalAmount | decimal(10,2) | Order total |
| Status | nvarchar(50) | Order status (Pending/Completed/Cancelled) |

#### OrderItems
| Column | Type | Description |
|--------|------|-------------|
| OrderItemID | int (PK, Identity) | Unique item identifier |
| OrderID | int (FK) | Reference to Orders |
| ProductID | int (FK) | Reference to Products |
| Quantity | int | Quantity ordered |
| UnitPrice | decimal(10,2) | Price at time of order |

---

## ⚙️ Configuration

### Environment Variables

Required for local scripts:

```powershell
# Windows PowerShell
$env:SQL_SERVER = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"

# Or create .env file in fabric/database/
SQL_SERVER=your-server.database.windows.net
SQL_DATABASE=your-database-name
```

### Azure Function Settings

Configured automatically by deployment script:

| Setting | Description | Example |
|---------|-------------|---------|
| SQL_SERVER | SQL Server FQDN | myserver.database.windows.net |
| SQL_DATABASE | Database name | sqldb-myagents-prod |
| SQL_AUTH_TYPE | Authentication method | AzureAD |
| AzureWebJobsStorage | Function storage | <connection-string> |
| FUNCTIONS_WORKER_RUNTIME | Runtime | python |

### Customizing Data Generation

Edit `fabric/database/generate_initial_data.py`:

```python
# Change quantities
num_customers = 100  # Default: 100
num_products = 50    # Default: 50
num_orders = 200     # Default: 200

# Change date ranges
start_date = datetime.now() - timedelta(days=365)
end_date = datetime.now()

# Change order size
items_per_order = random.randint(1, 5)  # 1-5 items per order
```

### Customizing Function Schedule

Edit `fabric/function/function_app.py`:

```python
# Change from every 5 minutes to every hour
@app.function_name(name="GenerateData")
@app.schedule(schedule="0 0 * * * *", arg_name="mytimer", run_on_startup=False)
def generate_data_timer(mytimer: func.TimerRequest) -> None:
    # ... function code
```

**Cron Schedule Examples:**
- Every 5 minutes: `0 */5 * * * *`
- Every hour: `0 0 * * * *`
- Every day at midnight: `0 0 0 * * *`
- Every Monday at 9am: `0 0 9 * * 1`

---

## 🧪 Testing & Verification

### Test Database Connection

```powershell
cd fabric\database
python test_connection.py
```

**Expected Output:**
```
✓ Connected to database
✓ Azure AD authentication working
✓ Tables accessible
✓ Data readable
```

### View Table Data

```powershell
python view_tables.py
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════╗
║              DATABASE TABLE SUMMARY                  ║
╚══════════════════════════════════════════════════════╝

Server:   myserver.database.windows.net
Database: mydb

Table               Records
──────────────────  ─────────
Categories          10
Products            50
Customers           100
Orders              200
OrderItems          450
```

### View Schema Details

```powershell
python view_schemas.py
```

Shows:
- Table structures
- Column types and constraints
- Foreign key relationships
- Indexes

### Test Function Deployment

```powershell
# View function logs
az functionapp log tail `
    -g <resource-group> `
    -n <function-name>

# Trigger function manually
az functionapp function invoke `
    -g <resource-group> `
    -n <function-name> `
    --function-name GenerateData
```

### Query Data Manually

In Azure Portal → SQL Query Editor:

```sql
-- View recent orders
SELECT TOP 10 
    o.OrderID,
    c.FirstName + ' ' + c.LastName AS Customer,
    o.OrderDate,
    o.TotalAmount,
    o.Status
FROM Orders o
JOIN Customers c ON o.CustomerID = c.CustomerID
ORDER BY o.OrderDate DESC;

-- View product inventory
SELECT 
    p.ProductName,
    cat.CategoryName,
    p.Price,
    p.StockQuantity
FROM Products p
JOIN Categories cat ON p.CategoryID = cat.CategoryID
ORDER BY p.StockQuantity DESC;

-- View order items
SELECT 
    o.OrderID,
    p.ProductName,
    oi.Quantity,
    oi.UnitPrice,
    oi.Quantity * oi.UnitPrice AS LineTotal
FROM OrderItems oi
JOIN Orders o ON oi.OrderID = o.OrderID
JOIN Products p ON oi.ProductID = p.ProductID
WHERE o.OrderID = 1;  -- Change order ID
```

---

## 🎮 Management

### Regenerate All Data

```powershell
cd fabric\database

# Clear existing data (except categories)
# Run in SQL Query Editor:
TRUNCATE TABLE OrderItems;
TRUNCATE TABLE Orders;
TRUNCATE TABLE Customers;
TRUNCATE TABLE Products;

# Regenerate
python generate_initial_data.py
```

### Update Schema

```powershell
# Edit fabric/database/schema.sql
# Then deploy changes:
python deploy_schema.py
```

**Note:** `deploy_schema.py` is NOT idempotent for schema changes. Drop tables first if structure changed.

### Monitor Function

```powershell
# Real-time logs
az functionapp log tail `
    -g rg-myagents-prod `
    -n func-fabric-myagents

# View executions in Azure Portal
# Functions → GenerateData → Monitor → Invocations
```

### Scale Function

```powershell
# Change function app plan (consumption → premium)
az functionapp plan update `
    --resource-group rg-myagents-prod `
    --name asp-fabric-myagents `
    --sku P1V2

# Or keep consumption and adjust concurrency in host.json
```

### Stop Data Generation

```powershell
# Disable function
az functionapp function disable `
    -g rg-myagents-prod `
    -n func-fabric-myagents `
    --function-name GenerateData

# Enable again
az functionapp function enable `
    -g rg-myagents-prod `
    -n func-fabric-myagents `
    --function-name GenerateData
```

### Delete Fabric Resources

```powershell
# Delete function app
az functionapp delete `
    -g rg-myagents-prod `
    -n func-fabric-myagents

# Delete storage account
az storage account delete `
    -n stfabricmyagents `
    -g rg-myagents-prod `
    --yes

# Clear database (optional)
# Run in SQL Query Editor:
DROP TABLE IF EXISTS OrderItems;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Categories;
```

---

## 🐛 Troubleshooting

### Issue: ODBC Driver Not Found

**Error:**
```
pyodbc.Error: ('01000', "[01000] [unixODBC][Driver Manager]Can't open lib 'ODBC Driver 18 for SQL Server'")
```

**Solution:**
Install ODBC Driver 18 (see [Prerequisites](#prerequisites))

**Verify Installation:**
```powershell
# Windows
odbcad32

# macOS/Linux
odbcinst -q -d
```

---

### Issue: Authentication Failed

**Error:**
```
Login failed for user '<token-identified principal>'
```

**Solution:**
```powershell
# 1. Ensure logged in to Azure CLI
az login

# 2. Check your access to the database
az sql db show `
    --resource-group rg-myagents-prod `
    --server sql-myagents-prod `
    --name sqldb-myagents-prod

# 3. Ensure you have SQL permissions
# Run in SQL Query Editor as admin:
CREATE USER [your-email@domain.com] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [your-email@domain.com];
```

---

### Issue: Table Already Exists

**Error:**
```
There is already an object named 'Categories' in the database
```

**Solution:**
Schema deployment is idempotent for data but not structure. Either:

**Option 1: Drop and recreate**
```sql
-- In SQL Query Editor
DROP TABLE IF EXISTS OrderItems;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Customers;
DROP TABLE IF EXISTS Products;
DROP TABLE IF EXISTS Categories;
```

Then redeploy:
```powershell
python deploy_schema.py
```

**Option 2: Skip schema deployment**
```powershell
.\setup-database.ps1 -SkipSchema -GenerateData
```

---

### Issue: Function Deployment Failed

**Error:**
```
Error: Azure Functions Core Tools not found
```

**Solution:**
```powershell
# Check if installed
func --version

# Install (Windows)
winget install Microsoft.Azure.FunctionsCoreTools

# Or use npm (cross-platform)
npm install -g azure-functions-core-tools@4
```

---

### Issue: Function Can't Access SQL

**Error (in function logs):**
```
Login failed for user 'NT AUTHORITY\ANONYMOUS LOGON'
```

**Solution:**
Grant managed identity SQL access (see [Step-by-Step Deployment](#step-by-step-deployment), Step 4)

```sql
-- Get function app name from Azure Portal
-- Navigate to Function App → Identity → System assigned → Object ID

-- In SQL Query Editor:
CREATE USER [func-fabric-myagents] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [func-fabric-myagents];
ALTER ROLE db_datawriter ADD MEMBER [func-fabric-myagents];
```

---

### Issue: No Data Generated

**Symptoms:**
- Scripts run without errors
- Tables exist but are empty

**Solution:**
```powershell
# Check if script actually ran
python generate_initial_data.py

# Check for connection issues
python test_connection.py

# View tables to verify
python view_tables.py

# Check script output for errors
```

If no errors but still no data, check SQL permissions:
```sql
-- In SQL Query Editor
SELECT 
    dp.name,
    dp.type_desc,
    drm.role_principal_id,
    drp.name AS role_name
FROM sys.database_principals dp
LEFT JOIN sys.database_role_members drm ON dp.principal_id = drm.member_principal_id
LEFT JOIN sys.database_principals drp ON drm.role_principal_id = drp.principal_id
WHERE dp.name LIKE '%your-email%';
```

Ensure you have `db_owner` or at least `db_datawriter` role.

---

### Issue: Python Package Errors

**Error:**
```
ModuleNotFoundError: No module named 'pyodbc'
```

**Solution:**
```powershell
cd fabric\database
pip install -r requirements.txt

# Or install individually
pip install pyodbc azure-identity Faker
```

**For Azure Function:**
```powershell
cd fabric\function
pip install -r requirements.txt
```

---

## 📚 Additional Resources

### Documentation
- [Fabric README](../fabric/README.md)
- [Main Deployment Guide](QUICK_START.md)
- [Azure SQL Documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)

### Tools
- [ODBC Driver Download](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- [Faker Documentation](https://faker.readthedocs.io/)

### Scripts Reference
- [Setup Database Script](../fabric/scripts/setup-database.ps1)
- [Deploy Function Script](../fabric/scripts/deploy-fabric-function.ps1)

---

## 🎯 Quick Command Reference

```powershell
# Complete deployment with data
.\deploy-complete.ps1 -ResourceGroupName "rg" -DeployFabric -GenerateInitialData

# Standalone database setup
.\fabric\scripts\setup-database.ps1 -GenerateData

# Deploy function only
.\fabric\scripts\deploy-fabric-function.ps1 -ResourceGroupName "rg" -SqlServerName "server" -SqlDatabaseName "db"

# View data
python fabric\database\view_tables.py
python fabric\database\view_schemas.py

# Test connection
python fabric\database\test_connection.py

# Monitor function
az functionapp log tail -g <rg> -n <function-name>
```

---

**🎉 Congratulations!** You now have a complete synthetic data generation system for your Azure Intelligent Agent Starter application!

For questions or issues, refer to the main [README](../README.md) or open an issue in the repository.

---

**Made with ❤️ for Azure Intelligent Agent Starter**  
*Realistic test data for better demos* 📊
