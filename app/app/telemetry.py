"""OpenTelemetry setup and helpers for agent telemetry.

This module configures OpenTelemetry tracing with the Azure Monitor exporter
and exposes helper functions to record tool calls and agent responses.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter


_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

# Configure tracer provider and Azure Monitor exporter if a connection string is present
_tracer_provider = TracerProvider()
trace.set_tracer_provider(_tracer_provider)

if _CONNECTION_STRING:
    _exporter = AzureMonitorTraceExporter(connection_string=_CONNECTION_STRING)
    _tracer_provider.add_span_processor(BatchSpanProcessor(_exporter))

_tracer = trace.get_tracer("agentsdemos.telemetry")


def trace_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    user_context: Optional[Dict[str, Any]] = None,
    status: str = "success",
    error: Optional[str] = None,
) -> None:
    """Create a span for a single tool invocation.

    Args:
        tool_name: Name of the tool function called.
        arguments: Arguments passed to the tool (may be trimmed/redacted).
        user_context: Optional user context dictionary.
        status: "success" or "error".
        error: Optional error message if the tool failed.
    """
    # Avoid leaking sensitive data: only log safe subsets of arguments.
    safe_args: Dict[str, Any] = {
        k: v for k, v in arguments.items() if k != "user_context"
    }

    with _tracer.start_as_current_span("AgentToolCall") as span:
        span.set_attribute("agent.tool.name", tool_name)
        span.set_attribute("agent.tool.status", status)
        span.set_attribute("agent.tool.args", str(safe_args))

        if user_context:
            user_id = user_context.get("user_id")
            region = user_context.get("region")
            span.set_attribute(
                "agent.user.id", str(user_id) if user_id is not None else ""
            )
            if region:
                span.set_attribute("agent.user.region", str(region))

        if error:
            span.set_attribute("agent.tool.error", error)


def trace_agent_response(
    conversation_id: Optional[str],
    user_id: Optional[str],
    response_text: str,
    model_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Create a span for a final agent response.

    Args:
        conversation_id: Identifier for the conversation/session.
        user_id: End-user identifier.
        response_text: Final response text sent to the client.
        model_name: Optional model name used for the response.
        extra: Optional dictionary of additional attributes to attach.
    """
    with _tracer.start_as_current_span("AgentResponse") as span:
        if conversation_id:
            span.set_attribute("agent.conversation.id", conversation_id)
        if user_id:
            span.set_attribute("agent.user.id", user_id)

        span.set_attribute("agent.response.length", len(response_text or ""))

        if model_name:
            span.set_attribute("agent.model.name", model_name)

        if extra:
            for key, value in extra.items():
                span.set_attribute(f"agent.response.{key}", str(value))
