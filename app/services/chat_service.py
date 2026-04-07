from typing import Any, Dict

from app.agent_framework_manager import AgentFrameworkManager, ConfigurationError


agent_backend_manager = AgentFrameworkManager()


async def process_chat_message(message: str, **kwargs) -> Dict[str, Any]:
    try:
        return await agent_backend_manager.chat(message=message, **kwargs)
    except ConfigurationError as exc:
        return {
            "error": str(exc),
            "status_code": 400,
            "mode": agent_backend_manager.chat_mode,
        }
