targetScope = 'resourceGroup'

@description('Deployment location')
param location string = resourceGroup().location

@description('Enable Microsoft Fabric add-on')
param enableFabric bool = false

@description('Analytics mode for the application')
@allowed([
  'sql'
  'fabric'
  'auto'
])
param analyticsMode string = 'sql'

@description('Enable Foundry-backed Fabric Data Agent path')
param useFoundryAgents bool = false

@description('Foundry project endpoint')
param foundryProjectEndpoint string = ''

@description('Fabric project connection name')
param fabricProjectConnectionName string = ''

@description('Foundry model deployment name')
param foundryModelDeploymentName string = ''

@description('Enable Fabric Real-Time Intelligence add-on planning')
param enableFabricRti bool = false

@description('Enable Direct Lake semantic model guidance')
param enableDirectLake bool = true

@description('Enable Microsoft Purview governance add-on')
param enablePurview bool = false

@description('Microsoft Purview account name')
param purviewAccountName string = ''

var tags = {
  solution: 'sql-fabric-rti-purview-reference'
  analyticsMode: analyticsMode
}

module fabricRti './modules/fabric-rti-placeholder.bicep' = if (enableFabric && enableFabricRti) {
  name: 'fabric-rti-placeholder'
  params: {
    enableFabricRti: enableFabricRti
    enableDirectLake: enableDirectLake
  }
}

module purview './modules/purview.bicep' = if (enablePurview) {
  name: 'purview-deploy'
  params: {
    location: location
    purviewAccountName: purviewAccountName
    tags: tags
  }
}

output deploymentProfile object = {
  enableFabric: enableFabric
  analyticsMode: analyticsMode
  useFoundryAgents: useFoundryAgents
  foundryProjectEndpoint: foundryProjectEndpoint
  fabricProjectConnectionName: fabricProjectConnectionName
  foundryModelDeploymentName: foundryModelDeploymentName
  enableFabricRti: enableFabricRti
  enableDirectLake: enableDirectLake
  enablePurview: enablePurview
  purviewAccountName: purviewAccountName
}
