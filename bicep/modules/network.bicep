// Network Module
// Deploys a VNet with two subnets:
//   - appservice-subnet  : delegated to Microsoft.Web/serverFarms for App Service outbound VNet integration
//   - private-endpoint-subnet : used for private endpoints (SQL, Key Vault, etc.)
//
// Required for MCAPS compliance when SQL Server public network access is disabled.

targetScope = 'resourceGroup'

@description('Virtual network name')
param vnetName string

@description('Location')
param location string

@description('Resource tags')
param tags object = {}

@description('VNet address space')
param vnetAddressPrefix string = '10.100.0.0/16'

@description('App Service outbound integration subnet prefix (min /28)')
param appServiceSubnetPrefix string = '10.100.1.0/24'

@description('Private endpoint subnet prefix (min /28)')
param privateEndpointSubnetPrefix string = '10.100.2.0/24'

// ========================================
// Resources
// ========================================

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [vnetAddressPrefix]
    }
    subnets: [
      {
        // Delegated subnet used by App Service regional VNet integration
        name: 'appservice-subnet'
        properties: {
          addressPrefix: appServiceSubnetPrefix
          delegations: [
            {
              name: 'webapp-delegation'
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ]
        }
      }
      {
        // Subnet used by private endpoints — network policies must be disabled on this subnet
        name: 'private-endpoint-subnet'
        properties: {
          addressPrefix: privateEndpointSubnetPrefix
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// ========================================
// Outputs
// ========================================

@description('VNet resource ID')
output vnetId string = vnet.id

@description('VNet name')
output vnetName string = vnet.name

@description('App Service integration subnet resource ID')
output appServiceSubnetId string = vnet.properties.subnets[0].id

@description('Private endpoint subnet resource ID')
output privateEndpointSubnetId string = vnet.properties.subnets[1].id
