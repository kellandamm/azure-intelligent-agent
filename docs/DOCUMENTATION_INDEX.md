# 📚 Documentation Index

Complete guide to deploying your Azure Agent Framework application with turnkey automation.

---

## 🚀 Quick Start (Start Here!)

**Want to deploy immediately?** Choose your path:

### Path 1: Using Azure Developer CLI (azd) ⭐ Recommended

1. **[azd Deployment Guide](AZD_DEPLOYMENT_GUIDE.md)** ⭐ **SIMPLEST METHOD**
   - Just run `azd up`
   - Perfect for developers
   - Built-in environment management
   - **Time: 2 minutes to read, 15 minutes to deploy**

### Path 2: Using PowerShell Scripts

1. **[Visual Deployment Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md)** ⭐ **DETAILED CONTROL**
   - Step-by-step visual walkthrough
   - Shows exactly what you'll see during deployment
   - Perfect for first-time users wanting control
   - **Time: 5 minutes to read, 15 minutes to deploy**

2. **[Scripts README](../scripts/README.md)**
   - Detailed documentation of all deployment scripts
   - Parameter reference and examples
   - Troubleshooting guide

---

## 📖 Core Documentation

### Getting Started

| Document | Description | When to Read |
|----------|-------------|--------------|
| [Main README](../README.md) | Project overview and features | Before starting |
| [Quick Start](QUICK_START.md) | Step-by-step deployment guide | First deployment |
| [Visual Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md) | Visual walkthrough with examples | Need visual guidance |

### Configuration

| Document | Description | When to Read |
|----------|-------------|--------------|
| [Parameters Reference](PARAMETERS.md) | All bicepparam parameters explained | Configuring deployment |
| [Azure Services Guide](AZURE_SERVICES_DEPLOYMENT.md) | Azure OpenAI, AI Foundry, Fabric, Power BI setup | Optional services |

### Deployment

| Document | Description | When to Read |
|----------|-------------|--------------|
| [azd Deployment Guide](AZD_DEPLOYMENT_GUIDE.md) ⭐ | Azure Developer CLI deployment | Simplest deployment method |
| [Scripts README](../scripts/README.md) | Complete script documentation | Using PowerShell scripts |
| [Fabric Deployment](FABRIC_DEPLOYMENT.md) | Synthetic data generation setup | Need test data for demos |
| [Deployment Comparison](DEPLOYMENT_COMPARISON.md) | Before/after analysis | Understanding improvements |
| [Turnkey Summary](../TURNKEY_DEPLOYMENT_SUMMARY.md) | Complete enhancement overview | Technical details |

### Reference

| Document | Description | When to Read |
|----------|-------------|--------------|
| [Architecture](ARCHITECTURE.md) | System architecture and design | Understanding structure |
| [Security Best Practices](SECURITY.md) | Security configuration guide | Hardening deployment |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and solutions | Having problems |

---

## 🎯 Documentation by Scenario

### Scenario 1: "I want to deploy for the first time"

**Path A: Using azd (Simplest):**
1. Read: [azd Deployment Guide](AZD_DEPLOYMENT_GUIDE.md) - 5 min
2. Run: `azd up` - 15 min
3. Verify: Open application URL

**Path B: Using PowerShell (More Control):**
1. Read: [Visual Deployment Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md) - 5 min
2. Configure: [Parameters Reference](PARAMETERS.md) - 10 min
3. Deploy: Run `deploy-complete.ps1` - 15 min
4. Verify: Follow post-deployment checklist

**Total time: ~20-30 minutes from zero to deployed application**

---

### Scenario 2: "I need to understand what will be deployed"

**Path:**
1. Read: [Main README](../README.md) - Architecture section
2. Review: [Azure Services Guide](AZURE_SERVICES_DEPLOYMENT.md) - Service details
3. Check: [Parameters Reference](PARAMETERS.md) - Configuration options
4. Review: Cost estimation sections

**Total time: ~15 minutes to understand scope**

---

### Scenario 3: "I want to deploy Azure OpenAI with my app"

**Path:**
1. Read: [Azure Services Guide](AZURE_SERVICES_DEPLOYMENT.md) - Azure OpenAI section
2. Configure: Set `deployAzureOpenAI = true` in bicepparam
3. Review: [Parameters Reference](PARAMETERS.md) - Azure OpenAI parameters
4. Deploy: Run `deploy-complete.ps1`

**Additional time: No extra time, included in standard deployment**

---

### Scenario 4: "I need to set up Fabric or Power BI"

**Path:**
1. Read: [Azure Services Guide](AZURE_SERVICES_DEPLOYMENT.md) - Fabric/Power BI sections
2. Follow: Manual setup steps (these services cannot be automated)
3. Configure: Update parameters with workspace IDs after setup

**Total time: ~30-60 minutes for manual configuration**

---

### Scenario 4b: "I want to deploy with synthetic test data"

**Path (Fabric Data Management):**
1. Read: [Fabric Deployment Guide](FABRIC_DEPLOYMENT.md) - Overview
2. Deploy: Run `deploy-complete.ps1 -ResourceGroupName "rg" -DeployFabric -GenerateInitialData`
3. Verify: Run `python fabric\database\view_tables.py`
4. Manage: Use management scripts to view and test data

**Total time: ~20 minutes (automatic deployment + verification)**

---

### Scenario 5: "I just want to update my application code"

**Path:**
1. Make code changes
2. Run: `deploy-complete.ps1 -ResourceGroupName "rg-name" -SkipInfrastructure`
3. Verify: Check application URL

**Total time: ~5 minutes**

---

### Scenario 6: "Something went wrong, I need help"

**Path:**
1. Check: [Scripts README](../scripts/README.md) - Common Issues section
2. Review: [Troubleshooting Guide](TROUBLESHOOTING.md)
3. View logs: `az webapp log tail --name <app> --resource-group <rg>`
4. Check: Azure Portal for resource status

**Resolution time: Usually 5-15 minutes**

---

### Scenario 7: "I want to set up CI/CD automation"

**Path:**
1. Read: [Scripts README](../scripts/README.md) - CI/CD section
2. Review: [Deployment Comparison](DEPLOYMENT_COMPARISON.md) - CI/CD examples
3. Use: `-AutoConfirmSql` flag for automation
4. Configure: Azure DevOps or GitHub Actions pipeline

**Setup time: ~30 minutes**

---

## 📁 File Organization

```
azure-deployment-template/
│
├── 📄 README.md                              # Project overview
├── 📄 TURNKEY_DEPLOYMENT_SUMMARY.md          # Enhancement summary
│
├── 📁 bicep/                                 # Infrastructure templates
│   ├── main.bicep                            # Main template
│   ├── main.bicepparam.template              # Parameters template
│   └── modules/                              # Bicep modules
│       ├── appService.bicep
│       ├── sqlDatabase.bicep
│       ├── keyVault.bicep
│       └── azureOpenAI.bicep                 # Azure OpenAI deployment
│
├── 📁 scripts/                               # Deployment automation
│   ├── 📄 README.md                          # ⭐ Script documentation
│   ├── 💻 deploy-complete.ps1                # ⭐ Master deployment script
│   ├── 💻 prepare-app.ps1                    # Application preparation
│   └── 💻 deploy.ps1                         # Infrastructure deployment
│
├── 📁 fabric/                                # Optional data management
│   ├── 📄 README.md                          # Fabric component overview
│   ├── 📁 database/                          # Database scripts
│   ├── 📁 function/                          # Azure Function
│   └── 📁 scripts/                           # Deployment automation
│
└── 📁 docs/                                  # Documentation
    ├── 📄 DOCUMENTATION_INDEX.md             # 👈 YOU ARE HERE
    ├── 📄 AZD_DEPLOYMENT_GUIDE.md            # ⭐ azd CLI guide
    ├── 📄 DEPLOYMENT_METHODS_COMPARISON.md   # azd vs PowerShell
    ├── 📄 TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md # ⭐ Visual walkthrough
    ├── 📄 DEPLOYMENT_COMPARISON.md           # Before/after analysis
    ├── 📄 AZURE_SERVICES_DEPLOYMENT.md       # Azure services guide
    ├── 📄 FABRIC_DEPLOYMENT.md               # Fabric data management
    ├── 📄 QUICK_START.md                     # Quick start guide
    ├── 📄 PARAMETERS.md                      # Parameters reference
    ├── 📄 ARCHITECTURE.md                    # Architecture details
    ├── 📄 SECURITY.md                        # Security best practices
    └── 📄 TROUBLESHOOTING.md                 # Common issues
```

---

## 🎓 Learning Path

### Level 1: Beginner (Never deployed to Azure before)

**Goal:** Successfully deploy the application

1. **Start:** [Visual Deployment Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md) - See what happens
2. **Understand:** [Main README](../README.md) - Learn about the application
3. **Configure:** [Parameters Reference](PARAMETERS.md) - Set up your deployment
4. **Deploy:** Follow the visual guide step-by-step
5. **Verify:** Check that everything works

**Time: 1-2 hours including reading**

---

### Level 2: Intermediate (Familiar with Azure)

**Goal:** Customize and optimize deployment

1. **Review:** [Architecture](ARCHITECTURE.md) - Understand the design
2. **Explore:** [Azure Services Guide](AZURE_SERVICES_DEPLOYMENT.md) - Optional services
3. **Customize:** [Parameters Reference](PARAMETERS.md) - Tune for your needs
4. **Secure:** [Security Best Practices](SECURITY.md) - Harden deployment
5. **Automate:** [Scripts README](../scripts/README.md) - Advanced usage

**Time: 2-3 hours for full mastery**

---

### Level 3: Advanced (DevOps/Platform Engineer)

**Goal:** Production deployment and CI/CD automation

1. **Analyze:** [Deployment Comparison](DEPLOYMENT_COMPARISON.md) - Understand automation
2. **Study:** [Turnkey Summary](../TURNKEY_DEPLOYMENT_SUMMARY.md) - Technical details
3. **Review:** Script source code - Understand implementation
4. **Customize:** Modify scripts for your requirements
5. **Integrate:** Set up CI/CD pipelines
6. **Monitor:** Configure monitoring and alerting

**Time: 4-8 hours for production-ready setup**

---

## 🔍 Quick Reference by Topic

### Azure OpenAI
- [Azure Services Guide - OpenAI Section](AZURE_SERVICES_DEPLOYMENT.md#azure-openai)
- [Parameters Reference - OpenAI Parameters](PARAMETERS.md#azure-openai-settings)
- Bicep Module: `bicep/modules/azureOpenAI.bicep`

### Azure AI Foundry
- [Azure Services Guide - AI Foundry Section](AZURE_SERVICES_DEPLOYMENT.md#azure-ai-foundry)
- Manual setup required for agents

### Microsoft Fabric
- [Azure Services Guide - Fabric Section](AZURE_SERVICES_DEPLOYMENT.md#microsoft-fabric)
- Manual setup required

### Power BI
- [Azure Services Guide - Power BI Section](AZURE_SERVICES_DEPLOYMENT.md#power-bi)
- Manual setup required

### SQL Database
- [Parameters Reference - SQL Settings](PARAMETERS.md#sql-database-settings)
- [Quick Start - SQL Configuration](QUICK_START.md#sql-configuration)

### Key Vault
- [Parameters Reference - Key Vault Settings](PARAMETERS.md#key-vault-settings)
- [Security Guide - Secrets Management](SECURITY.md#secrets-management)

### Monitoring
- [Parameters Reference - Monitoring Settings](PARAMETERS.md#monitoring-settings)
- [Architecture - Observability](ARCHITECTURE.md#observability)

### CI/CD
- [Scripts README - CI/CD Section](../scripts/README.md#cicd)
- [Deployment Comparison - CI/CD Examples](DEPLOYMENT_COMPARISON.md#cicd)

---

## 📊 Documentation Metrics

| Document | Pages | Reading Time | Purpose |
|----------|-------|--------------|---------|
| Visual Guide | ~15 | 10 min | Quick start |
| Scripts README | ~20 | 15 min | Script reference |
| Azure Services | ~25 | 20 min | Service setup |
| Deployment Comparison | ~30 | 20 min | Understanding improvements |
| Parameters Reference | ~15 | 10 min | Configuration |
| Quick Start | ~10 | 10 min | Step-by-step guide |
| Main README | ~15 | 10 min | Overview |
| Turnkey Summary | ~30 | 20 min | Technical details |
| **Total** | **~160** | **~2 hours** | Complete reference |

---

## 🎯 Most Important Documents

### Top 3 for Everyone:

1. **[Visual Deployment Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md)** ⭐⭐⭐
   - Must-read for first deployment
   - Shows exactly what to expect
   - 90% of users should start here

2. **[Scripts README](../scripts/README.md)** ⭐⭐⭐
   - Essential reference for deployment scripts
   - Includes troubleshooting
   - Read before running any script

3. **[Parameters Reference](PARAMETERS.md)** ⭐⭐
   - Required for configuration
   - Explains all settings
   - Refer to while configuring

---

## 💡 Documentation Tips

### For First-Time Users:
✅ Start with Visual Deployment Guide  
✅ Don't read everything - focus on what you need  
✅ Follow the scenario-based paths above  
✅ Come back to other docs as needed  

### For Experienced Users:
✅ Skip to Scripts README for advanced usage  
✅ Review Parameters Reference for customization  
✅ Check Deployment Comparison for best practices  
✅ Use this index as a quick reference  

### For DevOps Engineers:
✅ Read Turnkey Summary for technical details  
✅ Study script source code  
✅ Review Architecture documentation  
✅ Check Security best practices  

---

## 🆘 Getting Help

### Can't Find What You Need?

1. **Check this index** - Use scenario-based navigation
2. **Search within documents** - Use Ctrl+F in VS Code
3. **Check script output** - Scripts provide detailed help
4. **Review Azure logs** - Often has specific error messages
5. **Ask questions** - Include script output and error messages

### Still Stuck?

Include these details when asking for help:
- Which document you were following
- What step you're on
- Error message (full text)
- Script output
- Azure region
- Subscription type

---

## 📝 Documentation Updates

This documentation reflects the **Turnkey Deployment Enhancement** completed in January 2024.

**What's New:**
- ✅ Turnkey deployment scripts (deploy-complete.ps1, prepare-app.ps1)
- ✅ Visual deployment guide with examples
- ✅ Deployment comparison analysis
- ✅ Comprehensive script documentation
- ✅ This documentation index

**Previous Features:**
- Azure OpenAI optional deployment
- Azure Services Deployment Guide
- Original Bicep templates and modules

---

## 🎊 Ready to Deploy?

**Choose your path:**

- 🚀 **Fast track:** [Visual Deployment Guide](TURNKEY_DEPLOYMENT_VISUAL_GUIDE.md)
- 📖 **Detailed path:** [Quick Start Guide](QUICK_START.md)
- 🔧 **Technical path:** [Scripts README](../scripts/README.md)

**Then run:**
```powershell
cd scripts
.\deploy-complete.ps1 -ResourceGroupName "rg-your-app-prod"
```

**That's all!** ☕ Grab coffee and come back to a deployed application in 15 minutes.

---

## 📚 Printable Checklist

**Pre-Deployment:**
- [ ] Azure CLI installed
- [ ] Logged in to Azure (`az login`)
- [ ] Subscription selected
- [ ] Parameters file configured
- [ ] Application code available

**Deployment:**
- [ ] Run deploy-complete.ps1
- [ ] Monitor progress
- [ ] Complete SQL configuration
- [ ] Wait for completion

**Post-Deployment:**
- [ ] Open application URL
- [ ] Test API endpoints
- [ ] Check logs
- [ ] Configure monitoring
- [ ] Update DNS (if needed)

**Optional Services:**
- [ ] Set up Microsoft Fabric (manual)
- [ ] Configure Power BI (manual)
- [ ] Deploy Azure OpenAI (optional)
- [ ] Set up Azure AI Foundry (partial)

---

**Made with ❤️ for Azure Agent Framework**  
*Making documentation as turnkey as deployment* 📚✨
