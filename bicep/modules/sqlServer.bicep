// SQL Server & Database Module
// Deploys Azure SQL Server with database

targetScope = 'resourceGroup'

@description('SQL Server name (must be globally unique)')
param serverName string

@description('Location for SQL Server')
param location string

@description('Resource tags')
param tags object = {}

@description('SQL administrator login username')
param administratorLogin string = ''

@description('SQL administrator login password')
@secure()
param administratorLoginPassword string = ''

@description('Azure AD admin login name')
param azureAdAdminLogin string = ''

@description('Azure AD admin object ID (SID)')
param azureAdAdminSid string = ''

@description('Enable Azure AD-only authentication')
param azureADOnlyAuthentication bool = false

@description('Database name')
param databaseName string

@description('Database SKU (Basic, S0, S1, P1, etc.)')
param databaseSku string = 'Basic'

@description('Maximum database size in bytes')
param maxSizeBytes int = 2147483648 // 2GB

@description('Enable auditing')
param enableAudit bool = false

@description('Enable threat detection')
param enableThreatDetection bool = false

@description('Minimum TLS version')
@allowed([
  '1.0'
  '1.1'
  '1.2'
])
param minimalTlsVersion string = '1.2'

// ========================================
// Resources
// ========================================

resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: serverName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    administratorLogin: azureADOnlyAuthentication ? null : administratorLogin
    administratorLoginPassword: azureADOnlyAuthentication ? null : administratorLoginPassword
    minimalTlsVersion: minimalTlsVersion
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: 'Disabled'
  }
}

// Azure AD Administrator
resource sqlServerAzureAdAdmin 'Microsoft.Sql/servers/administrators@2023-05-01-preview' = if (!empty(azureAdAdminLogin) && !empty(azureAdAdminSid)) {
  parent: sqlServer
  name: 'ActiveDirectory'
  properties: {
    administratorType: 'ActiveDirectory'
    login: azureAdAdminLogin
    sid: azureAdAdminSid
    tenantId: subscription().tenantId
  }
}

// Azure AD-only authentication (separate resource)
resource azureAdOnlyAuth 'Microsoft.Sql/servers/azureADOnlyAuthentications@2023-05-01-preview' = if (azureADOnlyAuthentication && !empty(azureAdAdminLogin)) {
  parent: sqlServer
  name: 'Default'
  properties: {
    azureADOnlyAuthentication: true
  }
  dependsOn: [
    sqlServerAzureAdAdmin
  ]
}

// Allow Azure services firewall rule
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  parent: sqlServer
  name: 'AllowAllWindowsAzureIps'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// SQL Database
resource sqlDatabase 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: databaseName
  location: location
  tags: tags
  sku: {
    name: databaseSku
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: maxSizeBytes
    catalogCollation: 'SQL_Latin1_General_CP1_CI_AS'
    zoneRedundant: false
    readScale: 'Disabled'
  }
}

// Auditing settings (optional)
resource auditingSettings 'Microsoft.Sql/servers/auditingSettings@2023-05-01-preview' = if (enableAudit) {
  parent: sqlServer
  name: 'default'
  properties: {
    state: 'Enabled'
    isAzureMonitorTargetEnabled: true
    retentionDays: 90
  }
}

// Security alert policies (optional)
resource securityAlertPolicies 'Microsoft.Sql/servers/securityAlertPolicies@2023-05-01-preview' = if (enableThreatDetection) {
  parent: sqlServer
  name: 'Default'
  properties: {
    state: 'Enabled'
    emailAccountAdmins: true
    retentionDays: 90
  }
}

// ========================================
// Outputs
// ========================================

@description('SQL Server resource ID')
output resourceId string = sqlServer.id

@description('SQL Server name')
output serverName string = sqlServer.name

@description('SQL Server FQDN')
output fullyQualifiedDomainName string = sqlServer.properties.fullyQualifiedDomainName

@description('SQL Database resource ID')
output databaseResourceId string = sqlDatabase.id

@description('SQL Database name')
output databaseName string = sqlDatabase.name

@description('SQL Server system-assigned managed identity principal ID')
output managedIdentityPrincipalId string = sqlServer.identity.principalId
