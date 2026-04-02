"""Neutral backend selector for Contoso Sales agent execution.

This module exposes a single shared backend object for the rest of the app while
keeping the implementation names explicit and consistent.
"""
from __future__ import annotations

from config import settings

AGENT_BACKEND_MODE = (
    "foundry_hosted_agents"
    if settings.use_foundry_agents
    else "microsoft_agent_framework"
)

AGENT_BACKEND_LABEL = (
    "Foundry-hosted agents (app-driven routing)"
    if settings.use_foundry_agents
    else "Microsoft Agent Framework (code-orchestrated)"
)

if settings.use_foundry_agents:
    from app.azure_foundry_agent_manager import (
        foundry_hosted_agent_backend_manager as agent_backend_manager,
    )
else:
    from app.agent_framework_manager import (
        microsoft_agent_framework_backend_manager as agent_backend_manager,
    )
