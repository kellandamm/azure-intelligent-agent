# Azure Agent Framework Deployment Script
# This script builds, verifies, and deploys the application to Azure App Service
# with comprehensive error handling and verification

param(
    [string]$ResourceGroup = $env:AZURE_RESOURCE_GROUP,
    [string]$AppName = $env:AZURE_APP_NAME,
    [string]$AcrName = $env:AZURE_CONTAINER_REGISTRY,
    [switch]$SkipBuild,
    [switch]$SkipVerify
)

# Validate required parameters
if ([string]::IsNullOrWhiteSpace($ResourceGroup)) {
    throw "ResourceGroup is required. Set AZURE_RESOURCE_GROUP environment variable or provide -ResourceGroup parameter."
}
if ([string]::IsNullOrWhiteSpace($AppName)) {
    throw "AppName is required. Set AZURE_APP_NAME environment variable or provide -AppName parameter."
}
if ([string]::IsNullOrWhiteSpace($AcrName)) {
    throw "AcrName is required. Set AZURE_CONTAINER_REGISTRY environment variable or provide -AcrName parameter."
}

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }

# Start deployment
Write-Info "========================================="
Write-Info "Azure Agent Framework Deployment"
Write-Info "========================================="
Write-Info "Resource Group: $ResourceGroup"
Write-Info "App Name: $AppName"
Write-Info "ACR: $AcrName"
Write-Info ""

try {
    # Change to app directory
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location "$scriptPath\app"
    Write-Info "Working directory: $(Get-Location)"
    Write-Info ""

    # Generate unique tag with timestamp
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $tag = "release-$timestamp"
    $imageName = "$AcrName.azurecr.io/agentframework:$tag"
    $latestImageName = "$AcrName.azurecr.io/agentframework:latest"
    
    Write-Info "Image tag: $tag"
    Write-Info "Image name: $imageName"
    Write-Info ""

    # Step 1: Build Docker image (if not skipped)
    if (-not $SkipBuild) {
        Write-Info "Step 1: Building Docker image..."
        Write-Info "Command: docker build --no-cache -t $imageName -t $latestImageName ."
        Write-Info ""
        
        docker build --no-cache -t $imageName -t $latestImageName .
        
        if ($LASTEXITCODE -ne 0) {
            throw "Docker build failed with exit code $LASTEXITCODE"
        }
        
        Write-Success "✅ Docker image built successfully"
        Write-Info ""
    } else {
        Write-Warning "⚠️ Skipping build (using existing image)"
        Write-Info ""
    }

    # Step 2: Verify image contents (if not skipped)
    if (-not $SkipVerify) {
        Write-Info "Step 2: Verifying image contents..."
        Write-Info ""
        
        # Check if admin.html exists and contains Configuration tab
        Write-Info "Checking admin.html for Configuration tab..."
        $verifyResult = docker run --rm $imageName sh -c "test -f /app/static/admin.html && grep -c 'configManagementTab' /app/static/admin.html || echo 0"
        
        if ($verifyResult -eq "0" -or [string]::IsNullOrWhiteSpace($verifyResult)) {
            throw "Verification failed: Configuration tab not found in admin.html"
        }
        
        Write-Success "✅ Configuration tab found in admin.html ($verifyResult matches)"
        
        # Check if admin-dashboard.html has auth fix
        Write-Info "Checking admin-dashboard.html for auth token fix..."
        $authFixResult = docker run --rm $imageName sh -c "grep -c 'auth_token.*access_token' /app/static/admin-dashboard.html || echo 0"
        
        if ($authFixResult -eq "0" -or [string]::IsNullOrWhiteSpace($authFixResult)) {
            Write-Warning "⚠️ Warning: Auth token fix might not be present in admin-dashboard.html"
        } else {
            Write-Success "✅ Auth token fix found in admin-dashboard.html"
        }
        
        # Check if AdminConfigAgent exists
        Write-Info "Checking for AdminConfigAgent backend..."
        $agentExists = docker run --rm $imageName sh -c "test -f /app/app/agents/admin_config_agent.py && echo 'yes' || echo 'no'"
        
        if ($agentExists -ne "yes") {
            throw "Verification failed: AdminConfigAgent file not found"
        }
        
        Write-Success "✅ AdminConfigAgent backend file found"
        Write-Info ""
    } else {
        Write-Warning "⚠️ Skipping verification"
        Write-Info ""
    }

    # Step 3: Login to ACR
    Write-Info "Step 3: Logging into Azure Container Registry..."
    az acr login --name $AcrName
    
    if ($LASTEXITCODE -ne 0) {
        throw "ACR login failed with exit code $LASTEXITCODE"
    }
    
    Write-Success "✅ Logged into ACR"
    Write-Info ""

    # Step 4: Push images
    Write-Info "Step 4: Pushing images to ACR..."
    Write-Info "Pushing: $imageName"
    docker push $imageName
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker push failed for $imageName"
    }
    
    Write-Info "Pushing: $latestImageName"
    docker push $latestImageName
    
    if ($LASTEXITCODE -ne 0) {
        throw "Docker push failed for $latestImageName"
    }
    
    Write-Success "✅ Images pushed successfully"
    Write-Info ""

    # Step 5: Get image digest for reliability
    Write-Info "Step 5: Getting image digest..."
    $digestOutput = docker inspect --format='{{index .RepoDigests 0}}' $imageName
    
    if ([string]::IsNullOrWhiteSpace($digestOutput)) {
        Write-Warning "⚠️ Could not get digest, using tag instead"
        $deployImage = $imageName
    } else {
        $deployImage = $digestOutput
        Write-Info "Digest: $deployImage"
    }
    Write-Info ""

    # Step 6: Update App Service configuration
    Write-Info "Step 6: Updating App Service configuration..."
    az webapp config container set `
        --name $AppName `
        --resource-group $ResourceGroup `
        --docker-custom-image-name $deployImage
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update App Service configuration"
    }
    
    Write-Success "✅ App Service configuration updated"
    Write-Info ""

    # Step 7: Restart App Service
    Write-Info "Step 7: Restarting App Service..."
    az webapp restart --name $AppName --resource-group $ResourceGroup
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to restart App Service"
    }
    
    Write-Success "✅ App Service restarted"
    Write-Info ""

    # Step 8: Wait for app to stabilize
    Write-Info "Step 8: Waiting for app to stabilize (45 seconds)..."
    Start-Sleep -Seconds 45
    Write-Info ""

    # Step 9: Verify deployment
    Write-Info "Step 9: Verifying deployment..."
    $appUrl = "https://$AppName.azurewebsites.net/static/admin.html"
    Write-Info "Checking: $appUrl"
    
    try {
        $response = Invoke-WebRequest -Uri $appUrl -UseBasicParsing -TimeoutSec 30
        $content = $response.Content
        
        # Check for Configuration tab
        if ($content -match "configManagementTab" -and $content -match "Configuration Assistant") {
            Write-Success "✅ Configuration tab verified in deployment!"
        } else {
            Write-Error "❌ Configuration tab NOT found in deployed site"
            Write-Warning "The deployment completed but the Configuration tab is not visible."
            Write-Warning "This may indicate a caching issue or the wrong image was pulled."
            exit 1
        }
        
        # Check tab count
        $tabMatches = ([regex]::Matches($content, 'class="nav-tab"')).Count
        Write-Info "Found $tabMatches navigation tabs (expected: 4)"
        
        if ($tabMatches -lt 4) {
            Write-Warning "⚠️ Expected 4 tabs but found $tabMatches"
        }
        
    } catch {
        Write-Error "❌ Failed to verify deployment: $_"
        exit 1
    }
    
    Write-Info ""

    # Success!
    Write-Success "========================================="
    Write-Success "✅ DEPLOYMENT SUCCESSFUL!"
    Write-Success "========================================="
    Write-Info "Image: $deployImage"
    Write-Info "App URL: https://$AppName.azurewebsites.net"
    Write-Info "Admin Portal: https://$AppName.azurewebsites.net/static/admin.html"
    Write-Info ""
    Write-Success "Configuration tab is now live! 🎉"
    
} catch {
    Write-Error ""
    Write-Error "========================================="
    Write-Error "❌ DEPLOYMENT FAILED"
    Write-Error "========================================="
    Write-Error "Error: $_"
    Write-Error ""
    Write-Error "Deployment stopped due to error."
    exit 1
}
