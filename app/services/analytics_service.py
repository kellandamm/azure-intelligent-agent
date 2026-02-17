"""
Analytics Service

Business logic for analytics operations including
metrics, predictions, and cohort analysis.
"""

from typing import Dict, List
from fastapi import HTTPException
from utils.logging_config import logger


class AnalyticsService:
    """Service for handling analytics business logic."""
    
    @staticmethod
    def check_analyst_permission(roles: List[str]) -> None:
        """
        Check if user has analyst or admin role.
        
        Args:
            roles: List of user roles
            
        Raises:
            HTTPException: If user lacks required permissions
        """
        # Match the logic from routes_analytics.py
        allowed_roles = [
            "admin",
            "administrator",
            "superadmin",
            "data analyst",
            "analyst",
            "poweruser",
        ]
        
        # Ensure roles is a list
        if isinstance(roles, str):
            roles = [r.strip() for r in roles.split(",")]
        
        # Check if any user role matches allowed roles (case-insensitive)
        for role in roles:
            role_lower = str(role).strip().lower()
            if role_lower in allowed_roles:
                logger.info(f"✅ User has analyst permission: {role}")
                return
        
        logger.warning(f"❌ User lacks analyst permission. Roles: {roles}")
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    @staticmethod
    def get_overview_metrics() -> Dict:
        """
        Get overview metrics for analytics dashboard.
        
        TODO: Replace with actual Fabric queries with RLS filtering.
        Currently returns mock data.
        
        Returns:
            Dict of key metrics
        """
        # TODO: Implement actual Fabric queries with RLS filtering
        return {
            "total_customers": 2847,
            "total_revenue": 13260000.00,
            "total_opportunities": 342,
            "avg_deal_value": 38772.00,
            "conversion_rate": 24.5,
            "avg_sales_cycle_days": 45
        }
    
    @staticmethod
    def get_predictive_insights() -> Dict:
        """
        Get predictive insights for analytics dashboard.
        
        TODO: Implement actual ML-based predictions.
        Currently returns mock insights.
        
        Returns:
            Dict with predictive insights list
        """
        # TODO: Implement actual predictive models
        return {
            "insights": [
                {
                    "title": "Revenue Growth Trend",
                    "description": "Based on current trajectory, expect 15.3% revenue growth next quarter",
                    "confidence": 87,
                    "impact": "high"
                },
                {
                    "title": "Customer Churn Risk",
                    "description": "23 high-value customers showing decreased engagement patterns",
                    "confidence": 92,
                    "impact": "medium"
                },
                {
                    "title": "Product Demand Forecast",
                    "description": "Optimize Digital Solutions projected to increase demand by 28%",
                    "confidence": 78,
                    "impact": "high"
                }
            ]
        }
    
    @staticmethod
    def get_cohort_analysis() -> Dict:
        """
        Get cohort analysis data for analytics dashboard.
        
        TODO: Implement actual cohort analysis from data warehouse.
        Currently returns mock data.
        
        Returns:
            Dict with cohort analysis data
        """
        # TODO: Query actual cohort data from Fabric/warehouse
        return {
            "cohorts": [
                {"month": "Q1 2024", "customers": 245, "retention_rate": 78, "revenue": 2450000},
                {"month": "Q2 2024", "customers": 312, "retention_rate": 82, "revenue": 3120000},
                {"month": "Q3 2024", "customers": 387, "retention_rate": 85, "revenue": 3870000},
                {"month": "Q4 2024", "customers": 421, "retention_rate": 87, "revenue": 4210000}
            ]
        }
