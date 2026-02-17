"""
Page Routes

Route handlers for serving HTML pages.
Business logic delegated to services layer.
"""

from pathlib import Path
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

from services.auth_service import AuthService
from config import settings
from utils.logging_config import logger


router = APIRouter()

# Static directory path
static_dir = Path(__file__).parent.parent / "static"


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve landing page with navigation to all apps."""
    # Redirect to chat for now
    return RedirectResponse(url="/chat", status_code=302)


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve interactive chat UI. Authentication enforced server-side if enabled."""
    # Check authentication
    if settings.enable_authentication:
        try:
            await AuthService.check_page_auth(request, settings.enable_authentication)
        except Exception as e:
            # Redirect to login if authentication fails
            if hasattr(e, 'status_code') and e.status_code == 302:
                return RedirectResponse(url="/login", status_code=302)
            raise
    
    # Serve the contoso-sales-chat.html file
    return FileResponse(str(static_dir / "contoso-sales-chat.html"))


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve login page."""
    return FileResponse(str(static_dir / "login.html"))


@router.get("/admin", response_class=HTMLResponse)
async def admin_portal():
    """Serve admin dashboard page."""
    return FileResponse(str(static_dir / "admin.html"))


@router.get("/powerbi", response_class=HTMLResponse)
async def powerbi_page():
    """Serve dedicated Power BI reports page."""
    return FileResponse(str(static_dir / "powerbi.html"))


@router.get("/admin/test-auth", response_class=HTMLResponse)
async def admin_test_auth():
    """Serve authentication test page - Admin only."""
    # TODO: Add admin role check
    return FileResponse(str(static_dir / "test-auth.html"))
