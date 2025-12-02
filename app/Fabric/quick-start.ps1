# Quick Start Script for Local Development and Testing
# This script sets up the local environment and tests the synthetic data generation

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Synthetic Data Generator - Quick Start" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.9 or higher." -ForegroundColor Red
    exit 1
}

# Check Azure Functions Core Tools
Write-Host "Checking Azure Functions Core Tools..." -ForegroundColor Yellow
$funcVersion = func --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Azure Functions Core Tools found: $funcVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Azure Functions Core Tools not found." -ForegroundColor Red
    Write-Host "  Install from: https://learn.microsoft.com/azure/azure-functions/functions-run-local" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv .venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check for local.settings.json
Write-Host ""
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (Test-Path "local.settings.json") {
    Write-Host "✓ local.settings.json found" -ForegroundColor Green
} else {
    Write-Host "⚠ local.settings.json not found" -ForegroundColor Yellow
    Write-Host "  Creating from template..." -ForegroundColor Yellow
    Copy-Item "local.settings.json.template" "local.settings.json"
    Write-Host "  Please edit local.settings.json with your database credentials" -ForegroundColor Red
    Write-Host "  Then run this script again." -ForegroundColor Red
    code local.settings.json
    exit 0
}

# Menu
Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Generate initial data (run generate_initial_data.py)" -ForegroundColor White
Write-Host "2. Test Azure Function locally" -ForegroundColor White
Write-Host "3. Start Azure Function in watch mode" -ForegroundColor White
Write-Host "4. Deploy to Azure" -ForegroundColor White
Write-Host "5. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running initial data generation..." -ForegroundColor Yellow
        python generate_initial_data.py
    }
    "2" {
        Write-Host ""
        Write-Host "Testing Azure Function locally..." -ForegroundColor Yellow
        Write-Host "Note: This will run the function once. Press Ctrl+C to stop." -ForegroundColor Yellow
        Write-Host ""
        func start
    }
    "3" {
        Write-Host ""
        Write-Host "Starting Azure Function in watch mode..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
        Write-Host ""
        func start --python
    }
    "4" {
        Write-Host ""
        Write-Host "Preparing to deploy to Azure..." -ForegroundColor Yellow
        $dbName = Read-Host "Enter SQL Database name"
        $dbUser = Read-Host "Enter SQL Username"
        $dbPass = Read-Host "Enter SQL Password" -AsSecureString
        $dbPassPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($dbPass))
        
        .\deploy-to-azure.ps1 -SqlDatabase $dbName -SqlUsername $dbUser -SqlPassword $dbPassPlain
    }
    "5" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
Write-Host "Done!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Green
