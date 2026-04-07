from typing import Any, Dict
import inspect

from app.agent_framework_manager import AgentFrameworkManager

try:
    from app.agent_framework_manager import ConfigurationError
except ImportError:
    class ConfigurationError(RuntimeError):
        pass


agent_backend_manager = AgentFrameworkManager()


def _filter_supported_kwargs(func, kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return only kwargs supported by func.
    If func accepts **kwargs, pass everything through.
    """
    signature = inspect.signature(func)
    parameters = signature.parameters.values()

    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in parameters):
        return kwargs

    allowed = {
        name
        for name, param in signature.parameters.items()
        if param.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    }

    return {key: value for key, value in kwargs.items() if key in allowed}


class ChatService:
    @staticmethod
    async def set_rls_context(req, user_data) -> None:
        """
        Apply RLS context if the backend supports it.
        """
        if hasattr(agent_backend_manager, "set_rls_context"):
            result = agent_backend_manager.set_rls_context(req, user_data)
            if inspect.isawaitable(result):
                await result

    @staticmethod
    async def process_chat_message(message: str, **kwargs) -> Dict[str, Any]:
        """
        Process a chat message using the configured backend.
        Unsupported kwargs are filtered out before calling the backend.
        """
        try:
            filtered_kwargs = _filter_supported_kwargs(agent_backend_manager.chat, kwargs)
            return await agent_backend_manager.chat(message=message, **filtered_kwargs)
        except ConfigurationError as exc:
            return {
                "error": str(exc),
                "status_code": 400,
                "mode": getattr(agent_backend_manager, "chat_mode", "unknown"),
            }


async def process_chat_message(message: str, **kwargs) -> Dict[str, Any]:
    return await ChatService.process_chat_message(message, **kwargs)