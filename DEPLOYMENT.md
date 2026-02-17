# Deployment Guide

This guide explains how to deploy the Azure Agent Framework application to Azure App Service after making changes.

## Quick Start

To deploy after making changes:

```powershell
cd C:\code\azure-intelligent-agent
.\deploy.ps1
```

That's it! The script will:
1. Build a fresh Docker image without cache
2. Verify the image contains your changes
3. Push to Azure Container Registry
4. Update Azure App Service
5. Restart the app
6. Verify the deployment was successful

## Script Options

### Skip Build (use existing image)
```powershell
.\deploy.ps1 -SkipBuild
```

### Skip Verification
```powershell
.\deploy.ps1 -SkipVerify
```

### Custom Azure Resources
```powershell
.\deploy.ps1 -ResourceGroup "my-rg" -AppName "my-app" -AcrName "myacr"
```

## What the Script Does

### 1. Build Phase
- Creates a Docker image with timestamp tag (e.g., `release-20260130-110500`)
- Uses `--no-cache` to ensure fresh build with all your changes
- Tags image as both versioned and `latest`

### 2. Verification Phase
- Checks if `admin.html` contains Configuration tab code
- Verifies `admin-dashboard.html` has auth token fix
- Confirms `AdminConfigAgent` backend file exists
- **If verification fails, deployment stops** (preventing bad deployments)

### 3. Push Phase
- Logs into Azure Container Registry
- Pushes both the versioned tag and `latest` tag
- Retrieves image digest for reliable deployment

### 4. Deployment Phase
- Updates App Service to use the new image (by digest, not tag)
- Restarts the app to pull new container
- Waits 45 seconds for app to stabilize

### 5. Validation Phase
- Fetches the deployed admin.html via HTTP
- Confirms Configuration tab is present
- Checks for expected number of tabs
- **Reports failure if changes aren't live**

## Troubleshooting

### "Configuration tab not found in image"
Your local changes weren't included in the build. Possible causes:
- Files not saved before build
- Wrong working directory
- Git ignored files

**Solution**: Verify files are saved, commit changes if needed, run again.

### "Configuration tab NOT found in deployed site"
The image was built and pushed correctly, but Azure served old content. Possible causes:
- Azure cached the old `:latest` tag
- App Service didn't pull the new image
- Browser cache

**Solution**: 
1. Check Azure Portal → Container Settings → verify digest matches build
2. Try restarting app manually: `az webapp restart --name <your-app-service-name> --resource-group <your-resource-group>`
3. Check App Service logs for pull errors

### "Docker push failed"
ACR authentication expired or network issue.

**Solution**: Run `az login` and `az acr login --name <your-acr-name>` manually, then retry.

### "Deployment successful but still see old UI"
Browser caching the old admin.html.

**Solution**: Hard refresh (Ctrl+Shift+R) or open in incognito mode.

## Manual Verification

If you want to manually check the deployed image:

```powershell
# Check what image the app is using
az webapp config show --name <your-app-service-name> --resource-group <your-resource-group> --query "linuxFxVersion" -o tsv

# Check deployed admin.html
$response = Invoke-WebRequest -Uri "https://<your-app-service-name>.azurewebsites.net/static/admin.html" -UseBasicParsing
$response.Content | Select-String -Pattern "Configuration|configManagementTab"
```

## Rollback

If you need to rollback to a previous version:

```powershell
# List recent images
az acr repository show-tags --name <your-acr-name> --repository agentframework --orderby time_desc --top 10

# Deploy specific version
az webapp config container set --name <your-app-service-name> --resource-group <your-resource-group> --docker-custom-image-name "<your-acr-name>.azurecr.io/agentframework:release-20260130-110500"

# Restart
az webapp restart --name <your-app-service-name> --resource-group <your-resource-group>
```

## Best Practices

1. **Always use the deployment script** - Don't manually build/push, the script ensures verification
2. **Review verification output** - If warnings appear, investigate before proceeding
3. **Test locally first** - Run the app locally with Docker before deploying
4. **Keep tags** - Don't delete old image tags, they're your rollback points
5. **Monitor logs** - After deployment, check App Service logs for startup errors

## Files Modified

This deployment includes the following merged features from agentsdemos:

- `app/static/admin.html` - Configuration tab UI and JavaScript
- `app/static/admin-dashboard.html` - Fixed auth token retrieval
- `app/app/agents/admin_config_agent.py` - AdminConfigAgent backend
- `app/app/routes_admin_agents.py` - Configuration API endpoints

## Configuration Tab Features

The newly deployed Configuration tab allows SuperAdmin users to:
- View all agent configurations
- Update agents using natural language commands
- View configuration change history
- Rollback configuration changes
- Manage app and infrastructure settings

Example commands:
- "List all agents and their current configurations"
- "Update SalesAssistant to focus more on Azure AI services"
- "Add web_search tool to AnalyticsAssistant"
- "Show me recent configuration changes"

## Support

If deployment issues persist:
1. Check Azure Portal → App Service → Log Stream for errors
2. Verify ACR credentials: `az acr credential show --name <your-acr-name>`
3. Check App Service has managed identity access to ACR
4. Review container logs: `az webapp log tail --name <your-app-service-name> --resource-group <your-resource-group>`
