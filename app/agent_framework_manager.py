import asyncio
import os
from typing import Any, Dict, Optional, Tuple


class ConfigurationError(RuntimeError):
    """Raised when chat backend configuration is invalid or incomplete."""


class StandardChatClient:
    def __init__(self, endpoint: str, deployment: str):
        self.endpoint = endpoint
        self.deployment = deployment

    async def complete_with_tools(self, message: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0)
        return {
            "text": f"[tool-capable response via {self.deployment}] {message}",
            "history": kwargs.get("history", []),
            "usage": {"mode": "tools", "deployment": self.deployment},
        }

    async def complete(self, message: str, **kwargs) -> Dict[str, Any]:
        await asyncio.sleep(0)
        return {
            "text": f"[standard response via {self.deployment}] {message}",
            "history": kwargs.get("history", []),
            "usage": {"mode": "standard", "deployment": self.deployment},
        }


class AgentFrameworkManager:
    def __init__(self) -> None:
        self.use_foundry_agents = self._is_true(os.getenv("USE_FOUNDRY_AGENTS", "true"))
        self.chat_mode = os.getenv(
            "CHAT_BACKEND_MODE",
            "foundry" if self.use_foundry_agents else "standard",
        ).strip().lower()
        self.client: Optional[StandardChatClient] = None
        self.foundry_client: Optional[Dict[str, Any]] = None
        self._initialize_clients()

    @staticmethod
    def _is_true(value: str) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _initialize_clients(self) -> None:
        self.client = None
        self.foundry_client = None

        if self.chat_mode not in {"foundry", "standard"}:
            raise ConfigurationError("CHAT_BACKEND_MODE must be 'foundry' or 'standard'")

        if self.chat_mode == "foundry":
            project_endpoint = os.getenv("PROJECT_ENDPOINT") or os.getenv("FOUNDRY_PROJECT_ENDPOINT")
            if not project_endpoint:
                raise ConfigurationError(
                    "Foundry mode selected but PROJECT_ENDPOINT or FOUNDRY_PROJECT_ENDPOINT is not configured"
                )
            self.foundry_client = {"endpoint": project_endpoint}

        self.client = self._create_standard_chat_client()

    def _create_standard_chat_client(self) -> Optional[StandardChatClient]:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT") or os.getenv(
            "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"
        )
        if not endpoint or not deployment:
            return None
        return StandardChatClient(endpoint=endpoint, deployment=deployment)

    async def reload_from_settings(self, mode: Optional[str] = None) -> Dict[str, Any]:
        if mode:
            normalized = mode.lower().strip()
            if normalized not in {"foundry", "standard"}:
                raise ConfigurationError("mode must be 'foundry' or 'standard'")
            self.chat_mode = normalized
            self.use_foundry_agents = normalized == "foundry"
            os.environ["CHAT_BACKEND_MODE"] = normalized
            os.environ["USE_FOUNDRY_AGENTS"] = "true" if normalized == "foundry" else "false"

        self._initialize_clients()
        return {
            "chat_mode": self.chat_mode,
            "use_foundry_agents": self.use_foundry_agents,
            "client_ready": self.client is not None,
            "foundry_ready": self.foundry_client is not None,
        }

    async def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        response_text, history, usage = await self._run_orchestrator(message=message, **kwargs)
        return {
            "response": response_text,
            "history": history,
            "usage": usage,
            "mode": self.chat_mode,
        }

    async def _run_orchestrator(self, message: str, **kwargs) -> Tuple[str, list, Dict[str, Any]]:
        if self.chat_mode == "foundry":
            return await self._chat_with_tools(message=message, **kwargs)
        return await self._chat_standard(message=message, **kwargs)

    async def _chat_with_tools(self, message: str, **kwargs) -> Tuple[str, list, Dict[str, Any]]:
        if self.foundry_client is None:
            raise ConfigurationError("Foundry chat mode selected but Foundry client is not initialized")
        if self.client is None:
            raise ConfigurationError(
                "Foundry/tool chat requested but Azure OpenAI client is not initialized"
            )
        payload = await self.client.complete_with_tools(message=message, **kwargs)
        return payload["text"], payload.get("history", []), payload.get("usage", {})

    async def _chat_standard(self, message: str, **kwargs) -> Tuple[str, list, Dict[str, Any]]:
        if self.client is None:
            raise ConfigurationError(
                "Standard chat mode selected but Azure OpenAI client is not configured"
            )
        payload = await self.client.complete(message=message, **kwargs)
        return payload["text"], payload.get("history", []), payload.get("usage", {})
