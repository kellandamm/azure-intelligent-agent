# Configuration Guide

This guide explains how to configure the Azure Intelligent Agent application before deployment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Required Configuration](#required-configuration)
- [Optional Configuration](#optional-configuration)
- [Configuration Files](#configuration-files)
- [Security Best Practices](#security-best-practices)
- [Validation](#validation)

---

## Prerequisites

Before configuring the application, ensure you have:

1. **Azure Subscription** with appropriate permissions
2. **Azure CLI** installed and authenticated (`az login`)
3. **Azure OpenAI Service** deployed (or access to an existing instance)
4. **Azure SQL Database** or **Microsoft Fabric SQL Database** (for data storage)
5. **Service Principal** (optional, for Fabric/Power BI integration)

---

## Required Configuration

### 1. Environment Variables

Copy the template and create your environment file:

```bash
# In the app/ directory
cp .env.template .env
```

Or use the comprehensive example:

```bash
cp .env.example .env
```

### 2. Azure Resource Names

Set these environment variables **before running deployment scripts**:

```powershell
# PowerShell
$env:AZURE_RESOURCE_GROUP = "rg-myagent-prod"
$env:AZURE_APP_NAME = "myagent-app"
$env:AZURE_CONTAINER_REGISTRY = "myagentacr"
```

```bash
# Bash
export AZURE_RESOURCE_GROUP="rg-myagent-prod"
export AZURE_APP_NAME="myagent-app"
export AZURE_CONTAINER_REGISTRY="myagentacr"
```

### 3. Azure OpenAI Configuration

In your `.env` file, configure Azure OpenAI:

```env
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o  # Your model deployment name
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

**Where to find these values:**
- Portal: Azure OpenAI Service → Keys and Endpoint
- Deployment name: Azure OpenAI Service → Model deployments

### 4. Database Configuration

Configure your SQL database connection:

```env
SQL_SERVER=your-server.database.windows.net
SQL_DATABASE=your-database-name
SQL_USE_AZURE_AUTH=true  # Recommended: Use Azure AD authentication
SQL_USERNAME=  # Leave empty if using Azure AD
SQL_PASSWORD=  # Leave empty if using Azure AD
```

**For Azure SQL:**
- Portal: SQL Database → Connection strings
- Recommended: Use Azure AD authentication (no username/password)

**For Microsoft Fabric SQL:**
- Fabric portal: Workspace → SQL analytics endpoint
- Format: `xyz-abc123.datawarehouse.fabric.microsoft.com`

### 5. JWT Secret

Generate a secure random string for JWT token signing:

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# PowerShell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Add to `.env`:

```env
JWT_SECRET=your-generated-secure-random-string
```

---

## Optional Configuration

### Azure AI Foundry (Optional)

If using Azure AI Foundry native agents:

```env
PROJECT_ENDPOINT=https://your-project.api.azureml.ms
PROJECT_CONNECTION_STRING=your-connection-string
MODEL_DEPLOYMENT_NAME=gpt-4o
```

**Where to find:**
- Azure AI Foundry portal → Project → Settings → Connection string

### Microsoft Fabric Integration (Optional)

If integrating with Microsoft Fabric agents:

```env
FABRIC_WORKSPACE_ID=your-workspace-id
FABRIC_ORCHESTRATOR_AGENT_ID=your-agent-id
# ... other Fabric agent IDs
```

**Where to find:**
- Fabric portal → Workspace → Settings → Workspace ID
- Fabric portal → Agent → Settings → Agent ID

### Power BI Embedding (Optional)

If embedding Power BI reports:

1. **Create Service Principal:**
   ```bash
   az ad sp create-for-rbac --name "myagent-powerbi-sp"
   ```

2. **Grant Power BI permissions:**
   - Power BI Admin portal → Tenant settings
   - Enable "Service principals can use Power BI APIs"
   - Add your service principal to the enabled list

3. **Configure in `.env`:**
   ```env
   POWERBI_WORKSPACE_ID=your-workspace-id
   POWERBI_REPORT_ID=your-report-id
   POWERBI_CLIENT_ID=your-sp-client-id
   POWERBI_CLIENT_SECRET=your-sp-secret
   POWERBI_TENANT_ID=your-tenant-id
   ```

### Fabric SQL Analytics (Optional)

If querying Fabric lakehouse data:

```env
FABRIC_SQL_SERVER=xyz-abc123.datawarehouse.fabric.microsoft.com
FABRIC_SQL_DATABASE=MyLakehouse
FABRIC_CLIENT_ID=your-sp-client-id
FABRIC_CLIENT_SECRET=your-sp-secret
FABRIC_SQL_USE_AZURE_AUTH=true
```

---

## Configuration Files

### `.env` Files

- **`.env`**: Your actual configuration (NEVER commit to git)
- **`.env.template`**: Basic template with minimal required variables
- **`.env.example`**: Comprehensive example with all variables and comments

### Bicep Parameter Files

For Infrastructure as Code deployment:

1. **Copy template:**
   ```bash
   cp bicep/main.bicepparam.template bicep/main.bicepparam
   ```

2. **Edit `bicep/main.bicepparam`:**
   ```bicep
   using './main.bicep'
   
   param environmentName = 'prod'
   param location = 'eastus2'
   param sqlServerName = 'your-sql-server'
   param sqlDatabaseName = 'your-database'
   // ... other parameters
   ```

3. **NEVER commit `*.bicepparam` files** - they contain secrets!

### Azure Developer CLI

For `azd` deployment, configure in `.azure/`:

```bash
# Initialize azd
azd init

# Configure environment
azd env set AZURE_OPENAI_ENDPOINT "https://your-openai.openai.azure.com/"
azd env set SQL_SERVER "your-server.database.windows.net"
```

---

## Security Best Practices

### 1. Never Commit Secrets

Ensure `.gitignore` includes:
```
.env
.env.local
.env.*.local
*.bicepparam
local.settings.json
```

### 2. Use Azure Key Vault (Recommended for Production)

Instead of environment variables, store secrets in Key Vault:

```bash
# Store secrets in Key Vault
az keyvault secret set --vault-name your-keyvault --name "JwtSecret" --value "your-secret"
az keyvault secret set --vault-name your-keyvault --name "SqlPassword" --value "your-password"
```

Update App Service to reference Key Vault:

```bash
az webapp config appsettings set --name your-app --resource-group your-rg \
  --settings JWT_SECRET="@Microsoft.KeyVault(SecretUri=https://your-keyvault.vault.azure.net/secrets/JwtSecret/)"
```

### 3. Use Managed Identity

Enable managed identity for your App Service:

```bash
az webapp identity assign --name your-app --resource-group your-rg
```

Grant permissions to access resources (SQL, Key Vault, etc.) without passwords.

### 4. Rotate Secrets Regularly

- Generate new JWT secrets every 90 days
- Rotate service principal secrets every 6 months
- Use Azure Key Vault automatic rotation when possible

---

## Validation

### Validate Configuration File

```python
# Run from app/ directory
python -c "
from dotenv import load_dotenv
import os

load_dotenv()

required = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_DEPLOYMENT', 'SQL_SERVER', 'SQL_DATABASE', 'JWT_SECRET']
missing = [var for var in required if not os.getenv(var)]

if missing:
    print(f'❌ Missing required variables: {missing}')
    exit(1)
else:
    print('✅ All required variables configured')
"
```

### Test Database Connection

```python
# Run from app/ directory
python -c "
import pyodbc
from dotenv import load_dotenv
import os

load_dotenv()

server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')

conn_str = f'Driver={{ODBC Driver 18 for SQL Server}};Server={server};Database={database};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

if os.getenv('SQL_USE_AZURE_AUTH') == 'true':
    conn_str += 'Authentication=ActiveDirectoryDefault;'
else:
    conn_str += f'UID={os.getenv(\"SQL_USERNAME\")};PWD={os.getenv(\"SQL_PASSWORD\")};'

try:
    conn = pyodbc.connect(conn_str)
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

### Test Azure OpenAI Connection

```python
# Run from app/ directory
python -c "
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = AzureOpenAI(
    api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
)

try:
    response = client.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        messages=[{'role': 'user', 'content': 'Hello'}],
        max_tokens=10
    )
    print('✅ Azure OpenAI connection successful')
except Exception as e:
    print(f'❌ Azure OpenAI connection failed: {e}')
"
```

---

## Next Steps

After configuration:

1. **Local Testing:** Run the application locally to verify configuration
   ```bash
   cd app
   python main.py
   ```

2. **Deploy to Azure:** Use your preferred deployment method
   ```bash
   # Azure Developer CLI
   azd up
   
   # PowerShell script
   .\deploy.ps1
   ```

3. **Verify Deployment:** Check the deployed application
   ```bash
   curl https://your-app.azurewebsites.net/health
   ```

---

## Troubleshooting

### Configuration Not Loading

**Problem:** Application can't read configuration

**Solution:**
1. Verify `.env` file exists in `app/` directory
2. Check file permissions (should be readable)
3. Ensure no syntax errors (no spaces around `=`)

### Authentication Failures

**Problem:** Can't authenticate to Azure resources

**Solution:**
1. Verify credentials are correct
2. Check service principal has required permissions
3. For Azure AD auth, ensure managed identity is configured
4. Run `az login` to refresh Azure CLI authentication

### Database Connection Errors

**Problem:** Can't connect to SQL database

**Solution:**
1. Verify SQL Server firewall allows your IP
2. Check if Azure services can access server
3. Confirm connection string format is correct
4. For Azure AD auth, verify managed identity has SQL permissions

---

For more help, see:
- [Deployment Guide](DEPLOYMENT.md)
- [Azure Developer CLI Guide](docs/AZD_DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
