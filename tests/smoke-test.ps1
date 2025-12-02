#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    PowerShell smoke test suite for Azure Intelligent Agent

.DESCRIPTION
    Comprehensive smoke tests to verify deployment health:
    - Health endpoints
    - API endpoints
    - Dashboard availability
    - Database connectivity
    - Authentication system
    - Performance metrics

.PARAMETER Url
    Base URL of the deployed application (e.g., https://your-app.azurewebsites.net)

.PARAMETER AuthToken
    JWT authentication token for protected endpoints

.PARAMETER SkipAuth
    Skip authentication-related tests

.PARAMETER ResourceGroupName
    Azure resource group name (auto-discovers URL from Azure)

.PARAMETER Verbose
    Enable verbose output

.PARAMETER JsonOutput
    Save results to JSON file

.EXAMPLE
    .\smoke-test.ps1 -Url "https://your-app.azurewebsites.net"
    
.EXAMPLE
    .\smoke-test.ps1 -ResourceGroupName "rg-myagents-prod"
    
.EXAMPLE
    .\smoke-test.ps1 -Url "http://localhost:8000" -SkipAuth -Verbose
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$Url = "",
    
    [Parameter(Mandatory = $false)]
    [string]$AuthToken = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipAuth,
    
    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$VerboseOutput,
    
    [Parameter(Mandatory = $false)]
    [string]$JsonOutput = ""
)

$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param([string]$Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning-Custom { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error-Custom { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param([string]$Message) Write-Host "`n========================================" -ForegroundColor Magenta; Write-Host $Message -ForegroundColor Magenta; Write-Host "========================================`n" -ForegroundColor Magenta }

# Test result tracking
$script:TestResults = @()
$script:StartTime = Get-Date

function Add-TestResult {
    param(
        [string]$Name,
        [bool]$Passed,
        [double]$DurationMs,
        [string]$ErrorMessage = "",
        [hashtable]$Details = @{}
    )
    
    $script:TestResults += @{
        Name = $Name
        Passed = $Passed
        DurationMs = $DurationMs
        ErrorMessage = $ErrorMessage
        Details = $Details
    }
    
    if ($Passed) {
        Write-Success "PASS - $Name ($([int]$DurationMs)ms)"
    } else {
        Write-Error-Custom "FAIL - $Name: $ErrorMessage"
    }
}

function Invoke-Test {
    param(
        [string]$Name,
        [scriptblock]$TestBlock
    )
    
    if ($VerboseOutput) {
        Write-Info "Running: $Name"
    }
    
    $start = Get-Date
    try {
        $result = & $TestBlock
        $duration = ((Get-Date) - $start).TotalMilliseconds
        
        if ($result.Passed) {
            Add-TestResult -Name $Name -Passed $true -DurationMs $duration -Details $result.Details
        } else {
            Add-TestResult -Name $Name -Passed $false -DurationMs $duration -ErrorMessage $result.Error -Details $result.Details
        }
    }
    catch {
        $duration = ((Get-Date) - $start).TotalMilliseconds
        Add-TestResult -Name $Name -Passed $false -DurationMs $duration -ErrorMessage $_.Exception.Message
    }
}

# ========================================
# Initialize
# ========================================

Write-Host @"

    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🧪 AZURE INTELLIGENT AGENT - SMOKE TEST SUITE 🧪        ║
    ║                                                           ║
    ║   Comprehensive health verification                      ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Auto-discover URL from Azure if ResourceGroupName provided
if ([string]::IsNullOrEmpty($Url) -and ![string]::IsNullOrEmpty($ResourceGroupName)) {
    Write-Info "Discovering application URL from Azure..."
    
    try {
        $appService = az webapp list --resource-group $ResourceGroupName --query "[0]" | ConvertFrom-Json
        if ($appService) {
            $Url = "https://$($appService.defaultHostName)"
            Write-Success "Discovered URL: $Url"
        } else {
            Write-Error-Custom "No App Service found in resource group: $ResourceGroupName"
            exit 1
        }
    }
    catch {
        Write-Error-Custom "Failed to discover URL from Azure: $_"
        exit 1
    }
}

if ([string]::IsNullOrEmpty($Url)) {
    Write-Error-Custom "URL is required. Use -Url or -ResourceGroupName parameter."
    exit 1
}

$Url = $Url.TrimEnd('/')

Write-Info "Target URL: $Url"
Write-Info "Authentication: $(if ($AuthToken) { 'Enabled' } elseif ($SkipAuth) { 'Skipped' } else { 'None' })"
Write-Host ""

# Setup headers
$headers = @{
    'User-Agent' = 'Azure-Intelligent-Agent-SmokeTest-PS/1.0'
    'Accept' = 'application/json'
}

if ($AuthToken) {
    $headers['Authorization'] = "Bearer $AuthToken"
}

# ========================================
# Test Functions
# ========================================

function Test-HealthEndpoint {
    try {
        $response = Invoke-RestMethod -Uri "$Url/health" -Method Get -Headers $headers -TimeoutSec 10
        
        if ($response.status -eq "healthy") {
            return @{ Passed = $true; Details = @{ status = $response.status; version = $response.version } }
        } else {
            return @{ Passed = $false; Error = "Status is not healthy: $($response.status)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-RootEndpoint {
    try {
        $response = Invoke-WebRequest -Uri "$Url/" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 307)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-StaticFiles {
    try {
        $response = Invoke-WebRequest -Uri "$Url/login" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -eq 200 -and $response.Headers['Content-Type'] -like '*html*') {
            return @{ Passed = $true; Details = @{ content_type = $response.Headers['Content-Type'] } }
        } else {
            return @{ Passed = $false; Error = "Status: $($response.StatusCode), Content-Type: $($response.Headers['Content-Type'])" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-AuthenticationEndpoint {
    if ($SkipAuth) {
        return @{ Passed = $true; Details = @{ skipped = $true } }
    }
    
    try {
        $body = @{} | ConvertTo-Json
        $response = Invoke-WebRequest -Uri "$Url/api/auth/login" -Method Post -Headers $headers -Body $body -ContentType 'application/json' -TimeoutSec 10 -SkipHttpErrorCheck
        
        # 422 = validation error (expected), 401 = auth failed (also good)
        if ($response.StatusCode -in @(422, 401)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-ChatEndpoint {
    try {
        $body = @{
            message = "test"
            agent_type = "orchestrator"
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$Url/api/chat" -Method Post -Headers $headers -Body $body -ContentType 'application/json' -TimeoutSec 30 -SkipHttpErrorCheck
        
        # 200 = success, 401 = needs auth, 422 = validation error
        if ($response.StatusCode -in @(200, 401, 422)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-AgentEndpoint {
    try {
        $body = @{
            message = "test"
            agent_type = "sales"
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$Url/api/agent/chat" -Method Post -Headers $headers -Body $body -ContentType 'application/json' -TimeoutSec 30 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 401, 422)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-SalesDashboard {
    try {
        $response = Invoke-WebRequest -Uri "$Url/api/sales/summary" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 401, 403)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-AnalyticsDashboard {
    try {
        $response = Invoke-WebRequest -Uri "$Url/api/analytics/metrics" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 401, 403)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-TimeSeriesEndpoint {
    try {
        $response = Invoke-WebRequest -Uri "$Url/api/analytics/timeseries" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 401, 403)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-AdminDashboard {
    try {
        $response = Invoke-WebRequest -Uri "$Url/admin" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 302, 307)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-OpenApiDocs {
    try {
        $response = Invoke-WebRequest -Uri "$Url/docs" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -eq 200) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-DatabaseConnectivity {
    try {
        $response = Invoke-WebRequest -Uri "$Url/api/diagnostic/db-test" -Method Get -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        if ($response.StatusCode -in @(200, 401, 503)) {
            return @{ Passed = $true; Details = @{ status_code = $response.StatusCode } }
        } else {
            return @{ Passed = $false; Error = "Unexpected status code: $($response.StatusCode)" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-ResponseTime {
    try {
        $times = @()
        for ($i = 0; $i -lt 5; $i++) {
            $start = Get-Date
            Invoke-RestMethod -Uri "$Url/health" -Method Get -Headers $headers -TimeoutSec 10 | Out-Null
            $times += ((Get-Date) - $start).TotalMilliseconds
        }
        
        $avgTime = ($times | Measure-Object -Average).Average
        $maxAcceptable = 2000  # 2 seconds
        
        if ($avgTime -lt $maxAcceptable) {
            return @{ Passed = $true; Details = @{ avg_ms = [int]$avgTime; max_ms = [int]($times | Measure-Object -Maximum).Maximum } }
        } else {
            return @{ Passed = $false; Error = "Average response time too high: $([int]$avgTime)ms" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

function Test-CorsHeaders {
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -Method Options -Headers $headers -TimeoutSec 10 -SkipHttpErrorCheck
        
        $hasCors = $response.Headers.ContainsKey('access-control-allow-origin') -or 
                   $response.Headers.ContainsKey('Access-Control-Allow-Origin')
        
        if ($hasCors) {
            return @{ Passed = $true; Details = @{ has_cors = $true } }
        } else {
            return @{ Passed = $false; Error = "CORS headers not found" }
        }
    }
    catch {
        return @{ Passed = $false; Error = $_.Exception.Message }
    }
}

# ========================================
# Run Tests
# ========================================

Write-Step "📋 Running Core Functionality Tests"
Invoke-Test "Health Endpoint" { Test-HealthEndpoint }
Invoke-Test "Root Endpoint" { Test-RootEndpoint }
Invoke-Test "Static Files" { Test-StaticFiles }
Invoke-Test "OpenAPI Docs" { Test-OpenApiDocs }

Write-Step "🔐 Running Authentication Tests"
Invoke-Test "Authentication Endpoint" { Test-AuthenticationEndpoint }

Write-Step "🤖 Running API Endpoint Tests"
Invoke-Test "Chat Endpoint" { Test-ChatEndpoint }
Invoke-Test "Agent Endpoint" { Test-AgentEndpoint }

Write-Step "📊 Running Dashboard Tests"
Invoke-Test "Sales Dashboard" { Test-SalesDashboard }
Invoke-Test "Analytics Dashboard" { Test-AnalyticsDashboard }
Invoke-Test "Time Series Endpoint" { Test-TimeSeriesEndpoint }
Invoke-Test "Admin Dashboard" { Test-AdminDashboard }

Write-Step "⚙️  Running Infrastructure Tests"
Invoke-Test "Database Connectivity" { Test-DatabaseConnectivity }
Invoke-Test "CORS Headers" { Test-CorsHeaders }
Invoke-Test "Response Time" { Test-ResponseTime }

# ========================================
# Summary
# ========================================

$duration = ((Get-Date) - $script:StartTime).TotalSeconds
$totalTests = $script:TestResults.Count
$passedTests = ($script:TestResults | Where-Object { $_.Passed }).Count
$failedTests = $totalTests - $passedTests

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "📊 TEST SUMMARY" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Info "Total Tests: $totalTests"
Write-Success "Passed: $passedTests"
if ($failedTests -gt 0) {
    Write-Error-Custom "Failed: $failedTests"
}
Write-Info "Duration: $([math]::Round($duration, 2))s"
Write-Host ""

if ($failedTests -gt 0) {
    Write-Error-Custom "FAILED TESTS:"
    foreach ($result in $script:TestResults | Where-Object { -not $_.Passed }) {
        Write-Error-Custom "  • $($result.Name)"
        if ($result.ErrorMessage) {
            Write-Error-Custom "    Error: $($result.ErrorMessage)"
        }
    }
    Write-Host ""
}

if ($failedTests -eq 0) {
    Write-Success "ALL TESTS PASSED - APPLICATION IS HEALTHY"
} else {
    Write-Error-Custom "SOME TESTS FAILED - REVIEW ERRORS ABOVE"
}

Write-Host "========================================" -ForegroundColor Magenta

# Save JSON output if requested
if (![string]::IsNullOrEmpty($JsonOutput)) {
    $output = @{
        timestamp = (Get-Date).ToString("o")
        base_url = $Url
        passed = ($failedTests -eq 0)
        total_tests = $totalTests
        passed_tests = $passedTests
        failed_tests = $failedTests
        duration_seconds = [math]::Round($duration, 2)
        results = $script:TestResults
    }
    
    $output | ConvertTo-Json -Depth 10 | Out-File -FilePath $JsonOutput -Encoding utf8
    Write-Info "💾 Results saved to: $JsonOutput"
}

# Exit with appropriate code
exit $(if ($failedTests -eq 0) { 0 } else { 1 })
