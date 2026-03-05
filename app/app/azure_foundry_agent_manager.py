"""Azure AI Foundry Agents integration layer for the Fabric demo app."""
from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Agent,
    AgentThread,
    MessageRole,
    ThreadMessage,
    RunStatus,
    FunctionTool,
    ToolSet
)

from config import settings
from utils.logging_config import logger
from chart_generator import ResponseFormatter, ChartGenerator
import httpx


Message = Dict[str, Any]

# Error codes returned by Azure OpenAI / Azure AI Foundry when the
# content-filter policy (Security Policy 5207647b) blocks a request.
_CONTENT_FILTER_CODES = frozenset([
    "content_filter",
    "ResponsibleAIPolicyViolation",
    "content_management_policy",
])


def _is_content_safety_error(exc: Exception) -> bool:
    """Return True if *exc* was raised because the AI content filter blocked the request."""
    # Azure AI Foundry / azure-core raises HttpResponseError
    error_code = getattr(getattr(exc, 'error', None), 'code', None) or ""
    if error_code in _CONTENT_FILTER_CODES:
        return True
    # String fallback for wrapped or unexpected exception types
    msg = str(exc).lower()
    return any(kw in msg for kw in ("content_filter", "responsibleaipolicyviolation", "content_management"))


def _content_safety_message() -> str:
    """Return a user-facing message for content-filter blocks."""
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
        
        # Initialize Azure AI Foundry Project Client
        if settings.project_connection_string:
            self.client = AIProjectClient.from_connection_string(
                credential=self.credential,
                conn_str=settings.project_connection_string
            )
        else:
            self.client = AIProjectClient(
                endpoint=settings.project_endpoint,
                credential=self.credential
            )

        self.sessions: Dict[str, str] = {}  # thread_id -> agent_id mapping
        self._lock = asyncio.Lock()
        
        # MCP Client for tool calls
        self.mcp_client = httpx.AsyncClient(base_url=settings.mcp_server_url)
        self.mcp_tools_cache: Optional[List[Dict[str, Any]]] = None

        # Specialist agent definitions (use Foundry agent IDs)
        self.specialist_profiles: Dict[str, Dict[str, Any]] = {
            "sales": {
                "display_name": "SalesAssistant",
                "id": settings.fabric_sales_agent_id,
                "description": "Revenue insights, top products, and sales trends specialist",
            },
            "operations": {
                "display_name": "OperationsAssistant",
                "id": settings.fabric_realtime_agent_id,
                "description": "Real-time operational metrics and system health specialist",
            },
            "analytics": {
                "display_name": "AnalyticsAssistant",
                "id": settings.fabric_analytics_agent_id or "analytics-foundry-agent",
                "description": "Business intelligence, patterns, and KPI analysis specialist",
            },
            "financial": {
                "display_name": "FinancialAdvisor",
                "id": settings.fabric_financial_agent_id or "financial-foundry-agent",
                "description": "ROI calculations, revenue forecasting, and profitability specialist",
            },
            "support": {
                "display_name": "CustomerSupportAssistant",
                "id": settings.fabric_support_agent_id or "support-foundry-agent",
                "description": "Customer support and troubleshooting specialist",
            },
            "coordinator": {
                "display_name": "OperationsCoordinator",
                "id": settings.fabric_operations_agent_id or "operations-coordinator-foundry",
                "description": "Logistics, supply chain, and weather coordination specialist",
            },
            "customer_success": {
                "display_name": "CustomerSuccessAgent",
                "id": settings.fabric_customer_success_agent_id or "customer-success-foundry",
                "description": "Customer satisfaction, retention, and growth specialist",
            },
            "operations_excellence": {
                "display_name": "OperationsExcellenceAgent",
                "id": settings.fabric_operations_excellence_agent_id or "operations-excellence-foundry",
                "description": "Operational efficiency and process optimization specialist",
            },
        }

        # Orchestrator agent
        self.orchestrator_agent_id = settings.fabric_orchestrator_agent_id
        self.orchestrator_agent_name = settings.fabric_orchestrator_agent_name

    @staticmethod
    def _create_credential():
        try:
            return DefaultAzureCredential()
        except Exception:  # pragma: no cover - fallback for local dev
            logger.info("ℹ️ Falling back to AzureCliCredential for Azure AI Foundry client")
            return AzureCliCredential()

    async def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Fetch available MCP tools from the MCP server."""
        if self.mcp_tools_cache:
            return self.mcp_tools_cache
        
        try:
            if not settings.enable_mcp:
                logger.info("MCP is disabled, no tools available")
                return []
                
            response = await self.mcp_client.get("/mcp/tools")
            response.raise_for_status()
            
            data = response.json()
            tools = data.get("tools", [])
            
            # Convert MCP tools to Azure AI Foundry function tool format
            foundry_tools = []
            for tool in tools:
                foundry_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["inputSchema"]
                    }
                })
            
            self.mcp_tools_cache = foundry_tools
            logger.info(f"✅ Loaded {len(foundry_tools)} MCP tools")
            return foundry_tools
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch MCP tools: {e}")
            return []

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool via the MCP server."""
        try:
            response = await self.mcp_client.post(
                "/mcp/call",
                json={
                    "name": tool_name,
                    "arguments": arguments,
                    "user_context": None  # Can be enhanced with RLS context
                }
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

    async def _create_or_get_thread(self, thread_id: Optional[str] = None) -> tuple[str, bool]:
        """Create a new thread or get an existing one."""
        if thread_id and thread_id in self.sessions:
            return thread_id, False
        
        # Create new thread
        thread = await asyncio.to_thread(self.client.agents.create_thread)
        new_thread_id = thread.id
        
        logger.info(f"📋 Created new thread: {new_thread_id}")
        return new_thread_id, True

    async def _route_to_specialist(self, specialist_type: str, question: str, thread_id: Optional[str] = None) -> str:
        """Route a question to a specific specialist agent."""
        logger.info(f"🎯 Routing to {specialist_type} specialist: {question[:100]}")
        
        profile = self.specialist_profiles.get(specialist_type)
        if not profile:
            return f"Error: Unknown specialist type '{specialist_type}'"
        
        try:
            # Get or create thread
            agent_thread_id, _ = await self._create_or_get_thread(thread_id)
            
            # Create message
            await asyncio.to_thread(
                self.client.agents.create_message,
                thread_id=agent_thread_id,
                role="user",
                content=question
            )
            
            # Run the specialist agent
            run = await asyncio.to_thread(
                self.client.agents.create_and_process_run,
                thread_id=agent_thread_id,
                agent_id=profile["id"]
            )
            
            if run.status == "failed":
                logger.error(f"❌ Specialist run failed: {run.last_error}")
                last_error = run.last_error or {}
                error_code = getattr(last_error, 'code', None) or (last_error.get('code') if isinstance(last_error, dict) else None) or ""
                if error_code in _CONTENT_FILTER_CODES or any(kw in str(last_error).lower() for kw in ("content_filter", "responsibleaipolicy")):
                    logger.warning(f"⚠️ Content safety filter triggered for specialist={specialist_type}")
                    return _content_safety_message()
                return f"Error: Specialist agent failed - {run.last_error}"
            
            # Get the response messages
            messages = await asyncio.to_thread(
                self.client.agents.list_messages,
                thread_id=agent_thread_id
            )
            
            # Get the latest assistant message
            response_text = ""
            for msg in messages.data:
                if msg.role == "assistant" and msg.created_at >= run.created_at:
                    for content in msg.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            response_text = content.text.value
                            break
                    if response_text:
                        break
            
            # Format the response
            formatted_response = ResponseFormatter.format_specialist_response(
                specialist_name=profile["display_name"],
                response_text=response_text,
                data=None,
                question=question
            )
            
            return formatted_response
            
        except Exception as e:
            if _is_content_safety_error(e):
                logger.warning(f"⚠️ Content safety filter raised exception for specialist={specialist_type}: {e}")
                return _content_safety_message()
            logger.error(f"❌ Error routing to {specialist_type}: {e}")
            return f"Error contacting {specialist_type}: {str(e)}"

    async def chat(
        self,
        *,
        message: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> ChatResult:
        """Process a chat request through the orchestrator or specific specialist."""

        normalized_type = (agent_type or "").strip().lower()
        if not normalized_type or normalized_type in {"sales", "orchestrator", "auto", "default"}:
            normalized_type = "orchestrator"

        async with self._lock:
            # Get or create thread
            actual_thread_id, is_new = await self._create_or_get_thread(thread_id)
            
            if is_new:
                self.sessions[actual_thread_id] = normalized_type
                logger.info(f"🔄 New session: thread={actual_thread_id}, agent={normalized_type}")

            # Route to orchestrator or specialist
            if normalized_type == "orchestrator":
                agent_id = self.orchestrator_agent_id
                agent_name = self.orchestrator_agent_name
            elif normalized_type in self.specialist_profiles:
                profile = self.specialist_profiles[normalized_type]
                agent_id = profile["id"]
                agent_name = profile["display_name"]
            else:
                raise ValueError(f"Unknown agent type: {normalized_type}")

            logger.info(f"💬 Chat request - Agent: {agent_name}, Thread: {actual_thread_id}")
            logger.info(f"📨 User message: {message[:200]}")

            try:
                # Create user message
                await asyncio.to_thread(
                    self.client.agents.create_message,
                    thread_id=actual_thread_id,
                    role="user",
                    content=message
                )
                
                # Run the agent
                run = await asyncio.to_thread(
                    self.client.agents.create_and_process_run,
                    thread_id=actual_thread_id,
                    agent_id=agent_id
                )
                
            if run.status == "failed":
                logger.error(f"❌ Agent run failed: {run.last_error}")
                # Detect content-filter failures reported via run.last_error
                last_error = run.last_error or {}
                error_code = getattr(last_error, 'code', None) or (last_error.get('code') if isinstance(last_error, dict) else None) or ""
                if error_code in _CONTENT_FILTER_CODES or any(kw in str(last_error).lower() for kw in ("content_filter", "responsibleaipolicy")):
                    logger.warning(f"⚠️ Content safety filter triggered for thread={actual_thread_id}")
                    return ChatResult(
                        response=_content_safety_message(),
                        thread_id=actual_thread_id,
                        agent_id=agent_id,
                        run_id=run.id,
                        metadata={"content_filtered": True, "agent_type": normalized_type}
                    )
                raise RuntimeError(f"Agent run failed: {run.last_error}")
                
                # Get the response messages
                messages = await asyncio.to_thread(
                    self.client.agents.list_messages,
                    thread_id=actual_thread_id
                )
                
                # Extract the latest assistant response
                response_text = ""
                for msg in messages.data:
                    if msg.role == "assistant" and msg.created_at >= run.created_at:
                        for content in msg.content:
                            if hasattr(content, 'text') and hasattr(content.text, 'value'):
                                response_text = content.text.value
                                break
                        if response_text:
                            break
                
                logger.info(f"✅ Chat complete - Response: {response_text[:200]}")
                
                return ChatResult(
                    response=response_text,
                    thread_id=actual_thread_id,
                    agent_id=agent_id,
                    run_id=run.id,
                    metadata={
                        "agent_name": agent_name,
                        "agent_type": normalized_type,
                        "run_status": run.status,
                        "created_at": run.created_at.isoformat() if hasattr(run.created_at, 'isoformat') else str(run.created_at)
                    }
                )

            except Exception as e:
                if _is_content_safety_error(e):
                    logger.warning(f"⚠️ Content safety filter raised exception for thread={actual_thread_id}: {e}")
                    return ChatResult(
                        response=_content_safety_message(),
                        thread_id=actual_thread_id,
                        agent_id=agent_id,
                        run_id="",
                        metadata={"content_filtered": True, "agent_type": normalized_type}
                    )
                logger.error(f"❌ Chat error: {e}")
                raise

    async def cleanup(self):
        """Cleanup resources."""
        await self.mcp_client.aclose()
        logger.info("🧹 Cleaned up Azure AI Foundry Agent Manager resources")


# Global instance
agent_framework_manager = AzureAIFoundryAgentManager()
