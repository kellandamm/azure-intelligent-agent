# 📊 Fabric Data Management

This component provides synthetic data generation and maintenance for the Azure SQL database used by the Agent Framework application.

---

## 🎯 Overview

The Fabric component includes:

1. **Database Schema** - SQL tables, views, and stored procedures
2. **Data Generation Scripts** - Python scripts to create synthetic data
3. **Azure Function** - Automated ongoing data generation
4. **Management Tools** - Scripts to view, test, and manage database content

### Components

```
fabric/
├── database/                    # Database management scripts
│   ├── deploy_schema.py        # Deploy SQL schema
│   ├── generate_initial_data.py# Generate seed data
│   ├── view_tables.py          # View table contents
│   ├── view_schemas.py         # View schema information
│   ├── test_connection.py      # Test database connection
│   ├── schema.sql              # Main database schema
│   ├── auth_schema.sql         # Authentication schema
│   └── requirements.txt        # Python dependencies
│
├── function/                    # Azure Function
│   ├── function_app.py         # Function code
│   ├── host.json               # Function configuration
│   ├── requirements.txt        # Function dependencies
│   └── local.settings.json.template
│
└── scripts/                     # Deployment scripts
    ├── deploy-fabric-function.ps1
    └── setup-database.ps1
```

---

## 📋 Database Schema

The database contains the following tables:

### Core Tables

- **`dbo.Categories`** - Product categories (10 pre-seeded records)
- **`dbo.Products`** - Product catalog with pricing and inventory
- **`dbo.Customers`** - Customer information
- **`dbo.Orders`** - Customer orders
- **`dbo.OrderItems`** - Individual items in orders

### Entity Relationships

```
Categories (1) ─── (N) Products
Customers (1) ─── (N) Orders
Orders (1) ─── (N) OrderItems
Products (1) ─── (N) OrderItems
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Azure CLI** logged in
3. **ODBC Driver 18** for SQL Server
4. **Azure SQL Database** access with Azure AD authentication
5. **Azure Functions Core Tools v4** (for function deployment)

### Install ODBC Driver

**Windows:**
```powershell
# Download and install from:
https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
```

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18
```

**Linux (Ubuntu):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

---

## 🔧 Setup Instructions

### Option 1: Automated Setup (Recommended)

Use the PowerShell script to set up everything:

```powershell
# Set environment variables
$env:SQL_SERVER = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"

# Run setup script
cd fabric\scripts
.\setup-database.ps1 -GenerateData
```

This will:
1. ✅ Install Python dependencies
2. ✅ Deploy database schema
3. ✅ Generate initial synthetic data
4. ✅ Test database connection

---

### Option 2: Manual Setup

#### 1. Install Python Dependencies

```powershell
cd fabric\database
pip install -r requirements.txt
```

#### 2. Set Environment Variables

```powershell
$env:SQL_SERVER = "your-server.database.windows.net"
$env:SQL_DATABASE = "your-database-name"
```

Or create a `.env` file:
```env
SQL_SERVER=your-server.database.windows.net
SQL_DATABASE=your-database-name
```

#### 3. Deploy Database Schema

```powershell
python deploy_schema.py
```

This creates:
- Tables (Categories, Products, Customers, Orders, OrderItems)
- Relationships and foreign keys
- Indexes for performance
- Pre-seeded category data

#### 4. Generate Initial Data

```powershell
python generate_initial_data.py
```

This generates:
- 100 customers
- 50 products across categories
- 200 orders
- Order items with realistic quantities

#### 5. Verify Setup

```powershell
# Test connection
python test_connection.py

# View tables
python view_tables.py

# View schemas
python view_schemas.py
```

---

## ⚡ Deploy Azure Function

The Azure Function automatically generates ongoing synthetic data:

```powershell
cd fabric\scripts
.\deploy-fabric-function.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -SqlServerName "sql-myagents-prod" `
    -SqlDatabaseName "sqldb-myagents-prod"
```

This creates:
- Storage account for function
- Function App (consumption plan)
- System-assigned managed identity
- Configured app settings

**After deployment, grant SQL access:**

In Azure Portal → SQL Database → Query editor:

```sql
CREATE USER [func-fabric-myagents] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [func-fabric-myagents];
ALTER ROLE db_datawriter ADD MEMBER [func-fabric-myagents];
```

---

## 📖 Usage

### View Table Contents

```powershell
python database\view_tables.py
```

**Output:**
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

---

### View Schema Information

```powershell
python database\view_schemas.py
```

Shows:
- Table structures
- Column types
- Relationships
- Indexes

---

### Test Database Connection

```powershell
python database\test_connection.py
```

**Output:**
```
✓ Connected to database
✓ Azure AD authentication working
✓ Tables accessible
✓ Data readable
```

---

## 🔄 Integrated Deployment

### With PowerShell Scripts

Deploy Fabric as part of complete deployment:

```powershell
cd scripts
.\deploy-complete.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -DeployFabric `
    -GenerateInitialData
```

### With Azure Developer CLI (azd)

Fabric is included automatically:

```bash
azd up
```

The Fabric function is deployed as part of the standard workflow.

---

## 🎮 Management Commands

### List All Tables

```powershell
python database\view_tables.py
```

### View Specific Table

```powershell
# Edit view_tables.py to show specific table data
python database\view_tables.py
```

### Clear All Data

```sql
-- In SQL Query Editor
TRUNCATE TABLE dbo.OrderItems;
TRUNCATE TABLE dbo.Orders;
TRUNCATE TABLE dbo.Customers;
TRUNCATE TABLE dbo.Products;
-- Categories are preserved
```

### Regenerate Data

```powershell
python database\generate_initial_data.py
```

---

## 🔐 Authentication

The Fabric component uses **Azure AD authentication** (managed identity) for SQL access:

### For Local Development

Uses `DefaultAzureCredential` which tries:
1. Environment variables
2. Managed identity (in Azure)
3. Azure CLI credentials
4. Visual Studio credentials

**Ensure you're logged in:**
```powershell
az login
```

### For Azure Function

Uses system-assigned managed identity:

```sql
-- Grant access in SQL Database
CREATE USER [func-fabric-myagents] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [func-fabric-myagents];
ALTER ROLE db_datawriter ADD MEMBER [func-fabric-myagents];
```

---

## 📊 Data Generation Details

### Initial Data

- **Customers**: 100 realistic customer profiles
- **Products**: 50 products across 10 categories
- **Orders**: 200 orders with realistic dates
- **Order Items**: 1-5 items per order

### Azure Function

The function generates:
- **New orders**: Every 5 minutes
- **Customer updates**: Profile changes
- **Inventory updates**: Stock level changes
- **Product updates**: Price adjustments

---

## 🧪 Testing

### Test Connection

```powershell
python database\test_connection.py
```

### Verify Schema

```powershell
python database\view_schemas.py
```

### Check Data

```powershell
python database\view_tables.py
```

### Test Function

```powershell
# View function logs
az functionapp log tail -g <resource-group> -n <function-name>

# Trigger function manually
az functionapp function invoke -g <resource-group> -n <function-name> --function-name GenerateData
```

---

## 🐛 Troubleshooting

### Issue: "ODBC Driver not found"

**Solution:**
Install ODBC Driver 18 for SQL Server (see Prerequisites)

### Issue: "Authentication failed"

**Solution:**
```powershell
# Ensure Azure CLI is logged in
az login

# Check your access to the database
az sql db show --resource-group <rg> --server <server> --name <db>
```

### Issue: "Table already exists"

**Solution:**
Schema deployment is idempotent. Drop tables manually if needed:

```sql
-- In SQL Query Editor
DROP TABLE IF EXISTS dbo.OrderItems;
DROP TABLE IF EXISTS dbo.Orders;
DROP TABLE IF EXISTS dbo.Customers;
DROP TABLE IF EXISTS dbo.Products;
DROP TABLE IF EXISTS dbo.Categories;
```

Then redeploy:
```powershell
python database\deploy_schema.py
```

### Issue: "Function deployment failed"

**Solution:**
```powershell
# Ensure Azure Functions Core Tools installed
func --version

# Install if missing:
npm install -g azure-functions-core-tools@4

# Or on Windows:
winget install Microsoft.Azure.FunctionsCoreTools
```

---

## 📚 Additional Resources

- [Azure SQL Documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [ODBC Driver Download](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
- [Faker Documentation](https://faker.readthedocs.io/) - Synthetic data generation

---

## 🎯 Quick Reference

```powershell
# Setup database
.\fabric\scripts\setup-database.ps1 -GenerateData

# Deploy function
.\fabric\scripts\deploy-fabric-function.ps1 -ResourceGroupName "rg" -SqlServerName "server" -SqlDatabaseName "db"

# View data
python fabric\database\view_tables.py

# Test connection
python fabric\database\test_connection.py

# View schemas
python fabric\database\view_schemas.py
```

---

**Made with ❤️ for Azure Intelligent Agent Starter**  
*Synthetic data generation for realistic testing and demos* 📊
