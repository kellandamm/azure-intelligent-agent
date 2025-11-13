# Azure Agent Framework - Deployment Template Summary

## 🎉 What's Been Created

This folder contains a **complete, production-ready Azure deployment template** for the Microsoft Agent Framework application. Anyone can use this template to deploy the application to their own Azure subscription.

---

## 📁 Folder Structure

```
azure-deployment-template/
│
├── bicep/                          # Infrastructure as Code
│   ├── main.bicep                  # Main orchestration template
│   ├── main.bicepparam             # Parameters file with examples
│   └── modules/                    # Modular Bicep templates
│       ├── appInsights.bicep       # Application Insights monitoring
│       ├── appService.bicep        # App Service Plan & Web App
│       ├── containerRegistry.bicep # Azure Container Registry (optional)
│       ├── keyVault.bicep          # Key Vault for secrets
│       ├── roleAssignment.bicep    # RBAC role assignments
│       └── sqlServer.bicep         # SQL Server & Database
│
├── scripts/                        # Deployment automation
│   └── deploy.ps1                  # PowerShell deployment script
│
├── docs/                           # Documentation
│   ├── QUICK_START.md              # 15-minute deployment guide
│   └── PARAMETERS.md               # Complete parameters reference
│
├── app/                            # Application code (to be copied)
│   └── (Your application files go here)
│
└── README.md                       # Main documentation

```

---

## 🏗️ What Gets Deployed

### Azure Resources Created:

| Resource | Purpose | Cost (approx.) |
|----------|---------|----------------|
| **Resource Group** | Container for all resources | Free |
| **App Service Plan** (Linux, B2) | Hosts the web application | ~$26/month |
| **App Service** (Python 3.11) | FastAPI application runtime | Included in plan |
| **SQL Server** | Database server | Free (pay for database) |
| **SQL Database** (Basic/S0) | Stores application data | ~$5-15/month |
| **Key Vault** (optional) | Secure secrets management | ~$1/month |
| **Application Insights** (optional) | Monitoring & diagnostics | ~$2-10/month |
| **Container Registry** (optional) | Docker image storage | ~$20/month |

**Total Estimated Cost**: ~$35-75/month for development, $200-300/month for production

---

## ✨ Key Features

### 1. **Modular Bicep Templates**
- Separate modules for each Azure service
- Easy to customize and extend
- Follows Azure best practices
- Infrastructure as Code (IaC) approach

### 2. **Security Built-In**
- Azure Key Vault for secrets management
- Managed identities (no passwords in code)
- Azure AD authentication for SQL
- HTTPS-only with TLS 1.2+
- JWT authentication with Row-Level Security (RLS)

### 3. **Production-Ready**
- Application Insights monitoring
- Health check endpoints
- Automated scaling support
- Comprehensive logging
- Error handling and diagnostics

### 4. **Flexible Configuration**
- Support for dev/staging/prod environments
- Optional features (Key Vault, Container Registry)
- Configurable SKUs and pricing tiers
- Multiple authentication modes

### 5. **Complete Documentation**
- Step-by-step deployment guide
- Complete parameter reference
- Troubleshooting tips
- Cost estimates
- Best practices

---

## 🚀 How to Use

### Quick Start (15 minutes):

1. **Configure Parameters**:
   ```bash
   cd bicep
   # Edit main.bicepparam with your Azure resource IDs
   ```

2. **Deploy**:
   ```powershell
   cd scripts
   ./deploy.ps1 -ResourceGroupName "rg-myapp" -Location "eastus2"
   ```

3. **Access Application**:
   ```
   https://<your-app-name>.azurewebsites.net
   ```

### Full Documentation:
- **Quick Start**: [docs/QUICK_START.md](docs/QUICK_START.md)
- **Main README**: [README.md](README.md)
- **Parameters Guide**: [docs/PARAMETERS.md](docs/PARAMETERS.md)

---

## 📋 Prerequisites

### You Need:
1. ✅ Azure subscription with Contributor access
2. ✅ Azure CLI installed
3. ✅ **Pre-created Azure services**:
   - Azure OpenAI (with GPT-4 model)
   - Azure AI Foundry project
   - Microsoft Fabric workspace (with agents)
   - Power BI workspace (with service principal)

### Get Configuration Values:
- Azure OpenAI: Endpoint URL + API Key
- AI Foundry: Project endpoint
- Fabric: Workspace ID + 6 Agent IDs
- Power BI: Workspace ID, Report ID, Service Principal credentials
- SQL: Azure AD admin email + Object ID

---

## 🔧 Customization Options

### Environment-Specific Deployments:

**Development** (~$35/month):
```bicep
param environment = 'dev'
param appServicePlanSku = 'B1'
param sqlDatabaseSku = 'Basic'
param enableKeyVault = false
```

**Production** (~$276/month):
```bicep
param environment = 'prod'
param appServicePlanSku = 'P1v2'
param sqlDatabaseSku = 'S2'
param enableKeyVault = true
param enableApplicationInsights = true
```

### Optional Features:
- **Key Vault**: `enableKeyVault = true` (recommended for prod)
- **Container Registry**: `enableContainerRegistry = true` (if using Docker)
- **Application Insights**: `enableApplicationInsights = true` (recommended)
- **Authentication**: `enableAuthentication = true` (JWT + RLS)

---

## 📦 What's Included

### Bicep Templates:
- ✅ **Main orchestration template** with all parameters
- ✅ **6 modular templates** for each Azure service
- ✅ **Parameters file** with comprehensive documentation
- ✅ **Role-based access control** (RBAC) configuration
- ✅ **Managed identity** setup for secure access

### Deployment Scripts:
- ✅ **PowerShell script** with progress tracking
- ✅ **Pre-flight checks** (Azure CLI, login status)
- ✅ **Automated deployment** (infrastructure + code)
- ✅ **Error handling** and rollback support
- ✅ **Deployment outputs** (URLs, resource names)

### Documentation:
- ✅ **Main README** (architecture, prerequisites, deployment)
- ✅ **Quick Start guide** (15-minute deployment)
- ✅ **Parameters reference** (all 50+ parameters documented)
- ✅ **Troubleshooting guide** (common issues + solutions)
- ✅ **Cost estimation** (dev vs prod pricing)

---

## 🎯 Use Cases

This template is perfect for:

1. **Reusable Deployments**: Deploy the same app to multiple Azure subscriptions
2. **Environment Management**: Separate dev/staging/prod environments
3. **Team Collaboration**: Share deployment templates across teams
4. **CI/CD Integration**: Automate deployments in pipelines
5. **Customer Deployments**: Package for customer self-deployment
6. **Training & Demos**: Quick environment setup for workshops

---

## 🔐 Security Considerations

### What's Secure:
- ✅ Secrets stored in Azure Key Vault (optional)
- ✅ Managed identities for Azure resource access
- ✅ Azure AD authentication for SQL Database
- ✅ HTTPS-only with minimum TLS 1.2
- ✅ JWT authentication with secure tokens
- ✅ Row-Level Security (RLS) in SQL

### What You Need to Secure:
- ⚠️ **Never commit** `main.parameters.bicepparam` with real secrets
- ⚠️ **Change default** admin password after deployment
- ⚠️ **Rotate secrets** regularly in Key Vault
- ⚠️ **Review** Azure AD permissions and access
- ⚠️ **Monitor** Application Insights for security events

---

## 📊 Monitoring & Operations

### After Deployment:
- **View Logs**: `az webapp log tail --name <app> -g <rg>`
- **Live Metrics**: Azure Portal → Application Insights → Live Metrics
- **Resource Health**: Azure Portal → Resource Health
- **Cost Analysis**: Azure Portal → Cost Management + Billing

### Ongoing Maintenance:
- Update application settings via Azure Portal or CLI
- Monitor Application Insights for errors and performance
- Review and rotate secrets in Key Vault
- Scale App Service Plan based on usage
- Backup SQL Database regularly

---

## 🤝 Contributing

To improve this template:

1. **Test** the deployment in your environment
2. **Report issues** or suggest improvements
3. **Add examples** for common scenarios
4. **Update documentation** with lessons learned
5. **Share** with the community

---

## 📞 Support & Help

- 📖 **Documentation**: Start with [README.md](README.md)
- 🚀 **Quick Start**: See [docs/QUICK_START.md](docs/QUICK_START.md)
- 📋 **Parameters**: Reference [docs/PARAMETERS.md](docs/PARAMETERS.md)
- 🐛 **Troubleshooting**: Check README troubleshooting section
- 💡 **Best Practices**: Review Azure documentation

---

## 🎓 Learning Resources

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/azure/ai-services/agents/)
- [Azure App Service Best Practices](https://learn.microsoft.com/azure/app-service/app-service-best-practices)
- [Bicep Language Reference](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure Security Best Practices](https://learn.microsoft.com/azure/security/)

---

## ✅ Next Steps

1. **Review** the [README.md](README.md) for complete documentation
2. **Configure** parameters in `bicep/main.bicepparam`
3. **Deploy** using `scripts/deploy.ps1`
4. **Test** your deployed application
5. **Monitor** using Application Insights
6. **Customize** for your specific needs

---

## 🎉 Ready to Deploy?

```powershell
# 1. Edit parameters
cd bicep
notepad main.bicepparam

# 2. Run deployment
cd ../scripts
./deploy.ps1 -ResourceGroupName "rg-myagents" -Location "eastus2"

# 3. Access your app
# https://<your-app-name>.azurewebsites.net
```

---

**Template Version**: 1.0  
**Last Updated**: 2024  
**Compatibility**: Azure CLI 2.50+, PowerShell 7.0+  
**Target Platform**: Azure App Service (Linux), Python 3.11  

---

**Made with ❤️ for the Microsoft Agent Framework community**
