#!/usr/bin/env pwsh
#Requires -Version 7.0

<#
.SYNOPSIS
    Prepares application code for Azure deployment

.DESCRIPTION
    This script copies essential application files from the source directory to the
    deployment package, excluding unnecessary files like venv, cache, and deployment folders.

.PARAMETER SourceDir
    Path to the source application directory (default: parent directory of template)

.PARAMETER DestinationDir
    Path to destination app directory (default: ./app)

.PARAMETER Force
    Force overwrite existing files in destination

.EXAMPLE
    .\prepare-app.ps1
    
.EXAMPLE
    .\prepare-app.ps1 -SourceDir "C:\myapp" -Force
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$SourceDir = "",
    
    [Parameter(Mandatory = $false)]
    [string]$DestinationDir = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Color functions
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Info { param([string]$Message) Write-Host "ℹ️  $Message" -ForegroundColor Cyan }
function Write-Warning-Custom { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error-Custom { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param([string]$Message) Write-Host "`n========================================" -ForegroundColor Magenta; Write-Host $Message -ForegroundColor Magenta; Write-Host "========================================`n" -ForegroundColor Magenta }

# ========================================
# Initialize
# ========================================

Write-Step "🚀 Preparing Application for Deployment"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TemplateRoot = Split-Path -Parent $ScriptDir

# Set default source directory (parent of template)
if ([string]::IsNullOrEmpty($SourceDir)) {
    $SourceDir = Split-Path -Parent $TemplateRoot
}

# Set default destination directory
if ([string]::IsNullOrEmpty($DestinationDir)) {
    $DestinationDir = Join-Path $TemplateRoot "app"
}

Write-Info "Source Directory: $SourceDir"
Write-Info "Destination Directory: $DestinationDir"

# Validate source directory
if (-not (Test-Path $SourceDir)) {
    Write-Error-Custom "Source directory not found: $SourceDir"
    exit 1
}

# Check for essential files
$essentialFiles = @("main.py", "requirements.txt", "config.py")
$missingFiles = @()

foreach ($file in $essentialFiles) {
    $filePath = Join-Path $SourceDir $file
    if (-not (Test-Path $filePath)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Error-Custom "Essential files missing in source directory:"
    $missingFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Success "Source directory validated"

# ========================================
# Check Destination
# ========================================

if (Test-Path $DestinationDir) {
    if (-not $Force) {
        Write-Warning-Custom "Destination directory already exists: $DestinationDir"
        $response = Read-Host "Overwrite existing files? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Cancelled by user"
            exit 0
        }
    }
    Write-Info "Cleaning destination directory..."
    Remove-Item -Path "$DestinationDir\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    Write-Info "Creating destination directory..."
    New-Item -Path $DestinationDir -ItemType Directory -Force | Out-Null
}

Write-Success "Destination directory ready"

# ========================================
# Define Files and Folders to Copy
# ========================================

# Files to copy (root level)
$filesToCopy = @(
    "main.py",
    "config.py",
    "requirements.txt",
    "agent_framework_manager.py",
    "agent_tools.py",
    "routes_sales.py",
    "host.json",
    ".env.template"
)

# Add Dockerfile if it exists
if (Test-Path (Join-Path $SourceDir "Dockerfile")) {
    $filesToCopy += "Dockerfile"
}

# Folders to copy
$foldersToCopy = @(
    "app",
    "agent_framework",
    "utils",
    "static",
    "demos"
)

# Optional folders (copy if they exist)
$optionalFolders = @(
    "Fabric"
)

# Folders/files to exclude
$excludePatterns = @(
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    ".env",  # Don't copy actual .env with secrets
    "venv",
    ".venv",
    "node_modules",
    ".git",
    ".gitignore",
    "deployment",
    "azure-deployment-template",
    "tests"
)

# ========================================
# Copy Files
# ========================================

Write-Step "📦 Copying Application Files"

$copiedFiles = 0
$copiedFolders = 0

# Copy root files
Write-Info "Copying root files..."
foreach ($file in $filesToCopy) {
    $srcPath = Join-Path $SourceDir $file
    $dstPath = Join-Path $DestinationDir $file
    
    if (Test-Path $srcPath) {
        Copy-Item -Path $srcPath -Destination $dstPath -Force
        Write-Host "  ✓ $file" -ForegroundColor Green
        $copiedFiles++
    } else {
        Write-Host "  ⊗ $file (not found)" -ForegroundColor Yellow
    }
}

# Copy folders
Write-Info "`nCopying application folders..."
foreach ($folder in $foldersToCopy) {
    $srcPath = Join-Path $SourceDir $folder
    $dstPath = Join-Path $DestinationDir $folder
    
    if (Test-Path $srcPath) {
        # Create destination folder
        New-Item -Path $dstPath -ItemType Directory -Force | Out-Null
        
        # Copy contents, excluding patterns
        $excludeString = $excludePatterns -join ","
        
        Get-ChildItem -Path $srcPath -Recurse | ForEach-Object {
            $relativePath = $_.FullName.Substring($srcPath.Length)
            $shouldExclude = $false
            
            foreach ($pattern in $excludePatterns) {
                if ($_.FullName -like "*$pattern*") {
                    $shouldExclude = $true
                    break
                }
            }
            
            if (-not $shouldExclude) {
                $targetPath = Join-Path $dstPath $relativePath
                if ($_.PSIsContainer) {
                    New-Item -Path $targetPath -ItemType Directory -Force | Out-Null
                } else {
                    $targetDir = Split-Path -Parent $targetPath
                    if (-not (Test-Path $targetDir)) {
                        New-Item -Path $targetDir -ItemType Directory -Force | Out-Null
                    }
                    Copy-Item -Path $_.FullName -Destination $targetPath -Force
                }
            }
        }
        
        $fileCount = (Get-ChildItem -Path $dstPath -Recurse -File).Count
        Write-Host "  ✓ $folder ($fileCount files)" -ForegroundColor Green
        $copiedFolders++
    } else {
        Write-Host "  ⊗ $folder (not found)" -ForegroundColor Yellow
    }
}

# Copy optional folders
Write-Info "`nCopying optional folders..."
foreach ($folder in $optionalFolders) {
    $srcPath = Join-Path $SourceDir $folder
    $dstPath = Join-Path $DestinationDir $folder
    
    if (Test-Path $srcPath) {
        New-Item -Path $dstPath -ItemType Directory -Force | Out-Null
        Copy-Item -Path "$srcPath\*" -Destination $dstPath -Recurse -Force
        $fileCount = (Get-ChildItem -Path $dstPath -Recurse -File).Count
        Write-Host "  ✓ $folder ($fileCount files)" -ForegroundColor Green
        $copiedFolders++
    } else {
        Write-Host "  ⊗ $folder (optional, not found)" -ForegroundColor DarkGray
    }
}

Write-Success "`nCopied $copiedFiles files and $copiedFolders folders"

# ========================================
# Create .deployment file
# ========================================

Write-Step "⚙️ Creating Deployment Configuration"

$deploymentContent = @"
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT = true
"@

$deploymentFile = Join-Path $DestinationDir ".deployment"
Set-Content -Path $deploymentFile -Value $deploymentContent -Force
Write-Success ".deployment file created"

# ========================================
# Create startup script for App Service
# ========================================

$startupContent = @"
#!/bin/bash
# Azure App Service startup script for Python application

echo "Starting Agent Framework Application..."

# Install dependencies
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# Start the application with Gunicorn
echo "Starting Gunicorn server..."
gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=uvicorn.workers.UvicornWorker --timeout=600 main:app
"@

$startupFile = Join-Path $DestinationDir "startup.sh"
Set-Content -Path $startupFile -Value $startupContent -Force -NoNewline
Write-Success "startup.sh created"

# ========================================
# Validate Deployment Package
# ========================================

Write-Step "✅ Validating Deployment Package"

$validationErrors = @()

# Check for required files
$requiredFiles = @("main.py", "requirements.txt", "config.py", ".deployment")
foreach ($file in $requiredFiles) {
    if (-not (Test-Path (Join-Path $DestinationDir $file))) {
        $validationErrors += "Missing required file: $file"
    }
}

# Check for required folders
$requiredFolders = @("app", "agent_framework")
foreach ($folder in $requiredFolders) {
    if (-not (Test-Path (Join-Path $DestinationDir $folder))) {
        $validationErrors += "Missing required folder: $folder"
    }
}

# Check requirements.txt content
$requirementsPath = Join-Path $DestinationDir "requirements.txt"
if (Test-Path $requirementsPath) {
    $requirements = Get-Content $requirementsPath -Raw
    $criticalPackages = @("fastapi", "uvicorn", "gunicorn", "azure-identity")
    
    foreach ($package in $criticalPackages) {
        if ($requirements -notlike "*$package*") {
            $validationErrors += "requirements.txt missing critical package: $package"
        }
    }
}

if ($validationErrors.Count -gt 0) {
    Write-Error-Custom "Validation failed:"
    $validationErrors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Success "Deployment package validated successfully"

# ========================================
# Summary
# ========================================

Write-Step "📊 Deployment Package Summary"

$totalFiles = (Get-ChildItem -Path $DestinationDir -Recurse -File).Count
$totalSize = (Get-ChildItem -Path $DestinationDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "Location: $DestinationDir" -ForegroundColor Cyan
Write-Host "Total Files: $totalFiles" -ForegroundColor Cyan
Write-Host "Total Size: $totalSizeMB MB" -ForegroundColor Cyan

Write-Host "`n📁 Package Contents:" -ForegroundColor Yellow
Get-ChildItem -Path $DestinationDir -Directory | ForEach-Object {
    $fileCount = (Get-ChildItem -Path $_.FullName -Recurse -File).Count
    Write-Host "  📂 $($_.Name) ($fileCount files)" -ForegroundColor White
}

Write-Host "`n📄 Root Files:" -ForegroundColor Yellow
Get-ChildItem -Path $DestinationDir -File | ForEach-Object {
    Write-Host "  📄 $($_.Name)" -ForegroundColor White
}

Write-Success "`n✅ Application ready for deployment!"

Write-Host "`n💡 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Review the prepared files in: $DestinationDir"
Write-Host "  2. Update configuration if needed (check .env.template)"
Write-Host "  3. Run: .\deploy.ps1 -ResourceGroupName <your-rg-name>"
Write-Host ""
