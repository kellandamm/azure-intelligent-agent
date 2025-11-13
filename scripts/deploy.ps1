#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    Deploys the Azure Agent Framework Application to Azure

.DESCRIPTION
    This script automates the deployment of the Agent Framework application to Azure.
    It creates all necessary Azure resources using Bicep templates and deploys the application code.

.PARAMETER ResourceGroupName
    Name of the Azure resource group (will be created if it doesn't exist)

.PARAMETER Location
    Azure region for deployment (default: eastus2)

.PARAMETER ParametersFile
    Path to Bicep parameters file (default: main.bicepparam)

.PARAMETER SkipInfrastructure
    Skip infrastructure deployment and only deploy application code

.PARAMETER SkipAppCode
    Skip application code deployment and only deploy infrastructure

.EXAMPLE
    .\deploy.ps1 -ResourceGroupName "rg-myagents-prod" -Location "eastus2"
    
.EXAMPLE
    .\deploy.ps1 -ResourceGroupName "rg-myagents-dev" -SkipInfrastructure
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus2",
    
    [Parameter(Mandatory = $false)]
    [string]$ParametersFile = "main.bicepparam",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipInfrastructure,
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipAppCode
)

# ========================================
# Configuration
# ========================================
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BicepDir = Join-Path $ScriptDir "..\bicep"
$AppDir = Join-Path $ScriptDir "..\app"
$MainBicepFile = Join-Path $BicepDir "main.bicep"
$ParametersFilePath = Join-Path $BicepDir $ParametersFile

# ========================================
# Functions
# ========================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

# ========================================
# Pre-flight Checks
# ========================================

Write-Step "Pre-flight Checks"

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Success "Azure CLI version: $($azVersion.'azure-cli')"
} catch {
    Write-Error-Custom "Azure CLI is not installed. Please install from: https://aka.ms/installazurecli"
    exit 1
}

# Check if logged in to Azure
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Success "Logged in as: $($account.user.name)"
    Write-Info "Subscription: $($account.name) ($($account.id))"
} catch {
    Write-Warning-Custom "Not logged in to Azure. Running 'az login'..."
    az login
}

# Check if Bicep template exists
if (-not (Test-Path $MainBicepFile)) {
    Write-Error-Custom "Bicep template not found: $MainBicepFile"
    exit 1
}
Write-Success "Bicep template found"

# Check if parameters file exists
if (-not $SkipInfrastructure) {
    if (-not (Test-Path $ParametersFilePath)) {
        Write-Error-Custom "Parameters file not found: $ParametersFilePath"
        Write-Info "Please create a parameters file from the template: main.bicepparam"
        exit 1
    }
    Write-Success "Parameters file found"
}

# ========================================
# Step 1: Create Resource Group
# ========================================

if (-not $SkipInfrastructure) {
    Write-Step "Step 1: Creating Resource Group"
    
    $rgExists = az group exists --name $ResourceGroupName --output tsv
    
    if ($rgExists -eq "true") {
        Write-Info "Resource group '$ResourceGroupName' already exists"
    } else {
        Write-Info "Creating resource group: $ResourceGroupName in $Location"
        az group create --name $ResourceGroupName --location $Location --output none
        Write-Success "Resource group created"
    }
}

# ========================================
# Step 2: Deploy Infrastructure
# ========================================

if (-not $SkipInfrastructure) {
    Write-Step "Step 2: Deploying Azure Infrastructure"
    Write-Info "This may take 5-10 minutes..."
    
    try {
        $deploymentName = "intelligent-agent-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        
        Write-Info "Deployment name: $deploymentName"
        Write-Info "Resource group: $ResourceGroupName"
        Write-Info "Template: $MainBicepFile"
        Write-Info "Parameters: $ParametersFilePath"
        
        # Deploy Bicep template
        $deployment = az deployment group create `
            --name $deploymentName `
            --resource-group $ResourceGroupName `
            --template-file $MainBicepFile `
            --parameters $ParametersFilePath `
            --output json | ConvertFrom-Json
        
        Write-Success "Infrastructure deployment completed successfully!"
        
        # Display outputs
        Write-Host "`n" -NoNewline
        Write-Step "Deployment Outputs"
        Write-Info "Web App Name: $($deployment.properties.outputs.webAppName.value)"
        Write-Info "Web App URL: $($deployment.properties.outputs.webAppUrl.value)"
        Write-Info "SQL Server: $($deployment.properties.outputs.sqlServerName.value)"
        Write-Info "SQL Database: $($deployment.properties.outputs.sqlDatabaseName.value)"
        
        if ($deployment.properties.outputs.keyVaultName.value) {
            Write-Info "Key Vault: $($deployment.properties.outputs.keyVaultName.value)"
        }
        
        # Store outputs for next step
        $script:webAppName = $deployment.properties.outputs.webAppName.value
        $script:webAppUrl = $deployment.properties.outputs.webAppUrl.value
        
    } catch {
        Write-Error-Custom "Infrastructure deployment failed"
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

# ========================================
# Step 3: Configure SQL Database
# ========================================

if (-not $SkipInfrastructure) {
    Write-Step "Step 3: Configure SQL Database Access"
    
    Write-Warning-Custom "Manual step required!"
    Write-Info "Grant the Web App managed identity access to SQL Database:"
    Write-Host @"

    1. Open Azure Portal → SQL Database → Query Editor
    2. Run these SQL commands:
    
       CREATE USER [$($script:webAppName)] FROM EXTERNAL PROVIDER;
       ALTER ROLE db_owner ADD MEMBER [$($script:webAppName)];
    
    3. Press Enter when done...
"@ -ForegroundColor Yellow
    
    Read-Host "Press Enter to continue"
}

# ========================================
# Step 4: Deploy Application Code
// ========================================

if (-not $SkipAppCode) {
    Write-Step "Step 4: Deploy Application Code"
    
    # Get web app name if not already set
    if (-not $script:webAppName) {
        Write-Info "Retrieving web app name from deployment..."
        $deployments = az deployment group list `
            --resource-group $ResourceGroupName `
            --query "[?contains(name, 'intelligent-agent')].properties.outputs.webAppName.value" `
            --output json | ConvertFrom-Json
        
        if ($deployments.Count -eq 0) {
            Write-Error-Custom "No deployments found. Please deploy infrastructure first."
            exit 1
        }
        
        $script:webAppName = $deployments[0]
    }
    
    Write-Info "Deploying to: $($script:webAppName)"
    
    # Check if app directory exists
    if (-not (Test-Path $AppDir)) {
        Write-Error-Custom "Application directory not found: $AppDir"
        Write-Info "Please copy your application code to the 'app' folder"
        exit 1
    }
    
    # Create deployment package
    Write-Info "Creating deployment package..."
    $tempZip = Join-Path $env:TEMP "app-deployment-$(Get-Date -Format 'yyyyMMddHHmmss').zip"
    
    # Compress application files
    Compress-Archive -Path "$AppDir\*" -DestinationPath $tempZip -Force
    Write-Success "Deployment package created: $tempZip"
    
    # Deploy to Azure App Service
    Write-Info "Deploying to Azure App Service (this may take 2-5 minutes)..."
    az webapp deployment source config-zip `
        --resource-group $ResourceGroupName `
        --name $script:webAppName `
        --src $tempZip `
        --output none
    
    # Clean up
    Remove-Item $tempZip -Force
    Write-Success "Application code deployed successfully!"
    
    # Restart web app
    Write-Info "Restarting web app..."
    az webapp restart --name $script:webAppName --resource-group $ResourceGroupName --output none
    Write-Success "Web app restarted"
}

# ========================================
# Summary
// ========================================

Write-Host "`n"
Write-Step "🎉 Deployment Complete!"

Write-Info "Next Steps:"
Write-Host @"
1. Access your application:
   URL: $($script:webAppUrl)
   
2. Default login (if authentication enabled):
   Username: admin
   Password: Admin@123
   ⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!

3. Monitor your application:
   - View logs: az webapp log tail --name $($script:webAppName) -g $ResourceGroupName
   - App Service: https://portal.azure.com/#resource/subscriptions/.../resourceGroups/$ResourceGroupName/providers/Microsoft.Web/sites/$($script:webAppName)

4. Troubleshooting:
   - Check deployment logs in Azure Portal
   - Review Application Insights for errors
   - Verify all parameters in $ParametersFile

"@ -ForegroundColor Green

Write-Success "Deployment script completed successfully!"
