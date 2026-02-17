# Database Setup and Configuration Guide

This guide walks you through setting up the Azure SQL Database and configuring the synthetic data generator.

## Step 1: Create or Access Azure SQL Database

### Option A: Using Existing Database (<your-sql-server>.database.windows.net)

If the database already exists, ensure you have:
- Server admin credentials
- Firewall rules configured to allow your IP
- Database created

### Option B: Create New Database

```bash
# Using Azure CLI
az sql server create \
  --name <your-database-name> \
  --resource-group your-resource-group \
  --location eastus \
  --admin-user sqladmin \
  --admin-password YourStrongP@ssw0rd!

az sql db create \
  --resource-group your-resource-group \
  --server <your-sql-server> \
  --name FabricDB \
  --service-objective S0
```

## Step 2: Configure Firewall Rules

### Allow Your IP Address

**Azure Portal:**
1. Navigate to your SQL Server
2. Go to "Networking" under Security
3. Add your client IP address
4. Save

**Azure CLI:**
```bash
# Get your current IP
$myIp = (Invoke-WebRequest -Uri "https://api.ipify.org").Content

# Add firewall rule
az sql server firewall-rule create \
  --resource-group your-resource-group \
  --server <your-sql-server> \
  --name AllowMyIP \
  --start-ip-address $myIp \
  --end-ip-address $myIp
```

### Allow Azure Services

```bash
az sql server firewall-rule create \
  --resource-group your-resource-group \
  --server <your-sql-server> \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

## Step 3: Create Database Schema

### Using Azure Data Studio

1. Download Azure Data Studio: https://aka.ms/azuredatastudio
2. Connect to `<your-sql-server>.database.windows.net`
3. Open `schema.sql`
4. Execute the script

### Using sqlcmd

```powershell
# Windows
sqlcmd -S <your-sql-server>.database.windows.net -d FabricDB -U sqladmin -P YourPassword -i schema.sql

# Linux/macOS
sqlcmd -S <your-sql-server>.database.windows.net -d FabricDB -U sqladmin -P 'YourPassword' -i schema.sql
```

### Using Azure Portal Query Editor

1. Navigate to your database in Azure Portal
2. Go to "Query editor"
3. Login with SQL authentication
4. Copy and paste the contents of `schema.sql`
5. Run the query

## Step 4: Verify Schema Creation

Run this query to verify all tables were created:

```sql
SELECT 
    t.name AS TableName,
    c.name AS ColumnName,
    ty.name AS DataType
FROM sys.tables t
INNER JOIN sys.columns c ON t.object_id = c.object_id
INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
WHERE t.schema_id = SCHEMA_ID('dbo')
ORDER BY t.name, c.column_id;
```

Expected tables:
- Categories
- Customers
- Orders
- OrderItems
- Products

## Step 5: Configure Local Environment

### Create local.settings.json

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "SQL_SERVER": "<your-sql-server>.database.windows.net",
    "SQL_DATABASE": "FabricDB",
    "SQL_USERNAME": "sqladmin",
    "SQL_PASSWORD": "YourStrongP@ssw0rd!"
  }
}
```

### Set Environment Variables (Alternative)

**PowerShell:**
```powershell
$env:SQL_SERVER="<your-sql-server>.database.windows.net"
$env:SQL_DATABASE="FabricDB"
$env:SQL_USERNAME="sqladmin"
$env:SQL_PASSWORD="YourStrongP@ssw0rd!"
```

**Bash:**
```bash
export SQL_SERVER="<your-sql-server>.database.windows.net"
export SQL_DATABASE="FabricDB"
export SQL_USERNAME="sqladmin"
export SQL_PASSWORD="YourStrongP@ssw0rd!"
```

## Step 6: Test Database Connection

### Test Script

Create `test_connection.py`:

```python
import os
import pyodbc

SERVER = os.getenv('SQL_SERVER', '<your-sql-server>.database.windows.net')
DATABASE = os.getenv('SQL_DATABASE', 'FabricDB')
USERNAME = os.getenv('SQL_USERNAME')
PASSWORD = os.getenv('SQL_PASSWORD')

conn_string = (
    f'Driver={{ODBC Driver 18 for SQL Server}};'
    f'Server=tcp:{SERVER},1433;'
    f'Database={DATABASE};'
    f'Uid={USERNAME};'
    f'Pwd={PASSWORD};'
    f'Encrypt=yes;'
    f'TrustServerCertificate=no;'
    f'Connection Timeout=30;'
)

try:
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    row = cursor.fetchone()
    print("✓ Connected successfully!")
    print(f"  SQL Server version: {row[0][:50]}...")
    
    cursor.execute("SELECT COUNT(*) FROM dbo.Categories")
    count = cursor.fetchone()[0]
    print(f"  Categories count: {count}")
    
    conn.close()
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

Run the test:
```bash
python test_connection.py
```

## Step 7: Generate Initial Data

```bash
python generate_initial_data.py
```

Expected output:
```
Generating 100 products...
✓ Created 100 products
Generating 200 customers...
✓ Created 200 customers
Generating 300 orders with items...
✓ Created 300 orders
✓ Created 600+ order items
```

## Step 8: Deploy Azure Function

### Quick Deployment

```powershell
.\deploy-to-azure.ps1 `
  -SqlDatabase "FabricDB" `
  -SqlUsername "sqladmin" `
  -SqlPassword "YourStrongP@ssw0rd!"
```

### Manual Deployment Steps

See README.md for detailed deployment options.

## Troubleshooting

### Common Connection Errors

**Error: "Login failed for user"**
- Verify username and password
- Check if user has access to the database
- Ensure SQL authentication is enabled

**Error: "Cannot open server"**
- Check firewall rules
- Verify server name is correct
- Ensure your IP is allowed

**Error: "SSL Security error"**
- Update ODBC driver to version 18
- Verify TrustServerCertificate setting

**Error: "ODBC Driver not found"**
- Install ODBC Driver 18 for SQL Server
- Windows: Download from Microsoft
- Linux: Use package manager
- macOS: Use Homebrew

### Verify ODBC Driver

**Windows (PowerShell):**
```powershell
Get-OdbcDriver | Where-Object {$_.Name -like "*SQL Server*"}
```

**Linux:**
```bash
odbcinst -q -d
```

**macOS:**
```bash
odbcinst -q -d
```

## Security Recommendations

### 1. Use Azure AD Authentication (Recommended)

Modify connection string:
```python
conn_string = (
    f'Driver={{ODBC Driver 18 for SQL Server}};'
    f'Server=tcp:{SERVER},1433;'
    f'Database={DATABASE};'
    f'Authentication=ActiveDirectoryMsi;'
    f'Encrypt=yes;'
)
```

### 2. Store Secrets in Azure Key Vault

```bash
# Create Key Vault
az keyvault create --name kv-fabric-secrets --resource-group rg-fabric-synthetic-data

# Store password
az keyvault secret set --vault-name kv-fabric-secrets --name sql-password --value "YourPassword"

# Configure Function App to use Key Vault
az functionapp config appsettings set \
  --name your-function-app \
  --resource-group rg-fabric-synthetic-data \
  --settings SQL_PASSWORD="@Microsoft.KeyVault(SecretUri=https://kv-fabric-secrets.vault.azure.net/secrets/sql-password/)"
```

### 3. Use Managed Identity

1. Enable managed identity on Function App
2. Grant SQL permissions to the managed identity
3. Update connection code to use managed identity

## Next Steps

1. ✅ Schema created
2. ✅ Initial data generated
3. ✅ Azure Function deployed
4. 📊 Monitor function executions
5. 🔍 Query and analyze synthetic data

Your synthetic data generator is now ready!
