# 🧪 Smoke Test Quick Reference

## Quick Commands

### PowerShell
```powershell
# Auto-discover from Azure
.\tests\smoke-test.ps1 -ResourceGroupName "rg-myagents-prod"

# Direct URL
.\tests\smoke-test.ps1 -Url "https://app.azurewebsites.net"

# Local dev
.\tests\smoke-test.ps1 -Url "http://localhost:8000" -SkipAuth

# With auth token
.\tests\smoke-test.ps1 -Url "https://app.azurewebsites.net" -AuthToken "eyJ0..."

# Save results
.\tests\smoke-test.ps1 -Url "https://app.azurewebsites.net" -JsonOutput "results.json"
```

### Python
```bash
# Basic usage
python tests/smoke_test.py --url https://app.azurewebsites.net

# With auth
python tests/smoke_test.py --url https://app.azurewebsites.net --auth-token "eyJ0..."

# Verbose + JSON
python tests/smoke_test.py --url https://app.azurewebsites.net --verbose --json-output results.json
```

## Test Categories

| Category | Tests | What It Checks |
|----------|-------|----------------|
| **Core** | 4 tests | Health, root, static files, API docs |
| **Auth** | 1 test | Login endpoint availability |
| **APIs** | 2 tests | Chat and agent endpoints |
| **Dashboards** | 4 tests | Sales, Analytics, Time Series, Admin |
| **Infrastructure** | 3 tests | Database, CORS, response time |

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| `0` | All passed | ✅ Deploy to production |
| `1` | Some failed | ❌ Review and fix issues |

## Common Fixes

| Issue | Quick Fix |
|-------|-----------|
| Connection timeout | `az webapp start --name <app> --resource-group <rg>` |
| 503 errors | Check logs: `az webapp log tail --name <app> --resource-group <rg>` |
| 401 errors | Add `-SkipAuth` or provide `-AuthToken` |
| Database failed | Grant SQL permissions (see docs) |
| Slow response | Enable Always On, scale up App Service Plan |

## Integration

### GitHub Actions
```yaml
- name: Run Smoke Tests
  run: python tests/smoke_test.py --url ${{ secrets.APP_URL }} --json-output results.json
```

### Azure DevOps
```yaml
- task: PowerShell@2
  inputs:
    filePath: 'tests/smoke-test.ps1'
    arguments: '-Url $(AppServiceUrl) -JsonOutput results.json'
```

### Post-Deployment Script
```powershell
# Add to deploy-complete.ps1
.\tests\smoke-test.ps1 -ResourceGroupName $ResourceGroupName
```

## Troubleshooting Flowchart

```
Test Failed?
    ↓
Check App Running → az webapp show --query state
    ↓
Running? → Check logs → az webapp log tail
    ↓
See errors? → Fix configuration → Redeploy
    ↓
Still failing? → See tests/TROUBLESHOOTING.md
```

## Success Criteria

✅ **Production Ready:**
- All 15 tests pass
- Response time < 2 seconds
- No database errors
- CORS configured

⚠️ **Needs Attention:**
- 1-2 infrastructure tests fail
- Response time 2-3 seconds
- Optional features not working

❌ **Not Ready:**
- Core tests fail
- Database unreachable
- App not responding

## Quick Links

- [Full Test Documentation](README.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Deployment Guide](../README.md)

---

**Remember:** Run smoke tests after every deployment!
