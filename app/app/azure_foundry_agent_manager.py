"""Azure AI Foundry Published Agents integration layer using OpenAI conversations + agent_reference, with defensive debug logging."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from azure.ai.projects.aio import AIProjectClient
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


def _safe_repr(value: Any, max_len: int = 2000) -> str:
    try:
        if hasattr(value, "model_dump"):
            text = json.dumps(value.model_dump(), default=str)
        elif hasattr(value, "dict"):
            text = json.dumps(value.dict(), default=str)
        else:
            text = repr(value)
    except Exception as exc:
        text = f"<unserializable {type(value).__name__}: {exc}>"
    return text[:max_len]


@dataclass
class ChatResult:
    response: str
    thread_id: str
    agent_id: str
    run_id: str
    metadata: Optional[Dict[str, Any]] = None


class AzureAIFoundryAgentManager:
    """Manages orchestrator and specialist published agents using conversation-backed Responses API."""

    def __init__(self) -> None:
        self.credential = self._create_credential()

        if not settings.project_endpoint:
            raise ValueError(
                "PROJECT_ENDPOINT is required for the Azure AI Foundry agent backend. "
                "Set it in App Settings or .env."
            )

        self.project_client = AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=self.credential,
        )

        self._lock = asyncio.Lock()
        self.mcp_client = httpx.AsyncClient(base_url=settings.mcp_server_url)
        self.mcp_tools_cache: Optional[List[Dict[str, Any]]] = None

        self.specialist_profiles: Dict[str, Dict[str, Any]] = {
            "sales": {
                "display_name": "SalesAssistant",
                "id": settings.sales_agent_id,
                "description": "Revenue insights, top products, and sales trends specialist",
            },
            "operations": {
                "display_name": "OperationsAssistant",
                "id": settings.realtime_agent_id,
                "description": "Real-time operational metrics and system health specialist",
            },
            "analytics": {
                "display_name": "AnalyticsAssistant",
                "id": settings.analytics_agent_id,
                "description": "Business intelligence, patterns, and KPI analysis specialist",
            },
            "financial": {
                "display_name": "FinancialAdvisor",
                "id": settings.financial_agent_id,
                "description": "ROI calculations, revenue forecasting, and profitability specialist",
            },
            "support": {
                "display_name": "CustomerSupportAssistant",
                "id": settings.support_agent_id,
                "description": "Customer support and troubleshooting specialist",
            },
            "coordinator": {
                "display_name": "OperationsCoordinator",
                "id": settings.operations_agent_id,
                "description": "Logistics, supply chain, and coordination specialist",
            },
            "customer_success": {
                "display_name": "CustomerSuccessAgent",
                "id": settings.customer_success_agent_id,
                "description": "Customer satisfaction, retention, and growth specialist",
            },
            "operations_excellence": {
                "display_name": "OperationsExcellenceAgent",
                "id": settings.operations_excellence_agent_id,
                "description": "Operational efficiency and process optimisation specialist",
            },
        }

        self.orchestrator_agent_id = settings.orchestrator_agent_id
        self.orchestrator_agent_name = settings.orchestrator_agent_name

    @staticmethod
    def _create_credential():
        try:
            return DefaultAzureCredential()
        except Exception:
            logger.info("ℹ️ Falling back to AzureCliCredential for AIProjectClient")
            return AzureCliCredential()

    def _resolve_agent(self, agent_type: Optional[str]) -> tuple[str, str, str]:
        normalized_type = (agent_type or "").strip().lower()
        if not normalized_type or normalized_type in {"auto", "default", "orchestrator"}:
            normalized_type = "orchestrator"

        if normalized_type == "orchestrator":
            return normalized_type, self.orchestrator_agent_id, self.orchestrator_agent_name

        if normalized_type in self.specialist_profiles:
            profile = self.specialist_profiles[normalized_type]
            return normalized_type, profile["id"], profile["display_name"]

        raise ValueError(f"Unknown agent type: {normalized_type}")

    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        if self.mcp_tools_cache:
            return self.mcp_tools_cache

        if not settings.enable_mcp:
            return []

        try:
            response = await self.mcp_client.get("/mcp/tools")
            response.raise_for_status()
            tools = response.json().get("tools", [])
            self.mcp_tools_cache = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["inputSchema"],
                    },
                }
                for t in tools
            ]
            logger.info(f"✅ Loaded {len(self.mcp_tools_cache)} MCP tools")
            return self.mcp_tools_cache
        except Exception as e:
            logger.error(f"❌ Failed to fetch MCP tools: {e}")
            return []

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        try:
            response = await self.mcp_client.post(
                "/mcp/call",
                json={"name": tool_name, "arguments": arguments, "user_context": None},
            )
            response.raise_for_status()
            result = response.json()
            if result.get("error"):
                logger.error(f"MCP tool '{tool_name}' error: {result['error']}")
                return {"error": result["error"]}
            return result.get("result")
        except Exception as e:
            logger.error(f"❌ Failed to call MCP tool '{tool_name}': {e}")
            return {"error": str(e)}

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        text = getattr(response, "output_text", "") or ""
        if text:
            return text.strip()

        parts: List[str] = []
        for item in getattr(response, "output", None) or []:
            item_type = getattr(item, "type", "") or (item.get("type", "") if isinstance(item, dict) else "")
            if item_type in {"message", "text_message"}:
                for content in getattr(item, "content", None) or (item.get("content", []) if isinstance(item, dict) else []):
                    text_obj = getattr(content, "text", None)
                    value = getattr(text_obj, "value", None)
                    if value:
                        parts.append(value)
                        continue
                    if isinstance(content, dict):
                        text_dict = content.get("text") or {}
                        if isinstance(text_dict, dict) and text_dict.get("value"):
                            parts.append(text_dict["value"])
                direct_text = getattr(item, "text", None)
                if isinstance(direct_text, str) and direct_text:
                    parts.append(direct_text)
        return "\n".join(p for p in parts if p).strip()

    async def _create_or_append_conversation(self, openai_client: Any, thread_id: Optional[str], message: str) -> str:
        conversations = getattr(openai_client, "conversations", None)
        if conversations is None:
            raise AttributeError("OpenAI client has no 'conversations' attribute")

        logger.info(
            "🔍 conversations methods: %s",
            [name for name in dir(conversations) if not name.startswith("_")][:30],
        )

        if not thread_id:
            payload = {"items": [{"type": "message", "role": "user", "content": message}]}
            logger.info("🔍 create conversation payload: %s", _safe_repr(payload))
            conversation = await conversations.create(**payload)
            logger.info("🔍 create conversation response: %s", _safe_repr(conversation))
            return conversation.id

        items_client = getattr(conversations, "items", None)
        if items_client is None or not hasattr(items_client, "create"):
            raise AttributeError("OpenAI conversations client has no 'items.create' method")

        payload = {
            "conversation_id": thread_id,
            "items": [{"type": "message", "role": "user", "content": message}],
        }
        logger.info("🔍 append conversation payload: %s", _safe_repr(payload))
        result = await items_client.create(**payload)
        logger.info("🔍 append conversation response: %s", _safe_repr(result))
        return thread_id

    def _agent_reference_payloads(self, agent_id: str, agent_name: str) -> List[Dict[str, Any]]:
        return [
            {"agent_reference": {"name": agent_name, "type": "agent_reference"}},
            {"agent_reference": {"id": agent_id, "type": "agent_reference"}},
            {"agent_reference": {"name": agent_name}},
            {"agent_reference": {"id": agent_id}},
        ]

    async def _create_response_with_fallbacks(
        self,
        openai_client: Any,
        conversation_id: str,
        agent_id: str,
        agent_name: str,
    ) -> Any:
        responses_client = getattr(openai_client, "responses", None)
        if responses_client is None or not hasattr(responses_client, "create"):
            raise AttributeError("OpenAI client has no 'responses.create' method")

        logger.info(
            "🔍 responses methods: %s",
            [name for name in dir(responses_client) if not name.startswith("_")][:30],
        )

        last_exc: Optional[Exception] = None
        base_variants = [
            {"conversation": conversation_id},
            {"conversation_id": conversation_id},
        ]

        for base in base_variants:
            for extra_body in self._agent_reference_payloads(agent_id, agent_name):
                payload = dict(base)
                payload["extra_body"] = extra_body
                logger.info("🔍 responses.create payload: %s", _safe_repr(payload))
                try:
                    response = await responses_client.create(**payload)
                    logger.info("🔍 responses.create response: %s", _safe_repr(response))
                    return response
                except TypeError as exc:
                    last_exc = exc
                    logger.warning("⚠️ responses.create TypeError with payload variant: %s", exc)
                except Exception as exc:
                    last_exc = exc
                    logger.warning("⚠️ responses.create failed with payload variant: %s", exc)

        if last_exc:
            raise last_exc
        raise RuntimeError("responses.create failed for all payload variants")

    async def chat(
        self,
        *,
        message: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_context: Optional[Dict] = None,
    ) -> ChatResult:
        normalized_type, agent_id, agent_name = self._resolve_agent(agent_type)

        logger.info(
            f"💬 Chat (Responses API + conversation) – agent={agent_name}, conversation={thread_id or 'new'}"
        )
        logger.info(f"📨 User message: {message[:200]}")
        logger.info("🔍 agent_id=%s, agent_name=%s, agent_type=%s", agent_id, agent_name, normalized_type)

        try:
            async with self._lock:
                async with self.project_client.get_openai_client() as openai_client:
                    logger.info(
                        "🔍 openai client attrs: %s",
                        [name for name in dir(openai_client) if not name.startswith("_")][:40],
                    )

                    conversation_id = await self._create_or_append_conversation(
                        openai_client,
                        thread_id,
                        message,
                    )

                    response = await self._create_response_with_fallbacks(
                        openai_client,
                        conversation_id,
                        agent_id,
                        agent_name,
                    )

                    response_text = self._extract_response_text(response)
                    if not response_text:
                        logger.warning("⚠️ Response had no parsed text. Raw response: %s", _safe_repr(response))
                        response_text = "The agent completed successfully but returned no text."

                    run_id = getattr(response, "id", "") or ""

                    logger.info(f"✅ Chat complete – response: {response_text[:200]}")

                    if normalized_type != "orchestrator":
                        response_text = ResponseFormatter.format_specialist_response(
                            specialist_name=agent_name,
                            response_text=response_text,
                            data=None,
                            question=message,
                        )

                    return ChatResult(
                        response=response_text,
                        thread_id=conversation_id,
                        agent_id=agent_id,
                        run_id=run_id,
                        metadata={
                            "agent_name": agent_name,
                            "agent_type": normalized_type,
                        },
                    )

        except Exception as e:
            if _is_content_safety_error(e):
                logger.warning(
                    f"⚠️ Content safety filter raised exception for thread={thread_id}: {e}"
                )
                return ChatResult(
                    response=_content_safety_message(),
                    thread_id=thread_id or "new",
                    agent_id=agent_id,
                    run_id="",
                    metadata={"content_filtered": True, "agent_type": normalized_type},
                )
            logger.error("❌ Chat error (Responses API + conversation): %s", e, exc_info=True)
            raise

    async def cleanup(self):
        await self.project_client.close()
        await self.mcp_client.aclose()
        logger.info("🧹 Cleaned up Azure AI Foundry Agent Manager resources")


try:
    foundry_agent_manager = AzureAIFoundryAgentManager()
except Exception as _e:
    logger.warning("AzureAIFoundryAgentManager unavailable: %s", _e)
    foundry_agent_manager = None
