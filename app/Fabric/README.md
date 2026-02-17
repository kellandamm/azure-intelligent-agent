# Azure SQL Synthetic Data Generator

This project contains scripts and an Azure Function to generate and maintain synthetic data for your Azure SQL database.

## 📋 Table of Contents

- [Database Schema](#database-schema)
- [Setup Instructions](#setup-instructions)
- [Initial Data Generation](#initial-data-generation)
- [Azure Function Deployment](#azure-function-deployment)
- [Local Testing](#local-testing)
- [Environment Variables](#environment-variables)

## 🗄️ Database Schema

The database contains the following tables with relationships:

- **dbo.Categories** - Product categories (10 pre-seeded records)
- **dbo.Products** - Product catalog with pricing and inventory
- **dbo.Customers** - Customer information
- **dbo.Orders** - Customer orders
- **dbo.OrderItems** - Individual items in orders

### Entity Relationships
```
Categories (1) ─── (N) Products
Customers (1) ─── (N) Orders
Orders (1) ─── (N) OrderItems
Products (1) ─── (N) OrderItems
```

## 🚀 Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- Azure Functions Core Tools v4
- ODBC Driver 18 for SQL Server
- Azure SQL Database access
- Azure subscription (for deployment)

### 2. Install ODBC Driver

**Windows:**
Download and install from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18 mssql-tools18
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### 3. Install Python Dependencies

```bash
cd <your-repo-path>/app/Fabric
pip install -r requirements.txt
```

### 4. Create Database Schema

Connect to your Azure SQL Database and run the schema script:

```bash
# Using Azure Data Studio or SQL Server Management Studio
# Open and execute: schema.sql
```

Or using sqlcmd:
```bash
sqlcmd -S <your-sql-server>.database.windows.net -d your_database_name -U your_username -P your_password -i schema.sql
```

## 📊 Initial Data Generation

The `generate_initial_data.py` script creates an initial dataset:

- 100 Products across 10 categories
- 200 Customers
- 300 Orders
- 600+ Order Items

### Configuration

Set environment variables:

```powershell
# PowerShell
$env:SQL_SERVER="<your-sql-server>.database.windows.net"
$env:SQL_DATABASE="your_database_name"
$env:SQL_USERNAME="your_username"
$env:SQL_PASSWORD="your_password"
```

Or create a `.env` file:
```
SQL_SERVER=<your-sql-server>.database.windows.net
SQL_DATABASE=your_database_name
SQL_USERNAME=your_username
SQL_PASSWORD=your_password
```

### Run Initial Data Generation

```bash
python generate_initial_data.py
```

## ⚡ Azure Function Deployment

The Azure Function `daily_data_generator` runs every 24 hours at midnight UTC and generates 500 new records:

- 50 new Products
- 100 new Customers
- 200 new Orders
- 400-600 new Order Items

### Local Configuration

1. Copy the template:
```bash
cp local.settings.json.template local.settings.json
```

2. Edit `local.settings.json` with your database credentials:
```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "SQL_SERVER": "<your-sql-server>.database.windows.net",
    "SQL_DATABASE": "your_database_name",
    "SQL_USERNAME": "your_username",
    "SQL_PASSWORD": "your_password"
  }
}
```

### Deploy to Azure

#### Option 1: Using Azure CLI

```bash
# Login to Azure
az login

# Create a resource group (if needed)
az group create --name rg-fabric-synthetic-data --location eastus

# Create a storage account
az storage account create --name stfabricsynthdata --resource-group rg-fabric-synthetic-data --location eastus --sku Standard_LRS

# Create a Function App (Linux, Python 3.11)
az functionapp create --resource-group rg-fabric-synthetic-data --consumption-plan-location eastus --runtime python --runtime-version 3.11 --functions-version 4 --name func-fabric-synthetic-data --storage-account stfabricsynthdata --os-type Linux

# Configure app settings
az functionapp config appsettings set --name func-fabric-synthetic-data --resource-group rg-fabric-synthetic-data --settings SQL_SERVER="<your-sql-server>.database.windows.net" SQL_DATABASE="your_database_name" SQL_USERNAME="your_username" SQL_PASSWORD="your_password"

# Deploy the function
func azure functionapp publish func-fabric-synthetic-data
```

#### Option 2: Using VS Code Azure Functions Extension

1. Install the Azure Functions extension
2. Click the Azure icon in the Activity Bar
3. Sign in to Azure
4. Click "Deploy to Function App"
5. Follow the prompts to create or select a Function App
6. After deployment, add Application Settings in the Azure Portal:
   - `SQL_SERVER`: <your-sql-server>.database.windows.net
   - `SQL_DATABASE`: your_database_name
   - `SQL_USERNAME`: your_username
   - `SQL_PASSWORD`: your_password

#### Option 3: Using Azure Portal

1. Create a Function App in Azure Portal
2. Choose Runtime: Python, Version: 3.11
3. Deploy using VS Code or Azure Functions Core Tools
4. Add Application Settings (Configuration → Application settings)

## 🧪 Local Testing

### Test the Function Locally

```bash
# Start the Azure Functions runtime
func start
```

To test the timer trigger immediately without waiting:

1. Modify `function_app.py` temporarily:
```python
@app.timer_trigger(
    schedule="0 */5 * * * *",  # Every 5 minutes for testing
    arg_name="myTimer", 
    run_on_startup=True,  # Run immediately on startup
    use_monitor=False
)
```

2. Run the function:
```bash
func start
```

3. Restore the original schedule after testing:
```python
schedule="0 0 0 * * *",  # Daily at midnight
run_on_startup=False,
```

## 🔧 Environment Variables

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `SQL_SERVER` | Azure SQL Server hostname | <your-sql-server>.database.windows.net |
| `SQL_DATABASE` | Database name | FabricDB |
| `SQL_USERNAME` | SQL authentication username | sqladmin |
| `SQL_PASSWORD` | SQL authentication password | YourStrongP@ssw0rd! |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `FUNCTIONS_WORKER_RUNTIME` | Runtime for Azure Functions | python |
| `AzureWebJobsStorage` | Storage for function metadata | UseDevelopmentStorage=true (local) |

## 📅 Timer Schedule

The function uses CRON expressions for scheduling:

```
0 0 0 * * *
│ │ │ │ │ │
│ │ │ │ │ └─ Day of week (0-6, 0 = Sunday)
│ │ │ │ └─── Month (1-12)
│ │ │ └───── Day of month (1-31)
│ │ └─────── Hour (0-23)
│ └───────── Minute (0-59)
└─────────── Second (0-59)
```

**Current schedule:** `0 0 0 * * *` = Every day at midnight UTC

### Common Schedules

- Every hour: `0 0 * * * *`
- Every 6 hours: `0 0 */6 * * *`
- Every 12 hours: `0 0 */12 * * *`
- Every day at 2 AM: `0 0 2 * * *`
- Every Monday at midnight: `0 0 0 * * 1`

## 📈 Monitoring

### View Function Logs

**Azure Portal:**
1. Navigate to your Function App
2. Go to Functions → daily_data_generator
3. Click Monitor
4. View Invocation Traces and Logs

**Application Insights:**
```bash
# Enable Application Insights in Azure Portal
# Then query logs using Kusto Query Language (KQL)
```

### Sample Queries

```kql
// Recent executions
traces
| where message contains "SYNTHETIC DATA GENERATION COMPLETE"
| project timestamp, message
| order by timestamp desc
| take 10

// Error tracking
traces
| where severityLevel >= 3
| project timestamp, message, severityLevel
| order by timestamp desc
```

## 🔒 Security Best Practices

1. **Use Managed Identity (Recommended)**
   - Configure Azure SQL to allow Azure AD authentication
   - Use the Function App's managed identity
   - No passwords in configuration!

2. **Use Key Vault for Secrets**
   ```bash
   # Store password in Key Vault
   az keyvault secret set --vault-name your-keyvault --name sql-password --value "YourPassword"
   
   # Reference in Function App
   SQL_PASSWORD="@Microsoft.KeyVault(SecretUri=https://your-keyvault.vault.azure.net/secrets/sql-password/)"
   ```

3. **Network Security**
   - Configure Azure SQL firewall rules
   - Enable VNet integration for Function App
   - Use private endpoints

## 🧹 Maintenance

### Clean Up Old Data

```sql
-- Example: Delete orders older than 2 years
DELETE FROM dbo.OrderItems 
WHERE OrderID IN (
    SELECT OrderID FROM dbo.Orders 
    WHERE OrderDate < DATEADD(YEAR, -2, GETUTCDATE())
);

DELETE FROM dbo.Orders 
WHERE OrderDate < DATEADD(YEAR, -2, GETUTCDATE());
```

### Monitor Database Size

```sql
-- Check database size
SELECT 
    DB_NAME() AS DatabaseName,
    SUM(size) * 8 / 1024 AS SizeMB
FROM sys.master_files
WHERE database_id = DB_ID()
GROUP BY database_id;

-- Check table row counts
SELECT 
    t.NAME AS TableName,
    p.rows AS RowCounts
FROM sys.tables t
INNER JOIN sys.partitions p ON t.object_id = p.OBJECT_ID
WHERE t.is_ms_shipped = 0 AND p.index_id < 2
ORDER BY p.rows DESC;
```

## 📝 Troubleshooting

### Common Issues

**Issue:** "ODBC Driver not found"
- **Solution:** Install ODBC Driver 18 for SQL Server (see Prerequisites)

**Issue:** "Login failed for user"
- **Solution:** Verify SQL credentials and firewall rules in Azure Portal

**Issue:** "Function not triggering"
- **Solution:** Check Application Insights logs, verify timer schedule syntax

**Issue:** "Duplicate key errors"
- **Solution:** The function handles duplicate emails/SKUs gracefully with warnings

## 📞 Support

For issues or questions:
1. Check Application Insights logs
2. Review Azure SQL Database activity logs
3. Verify all environment variables are set correctly

## 🎯 Summary

✅ **Schema**: Complete database schema with relationships and constraints  
✅ **Initial Data**: Script to generate 700+ initial records  
✅ **Azure Function**: Automated daily generation of 500 new records  
✅ **Monitoring**: Comprehensive logging and tracking  
✅ **Documentation**: Full setup and deployment guide  

The system is now ready to provide continuous synthetic data for your Fabric application!
