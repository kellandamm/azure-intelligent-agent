# Solution architecture design update

## Architecture

The target architecture should now be described as a SQL-first base solution with optional Fabric, Direct Lake, RTI, Foundry/Data Agent, and Purview extensions. This creates a progressive maturity path instead of a single mandatory target state.

## Core design principles

- SQL remains the baseline live analytics source when Fabric is not enabled.
- Fabric remains optional, not mandatory.
- Direct Lake is the preferred semantic model path when Gold data is curated in Fabric.
- RTI is optional and should be used for event-driven and operational scenarios.
- Purview is optional and should be used when governance maturity is needed.

## Logical architecture

1. Application users interact with app experiences, dashboards, and optional chat features.
2. The app reads analytics from either Azure SQL or Fabric Gold depending on runtime configuration.
3. Fabric transforms data through Bronze, Silver, and Gold when enabled.
4. Direct Lake semantic models sit on top of Fabric Gold for reporting performance.
5. RTI consumes event streams for near-real-time monitoring and alerts when enabled.
6. Purview overlays governance, catalog, classification, and lineage when enabled.

## Dataflow patterns

### Dataflow 1: Base SQL analytics

`Operational app data -> Azure SQL operational tables -> SQL reporting views/tables -> app analytics / embedded reporting`

### Dataflow 2: Fabric medallion analytics

`Source systems or Azure SQL -> Bronze Lakehouse -> Silver Lakehouse -> Gold Lakehouse/Warehouse -> Direct Lake semantic model -> reports / app analytics / Data Agent`

### Dataflow 3: RTI operational flow

`Operational events -> Eventstream -> Eventhouse / real-time dashboard -> Activator rules -> operational alerting or action`

### Dataflow 4: Foundry conversational flow

`Curated Gold tables -> Fabric Data Agent -> Foundry Fabric connection -> Foundry agent -> app chat experience`

### Dataflow 5: Governance overlay

`SQL / Fabric / other supported data sources -> Purview catalog and scans -> lineage / classification / governance experiences`

## Recommended deployment profiles

- Base: SQL-first app only.
- Analytics: Base + Fabric + Direct Lake.
- Operations: Analytics + RTI.
- Governed analytics: Analytics + Purview.
- Full platform: Analytics + RTI + Foundry/Data Agent + Purview.
