// ============================================================================
// Resources Bicep - Reuse Existing Infrastructure
// Only creates: Container Apps (main + MCP), Managed Identity
// ============================================================================

@description('Location for all resources')
param location string

@description('Environment name')
param environmentName string

@description('Resource token for unique naming')
param resourceToken string

// Existing resource names
param existingContainerEnvName string
param existingAcrName string
param existingLogAnalyticsName string
param existingAppInsightsName string

// Configuration parameters
param projectEndpoint string
@secure()
param projectConnectionString string
param fabricOrchestratorAgentId string
param fabricSalesAgentId string
param fabricRealtimeAgentId string
param fabricAnalyticsAgentId string
param fabricFinancialAgentId string
param fabricSupportAgentId string
param fabricOperationsAgentId string
param fabricCustomerSuccessAgentId string
param fabricOperationsExcellenceAgentId string
param fabricWorkspaceId string
param powerbiTenantId string
param powerbiWorkspaceId string
param enableSqlDatabase bool
@secure()
param sqlConnectionString string
param mainContainerImage string
param mcpContainerImage string
param logLevel string

// ============================================================================
// Reference Existing Resources
// ============================================================================

resource existingContainerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: existingAcrName
}

resource existingContainerEnv 'Microsoft.App/managedEnvironments@2023-05-01' existing = {
  name: existingContainerEnvName
}

resource existingLogAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: existingLogAnalyticsName
}

resource existingAppInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: existingAppInsightsName
}

// ============================================================================
// User-Assigned Managed Identity (for Container Apps)
// ============================================================================

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'azid-foundry-mcp-${resourceToken}'
  location: location
}

// ============================================================================
// ACR Pull Role Assignment
// ============================================================================

resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(existingContainerRegistry.id, managedIdentity.id, 'acrpull-foundry-mcp')
  scope: existingContainerRegistry
  properties: {
    principalId: managedIdentity.properties.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalType: 'ServicePrincipal'
  }
}

// ============================================================================
// MCP Server Container App (Internal Only)
// ============================================================================

resource mcpServerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'mcp-server-${environmentName}'
  location: location
  dependsOn: [acrPullRole]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: existingContainerEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: false // Internal only
        targetPort: 3000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: '${existingAcrName}.azurecr.io'
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'mcp-server'
          image: mcpContainerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'LOG_LEVEL'
              value: logLevel
            }
            {
              name: 'PORT'
              value: '3000'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '10'
              }
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// Main Application Container App (External)
// ============================================================================

resource mainApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'main-app-${environmentName}'
  location: location
  dependsOn: [acrPullRole, mcpServerApp]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: existingContainerEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true // Publicly accessible
        targetPort: 8080
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: '${existingAcrName}.azurecr.io'
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'main-app'
          image: mainContainerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            // Azure AI Foundry
            {
              name: 'PROJECT_ENDPOINT'
              value: projectEndpoint
            }
            {
              name: 'PROJECT_CONNECTION_STRING'
              secretRef: 'project-connection-string'
            }
            // Agent IDs
            {
              name: 'FABRIC_ORCHESTRATOR_AGENT_ID'
              value: fabricOrchestratorAgentId
            }
            {
              name: 'FABRIC_SALES_AGENT_ID'
              value: fabricSalesAgentId
            }
            {
              name: 'FABRIC_REALTIME_AGENT_ID'
              value: fabricRealtimeAgentId
            }
            {
              name: 'FABRIC_ANALYTICS_AGENT_ID'
              value: fabricAnalyticsAgentId
            }
            {
              name: 'FABRIC_FINANCIAL_AGENT_ID'
              value: fabricFinancialAgentId
            }
            {
              name: 'FABRIC_SUPPORT_AGENT_ID'
              value: fabricSupportAgentId
            }
            {
              name: 'FABRIC_OPERATIONS_AGENT_ID'
              value: fabricOperationsAgentId
            }
            {
              name: 'FABRIC_CUSTOMER_SUCCESS_AGENT_ID'
              value: fabricCustomerSuccessAgentId
            }
            {
              name: 'FABRIC_OPERATIONS_EXCELLENCE_AGENT_ID'
              value: fabricOperationsExcellenceAgentId
            }
            // Fabric & Power BI
            {
              name: 'FABRIC_WORKSPACE_ID'
              value: fabricWorkspaceId
            }
            {
              name: 'POWERBI_TENANT_ID'
              value: powerbiTenantId
            }
            {
              name: 'POWERBI_WORKSPACE_ID'
              value: powerbiWorkspaceId
            }
            // MCP Server Configuration
            {
              name: 'MCP_SERVER_HOST'
              value: mcpServerApp.properties.configuration.ingress.fqdn
            }
            {
              name: 'MCP_SERVER_PORT'
              value: '443' // HTTPS on Container Apps
            }
            {
              name: 'ENABLE_MCP'
              value: 'true'
            }
            // SQL Database (if enabled)
            {
              name: 'ENABLE_SQL_DATABASE'
              value: string(enableSqlDatabase)
            }
            {
              name: 'SQL_CONNECTION_STRING'
              secretRef: 'sql-connection-string'
            }
            // Monitoring
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: existingAppInsights.properties.ConnectionString
            }
            {
              name: 'ENABLE_TRACING'
              value: 'true'
            }
            {
              name: 'LOG_LEVEL'
              value: logLevel
            }
            {
              name: 'APP_PORT'
              value: '8080'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '50'
              }
            }
          }
        ]
      }
    }
  }
}

// ============================================================================
// Secrets for Main App
// ============================================================================

resource mainAppSecrets 'Microsoft.App/containerApps/secrets@2023-05-01' = {
  name: 'project-connection-string'
  parent: mainApp
  properties: {
    value: projectConnectionString
  }
}

resource sqlConnectionStringSecret 'Microsoft.App/containerApps/secrets@2023-05-01' = if (enableSqlDatabase) {
  name: 'sql-connection-string'
  parent: mainApp
  properties: {
    value: sqlConnectionString
  }
}

// ============================================================================
// Outputs
// ============================================================================

output mainAppUrl string = 'https://${mainApp.properties.configuration.ingress.fqdn}'
output mcpServerUrl string = 'https://${mcpServerApp.properties.configuration.ingress.fqdn}'
output managedIdentityId string = managedIdentity.id
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output containerEnvironmentId string = existingContainerEnv.id
output applicationInsightsConnectionString string = existingAppInsights.properties.ConnectionString
