# Smoke Test Troubleshooting Guide

This guide helps you diagnose and fix common issues encountered during smoke testing.

## 🔍 Quick Diagnostics

### Check Application Status

```powershell
# PowerShell - Check if app is running
Invoke-WebRequest -Uri "https://your-app.azurewebsites.net/health" -Method Get

# Check App Service status in Azure
az webapp show --name <app-name> --resource-group <rg-name> --query state
```

```bash
# Bash - Check if app is running
curl https://your-app.azurewebsites.net/health

# Check detailed status
az webapp show --name <app-name> --resource-group <rg-name>
```

## 🐛 Common Issues and Solutions

### 1. Connection Timeout

**Symptom:**
```
❌ FAIL - Health Endpoint: Connection timeout after 10 seconds
```

**Possible Causes:**
- Application not started yet
- App Service stopped or suspended
- Network/firewall issues
- Application crashing on startup

**Solutions:**

```powershell
# Check if App Service is running
az webapp show --name <app-name> --resource-group <rg-name> --query state

# Start the App Service if stopped
az webapp start --name <app-name> --resource-group <rg-name>

# Check recent logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Wait longer and retry
Start-Sleep -Seconds 60
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net"
```

### 2. 503 Service Unavailable

**Symptom:**
```
❌ FAIL - Health Endpoint: 503 Service Unavailable
```

**Possible Causes:**
- Application startup failure
- Configuration error
- Missing dependencies
- Database connection failure

**Solutions:**

```powershell
# Check application logs for errors
az webapp log tail --name <app-name> --resource-group <rg-name>

# Check Application Insights for exceptions
az monitor app-insights query \
  --app <app-insights-name> \
  --analytics-query "exceptions | order by timestamp desc | take 20"

# Restart the app
az webapp restart --name <app-name> --resource-group <rg-name>
```

**Common Configuration Issues:**

1. **Missing environment variables**
   ```powershell
   # Verify all required settings are present
   az webapp config appsettings list \
     --name <app-name> \
     --resource-group <rg-name> \
     --query "[].{name:name, value:value}"
   ```

2. **Database connection failure**
   ```powershell
   # Test database connection
   curl https://your-app.azurewebsites.net/api/diagnostic/db-test
   
   # Check if managed identity has SQL permissions
   # Azure Portal → SQL Database → Query Editor
   # Run: SELECT name FROM sys.database_principals WHERE type = 'E'
   ```

### 3. 401 Unauthorized

**Symptom:**
```
❌ FAIL - Chat Endpoint: 401 Unauthorized
```

**Expected Behavior:**
This is actually **normal** if authentication is enabled and no token is provided!

**Solutions:**

**Option 1: Skip auth tests** (for initial testing)
```powershell
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net" -SkipAuth
```

**Option 2: Get JWT token and test with auth**
```powershell
# Get token via API
$loginResponse = Invoke-RestMethod -Uri "https://your-app.azurewebsites.net/api/auth/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"Admin@123"}'

$token = $loginResponse.token

# Run tests with token
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net" -AuthToken $token
```

### 4. Database Connectivity Failed

**Symptom:**
```
❌ FAIL - Database Connectivity: 503 Service Unavailable
```

**Possible Causes:**
- Managed identity not configured
- SQL firewall blocking access
- Missing database user
- Connection string incorrect

**Solutions:**

**Check 1: Verify managed identity is enabled**
```powershell
$identity = az webapp identity show \
  --name <app-name> \
  --resource-group <rg-name> \
  --query principalId -o tsv

if ([string]::IsNullOrEmpty($identity)) {
  Write-Host "Managed identity is NOT enabled"
  # Enable it
  az webapp identity assign --name <app-name> --resource-group <rg-name>
}
```

**Check 2: Verify SQL firewall rules**
```powershell
# Allow Azure services
az sql server firewall-rule create \
  --resource-group <rg-name> \
  --server <sql-server-name> \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

**Check 3: Create database user for managed identity**
```sql
-- Run in SQL Query Editor (Azure Portal)
-- Replace <app-name> with your App Service name
CREATE USER [<app-name>] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [<app-name>];
GO
```

**Check 4: Verify connection string in Key Vault**
```powershell
# Get connection string from Key Vault
az keyvault secret show \
  --vault-name <keyvault-name> \
  --name database-connection-string \
  --query value -o tsv
```

### 5. Response Time Too High

**Symptom:**
```
❌ FAIL - Response Time: Average response time too high: 2500ms
```

**Possible Causes:**
- Underpowered App Service Plan
- Cold start (first request after idle)
- Database query optimization needed
- External API latency

**Solutions:**

**Check 1: Scale up App Service Plan**
```powershell
# Check current SKU
az appservice plan show \
  --name <plan-name> \
  --resource-group <rg-name> \
  --query sku.name

# Scale up to Standard S2
az appservice plan update \
  --name <plan-name> \
  --resource-group <rg-name> \
  --sku S2
```

**Check 2: Enable Always On**
```powershell
az webapp config set \
  --name <app-name> \
  --resource-group <rg-name> \
  --always-on true
```

**Check 3: Check Application Insights performance**
```powershell
# Query slow requests
az monitor app-insights query \
  --app <app-insights-name> \
  --analytics-query "requests | where duration > 1000 | order by duration desc | take 20"
```

**Check 4: Warm up the application**
```powershell
# Make several requests to warm up
1..5 | ForEach-Object {
  Invoke-WebRequest -Uri "https://your-app.azurewebsites.net/health"
  Start-Sleep -Seconds 2
}

# Then run smoke tests
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net"
```

### 6. CORS Headers Missing

**Symptom:**
```
❌ FAIL - CORS Headers: CORS headers not found
```

**Possible Causes:**
- CORS middleware not configured
- App not responding to OPTIONS requests

**Solutions:**

**Check CORS configuration in code:**
```python
# In main.py, ensure CORS middleware is added:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Configure CORS in Azure Portal:**
```powershell
az webapp cors add \
  --name <app-name> \
  --resource-group <rg-name> \
  --allowed-origins '*'
```

### 7. Static Files Not Found

**Symptom:**
```
❌ FAIL - Static Files: 404 Not Found
```

**Possible Causes:**
- Static files not included in deployment
- Incorrect static file path configuration
- Missing static directory

**Solutions:**

**Check 1: Verify static directory exists**
```powershell
# Connect to Kudu console
# https://<app-name>.scm.azurewebsites.net/DebugConsole
# Navigate to /home/site/wwwroot/static

# Or use Azure CLI
az webapp ssh --name <app-name> --resource-group <rg-name>
ls -la /home/site/wwwroot/static
```

**Check 2: Verify deployment includes static files**
```powershell
# Check what was deployed
az webapp deployment list \
  --name <app-name> \
  --resource-group <rg-name>
```

**Check 3: Redeploy with static files**
```powershell
# Ensure static files are in deployment package
cd app
zip -r ../deploy.zip . -i "*.py" "*.html" "*.css" "*.js" "static/*"
az webapp deployment source config-zip \
  --name <app-name> \
  --resource-group <rg-name> \
  --src ../deploy.zip
```

### 8. Multiple Tests Failing

**Symptom:**
```
❌ Failed: 10/15 tests
```

**Possible Causes:**
- Application not running
- Major configuration issue
- Infrastructure deployment incomplete

**Solutions:**

**Full diagnostic checklist:**

```powershell
# 1. Check App Service status
az webapp show --name <app-name> --resource-group <rg-name> --query state

# 2. Check recent deployments
az webapp deployment list --name <app-name> --resource-group <rg-name> --query "[0]"

# 3. Check application logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# 4. Check Application Insights
az monitor app-insights query \
  --app <app-insights-name> \
  --analytics-query "traces | where severityLevel >= 3 | order by timestamp desc | take 50"

# 5. Restart and wait
az webapp restart --name <app-name> --resource-group <rg-name>
Start-Sleep -Seconds 60

# 6. Run smoke tests with verbose output
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net" -VerboseOutput
```

## 🔧 Advanced Diagnostics

### Enable Debug Logging

**In local development:**
```bash
export LOG_LEVEL=DEBUG
python -m uvicorn main:app --reload
```

**In Azure:**
```powershell
az webapp config appsettings set \
  --name <app-name> \
  --resource-group <rg-name> \
  --settings LOG_LEVEL=DEBUG

az webapp restart --name <app-name> --resource-group <rg-name>
```

### View Container Logs

```powershell
# Stream all logs
az webapp log tail --name <app-name> --resource-group <rg-name>

# Download logs
az webapp log download \
  --name <app-name> \
  --resource-group <rg-name> \
  --log-file app-logs.zip
```

### Test Individual Endpoints

```powershell
# Test health endpoint
Invoke-RestMethod -Uri "https://your-app.azurewebsites.net/health"

# Test with detailed output
Invoke-WebRequest -Uri "https://your-app.azurewebsites.net/health" -Verbose

# Test chat endpoint (with auth)
$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}
$body = @{
    message = "test"
    agent_type = "orchestrator"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://your-app.azurewebsites.net/api/chat" `
  -Method Post `
  -Headers $headers `
  -Body $body
```

### Check Resource Health

```powershell
# Check App Service health
az webapp show \
  --name <app-name> \
  --resource-group <rg-name> \
  --query "{name:name, state:state, enabled:enabled, availabilityState:availabilityState}"

# Check SQL Database health
az sql db show \
  --name <db-name> \
  --server <server-name> \
  --resource-group <rg-name> \
  --query "{name:name, status:status}"
```

## 📊 Interpreting Test Results

### Green Tests (All Passed)
```
✅ ALL TESTS PASSED - APPLICATION IS HEALTHY
```
**Action:** No action needed. Application is fully functional.

### Yellow Tests (Some Warning)
```
⚠️  WARN - Response Time: 1800ms (threshold: 2000ms)
```
**Action:** Monitor performance. Consider scaling if consistently high.

### Red Tests (Failed)
```
❌ FAIL - Database Connectivity
```
**Action:** Immediate attention required. Review solutions above.

## 🆘 Getting Help

If smoke tests continue to fail after trying these solutions:

1. **Check logs in this order:**
   - Application Insights exceptions
   - App Service logs
   - SQL Database metrics
   - Key Vault access logs

2. **Gather diagnostic information:**
   ```powershell
   # Run this script to collect all diagnostics
   $diagFile = "diagnostics-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
   
   "=== App Service Status ===" | Out-File $diagFile
   az webapp show --name <app-name> --resource-group <rg-name> | Out-File $diagFile -Append
   
   "=== Recent Logs ===" | Out-File $diagFile -Append
   az webapp log tail --name <app-name> --resource-group <rg-name> | Out-File $diagFile -Append
   
   "=== App Settings ===" | Out-File $diagFile -Append
   az webapp config appsettings list --name <app-name> --resource-group <rg-name> | Out-File $diagFile -Append
   
   Write-Host "Diagnostics saved to: $diagFile"
   ```

3. **Review documentation:**
   - [Main README](../README.md)
   - [Deployment Guide](../docs/QUICK_START.md)
   - [Azure Services Setup](../docs/AZURE_SERVICES_DEPLOYMENT.md)

4. **Open an issue** with:
   - Smoke test output
   - Diagnostic information
   - Deployment method used
   - Azure region

---

**Remember:** Most failures are due to configuration issues, not code bugs. Double-check your parameters!
