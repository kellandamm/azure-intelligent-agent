"""
On-Behalf-Of (OBO) Token Service

Exchanges the app's local JWT for a Microsoft Entra access token scoped to
Azure AI Foundry, enabling the Foundry-hosted agents to call Fabric Data Agents
on behalf of the signed-in user.

Required app settings when ENABLE_OBO_AUTH=true:
  ENTRA_CLIENT_ID      - App Registration client ID
  ENTRA_CLIENT_SECRET  - App Registration client secret
  ENTRA_TENANT_ID      - Entra tenant ID
  ENTRA_USER_ASSERTION - The incoming bearer token representing the user
                         (populated at request time, not a static setting)

The App Registration must have delegated permissions for:
  - Azure AI Services / Azure AI Foundry: user_impersonation
  - Power BI Service / Microsoft Fabric: Tenant.Read.All (or user_impersonation)
"""
from __future__ import annotations

import asyncio
from typing import Optional

import msal

from config import settings
from utils.logging_config import logger


class OBOTokenService:
    """Acquires Entra access tokens via the OAuth2 On-Behalf-Of flow."""

    # Module-level MSAL app — created once, reused across requests.
    # MSAL handles token caching internally.
    _msal_app: Optional[msal.ConfidentialClientApplication] = None
    _init_lock = asyncio.Lock()

    @classmethod
    def _get_msal_app(cls) -> msal.ConfidentialClientApplication:
        if cls._msal_app is None:
            if not settings.entra_client_id:
                raise ValueError("ENTRA_CLIENT_ID must be set when ENABLE_OBO_AUTH=true")
            if not settings.entra_client_secret:
                raise ValueError("ENTRA_CLIENT_SECRET must be set when ENABLE_OBO_AUTH=true")
            if not settings.entra_tenant_id:
                raise ValueError("ENTRA_TENANT_ID must be set when ENABLE_OBO_AUTH=true")

            cls._msal_app = msal.ConfidentialClientApplication(
                client_id=settings.entra_client_id,
                client_credential=settings.entra_client_secret,
                authority=f"https://login.microsoftonline.com/{settings.entra_tenant_id}",
            )
            logger.info("🔐 MSAL ConfidentialClientApplication initialised for OBO flow")
        return cls._msal_app

    @classmethod
    async def get_foundry_token(cls, user_assertion: str) -> str:
        """
        Exchange *user_assertion* (the caller's bearer token) for an access
        token scoped to Azure AI Foundry using the OBO flow.

        Args:
            user_assertion: The raw bearer token from the incoming request
                            Authorization header.

        Returns:
            An Entra access token accepted by the Foundry Responses API.

        Raises:
            RuntimeError: If MSAL cannot acquire a token.
        """
        loop = asyncio.get_event_loop()
        # MSAL is synchronous — run in thread pool to avoid blocking the event loop
        token = await loop.run_in_executor(
            None,
            cls._acquire_token_sync,
            user_assertion,
            settings.entra_foundry_scope,
        )
        return token

    @classmethod
    def _acquire_token_sync(cls, user_assertion: str, scope: str) -> str:
        app = cls._get_msal_app()
        result = app.acquire_token_on_behalf_of(
            user_assertion=user_assertion,
            scopes=[scope],
        )

        if "access_token" in result:
            logger.debug("✅ OBO token acquired for scope=%s", scope)
            return result["access_token"]

        error = result.get("error", "unknown_error")
        description = result.get("error_description", "No description")
        logger.error("❌ OBO token acquisition failed: %s – %s", error, description)
        raise RuntimeError(
            f"OBO token acquisition failed ({error}): {description}"
        )
