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

@description('Azure AD admin login name (UPN or display name, e.g. admin@contoso.com)')
param azureAdAdminLogin string = ''

@description('''Azure AD admin Object ID - MUST be a valid GUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx).
Get it with: az ad user show --id <UPN> --query id -o tsv
Leave empty to skip inline AD admin configuration.
WARNING: An invalid value (placeholder, email, empty path segment) causes ARM error
InvalidResourceIdSegment on parameters.properties.administrators.sid.''')
@maxLength(36)
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

@description('Enable SQL Vulnerability Assessment (Express configuration, no storage account needed). Recommended by MCSB (SecurityCenterBuiltIn).')
param enableVulnerabilityAssessment bool = false

@description('Minimum TLS version')
@allowed([
  '1.0'
  '1.1'
  '1.2'
])
param minimalTlsVersion string = '1.2'

@description('Public network access for SQL server. Set Disabled for MCAPS compliance — connectivity must go through a private endpoint.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string = 'Disabled'

@description('Restrict outbound network access for SQL server. Set Enabled for MCAPS compliance — prevents SQL from making arbitrary outbound connections outside allowed resources.')
@allowed([
  'Enabled'
  'Disabled'
])
param restrictOutboundNetworkAccess string = 'Enabled'

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
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: restrictOutboundNetworkAccess
    // Inline administrators block — REQUIRED by MCAPS deny policy:
    // AzureSQL_WithoutAzureADOnlyAuthentication_Deny (SFI-ID4.2.2 SQL DB - Safe Secrets Standard).
    //
    // The policy evaluates properties.administrators.azureADOnlyAuthentication on the
    // Microsoft.Sql/servers resource itself at ARM validation time, BEFORE any child
    // resources (/administrators, /azureADOnlyAuthentications) are deployed. Using a
    // separate child resource means the server-level property is absent during validation
    // and the deny policy fires. Setting it inline here ensures the check is satisfied.
    administrators: (!empty(azureAdAdminLogin) && !empty(azureAdAdminSid)) ? {
      administratorType: 'ActiveDirectory'
      login: azureAdAdminLogin
      sid: azureAdAdminSid
      tenantId: subscription().tenantId
      azureADOnlyAuthentication: azureADOnlyAuthentication
    } : null
  }
}

// Allow Azure services firewall rule — only relevant when public network access is Enabled.
// When publicNetworkAccess is Disabled, SQL is reachable only via private endpoint and
// this rule has no effect; omitting it reduces attack surface and avoids policy flags.
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = if (publicNetworkAccess == 'Enabled') {
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

// SQL Vulnerability Assessment - Express configuration (no storage account required)
// Recommended by MCSB (SecurityCenterBuiltIn): SQL servers should have vulnerability assessment enabled.
resource sqlVulnerabilityAssessment 'Microsoft.Sql/servers/sqlVulnerabilityAssessments@2022-11-01-preview' = if (enableVulnerabilityAssessment) {
  parent: sqlServer
  name: 'default'
  properties: {
    state: 'Enabled'
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
