#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    Complete turnkey deployment of Azure Intelligent Agent Starter

.DESCRIPTION
    This master script orchestrates the complete deployment process for the
    Azure Intelligent Agent Starter template:
    1. Prepares application code
    2. Deploys infrastructure to Azure
    3. Configures SQL database access
    4. Deploys application code
    5. Verifies deployment
    6. (Optional) Deploys Fabric data management

.PARAMETER ResourceGroupName
    Name of the Azure resource group (will be created if it doesn't exist)

.PARAMETER Location
    Azure region for deployment (default: eastus2)

.PARAMETER ParametersFile
    Path to Bicep parameters file (default: ../bicep/main.bicepparam)

.PARAMETER SourceAppDir
    Source directory containing application code (default: auto-detect parent folder)

.PARAMETER SkipPreparation
    Skip application code preparation step

.PARAMETER SkipInfrastructure
    Skip infrastructure deployment

.PARAMETER SkipSqlConfig
    Skip manual SQL configuration step

.PARAMETER SkipAppCode
    Skip application code deployment

.PARAMETER AutoConfirmSql
    Automatically continue without waiting for SQL configuration

.PARAMETER DeployFabric
    Deploy Fabric data management component (synthetic data generation)

.PARAMETER GenerateInitialData
    Generate initial synthetic data during Fabric deployment

.EXAMPLE
    .\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod"
    
.EXAMPLE
    .\deploy-complete.ps1 -ResourceGroupName "rg-myagents-dev" -Location "westus2" -AutoConfirmSql
    
.EXAMPLE
    .\deploy-complete.ps1 -ResourceGroupName "rg-myagents-prod" -DeployFabric -GenerateInitialData
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus2",
    
    [Parameter(Mandatory = $false)]
    [string]$ParametersFile = "",
    
    [Parameter(Mandatory = $false)]
    [string]$SourceAppDir = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipPreparation,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipInfrastructure,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipSqlConfig,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipAppCode,
    
    [Parameter(Mandatory = $false)]
    [switch]$AutoConfirmSql,
    
    [Parameter(Mandatory = $false)]
    [switch]$DeployFabric,
    
    [Parameter(Mandatory = $false)]
    [switch]$GenerateInitialData
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param([string]$Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning-Custom { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error-Custom { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param([string]$Message) Write-Host "`n========================================" -ForegroundColor Magenta; Write-Host $Message -ForegroundColor Magenta; Write-Host "========================================`n" -ForegroundColor Magenta }

# ========================================
# Initialize
# ========================================

Write-Host @"

    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🚀 AZURE INTELLIGENT AGENT STARTER DEPLOYMENT 🚀        ║
    ║                                                           ║
    ║   Turnkey deployment for intelligent AI agents           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

$startTime = Get-Date

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TemplateRoot = Split-Path -Parent $ScriptDir

Write-Info "Template Root: $TemplateRoot"
Write-Info "Resource Group: $ResourceGroupName"
Write-Info "Location: $Location"
Write-Host ""

# Set default parameters file
if ([string]::IsNullOrEmpty($ParametersFile)) {
    $ParametersFile = Join-Path $TemplateRoot "bicep\main.bicepparam"
}

# Set default source app directory
if ([string]::IsNullOrEmpty($SourceAppDir)) {
    $SourceAppDir = Split-Path -Parent $TemplateRoot
}

# ========================================
# Pre-flight Checks
# ========================================

Write-Step "🔍 Pre-flight Checks"

# Check Azure CLI
Write-Info "Checking Azure CLI..."
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI version: $($azVersion.'azure-cli')"
} catch {
    Write-Error-Custom "Azure CLI not found. Please install: https://aka.ms/installazurecli"
    exit 1
}

# Check Azure login
Write-Info "Checking Azure login..."
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Success "Logged in as: $($account.user.name)"
    Write-Info "Subscription: $($account.name) ($($account.id))"
} catch {
    Write-Error-Custom "Not logged in to Azure. Run: az login"
    exit 1
}

# Check parameters file
if (-not (Test-Path $ParametersFile)) {
    Write-Error-Custom "Parameters file not found: $ParametersFile"
    Write-Info "Please create a parameters file from main.bicepparam.template"
    exit 1
}
Write-Success "Parameters file found: $ParametersFile"

# Check source app directory
if (-not $SkipPreparation -and -not $SkipAppCode) {
    if (-not (Test-Path $SourceAppDir)) {
        Write-Error-Custom "Source application directory not found: $SourceAppDir"
        exit 1
    }
    Write-Success "Source application directory found: $SourceAppDir"
}

Write-Success "All pre-flight checks passed!"

# ========================================
# Step 1: Prepare Application Code
# ========================================

if (-not $SkipPreparation -and -not $SkipAppCode) {
    Write-Step "📦 Step 1: Preparing Application Code"
    
    $prepareScript = Join-Path $ScriptDir "prepare-app.ps1"
    $appDir = Join-Path $TemplateRoot "app"
    
    if (Test-Path $prepareScript) {
        Write-Info "Running application preparation script..."
        & $prepareScript -SourceDir $SourceAppDir -DestinationDir $appDir -Force
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Application preparation failed"
            exit 1
        }
        
        Write-Success "Application code prepared successfully"
    } else {
        Write-Warning-Custom "Preparation script not found: $prepareScript"
        Write-Info "Assuming app folder is already prepared..."
    }
} else {
    Write-Info "⏭️  Skipping application preparation"
}

# ========================================
# Step 2: Deploy Infrastructure
# ========================================

if (-not $SkipInfrastructure) {
    Write-Step "🏗️  Step 2: Deploying Infrastructure"
    
    $deployScript = Join-Path $ScriptDir "deploy.ps1"
    
    if (-not (Test-Path $deployScript)) {
        Write-Error-Custom "Deploy script not found: $deployScript"
        exit 1
    }
    
    Write-Info "Running infrastructure deployment..."
    
    $deployParams = @(
        "-ResourceGroupName", $ResourceGroupName,
        "-Location", $Location,
        "-ParametersFile", $ParametersFile
    )
    
    if ($SkipAppCode) {
        $deployParams += "-SkipAppCode"
    }
    
    if ($SkipSqlConfig -or $AutoConfirmSql) {
        # We'll handle SQL config in this script
        Write-Info "Will handle SQL configuration in this script..."
    }
    
    & $deployScript @deployParams
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Infrastructure deployment failed"
        exit 1
    }
    
    Write-Success "Infrastructure deployed successfully"
} else {
    Write-Info "⏭️  Skipping infrastructure deployment"
}

# ========================================
# Step 3: Configure SQL Database (Smart)
# ========================================

if (-not $SkipSqlConfig -and -not $SkipInfrastructure) {
    Write-Step "🗄️  Step 3: Configuring SQL Database Access"
    
    # Get deployment outputs
    Write-Info "Retrieving deployment information..."
    
    try {
        $deployment = az deployment group show `
            --name "intelligent-agent-deployment-$(Get-Date -Format 'yyyyMMdd')*" `
            --resource-group $ResourceGroupName `
            --query "properties.outputs" `
            --output json 2>$null | ConvertFrom-Json
        
        if (-not $deployment) {
            # Try alternative deployment name
            $deployments = az deployment group list `
                --resource-group $ResourceGroupName `
                --query "[?contains(name, 'intelligent-agent')].name" `
                --output json | ConvertFrom-Json
            
            if ($deployments.Count -gt 0) {
                $deployment = az deployment group show `
                    --name $deployments[0] `
                    --resource-group $ResourceGroupName `
                    --query "properties.outputs" `
                    --output json | ConvertFrom-Json
            }
        }
        
        if ($deployment) {
            $webAppName = $deployment.webAppName.value
            $sqlServerName = $deployment.sqlServerName.value
            $sqlDatabaseName = $deployment.sqlDatabaseName.value
            
            Write-Info "Web App: $webAppName"
            Write-Info "SQL Server: $sqlServerName"
            Write-Info "SQL Database: $sqlDatabaseName"
            
            if ($AutoConfirmSql) {
                Write-Warning-Custom "Auto-confirm enabled. Please configure SQL manually later if needed."
                Write-Host @"

SQL Configuration Commands:
---------------------------------------
CREATE USER [$webAppName] FROM EXTERNAL PROVIDER;
ALTER ROLE db_owner ADD MEMBER [$webAppName];
---------------------------------------

Run these in: Azure Portal → SQL Database → Query Editor

"@ -ForegroundColor Yellow
            } else {
                Write-Host @"

🔐 SQL Database Access Configuration Required

To grant the Web App managed identity access to SQL Database:

1. Open Azure Portal
2. Navigate to: SQL Databases → $sqlDatabaseName → Query Editor
3. Authenticate using your Azure AD account
4. Run these SQL commands:

   ╔════════════════════════════════════════════════════╗
   ║                                                    ║
   ║  CREATE USER [$webAppName] FROM EXTERNAL PROVIDER; ║
   ║  ALTER ROLE db_owner ADD MEMBER [$webAppName];     ║
   ║                                                    ║
   ╚════════════════════════════════════════════════════╝

5. Press Enter when complete...

"@ -ForegroundColor Yellow
                
                Read-Host "Press Enter to continue after SQL configuration"
                Write-Success "SQL configuration acknowledged"
            }
        } else {
            Write-Warning-Custom "Could not retrieve deployment information"
            Write-Info "Please configure SQL access manually using the instructions in the deployment output"
        }
    } catch {
        Write-Warning-Custom "Error retrieving deployment info: $_"
        Write-Info "Please configure SQL access manually"
    }
} else {
    Write-Info "⏭️  Skipping SQL configuration"
}

# ========================================
# Step 4: Deploy Application Code
# ========================================

if (-not $SkipAppCode) {
    Write-Step "🚀 Step 4: Deploying Application Code"
    
    $appDir = Join-Path $TemplateRoot "app"
    
    # Verify app directory exists
    if (-not (Test-Path $appDir)) {
        Write-Error-Custom "Application directory not found: $appDir"
        Write-Info "Please run with -SkipPreparation=$false or prepare the app folder manually"
        exit 1
    }
    
    # Get web app name
    Write-Info "Retrieving web app information..."
    
    try {
        $webAppName = ""
        $deployment = az deployment group show `
            --name "intelligent-agent-deployment-$(Get-Date -Format 'yyyyMMdd')*" `
            --resource-group $ResourceGroupName `
            --query "properties.outputs.webAppName.value" `
            --output tsv 2>$null
        
        if ([string]::IsNullOrEmpty($deployment)) {
            # Fallback: list all deployments
            $deployments = az deployment group list `
                --resource-group $ResourceGroupName `
                --query "[?contains(name, 'intelligent-agent')].name" `
                --output json | ConvertFrom-Json
            
            if ($deployments.Count -gt 0) {
                $webAppName = az deployment group show `
                    --name $deployments[0] `
                    --resource-group $ResourceGroupName `
                    --query "properties.outputs.webAppName.value" `
                    --output tsv
            }
        } else {
            $webAppName = $deployment
        }
        
        if ([string]::IsNullOrEmpty($webAppName)) {
            Write-Error-Custom "Could not retrieve web app name from deployment"
            exit 1
        }
        
        Write-Success "Web App: $webAppName"
        
    } catch {
        Write-Error-Custom "Error retrieving web app information: $_"
        exit 1
    }
    
    # Create deployment package
    Write-Info "Creating deployment package..."
    $timestamp = Get-Date -Format 'yyyyMMddHHmmss'
    $tempZip = Join-Path $env:TEMP "intelligent-agent-deployment-$timestamp.zip"
    
    Compress-Archive -Path "$appDir\*" -DestinationPath $tempZip -Force
    $zipSize = [math]::Round((Get-Item $tempZip).Length / 1MB, 2)
    Write-Success "Package created: $zipSize MB"
    
    # Deploy to Azure
    Write-Info "Deploying to Azure App Service..."
    Write-Warning-Custom "This may take 3-5 minutes. Azure will install dependencies and start the app."
    
    az webapp deployment source config-zip `
        --resource-group $ResourceGroupName `
        --name $webAppName `
        --src $tempZip `
        --timeout 600 `
        --output none
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Application deployment failed"
        Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
        exit 1
    }
    
    # Clean up
    Remove-Item $tempZip -Force
    Write-Success "Application deployed successfully!"
    
    # Restart web app
    Write-Info "Restarting web app to apply changes..."
    az webapp restart --name $webAppName --resource-group $ResourceGroupName --output none
    Write-Success "Web app restarted"
    
} else {
    Write-Info "⏭️  Skipping application code deployment"
}

# ========================================
# Step 5: Verify Deployment
# ========================================

Write-Step "✅ Step 5: Verifying Deployment"

try {
    # Get deployment outputs
    $deployment = az deployment group show `
        --name "intelligent-agent-deployment-$(Get-Date -Format 'yyyyMMdd')*" `
        --resource-group $ResourceGroupName `
        --query "properties.outputs" `
        --output json 2>$null | ConvertFrom-Json
    
    if (-not $deployment) {
        $deployments = az deployment group list `
            --resource-group $ResourceGroupName `
            --query "[?contains(name, 'intelligent-agent')].name" `
            --output json | ConvertFrom-Json
        
        if ($deployments.Count -gt 0) {
            $deployment = az deployment group show `
                --name $deployments[0] `
                --resource-group $ResourceGroupName `
                --query "properties.outputs" `
                --output json | ConvertFrom-Json
        }
    }
    
    if ($deployment) {
        $webAppUrl = $deployment.webAppUrl.value
        $webAppName = $deployment.webAppName.value
        
        Write-Info "Checking application health..."
        Start-Sleep -Seconds 10  # Give app time to start
        
        try {
            $response = Invoke-WebRequest -Uri "$webAppUrl/health" -Method GET -TimeoutSec 30 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Application is responding! Health check passed."
            }
        } catch {
            Write-Warning-Custom "Could not verify health endpoint (this is normal during startup)"
            Write-Info "The application may still be starting up. Check in a few minutes."
        }
    }
} catch {
    Write-Warning-Custom "Could not verify deployment automatically"
}

# ========================================
# Step 6: Deploy Fabric Data Management (Optional)
# ========================================

if ($DeployFabric) {
    Write-Step "📊 Step 6: Deploying Fabric Data Management"
    
    # Get deployment outputs
    Write-Info "Retrieving SQL Database information..."
    
    try {
        $deployment = $null
        $deployments = az deployment group list `
            --resource-group $ResourceGroupName `
            --query "[?contains(name, 'intelligent-agent')].name" `
            --output json | ConvertFrom-Json
        
        if ($deployments.Count -gt 0) {
            $deployment = az deployment group show `
                --name $deployments[0] `
                --resource-group $ResourceGroupName `
                --query "properties.outputs" `
                --output json | ConvertFrom-Json
        }
        
        if (-not $deployment) {
            Write-Error-Custom "Could not retrieve deployment information. Please deploy infrastructure first."
            exit 1
        }
        
        $sqlServerName = $deployment.sqlServerName.value
        $sqlDatabaseName = $deployment.sqlDatabaseName.value
        
        Write-Info "SQL Server: $sqlServerName"
        Write-Info "SQL Database: $sqlDatabaseName"
        
        # Set environment variables for Fabric scripts
        $env:SQL_SERVER = "$sqlServerName.database.windows.net"
        $env:SQL_DATABASE = $sqlDatabaseName
        
        # Run database setup
        Write-Info "Setting up database schema and data..."
        $setupScript = Join-Path $TemplateRoot "fabric\scripts\setup-database.ps1"
        
        if (-not (Test-Path $setupScript)) {
            Write-Error-Custom "Fabric setup script not found: $setupScript"
            exit 1
        }
        
        $setupParams = @(
            "-SqlServer", $env:SQL_SERVER,
            "-SqlDatabase", $env:SQL_DATABASE
        )
        
        if ($GenerateInitialData) {
            $setupParams += "-GenerateData"
        }
        
        & $setupScript @setupParams
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Fabric database setup failed"
            exit 1
        }
        
        Write-Success "Database schema and data configured successfully!"
        
        # Deploy Fabric Function
        Write-Info "Deploying Fabric Azure Function..."
        $functionScript = Join-Path $TemplateRoot "fabric\scripts\deploy-fabric-function.ps1"
        
        if (-not (Test-Path $functionScript)) {
            Write-Error-Custom "Fabric function script not found: $functionScript"
            exit 1
        }
        
        $functionParams = @(
            "-ResourceGroupName", $ResourceGroupName,
            "-SqlServerName", $sqlServerName,
            "-SqlDatabaseName", $sqlDatabaseName,
            "-Location", $Location
        )
        
        & $functionScript @functionParams
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Fabric function deployment failed"
            exit 1
        }
        
        Write-Success "Fabric data management deployed successfully!"
        
        Write-Host @"

╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  📊 FABRIC DATA MANAGEMENT - POST-DEPLOYMENT STEPS         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

To complete Fabric setup, grant SQL access to the Function:

1. Open Azure Portal
2. Navigate to: SQL Databases → $sqlDatabaseName → Query Editor
3. Authenticate using your Azure AD account
4. Run these SQL commands:

   CREATE USER [func-fabric-*] FROM EXTERNAL PROVIDER;
   ALTER ROLE db_datareader ADD MEMBER [func-fabric-*];
   ALTER ROLE db_datawriter ADD MEMBER [func-fabric-*];

   (Replace * with your function app name from output above)

"@ -ForegroundColor Cyan
        
    } catch {
        Write-Error-Custom "Error during Fabric deployment: $_"
        Write-Info "You can deploy Fabric manually using the scripts in fabric/scripts/"
        exit 1
    }
} else {
    Write-Info "⏭️  Skipping Fabric data management deployment (use -DeployFabric to enable)"
}

# ========================================
# Summary
# ========================================

$endTime = Get-Date
$duration = $endTime - $startTime
$durationMinutes = [math]::Round($duration.TotalMinutes, 1)

Write-Host "`n`n"
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "║   🎉 DEPLOYMENT COMPLETE! 🎉                              ║" -ForegroundColor Green
Write-Host "║                                                           ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "  Duration: $durationMinutes minutes" -ForegroundColor White
Write-Host "  Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "  Region: $Location" -ForegroundColor White

if ($deployment) {
    Write-Host "`n🌐 Application URL:" -ForegroundColor Cyan
    Write-Host "  $($deployment.webAppUrl.value)" -ForegroundColor Green
    
    Write-Host "`n📋 Resource Details:" -ForegroundColor Cyan
    Write-Host "  Web App: $($deployment.webAppName.value)" -ForegroundColor White
    Write-Host "  SQL Server: $($deployment.sqlServerName.value)" -ForegroundColor White
    Write-Host "  SQL Database: $($deployment.sqlDatabaseName.value)" -ForegroundColor White
    
    if ($deployment.keyVaultName.value) {
        Write-Host "  Key Vault: $($deployment.keyVaultName.value)" -ForegroundColor White
    }
    
    if ($DeployFabric) {
        Write-Host "`n📊 Fabric Data Management:" -ForegroundColor Cyan
        Write-Host "  Status: Deployed" -ForegroundColor Green
        Write-Host "  Database Schema: Deployed" -ForegroundColor White
        if ($GenerateInitialData) {
            Write-Host "  Initial Data: Generated" -ForegroundColor White
        }
        Write-Host "  Function App: func-fabric-* (see output above)" -ForegroundColor White
    }
}

Write-Host "`n💡 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run smoke tests to verify deployment" -ForegroundColor White
Write-Host "     .\tests\smoke-test.ps1 -ResourceGroupName $ResourceGroupName" -ForegroundColor Gray
Write-Host "  2. Open the application URL in your browser" -ForegroundColor White
Write-Host "  3. Test the agent endpoints" -ForegroundColor White
if ($DeployFabric) {
    Write-Host "  4. Complete Fabric SQL grants (see instructions above)" -ForegroundColor White
    Write-Host "  5. View database data: python fabric\database\view_tables.py" -ForegroundColor White
    Write-Host "  6. Monitor logs: az webapp log tail --name <web-app-name> --resource-group $ResourceGroupName" -ForegroundColor White
    Write-Host "  7. View metrics in Azure Portal → Application Insights" -ForegroundColor White
} else {
    Write-Host "  4. Monitor logs: az webapp log tail --name <web-app-name> --resource-group $ResourceGroupName" -ForegroundColor White
    Write-Host "  5. View metrics in Azure Portal → Application Insights" -ForegroundColor White
}

Write-Host "`n📚 Documentation:" -ForegroundColor Cyan
Write-Host "  README: $TemplateRoot\README.md" -ForegroundColor White
Write-Host "  Troubleshooting: $TemplateRoot\docs\QUICK_START.md" -ForegroundColor White
Write-Host "  Smoke Tests: $TemplateRoot\tests\README.md" -ForegroundColor White

Write-Host "`n✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host ""

# ========================================
# Optional: Run Smoke Tests
# ========================================

$runSmokeTests = $false
if ($PSCmdlet.ShouldProcess("Run smoke tests to verify deployment?", "Smoke Tests", "Run")) {
    Write-Host "`n🧪 Run smoke tests now? (Recommended)" -ForegroundColor Yellow
    $response = Read-Host "  Enter 'y' to run smoke tests, any other key to skip"
    $runSmokeTests = ($response -eq 'y' -or $response -eq 'Y')
}

if ($runSmokeTests) {
    Write-Step "🧪 Running Smoke Tests"
    
    $smokeTestScript = Join-Path $TemplateRoot "tests\smoke-test.ps1"
    if (Test-Path $smokeTestScript) {
        try {
            & $smokeTestScript -ResourceGroupName $ResourceGroupName -VerboseOutput
            Write-Success "Smoke tests completed"
        }
        catch {
            Write-Warning-Custom "Smoke tests failed: $_"
            Write-Info "You can run smoke tests manually later:"
            Write-Info "  .\tests\smoke-test.ps1 -ResourceGroupName $ResourceGroupName"
        }
    } else {
        Write-Warning-Custom "Smoke test script not found at: $smokeTestScript"
    }
} else {
    Write-Info "Skipping smoke tests. Run manually later:"
    Write-Info "  .\tests\smoke-test.ps1 -ResourceGroupName $ResourceGroupName"
}
