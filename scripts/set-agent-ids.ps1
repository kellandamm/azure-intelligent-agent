#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    Applies Azure AI Foundry / Fabric agent IDs to an App Service after manual agent creation.

.DESCRIPTION
    After you create agents in the Azure AI Foundry or Microsoft Fabric portal and copy their
    IDs, run this script to push them to App Settings in one step rather than using the portal
    or typing multiple az CLI commands.

    Accepts individual agent ID parameters or reads them interactively if omitted.
    Restarts the app automatically so the new settings take effect immediately.

.PARAMETER ResourceGroupName
    Azure resource group containing the App Service.

.PARAMETER AppName
    App Service name.

.PARAMETER ProjectEndpoint
    Azure AI Foundry project endpoint URL.

.PARAMETER OrchestratorAgentId
    Orchestrator agent ID (format: asst_xxx...).

.PARAMETER SalesAgentId
    Sales specialist agent ID.

.PARAMETER RealtimeAgentId
    Operations / real-time agent ID.

.PARAMETER AnalyticsAgentId
    Analytics specialist agent ID.

.PARAMETER FinancialAgentId
    Financial advisor agent ID.

.PARAMETER SupportAgentId
    Customer support agent ID.

.PARAMETER FabricWorkspaceId
    Microsoft Fabric workspace GUID.

.PARAMETER NoRestart
    Skip the app restart after applying settings.

.EXAMPLE
    .\set-agent-ids.ps1 -ResourceGroupName "rg-myagents-prod" -AppName "agentXXXX-prod-app"

.EXAMPLE
    .\set-agent-ids.ps1 `
        -ResourceGroupName "rg-myagents-prod" `
        -AppName "agentXXXX-prod-app" `
        -OrchestratorAgentId "asst_abc123" `
        -SalesAgentId "asst_def456" `
        -FabricWorkspaceId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
#>

param(
    [Parameter(Mandatory = $true)]  [string]$ResourceGroupName,
    [Parameter(Mandatory = $true)]  [string]$AppName,
    [Parameter(Mandatory = $false)] [string]$ProjectEndpoint,
    [Parameter(Mandatory = $false)] [string]$OrchestratorAgentId,
    [Parameter(Mandatory = $false)] [string]$SalesAgentId,
    [Parameter(Mandatory = $false)] [string]$RealtimeAgentId,
    [Parameter(Mandatory = $false)] [string]$AnalyticsAgentId,
    [Parameter(Mandatory = $false)] [string]$FinancialAgentId,
    [Parameter(Mandatory = $false)] [string]$SupportAgentId,
    [Parameter(Mandatory = $false)] [string]$FabricWorkspaceId,
    [Parameter(Mandatory = $false)] [switch]$NoRestart
)

$ErrorActionPreference = "Stop"

function Write-Step { param([string]$m) Write-Host "`n=== $m ===" -ForegroundColor Cyan }
function Write-Ok   { param([string]$m) Write-Host "✅ $m" -ForegroundColor Green }
function Write-Info { param([string]$m) Write-Host "ℹ️  $m" -ForegroundColor Blue }
function Write-Warn { param([string]$m) Write-Host "⚠️  $m" -ForegroundColor Yellow }

# ── Pre-flight ─────────────────────────────────────────────────────────────────

Write-Step "Pre-flight checks"

try {
    az account show --output none 2>$null
    $account = az account show --output json | ConvertFrom-Json
    Write-Ok "Logged in as $($account.user.name)"
} catch {
    az login
}

# Verify app exists
$webApp = az webapp show --name $AppName --resource-group $ResourceGroupName --output json 2>$null | ConvertFrom-Json
if (-not $webApp) {
    Write-Host "❌ App Service '$AppName' not found in '$ResourceGroupName'" -ForegroundColor Red
    exit 1
}
Write-Ok "App Service found: $AppName"

# ── Interactive prompts for any missing IDs ────────────────────────────────────

Write-Step "Agent ID collection"
Write-Info "Press Enter to skip any agent you have not created yet (can be re-run later)."
Write-Host ""

function Prompt-IfEmpty {
    param([string]$Value, [string]$Label, [string]$Hint = "asst_...")
    if ($Value) { return $Value }
    $input = Read-Host "  $Label ($Hint) [blank to skip]"
    return $input.Trim()
}

$ProjectEndpoint      = Prompt-IfEmpty $ProjectEndpoint      "AI Foundry project endpoint" "https://<project>.<region>.api.azureml.ms/..."
$OrchestratorAgentId  = Prompt-IfEmpty $OrchestratorAgentId  "Orchestrator agent ID"
$SalesAgentId         = Prompt-IfEmpty $SalesAgentId         "Sales agent ID"
$RealtimeAgentId      = Prompt-IfEmpty $RealtimeAgentId      "Operations / real-time agent ID"
$AnalyticsAgentId     = Prompt-IfEmpty $AnalyticsAgentId     "Analytics agent ID"
$FinancialAgentId     = Prompt-IfEmpty $FinancialAgentId     "Financial agent ID"
$SupportAgentId       = Prompt-IfEmpty $SupportAgentId       "Support agent ID"
$FabricWorkspaceId    = Prompt-IfEmpty $FabricWorkspaceId    "Fabric workspace ID" "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# ── Build settings array ───────────────────────────────────────────────────────

$settings = @()

if ($ProjectEndpoint)     { $settings += "PROJECT_ENDPOINT=$ProjectEndpoint" }
if ($OrchestratorAgentId) { $settings += "FABRIC_ORCHESTRATOR_AGENT_ID=$OrchestratorAgentId" }
if ($SalesAgentId)        { $settings += "FABRIC_SALES_AGENT_ID=$SalesAgentId" }
if ($RealtimeAgentId)     { $settings += "FABRIC_REALTIME_AGENT_ID=$RealtimeAgentId" }
if ($AnalyticsAgentId)    { $settings += "FABRIC_ANALYTICS_AGENT_ID=$AnalyticsAgentId" }
if ($FinancialAgentId)    { $settings += "FABRIC_FINANCIAL_AGENT_ID=$FinancialAgentId" }
if ($SupportAgentId)      { $settings += "FABRIC_SUPPORT_AGENT_ID=$SupportAgentId" }
if ($FabricWorkspaceId)   { $settings += "FABRIC_WORKSPACE_ID=$FabricWorkspaceId" }

if ($settings.Count -eq 0) {
    Write-Warn "No values provided — nothing to apply."
    exit 0
}

# ── Apply settings ─────────────────────────────────────────────────────────────

Write-Step "Applying $($settings.Count) setting(s) to $AppName"

az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroupName `
    --settings @settings `
    --output none

Write-Ok "Applied settings:"
foreach ($s in $settings) {
    $key = $s.Split("=")[0]
    Write-Host "   $key" -ForegroundColor DarkGray
}

# ── Restart ────────────────────────────────────────────────────────────────────

if (-not $NoRestart) {
    Write-Step "Restarting app to apply new settings"
    az webapp restart --name $AppName --resource-group $ResourceGroupName --output none
    Write-Ok "App restarted — new agent IDs are active"
} else {
    Write-Warn "Restart skipped (-NoRestart). Restart manually to apply settings:"
    Write-Host "  az webapp restart --name $AppName --resource-group $ResourceGroupName"
}

# ── Summary ────────────────────────────────────────────────────────────────────

Write-Step "Done"
Write-Info "Verify settings are active:"
Write-Host "  az webapp config appsettings list --name $AppName -g $ResourceGroupName --query ""[?starts_with(name,'FABRIC') || name=='PROJECT_ENDPOINT']"" -o table"
Write-Host ""
Write-Info "View live logs:"
Write-Host "  az webapp log tail --name $AppName --resource-group $ResourceGroupName"
