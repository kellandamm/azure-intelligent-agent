# Architecture

## Scope

The solution is a SQL-first application architecture with optional Microsoft Fabric analytics and optional enterprise add-ons.

## Main components

- Application layer.
- Azure SQL live analytics path.
- Optional Fabric medallion analytics path.
- Optional Direct Lake semantic model path.
- Optional Real-Time Intelligence path.
- Optional Fabric Data Agent plus Foundry path.
- Optional Purview governance overlay.

## Deployment profiles

- Base.
- Analytics.
- Operations.
- Governed.
- Full platform.

## Design principles

- Keep SQL as the default live analytics path.
- Keep Fabric optional.
- Use Direct Lake as the preferred Fabric reporting mode over curated Gold data.
- Treat RTI, Foundry/Data Agent, and Purview as optional add-ons.
- Keep infrastructure provisioning separate from Fabric workspace configuration where needed.
