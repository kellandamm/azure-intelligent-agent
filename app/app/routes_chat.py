"""
Chat API Routes

Route handlers for chat interactions with AI agents.
Business logic delegated to chat service.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from config import settings
from services.auth_service import AuthService
from services.chat_service import process_chat_message
from utils.logging_config import logger

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model with security validation."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message (1-4000 characters)",
    )
    agent_type: str = Field(default="orchestrator", pattern=r"^[a-z_]+$")
    thread_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, value: str) -> str:
        sanitized = "".join(
            char for char in value if ord(char) >= 32 or char in ("\n", "\t")
        ).strip()

        dangerous_patterns = [
            "ignore previous",
            "ignore all previous",
            "system prompt",
            "admin mode",
            "developer mode",
            "god mode",
            "override instructions",
            "disregard instructions",
        ]

        lowered = sanitized.lower()
        for pattern in dangerous_patterns:
            if pattern in lowered:
                logger.warning(
                    "Potential prompt injection detected",
                    extra={"pattern": pattern},
                )
                raise ValueError(f"Message contains suspicious content: {pattern}")

        return sanitized


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    thread_id: str
    agent_id: str
    run_id: str


@router.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, req: Request) -> ChatResponse:
    """
    Send a message to an agent and get a response.
    Requires authentication if enabled in settings.
    """
    user_data = None

    try:
        if settings.enable_authentication:
            user_data = await AuthService.verify_request_auth(
                req, settings.enable_authentication
            )

        result = await process_chat_message(
            message=request.message,
            agent_type=request.agent_type,
            thread_id=request.thread_id,
            user_context=user_data,
            request=req,
        )

        if not isinstance(result, dict):
            logger.error("Chat service returned non-dict response")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response from chat service",
            )

        if "error" in result:
            raise HTTPException(
                status_code=int(
                    result.get("status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
                ),
                detail=result["error"],
            )

        return ChatResponse(**result)

    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Chat request validation failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat request failed",
        ) from exc