from typing import Any, Dict
import inspect
import uuid

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


def _normalize_chat_response(
    backend_result: Dict[str, Any],
    incoming_kwargs: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize backend response to the API contract expected by routes_chat.py.
    """
    thread_id = incoming_kwargs.get("thread_id") or str(uuid.uuid4())
    usage = backend_result.get("usage", {}) or {}
    mode = backend_result.get("mode") or usage.get("mode") or "unknown"

    agent_id = str(
        usage.get("deployment")
        or incoming_kwargs.get("agent_type")
        or mode
        or "agent"
    )
    run_id = str(uuid.uuid4())

    return {
        "response": backend_result.get("response", ""),
        "thread_id": thread_id,
        "agent_id": agent_id,
        "run_id": run_id,
    }


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
            req = kwargs.get("request")
            user_data = kwargs.get("user_context")

            if req is not None:
                await ChatService.set_rls_context(req, user_data)

            filtered_kwargs = _filter_supported_kwargs(agent_backend_manager.chat, kwargs)
            backend_result = await agent_backend_manager.chat(
                message=message,
                **filtered_kwargs,
            )

            if not isinstance(backend_result, dict):
                return {
                    "error": "Chat backend returned an invalid response",
                    "status_code": 500,
                    "mode": getattr(agent_backend_manager, "chat_mode", "unknown"),
                }

            return _normalize_chat_response(backend_result, kwargs)

        except ConfigurationError as exc:
            return {
                "error": str(exc),
                "status_code": 400,
                "mode": getattr(agent_backend_manager, "chat_mode", "unknown"),
            }


async def process_chat_message(message: str, **kwargs) -> Dict[str, Any]:
    return await ChatService.process_chat_message(message, **kwargs)