"""
Services Package

This package contains business logic separated from route handlers.
Services handle the core business operations and data processing,
keeping route handlers thin and focused on HTTP concerns.
"""

# Use absolute imports for Azure App Service compatibility
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.admin_service import AdminService
from services.analytics_service import AnalyticsService

__all__ = [
    "AuthService",
    "ChatService",
    "AdminService",
    "AnalyticsService",
]
