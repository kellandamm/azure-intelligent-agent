"""
Chat Service

Business logic for handling chat interactions with AI agents,
including RLS context management and audit logging.
"""

from typing import Dict, Optional
from datetime import datetime
from fastapi import Request, HTTPException
from pydantic import BaseModel

from app.agent_framework_manager import agent_framework_manager
from app.routes_admin_agents import log_agent_request
from app.telemetry import trace_agent_response
from app.rls_middleware import RLSMiddleware
from utils.db_connection import DatabaseConnection
from utils.logging_config import logger
from config import settings


class ChatService:
    """Service for handling chat business logic."""
    
    @staticmethod
    async def set_rls_context(
        request: Request,
        user_data: Dict
    ) -> None:
        """
        Set Row-Level Security context for the user.
        
        Args:
            request: FastAPI request object
            user_data: User data dictionary from authentication
        """
        if not settings.enable_rls or not user_data:
            return
            
        try:
            rls_middleware: RLSMiddleware = request.app.state.rls_middleware
            db_connection: DatabaseConnection = request.app.state.db_connection
            
            with db_connection.get_connection() as conn:
                await rls_middleware.set_user_context(user_data, conn)
                logger.debug(f"🔐 RLS context set for user: {user_data.get('username')}")
                
                # Get user's data scope for logging
                user_id = user_data.get("user_id")
                data_scope = await rls_middleware.get_user_data_scope(user_id, conn)
                user_data["data_scope"] = data_scope
                logger.info(f"🔍 DEBUG - data_scope: {data_scope}")
                
                # Extract primary region for tool RLS filtering
                territories = data_scope.get("territories", [])
                logger.info(f"🔍 DEBUG - territories extracted: {territories}")
                if territories and len(territories) > 0:
                    primary_territory = territories[0].get("territory", "")
                    logger.info(f"🔍 DEBUG - primary_territory: {primary_territory}")
                    if primary_territory:
                        user_data["region"] = primary_territory
                        logger.info(f"🔐 User region set to: {primary_territory}")
        except Exception as rls_error:
            logger.error(f"❌ Failed to set RLS context: {rls_error}")
            # Continue without RLS - better to allow access than fail
    
    @staticmethod
    async def process_chat_message(
        message: str,
        agent_type: str,
        thread_id: Optional[str],
        user_context: Optional[Dict],
        user_id: Optional[int],
        request: Request
    ) -> Dict:
        """
        Process a chat message through the agent framework.
        
        Args:
            message: User's message
            agent_type: Type of agent to use
            thread_id: Optional thread ID for conversation continuity
            user_context: User context data (including RLS info)
            user_id: User ID for logging
            request: FastAPI request object
            
        Returns:
            Dict with response, thread_id, agent_id, run_id
        """
        start_time = datetime.utcnow()
        agent_key = agent_type or "orchestrator"
        
        try:
            # Call agent framework
            result = await agent_framework_manager.chat(
                message=message,
                agent_type=agent_type,
                thread_id=thread_id,
                user_context=user_context,
            )
            
            # Calculate response time
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            # Log successful request
            if user_id:
                await ChatService._log_successful_request(
                    agent_key=agent_key,
                    message=message,
                    response=result.response,
                    user_id=user_id,
                    response_time=response_time
                )
                
                # Log data access audit
                if settings.enable_audit_logging and user_context:
                    await ChatService._log_data_access(
                        request=request,
                        user_context=user_context,
                        message=message
                    )
            
            # Emit telemetry
            ChatService._trace_response(
                result=result,
                user_id=user_id,
                agent_key=agent_key,
                response_time=response_time
            )
            
            return {
                "response": result.response,
                "thread_id": result.thread_id,
                "agent_id": result.agent_id,
                "run_id": result.run_id,
            }
            
        except Exception as exc:
            # Log failed request
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds()
            
            if user_id:
                try:
                    await log_agent_request(
                        agent_key=agent_key,
                        message=message,
                        response="",
                        user_id=user_id,
                        response_time=response_time,
                        success=False,
                        error=str(exc),
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log error: {log_error}")
            
            logger.error("❌ Chat error: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail=str(exc))
    
    @staticmethod
    async def _log_successful_request(
        agent_key: str,
        message: str,
        response: str,
        user_id: int,
        response_time: float
    ) -> None:
        """Log a successful agent request."""
        try:
            await log_agent_request(
                agent_key=agent_key,
                message=message,
                response=response[:2000],  # Truncate
                user_id=user_id,
                response_time=response_time,
                success=True,
            )
        except Exception as log_error:
            logger.warning(f"Failed to log request: {log_error}")
    
    @staticmethod
    async def _log_data_access(
        request: Request,
        user_context: Dict,
        message: str
    ) -> None:
        """Log data access for audit purposes."""
        try:
            rls_middleware: RLSMiddleware = request.app.state.rls_middleware
            await rls_middleware.log_data_access(
                user_data=user_context,
                access_type="Chat",
                table_accessed="AgentChat",
                query_text=message[:500],  # Truncate for storage
                rows_returned=None,
                request=request,
            )
        except Exception as audit_error:
            logger.warning(f"Failed to log data access audit: {audit_error}")
    
    @staticmethod
    def _trace_response(
        result,
        user_id: Optional[int],
        agent_key: str,
        response_time: float
    ) -> None:
        """Emit telemetry for agent response."""
        model_name: Optional[str] = None
        if result.metadata:
            usage = result.metadata.get("usage")
            if isinstance(usage, dict):
                model_name = usage.get("model")
            elif "model" in result.metadata:
                model_name = result.metadata.get("model")
        
        trace_agent_response(
            conversation_id=result.thread_id,
            user_id=str(user_id) if user_id else None,
            response_text=result.response,
            model_name=model_name,
            extra={
                "agent_id": result.agent_id,
                "agent_type": agent_key,
                "run_id": result.run_id,
                "response_time_sec": response_time,
            },
        )
