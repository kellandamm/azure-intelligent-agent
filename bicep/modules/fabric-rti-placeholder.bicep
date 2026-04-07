@description('Enable RTI profile')
param enableFabricRti bool

@description('Prefer Direct Lake semantic model mode')
param enableDirectLake bool

output fabricRtiEnabled bool = enableFabricRti
output directLakePreferred bool = enableDirectLake
