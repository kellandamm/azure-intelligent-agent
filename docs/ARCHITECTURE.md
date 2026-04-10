# Architecture

## Scope

The solution is a SQL-first application architecture with optional Microsoft Fabric analytics and optional enterprise add-ons.

## Main components

- Application layer.
- Azure SQL live analytics path.
- Optional Fabric medallion analytics path.
- Optional Direct Lake semantic model path.
- Optional Real-Time Intelligence path.
- Optional Fabric Data Agent plus Foundry path (requires OBO auth).
- Optional Purview governance overlay.

## Authentication model

The application supports two parallel login paths that coexist at the same time:

- **SQL login** — username/password stored in `dbo.Users` with bcrypt hashing. Issues an app JWT on success. Works for all features that do not require Fabric Data Agents.
- **Sign in with Microsoft (Entra)** — OAuth2 authorization code flow via MSAL. Issues the same app JWT (existing auth middleware unchanged) plus an `entra_token` cookie used as the OBO user assertion.

### On-Behalf-Of (OBO) flow — required for Fabric Data Agents

When a Foundry hosted agent calls a Fabric Data Agent tool, Fabric validates the caller's identity. An app-only managed identity is rejected. The OBO flow solves this:

```
User (Entra login)
  → entra_token cookie stored
  → Chat request → MSAL OBO exchange
  → Token scoped to https://ai.azure.com/.default
  → AIProjectClient with user identity
  → Foundry agent → Fabric Data Agent ✅
```

SQL-only users (no `entra_token`) continue to work for all non-Fabric-Data-Agent features unchanged.

See [OBO_AUTH_SETUP.md](OBO_AUTH_SETUP.md) for setup instructions.

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
- OBO auth is additive — SQL login users are unaffected by enabling it.
