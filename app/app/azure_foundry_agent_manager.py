"""Azure AI Foundry Agents integration layer for the demo app."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, RunStatus

from config import settings
from utils.logging_config import logger
from chart_generator import ResponseFormatter
import httpx


Message = Dict[str, Any]

# Error codes returned by Azure AI Foundry when the content-filter policy blocks a request.
_CONTENT_FILTER_CODES = frozenset([
    "content_filter",
    "ResponsibleAIPolicyViolation",
    "content_management_policy",
])


def _is_content_safety_error(exc: Exception) -> bool:
    """Return True if *exc* was raised because the AI content filter blocked the request."""
    error_code = getattr(getattr(exc, "error", None), "code", None) or ""
    if error_code in _CONTENT_FILTER_CODES:
        return True
    msg = str(exc).lower()
    return any(kw in msg for kw in ("content_filter", "responsibleaipolicyviolation", "content_management"))


def _content_safety_message() -> str:
    return (
        "I'm unable to respond to that request because it was flagged by the content safety "
        "policy. Please rephrase your question or contact your administrator if you believe "
        "this is in error."
    )


@dataclass
class ChatResult:
    """Container for chat responses."""

    response: str
    thread_id: str
    agent_id: str
    run_id: str
    metadata: Optional[Dict[str, Any]] = None


class AzureAIFoundryAgentManager:
    """Manages orchestrator and specialist agents using Azure AI Foundry."""

    def __init__(self) -> None:
        self.credential = self._create_credential()

        if not settings.project_endpoint:
            raise ValueError(
                "PROJECT_ENDPOINT is required for the Azure AI Foundry agent backend. "
                "Set it in App Settings or .env."
            )

        # AgentsClient connects directly to the Azure AI Foundry project endpoint.
        self.client = AgentsClient(
            endpoint=settings.project_endpoint,
            credential=self.credential,
        )

        self.sessions: Dict[str, str] = {}  # thread_id -> agent_type mapping
        self._lock = asyncio.Lock()

        # Optional MCP client for external tool calls
        self.mcp_client = httpx.AsyncClient(base_url=settings.mcp_server_url)
        self.mcp_tools_cache: Optional[List[Dict[str, Any]]] = None

        # Specialist agent definitions — IDs sourced from App Settings (no Fabric prefix)
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
            logger.info("ℹ️ Falling back to AzureCliCredential for Azure AI Foundry client")
            return AzureCliCredential()

    # ── MCP helpers ────────────────────────────────────────────────────────────

    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Fetch available MCP tools from the MCP server (cached)."""
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
        """Call an MCP tool via the MCP server."""
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

    # ── Thread management ──────────────────────────────────────────────────────

    async def _create_or_get_thread(self, thread_id: Optional[str] = None) -> tuple[str, bool]:
        """Create a new thread or reuse an existing one by ID."""
        if thread_id and thread_id in self.sessions:
            return thread_id, False

        thread = await asyncio.to_thread(self.client.threads.create)
        logger.info(f"📋 Created new thread: {thread.id}")
        return thread.id, True

    # ── Specialist routing ─────────────────────────────────────────────────────

    async def _route_to_specialist(
        self, specialist_type: str, question: str, thread_id: Optional[str] = None
    ) -> str:
        """Route a question directly to a specialist agent."""
        logger.info(f"🎯 Routing to {specialist_type} specialist: {question[:100]}")

        profile = self.specialist_profiles.get(specialist_type)
        if not profile:
            return f"Error: Unknown specialist type '{specialist_type}'"

        try:
            agent_thread_id, _ = await self._create_or_get_thread(thread_id)

            await asyncio.to_thread(
                self.client.messages.create,
                thread_id=agent_thread_id,
                role=MessageRole.USER,
                content=question,
            )

            run = await asyncio.to_thread(
                self.client.runs.create_and_process,
                thread_id=agent_thread_id,
                agent_id=profile["id"],
            )

            if run.status == RunStatus.FAILED:
                logger.error(f"❌ Specialist run failed: {run.last_error}")
                last_error = run.last_error or {}
                error_code = (
                    getattr(last_error, "code", None)
                    or (last_error.get("code") if isinstance(last_error, dict) else None)
                    or ""
                )
                if error_code in _CONTENT_FILTER_CODES or any(
                    kw in str(last_error).lower() for kw in ("content_filter", "responsibleaipolicy")
                ):
                    logger.warning(f"⚠️ Content safety filter triggered for specialist={specialist_type}")
                    return _content_safety_message()
                return f"Error: Specialist agent failed - {run.last_error}"

            response_text = self._extract_response(
                await asyncio.to_thread(self.client.messages.list, thread_id=agent_thread_id),
                run.created_at,
            )

            return ResponseFormatter.format_specialist_response(
                specialist_name=profile["display_name"],
                response_text=response_text,
                data=None,
                question=question,
            )

        except Exception as e:
            if _is_content_safety_error(e):
                logger.warning(f"⚠️ Content safety filter raised exception for specialist={specialist_type}: {e}")
                return _content_safety_message()
            logger.error(f"❌ Error routing to {specialist_type}: {e}")
            return f"Error contacting {specialist_type}: {str(e)}"

    @staticmethod
    def _extract_response(messages, created_at) -> str:
        """Extract the latest agent/assistant message from a message list."""
        for msg in messages:
            role = str(msg.role).lower()
            if role in ("assistant", "agent"):
                msg_time = getattr(msg, "created_at", None)
                if msg_time is None or msg_time >= created_at:
                    for content in msg.content:
                        if hasattr(content, "text") and hasattr(content.text, "value"):
                            return content.text.value
        return ""

    # ── Primary chat entry point ───────────────────────────────────────────────

    async def chat(
        self,
        *,
        message: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """Process a chat request through the orchestrator or a specific specialist."""

        normalized_type = (agent_type or "").strip().lower()
        if not normalized_type or normalized_type in {"sales", "orchestrator", "auto", "default"}:
            normalized_type = "orchestrator"

        async with self._lock:
            actual_thread_id, is_new = await self._create_or_get_thread(thread_id)

            if is_new:
                self.sessions[actual_thread_id] = normalized_type
                logger.info(f"🔄 New session: thread={actual_thread_id}, agent={normalized_type}")

            if normalized_type == "orchestrator":
                agent_id = self.orchestrator_agent_id
                agent_name = self.orchestrator_agent_name
            elif normalized_type in self.specialist_profiles:
                profile = self.specialist_profiles[normalized_type]
                agent_id = profile["id"]
                agent_name = profile["display_name"]
            else:
                raise ValueError(f"Unknown agent type: {normalized_type}")

            logger.info(f"💬 Chat – agent={agent_name}, thread={actual_thread_id}")
            logger.info(f"📨 User message: {message[:200]}")

            try:
                await asyncio.to_thread(
                    self.client.messages.create,
                    thread_id=actual_thread_id,
                    role=MessageRole.USER,
                    content=message,
                )

                run = await asyncio.to_thread(
                    self.client.runs.create_and_process,
                    thread_id=actual_thread_id,
                    agent_id=agent_id,
                )

                if run.status == RunStatus.FAILED:
                    logger.error(f"❌ Agent run failed: {run.last_error}")
                    last_error = run.last_error or {}
                    error_code = (
                        getattr(last_error, "code", None)
                        or (last_error.get("code") if isinstance(last_error, dict) else None)
                        or ""
                    )
                    if error_code in _CONTENT_FILTER_CODES or any(
                        kw in str(last_error).lower()
                        for kw in ("content_filter", "responsibleaipolicy")
                    ):
                        logger.warning(f"⚠️ Content safety filter triggered for thread={actual_thread_id}")
                        return ChatResult(
                            response=_content_safety_message(),
                            thread_id=actual_thread_id,
                            agent_id=agent_id,
                            run_id=run.id,
                            metadata={"content_filtered": True, "agent_type": normalized_type},
                        )
                    raise RuntimeError(f"Agent run failed: {run.last_error}")

                messages = await asyncio.to_thread(
                    self.client.messages.list, thread_id=actual_thread_id
                )
                response_text = self._extract_response(messages, run.created_at)

                logger.info(f"✅ Chat complete – response: {response_text[:200]}")

                return ChatResult(
                    response=response_text,
                    thread_id=actual_thread_id,
                    agent_id=agent_id,
                    run_id=run.id,
                    metadata={
                        "agent_name": agent_name,
                        "agent_type": normalized_type,
                        "run_status": str(run.status),
                        "created_at": (
                            run.created_at.isoformat()
                            if hasattr(run.created_at, "isoformat")
                            else str(run.created_at)
                        ),
                    },
                )

            except Exception as e:
                if _is_content_safety_error(e):
                    logger.warning(f"⚠️ Content safety filter raised exception for thread={actual_thread_id}: {e}")
                    return ChatResult(
                        response=_content_safety_message(),
                        thread_id=actual_thread_id,
                        agent_id=agent_id,
                        run_id="",
                        metadata={"content_filtered": True, "agent_type": normalized_type},
                    )
                logger.error(f"❌ Chat error: {e}")
                raise

    async def cleanup(self):
        """Release resources."""
        await self.mcp_client.aclose()
        logger.info("🧹 Cleaned up Azure AI Foundry Agent Manager resources")


# Module-level singleton — guarded so import succeeds without PROJECT_ENDPOINT configured
try:
    foundry_agent_manager = AzureAIFoundryAgentManager()
except Exception as _e:
    logger.warning("AzureAIFoundryAgentManager unavailable: %s", _e)
    foundry_agent_manager = None
