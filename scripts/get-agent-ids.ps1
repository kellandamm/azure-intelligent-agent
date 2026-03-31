#Requires -Version 7.0
<#
.SYNOPSIS
    Retrieves agent IDs from Microsoft AI Foundry and optionally applies them to App Service.

.DESCRIPTION
    This script:
    - Retrieves agent IDs from your Microsoft AI Foundry project by name
    - Maps them to environment variables for the application
    - Optionally configures your App Service with agent IDs

    Note: Agents must be created manually in the Microsoft AI Foundry portal at https://ai.azure.com
    Automatic agent creation via API is not currently available.

.PARAMETER ProjectEndpoint
    Azure AI Foundry project endpoint URL.
    Format: https://<resource>.services.ai.azure.com/api/projects/<project-name>
    Find in Azure AI Foundry portal → Project → Settings → Endpoint

.PARAMETER ModelName
    (Optional) Model deployment name used by agents. Not used for retrieval, only for display.
    Default: 'gpt-4o'

.PARAMETER Create
    Shows the agent definitions (names and system prompts) that need to be created manually
    in the portal. Does not actually create agents via API.

.PARAMETER ResourceGroupName
    Azure resource group name containing the App Service.

.PARAMETER AppName
    App Service name to update with agent IDs.

.PARAMETER Apply
    Switch to automatically apply agent IDs to App Service settings.
    Without this flag, the script only displays agent IDs.

.PARAMETER NoRestart
    Skip restarting the App Service after updating settings.

.EXAMPLE
    # Show agent definitions to create in portal
    .\scripts\get-agent-ids.ps1 `
        -ProjectEndpoint "https://myproject.services.ai.azure.com/api/projects/myproject" `
        -Create

.EXAMPLE
    # Retrieve agent IDs and apply to App Service
    .\scripts\get-agent-ids.ps1 `
        -ProjectEndpoint "https://myproject.services.ai.azure.com/api/projects/myproject" `
        -ResourceGroupName "rg-myagents-prod" `
        -AppName "myapp-prod-app" `
        -Apply

.EXAMPLE
    # Just list agent IDs without applying
    .\scripts\get-agent-ids.ps1 `
        -ProjectEndpoint "https://myproject.services.ai.azure.com/api/projects/myproject"

.NOTES
    Prerequisites:
    - Azure CLI (az) installed and authenticated (run 'az login')
    - 'Azure AI Developer' role on the AI Foundry Hub/Project
      (See: https://learn.microsoft.com/azure/ai-studio/concepts/rbac-ai-studio)
    - PowerShell 7.0 or later
    - Agents must be created manually in portal before running this script
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectEndpoint,

    [Parameter(Mandatory = $false)]
    [string]$ModelName = "gpt-4o",

    [Parameter(Mandatory = $false)]
    [switch]$Create,

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory = $false)]
    [string]$AppName,

    [Parameter(Mandatory = $false)]
    [switch]$Apply,

    [Parameter(Mandatory = $false)]
    [switch]$NoRestart
)

$ErrorActionPreference = "Stop"

# Validate endpoint format
if ($ProjectEndpoint -notmatch '^https://.*\.services\.ai\.azure\.com/api/projects/.*$') {
    Write-Error "Invalid PROJECT_ENDPOINT format. Expected: https://<resource>.services.ai.azure.com/api/projects/<project>"
    exit 1
}

# If -Apply is specified, require ResourceGroupName and AppName
if ($Apply -and (-not $ResourceGroupName -or -not $AppName)) {
    Write-Error "-Apply requires both -ResourceGroupName and -AppName parameters"
    exit 1
}

# Agent definitions with system prompts
$agentDefinitions = @(
    @{
        Name = "RetailAssistantOrchestrator"
        Role = "orchestrator"
        Instructions = @"
You are a retail business orchestrator. Your job is to understand the user's question and
route it to the correct specialist. You have access to specialists for: sales data, operations
metrics, analytics, financial planning, customer support, logistics, customer success, and
operations excellence. Respond concisely and delegate complex questions to the right expert.
"@
    },
    @{
        Name = "SalesAssistant"
        Role = "sales"
        Instructions = @"
You are a sales intelligence specialist for a retail business. You answer questions about
revenue, top-performing products, sales trends, regional performance, and customer purchasing
behaviour. Provide data-driven insights and actionable recommendations. Be concise and precise.
"@
    },
    @{
        Name = "OperationsAssistant"
        Role = "realtime"
        Instructions = @"
You are an operations monitoring specialist. You answer questions about real-time system
health, uptime, order processing status, fulfilment rates, and operational KPIs.
Highlight anomalies and surface actionable findings.
"@
    },
    @{
        Name = "AnalyticsAssistant"
        Role = "analytics"
        Instructions = @"
You are a business intelligence analyst. You answer questions about customer demographics,
cohort analysis, conversion funnels, seasonal patterns, and performance benchmarking.
Provide clear, data-backed conclusions.
"@
    },
    @{
        Name = "FinancialAdvisor"
        Role = "financial"
        Instructions = @"
You are a financial planning specialist. You answer questions about ROI calculations, revenue
forecasting, margin analysis, cost optimisation, and profitability. Apply sound financial
reasoning and present findings clearly.
"@
    },
    @{
        Name = "CustomerSupportAssistant"
        Role = "support"
        Instructions = @"
You are a customer support specialist. You help customers with product questions, order
issues, returns, and general troubleshooting. Be empathetic, concise, and solution-focused.
Escalate complex cases when appropriate.
"@
    },
    @{
        Name = "OperationsCoordinator"
        Role = "operations"
        Instructions = @"
You are a logistics and supply chain coordinator. You answer questions about inventory levels,
supplier lead times, shipping status, and supply chain optimisation. Identify bottlenecks and
recommend practical solutions.
"@
    },
    @{
        Name = "CustomerSuccessAgent"
        Role = "customer_success"
        Instructions = @"
You are a customer success specialist. You analyse customer satisfaction data, churn signals,
retention strategies, and growth opportunities. Provide proactive recommendations to improve
customer lifetime value and loyalty.
"@
    },
    @{
        Name = "OperationsExcellenceAgent"
        Role = "operations_excellence"
        Instructions = @"
You are an operations excellence specialist. You identify inefficiencies, analyse process
metrics, and recommend improvements. Apply continuous-improvement frameworks (Lean, Six Sigma)
where relevant and quantify the expected impact of changes.
"@
    }
)

# Get access token using Azure CLI
# Microsoft AI Foundry uses https://ai.azure.com scope
Write-Host "🔐 Authenticating..." -ForegroundColor Cyan

try {
    $token = az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv 2>&1
    if ($LASTEXITCODE -ne 0 -or $token -like "*ERROR*") {
        throw "Failed to get access token"
    }
    Write-Host "   ✅ Token obtained" -ForegroundColor Green
} catch {
    Write-Error "Failed to authenticate with Azure AI Foundry."
    Write-Host ""
    Write-Host "💡 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Run 'az login' to authenticate" -ForegroundColor Gray
    Write-Host "   2. Verify you have 'Azure AI Developer' role on the AI Hub" -ForegroundColor Gray
    Write-Host "   3. RBAC Guide: https://learn.microsoft.com/azure/ai-studio/concepts/rbac-ai-studio" -ForegroundColor Gray
    exit 1
}

# Parse project endpoint to extract Azure resource details
# Format: https://{aiResource}.services.ai.azure.com/api/projects/{project}
Write-Host "🔍 Parsing project endpoint..." -ForegroundColor Cyan

if ($ProjectEndpoint -match 'https://([^.]+)\.services\.ai\.azure\.com/api/projects/(.+)') {
    $aiResource = $matches[1].Trim()
    $projectName = $matches[2].Trim()
} else {
    Write-Error "Invalid PROJECT_ENDPOINT format. Expected: https://<resource>.services.ai.azure.com/api/projects/<project>"
    Write-Host "   Your value: $ProjectEndpoint" -ForegroundColor Gray
    exit 1
}

Write-Host "   AI Resource: $aiResource" -ForegroundColor Gray
Write-Host "   Project: $projectName" -ForegroundColor Gray

# Get subscription and resource group from Azure CLI
try {
    Write-Host "   Fetching subscription info..." -ForegroundColor Gray
    $accountInfo = az account show 2>&1 | ConvertFrom-Json
    $subscriptionId = $accountInfo.id
    Write-Host "   Subscription: $subscriptionId" -ForegroundColor Gray

    # Find the resource group for this AI resource
    Write-Host "   Locating resource group..." -ForegroundColor Gray
    $resourceInfo = az resource list --name $aiResource --query "[0].resourceGroup" -o tsv 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $resourceInfo) {
        Write-Host "   ⚠️  Could not auto-detect resource group" -ForegroundColor Yellow
        Write-Host "   Searching all resource groups..." -ForegroundColor Gray
        $allResources = az resource list --query "[?name=='$aiResource'].resourceGroup" -o tsv 2>&1
        if ($allResources) {
            $resourceGroup = $allResources
        } else {
            Write-Error "Could not find resource group for AI resource: $aiResource"
            Write-Host "   Please provide it manually" -ForegroundColor Gray
            $resourceGroup = Read-Host "   Enter resource group name"
        }
    } else {
        $resourceGroup = $resourceInfo.Trim()
    }

    Write-Host "   Resource Group: $resourceGroup" -ForegroundColor Gray
    Write-Host "   ✅ Configuration ready" -ForegroundColor Green
} catch {
    Write-Error "Failed to get Azure subscription info. Ensure you're logged in with 'az login'"
    exit 1
}

# Use the actual Microsoft AI Foundry portal API (not the documented REST API)
# Based on portal behavior: https://ai.azure.com/nextgen/api/...
$baseUrl = "https://ai.azure.com/nextgen/api"

 $headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host ""

# Note: Automatic agent creation via API is not currently available
# Agents must be created manually in the portal at https://ai.azure.com
if ($Create) {
    Write-Host "⚠️  Note: Automatic agent creation via API is not available" -ForegroundColor Yellow
    Write-Host "   Microsoft AI Foundry agents must be created through the portal" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Please create these agents manually:" -ForegroundColor Cyan
    Write-Host ""
    foreach ($agentDef in $agentDefinitions) {
        Write-Host "   • $($agentDef.Name)" -ForegroundColor White
        Write-Host "     Role: $($agentDef.Role)" -ForegroundColor Gray
        Write-Host "     Instructions: $($agentDef.Instructions.Substring(0, [Math]::Min(100, $agentDef.Instructions.Length)))..." -ForegroundColor DarkGray
        Write-Host ""
    }
    Write-Host "   After creating agents, re-run this script without -Create" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "🔍 Retrieving agents from Azure AI Foundry..." -ForegroundColor Cyan
Write-Host ""

# Portal uses getAgentApplication endpoint with agent name
# Try to retrieve each agent by its expected name
$foundAgents = @()

foreach ($agentDef in $agentDefinitions) {
    $agentName = $agentDef.Name
    Write-Host "Looking for agent: $agentName..." -ForegroundColor Gray

    try {
        $getUrl = "$baseUrl/getAgentApplication" + `
            "?subscriptionId=$subscriptionId" + `
            "&resourceGroup=$resourceGroup" + `
            "&aiResource=$aiResource" + `
            "&project=$projectName" + `
            "&applicationName=$agentName"

        $agentData = Invoke-RestMethod -Uri $getUrl -Headers $headers -Method Get -ErrorAction Stop

        # Extract ID from response
        if ($agentData.id) {
            $agentId = $agentData.id
        } elseif ($agentData.name) {
            $agentId = $agentData.name
        } elseif ($agentData.applicationName) {
            $agentId = $agentData.applicationName
        } else {
            $agentId = $agentName
        }

        $foundAgents += @{
            Name = $agentName
            Role = $agentDef.Role
            Id = $agentId
            Data = $agentData
        }

        Write-Host "   ✅ Found: $agentId" -ForegroundColor Green

    } catch {
        if ($_.Exception.Response.StatusCode -eq 404) {
            Write-Host "   ⚠️  Not found (needs to be created in portal)" -ForegroundColor Yellow
        } else {
            Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

if ($foundAgents.Count -eq 0) {
    Write-Host ""
    Write-Host "❌ No agents found in the project" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Next steps:" -ForegroundColor Cyan
    Write-Host "   1. Go to https://ai.azure.com" -ForegroundColor Gray
    Write-Host "   2. Navigate to your project: $projectName" -ForegroundColor Gray
    Write-Host "   3. Click 'Agents' in the left menu" -ForegroundColor Gray
    Write-Host "   4. Create agents with these exact names:" -ForegroundColor Gray
    Write-Host ""
    foreach ($agentDef in $agentDefinitions) {
        Write-Host "      • $($agentDef.Name) ($($agentDef.Role))" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "   5. Use the system prompts defined in this script" -ForegroundColor Gray
    Write-Host "   6. Re-run this script to retrieve their IDs" -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "✅ Found $($foundAgents.Count) agent(s)" -ForegroundColor Green
Write-Host ""

# Build agentMap directly from foundAgents since we know the roles
$agentMap = @{
    "orchestrator" = $null
    "sales" = $null
    "realtime" = $null
    "analytics" = $null
    "financial" = $null
    "support" = $null
    "operations" = $null
    "customer_success" = $null
    "operations_excellence" = $null
}

Write-Host "📋 Agent Mapping:" -ForegroundColor Cyan
foreach ($agent in $foundAgents) {
    $role = $agent.Role
    $agentId = $agent.Id
    $agentName = $agent.Name

    Write-Host "   • $agentName" -ForegroundColor White
    Write-Host "     Role: $role" -ForegroundColor Gray
    Write-Host "     ID: $agentId" -ForegroundColor Gray

    if ($agentMap.ContainsKey($role)) {
        $agentMap[$role] = $agentId
        Write-Host "     ✅ Mapped to: ${role}_agent_id" -ForegroundColor Green
    } else {
        Write-Host "     ⚠️  Unknown role: $role" -ForegroundColor Yellow
    }

    Write-Host ""
}

Write-Host "📌 Environment Variables:" -ForegroundColor Cyan
$settings = @()
foreach ($role in $agentMap.Keys | Sort-Object) {
    $id = $agentMap[$role]
    $envVar = $role.ToUpper() + "_AGENT_ID"
    if ($id) {
        Write-Host "   $envVar = $id" -ForegroundColor Green
        $settings += "$envVar=$id"
    } else {
        Write-Host "   $envVar = (not set)" -ForegroundColor DarkGray
    }
}
Write-Host ""

# Apply to App Service if requested
if ($Apply) {
    Write-Host "🚀 Applying agent IDs to App Service..." -ForegroundColor Cyan
    Write-Host "   Resource Group: $ResourceGroupName" -ForegroundColor Gray
    Write-Host "   App Name: $AppName" -ForegroundColor Gray

    # Add PROJECT_ENDPOINT and USE_FOUNDRY_AGENTS
    $settings += "PROJECT_ENDPOINT=$ProjectEndpoint"
    $settings += "USE_FOUNDRY_AGENTS=true"

    try {
        az webapp config appsettings set `
            --name $AppName `
            --resource-group $ResourceGroupName `
            --settings $settings `
            --output none

        Write-Host "✅ App Settings updated successfully" -ForegroundColor Green

        if (-not $NoRestart) {
            Write-Host "🔄 Restarting app..." -ForegroundColor Cyan
            az webapp restart --name $AppName --resource-group $ResourceGroupName --output none
            Write-Host "✅ App restarted" -ForegroundColor Green
        }
    } catch {
        Write-Error "Failed to update App Service: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "💡 To apply these settings to your App Service, run:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host ".\scripts\get-agent-ids.ps1 ``" -ForegroundColor White
    Write-Host "    -ProjectEndpoint `"$ProjectEndpoint`" ``" -ForegroundColor White
    Write-Host "    -ResourceGroupName `"<your-resource-group>`" ``" -ForegroundColor White
    Write-Host "    -AppName `"<your-app-name>`" ``" -ForegroundColor White
    Write-Host "    -Apply" -ForegroundColor White
    Write-Host ""
}

Write-Host "✅ Done" -ForegroundColor Green
