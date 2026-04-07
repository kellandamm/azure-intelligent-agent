# Dataflows

## Supported flows

### Base SQL analytics

`Operational data -> Azure SQL -> reporting views/tables -> app analytics / embedded reporting`

### Fabric medallion analytics

`Source systems or Azure SQL -> Bronze -> Silver -> Gold -> semantic model -> reports / app analytics / Data Agent`

### Direct Lake reporting

`Gold Delta-backed Fabric data -> Direct Lake semantic model -> reports / app analytics`

### RTI event flow

`Azure SQL Database CDC or other source -> Eventstream -> Eventhouse / Activator / dashboard`

### Conversational analytics flow

`Curated Gold data -> Fabric Data Agent -> Foundry connection -> Foundry agent -> app chat`

### Governance overlay

`SQL / Fabric / supported sources -> Purview catalog and scans -> lineage / governance experiences`
