from typing import Any, Dict
from app.agent_framework_manager import AgentFrameworkManager

try:
    from app.agent_framework_manager import ConfigurationError
except ImportError:
    class ConfigurationError(RuntimeError):
        pass

agent_backend_manager = AgentFrameworkManager()

class ChatService:
    async def process_chat_message(self, message: str, **kwargs) -> Dict[str, Any]:
        try:
            return await agent_backend_manager.chat(message=message, **kwargs)
        except ConfigurationError as exc:
            return {
                "error": str(exc),
                "status_code": 400,
                "mode": getattr(agent_backend_manager, "chat_mode", "unknown"),
            }

async def process_chat_message(message: str, **kwargs) -> Dict[str, Any]:
    return await ChatService().process_chat_message(message, **kwargs)