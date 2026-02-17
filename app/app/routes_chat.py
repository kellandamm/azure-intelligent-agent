"""
Chat API Routes

Route handlers for chat interactions with AI agents.
Business logic delegated to ChatService.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, validator

from services.auth_service import AuthService
from services.chat_service import ChatService
from config import settings
from utils.logging_config import logger


router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model with security validation."""

    message: str = Field(..., min_length=1, max_length=4000, description="User message (1-4000 characters)")
    agent_type: str = Field(default="orchestrator", pattern="^[a-z_]+$")
    thread_id: Optional[str] = Field(None, max_length=100)
    
    @validator('message')
    def sanitize_message(cls, v):
        """Sanitize message to prevent injection attacks."""
        # Remove control characters except newlines and tabs
        v = ''.join(char for char in v if ord(char) >= 32 or char in ('\n', '\t'))
        
        # Check for potential prompt injection patterns
        dangerous_patterns = [
            'ignore previous', 'ignore all previous', 'system prompt',
            'admin mode', 'developer mode', 'god mode',
            'override instructions', 'disregard instructions'
        ]
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                logger.warning(f"Potential prompt injection detected: {pattern}")
                raise ValueError(f'Message contains suspicious content: {pattern}')
        
        return v.strip()


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    thread_id: str
    agent_id: str
    run_id: str


@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, req: Request):
    """
    Send a message to an agent and get a response.
    Requires authentication if enabled in settings.
    RLS context is automatically applied for authenticated users.
    """
    user_data = None
    user_id = None
    
    # Check authentication if enabled
    if settings.enable_authentication:
        user_data = await AuthService.verify_request_auth(req, settings.enable_authentication)
        user_id = user_data.get("user_id")
        
        # Set RLS context if enabled
        await ChatService.set_rls_context(req, user_data)
    
    # Process chat message
    result = await ChatService.process_chat_message(
        message=request.message,
        agent_type=request.agent_type,
        thread_id=request.thread_id,
        user_context=user_data,
        user_id=user_id,
        request=req
    )
    
    return ChatResponse(**result)
