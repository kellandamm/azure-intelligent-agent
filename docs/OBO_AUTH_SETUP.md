# Entra ID / On-Behalf-Of (OBO) Authentication Setup

This guide explains how to enable **"Sign in with Microsoft"** and configure the
**On-Behalf-Of (OBO)** token flow so that the application can call Azure AI Foundry agents
on behalf of the signed-in user — which is required for Foundry hosted agents that use
**Microsoft Fabric Data Agents** as tools.

---

## Why OBO is needed

When a Foundry hosted agent (e.g. `SalesAssistant`) calls a Fabric Data Agent tool, Fabric
checks that the caller is an authorised user — not just an app identity. Without OBO:

```
App (managed identity) → Foundry → Fabric Data Agent → ❌ Authentication failed
```

With OBO:

```
User (Entra token) → App → OBO exchange → Foundry → Fabric Data Agent → ✅ Works
```

The OBO flow is **additive**: existing SQL username/password login continues to work
unchanged. Users who log in with their Microsoft account get the OBO capability;
SQL-only users do not call Fabric Data Agents on behalf of themselves.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| Azure App Service with Managed Identity | Already configured by Bicep — see [AZD_DEPLOYMENT_GUIDE.md](AZD_DEPLOYMENT_GUIDE.md) |
| Fabric workspace membership | App Service managed identity added as workspace member |
| Fabric capacity F64 or higher | Fabric Trial (FT1) cannot host Foundry-backed Data Agents |
| Azure AI Foundry project | With hosted agents deployed and the Sales-Agent connection using **Project Managed Identity** auth |

---

## Step 1 — Register an Entra Application

1. Go to [portal.azure.com](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → **New registration**

2. Fill in:
   - **Name**: `Contoso Sales App` (or your app name)
   - **Supported account types**: *Accounts in this organizational directory only*
   - **Redirect URI**: select **Web**, enter:
     ```
     https://<your-app-name>.azurewebsites.net/api/auth/entra/callback
     ```
     For local development also add:
     ```
     http://localhost:8000/api/auth/entra/callback
     ```

3. Click **Register**. Note the **Application (client) ID** and **Directory (tenant) ID** from the Overview page.

---

## Step 2 — Create a Client Secret

1. In your App Registration → **Certificates & secrets** → **Client secrets** → **New client secret**
2. Set a description (e.g. `obo-secret`) and expiry (12 months recommended)
3. Copy the **Value** immediately — it is only shown once

---

## Step 3 — Expose an API (required for OBO)

The OBO flow requires the app to have an exposed API scope so the Entra access token
issued during login has **this app as its audience** (not just Microsoft Graph).

1. In your App Registration → **Expose an API**
2. Click **Add** next to *Application ID URI* — accept the default `api://<client-id>`
3. Click **Add a scope**:
   - Scope name: `user_impersonation`
   - Who can consent: *Admins and users*
   - Admin consent display name: `Access Contoso Sales on behalf of user`
   - User consent display name: `Access Contoso Sales`
   - State: **Enabled**
4. Click **Add scope**

Your full scope will be: `api://<client-id>/user_impersonation`

---

## Step 4 — Grant API Permissions

The app needs delegated permissions to call Foundry and Fabric on behalf of the user.

1. In your App Registration → **API permissions** → **Add a permission**

2. Add the following delegated permissions:

   | API | Permission | Notes |
   |-----|-----------|-------|
   | **Azure Machine Learning Services** | `user_impersonation` | Required — this is the SP for the `https://ai.azure.com` audience used by the Foundry Conversations API |
   | **Microsoft Cognitive Services** | `user_impersonation` | Required for Cognitive Services / AIServices-kind Foundry resources |
   | **Power BI Service** | `Tenant.Read.All` | Lets the app read Fabric/Power BI as the user |

   > ⚠️ **Important naming note**: In the portal, **"Azure AI Services"** may not appear in search results. The correct SP name is **"Azure Machine Learning Services"** (audience `https://ai.azure.com`). If the portal search does not find it, add it via CLI (see below).

3. Click **Grant admin consent** for your organisation (requires Global Admin or Application Admin)

### Adding permissions via CLI (recommended — avoids portal search issues)

```powershell
$appId = "<your-app-client-id>"

# Add Azure Machine Learning Services (https://ai.azure.com audience)
az ad app permission add --id $appId `
  --api "18a66f5f-dbdf-4c17-9dd7-1634712a9cbe" `
  --api-permissions "1a7925b5-f871-417a-9b8b-303f9f29fa10=Scope"

# Add Microsoft Cognitive Services (cognitiveservices.azure.com)
az ad app permission add --id $appId `
  --api "7d312290-28c8-473c-a0ed-8e53749b6d6d" `
  --api-permissions "5f1e8914-a52b-429f-9324-91b92b81adaf=Scope"
```

### Granting admin consent via CLI (required — portal "Grant admin consent" button may not create the underlying grant)

```powershell
# Get the SP object ID for your app registration
$spObjectId = az ad sp show --id $appId --query "id" -o tsv

# Get SP object IDs for each resource
$mlSpId  = az ad sp show --id "18a66f5f-dbdf-4c17-9dd7-1634712a9cbe" --query "id" -o tsv
$cogSpId = az ad sp show --id "7d312290-28c8-473c-a0ed-8e53749b6d6d" --query "id" -o tsv

# Grant consent directly via Microsoft Graph (more reliable than az ad app permission admin-consent)
$grant1 = "{`"clientId`":`"$spObjectId`",`"consentType`":`"AllPrincipals`",`"resourceId`":`"$mlSpId`",`"scope`":`"user_impersonation`"}"
$grant2 = "{`"clientId`":`"$spObjectId`",`"consentType`":`"AllPrincipals`",`"resourceId`":`"$cogSpId`",`"scope`":`"user_impersonation`"}"

$grant1 | Out-File "$env:TEMP\grant1.json" -Encoding utf8 -NoNewline
$grant2 | Out-File "$env:TEMP\grant2.json" -Encoding utf8 -NoNewline

az rest --method POST --uri "https://graph.microsoft.com/v1.0/oauth2PermissionGrants" `
  --headers "Content-Type=application/json" --body "@$env:TEMP\grant1.json"

az rest --method POST --uri "https://graph.microsoft.com/v1.0/oauth2PermissionGrants" `
  --headers "Content-Type=application/json" --body "@$env:TEMP\grant2.json"
```

> **Why not just use `az ad app permission admin-consent`?**  
> That command grants consent for permissions already in the manifest, but it does not always create the `oauth2PermissionGrant` object that the OBO flow checks at runtime (`AADSTS65001`). The direct Graph API POST above creates that object explicitly.

---

## Step 5 — Configure App Service Settings

Go to **Azure Portal** → your App Service → **Configuration** → **Application settings**,
or use the Azure CLI:

```powershell
az webapp config appsettings set `
  --name <your-app-name> `
  --resource-group <your-resource-group> `
  --settings `
    ENABLE_OBO_AUTH="true" `
    ENTRA_CLIENT_ID="<Application (client) ID from Step 1>" `
    ENTRA_CLIENT_SECRET="<Secret value from Step 2>" `
    ENTRA_TENANT_ID="<Directory (tenant) ID from Step 1>" `
    ENTRA_REDIRECT_URI="https://<your-app-name>.azurewebsites.net/api/auth/entra/callback" `
    ENTRA_APP_SCOPE="api://<client-id>/user_impersonation"
```

> ⚠️ Never put secrets in `bicep/main.bicepparam` or commit them to source control.
> Use Key Vault references for production: see [SECURITY_SETUP.md](SECURITY_SETUP.md).

### Verify the settings were applied

```powershell
az webapp config appsettings list `
  --name <your-app-name> `
  --resource-group <your-resource-group> `
  --query "[?name=='ENABLE_OBO_AUTH' || name=='ENTRA_CLIENT_ID' || name=='ENTRA_TENANT_ID'].{name:name, value:value}" `
  -o table
```

---

## Step 6 — Restart the App

```powershell
az webapp restart --name <your-app-name> --resource-group <your-resource-group>
```

---

## Step 7 — Test the Login

1. Open your app URL and click **Sign in with Microsoft**
2. You will be redirected to Microsoft's login page
3. After authenticating, you are returned to the app home page
4. Try a chat message that routes to `SalesAssistant` — it should now succeed

---

## How it works (technical detail)

```
1. User clicks "Sign in with Microsoft"
   → GET /api/auth/entra/login
   → Redirects to https://login.microsoftonline.com/...

2. User authenticates with Entra (MFA etc.)
   → Microsoft redirects to /api/auth/entra/callback?code=...

3. App exchanges the code for tokens (MSAL authorization_code flow)
   → Gets: id_token (user identity), access_token (scoped to api://<client-id>)

4. App sets two HTTP-only cookies:
   auth_token   = app's own JWT  (existing auth system — unchanged)
   entra_token  = Entra access token  (used as OBO assertion)

5. User sends a chat message
   → /api/chat — app reads entra_token cookie
   → MSAL OBO: exchanges entra_token for a token scoped to https://ai.azure.com/.default
   → AIProjectClient is created with that OBO token
   → Foundry call carries the user's identity
   → Fabric Data Agent accepts the call ✅
```

---

## Local Development

Add these to `app/.env`:

```env
ENABLE_OBO_AUTH=true
ENTRA_CLIENT_ID=<your-client-id>
ENTRA_CLIENT_SECRET=<your-secret>
ENTRA_TENANT_ID=<your-tenant-id>
ENTRA_REDIRECT_URI=http://localhost:8000/api/auth/entra/callback
ENTRA_APP_SCOPE=api://<your-client-id>/user_impersonation
```

Ensure `http://localhost:8000/api/auth/entra/callback` is in your App Registration's
Redirect URIs (see Step 1).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Login button not visible | `ENABLE_OBO_AUTH` not set, or static login.html not redeployed | Set `ENABLE_OBO_AUTH=true` and restart |
| Redirect URI mismatch error | `ENTRA_REDIRECT_URI` doesn't exactly match what's registered | Ensure no trailing slash; check App Registration Redirect URIs |
| `state_mismatch` error | Cookie blocked (HTTP, or cross-site issue) | Ensure app is on HTTPS; `ENTRA_REDIRECT_URI` must be the same hostname as the app |
| `token_exchange_failed` | Wrong client secret, or wrong tenant | Double-check `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID` |
| Chat still fails after Entra login | OBO exchange failing | Check app logs: `az webapp log tail --name <app> --resource-group <rg>` — look for `OBO token acquisition failed` |
| `AADSTS65001: has not consented` | OAuth2PermissionGrant not created — `az ad app permission admin-consent` alone is insufficient | Use the direct Graph API POST in Step 4 CLI section to create the grant explicitly |
| `401 audience is incorrect (https://ai.azure.com)` | `ENTRA_FOUNDRY_SCOPE` is set to `cognitiveservices.azure.com` instead of `ai.azure.com` | Ensure `ENTRA_FOUNDRY_SCOPE=https://ai.azure.com/.default` (default); the Foundry Conversations API requires this audience |
| `insufficient_privileges` from Fabric | User is not a workspace member | Add the user's Entra account to the Fabric workspace as Contributor or Member |
| OBO fails with `invalid_grant` | `ENTRA_APP_SCOPE` not set, so token doesn't have the right audience | Set `ENTRA_APP_SCOPE=api://<client-id>/user_impersonation` |
| SQL login users still need Fabric | Expected — SQL-only users don't have an Entra token | They can still use agents that don't require Fabric Data Agents |
| `ValueError: You cannot use any scope value that is reserved` | MSAL scope list includes `openid`, `profile`, etc. | Only pass the resource scope (e.g. `api://<client-id>/user_impersonation`) — MSAL adds OIDC scopes automatically |

---

## Security Notes

- The `entra_token` cookie is **HTTP-only** (JavaScript cannot read it) and **Secure** (HTTPS only) — it is never exposed to the browser's JS runtime.
- The `auth_token` (SQL JWT) and `entra_token` (Entra) are **separate cookies** — compromise of one does not affect the other.
- The client secret must be rotated before it expires. Set a calendar reminder when you create it.
- Minimum required permissions are documented in Step 4 — do not grant broader permissions than listed.
