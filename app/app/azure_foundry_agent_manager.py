"""Azure AI Foundry Published Agents integration layer using the Responses API."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx

from azure.identity.aio import DefaultAzureCredential, AzureCliCredential
from azure.ai.projects.aio import AIProjectClient

from config import settings
from utils.logging_config import logger
from .chart_generator import ResponseFormatter

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
    """Manages orchestrator and specialist published agents using the Responses API."""

    def __init__(self) -> None:
        self.credential = self._create_credential()

        if not settings.project_endpoint:
            raise ValueError(
                "PROJECT_ENDPOINT is required for the Azure AI Foundry agent backend. "
                "Set it in App Settings or .env."
            )

        # Initialize the new async project client for Responses API
        self.project_client = AIProjectClient(
            endpoint=settings.project_endpoint,
            credential=self.credential,
        )

        self._lock = asyncio.Lock()

        # Optional MCP client for external tool calls (Retained for backward compatibility)
        self.mcp_client = httpx.AsyncClient(base_url=settings.mcp_server_url)
        self.mcp_tools_cache: Optional[List[Dict[str, Any]]] = None

        # Specialist profiles map to Published Agent Resource IDs
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

    # ── MCP helpers (Retained for compatibility) ───────────────────────────────

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

    # ── Primary chat entry point (Responses API) ───────────────────────────────

    async def chat(
        self,
        *,
        message: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_context: Optional[Dict] = None,
    ) -> ChatResult:
        """Process a chat request through a specific published agent."""

        normalized_type = (agent_type or "").strip().lower()
        if not normalized_type or normalized_type in {"auto", "default", "orchestrator"}:
            normalized_type = "orchestrator"

        if normalized_type == "orchestrator":
            agent_id = self.orchestrator_agent_id
            agent_name = self.orchestrator_agent_name
        elif normalized_type in self.specialist_profiles:
            profile = self.specialist_profiles[normalized_type]
            agent_id = profile["id"]
            agent_name = profile["display_name"]
        else:
            raise ValueError(f"Unknown agent type: {normalized_type}")

        logger.info(f"💬 Chat (Responses API) – agent={agent_name}, conversation={thread_id or 'new'}")
        logger.info(f"📨 User message: {message[:200]}")

        try:
            async with self._lock:
                # Use the OpenAI compatibility layer for Responses
                async with self.project_client.get_openai_client() as openai_client:
                    
                    # Prepare the Responses API payload
                    kwargs = {
                        "agent_id": agent_id,
                        "input": message,
                    }
                    
                    # Pass the conversation history ID if this is a continuing thread
                    if thread_id:
                        kwargs["conversation_id"] = thread_id

                    # Single-shot invocation
                    response = await openai_client.responses.create(**kwargs)

                    # Extract the response text safely depending on SDK structure
                    response_text = getattr(response, "output_text", "")
                    if not response_text and hasattr(response, "output"):
                        for out in response.output:
                            if getattr(out, "type", "") == "text_message":
                                response_text += getattr(out, "text", "")

                    # Extract conversation persistence details
                    new_thread_id = getattr(response, "conversation_id", thread_id or "new_session")
                    response_id = getattr(response, "id", "response_completed")

                    logger.info(f"✅ Chat complete – response: {response_text[:200]}")

                    # If this was routed to a specialist explicitly, format the response
                    if normalized_type != "orchestrator":
                        response_text = ResponseFormatter.format_specialist_response(
                            specialist_name=agent_name,
                            response_text=response_text,
                            data=None,
                            question=message,
                        )

                    return ChatResult(
                        response=response_text,
                        thread_id=new_thread_id,
                        agent_id=agent_id,
                        run_id=response_id,
                        metadata={
                            "agent_name": agent_name,
                            "agent_type": normalized_type
                        },
                    )

        except Exception as e:
            if _is_content_safety_error(e):
                logger.warning(f"⚠️ Content safety filter raised exception for thread={thread_id}: {e}")
                return ChatResult(
                    response=_content_safety_message(),
                    thread_id=thread_id or "new",
                    agent_id=agent_id,
                    run_id="",
                    metadata={"content_filtered": True, "agent_type": normalized_type},
                )
            logger.error(f"❌ Chat error (Responses API): {e}")
            raise

    async def cleanup(self):
        """Release resources."""
        await self.project_client.close()
        await self.mcp_client.aclose()
        logger.info("🧹 Cleaned up Azure AI Foundry Agent Manager resources")


# Module-level singleton — guarded so import succeeds without PROJECT_ENDPOINT configured
try:
    foundry_agent_manager = AzureAIFoundryAgentManager()
except Exception as _e:
    logger.warning("AzureAIFoundryAgentManager unavailable: %s", _e)
    foundry_agent_manager = None