"""
Analytics API Routes

Route handlers for analytics dashboard API endpoints.
Business logic delegated to AnalyticsService.
"""

from fastapi import APIRouter, HTTPException, Request, status

from services.auth_service import AuthService
from services.analytics_service import AnalyticsService
from config import settings
from utils.logging_config import logger


router = APIRouter()


@router.get("/api/analytics/metrics")
async def get_analytics_metrics(req: Request):
    """Get overview metrics for analytics dashboard with RLS filtering."""
    try:
        # Check authentication
        user_data = await AuthService.verify_request_auth(req, settings.enable_authentication)
        
        # Check permissions
        roles = user_data.get("roles", [])
        AnalyticsService.check_analyst_permission(roles)
        
        # Get metrics
        return AnalyticsService.get_overview_metrics()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/predictive-insights")
async def get_predictive_insights(req: Request):
    """Get predictive insights for analytics dashboard."""
    try:
        # Check authentication
        user_data = await AuthService.verify_request_auth(req, settings.enable_authentication)
        
        # Check permissions
        roles = user_data.get("roles", [])
        AnalyticsService.check_analyst_permission(roles)
        
        # Get insights
        return AnalyticsService.get_predictive_insights()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictive insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/analytics/cohort-analysis")
async def get_cohort_analysis(req: Request):
    """Get cohort analysis data for analytics dashboard."""
    try:
        # Check authentication
        user_data = await AuthService.verify_request_auth(req, settings.enable_authentication)
        
        # Check permissions
        roles = user_data.get("roles", [])
        AnalyticsService.check_analyst_permission(roles)
        
        # Get cohort data
        return AnalyticsService.get_cohort_analysis()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cohort analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
