# README update draft

## Architecture profiles

This solution uses a SQL-first default architecture with optional enterprise add-ons.

Supported profiles:

- **Base**: live analytics from Azure SQL.
- **Analytics**: Microsoft Fabric medallion analytics with Direct Lake reporting.
- **Operations**: Analytics profile plus Real-Time Intelligence.
- **Governed**: Analytics profile plus Microsoft Purview.
- **Full platform**: Analytics + RTI + Fabric Data Agent/Foundry + Purview.

## Key points

- SQL remains the default live analytics path.
- Microsoft Fabric is optional.
- Direct Lake is the preferred Fabric semantic model mode over curated Gold data.
- Real-Time Intelligence is optional for event-driven monitoring and actions.
- Fabric Data Agent plus Foundry is optional for conversational analytics.
- Purview is optional for governance.

## Deployment docs

See:

- `docs/CONSOLIDATED_DEPLOYMENT_AND_INTEGRATION_GUIDE.md`
- `docs/ARCHITECTURE.md`
- `docs/DATAFLOWS.md`
- `docs/FABRIC_DEPLOYMENT.md`
- `docs/FABRIC_RTI_OPTIONAL_DEPLOYMENT.md`
- `docs/FABRIC_DATA_AGENT_FOUNDRY_APP_SETUP.md`
- `docs/PURVIEW_OPTIONAL_DEPLOYMENT.md`
