# Azure Function Deployment Script for Synthetic Data Generator
# This script deploys the Azure Function to Azure

param(
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-fabric-synthetic-data",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$FunctionAppName = "func-fabric-synth-data-$(Get-Random -Minimum 1000 -Maximum 9999)",
    
    [Parameter(Mandatory=$false)]
    [string]$StorageAccountName = "stfabricsynth$(Get-Random -Minimum 1000 -Maximum 9999)",
    
    [Parameter(Mandatory=$true)]
    [string]$SqlDatabase,
    
    [Parameter(Mandatory=$true)]
    [string]$SqlUsername,
    
    [Parameter(Mandatory=$true)]
    [string]$SqlPassword
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Azure Function Deployment - Synthetic Data Generator" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Check if logged in to Azure
Write-Host "Checking Azure login status..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in to Azure. Please login..." -ForegroundColor Red
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to login to Azure. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ Logged in to Azure as: $($account.user.name)" -ForegroundColor Green
Write-Host "✓ Subscription: $($account.name)" -ForegroundColor Green
Write-Host ""

# Create Resource Group
Write-Host "Creating resource group: $ResourceGroupName..." -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location --output none
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Resource group created/verified" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create resource group" -ForegroundColor Red
    exit 1
}

# Create Storage Account
Write-Host "Creating storage account: $StorageAccountName..." -ForegroundColor Yellow
az storage account create `
    --name $StorageAccountName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku Standard_LRS `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Storage account created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create storage account" -ForegroundColor Red
    exit 1
}

# Create Function App (Linux, Python 3.11)
Write-Host "Creating Function App: $FunctionAppName..." -ForegroundColor Yellow
az functionapp create `
    --resource-group $ResourceGroupName `
    --consumption-plan-location $Location `
    --runtime python `
    --runtime-version 3.11 `
    --functions-version 4 `
    --name $FunctionAppName `
    --storage-account $StorageAccountName `
    --os-type Linux `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Function App created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create Function App" -ForegroundColor Red
    exit 1
}

# Configure App Settings
Write-Host "Configuring application settings..." -ForegroundColor Yellow
az functionapp config appsettings set `
    --name $FunctionAppName `
    --resource-group $ResourceGroupName `
    --settings `
        "SQL_SERVER=aiagentsdemo.database.windows.net" `
        "SQL_DATABASE=$SqlDatabase" `
        "SQL_USERNAME=$SqlUsername" `
        "SQL_PASSWORD=$SqlPassword" `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Application settings configured" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to configure app settings" -ForegroundColor Red
    exit 1
}

# Deploy the Function
Write-Host "Deploying function code..." -ForegroundColor Yellow
func azure functionapp publish $FunctionAppName --python

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Function deployed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to deploy function" -ForegroundColor Red
    exit 1
}

# Display summary
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host ""
Write-Host "Function App Name:    $FunctionAppName" -ForegroundColor Cyan
Write-Host "Resource Group:       $ResourceGroupName" -ForegroundColor Cyan
Write-Host "Location:             $Location" -ForegroundColor Cyan
Write-Host "Function URL:         https://$FunctionAppName.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Verify the function in Azure Portal" -ForegroundColor White
Write-Host "2. Check Application Insights for logs" -ForegroundColor White
Write-Host "3. Test the function manually or wait for the next scheduled run" -ForegroundColor White
Write-Host ""
Write-Host "Monitor the function:" -ForegroundColor Yellow
Write-Host "  az functionapp logs tail --name $FunctionAppName --resource-group $ResourceGroupName" -ForegroundColor White
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
