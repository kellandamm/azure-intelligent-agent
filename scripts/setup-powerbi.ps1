#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    Creates and configures the Azure AD service principal required for Power BI embedding.

.DESCRIPTION
    Automates the Azure AD portion of Power BI service principal setup:
      - Creates an app registration and client secret
      - Outputs all values needed for bicep/main.bicepparam and App Settings

    Two manual steps remain after running this script (portal-only):
      1. Power BI Admin portal → Tenant settings → Enable "Service principals can use Power BI APIs"
      2. Your Power BI workspace → Access → add the service principal as Member

.PARAMETER AppRegistrationName
    Display name for the app registration (default: PowerBI-SP-AgentApp)

.PARAMETER SecretExpiryYears
    Client secret lifetime in years (default: 1)

.PARAMETER ResourceGroupName
    Optional: if provided, applies the Power BI settings to the named App Service automatically.

.PARAMETER AppName
    Optional: App Service name. Required when ResourceGroupName is supplied.

.EXAMPLE
    .\setup-powerbi.ps1

.EXAMPLE
    .\setup-powerbi.ps1 -ResourceGroupName "rg-myagents-prod" -AppName "agentXXXX-prod-app"
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$AppRegistrationName = "PowerBI-SP-AgentApp",

    [Parameter(Mandatory = $false)]
    [int]$SecretExpiryYears = 1,

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory = $false)]
    [string]$AppName
)

$ErrorActionPreference = "Stop"

function Write-Step   { param([string]$m) Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok     { param([string]$m) Write-Host "✅ $m" -ForegroundColor Green }
function Write-Info   { param([string]$m) Write-Host "ℹ️  $m" -ForegroundColor Blue }
function Write-Warn   { param([string]$m) Write-Host "⚠️  $m" -ForegroundColor Yellow }
function Write-Manual { param([string]$m) Write-Host "👉 $m" -ForegroundColor Magenta }

# ── Pre-flight ─────────────────────────────────────────────────────────────────

Write-Step "Pre-flight checks"

try {
    az account show --output none 2>$null
    $account = az account show --output json | ConvertFrom-Json
    Write-Ok "Logged in as $($account.user.name) | Subscription: $($account.name)"
} catch {
    Write-Warn "Not logged in — running az login..."
    az login
    $account = az account show --output json | ConvertFrom-Json
}

$tenantId = $account.tenantId

# ── App Registration ───────────────────────────────────────────────────────────

Write-Step "Creating app registration: $AppRegistrationName"

$existing = az ad app list --display-name $AppRegistrationName --query "[0].appId" -o tsv 2>$null
if ($existing) {
    Write-Warn "App registration '$AppRegistrationName' already exists (appId: $existing)"
    Write-Info "Using existing registration. Delete it first to recreate."
    $clientId = $existing
    $spObjectId = az ad sp show --id $clientId --query id -o tsv 2>$null
    if (-not $spObjectId) {
        $spObjectId = (az ad sp create --id $clientId --output json | ConvertFrom-Json).id
    }
} else {
    $app = az ad app create `
        --display-name $AppRegistrationName `
        --sign-in-audience AzureADMyOrg `
        --output json | ConvertFrom-Json

    $clientId = $app.appId
    Write-Ok "App registered: $AppRegistrationName (appId: $clientId)"

    # Create service principal
    $sp = az ad sp create --id $clientId --output json | ConvertFrom-Json
    $spObjectId = $sp.id
    Write-Ok "Service principal created (objectId: $spObjectId)"
}

# ── Client Secret ──────────────────────────────────────────────────────────────

Write-Step "Creating client secret (expires in $SecretExpiryYears year(s))"

$expiryDate = (Get-Date).AddYears($SecretExpiryYears).ToString("yyyy-MM-dd")

$secretResult = az ad app credential reset `
    --id $clientId `
    --years $SecretExpiryYears `
    --display-name "PowerBI-AgentApp-$(Get-Date -Format 'yyyyMMdd')" `
    --output json | ConvertFrom-Json

$clientSecret = $secretResult.password
Write-Ok "Client secret created (expires: $expiryDate)"
Write-Warn "The secret value is shown once below — save it now."

# ── Summary ────────────────────────────────────────────────────────────────────

Write-Step "Your Power BI service principal values"

Write-Host @"

  powerbiClientId     = '$clientId'
  powerbiTenantId     = '$tenantId'
  powerbiClientSecret = '$clientSecret'

"@ -ForegroundColor Green

Write-Info "Copy the three values above into bicep/main.bicepparam."
Write-Info "You will also need:"
Write-Host "  powerbiWorkspaceId  = '<GUID from Power BI workspace settings>'" -ForegroundColor DarkGray
Write-Host "  powerbiReportId     = '<GUID from Power BI report URL>'" -ForegroundColor DarkGray

# ── Apply to App Service (optional) ───────────────────────────────────────────

if ($ResourceGroupName -and $AppName) {
    Write-Step "Applying Power BI settings to App Service: $AppName"
    az webapp config appsettings set `
        --name $AppName `
        --resource-group $ResourceGroupName `
        --settings `
            "POWERBI_CLIENT_ID=$clientId" `
            "POWERBI_TENANT_ID=$tenantId" `
            "POWERBI_CLIENT_SECRET=$clientSecret" `
        --output none
    Write-Ok "POWERBI_CLIENT_ID, POWERBI_TENANT_ID, POWERBI_CLIENT_SECRET applied to $AppName"
    Write-Info "Workspace ID and Report ID must still be set manually once you have them."
}

# ── Remaining manual steps ─────────────────────────────────────────────────────

Write-Step "Remaining manual steps (portal-only, cannot be automated)"

Write-Manual "1. Enable Power BI API for service principals (one-time tenant setting):"
Write-Host "     Power BI portal → Settings (⚙) → Admin portal → Tenant settings" -ForegroundColor DarkGray
Write-Host "     → Developer settings → 'Allow service principals to use Power BI APIs' → Enable" -ForegroundColor DarkGray
Write-Host "     → Add your service principal to the allowed list if using a specific security group" -ForegroundColor DarkGray

Write-Host ""
Write-Manual "2. Grant workspace access:"
Write-Host "     Power BI portal → Your workspace → Access → Add people or groups" -ForegroundColor DarkGray
Write-Host "     → Enter '$AppRegistrationName' → Role: Member → Add" -ForegroundColor DarkGray

Write-Host ""
Write-Manual "3. Get workspace and report IDs then update bicep/main.bicepparam or App Settings:"
Write-Host "     Workspace ID: Power BI workspace → Settings → Workspace settings" -ForegroundColor DarkGray
Write-Host "     Report ID:    Open a report → copy the GUID from the URL" -ForegroundColor DarkGray

Write-Host ""
Write-Ok "Power BI service principal setup complete. Complete the two portal steps above to enable embedding."
