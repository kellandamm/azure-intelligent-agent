@description('Deployment location')
param location string

@description('Microsoft Purview account name')
param purviewAccountName string

@description('Optional resource tags')
param tags object = {}

resource purview 'Microsoft.Purview/accounts@2024-04-01-preview' = {
  name: purviewAccountName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'Standard'
    capacity: 4
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    managedResourcesPublicNetworkAccess: 'Enabled'
    managedEventHubState: 'Enabled'
    tenantEndpointState: 'Enabled'
  }
}

output purviewId string = purview.id
output purviewName string = purview.name
