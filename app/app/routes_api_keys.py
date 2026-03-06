"""
API Key Management Routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, List
from app.api_keys import api_key_manager
from utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/admin/api-keys", tags=["API Keys"])


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating API key"""
    user_id: int = Field(..., description="User ID to create key for")
    name: str = Field(..., min_length=1, max_length=255, description="Descriptive name for the key")
    expires_days: int = Field(default=90, ge=1, le=365, description="Days until expiration (1-365)")
    scopes: Optional[List[str]] = Field(default=None, description="Permission scopes (e.g., ['chat:read', 'chat:write'])")


class APIKeyResponse(BaseModel):
    """Response model for API key"""
    key: Optional[str] = Field(None, description="API key (shown only on creation)")
    key_id: int
    name: str
    created_at: Optional[str] = None
    expires_at: str
    last_used_at: Optional[str] = None
    usage_count: Optional[int] = 0
    revoked: Optional[bool] = False
    scopes: Optional[List[str]] = None


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new API key for a user (Admin only)
    
    The API key is returned only once. Store it securely!
    
    **Scopes:**
    - `chat:read` - Read chat messages
    - `chat:write` - Send chat messages
    - `analytics:read` - View analytics
    - `analytics:write` - Modify analytics
    - `admin:*` - Full admin access
    """
    try:
        result = await api_key_manager.generate_key(
            user_id=request.user_id,
            name=request.name,
            expires_days=request.expires_days,
            scopes=request.scopes
        )
        
        return APIKeyResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    user_id: Optional[int] = None,
    current_user: dict = Depends(require_admin)
):
    """
    List API keys (Admin only)
    
    If user_id is provided, list keys for that user.
    Otherwise, list all keys (admin view).
    """
    try:
        if user_id:
            keys = await api_key_manager.list_keys(user_id)
        else:
            # TODO: Implement list_all_keys for admin
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Listing all keys not yet implemented. Provide user_id parameter."
            )
        
        return [APIKeyResponse(**key) for key in keys]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    Revoke an API key (Admin only)
    
    Once revoked, the key can no longer be used for authentication.
    """
    try:
        revoked_by = current_user.get("username", "admin")
        await api_key_manager.revoke_key(key_id, revoked_by)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get("/my-keys", response_model=List[APIKeyResponse])
async def list_my_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """
    List API keys for the current user
    
    Users can view their own API keys (but not the actual key values).
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        
        keys = await api_key_manager.list_keys(user_id)
        return [APIKeyResponse(**key) for key in keys]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )
