from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.chat_service import agent_backend_manager
from app.agent_framework_manager import ConfigurationError

router = APIRouter(prefix="/api/admin/config", tags=["admin-config"])


class ChatModeUpdateRequest(BaseModel):
    mode: str


@router.get('/chat-mode')
async def get_chat_mode():
    return {
        "mode": agent_backend_manager.chat_mode,
        "use_foundry_agents": agent_backend_manager.use_foundry_agents,
        "client_ready": agent_backend_manager.client is not None,
        "foundry_ready": agent_backend_manager.foundry_client is not None,
    }


@router.post('/chat-mode')
async def set_chat_mode(request: ChatModeUpdateRequest):
    try:
        return await agent_backend_manager.reload_from_settings(request.mode)
    except ConfigurationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
