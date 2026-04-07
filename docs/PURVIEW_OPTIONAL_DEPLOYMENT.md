# Purview optional deployment

## Scope

This doc describes Microsoft Purview as an optional governance add-on for the solution. Purview should complement both SQL-only and Fabric-enabled deployments, but it should not be required for the base application rollout.

## Where Purview fits

Use Purview when the customer needs:

- centralized catalog and discovery,
- lineage visibility,
- sensitivity labeling and protection alignment,
- governance visibility across the wider data estate.

Purview works with Microsoft Fabric so Fabric items can appear in Microsoft Purview experiences, and Fabric also includes a Microsoft Purview hub for governance visibility inside Fabric.

## Supported deployment positions

- Base app with no Purview.
- SQL-first app with Purview governance.
- Fabric analytics with no Purview.
- Fabric analytics with Purview governance.

## Bicep position

Purview should be deployed through the optional Bicep module and parameters already prepared in infrastructure changes:

- `enablePurview`
- `purviewAccountName`

Provisioning the account is only the first step.

## Post-deployment tasks

After the Purview account is created, complete these tasks:

1. Create or organize collections.
2. Register data sources.
3. Create credentials where needed.
4. Configure scans.
5. Validate lineage and metadata visibility.
6. Align access roles and governance ownership.
7. Validate networking and tenant prerequisites.

## Fabric-specific setup

If Fabric is enabled, add these tasks:

1. Register the Fabric tenant as a source in Microsoft Purview.
2. Enable Fabric metadata scanning and required admin API settings.
3. Wait for settings propagation before testing scans.
4. Create a Fabric scan in Purview.
5. Validate that Fabric items appear in catalog and lineage experiences.

## SQL-first setup

If Fabric is not enabled, Purview can still be valuable for Azure SQL governance.

Recommended SQL-first tasks:

- register Azure SQL as a data source,
- configure scans,
- validate catalog entries,
- validate lineage where applicable,
- align roles and glossary/governance practices if used.

## Networking and credentials

Networking and credential choices vary by same-tenant vs cross-tenant setup and by public vs private network patterns. Validate managed identity, Key Vault access, tenant alignment, and any required integration runtime settings before blaming scan failures on Purview itself.

## Repo merge notes

- Keep Purview optional in README, QUICK_START, architecture, and deployment docs.
- Do not imply that Purview is automatically operational immediately after Bicep deployment.
- Distinguish clearly between provisioning and governance onboarding.
