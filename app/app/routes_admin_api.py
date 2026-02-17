"""
Admin API Routes

Route handlers for admin portal API endpoints.
Business logic delegated to AdminService.
"""

from fastapi import APIRouter, Depends, Request

from services.admin_service import AdminService
from services.auth_service import AuthService
from utils.auth import require_admin
from config import settings


router = APIRouter()


@router.get("/api/admin/config")
async def get_admin_config(request: Request, current_user: dict = Depends(require_admin)):
    """Get sanitized configuration for admin portal. Requires admin role."""
    return AdminService.get_sanitized_config()


@router.get("/api/admin/stats")
async def get_admin_stats(request: Request, current_user: dict = Depends(require_admin)):
    """Get real-time statistics for admin dashboard. Requires admin role."""
    return AdminService.get_system_stats()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return AdminService.get_health_status()
