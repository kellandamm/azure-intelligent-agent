# validate-policy-compliance.ps1
#
# Pre-deployment policy compliance checker for the Azure Intelligent Agent Starter.
#
# Runs three validation layers before `azd up` / `az deployment group create`:
#   1. Bicep template validation  (az deployment group validate)
#   2. What-if deployment preview (az deployment group what-if)
#   3. Active deny-policy audit   (az policy assignment list + policy state)
#
# Usage:
#   .\scripts\validate-policy-compliance.ps1 `
#       -ResourceGroup  <rg-name>         `
#       -Location       westus3         `
#       -ParametersFile bicep\main.bicepparam
#
# Optional flags:
#   -SkipWhatIf     Skip the what-if step (faster, but no resource diff)
#   -SkipPolicyList Skip listing policy assignments (useful without az policy extension)
#
# Requirements:
#   - Azure CLI  (az)  and Bicep CLI  (az bicep) installed
#   - Logged in: az login
#   - Subscription selected: az account set --subscription <id>

param(
    [Parameter(Mandatory)]
    [string]$ResourceGroup,

    [string]$Location       = 'westus3',
    [string]$TemplateFile   = 'bicep\main.bicep',
    [string]$ParametersFile = 'bicep\main.bicepparam',

    [switch]$SkipWhatIf,
    [switch]$SkipPolicyList
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ── helpers ───────────────────────────────────────────────────────────────────
function Write-Section  ($msg) { Write-Host "`n━━━ $msg ━━━" -ForegroundColor Cyan }
function Write-Pass     ($msg) { Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Fail     ($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red }
function Write-Warn     ($msg) { Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Info     ($msg) { Write-Host "    $msg" -ForegroundColor Gray }

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot  = Split-Path -Parent $scriptDir
Push-Location $repoRoot

$overallPass = $true

# ── 0. Pre-flight: check CLI + auth ──────────────────────────────────────────
Write-Section 'Pre-flight checks'

try {
    $null = az account show 2>&1
    $account = az account show | ConvertFrom-Json
    Write-Pass "Authenticated as: $($account.user.name)"
    Write-Pass "Subscription : $($account.name)  ($($account.id))"
} catch {
    Write-Fail 'Not logged in to Azure CLI.  Run: az login'
    exit 1
}

# Ensure Bicep is installed
try {
    az bicep install 2>$null | Out-Null
    Write-Pass 'Bicep CLI available'
} catch {
    Write-Warn 'Could not verify Bicep CLI; validation may fail'
}

# Resolve template and parameters paths
$templatePath   = Join-Path $repoRoot $TemplateFile
$parametersPath = Join-Path $repoRoot $ParametersFile

if (-not (Test-Path $templatePath)) {
    Write-Fail "Template file not found: $templatePath"
    exit 1
}
if (-not (Test-Path $parametersPath)) {
    Write-Warn "Parameters file not found: $parametersPath  – running validation without parameters"
    $parametersPath = $null
}

# ── 1. Check resource group ───────────────────────────────────────────────────
Write-Section 'Resource group'

$rgExists = az group exists --name $ResourceGroup | ConvertFrom-Json
if ($rgExists) {
    Write-Pass "Resource group '$ResourceGroup' exists"
    $rgLocation = (az group show --name $ResourceGroup | ConvertFrom-Json).location
    Write-Info  "Location: $rgLocation"
} else {
    Write-Warn  "Resource group '$ResourceGroup' does not exist yet – it will be created during deployment"
    Write-Info  "Target location: $Location"
}

# ── 1b. Parameter health checks (catches bad values before hitting ARM) ─────────
Write-Section 'Parameter health checks'

$paramHealthPass = $true

if ($null -ne $parametersPath) {
    # Detect .bicepparam files (using keyword) vs JSON
    $paramRaw = Get-Content $parametersPath -Raw

    # Helper: extract a raw value from either .bicepparam (param x = 'val') or .json parameters
    function Get-ParamValue ([string]$Content, [string]$ParamName) {
        # bicepparam: param sqlAzureAdAdminSid = 'xxx'
        if ($Content -match "param\s+$ParamName\s*=\s*'([^']*)'") { return $Matches[1] }
        # parameters.json: "sqlAzureAdAdminSid": { "value": "xxx" }
        # Use -f format so we never embed double-quotes inside a double-quoted string
        $jsonPattern = '"{0}"\s*:\s*\{{[^}}]*"value"\s*:\s*"([^"]*)"' -f $ParamName
        if ($Content -match $jsonPattern) { return $Matches[1] }
        return $null
    }

    $guidPattern = '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    $placeholderPattern = '<[^>]+>|REPLACE|YOUR_|<FILL|TODO'

    # --- sqlAzureAdAdminSid ---
    $sid = Get-ParamValue $paramRaw 'sqlAzureAdAdminSid'
    if ($null -eq $sid) {
        Write-Warn 'sqlAzureAdAdminSid not found in parameters file — will use Bicep default (empty)'
        Write-Info '  If sqlUseAzureAuth=true, Azure AD admin details are required.'
        Write-Info '  Get the Object ID: az ad user show --id <UPN> --query id -o tsv'
    } elseif ([string]::IsNullOrWhiteSpace($sid) -or $sid -eq '') {
        Write-Warn 'sqlAzureAdAdminSid is empty — ARM will reject if Azure AD auth is enabled'
        Write-Info '  Get the Object ID: az ad user show --id <UPN> --query id -o tsv'
        $paramHealthPass = $false
    } elseif ($sid -match $placeholderPattern) {
        Write-Fail "sqlAzureAdAdminSid is still a placeholder: '$sid'"
        Write-Info '  This causes: InvalidResourceIdSegment on parameters.properties.administrators.sid'
        Write-Info '  Fix: replace with real Object ID from Azure AD'
        Write-Info '  Get it: az ad user show --id <UPN> --query id -o tsv'
        $paramHealthPass = $false
        $overallPass = $false
    } elseif ($sid -notmatch $guidPattern) {
        Write-Fail "sqlAzureAdAdminSid '$sid' is not a valid GUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
        Write-Info '  This causes: InvalidResourceIdSegment on parameters.properties.administrators.sid'
        Write-Info '  Fix: ensure the value is the Azure AD Object ID, not a UPN/email/display name'
        Write-Info '  Get it: az ad user show --id <UPN> --query id -o tsv'
        $paramHealthPass = $false
        $overallPass = $false
    } else {
        Write-Pass "sqlAzureAdAdminSid is a valid GUID: $sid"
    }

    # --- sqlAzureAdAdminLogin ---
    $login = Get-ParamValue $paramRaw 'sqlAzureAdAdminLogin'
    if ($null -ne $login -and $login -match $placeholderPattern) {
        Write-Fail "sqlAzureAdAdminLogin is still a placeholder: '$login'"
        $paramHealthPass = $false
        $overallPass = $false
    } elseif ($null -ne $login -and -not [string]::IsNullOrWhiteSpace($login)) {
        Write-Pass "sqlAzureAdAdminLogin: $login"
    }

    # --- Cross-check: if one is set, both must be set ---
    $sidSet   = $null -ne $sid   -and -not [string]::IsNullOrWhiteSpace($sid)   -and $sid   -notmatch $placeholderPattern
    $loginSet = $null -ne $login -and -not [string]::IsNullOrWhiteSpace($login) -and $login -notmatch $placeholderPattern
    if ($sidSet -xor $loginSet) {
        Write-Fail 'sqlAzureAdAdminLogin and sqlAzureAdAdminSid must both be set (or both empty)'
        Write-Info "  Login : $(if ($loginSet) { $login } else { '(missing)' })"
        Write-Info "  SID   : $(if ($sidSet)   { $sid   } else { '(missing)' })"
        $paramHealthPass = $false
        $overallPass = $false
    }

    if ($paramHealthPass -and -not ($overallPass -eq $false)) {
        Write-Pass 'Parameter values look healthy'
    }
} else {
    Write-Warn 'No parameters file found — skipping parameter health checks'
}

# ── 2. Bicep template validation ──────────────────────────────────────────────
Write-Section 'Bicep template validation  (az deployment group validate)'

if (-not $rgExists) {
    # Resource group doesn't exist yet — fall back to az bicep build (syntax + type check only)
    Write-Info 'Resource group does not exist; using bicep build for syntax/type validation...'
    $buildRaw  = az bicep build --file $templatePath 2>&1
    $buildExit = $LASTEXITCODE
    if ($buildExit -eq 0) {
        Write-Pass 'Bicep build succeeded (syntax and types valid)'
        Write-Warn 'Full ARM validation skipped — resource group must exist for parameter checking'
    } else {
        Write-Fail 'Bicep build FAILED (syntax/type errors):'
        $buildRaw | ForEach-Object { Write-Info $_ }
        $overallPass = $false
    }
} else {
    Write-Info 'Running...'
    $validateArgs = @(
        'deployment', 'group', 'validate',
        '--resource-group', $ResourceGroup,
        '--template-file',  $templatePath
    )
    if ($null -ne $parametersPath) { $validateArgs += '--parameters', $parametersPath }

    $validateRaw  = az @validateArgs 2>&1
    $validateExit = $LASTEXITCODE

    if ($validateExit -eq 0) {
        Write-Pass 'Template is syntactically valid and all required parameters are supplied'
    } else {
        # Policy violations show up here too — surface them clearly
        $policyLines = $validateRaw | Select-String 'RequestDisallowedByPolicy|InvalidTemplateDeployment'
        if ($policyLines) {
            Write-Fail 'Validation blocked by POLICY VIOLATIONS — fix before deploying:'
            $policyLines | ForEach-Object { Write-Info "  $_" }
        } else {
            Write-Fail 'Template validation FAILED:'
            $validateRaw | ForEach-Object { Write-Info $_ }
        }
        $overallPass = $false
    }
}

# ── 3. What-if deployment ─────────────────────────────────────────────────────
if (-not $SkipWhatIf) {
    Write-Section 'What-if deployment preview  (az deployment group what-if)'
    Write-Info 'Running (this may take 30-90 seconds)...'

    $whatIfArgs = @(
        'deployment', 'group', 'what-if',
        '--resource-group', $ResourceGroup,
        '--template-file',  $templatePath,
        '--no-pretty-print'
    )
    if ($null -ne $parametersPath) { $whatIfArgs += '--parameters', $parametersPath }

    $whatIfRaw  = az @whatIfArgs 2>&1
    $whatIfExit = $LASTEXITCODE

    if ($whatIfExit -eq 0) {
        Write-Pass 'What-if succeeded – no blocking errors detected'

        # Count planned operations
        $created  = ($whatIfRaw | Select-String '\+ Create').Count
        $modified = ($whatIfRaw | Select-String '~ Modify').Count
        $deleted  = ($whatIfRaw | Select-String '- Delete').Count
        $noChange = ($whatIfRaw | Select-String '= NoChange').Count
        Write-Info "Planned: +$created created  ~$modified modified  -$deleted deleted  =$noChange unchanged"
    } else {
        # Policy violations appear as errors in the what-if output
        $policyErrors = $whatIfRaw | Select-String 'RequestDisallowedByPolicy|InvalidTemplateDeployment'
        if ($policyErrors) {
            Write-Fail 'What-if detected POLICY VIOLATIONS:'
            $policyErrors | ForEach-Object { Write-Info "  $_" }
        } else {
            Write-Fail "What-if failed (exit $whatIfExit):"
            $whatIfRaw | Select-Object -Last 20 | ForEach-Object { Write-Info $_ }
        }
        $overallPass = $false
    }
}

# ── 4. Active deny-policy audit ───────────────────────────────────────────────
if (-not $SkipPolicyList) {
    Write-Section 'Active deny-policy assignments'

    $subId      = $account.id
    $subScope   = "/subscriptions/$subId"
    $rgScope    = "/subscriptions/$subId/resourceGroups/$ResourceGroup"

    $assignments = az policy assignment list --scope $subScope 2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue
    if (-not $assignments) {
        Write-Warn 'Could not retrieve policy assignments (may need az policy extension or elevated rights)'
    } else {
        $denyAssignments = $assignments | Where-Object { $_.enforcementMode -ne 'DoNotEnforce' }
        Write-Info "Total assignments in scope: $($assignments.Count)"
        Write-Info "Enforced (non-DoNotEnforce): $($denyAssignments.Count)"

        # Flag policies with known MCAPS-relevant keywords
        $mcapsKeywords = @('MCAPS','SQL','network','public network','outbound','TLS','authentication','Entra','AAD','mcsb')
        $flagged = $denyAssignments | Where-Object {
            $name = "$($_.displayName) $($_.name)"
            $mcapsKeywords | Where-Object { $name -like "*$_*" }
        }
        if ($flagged) {
            Write-Warn "Assignments flagged for review (SQL / network / auth related):"
            $flagged | ForEach-Object {
                Write-Info "  • $($_.displayName)  [mode: $($_.enforcementMode)]"
            }
        } else {
            Write-Pass 'No obviously MCAPS-related deny assignments found (check AzPolicyWiki for full list)'
        }
    }

    # Check current compliance state for SQL resources if RG exists
    if ($rgExists) {
        Write-Section 'Current resource compliance state (SQL)'
        $sqlStates = az policy state list `
            --resource-group $ResourceGroup `
            --filter "resourceType eq 'Microsoft.Sql/servers' and complianceState eq 'NonCompliant'" `
            2>&1 | ConvertFrom-Json -ErrorAction SilentlyContinue

        if ($sqlStates -and $sqlStates.Count -gt 0) {
            Write-Warn "Non-compliant SQL resources detected ($($sqlStates.Count)):"
            $sqlStates | ForEach-Object {
                Write-Info "  Resource : $($_.resourceId)"
                Write-Info "  Policy   : $($_.policyDefinitionName)"
                Write-Info "  Effect   : $($_.policyDefinitionAction)"
                Write-Info ''
            }
            $overallPass = $false
        } else {
            Write-Pass 'No non-compliant SQL resources found in this resource group'
        }
    }
}

# ── 5. Static MCAPS property checks ──────────────────────────────────────────
Write-Section 'Static MCAPS property checks (template scan)'

$sqlModulePath = Join-Path $repoRoot 'bicep\modules\sqlServer.bicep'
$sqlContent    = Get-Content $sqlModulePath -Raw

$checks = @(
    @{
        Name    = "SQL publicNetworkAccess defaults to 'Disabled'"
        Pass    = $sqlContent -match "param publicNetworkAccess string = 'Disabled'"
        Fix     = "Set param publicNetworkAccess string = 'Disabled' in sqlServer.bicep"
    }
    @{
        Name    = "SQL restrictOutboundNetworkAccess defaults to 'Enabled'"
        Pass    = $sqlContent -match "param restrictOutboundNetworkAccess string = 'Enabled'"
        Fix     = "Set param restrictOutboundNetworkAccess string = 'Enabled' in sqlServer.bicep"
    }
    @{
        Name    = "SQL minimalTlsVersion is '1.2'"
        Pass    = $sqlContent -match "param minimalTlsVersion string = '1\.2'"
        Fix     = "Set param minimalTlsVersion string = '1.2' in sqlServer.bicep"
    }
    @{
        Name    = "SQL AllowAllWindowsAzureIps firewall rule is conditional"
        Pass    = $sqlContent -match "= if \(publicNetworkAccess == 'Enabled'\)"
        Fix     = "Wrap the AllowAllWindowsAzureIps rule with: if (publicNetworkAccess == 'Enabled')"
    }
    @{
        # MCAPS AzureSQL_WithoutAzureADOnlyAuthentication_Deny (SFI-ID4.2.2):
        # The policy reads properties.administrators.azureADOnlyAuthentication on the
        # server resource at ARM validation time — BEFORE child resources are deployed.
        # Using a separate /administrators or /azureADOnlyAuthentications child resource
        # does NOT satisfy this check. The administrators block must be inline.
        Name    = "SQL Entra-only auth is set INLINE on server resource (required by AzureSQL_WithoutAzureADOnlyAuthentication_Deny)"
        Pass    = $sqlContent -match 'administrators:' -and $sqlContent -match 'azureADOnlyAuthentication: azureADOnlyAuthentication'
        Fix     = "Add 'administrators: { ... azureADOnlyAuthentication: azureADOnlyAuthentication }' inline inside the sqlServer resource properties block. Child resources (/administrators, /azureADOnlyAuthentications) are NOT evaluated by this policy."
    }
)

$mainContent = Get-Content $templatePath -Raw
$checks += @(
    @{
        Name    = "main.bicep passes publicNetworkAccess: 'Disabled' to SQL module"
        Pass    = $mainContent -match "publicNetworkAccess: 'Disabled'"
        Fix     = "Add publicNetworkAccess: 'Disabled' to sqlServerModule params"
    }
    @{
        Name    = "main.bicep passes restrictOutboundNetworkAccess: 'Enabled' to SQL module"
        Pass    = $mainContent -match "restrictOutboundNetworkAccess: 'Enabled'"
        Fix     = "Add restrictOutboundNetworkAccess: 'Enabled' to sqlServerModule params"
    }
    @{
        Name    = "VNet integration is enabled for private endpoint connectivity"
        Pass    = $mainContent -match "param enableVnetIntegration bool = true"
        Fix     = "Set enableVnetIntegration default to true in main.bicep"
    }
    @{
        # ARM returns InvalidResourceIdSegment when the SID is not a valid GUID.
        # The @maxLength(36) constraint on the parameter prevents oversized/placeholder values
        # from reaching ARM; combined with the parameter health check above this catches the
        # common 'still a placeholder' mistake at script time rather than deploy time.
        Name    = 'SQL azureAdAdminSid has @maxLength(36) guard (prevents placeholder reaching ARM)'
        Pass    = $sqlContent -match '@maxLength\(36\)' -and $sqlContent -match 'param azureAdAdminSid'
        Fix     = "Add '@maxLength(36)' decorator on param azureAdAdminSid in sqlServer.bicep"
    }
)

foreach ($check in $checks) {
    if ($check.Pass) {
        Write-Pass $check.Name
    } else {
        Write-Fail "$($check.Name)`n         Fix: $($check.Fix)"
        $overallPass = $false
    }
}

# ── 6. Summary ────────────────────────────────────────────────────────────────
Write-Section 'Summary'

if ($overallPass) {
    Write-Host "`n  ✅  All checks passed — safe to deploy`n" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n  ❌  One or more checks FAILED — fix the issues above before deploying`n" -ForegroundColor Red
    exit 1
}

Pop-Location
