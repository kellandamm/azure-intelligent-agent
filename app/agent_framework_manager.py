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
from agent_tools import (
    FABRIC_TOOLS,
    SALES_TOOLS,
    CALCULATION_TOOLS,
    WEATHER_TOOLS,
    SUPPORT_TOOLS,
    execute_tool_call,
)
from utils.logging_config import logger
from app.chart_generator import ResponseFormatter, ChartGenerator


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
        self.user_context: Optional[Dict[str, Any]] = None  # Store user context for RLS

        # Specialist agent definitions
        self.specialist_profiles: Dict[str, Dict[str, Any]] = {
            "sales": {
                "display_name": "SalesAssistant",
                "id": settings.sales_agent_id,
                "prompt": (
                    "You are SalesAssistant with direct access to Fabric lakehouse data via Data Agents. "
                    "Provide revenue insights, top products, and sales trends using clear, metric-driven language. "
                    "When users ask about sales data, query the SalesFact, CustomerDim, and ProductDim tables. "
                    "IMPORTANT: Always query for the most recent data. Use date filters like 'last month', 'current quarter', or 'year 2026' to ensure up-to-date results. "
                    "Data is automatically filtered by the user's authorized region. "
                    "Summaries should highlight key successes and risks, ending with an actionable recommendation."
                ),
                "tools": self._get_data_agent_tools() if settings.enable_data_agents else SALES_TOOLS,
            },
            "operations": {
                "display_name": "OperationsAssistant",
                "id": settings.realtime_agent_id,
                "prompt": (
                    "You are OperationsAssistant with access to operational data in Fabric lakehouse. "
                    "Query InventoryFact, OrderFact, and FulfillmentMetrics tables for real-time operational metrics, "
                    "uptime, and system health. Focus on providing concise readiness summaries and next best actions."
                ),
                "tools": self._get_data_agent_tools(["InventoryFact", "OrderFact", "FulfillmentMetrics"]) if settings.enable_data_agents else FABRIC_TOOLS,
            },
            "analytics": {
                "display_name": "AnalyticsAssistant",
                "id": settings.analytics_agent_id or "analytics-agent-framework",
                "prompt": (
                    "You are AnalyticsAssistant with LIVE access to Microsoft Fabric lakehouse. You can query data RIGHT NOW.\n\n"
                    "🚫 FORBIDDEN RESPONSES:\n"
                    "- 'Suggest segmenting customers using RFM analysis' → NO, DO the analysis\n"
                    "- 'Run a customer segmentation report' → NO, RUN the query yourself\n"
                    "- 'This involves filtering for...' → NO, EXECUTE the filter now\n"
                    "- 'Average order value was $421' without customer names → UNACCEPTABLE\n\n"
                    "✅ REQUIRED BEHAVIOR:\n"
                    "- IMMEDIATELY use data_agent tool when user asks about customers/sales/products\n"
                    "- Return ACTUAL customer names, IDs, and individual spending amounts\n"
                    "- Show row-level detail, not just summary statistics\n"
                    "- Use real numbers from the query, not placeholders\n\n"
                    "EXAMPLE GOOD RESPONSE:\n"
                    "'I found 23 customers who haven't purchased in 90+ days:\n"
                    "1. Acme Corp (ID: 1045) - Last order: 127 days ago - Avg monthly spend: $3,240\n"
                    "2. Beta Industries (ID: 1089) - Last order: 94 days ago - Avg monthly spend: $1,876\n"
                    "[... rest of list]'\n\n"
                    "QUERY APPROACH:\n"
                    "1. IMMEDIATELY query: 'Show CustomerID, CustomerName, MAX(OrderDate) as LastPurchase, SUM(TotalAmount) as TotalSpent, "
                    "COUNT(OrderID) as OrderCount, AVG(TotalAmount) as AvgOrderValue FROM SalesFact JOIN CustomerDim ON CustomerID "
                    "WHERE YEAR(OrderDate) >= 2025 GROUP BY CustomerID, CustomerName HAVING DATEDIFF(day, MAX(OrderDate), GETDATE()) > 90'\n"
                    "2. Present ACTUAL results with customer names\n"
                    "3. Calculate metrics from REAL data (monthly spend = total spend / months between first and last order)\n"
                    "4. Provide specific, actionable insights based on ACTUAL customer details\n\n"
                    "Tables available: SalesFact, InventoryFact, CustomerDim, ProductDim, PerformanceMetrics\n"
                    "🎯 Your job: Query data and show REAL customer details. Not theory, not suggestions - ACTUAL RESULTS."
                ),
                "tools": self._get_data_agent_tools() if settings.enable_data_agents else FABRIC_TOOLS,
            },
            "financial": {
                "display_name": "FinancialAdvisor",
                "id": settings.financial_agent_id or "financial-agent-framework",
                "prompt": (
                    "You are FinancialAdvisor with direct access to Microsoft Fabric lakehouse for financial analysis.\n\n"
                    "You have access to:\n"
                    "1. Real-time inventory and sales data via Data Agents (InventoryFact, SalesFact, ProductDim tables)\n"
                    "2. Financial calculation tools (calculate_roi, forecast_revenue, calculate_carrying_costs)\n\n"
                    "For CARRYING COSTS calculations:\n"
                    "- AUTOMATICALLY query InventoryFact for aged inventory data (items over 60 days)\n"
                    "- Use calculate_carrying_costs tool with the inventory value you retrieve\n"
                    "- Default assumptions: 25% annual carrying cost rate (storage, depreciation, insurance, opportunity cost)\n"
                    "- Break down costs by: storage (8%), depreciation (7%), insurance (3%), obsolescence (4%), opportunity cost (3%)\n"
                    "- Present results with specific products and their individual carrying costs\n\n"
                    "For REVENUE FORECASTS:\n"
                    "- Query SalesFact for recent revenue and growth trends\n"
                    "- Use forecast_revenue with actual historical data\n"
                    "- Include period-by-period breakdowns\n\n"
                    "For ROI CALCULATIONS:\n"
                    "- Query actual investment and return data when available\n"
                    "- Use calculate_roi tool with real numbers\n\n"
                    "IMPORTANT: Always query for current 2026 data. Don't ask users for data you can retrieve automatically. "
                    "Present findings with clear numbers, assumptions, breakdown by category, and actionable financial recommendations."
                ),
                "tools": (self._get_data_agent_tools(["InventoryFact", "SalesFact", "ProductDim", "CustomerDim"]) if settings.enable_data_agents else FABRIC_TOOLS) + CALCULATION_TOOLS,
            },
            "support": {
                "display_name": "CustomerSupportAssistant",
                "id": settings.support_agent_id or "support-agent-framework",
                "prompt": (
                    "You are CustomerSupportAssistant, a friendly, empathetic, and highly capable customer support specialist.\n"
                    "You help customers with account issues, order inquiries, product questions, billing concerns, and general troubleshooting.\n\n"
                    "Your capabilities:\n"
                    "- Search knowledge base for help articles and step-by-step guides\n"
                    "- Look up order status and tracking information\n"
                    "- Create support tickets for complex issues requiring investigation\n"
                    "- Provide quick solutions for common issues\n\n"
                    "Best practices:\n"
                    "1. Always be empathetic and acknowledge the customer's concern\n"
                    "2. Use tools to find accurate information (don't guess)\n"
                    "3. Provide clear, step-by-step instructions\n"
                    "4. Offer multiple solutions when available\n"
                    "5. Escalate complex issues by creating a support ticket\n"
                    "6. Follow up with next steps and contact information\n\n"
                    "Remember: Customer satisfaction is your top priority. Be patient, thorough, and helpful."
                ),
                "tools": SUPPORT_TOOLS,
            },
            "customer_success": {
                "display_name": "CustomerSuccessAgent",
                "id": settings.support_agent_id or "customer-success-framework",
                "prompt": (
                    "You are CustomerSuccessAgent with DIRECT, IMMEDIATE access to Microsoft Fabric lakehouse.\n\n"
                    "🚫 NEVER say: 'data isn't directly available', 'can be calculated', 'need to run a report', 'need to access data'\n"
                    "✅ ALWAYS: Query the data IMMEDIATELY and provide ACTUAL customer lists with real numbers\n\n"
                    "When user asks about churned/inactive/at-risk customers:\n"
                    "1. IMMEDIATELY use your data_agent tool to query SalesFact and CustomerDim\n"
                    "2. Request this exact data: CustomerID, CustomerName, OrderDate, TotalAmount\n"
                    "3. Calculate: days since last purchase, total spend, average order value, purchase frequency\n"
                    "4. Return SPECIFIC customer names and numbers - NOT generic analysis\n\n"
                    "QUERY TEMPLATE (use data_agent tool with this):\n"
                    "'From SalesFact joined with CustomerDim, show me customers whose most recent OrderDate is more than 90 days ago "
                    "but who had multiple purchases before that. Include CustomerID, CustomerName, last OrderDate, "
                    "sum of TotalAmount, count of orders, and average order value. Filter for transactions in 2025-2026.'\n\n"
                    "REQUIRED OUTPUT FORMAT:\n"
                    "✅ Total Customers at Risk: [ACTUAL COUNT from query]\n"
                    "✅ Total Revenue at Stake: $[ACTUAL SUM from query]\n"
                    "✅ Average Customer Value: $[ACTUAL AVG from query]\n\n"
                    "📋 Customer Details: [ACTUAL NAMES AND IDS from query]\n"
                    "1. [REAL Customer Name] (ID: [REAL ID])\n"
                    "   - Last Purchase: [ACTUAL DAYS] days ago ([REAL DATE])\n"
                    "   - Lifetime Revenue: $[REAL AMOUNT]\n"
                    "   - Avg Monthly Spend: $[CALCULATED from real data]\n"
                    "   - Total Orders: [REAL COUNT]\n"
                    "2. [Next customer...]\n\n"
                    "🎯 CRITICAL: You HAVE the data. Query it NOW. Show REAL customer names and numbers. No excuses."
                ),
                "tools": self._get_data_agent_tools(["SalesFact", "CustomerDim", "ProductDim"]) if settings.enable_data_agents else FABRIC_TOOLS,
            },
            "coordinator": {
                "display_name": "OperationsCoordinator",
                "id": settings.operations_agent_id or "operations-coordinator-framework",
                "prompt": (
                    "You are OperationsCoordinator overseeing logistics and supply chain status.\n"
                    "Combine Fabric metrics with weather insights when appropriate to anticipate disruptions."
                ),
                "tools": FABRIC_TOOLS + WEATHER_TOOLS,
            },
            "customer_success": {
                "display_name": "CustomerSuccessAgent",
                "id": settings.customer_success_agent_id or "customer-success-framework",
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
                "id": settings.operations_excellence_agent_id or "operations-excellence-framework",
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
            "- SalesAssistant: revenue insights, sales trends, top products, current sales data\n"
            "- OperationsAssistant: real-time metrics, system health, uptime\n"
            "- AnalyticsAssistant: business intelligence, patterns, KPIs, comparative analysis\n"
            "- FinancialAdvisor: ROI calculations, revenue forecasting, financial projections, growth predictions\n"
            "- CustomerSupportAssistant: troubleshooting, customer service issues\n"
            "- CustomerSuccessAgent: **CHURN ANALYSIS**, at-risk customers, retention, customer lists with spending history\n"
            "- OperationsCoordinator: logistics, supply chain, weather impacts\n"
            "- OperationsExcellenceAgent: efficiency, process optimization, productivity KPIs\n\n"
            "Routing Guidelines:\n"
            "- Use CustomerSuccessAgent for: 'churned customers', 'haven't purchased', 'inactive customers', 'at-risk', 'customer retention', 'days since last purchase'\n"
            "- Use FinancialAdvisor for: 'forecast', 'predict', 'project', 'ROI', 'future revenue', 'growth projections'\n"
            "- Use SalesAssistant for: 'current sales', 'last quarter', 'top products', 'what were sales'\n"
            "- Use AnalyticsAssistant for: 'trends', 'patterns', 'compare', 'analyze' (general business intelligence)\n\n"
            "Row-Level Security (RLS) Handling:\n"
            "When a specialist returns data, it is ALREADY filtered for the user's authorized scope (e.g., their region). "
            "If the response indicates a specific region (e.g., 'region': 'East'), that means the user has access to THAT region's data. "
            "When summarizing:\n"
            "- State the data you CAN provide clearly (e.g., 'Here is your East region data')\n"
            "- If the user asked for a different region than what was returned, explain: 'The data shown is for your authorized region'\n"
            "- Never incorrectly state which region the user has access to\n\n"
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

        self.orchestrator_agent_id = settings.orchestrator_agent_id or "agent-framework-orchestrator"

    def _get_data_agent_tools(self, tables: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generate Data Agent tool configuration for querying Fabric lakehouse.
        
        Args:
            tables: Optional list of specific tables to query. If None, allows all tables.
            
        Returns:
            List of tool definitions including Data Agent configuration
        """
        if not settings.enable_data_agents:
            logger.warning("⚠️ Data Agents DISABLED - using mock data tools. Set ENABLE_DATA_AGENTS=true to enable real queries.")
            return FABRIC_TOOLS
        
        if not settings.fabric_lakehouse_id:
            logger.error("❌ Data Agents enabled but FABRIC_LAKEHOUSE_ID not configured! Falling back to mock data.")
            return FABRIC_TOOLS
        
        # Default tables if none specified
        if tables is None:
            tables = ["SalesFact", "InventoryFact", "CustomerDim", "ProductDim", "PerformanceMetrics"]
        
        logger.info(f"✅ Configuring Data Agent tools for tables: {', '.join(tables)}")
        logger.info(f"   Lakehouse: {settings.fabric_lakehouse_name} (ID: {settings.fabric_lakehouse_id[:20]}...)")
        
        data_agent_tool = {
            "type": "fabric_data_agent",
            "fabric": {
                "workspace_id": settings.fabric_workspace_id,
                "lakehouse_id": settings.fabric_lakehouse_id,
                "lakehouse_name": settings.fabric_lakehouse_name,
                "tables": tables,
                "use_user_context": True,  # Apply RLS filtering
                "security_context": {
                    "region": self.user_context.get("region") if self.user_context else None,
                    "roles": self.user_context.get("roles") if self.user_context else [],
                }
            },
            "description": (
                f"Query Microsoft Fabric lakehouse for real-time data. "
                f"Available tables: {', '.join(tables)}. "
                f"Use natural language like: 'show customers who haven't purchased in 90 days with their spending history' or "
                f"'list inventory items over 60 days old with costs'. Data is automatically filtered by user permissions."
            )
        }
        
        # Return Data Agent tool plus any calculation tools if needed
        return [data_agent_tool]

    @staticmethod
    def _create_credential():
        try:
            return DefaultAzureCredential()
        except Exception:  # pragma: no cover - fallback for local dev
            logger.info("ℹ️ Falling back to AzureCliCredential for Agent Framework client")
            return AzureCliCredential()

    async def _route_to_specialist(self, specialist_type: str, question: str) -> str:
        """Route a question to a specific specialist and return their response."""
        logger.info(f"🎯 Routing to {specialist_type} specialist: {question[:100]}")
        
        # Create a simple message history with system prompt and user question
        profile = self.specialist_profiles.get(specialist_type)
        if not profile:
            return f"Error: Unknown specialist type '{specialist_type}'"
        
        # Enhanced system prompt to include formatting instructions
        enhanced_prompt = profile["prompt"] + "\n\nWhen providing data, structure your response with:\n" \
                         "- Key metrics first (e.g., 'Total Revenue: $5.2M, Growth: +15%')\n" \
                         "- Top items in bullet points or lists\n" \
                         "- Clear section headers\n" \
                         "- Actionable insights at the end"
        
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": question},
        ]
        
        # Enable tools for specialists so they can query Fabric data
        tool_executor = self._execute_tool_call if profile["tools"] else None
        try:
            response_text, _, _ = await self._chat_with_tools(
                messages=messages,
                tools=profile["tools"] if profile["tools"] else None,
                tool_executor=tool_executor,
            )
            
            # Format the response with visual enhancements
            formatted_response = ResponseFormatter.format_specialist_response(
                specialist_name=profile["display_name"],
                response_text=response_text,
                data=None,  # Will add data when tools are enabled
                question=question
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
        self.user_context = user_context

        normalized_type = (agent_type or "").strip().lower()
        if not normalized_type or normalized_type in {"sales", "orchestrator", "auto", "default"}:
            normalized_type = "orchestrator"

        async with self._lock:
            if not thread_id or thread_id not in self.sessions:
                thread_id = thread_id or str(uuid.uuid4())
                self.sessions[thread_id] = []
            session_history = list(self.sessions[thread_id])

        # Append the user message for this turn
        session_history.append({"role": "user", "content": message})

        if normalized_type == "orchestrator":
            response_text, updated_history, usage = await self._run_orchestrator(session_history)
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
                        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                        "total_tokens": getattr(response.usage, "total_tokens", 0),
                    }
            else:
                tool_schemas = self._convert_tools_for_openai(tools)
                payload = await self.client.complete_with_tools(
                    messages=[msg.to_dict() if hasattr(msg, "to_dict") else msg for msg in formatted_messages],
                    tools=tool_schemas,
                    tool_choice="auto" if tool_schemas else "none",
                )

                choices = payload.get("choices", []) if isinstance(payload, dict) else []
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

                usage_payload = payload.get("usage") if isinstance(payload, dict) else None
                if isinstance(usage_payload, dict):
                    usage_info = {
                        "prompt_tokens": int(usage_payload.get("prompt_tokens", 0)),
                        "completion_tokens": int(usage_payload.get("completion_tokens", 0)),
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
                    raise RuntimeError("Tool calls encountered but no executor provided")
                for call in tool_calls:
                    tool_output = await tool_executor(call)
                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "content": str(tool_output) if tool_output else "Tool execution completed",
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
            logger.error(f"❌ Unknown orchestrator tool requested: {name} (available: {list(self._tool_to_agent.keys())})")
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
            result = await asyncio.to_thread(execute_tool_call, name, arguments, self.user_context)
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
    def _convert_tools_for_openai(tools: Optional[List[Any]]) -> Optional[List[Dict[str, Any]]]:
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
                        "description": f"Argument '{param_name}'"
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


# Singleton manager used by FastAPI endpoints
agent_framework_manager = AgentFrameworkManager()
