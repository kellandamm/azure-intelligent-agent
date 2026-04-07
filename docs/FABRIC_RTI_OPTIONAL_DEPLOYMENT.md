# Fabric RTI optional deployment

## Scope

This doc describes the optional Microsoft Fabric Real-Time Intelligence path for the solution. RTI should be enabled only when the customer needs near-real-time operational monitoring, event-driven dashboards, or trigger-based actions.

## Recommended RTI components

- **Eventstream** for ingesting, transforming, and routing events.
- **Eventhouse** for querying and analyzing event data.
- **Activator** for no-code threshold and pattern-based alerting or actions.
- Optional real-time dashboards for operations visibility.

## Recommended event source path

For this solution, the clearest first RTI source path is:

`Azure SQL Database CDC -> Eventstream -> Eventhouse -> Activator / dashboard`

This is a strong fit because Eventstream supports Azure SQL Database CDC as a source, can route events to Eventhouse, and can also route to Activator destinations for alerting and automation.

## Alternative sources

Other valid source options include:

- Azure Event Hubs.
- Custom endpoint / custom app events.
- Fabric workspace item events.
- Fabric OneLake events.
- Fabric job events.

## Eventstream guidance

Use Eventstream as the main no-code intake and routing layer. Eventstream supports transformations such as Filter, Manage fields, Aggregate, Group by, Union, Expand, and Join, and can route the same stream to multiple destinations without interfering with each other.

## Eventhouse guidance

Use Eventhouse as the main operational analysis store for event data that needs KQL-style investigation, historical slicing, or operational dashboards.

## Activator guidance

Use Activator when the business wants actions, not just dashboards. Activator can monitor eventstreams or Power BI data and take actions such as email alerts, Teams notifications, Power Automate workflows, or other configured downstream actions when thresholds or patterns are detected.

Recommended first rules for this solution:

- Support-ticket surge alert.
- Order anomaly alert.
- KPI threshold breach alert.
- Customer health deterioration alert.

## Capacity guidance

Microsoft recommends using Fabric Eventstream with at least F4 capacity.

## Post-deployment setup steps

1. Create or identify the Fabric workspace for RTI.
2. Create the Eventstream item.
3. Add the first source connector, preferably Azure SQL Database CDC for the initial implementation.
4. Add one or more transformations if field cleanup or shaping is needed.
5. Add Eventhouse as a destination.
6. Add Activator as a destination for at least one alerting rule.
7. Add a real-time dashboard or downstream consumer if needed.
8. Validate end-to-end event arrival, routing, and alert triggering.

## Suggested smoke test

Use this first smoke test path:

1. Publish a known row-level change into the selected source table.
2. Confirm the event appears in Eventstream.
3. Confirm the routed record appears in Eventhouse.
4. Confirm the Activator rule fires when the threshold condition is met.
5. Confirm alert delivery or downstream action execution.

## Repo merge notes

- Create `docs/FABRIC_RTI_OPTIONAL_DEPLOYMENT.md` from this file.
- Keep RTI optional in all architecture and quick-start docs.
- Do not overstate provisioning automation in Bicep; keep infrastructure and workspace setup responsibilities separate.
