"""
Unit Tests for Services Layer

Tests the business logic in services/ without HTTP concerns.
Uses pytest and mocking to isolate units of code.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import HTTPException

# Import services to test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from services.auth_service import AuthService
from services.admin_service import AdminService
from services.analytics_service import AnalyticsService


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.mark.asyncio
    async def test_verify_request_auth_disabled(self):
        """Test that auth check returns None when disabled."""
        request = Mock()
        result = await AuthService.verify_request_auth(request, auth_enabled=False)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_verify_request_auth_missing_manager(self):
        """Test that missing auth manager raises 503."""
        request = Mock()
        request.app.state = Mock()
        request.app.state.auth_manager = None
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.verify_request_auth(request, auth_enabled=True)
        
        assert exc_info.value.status_code == 503
    
    @pytest.mark.asyncio
    async def test_verify_request_auth_no_token(self):
        """Test that missing token raises 401."""
        request = Mock()
        request.app.state.auth_manager = Mock()
        request.cookies.get.return_value = None
        request.headers.get.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.verify_request_auth(request, auth_enabled=True)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_verify_request_auth_cookie_token_valid(self):
        """Test successful auth with cookie token."""
        request = Mock()
        auth_manager = Mock()
        auth_manager.verify_jwt_token.return_value = {
            "user_id": 1,
            "username": "testuser"
        }
        request.app.state.auth_manager = auth_manager
        request.cookies.get.return_value = "valid_token"
        
        result = await AuthService.verify_request_auth(request, auth_enabled=True)
        
        assert result["user_id"] == 1
        assert result["username"] == "testuser"
    
    @pytest.mark.asyncio
    async def test_verify_request_auth_header_token_valid(self):
        """Test successful auth with Authorization header."""
        request = Mock()
        auth_manager = Mock()
        auth_manager.verify_jwt_token.return_value = {
            "user_id": 2,
            "username": "apiuser"
        }
        request.app.state.auth_manager = auth_manager
        request.cookies.get.return_value = None
        request.headers.get.return_value = "Bearer header_token"
        
        result = await AuthService.verify_request_auth(request, auth_enabled=True)
        
        assert result["user_id"] == 2
        assert result["username"] == "apiuser"
    
    @pytest.mark.asyncio
    async def test_verify_request_auth_invalid_token(self):
        """Test that invalid token raises 401."""
        request = Mock()
        auth_manager = Mock()
        auth_manager.verify_jwt_token.return_value = None
        request.app.state.auth_manager = auth_manager
        request.cookies.get.return_value = "invalid_token"
        
        with pytest.raises(HTTPException) as exc_info:
            await AuthService.verify_request_auth(request, auth_enabled=True)
        
        assert exc_info.value.status_code == 401


class TestAdminService:
    """Test cases for AdminService."""
    
    def test_get_sanitized_config(self):
        """Test that config is properly sanitized."""
        with patch('services.admin_service.settings') as mock_settings:
            mock_settings.azure_openai_endpoint = "https://test-instance.openai.azure.com"
            mock_settings.azure_openai_deployment = "gpt-4"
            mock_settings.azure_openai_api_version = "2023-05-15"
            mock_settings.fabric_workspace_id = "12345678-1234-1234-1234-123456789012"
            mock_settings.app_port = 8000
            mock_settings.log_level = "INFO"
            mock_settings.enable_tracing = True
            
            result = AdminService.get_sanitized_config()
            
            assert "test-instance" in result["Azure OpenAI Endpoint"]
            assert result["Deployment"] == "gpt-4"
            assert result["Fabric Workspace"] == "12345678..."
            assert result["App Port"] == 8000
            assert result["Environment"] == "Production"
    
    def test_get_system_stats(self):
        """Test that system stats are returned."""
        result = AdminService.get_system_stats()
        
        assert "total_conversations" in result
        assert "active_agents" in result
        assert "avg_response_time" in result
        assert isinstance(result["total_conversations"], int)
    
    def test_get_health_status(self):
        """Test health status response."""
        with patch('services.admin_service.settings') as mock_settings:
            mock_settings.project_endpoint = None
            mock_settings.fabric_workspace_id = "test-workspace"
            mock_settings.enable_authentication = True
            
            result = AdminService.get_health_status()
            
            assert result["status"] == "healthy"
            assert result["framework_mode"] == "Agent Framework"
            assert result["authentication_enabled"] is True


class TestAnalyticsService:
    """Test cases for AnalyticsService."""
    
    def test_check_analyst_permission_admin(self):
        """Test that admin role passes permission check."""
        # Should not raise exception
        AnalyticsService.check_analyst_permission(["admin"])
    
    def test_check_analyst_permission_analyst(self):
        """Test that analyst role passes permission check."""
        # Should not raise exception
        AnalyticsService.check_analyst_permission(["analyst"])
    
    def test_check_analyst_permission_denied(self):
        """Test that user without required role is denied."""
        with pytest.raises(HTTPException) as exc_info:
            AnalyticsService.check_analyst_permission(["user"])
        
        assert exc_info.value.status_code == 403
    
    def test_get_overview_metrics(self):
        """Test that overview metrics are returned."""
        result = AnalyticsService.get_overview_metrics()
        
        assert "total_customers" in result
        assert "total_revenue" in result
        assert "conversion_rate" in result
        assert isinstance(result["total_customers"], int)
        assert isinstance(result["total_revenue"], float)
    
    def test_get_predictive_insights(self):
        """Test that predictive insights are returned."""
        result = AnalyticsService.get_predictive_insights()
        
        assert "insights" in result
        assert isinstance(result["insights"], list)
        assert len(result["insights"]) > 0
        
        # Check first insight structure
        insight = result["insights"][0]
        assert "title" in insight
        assert "description" in insight
        assert "confidence" in insight
        assert "impact" in insight
    
    def test_get_cohort_analysis(self):
        """Test that cohort analysis data is returned."""
        result = AnalyticsService.get_cohort_analysis()
        
        assert "cohorts" in result
        assert isinstance(result["cohorts"], list)
        assert len(result["cohorts"]) > 0
        
        # Check first cohort structure
        cohort = result["cohorts"][0]
        assert "month" in cohort
        assert "customers" in cohort
        assert "retention_rate" in cohort
        assert "revenue" in cohort


# Test configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
