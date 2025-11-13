# ========================================
# Setup Fabric Database Schema and Data
# ========================================

param(
    [string]$SqlServer = $env:SQL_SERVER,
    [string]$SqlDatabase = $env:SQL_DATABASE,
    [switch]$SkipSchema,
    [switch]$SkipData,
    [switch]$GenerateData
)

# Color output functions
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Fabric Database Setup" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Validate parameters
if (-not $SqlServer) {
    Write-Error "SQL_SERVER environment variable or -SqlServer parameter required"
    Write-Host "Usage: .\setup-database.ps1 -SqlServer 'server.database.windows.net' -SqlDatabase 'dbname'" -ForegroundColor Gray
    exit 1
}

if (-not $SqlDatabase) {
    Write-Error "SQL_DATABASE environment variable or -SqlDatabase parameter required"
    exit 1
}

Write-Info "SQL Server: $SqlServer"
Write-Info "Database: $SqlDatabase"
Write-Host ""

# Set environment variables for Python scripts
$env:SQL_SERVER = $SqlServer
$env:SQL_DATABASE = $SqlDatabase

try {
    # Navigate to database directory
    Push-Location "$PSScriptRoot\..\database"
    
    # Check Python is installed
    $pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonInstalled) {
        Write-Error "Python is not installed or not in PATH"
        exit 1
    }
    
    # Check for required Python packages
    Write-Info "Checking Python dependencies..."
    $pipList = pip list 2>$null
    $requiredPackages = @("pyodbc", "azure-identity", "Faker")
    $missingPackages = @()
    
    foreach ($package in $requiredPackages) {
        if ($pipList -notmatch $package) {
            $missingPackages += $package
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Warning "Missing packages: $($missingPackages -join ', ')"
        Write-Info "Installing missing packages..."
        pip install $missingPackages -q
    }
    Write-Success "  ✓ Dependencies installed"
    Write-Host ""
    
    # Deploy schema
    if (-not $SkipSchema) {
        Write-Info "Deploying database schema..."
        python deploy_schema.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ Schema deployed successfully"
        } else {
            Write-Error "  ✗ Schema deployment failed"
            Pop-Location
            exit 1
        }
        Write-Host ""
    } else {
        Write-Info "Skipping schema deployment"
    }
    
    # Generate initial data
    if ($GenerateData -and -not $SkipData) {
        Write-Info "Generating initial synthetic data..."
        python generate_initial_data.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  ✓ Initial data generated successfully"
        } else {
            Write-Warning "  ⚠ Initial data generation had warnings"
        }
        Write-Host ""
    } elseif (-not $SkipData) {
        Write-Info "Skipping data generation (use -GenerateData to enable)"
    }
    
    # Test connection
    Write-Info "Testing database connection..."
    python test_connection.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  ✓ Database connection successful"
    } else {
        Write-Warning "  ⚠ Database connection test failed"
    }
    
    Pop-Location
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "Database Setup Complete!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    
    Write-Info "📋 Next Steps:"
    Write-Host "  1. View tables:" -ForegroundColor White
    Write-Host "     python fabric\database\view_tables.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. View schemas:" -ForegroundColor White
    Write-Host "     python fabric\database\view_schemas.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Deploy Fabric function:" -ForegroundColor White
    Write-Host "     .\fabric\scripts\deploy-fabric-function.ps1 -ResourceGroupName 'rg-name' -SqlServerName 'server' -SqlDatabaseName 'db'" -ForegroundColor Gray
    Write-Host ""
    
    exit 0
    
} catch {
    Write-Error "✗ Setup failed: $_"
    Pop-Location
    exit 1
}
