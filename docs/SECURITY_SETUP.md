# Security Setup

This covers the two SQL security schemas that must be deployed once the database is up, and how the application enforces per-user data access at runtime.

---

## Overview

Security is split across two SQL files and a Python middleware layer:

| Component | File | Purpose |
|-----------|------|---------|
| Auth schema | `app/Fabric/auth_schema.sql` | Users, Roles, Permissions tables + stored procs |
| RLS infrastructure | `app/Fabric/rls_security_policies.sql` | Security schema, session context, predicate functions |
| Runtime enforcement | `app/app/rls_middleware.py` | Sets/clears SQL session context per request |

---

## Step 1 — Deploy the auth schema

Run `app/Fabric/auth_schema.sql` in Azure Portal → SQL Database → Query Editor (authenticate with your Azure AD account).

This creates:
- `dbo.Users` — application user accounts with bcrypt password hashes, lockout tracking
- `dbo.Roles` — 5 default roles (see table below)
- `dbo.Permissions` — 17 permissions across resources
- `dbo.UserRoles` / `dbo.RolePermissions` — junction tables
- Stored procs: `sp_GetUserByUsername`, `sp_UpdateLastLogin`, `sp_RecordFailedLogin`

### Default roles and permissions

| Role | Chat | Admin | Analytics | Fabric | Power BI |
|------|------|-------|-----------|--------|----------|
| SuperAdmin | Full | Full | Full | Full | Full |
| Admin | Full | Full (no delete) | Full | Full | View |
| PowerUser | Full | — | Full | Full | Full |
| User | Send/Read | — | View | View | View |
| ReadOnly | Read only | — | View | View | View |

> The admin user is **not** seeded by this script. Create it via the Python API or see [CREATE_ADMIN_USER.md](../CREATE_ADMIN_USER.md).

---

## Step 2 — Deploy RLS infrastructure

Run `app/Fabric/rls_security_policies.sql` in the Query Editor **after** `auth_schema.sql`.

This creates:
- `Security` schema
- Session context functions (`fn_GetCurrentUserId`, `fn_GetCurrentUserRoles`, `fn_IsAdmin`, etc.)
- RLS predicate functions for sales/customer/employee filtering
- Supporting tables:
  - `Security.UserTerritories` — maps users to regions/territories
  - `Security.UserCustomerAssignments` — maps users to specific customers
  - `Security.OrganizationHierarchy` — manager → direct report relationships
  - `Security.DataAccessLog` — audit trail for all data access events
- Stored procs: `Security.usp_SetUserContext`, `Security.sp_ClearUserContext`, `Security.usp_LogDataAccess`

> **Note:** The actual SQL security policies (filter predicates on tables) are commented out in Step 6 of the script. The infrastructure is in place but enforcement is not yet active on the demo data tables — see [Activating RLS policies](#activating-rls-policies) below.

---

## Step 3 — Assign users to territories

After creating users via the admin UI, assign territory access in the Query Editor:

```sql
-- Assign a user to a territory
INSERT INTO Security.UserTerritories (UserID, Territory, Region)
VALUES
    (2, 'West',    'USA-West'),
    (3, 'East',    'USA-East'),
    (4, 'Central', 'USA-Central');

-- Assign a user to specific customers
INSERT INTO Security.UserCustomerAssignments (UserID, CustomerID)
VALUES (2, 101), (2, 102), (2, 103);
```

Users without territory assignments will only see records where `Region IS NULL` unless they have Admin/SuperAdmin role (which bypasses all filters).

---

## How runtime enforcement works

On every authenticated request, `rls_middleware.py`:

1. **Sets session context** — calls `Security.usp_SetUserContext` with the user's ID, roles, and region. SQL Server RLS predicate functions read these values via `SESSION_CONTEXT()`.
2. **Request is processed** — any query hitting a table with an active RLS policy is automatically filtered.
3. **Clears session context** — calls `Security.sp_ClearUserContext` after the response. This is critical to prevent context leaking across pooled connections.

Admin and SuperAdmin roles bypass all RLS filters — their queries always return full data.

### Chat / agent query rewriting

For non-admin users, `ChatAgentRLSHelper` in `rls_middleware.py` appends territory/customer scope to natural language queries before they reach the AI agent. This is a secondary safety layer — primary enforcement happens at the SQL level.

### Power BI RLS role mapping

| App role | Power BI dataset role |
|----------|-----------------------|
| SuperAdmin / Admin | `AllData` |
| PowerUser / Manager | `ManagerView` |
| User / ReadOnly | `UserView` |

These are used when generating embedded Power BI tokens via `get_powerbi_effective_identity()`.

---

## Activating RLS policies

The predicate functions exist but are not applied to tables until you uncomment Step 6 in `rls_security_policies.sql` and run it.

Before activating, your tables need a `Region` or `CustomerID` column that the predicates can filter on. The demo data tables (`dbo.Orders`, `dbo.Customers`) already have `CustomerID` — to activate customer-level filtering:

```sql
-- Apply RLS to Customers table
CREATE SECURITY POLICY Security.CustomerSecurityPolicy
ADD FILTER PREDICATE Security.fn_CustomerAccessPredicate(CustomerID) ON dbo.Customers
WITH (STATE = ON);

-- Apply RLS to Orders table
CREATE SECURITY POLICY Security.OrderSecurityPolicy
ADD FILTER PREDICATE Security.fn_CustomerAccessPredicate(CustomerID) ON dbo.Orders
WITH (STATE = ON);
```

Verify active policies:
```sql
SELECT * FROM sys.security_policies;
SELECT * FROM sys.security_predicates;
```

Disable a policy without dropping it:
```sql
ALTER SECURITY POLICY Security.CustomerSecurityPolicy WITH (STATE = OFF);
```

---

## Entra ID / OBO Authentication (additive)

The SQL auth system above is the primary mechanism. An additional **"Sign in with Microsoft"** path is available alongside it and does not replace or modify the SQL auth flow.

When enabled (`ENABLE_OBO_AUTH=true`), users can sign in with their Entra account. This:
- Issues the same app JWT as SQL login (all existing middleware and RLS work identically)
- Additionally stores an `entra_token` httpOnly cookie used exclusively for OBO token exchange
- Enables the app to call Azure AI Foundry agents on behalf of the signed-in user, which is required for Foundry → Fabric Data Agent calls

**SQL users are completely unaffected** — they continue to log in as before.

The `entra_token` cookie is:
- **HTTP-only** — JavaScript cannot read it
- **Secure** — HTTPS only
- **Separate** from the app JWT — stored in its own cookie, never in localStorage

For full setup instructions see [OBO_AUTH_SETUP.md](OBO_AUTH_SETUP.md).

---

## Verify the setup

```sql
-- Confirm all security tables exist
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA IN ('dbo', 'Security')
ORDER BY TABLE_SCHEMA, TABLE_NAME;

-- Test session context (run as any user)
EXEC Security.usp_SetUserContext
    @UserId = 1,
    @Username = 'testuser',
    @UserEmail = 'test@example.com',
    @UserRoles = 'Admin',
    @UserRegion = 'West';

SELECT
    CAST(SESSION_CONTEXT(N'UserId')    AS INT)          AS UserId,
    CAST(SESSION_CONTEXT(N'UserRoles') AS NVARCHAR(MAX)) AS UserRoles,
    CAST(SESSION_CONTEXT(N'UserRegion')AS NVARCHAR(50))  AS UserRegion;

-- Clear context
EXEC Security.sp_ClearUserContext;

-- View audit log
SELECT TOP 20 * FROM Security.DataAccessLog ORDER BY Timestamp DESC;
```
