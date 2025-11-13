# 🔄 Fabric Integration Strategy

## 📊 Overview

The **Fabric component** provides synthetic data generation and maintenance for the Azure SQL database. This document outlines how to integrate it into the deployment template.

---

## 🎯 What is the Fabric Component?

Based on your existing code, the Fabric component includes:

1. **SQL Schema Deployment** - Creates database tables and relationships
2. **Initial Data Generation** - Seeds the database with synthetic data
3. **Azure Function** - Maintains and generates ongoing synthetic data
4. **Data Management Scripts** - View, test, and manage database content

### Key Files:
- `deploy_schema.py` - Deploy database schema
- `generate_initial_data.py` - Create initial synthetic data
- `function_app.py` - Azure Function for ongoing data generation
- `view_tables.py` / `view_schemas.py` - Database inspection tools
- `test_connection.py` - Verify database connectivity

---

## 🏗️ Recommended Integration Approach

### Option 1: Separate Fabric Folder (Recommended) ⭐

**Structure:**
```
azure-deployment-template/
├── fabric/                           # NEW: Fabric data management
│   ├── README.md                     # Fabric-specific documentation
│   ├── requirements.txt              # Python dependencies
│   ├── deploy_schema.py              # Deploy DB schema
│   ├── generate_initial_data.py      # Generate seed data
│   ├── view_tables.py                # View DB tables
│   ├── view_schemas.py               # View DB schemas
│   ├── test_connection.py            # Test DB connection
│   ├── function/                     # Azure Function
│   │   ├── function_app.py           # Function code
│   │   ├── host.json                 # Function host config
│   │   ├── local.settings.json.template
│   │   └── requirements.txt          # Function dependencies
│   └── scripts/                      # Deployment scripts
│       ├── deploy-fabric-function.ps1
│       ├── setup-database.ps1
│       └── generate-data.ps1
├── bicep/
├── scripts/
└── docs/
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Can be deployed independently
- ✅ Easy to include/exclude from main deployment
- ✅ Self-contained with own README and dependencies

---

### Option 2: Integrated into Main Scripts

**Structure:**
```
azure-deployment-template/
├── scripts/
│   ├── deploy-complete.ps1           # Extended with Fabric steps
│   ├── deploy-fabric.ps1             # NEW: Fabric deployment
│   └── ...
├── fabric/                            # Fabric code
└── docs/
    └── FABRIC_DEPLOYMENT.md           # NEW: Fabric guide
```

**Benefits:**
- ✅ Single deployment flow
- ✅ Integrated with existing scripts
- ✅ Unified deployment experience

---

## 🚀 Implementation Plan (Option 1 - Recommended)

### Phase 1: Create Fabric Folder Structure

1. **Create `fabric/` directory** with all necessary code
2. **Add Fabric-specific README** with setup instructions
3. **Include deployment scripts** for Fabric components

### Phase 2: Extend Deployment Scripts

Update `deploy-complete.ps1` to include optional Fabric deployment:

```powershell
# New parameter
param(
    [switch]$DeployFabric,
    # ... existing parameters
)

# New step after app deployment
if ($DeployFabric) {
    Write-Host "═══════════════════════════════════════════════════════════════"
    Write-Host "STEP 6/6: Deploying Fabric Components"
    Write-Host "═══════════════════════════════════════════════════════════════"
    
    # Deploy database schema
    python ..\fabric\deploy_schema.py
    
    # Generate initial data
    python ..\fabric\generate_initial_data.py
    
    # Deploy Azure Function
    & ..\fabric\scripts\deploy-fabric-function.ps1
}
```

### Phase 3: Add azd Support

Update `azure.yaml` to include Fabric function:

```yaml
services:
  web:
    project: ./app
    # ... existing config
  
  fabric-function:
    project: ./fabric/function
    language: python
    host: function
    hooks:
      prerestore:
        shell: sh
        run: |
          echo "Installing Fabric function dependencies..."
          pip install -r requirements.txt
```

### Phase 4: Documentation

Create comprehensive documentation:
- `fabric/README.md` - Fabric component guide
- `docs/FABRIC_DEPLOYMENT.md` - Deployment instructions
- Update main README with Fabric section

---

## 📝 Detailed Implementation

### 1. Fabric Directory Structure

```
fabric/
├── README.md                          # Main Fabric documentation
├── requirements.txt                   # Python dependencies
├── .env.template                      # Environment variable template
├── .gitignore                         # Ignore local settings
│
├── scripts/                           # PowerShell deployment scripts
│   ├── deploy-fabric-function.ps1    # Deploy Azure Function
│   ├── setup-database.ps1            # Deploy schema and seed data
│   └── test-fabric.ps1               # Test Fabric components
│
├── database/                          # Database management
│   ├── deploy_schema.py              # Deploy SQL schema
│   ├── generate_initial_data.py      # Generate synthetic data
│   ├── view_tables.py                # View table contents
│   ├── view_schemas.py               # View schema info
│   ├── test_connection.py            # Test DB connection
│   └── schema/                       # SQL schema files
│       ├── tables.sql
│       ├── views.sql
│       └── stored_procedures.sql
│
└── function/                          # Azure Function
    ├── function_app.py               # Function code
    ├── host.json                     # Function host config
    ├── requirements.txt              # Function dependencies
    ├── local.settings.json.template  # Settings template
    └── .funcignore                   # Files to ignore
```

---

### 2. Updated deploy-complete.ps1

Add Fabric deployment as optional step:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [string]$Location = "eastus2",
    [string]$ParametersFile,
    [string]$SourceAppDir,
    [switch]$SkipPreparation,
    [switch]$SkipInfrastructure,
    [switch]$SkipSqlConfig,
    [switch]$SkipAppCode,
    [switch]$AutoConfirmSql,
    [switch]$DeployFabric,              # NEW: Deploy Fabric components
    [switch]$GenerateInitialData        # NEW: Generate seed data
)

# ... existing steps 1-5 ...

# NEW: Step 6 - Deploy Fabric Components (Optional)
if ($DeployFabric) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "STEP 6/6: Deploying Fabric Components" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    # Deploy database schema
    Write-Host "📊 Deploying database schema..." -ForegroundColor Cyan
    $schemaResult = python "$PSScriptRoot\..\fabric\database\deploy_schema.py"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Schema deployment failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Schema deployed successfully" -ForegroundColor Green
    
    # Generate initial data (if requested)
    if ($GenerateInitialData) {
        Write-Host "🎲 Generating initial synthetic data..." -ForegroundColor Cyan
        $dataResult = python "$PSScriptRoot\..\fabric\database\generate_initial_data.py"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️  Initial data generation had warnings" -ForegroundColor Yellow
        } else {
            Write-Host "  ✓ Initial data generated successfully" -ForegroundColor Green
        }
    }
    
    # Deploy Azure Function
    Write-Host "⚡ Deploying Fabric Azure Function..." -ForegroundColor Cyan
    & "$PSScriptRoot\..\fabric\scripts\deploy-fabric-function.ps1" `
        -ResourceGroupName $ResourceGroupName `
        -WebAppName $webAppName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Fabric function deployed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Fabric function deployment failed" -ForegroundColor Red
        exit 1
    }
}

# Update summary to include Fabric
if ($DeployFabric) {
    Write-Host "   • Fabric Function: func-$webAppName" -ForegroundColor White
    Write-Host ""
    Write-Host "   6. 📊 Verify Fabric data generation:" -ForegroundColor Cyan
    Write-Host "      python fabric\database\view_tables.py" -ForegroundColor White
}
```

---

### 3. Updated azure.yaml (for azd)

Add Fabric function as a service:

```yaml
name: azure-agent-framework

services:
  web:
    project: ./app
    language: python
    host: appservice
  
  # NEW: Fabric data generation function
  fabric:
    project: ./fabric/function
    language: python
    host: function
    hooks:
      prerestore:
        shell: sh
        run: |
          echo "Installing Fabric function dependencies..."
          pip install -r requirements.txt
      
      postdeploy:
        shell: pwsh
        run: |
          Write-Host "📊 Setting up Fabric database schema..." -ForegroundColor Cyan
          python ../database/deploy_schema.py
          
          Write-Host "🎲 Generating initial data..." -ForegroundColor Cyan
          python ../database/generate_initial_data.py

# Environment variables for Fabric
hooks:
  postprovision:
    shell: pwsh
    run: |
      # ... existing SQL config ...
      
      Write-Host ""
      Write-Host "📊 Fabric Configuration:" -ForegroundColor Cyan
      Write-Host "   The Fabric function will automatically generate synthetic data." -ForegroundColor White
      Write-Host "   View data: python fabric/database/view_tables.py" -ForegroundColor White
```

---

### 4. Fabric README.md

Create comprehensive documentation:

```markdown
# Fabric Data Management

This component provides synthetic data generation and maintenance for the Azure SQL database.

## Components

1. **Database Schema** - SQL tables, views, stored procedures
2. **Data Generation** - Python scripts to create synthetic data
3. **Azure Function** - Automated ongoing data generation
4. **Management Tools** - Scripts to view and test database

## Quick Start

### Deploy Database Schema

```powershell
python database/deploy_schema.py
```

### Generate Initial Data

```powershell
python database/generate_initial_data.py
```

### Deploy Azure Function

```powershell
cd scripts
.\deploy-fabric-function.ps1 -ResourceGroupName "rg-myagents-prod"
```

## Configuration

Set these environment variables:

- `SQL_SERVER` - Azure SQL server name
- `SQL_DATABASE` - Database name
- `SQL_USERNAME` - SQL admin username
- `SQL_PASSWORD` - SQL admin password

## Usage

### View Tables

```powershell
python database/view_tables.py
```

### Test Connection

```powershell
python database/test_connection.py
```

### View Schemas

```powershell
python database/view_schemas.py
```
```

---

### 5. New PowerShell Scripts

**`fabric/scripts/deploy-fabric-function.ps1`:**

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$WebAppName
)

$functionAppName = "func-$WebAppName"
$storageAccountName = "st$($WebAppName.Replace('-',''))".Substring(0, [Math]::Min(24, "st$($WebAppName.Replace('-',''))".Length))

Write-Host "Creating Azure Function App: $functionAppName" -ForegroundColor Cyan

# Create storage account for function
az storage account create `
    --name $storageAccountName `
    --resource-group $ResourceGroupName `
    --location eastus2 `
    --sku Standard_LRS

# Create function app
az functionapp create `
    --name $functionAppName `
    --resource-group $ResourceGroupName `
    --storage-account $storageAccountName `
    --consumption-plan-location eastus2 `
    --runtime python `
    --runtime-version 3.11 `
    --functions-version 4 `
    --os-type Linux

# Deploy function code
cd "$PSScriptRoot\..\function"
func azure functionapp publish $functionAppName

Write-Host "✓ Fabric function deployed successfully" -ForegroundColor Green
```

---

## 📚 Documentation to Create

1. **`fabric/README.md`** - Fabric component overview and quick start
2. **`docs/FABRIC_DEPLOYMENT.md`** - Detailed deployment guide
3. **`docs/FABRIC_ARCHITECTURE.md`** - How Fabric integrates with the system
4. **Update `docs/AZURE_SERVICES_DEPLOYMENT.md`** - Add Fabric section
5. **Update main `README.md`** - Mention optional Fabric deployment

---

## 🎯 Usage Examples

### Deploy with Fabric (PowerShell):

```powershell
# Full deployment including Fabric
.\scripts\deploy-complete.ps1 `
    -ResourceGroupName "rg-myagents-prod" `
    -DeployFabric `
    -GenerateInitialData
```

### Deploy with Fabric (azd):

```bash
# Deploy everything including Fabric function
azd up

# Fabric function automatically included
```

### Deploy Fabric Separately:

```powershell
# Just deploy Fabric components
cd fabric\scripts
.\deploy-fabric-function.ps1 -ResourceGroupName "rg-myagents-prod" -WebAppName "webapp-myagents-prod"
```

---

## ✅ Benefits of This Approach

1. **Clear Separation** - Fabric is self-contained and optional
2. **Easy to Include/Exclude** - Use `-DeployFabric` flag
3. **Independent Deployment** - Can deploy Fabric separately
4. **Testable** - Scripts to test each component
5. **Documented** - Comprehensive documentation
6. **azd Support** - Works with both deployment methods
7. **Maintainable** - Easy to update Fabric independently

---

## 🚀 Next Steps

**What would you like me to do?**

1. **Create the full `fabric/` folder structure** with all scripts and documentation
2. **Update `deploy-complete.ps1`** to include optional Fabric deployment
3. **Update `azure.yaml`** to include Fabric function
4. **Create comprehensive Fabric documentation**
5. **Update main README** with Fabric information

Let me know which approach you prefer, and I'll implement it! 🎯
