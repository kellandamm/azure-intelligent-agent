"""
Admin Service

Business logic for admin portal operations including
configuration management and statistics.
"""

from typing import Dict
from config import settings


class AdminService:
    """Service for handling admin business logic."""
    
    @staticmethod
    def get_sanitized_config() -> Dict[str, str]:
        """
        Get sanitized configuration for admin portal.
        Hides sensitive information while providing useful context.
        
        Returns:
            Dict of configuration key-value pairs
        """
        return {
            "Azure OpenAI Endpoint": settings.azure_openai_endpoint.replace(
                "https://", ""
            ).split(".")[0]
            + ".openai.azure.com",
            "Deployment": settings.azure_openai_deployment,
            "API Version": settings.azure_openai_api_version,
            "Fabric Workspace": settings.fabric_workspace_id[:8] + "..."
            if settings.fabric_workspace_id
            else "Not configured",
            "App Port": settings.app_port,
            "Log Level": settings.log_level,
            "Tracing Enabled": settings.enable_tracing,
            "Environment": "Development" if settings.log_level == "DEBUG" else "Production",
        }
    
    @staticmethod
    def get_system_stats() -> Dict:
        """
        Get real-time statistics for admin dashboard.
        
        TODO: Implement actual tracking from database/metrics.
        Currently returns mock data.
        
        Returns:
            Dict of system statistics
        """
        # TODO: Query actual metrics from database or monitoring system
        return {
            "total_conversations": 1247,
            "active_agents": 6,
            "avg_response_time": 1.2,
            "token_usage_24h": 42300,
            "success_rate": 98.4,
            "most_used_agent": "AnalyticsAssistant",
        }
    
    @staticmethod
    def get_health_status() -> Dict:
        """
        Build health check response.
        
        Returns:
            Dict with health status and system information
        """
        framework_mode = (
            "Azure AI Foundry"
            if settings.project_endpoint
            else "Agent Framework"
        )
        return {
            "status": "healthy",
            "version": "1.0.0",
            "fabric_workspace": settings.fabric_workspace_id,
            "project_endpoint": settings.project_endpoint or "",
            "framework_mode": framework_mode,
            "authentication_enabled": settings.enable_authentication,
        }
