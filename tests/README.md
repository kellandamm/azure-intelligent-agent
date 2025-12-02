# Smoke Test Suite

Comprehensive smoke tests to verify Azure Intelligent Agent deployment health and functionality.

## 🎯 Overview

The smoke test suite validates:
- ✅ **Core Functionality** - Health endpoints, static files, API documentation
- ✅ **Authentication** - Login system and JWT token handling
- ✅ **API Endpoints** - Chat, agent, dashboard APIs
- ✅ **Dashboards** - Sales, Analytics, Admin dashboards
- ✅ **Infrastructure** - Database connectivity, CORS, performance
- ✅ **Row-Level Security** - Data filtering by user region

## 🚀 Quick Start

### PowerShell (Recommended for Azure deployments)

```powershell
# Test deployed application (auto-discovers URL)
.\tests\smoke-test.ps1 -ResourceGroupName "rg-myagents-prod"

# Test specific URL
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net"

# Test local development
.\tests\smoke-test.ps1 -Url "http://localhost:8000" -SkipAuth

# Save results to JSON
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net" -JsonOutput "results.json"
```

### Python (Cross-platform)

```bash
# Install dependencies
pip install requests

# Test deployed application
python tests/smoke_test.py --url https://your-app.azurewebsites.net

# Test with authentication
python tests/smoke_test.py --url https://your-app.azurewebsites.net --auth-token YOUR_JWT_TOKEN

# Test local development
python tests/smoke_test.py --url http://localhost:8000 --skip-auth

# Verbose output with JSON results
python tests/smoke_test.py --url https://your-app.azurewebsites.net --verbose --json-output results.json
```

## 📋 Test Categories

### 1. Core Functionality Tests
- **Health Endpoint** - Validates `/health` returns healthy status
- **Root Endpoint** - Ensures root URL is accessible
- **Static Files** - Verifies static file serving (login page)
- **OpenAPI Docs** - Checks API documentation at `/docs`

### 2. Authentication Tests
- **Authentication Endpoint** - Tests `/api/auth/login` availability
- **JWT Token Handling** - Validates token-based authentication

### 3. API Endpoint Tests
- **Chat Endpoint** - Tests `/api/chat` for orchestrator agent
- **Agent Endpoint** - Tests `/api/agent/chat` for specialist agents

### 4. Dashboard Tests
- **Sales Dashboard** - Validates `/api/sales/summary` endpoint
- **Analytics Dashboard** - Tests `/api/analytics/metrics` endpoint
- **Time Series** - Checks `/api/analytics/timeseries` data availability
- **Admin Dashboard** - Ensures `/admin` page loads

### 5. Infrastructure Tests
- **Database Connectivity** - Tests database connection via diagnostic endpoint
- **CORS Headers** - Validates CORS configuration
- **Response Time** - Measures average response time (< 2 seconds)

## 🔧 Usage Scenarios

### Post-Deployment Verification

After deploying with `azd up` or PowerShell scripts:

```powershell
# Automatically discover and test your deployment
.\tests\smoke-test.ps1 -ResourceGroupName "rg-myagents-prod"
```

### CI/CD Pipeline Integration

Add to your Azure DevOps or GitHub Actions pipeline:

```yaml
# GitHub Actions
- name: Run Smoke Tests
  run: |
    python tests/smoke_test.py --url ${{ secrets.APP_URL }} --json-output smoke-test-results.json
  
- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: smoke-test-results
    path: smoke-test-results.json
```

```yaml
# Azure DevOps
- task: PowerShell@2
  displayName: 'Run Smoke Tests'
  inputs:
    filePath: 'tests/smoke-test.ps1'
    arguments: '-Url $(AppServiceUrl) -JsonOutput $(Build.ArtifactStagingDirectory)/smoke-test-results.json'
```

### Local Development Testing

```bash
# Start your local dev server
python -m uvicorn main:app --reload

# In another terminal, run smoke tests
python tests/smoke_test.py --url http://localhost:8000 --skip-auth
```

### Monitoring & Health Checks

Set up automated health checks:

```powershell
# Run every 5 minutes via Task Scheduler
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net" -JsonOutput "C:\logs\health-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
```

## 📊 Understanding Results

### Successful Test Run

```
✅ PASS - Health Endpoint (145ms)
✅ PASS - Root Endpoint (89ms)
✅ PASS - Static Files (234ms)
...
========================================
📊 TEST SUMMARY
========================================
Total Tests: 15
✅ Passed: 15
⏱️  Duration: 3.42s

✅ ALL TESTS PASSED - APPLICATION IS HEALTHY
```

### Failed Test Run

```
❌ FAIL - Health Endpoint: Connection timeout
✅ PASS - Root Endpoint (89ms)
...
========================================
📊 TEST SUMMARY
========================================
Total Tests: 15
✅ Passed: 14
❌ Failed: 1
⏱️  Duration: 8.21s

❌ FAILED TESTS:
  • Health Endpoint
    Error: Connection timeout after 10 seconds

❌ SOME TESTS FAILED - REVIEW ERRORS ABOVE
```

## 🎛️ Advanced Options

### PowerShell Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-Url` | Base URL of application | `-Url "https://app.azurewebsites.net"` |
| `-ResourceGroupName` | Auto-discover URL from Azure | `-ResourceGroupName "rg-myagents"` |
| `-AuthToken` | JWT token for protected endpoints | `-AuthToken "eyJ0eXAi..."` |
| `-SkipAuth` | Skip authentication tests | `-SkipAuth` |
| `-VerboseOutput` | Enable detailed logging | `-VerboseOutput` |
| `-JsonOutput` | Save results to JSON file | `-JsonOutput "results.json"` |

### Python Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--url` | Base URL of application (required) | `--url https://app.azurewebsites.net` |
| `--auth-token` | JWT token for protected endpoints | `--auth-token "eyJ0eXAi..."` |
| `--skip-auth` | Skip authentication tests | `--skip-auth` |
| `--verbose` | Enable detailed logging | `--verbose` |
| `--json-output` | Save results to JSON file | `--json-output results.json` |

## 🔒 Testing with Authentication

### Get JWT Token

1. **Via API**:
```bash
curl -X POST https://your-app.azurewebsites.net/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'
```

2. **Via Browser Console** (on login page):
```javascript
localStorage.getItem('token')
```

3. **Use Token in Tests**:
```powershell
.\tests\smoke-test.ps1 -Url "https://your-app.azurewebsites.net" -AuthToken "eyJ0eXAi..."
```

## 🐛 Troubleshooting

### Common Issues

#### Connection Timeout
```
❌ FAIL - Health Endpoint: Connection timeout
```
**Solution**: Check if application is running and accessible at the URL

#### 401 Unauthorized
```
❌ FAIL - Chat Endpoint: 401 Unauthorized
```
**Solution**: This is expected if authentication is enabled. Either:
- Provide `-AuthToken` parameter with valid JWT
- Use `-SkipAuth` for public endpoint testing only

#### Database Connectivity Failed
```
❌ FAIL - Database Connectivity: 503 Service Unavailable
```
**Solution**: 
- Verify database connection string in Key Vault
- Check SQL firewall rules allow Azure services
- Ensure managed identity has proper SQL permissions

#### Response Time Too High
```
❌ FAIL - Response Time: Average response time too high: 2500ms
```
**Solution**:
- Check application scaling (App Service Plan tier)
- Review Application Insights performance metrics
- Consider enabling CDN for static files

## 📈 Interpreting JSON Output

```json
{
  "timestamp": "2025-12-02T10:30:45Z",
  "base_url": "https://your-app.azurewebsites.net",
  "passed": true,
  "total_tests": 15,
  "passed_tests": 15,
  "failed_tests": 0,
  "duration_seconds": 3.42,
  "results": [
    {
      "name": "Health Endpoint",
      "passed": true,
      "duration_ms": 145.23,
      "error_message": null,
      "details": {
        "status": "healthy",
        "version": "1.0.0"
      }
    }
  ]
}
```

## 🔄 Integration with Deployment

The smoke tests are automatically integrated into the deployment process:

1. **After `deploy-complete.ps1` finishes**, you'll be prompted:
   ```
   🧪 Run smoke tests now? (Recommended)
   Enter 'y' to run smoke tests, any other key to skip: 
   ```

2. **Tests run automatically** and report results

3. **Results are saved** to deployment logs for troubleshooting

## 🎓 Best Practices

1. **Always run smoke tests** after deployment
2. **Include in CI/CD pipelines** for automated verification
3. **Monitor trends** by comparing JSON outputs over time
4. **Set up alerts** if critical tests fail
5. **Run before major changes** to establish baseline
6. **Test both production and staging** environments

## 📞 Support

If tests consistently fail:
1. Check [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)
2. Review Application Insights logs
3. Verify all prerequisites are met
4. Check Azure resource health

## 🔗 Related Documentation

- [Deployment Guide](../README.md)
- [PowerShell Scripts Guide](../scripts/README.md)
- [Azure Developer CLI Guide](../docs/AZD_DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)

---

**Need Help?** Open an issue or check the documentation!
