"""
Authentication Service

Business logic for user authentication, token verification,
and session management.
"""

from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from utils.auth import AuthManager
from utils.logging_config import logger


class AuthService:
    """Service for handling authentication business logic."""
    
    @staticmethod
    async def verify_request_auth(
        request: Request,
        auth_enabled: bool = True
    ) -> Optional[Dict]:
        """
        Verify authentication for an incoming request.
        
        Args:
            request: FastAPI request object
            auth_enabled: Whether authentication is enabled globally
            
        Returns:
            User data dict if authenticated, None if auth disabled
            
        Raises:
            HTTPException: If authentication fails
        """
        if not auth_enabled:
            return None
            
        # Check if auth manager is available
        if not hasattr(request.app.state, "auth_manager") or request.app.state.auth_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication system not initialized",
            )
        
        auth_manager: AuthManager = request.app.state.auth_manager
        
        # Get token from cookie first (HTTP-only), then fallback to Authorization header
        token = request.cookies.get("auth_token")
        
        if not token:
            # Fallback to Authorization header for API calls
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            token = auth_header.split(" ")[1]
        
        user_data = auth_manager.verify_jwt_token(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"✅ User {user_data.get('username')} authenticated")
        return user_data
    
    @staticmethod
    async def check_page_auth(
        request: Request,
        auth_enabled: bool = True
    ) -> Optional[Dict]:
        """
        Check authentication for page requests (HTML).
        Returns redirect response or user data.
        
        Args:
            request: FastAPI request object
            auth_enabled: Whether authentication is enabled
            
        Returns:
            User data if authenticated, None if auth disabled
            
        Raises:
            HTTPException with redirect if authentication fails
        """
        if not auth_enabled:
            return None
            
        from fastapi.responses import RedirectResponse
        
        # Check for token in cookies
        token = request.cookies.get("auth_token")
        
        # If no cookie, check Authorization header
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        # If still no token, redirect to login
        if not token:
            raise HTTPException(
                status_code=302,
                detail="Redirect to login",
                headers={"Location": "/login"}
            )
        
        # Verify the token
        auth_manager = request.app.state.auth_manager
        user_data = auth_manager.verify_jwt_token(token)
        
        if not user_data:
            # Invalid/expired token - redirect to login and clear cookie
            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("auth_token")
            raise HTTPException(
                status_code=302,
                detail="Redirect to login",
                headers={"Location": "/login", "Set-Cookie": response.headers.get("set-cookie", "")}
            )
        
        logger.info(f"✅ User {user_data.get('username')} accessed page")
        return user_data
