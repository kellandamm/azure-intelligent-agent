# Agent backend naming standard

Use this naming scheme consistently across the Contoso Sales app, docs, logs, screenshots, and demo narration.

## Runtime modes

- **Foundry-hosted agents (app-driven routing)**
  - Config: `USE_FOUNDRY_AGENTS=true`
  - Meaning: the application decides which specialist should handle the request, then calls the selected Microsoft Foundry hosted agent directly.
  - Primary class: `FoundryHostedAgentBackendManager`
  - Shared singleton: `foundry_hosted_agent_backend_manager`

- **Microsoft Agent Framework (code-orchestrated)**
  - Config: `USE_FOUNDRY_AGENTS=false`
  - Meaning: the application uses the local Microsoft Agent Framework orchestration path in code.
  - Primary class: `MicrosoftAgentFrameworkBackendManager`
  - Shared singleton: `microsoft_agent_framework_backend_manager`

## Shared integration names

Use these neutral names in shared plumbing:

- Selector module: `agent_backend_manager.py`
- Shared backend object: `agent_backend_manager`
- Display label: `AGENT_BACKEND_LABEL`
- Mode value: `AGENT_BACKEND_MODE`

## Avoid these ambiguous names

- `agent_framework_manager` in shared code when the active backend might be Microsoft Foundry hosted agents
- `Azure AI Foundry backend` without clarifying whether you mean hosted agents, portal workflows, or app-driven routing
- `the orchestrator routes to specialists` when the application code is actually doing the routing

## Backward compatibility

The backend manager files keep legacy aliases so older imports do not break immediately:

- `AzureAIFoundryAgentManager` remains as an alias for `FoundryHostedAgentBackendManager`
- `AgentFrameworkManager` remains as an alias for `MicrosoftAgentFrameworkBackendManager`
- Older singleton names remain as aliases for the new singleton names
