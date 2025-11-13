# ========================================
# Deploy Fabric Azure Function
# ========================================

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$SqlServerName,
    
    [Parameter(Mandatory=$true)]
    [string]$SqlDatabaseName,
    
    [string]$Location = "eastus2",
    [string]$FunctionAppNamePrefix,
    [switch]$SkipFunctionDeploy
)

# Color output functions
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Deploying Fabric Azure Function" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Generate function app name if not provided
if (-not $FunctionAppNamePrefix) {
    $FunctionAppNamePrefix = $SqlServerName.Replace("sql-", "").Replace("-server", "")
}

$functionAppName = "func-fabric-$FunctionAppNamePrefix"
$storageAccountName = "stfabric$($FunctionAppNamePrefix.Replace('-',''))".Substring(0, [Math]::Min(24, "stfabric$($FunctionAppNamePrefix.Replace('-',''))".Length)).ToLower()

Write-Info "Function App: $functionAppName"
Write-Info "Storage Account: $storageAccountName"
Write-Info "Resource Group: $ResourceGroupName"
Write-Info "Location: $Location"
Write-Host ""

try {
    # Check if resource group exists
    Write-Info "Checking resource group..."
    $rgExists = az group exists --name $ResourceGroupName
    if ($rgExists -eq "false") {
        Write-Error "Resource group '$ResourceGroupName' does not exist"
        exit 1
    }
    Write-Success "  ✓ Resource group exists"
    
    # Create storage account for function
    Write-Info "Creating storage account..."
    $storageExists = az storage account show --name $storageAccountName --resource-group $ResourceGroupName 2>$null
    if (-not $storageExists) {
        az storage account create `
            --name $storageAccountName `
            --resource-group $ResourceGroupName `
            --location $Location `
            --sku Standard_LRS `
            --kind StorageV2 `
            --output none
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ Storage account created"
        } else {
            Write-Error "  ✗ Failed to create storage account"
            exit 1
        }
    } else {
        Write-Success "  ✓ Storage account already exists"
    }
    
    # Create function app
    Write-Info "Creating Azure Function App..."
    $functionExists = az functionapp show --name $functionAppName --resource-group $ResourceGroupName 2>$null
    if (-not $functionExists) {
        az functionapp create `
            --name $functionAppName `
            --resource-group $ResourceGroupName `
            --storage-account $storageAccountName `
            --consumption-plan-location $Location `
            --runtime python `
            --runtime-version 3.11 `
            --functions-version 4 `
            --os-type Linux `
            --output none
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ Function app created"
        } else {
            Write-Error "  ✗ Failed to create function app"
            exit 1
        }
    } else {
        Write-Success "  ✓ Function app already exists"
    }
    
    # Enable managed identity
    Write-Info "Enabling system-assigned managed identity..."
    az functionapp identity assign `
        --name $functionAppName `
        --resource-group $ResourceGroupName `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  ✓ Managed identity enabled"
    } else {
        Write-Warning "  ⚠ Failed to enable managed identity"
    }
    
    # Configure app settings
    Write-Info "Configuring app settings..."
    az functionapp config appsettings set `
        --name $functionAppName `
        --resource-group $ResourceGroupName `
        --settings `
            "SQL_SERVER=$SqlServerName.database.windows.net" `
            "SQL_DATABASE=$SqlDatabaseName" `
            "SQL_AUTH_TYPE=AzureAD" `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  ✓ App settings configured"
    } else {
        Write-Error "  ✗ Failed to configure app settings"
        exit 1
    }
    
    if (-not $SkipFunctionDeploy) {
        # Deploy function code
        Write-Info "Deploying function code..."
        Push-Location "$PSScriptRoot\..\function"
        
        # Check if func CLI is installed
        $funcInstalled = Get-Command func -ErrorAction SilentlyContinue
        if (-not $funcInstalled) {
            Write-Warning "  ⚠ Azure Functions Core Tools not installed"
            Write-Warning "    Install from: https://aka.ms/func-install"
            Write-Warning "    Skipping function code deployment"
        } else {
            func azure functionapp publish $functionAppName --python
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "  ✓ Function code deployed"
            } else {
                Write-Error "  ✗ Failed to deploy function code"
                Pop-Location
                exit 1
            }
        }
        
        Pop-Location
    } else {
        Write-Info "Skipping function code deployment (use -SkipFunctionDeploy:$false to deploy)"
    }
    
    # Get function principal ID
    Write-Info "Getting function managed identity..."
    $principalId = az functionapp identity show `
        --name $functionAppName `
        --resource-group $ResourceGroupName `
        --query principalId `
        --output tsv
    
    if ($principalId) {
        Write-Success "  ✓ Function Principal ID: $principalId"
    } else {
        Write-Warning "  ⚠ Could not retrieve principal ID"
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "Fabric Function Deployment Complete!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    
    Write-Info "📋 Next Steps:"
    Write-Host "  1. Grant SQL database access to the function's managed identity:" -ForegroundColor White
    Write-Host ""
    Write-Host "     In Azure Portal → SQL Database → Query editor, run:" -ForegroundColor White
    Write-Host "     CREATE USER [$functionAppName] FROM EXTERNAL PROVIDER;" -ForegroundColor Green
    Write-Host "     ALTER ROLE db_datareader ADD MEMBER [$functionAppName];" -ForegroundColor Green
    Write-Host "     ALTER ROLE db_datawriter ADD MEMBER [$functionAppName];" -ForegroundColor Green
    Write-Host ""
    Write-Host "  2. Test the function:" -ForegroundColor White
    Write-Host "     az functionapp function show -g $ResourceGroupName -n $functionAppName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. View function logs:" -ForegroundColor White
    Write-Host "     az functionapp log tail -g $ResourceGroupName -n $functionAppName" -ForegroundColor Gray
    Write-Host ""
    
    Write-Info "🌐 Function URL:"
    Write-Host "   https://$functionAppName.azurewebsites.net" -ForegroundColor White
    Write-Host ""
    
    exit 0
    
} catch {
    Write-Error "✗ Deployment failed: $_"
    exit 1
}
