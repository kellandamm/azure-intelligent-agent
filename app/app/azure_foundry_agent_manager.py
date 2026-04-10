"""Microsoft Foundry hosted-agent backend with app-driven routing.

This backend keeps specialist agents hosted in Microsoft Foundry, while the web
application performs routing in code before invoking the selected hosted agent.
That makes the routing model explicit and avoids relying on classic connected-
agent behavior from older Foundry experiences.
"""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx
from azure.ai.projects.aio import AIProjectClient
from azure.core.credentials import AccessToken
from azure.core.credentials_async import AsyncTokenCredential
from azure.identity.aio import AzureCliCredential, DefaultAzureCredential

from config import settings
from utils.logging_config import logger
from .chart_generator import ResponseFormatter

_CONTENT_FILTER_CODES = frozenset(
    [
        "content_filter",
        "ResponsibleAIPolicyViolation",
        "content_management_policy",
    ]
)


class _StaticTokenCredential(AsyncTokenCredential):
    """Wraps a pre-acquired Entra access token as an AsyncTokenCredential.

    Used for the OBO flow where the token is obtained outside the normal
    DefaultAzureCredential chain.
    """

    def __init__(self, token: str) -> None:
        import time
        # Set a generous expiry — the token was just acquired so it is valid
        # for at least ~3 minutes (MSAL returns tokens with ~1h lifetime).
        self._token = AccessToken(token=token, expires_on=int(time.time()) + 3300)

    async def get_token(self, *scopes: str, **kwargs: Any) -> AccessToken:  # type: ignore[override]
        return self._token

    async def close(self) -> None:
        pass

    async def __aenter__(self) -> "_StaticTokenCredential":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


def _is_content_safety_error(exc: Exception) -> bool:
    error_code = getattr(getattr(exc, "error", None), "code", None) or ""
    if error_code in _CONTENT_FILTER_CODES:
        return True
    msg = str(exc).lower()
    return any(
        kw in msg
        for kw in ("content_filter", "responsibleaipolicyviolation", "content_management")
    )


def _content_safety_message() -> str:
    return (
        "I'm unable to respond to that request because it was flagged by the content safety "
        "policy. Please rephrase your question or contact your administrator if you believe "
        "this is in error."
    )


@dataclass
class ChatResult:
    response: str
    thread_id: str
    agent_id: str
    run_id: str
    metadata: Optional[Dict[str, Any]] = None


class FoundryHostedAgentBackendManager:
    """Routes requests in app code, then invokes Microsoft Foundry hosted agents."""

    def __init__(self) -> None:
        self.credential = self._create_credential()

        if not settings.project_endpoint:
            raise ValueError(
                "PROJECT_ENDPOINT is required for the Microsoft Foundry hosted-agent backend. "
                "Set it in App Settings or .env."
            )

        self.project_client = AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=self.credential,
        )

        self._lock = asyncio.Lock()
        self.mcp_client = httpx.AsyncClient(base_url=settings.mcp_server_url)

        self.specialist_profiles: Dict[str, Dict[str, Any]] = {
            "sales": {
                "display_name": "SalesAssistant",
                "id": settings.sales_agent_id,
                "description": "Revenue insights, top products, customer sales, regional sales performance",
            },
            "operations": {
                "display_name": "OperationsAssistant",
                "id": settings.realtime_agent_id,
                "description": "Operational metrics, uptime, fulfillment, inventory, order execution",
            },
            "analytics": {
                "display_name": "AnalyticsAssistant",
                "id": settings.analytics_agent_id,
                "description": "Patterns, comparisons, KPI analysis, segmentation, business intelligence",
            },
            "financial": {
                "display_name": "FinancialAdvisor",
                "id": settings.financial_agent_id,
                "description": "ROI, margin, cost, forecast, profitability",
            },
            "support": {
                "display_name": "CustomerSupportAssistant",
                "id": settings.support_agent_id,
                "description": "Support, troubleshooting, billing, orders, tickets",
            },
            "customer_success": {
                "display_name": "CustomerSuccessAgent",
                "id": settings.customer_success_agent_id,
                "description": "Churn, retention, inactive customers, at-risk accounts",
            },
            "coordinator": {
                "display_name": "OperationsCoordinator",
                "id": settings.operations_agent_id,
                "description": "Logistics, supply chain, shipping, weather impacts",
            },
            "operations_excellence": {
                "display_name": "OperationsExcellenceAgent",
                "id": settings.operations_excellence_agent_id,
                "description": "Process optimization, productivity, throughput, efficiency",
            },
        }

        self.orchestrator_agent_id = settings.orchestrator_agent_id
        self.orchestrator_agent_name = settings.orchestrator_agent_name or "RetailAssistantOrchestrator"

    @staticmethod
    def _create_credential():
        try:
            return DefaultAzureCredential()
        except Exception:
            logger.info("ℹ️ Falling back to AzureCliCredential for AIProjectClient")
            return AzureCliCredential()

    def _resolve_explicit_agent(self, agent_type: Optional[str]) -> Tuple[str, str, str]:
        normalized_type = (agent_type or "").strip().lower()

        if not normalized_type or normalized_type in {"auto", "default", "orchestrator"}:
            return "orchestrator", self.orchestrator_agent_id, self.orchestrator_agent_name

        if normalized_type in self.specialist_profiles:
            profile = self.specialist_profiles[normalized_type]
            return normalized_type, profile["id"], profile["display_name"]

        raise ValueError(f"Unknown agent type: {normalized_type}")

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def _route_request(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        text = self._normalize_text(message)

        route_rules = [
            (
                "customer_success",
                [
                    "churn",
                    "retention",
                    "at-risk",
                    "at risk",
                    "inactive customer",
                    "inactive customers",
                    "haven't purchased",
                    "have not purchased",
                    "days since last purchase",
                    "renewal",
                    "renewals",
                ],
                "Customer retention / churn style request",
            ),
            (
                "financial",
                [
                    "roi",
                    "return on investment",
                    "forecast",
                    "predict",
                    "projection",
                    "projected",
                    "margin",
                    "profit",
                    "profitability",
                    "carrying cost",
                    "cost of inventory",
                    "revenue forecast",
                ],
                "Financial / ROI / forecast request",
            ),
            (
                "operations_excellence",
                [
                    "efficiency",
                    "optimi",
                    "throughput",
                    "productivity",
                    "process improvement",
                    "waste",
                    "cycle time",
                    "bottleneck",
                    "operational excellence",
                ],
                "Operational excellence / optimization request",
            ),
            (
                "coordinator",
                [
                    "logistics",
                    "supply chain",
                    "shipping",
                    "shipment",
                    "weather impact",
                    "route delay",
                    "delivery issue",
                ],
                "Coordination / logistics request",
            ),
            (
                "operations",
                [
                    "inventory",
                    "fulfillment",
                    "uptime",
                    "downtime",
                    "system health",
                    "operations status",
                    "order backlog",
                    "real-time",
                    "real time",
                    "warehouse",
                ],
                "Operations / inventory / fulfillment request",
            ),
            (
                "analytics",
                [
                    "segment",
                    "segmentation",
                    "analyze",
                    "analysis",
                    "pattern",
                    "patterns",
                    "compare",
                    "comparison",
                    "kpi",
                    "kpis",
                    "trend",
                    "trends",
                    "dashboard",
                ],
                "Analytics / BI request",
            ),
            (
                "support",
                [
                    "support",
                    "troubleshoot",
                    "issue",
                    "problem",
                    "ticket",
                    "billing issue",
                    "refund",
                    "return order",
                    "help me with",
                    "order status",
                ],
                "Support / troubleshooting request",
            ),
            (
                "sales",
                [
                    "sales",
                    "revenue",
                    "best-selling",
                    "best selling",
                    "top product",
                    "top products",
                    "top customer",
                    "top customers",
                    "sales performance",
                    "by region",
                    "quarter",
                    "quota",
                ],
                "Sales / revenue request",
            ),
        ]

        for route, keywords, reason in route_rules:
            if any(keyword in text for keyword in keywords):
                return {
                    "route": route,
                    "reason": reason,
                    "rewritten_query": message.strip(),
                }

        return {
            "route": "orchestrator",
            "reason": "No specialist rule matched cleanly",
            "rewritten_query": message.strip(),
        }

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        output_text = getattr(response, "output_text", "") or ""
        if output_text:
            return output_text.strip()

        parts: List[str] = []
        for item in getattr(response, "output", None) or []:
            if isinstance(item, dict):
                item_type = item.get("type", "")
                content = item.get("content", [])
                direct_text = item.get("text")
            else:
                item_type = getattr(item, "type", "")
                content = getattr(item, "content", None) or []
                direct_text = getattr(item, "text", None)

            if item_type in {"message", "text_message"}:
                for content_item in content:
                    if isinstance(content_item, dict):
                        text_dict = content_item.get("text") or {}
                        value = text_dict.get("value")
                    else:
                        text_obj = getattr(content_item, "text", None)
                        value = getattr(text_obj, "value", None)
                    if value:
                        parts.append(value)
            if isinstance(direct_text, str) and direct_text:
                parts.append(direct_text)
            return "\n".join(p for p in parts if p).strip()

    async def _create_or_append_conversation(self, openai_client: Any, thread_id: Optional[str], message: str) -> str:
        if not thread_id:
            conversation = await openai_client.conversations.create(
                items=[{"type": "message", "role": "user", "content": message}]
            )
            return conversation.id

        await openai_client.conversations.items.create(
            conversation_id=thread_id,
            items=[{"type": "message", "role": "user", "content": message}],
        )
        return thread_id

    async def _invoke_foundry_agent(
        self,
        *,
        agent_id: str,
        agent_name: str,
        message: str,
        thread_id: Optional[str],
        obo_token: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        # When OBO is enabled and we have a user token, create a short-lived
        # per-request AIProjectClient using that token so Foundry forwards the
        # user's identity to downstream Fabric Data Agents.
        if obo_token and settings.enable_obo_auth:
            credential = _StaticTokenCredential(obo_token)
            per_request_client = AIProjectClient(
                endpoint=settings.project_endpoint,
                credential=credential,
            )
            client_cm = per_request_client
            logger.debug("🔐 Using OBO credential for Foundry call agent=%s", agent_name)
        else:
            client_cm = self.project_client

        async with client_cm.get_openai_client() as openai_client:
            conversation_id = await self._create_or_append_conversation(openai_client, thread_id, message)

            payload_variants = [
                {
                    "conversation": conversation_id,
                    "extra_body": {"agent_reference": {"name": agent_name, "type": "agent_reference"}},
                },
                {
                    "conversation": conversation_id,
                    "extra_body": {"agent_reference": {"id": agent_id, "name": agent_name, "type": "agent_reference"}},
                },
            ]

            last_exc: Optional[Exception] = None
            response: Any = None
            for payload in payload_variants:
                try:
                    response = await openai_client.responses.create(**payload)
                    break
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "⚠️ Hosted-agent payload variant failed for agent=%s payload=%s error=%s",
                        agent_name,
                        json.dumps(payload, default=str)[:800],
                        exc,
                    )

            if response is None:
                raise last_exc or RuntimeError("No response payload variant succeeded")

            response_text = self._extract_response_text(response)
            response_id = getattr(response, "id", "") or ""
            return response_text, conversation_id, response_id

    async def chat(
        self,
        *,
        message: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
        obo_user_assertion: Optional[str] = None,
    ) -> ChatResult:
        normalized_type, explicit_agent_id, explicit_agent_name = self._resolve_explicit_agent(agent_type)

        logger.info(
            "💬 Chat (Foundry-hosted agents + app-driven routing) – agent_type=%s, conversation=%s",
            normalized_type,
            thread_id or "new",
        )
        logger.info("📨 User message: %s", message[:200])

        try:
            async with self._lock:
                if normalized_type != "orchestrator":
                    final_agent_key = normalized_type
                    final_agent_id = explicit_agent_id
                    final_agent_name = explicit_agent_name
                    routed_query = message
                    route_reason = "Explicit specialist requested by caller"
                else:
                    route = self._route_request(message=message, user_context=user_context)
                    final_agent_key = route["route"]
                    route_reason = route["reason"]
                    routed_query = route["rewritten_query"]

                    if final_agent_key == "orchestrator":
                        final_agent_id = self.orchestrator_agent_id
                        final_agent_name = self.orchestrator_agent_name
                    else:
                        profile = self.specialist_profiles[final_agent_key]
                        final_agent_id = profile["id"]
                        final_agent_name = profile["display_name"]

                logger.info(
                    "🧭 Routed request to agent=%s (key=%s) reason=%s",
                    final_agent_name,
                    final_agent_key,
                    route_reason,
                )

                # Acquire OBO token once per request (if enabled)
                obo_token: Optional[str] = None
                if settings.enable_obo_auth and obo_user_assertion:
                    from services.obo_token_service import OBOTokenService
                    obo_token = await OBOTokenService.get_foundry_token(obo_user_assertion)

                response_text, new_thread_id, response_id = await self._invoke_foundry_agent(
                    agent_id=final_agent_id,
                    agent_name=final_agent_name,
                    message=routed_query,
                    thread_id=thread_id,
                    obo_token=obo_token,
                )

                if not response_text:
                    response_text = "The selected hosted agent completed successfully but returned no text."

                if final_agent_key != "orchestrator":
                    response_text = ResponseFormatter.format_specialist_response(
                        specialist_name=final_agent_name,
                        response_text=response_text,
                        data=None,
                        question=message,
                    )

                logger.info("✅ Chat complete – routed_agent=%s response=%s", final_agent_name, response_text[:200])

                return ChatResult(
                    response=response_text,
                    thread_id=new_thread_id,
                    agent_id=final_agent_id,
                    run_id=response_id,
                    metadata={
                        "requested_agent_type": normalized_type,
                        "routed_agent_type": final_agent_key,
                        "agent_name": final_agent_name,
                        "route_reason": route_reason,
                    },
                )

        except Exception as e:
            if _is_content_safety_error(e):
                logger.warning("⚠️ Content safety filter raised exception for thread=%s: %s", thread_id, e)
                return ChatResult(
                    response=_content_safety_message(),
                    thread_id=thread_id or "new",
                    agent_id=explicit_agent_id,
                    run_id="",
                    metadata={"content_filtered": True, "agent_type": normalized_type},
                )
            logger.error("❌ Chat error (Foundry-hosted agents + app-driven routing): %s", e, exc_info=True)
            raise

    async def cleanup(self):
        await self.project_client.close()
        await self.mcp_client.aclose()
        logger.info("🧹 Cleaned up Foundry-hosted agent backend resources")


foundry_hosted_agent_backend_manager = FoundryHostedAgentBackendManager()

# Backward-compatible aliases for older imports.
AzureAIFoundryAgentManager = FoundryHostedAgentBackendManager
foundry_agent_manager = foundry_hosted_agent_backend_manager
