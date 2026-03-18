// SQL Private Endpoint Module
// Provisions a private endpoint targeting an Azure SQL Server, a private DNS zone
// (privatelink.database.windows.net), a VNet link, and a DNS zone group so the SQL
// server FQDN resolves to a private IP inside the VNet.
//
// Required when SQL Server publicNetworkAccess is 'Disabled'.

targetScope = 'resourceGroup'

@description('Base name for private endpoint and related resources')
param privateEndpointName string

@description('SQL Server resource ID')
param sqlServerResourceId string

@description('Resource ID of the private endpoint subnet')
param subnetId string

@description('Resource ID of the VNet for DNS zone link')
param vnetId string

@description('Location')
param location string

@description('Resource tags')
param tags object = {}

// ========================================
// Resources
// ========================================

// Private DNS zone that resolves *.database.windows.net to private IPs inside the VNet
// zone name uses environment() so it works in all Azure clouds (public, gov, China)
var sqlPrivateDnsZoneName = 'privatelink${environment().suffixes.sqlServerHostname}'

resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: sqlPrivateDnsZoneName
  location: 'global'
  tags: tags
}

// Link the DNS zone to the VNet so name resolution works from within the VNet
resource privateDnsZoneVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZone
  name: '${privateEndpointName}-vnet-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// Private endpoint — creates a NIC with a private IP in the subnet pointing at the SQL server
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = {
  name: privateEndpointName
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: privateEndpointName
        properties: {
          privateLinkServiceId: sqlServerResourceId
          groupIds: ['sqlServer']
        }
      }
    ]
  }
}

// DNS zone group — automatically registers the private endpoint's IP in the private DNS zone
resource privateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'sql-privatelink'
        properties: {
          privateDnsZoneId: privateDnsZone.id
        }
      }
    ]
  }
}

// ========================================
// Outputs
// ========================================

@description('Private endpoint resource ID')
output privateEndpointId string = privateEndpoint.id

@description('Private DNS zone resource ID')
output privateDnsZoneId string = privateDnsZone.id
