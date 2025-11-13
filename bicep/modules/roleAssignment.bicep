// Role Assignment Module
// Assigns RBAC roles to managed identities

targetScope = 'resourceGroup'

@description('Principal ID (managed identity) to assign the role to')
param principalId string

@description('Role definition ID (GUID of the built-in or custom role)')
param roleDefinitionId string

@description('Target resource ID to assign the role on')
param targetResourceId string

@description('Principal type')
@allowed([
  'ServicePrincipal'
  'User'
  'Group'
])
param principalType string = 'ServicePrincipal'

// ========================================
// Resources
// ========================================

// Note: Role assignments for SQL are handled differently (via SQL commands)
// This is a placeholder for other Azure resources like Key Vault

// Skip if roleDefinitionId is the placeholder
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (roleDefinitionId != '00000000-0000-0000-0000-000000000000') {
  name: guid(principalId, roleDefinitionId, targetResourceId)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: principalId
    principalType: principalType
  }
}

// ========================================
// Outputs
// ========================================

@description('Role assignment resource ID')
output resourceId string = roleDefinitionId != '00000000-0000-0000-0000-000000000000' ? roleAssignment.id : ''
