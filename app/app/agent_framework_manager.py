"""Agent Framework integration layer for the Fabric demo app."""

from __future__ import annotations

import asyncio
import json
import inspect
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Awaitable

from azure.identity import DefaultAzureCredential, AzureCliCredential
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework._types import ChatMessage, TextContent

from config import settings
from .agent_tools import (
    FABRIC_TOOLS,
    SALES_TOOLS,
    CALCULATION_TOOLS,
    WEATHER_TOOLS,
    execute_tool_call,
)
from utils.logging_config import logger
from .chart_generator import ResponseFormatter, ChartGenerator


Message = Dict[str, Any]


@dataclass
class ChatResult:
    """Container for chat responses."""

    response: str
    thread_id: str
    agent_id: str
    run_id: str
    metadata: Optional[Dict[str, Any]] = None


class AgentFrameworkManager:
    """Manages orchestrator and specialist agents using Microsoft Agent Framework."""

    def __init__(self) -> None:
        self.credential = self._create_credential()
        self.client = AzureOpenAIChatClient(
            endpoint=settings.azure_openai_endpoint,
            deployment_name=settings.azure_openai_deployment,
            credential=self.credential,
            api_version=settings.azure_openai_api_version,
        )

        self.sessions: Dict[str, List[Message]] = {}
        self._lock = asyncio.Lock()
        self.current_user_context: Optional[Dict[str, Any]] = None  # For RLS filtering

        # Specialist agent definitions
        self.specialist_profiles: Dict[str, Dict[str, Any]] = {
            "sales": {
                "display_name": "SalesAssistant",
                "id": settings.fabric_sales_agent_id,
                "prompt": (
                    "You are SalesAssistant. Provide revenue insights, top products, and sales trends "
                    "using clear, metric-driven language. When data is requested, call the provided "
                    "tools to gather accurate figures before responding. Summaries should highlight key "
                    "successes and risks, ending with an actionable recommendation. Data is automatically "
                    "filtered by the user's authorized region."
                ),
                "tools": SALES_TOOLS,  # Use local tools with RLS support
            },
            "operations": {
                "display_name": "OperationsAssistant",
                "id": settings.fabric_realtime_agent_id,
                "prompt": (
                    "You are OperationsAssistant. Monitor real-time operational metrics, uptime, and system "
                    "health. Use Fabric data tools to reference current status and highlight incidents. Focus "
                    "on providing concise readiness summaries and next best actions."
                ),
                "tools": FABRIC_TOOLS,
            },
            "analytics": {
                "display_name": "AnalyticsAssistant",
                "id": settings.fabric_analytics_agent_id or "analytics-agent-framework",
                "prompt": (
                    "You are AnalyticsAssistant, a senior business intelligence analyst specializing in Microsoft Fabric data.\n"
                    "Capabilities:\n"
                    "- Analyze sales performance, growth trends, and seasonality\n"
                    "- Provide customer demographic insights and segmentation\n"
                    "- Monitor inventory, fulfillment, and operational KPIs\n"
                    "- Summarize key patterns with supporting data points\n\n"
                    "When users request reports or visualizations, provide the insights and let the system know "
                    "that charts will be automatically generated. Always cite metrics and suggest actionable insights."
                ),
                "tools": FABRIC_TOOLS,
            },
            "financial": {
                "display_name": "FinancialAdvisor",
                "id": settings.fabric_financial_agent_id or "financial-agent-framework",
                "prompt": (
                    "You are FinancialAdvisor. Offer ROI calculations, revenue forecasting, and profitability analysis.\n"
                    "When presenting financial forecasts or comparisons, structure your response with clear numbers "
                    "and note that interactive charts will be displayed automatically. Whenever math is needed, call "
                    "the calculation tools to provide accurate numbers. Explain your assumptions, outline risks, "
                    "and conclude with a financial recommendation."
                ),
                "tools": CALCULATION_TOOLS,
            },
            "support": {
                "display_name": "CustomerSupportAssistant",
                "id": settings.fabric_support_agent_id or "support-agent-framework",
                "prompt": (
                    "You are CustomerSupportAssistant, a friendly and empathetic support specialist.\n"
                    "Clarify the customer request, offer clear troubleshooting steps, and suggest helpful follow-ups."
                ),
                "tools": [],
            },
            "coordinator": {
                "display_name": "OperationsCoordinator",
                "id": settings.fabric_operations_agent_id
                or "operations-coordinator-framework",
                "prompt": (
                    "You are OperationsCoordinator overseeing logistics and supply chain status.\n"
                    "Combine Fabric metrics with weather insights when appropriate to anticipate disruptions."
                ),
                "tools": FABRIC_TOOLS + WEATHER_TOOLS,
            },
            "customer_success": {
                "display_name": "CustomerSuccessAgent",
                "id": settings.fabric_customer_success_agent_id
                or "customer-success-framework",
                "prompt": (
                    "You are CustomerSuccessAgent focused on customer satisfaction, retention, and growth.\n"
                    "Analyze customer health scores, engagement metrics, churn risk, and expansion opportunities. "
                    "Use Fabric data tools to provide insights on customer lifecycle, NPS scores, support ticket trends, "
                    "and product adoption. Provide actionable recommendations to improve customer outcomes and drive retention."
                ),
                "tools": FABRIC_TOOLS,
            },
            "operations_excellence": {
                "display_name": "OperationsExcellenceAgent",
                "id": settings.fabric_operations_excellence_agent_id
                or "operations-excellence-framework",
                "prompt": (
                    "You are OperationsExcellenceAgent dedicated to operational efficiency and process optimization.\n"
                    "Monitor KPIs related to productivity, quality, cost management, and process improvements. "
                    "Use Fabric data to analyze operational bottlenecks, resource utilization, cycle times, and efficiency metrics. "
                    "Provide data-driven recommendations to streamline operations, reduce waste, and enhance overall performance."
                ),
                "tools": FABRIC_TOOLS,
            },
        }

        # Orchestrator configuration
        self.orchestrator_prompt = (
            "You are RetailAssistantOrchestrator. Analyze each user request, decide whether to answer directly "
            "or to call one of the specialist functions. Available specialists:\n"
            "- SalesAssistant: revenue insights, sales trends, top products\n"
            "- OperationsAssistant: real-time metrics, system health, uptime\n"
            "- AnalyticsAssistant: business intelligence, patterns, KPIs\n"
            "- FinancialAdvisor: ROI, forecasting, profitability\n"
            "- CustomerSupportAssistant: troubleshooting, customer service\n"
            "- OperationsCoordinator: logistics, supply chain, weather impacts\n"
            "- CustomerSuccessAgent: customer health, retention, engagement, churn risk\n"
            "- OperationsExcellenceAgent: efficiency, process optimization, productivity KPIs\n\n"
            "When a specialist is used, summarize their findings, cite the specialist by name, and add your own "
            "brief recommendation. If no specialist is required, answer confidently using available context."
        )

        # Define orchestrator tool functions as methods
        # These will be called by the Agent Framework when the LLM decides to use them
        async def call_sales_specialist(question: str) -> str:
            """Route question to SalesAssistant specialist."""
            return await self._route_to_specialist("sales", question)

        async def call_operations_specialist(question: str) -> str:
            """Route question to OperationsAssistant specialist."""
            return await self._route_to_specialist("operations", question)

        async def call_analytics_specialist(question: str) -> str:
            """Route question to AnalyticsAssistant specialist."""
            return await self._route_to_specialist("analytics", question)

        async def call_financial_specialist(question: str) -> str:
            """Route question to FinancialAdvisor specialist."""
            return await self._route_to_specialist("financial", question)

        async def call_support_specialist(question: str) -> str:
            """Route question to CustomerSupportAssistant specialist."""
            return await self._route_to_specialist("support", question)

        async def call_operations_coordinator(question: str) -> str:
            """Route question to OperationsCoordinator specialist."""
            return await self._route_to_specialist("coordinator", question)

        async def call_customer_success_specialist(question: str) -> str:
            """Route question to CustomerSuccessAgent specialist."""
            return await self._route_to_specialist("customer_success", question)

        async def call_operations_excellence_specialist(question: str) -> str:
            """Route question to OperationsExcellenceAgent specialist."""
            return await self._route_to_specialist("operations_excellence", question)

        # Store functions for tool execution
        self.orchestrator_functions = {
            "call_sales_specialist": call_sales_specialist,
            "call_operations_specialist": call_operations_specialist,
            "call_analytics_specialist": call_analytics_specialist,
            "call_financial_specialist": call_financial_specialist,
            "call_support_specialist": call_support_specialist,
            "call_operations_coordinator": call_operations_coordinator,
            "call_customer_success_specialist": call_customer_success_specialist,
            "call_operations_excellence_specialist": call_operations_excellence_specialist,
        }

        # Register tools with Agent Framework - pass actual functions
        self.orchestrator_tools = [
            call_sales_specialist,
            call_operations_specialist,
            call_analytics_specialist,
            call_financial_specialist,
            call_support_specialist,
            call_operations_coordinator,
            call_customer_success_specialist,
            call_operations_excellence_specialist,
        ]

        self._tool_to_agent = {
            "call_sales_specialist": "sales",
            "call_operations_specialist": "operations",
            "call_analytics_specialist": "analytics",
            "call_financial_specialist": "financial",
            "call_support_specialist": "support",
            "call_operations_coordinator": "coordinator",
            "call_customer_success_specialist": "customer_success",
            "call_operations_excellence_specialist": "operations_excellence",
        }

        self.orchestrator_agent_id = (
            settings.fabric_orchestrator_agent_id or "agent-framework-orchestrator"
        )

    @staticmethod
    def _create_credential():
        try:
            return DefaultAzureCredential()
        except Exception:  # pragma: no cover - fallback for local dev
            logger.info(
                "ℹ️ Falling back to AzureCliCredential for Agent Framework client"
            )
            return AzureCliCredential()

    async def _route_to_specialist(self, specialist_type: str, question: str) -> str:
        """Route a question to a specific specialist and return their response."""
        logger.info(f"🎯 Routing to {specialist_type} specialist: {question[:100]}")

        # Create a simple message history with system prompt and user question
        profile = self.specialist_profiles.get(specialist_type)
        if not profile:
            return f"Error: Unknown specialist type '{specialist_type}'"

        # Enhanced system prompt to include formatting instructions
        enhanced_prompt = (
            profile["prompt"]
            + "\n\nWhen providing data, structure your response with:\n"
            "- Key metrics first (e.g., 'Total Revenue: $5.2M, Growth: +15%')\n"
            "- Top items in bullet points or lists\n"
            "- Clear section headers\n"
            "- Actionable insights at the end"
        )

        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": question},
        ]

        # Run the specialist WITHOUT tools for now (tools need to be callable functions)
        # The specialist will use its knowledge to answer based on the prompt
        try:
            response_text, _, _ = await self._chat_with_tools(
                messages=messages,
                tools=None,  # TODO: Convert tool schemas to callable functions
                tool_executor=None,
            )

            # Format the response with visual enhancements
            formatted_response = ResponseFormatter.format_specialist_response(
                specialist_name=profile["display_name"],
                response_text=response_text,
                data=None,  # Will add data when tools are enabled
                question=question,
            )

            return formatted_response
        except Exception as e:
            logger.error(f"❌ Error routing to {specialist_type}: {e}")
            return f"Error contacting {specialist_type}: {str(e)}"

    async def chat(
        self,
        *,
        message: str,
        agent_type: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> ChatResult:
        """Process a chat request through the orchestrator or specific specialist."""

        # Store user context for tool execution
        self.current_user_context = user_context

        normalized_type = (agent_type or "").strip().lower()
        if not normalized_type or normalized_type in {
            "sales",
            "orchestrator",
            "auto",
            "default",
        }:
            normalized_type = "orchestrator"

        async with self._lock:
            if not thread_id or thread_id not in self.sessions:
                thread_id = thread_id or str(uuid.uuid4())
                self.sessions[thread_id] = []
            session_history = list(self.sessions[thread_id])

        # Append the user message for this turn
        session_history.append({"role": "user", "content": message})

        if normalized_type == "orchestrator":
            response_text, updated_history, usage = await self._run_orchestrator(
                session_history
            )
            async with self._lock:
                self.sessions[thread_id] = updated_history
            metadata = {"usage": usage} if usage else None
            return ChatResult(
                response=response_text,
                thread_id=thread_id,
                agent_id=self.orchestrator_agent_id,
                run_id=str(uuid.uuid4()),
                metadata=metadata,
            )

        if normalized_type not in self.specialist_profiles:
            raise ValueError(f"Unknown agent type: {agent_type}")

        specialist_key = normalized_type
        specialist_text, specialist_history = await self._run_specialist(
            specialist_key,
            message,
        )

        # Persist simplified conversation (user + specialist reply) for future context
        session_history.extend(specialist_history)
        async with self._lock:
            self.sessions[thread_id] = session_history

        profile = self.specialist_profiles[specialist_key]
        return ChatResult(
            response=specialist_text,
            thread_id=thread_id,
            agent_id=profile["id"],
            run_id=str(uuid.uuid4()),
        )

    async def _run_orchestrator(
        self,
        session_history: List[Message],
    ) -> tuple[str, List[Message], Optional[Dict[str, Any]]]:
        messages: List[Message] = [
            {"role": "system", "content": self.orchestrator_prompt},
            *session_history,
        ]

        response_text, full_history, usage = await self._chat_with_tools(
            messages=messages,
            tools=self.orchestrator_tools,
            tool_executor=self._execute_orchestrator_tool,
        )

        # Remove system message when persisting
        persisted_history = [msg for msg in full_history if msg.get("role") != "system"]
        return response_text, persisted_history, usage

    async def _run_specialist(
        self,
        agent_key: str,
        question: str,
    ) -> tuple[str, List[Message]]:
        profile = self.specialist_profiles[agent_key]
        messages: List[Message] = [
            {"role": "system", "content": profile["prompt"]},
            {"role": "user", "content": question},
        ]

        tool_executor = self._execute_tool_call if profile["tools"] else None
        response_text, history, _ = await self._chat_with_tools(
            messages=messages,
            tools=profile["tools"] if profile["tools"] else None,
            tool_executor=tool_executor,
        )

        # Exclude system message when returning history
        persisted_history = [msg for msg in history if msg.get("role") != "system"]
        return response_text, persisted_history

    async def _chat_with_tools(
        self,
        *,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        tool_executor: Optional[Callable[[Dict[str, Any]], Awaitable[str]]],
        max_iterations: int = 5,
    ) -> tuple[str, List[Message], Optional[Dict[str, Any]]]:
        """Core loop that manages tool calling conversations."""

        history: List[Message] = [self._clone_message(msg) for msg in messages]
        iterations = 0

        while iterations < max_iterations:
            iterations += 1

            # Convert messages to Agent Framework format (string format for simple messages)
            formatted_messages = self._format_messages_for_framework(history)

            assistant_content = ""
            tool_calls: List[Dict[str, Any]] = []
            usage_info: Optional[Dict[str, Any]] = None

            if hasattr(self.client, "get_response"):
                response = await self.client.get_response(
                    messages=formatted_messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else "none",
                )

                last_message = response.messages[-1] if response.messages else None
                if not last_message:
                    raise RuntimeError("No message in response")

                assistant_content = getattr(last_message, "text", "") or ""
                tool_calls = [
                    {
                        "id": getattr(tc, "id", str(uuid.uuid4())),
                        "type": "function",
                        "function": {
                            "name": getattr(tc, "name", ""),
                            "arguments": getattr(tc, "arguments", "{}"),
                        },
                    }
                    for tc in getattr(last_message, "tool_calls", [])
                ]

                if getattr(response, "usage", None):
                    usage_info = {
                        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(
                            response.usage, "completion_tokens", 0
                        ),
                        "total_tokens": getattr(response.usage, "total_tokens", 0),
                    }
            else:
                tool_schemas = self._convert_tools_for_openai(tools)
                payload = await self.client.complete_with_tools(
                    messages=[
                        msg.to_dict() if hasattr(msg, "to_dict") else msg
                        for msg in formatted_messages
                    ],
                    tools=tool_schemas,
                    tool_choice="auto" if tool_schemas else "none",
                )

                choices = (
                    payload.get("choices", []) if isinstance(payload, dict) else []
                )
                message_payload = choices[-1].get("message", {}) if choices else {}

                content_payload = message_payload.get("content")
                if isinstance(content_payload, list):
                    assistant_content = "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content_payload
                    )
                else:
                    assistant_content = content_payload or ""

                tool_calls_payload = message_payload.get("tool_calls") or []
                tool_calls = [
                    {
                        "id": call.get("id") or str(uuid.uuid4()),
                        "type": call.get("type", "function"),
                        "function": call.get("function", {}),
                    }
                    for call in tool_calls_payload
                ]

                usage_payload = (
                    payload.get("usage") if isinstance(payload, dict) else None
                )
                if isinstance(usage_payload, dict):
                    usage_info = {
                        "prompt_tokens": int(usage_payload.get("prompt_tokens", 0)),
                        "completion_tokens": int(
                            usage_payload.get("completion_tokens", 0)
                        ),
                        "total_tokens": int(usage_payload.get("total_tokens", 0)),
                    }

            assistant_message = {
                "role": "assistant",
                "content": assistant_content or "",
            }

            if tool_calls:
                # Tool calls are already in dict format, just assign them
                assistant_message["tool_calls"] = tool_calls

            history.append(assistant_message)

            if tool_calls:
                if not tool_executor:
                    raise RuntimeError(
                        "Tool calls encountered but no executor provided"
                    )
                for call in tool_calls:
                    tool_output = await tool_executor(call)
                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "content": str(tool_output)
                            if tool_output
                            else "Tool execution completed",
                        }
                    )
                continue

            return assistant_content, history, usage_info

        raise RuntimeError("Agent interaction exceeded maximum iterations")

    async def _execute_orchestrator_tool(self, tool_call: Dict[str, Any]) -> str:
        function = tool_call.get("function", {})
        name = function.get("name")
        args_raw = function.get("arguments", "{}")

        try:
            arguments = json.loads(args_raw) if args_raw else {}
        except json.JSONDecodeError:
            arguments = {"question": args_raw}

        agent_key = self._tool_to_agent.get(name)
        if not agent_key:
            logger.error(
                f"❌ Unknown orchestrator tool requested: {name} (available: {list(self._tool_to_agent.keys())})"
            )
            return json.dumps({"error": f"Unknown tool {name}"})

        question = arguments.get("question", "").strip()
        specialist_response, _ = await self._run_specialist(agent_key, question)

        payload = {
            "agent": self.specialist_profiles[agent_key]["display_name"],
            "agent_id": self.specialist_profiles[agent_key]["id"],
            "answer": specialist_response,
        }
        return json.dumps(payload, ensure_ascii=False)

    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        function = tool_call.get("function", {})
        name = function.get("name")
        args_raw = function.get("arguments", "{}")
        try:
            arguments = json.loads(args_raw) if args_raw else {}
        except json.JSONDecodeError:
            arguments = {}

        try:
            # Pass user context to tool execution for RLS filtering
            result = await asyncio.to_thread(
                execute_tool_call,
                name,
                arguments,
                self.current_user_context,  # Pass user context
            )
        except Exception as exc:  # pragma: no cover - surface error to model
            logger.error("❌ Tool '%s' execution failed: %s", name, exc)
            result = {"error": str(exc)}

        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False)
        return str(result)

    @staticmethod
    def _format_messages_for_framework(messages: List[Message]) -> List[ChatMessage]:
        """Convert dict messages to ChatMessage objects expected by Agent Framework."""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Create ChatMessage with TextContent list
            # Agent Framework expects ChatMessage objects with proper structure
            chat_msg = ChatMessage(
                role=role,
                content=[TextContent(text=str(content) if content else "")],
            )

            # Preserve tool_calls for assistant messages
            if role == "assistant" and "tool_calls" in msg:
                chat_msg.tool_calls = msg["tool_calls"]

            # Preserve tool_call_id for tool messages
            if role == "tool" and "tool_call_id" in msg:
                chat_msg.tool_call_id = msg["tool_call_id"]

            formatted.append(chat_msg)

        return formatted

    @staticmethod
    def _convert_tools_for_openai(
        tools: Optional[List[Any]],
    ) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None

        converted: List[Dict[str, Any]] = []
        for tool in tools:
            if isinstance(tool, dict):
                converted.append(tool)
                continue
            if callable(tool):
                name = getattr(tool, "__name__", "tool_function")
                description = inspect.getdoc(tool) or f"Tool function {name}"
                sig = inspect.signature(tool)
                properties: Dict[str, Any] = {}
                required: List[str] = []
                for param_name, param in sig.parameters.items():
                    properties[param_name] = {
                        "type": "string",
                        "description": f"Argument '{param_name}'",
                    }
                    if param.default is inspect._empty:
                        required.append(param_name)
                converted.append(
                    {
                        "type": "function",
                        "function": {
                            "name": name,
                            "description": description,
                            "parameters": {
                                "type": "object",
                                "properties": properties,
                                "required": required,
                            },
                        },
                    }
                )
        return converted or None

    @staticmethod
    def _clone_message(message: Message) -> Message:
        cloned = {key: value for key, value in message.items() if key != "tool_calls"}
        if "tool_calls" in message:
            cloned["tool_calls"] = json.loads(json.dumps(message["tool_calls"]))
        return cloned

    @staticmethod
    def _normalize_assistant_message(message: Dict[str, Any]) -> Message:
        content = message.get("content", "")
        if isinstance(content, list):
            # Azure OpenAI may return list-based content segments
            combined = []
            for item in content:
                if isinstance(item, dict):
                    text_block = item.get("text")
                    if isinstance(text_block, dict):
                        combined.append(text_block.get("value", ""))
                    elif isinstance(text_block, str):
                        combined.append(text_block)
            content_text = "".join(combined)
        else:
            content_text = content or ""

        assistant_message: Message = {
            "role": "assistant",
            "content": content_text,
        }

        tool_calls = message.get("tool_calls")
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls

        return assistant_message


agent_framework_manager = AgentFrameworkManager()
"""Singleton manager used by FastAPI endpoints."""
