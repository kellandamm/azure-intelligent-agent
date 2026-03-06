"""
Enhanced Agent Tools for Fabric Integration

⚠️ DEPRECATION NOTICE:
This file contains mock data for demonstration purposes.
When Azure AI Foundry Data Agents are enabled (enable_data_agents=True in config.py),
agents will query Microsoft Fabric lakehouse directly instead of using these mock functions.

To enable Data Agents:
1. Set AI_FOUNDRY_PROJECT_ENDPOINT and FABRIC_LAKEHOUSE_ID in .env
2. Set ENABLE_DATA_AGENTS=true
3. Data Agents will automatically query SalesFact, InventoryFact, CustomerDim, etc.

The functions below remain for backward compatibility when Data Agents are not configured.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random


class FabricDataTools:
    """Tools for querying and analyzing Fabric data.
    
    ⚠️ These tools return mock data. When Data Agents are enabled, real queries
    will be executed against Microsoft Fabric lakehouse automatically.
    """

    @staticmethod
    def get_sales_summary(
        time_period: str = "last_quarter", user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get sales summary for a specified time period with RLS filtering.

        Args:
            time_period: Time period to analyze (e.g., "last_quarter", "last_month", "ytd")
            user_context: User context for RLS (region, data_scope, roles)

        Returns:
            Dictionary containing sales summary data filtered by user's allowed scope
        """
        # Apply RLS: Check user's allowed region/data_scope
        user_region = None
        user_data_scope = None

        if user_context:
            user_region = user_context.get("region")
            user_data_scope = user_context.get("data_scope", [])
            
            # DEBUG: Log what we received
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔍 RLS FILTER - user_region: {user_region}, user_context keys: {list(user_context.keys())}")


        # Mock data with regional breakdown - replace with actual Fabric queries
        sales_by_region = {
            "east": {
                "time_period": time_period,
                "total_revenue": 5250000.00,
                "total_units": 12450,
                "avg_order_value": 421.69,
                "region": "East",
                "top_products": [
                    {
                        "name": "Drive Scalable Info-Mediaries",
                        "revenue": 552858.36,
                        "units": 1173,
                    },
                    {
                        "name": "Engineer Visionary Systems",
                        "revenue": 508690.56,
                        "units": 1176,
                    },
                    {
                        "name": "Monetize Collaborative Metrics",
                        "revenue": 413711.32,
                        "units": 1207,
                    },
                ],
                "growth_rate": 15.3,
            },
            "west": {
                "time_period": time_period,
                "total_revenue": 3890000.00,
                "total_units": 9240,
                "avg_order_value": 421.00,
                "region": "West",
                "top_products": [
                    {
                        "name": "Optimize Digital Solutions",
                        "revenue": 410456.78,
                        "units": 875,
                    },
                    {
                        "name": "Streamline Cloud Services",
                        "revenue": 378920.45,
                        "units": 923,
                    },
                    {
                        "name": "Enhance User Experience",
                        "revenue": 312890.12,
                        "units": 1012,
                    },
                ],
                "growth_rate": 12.8,
            },
            "central": {
                "time_period": time_period,
                "total_revenue": 4120000.00,
                "total_units": 10800,
                "avg_order_value": 381.48,
                "region": "Central",
                "top_products": [
                    {
                        "name": "Deploy Enterprise Systems",
                        "revenue": 432100.25,
                        "units": 950,
                    },
                    {
                        "name": "Integrate Business Platforms",
                        "revenue": 395678.90,
                        "units": 1020,
                    },
                    {
                        "name": "Transform Data Analytics",
                        "revenue": 367234.56,
                        "units": 1105,
                    },
                ],
                "growth_rate": 14.1,
            },
        }

        # Filter by user's region if specified
        if user_region:
            region_lower = user_region.lower()
            if region_lower in sales_by_region:
                return sales_by_region[region_lower]
            else:
                return {
                    "error": f"No data available for region: {user_region}",
                    "time_period": time_period,
                }

        # No region restriction - return aggregated data (for admin users)
        total_revenue = sum(data["total_revenue"] for data in sales_by_region.values())
        total_units = sum(data["total_units"] for data in sales_by_region.values())

        return {
            "time_period": time_period,
            "total_revenue": total_revenue,
            "total_units": total_units,
            "avg_order_value": total_revenue / total_units if total_units > 0 else 0,
            "top_products": [
                {
                    "name": "Drive Scalable Info-Mediaries",
                    "revenue": 552858.36,
                    "units": 1173,
                },
                {
                    "name": "Engineer Visionary Systems",
                    "revenue": 508690.56,
                    "units": 1176,
                },
                {
                    "name": "Monetize Collaborative Metrics",
                    "revenue": 413711.32,
                    "units": 1207,
                },
            ],
            "growth_rate": 15.3,
            "regions_included": list(sales_by_region.keys()),
        }

    @staticmethod
    def get_customer_demographics(
        segment: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get customer demographic information with RLS filtering.

        Args:
            segment: Optional customer segment to filter by
            user_context: User context for RLS (region, data_scope, roles)

        Returns:
            Dictionary containing demographic data filtered by user's allowed scope
        """
        # Apply RLS filtering
        user_region = None
        if user_context:
            user_region = user_context.get("region")

        # Regional customer data
        regional_data = {
            "east": {
                "total_customers": 3542,
                "segment": segment or "all",
                "region": "East",
                "age_distribution": {
                    "18-25": 545,
                    "26-35": 1190,
                    "36-45": 941,
                    "46-55": 623,
                    "55+": 243,
                },
                "geographic_distribution": {
                    "Northeast": 52.1,
                    "Southeast": 47.9,
                },
            },
            "west": {
                "total_customers": 2800,
                "segment": segment or "all",
                "region": "West",
                "age_distribution": {
                    "18-25": 445,
                    "26-35": 945,
                    "36-45": 741,
                    "46-55": 523,
                    "55+": 146,
                },
                "geographic_distribution": {
                    "Pacific": 68.3,
                    "Mountain": 31.7,
                },
            },
            "central": {
                "total_customers": 2200,
                "segment": segment or "all",
                "region": "Central",
                "age_distribution": {
                    "18-25": 255,
                    "26-35": 755,
                    "36-45": 659,
                    "46-55": 377,
                    "55+": 154,
                },
                "geographic_distribution": {
                    "Midwest": 72.4,
                    "Plains": 27.6,
                },
            },
        }

        # Filter by user's region
        if user_region:
            region_lower = user_region.lower()
            if region_lower in regional_data:
                return regional_data[region_lower]
            else:
                return {
                    "error": f"No customer data available for region: {user_region}"
                }

        # Aggregated data for admin users
        return {
            "total_customers": 8542,
            "segment": segment or "all",
            "age_distribution": {
                "18-25": 1245,
                "26-35": 2890,
                "36-45": 2341,
                "46-55": 1523,
                "55+": 543,
            },
            "geographic_distribution": {
                "North America": 45.2,
                "Europe": 32.1,
                "Asia Pacific": 18.5,
                "Other": 4.2,
            },
        }

    @staticmethod
    def get_inventory_status(
        product_category: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get current inventory status with RLS filtering.

        Args:
            product_category: Optional category to filter by
            user_context: User context for RLS (region, data_scope, roles)

        Returns:
            Dictionary containing inventory data filtered by user's allowed scope
        """
        # Apply RLS filtering
        user_region = None
        if user_context:
            user_region = user_context.get("region")

        # Regional inventory data
        regional_inventory = {
            "east": {
                "category": product_category or "all",
                "region": "East",
                "total_sku_count": 242,
                "in_stock": 217,
                "low_stock": 19,
                "out_of_stock": 6,
                "avg_stock_days": 36.2,
                "reorder_alerts": [
                    {
                        "product": "Wireless Headphones Pro",
                        "current_stock": 15,
                        "reorder_point": 50,
                    },
                    {
                        "product": "Smart Watch Elite",
                        "current_stock": 8,
                        "reorder_point": 25,
                    },
                ],
            },
            "west": {
                "category": product_category or "all",
                "region": "West",
                "total_sku_count": 189,
                "in_stock": 165,
                "low_stock": 15,
                "out_of_stock": 9,
                "avg_stock_days": 31.8,
                "reorder_alerts": [
                    {
                        "product": "Gaming Console X",
                        "current_stock": 12,
                        "reorder_point": 40,
                    },
                    {
                        "product": "Tablet Pro 12",
                        "current_stock": 6,
                        "reorder_point": 20,
                    },
                ],
            },
            "central": {
                "category": product_category or "all",
                "region": "Central",
                "total_sku_count": 211,
                "in_stock": 189,
                "low_stock": 14,
                "out_of_stock": 8,
                "avg_stock_days": 33.5,
                "reorder_alerts": [
                    {
                        "product": "Laptop Ultra 15",
                        "current_stock": 10,
                        "reorder_point": 30,
                    },
                    {
                        "product": "Wireless Mouse Pro",
                        "current_stock": 7,
                        "reorder_point": 25,
                    },
                ],
            },
        }

        # Filter by user's region
        if user_region:
            region_lower = user_region.lower()
            if region_lower in regional_inventory:
                return regional_inventory[region_lower]
            else:
                return {
                    "error": f"No inventory data available for region: {user_region}"
                }

        # Aggregated data for admin users
        return {
            "category": product_category or "all",
            "total_sku_count": 542,
            "in_stock": 487,
            "low_stock": 42,
            "out_of_stock": 13,
            "avg_stock_days": 34.5,
            "reorder_alerts": [
                {
                    "product": "Wireless Headphones Pro",
                    "current_stock": 15,
                    "reorder_point": 50,
                },
                {
                    "product": "Smart Watch Elite",
                    "current_stock": 8,
                    "reorder_point": 25,
                },
            ],
        }

    @staticmethod
    def get_performance_metrics(
        metric_type: str = "sales", user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for various business areas with RLS filtering.

        Args:
            metric_type: Type of metrics ("sales", "operations", "customer_service")
            user_context: User context for RLS (region, data_scope, roles)

        Returns:
            Dictionary containing performance metrics filtered by user's allowed scope
        """
        # Apply RLS filtering
        user_region = None
        if user_context:
            user_region = user_context.get("region")

        # Regional performance metrics
        regional_metrics = {
            "east": {
                "sales": {
                    "region": "East",
                    "conversion_rate": 3.5,
                    "avg_deal_size": 1320.00,
                    "sales_cycle_days": 16,
                    "win_rate": 45.2,
                },
                "operations": {
                    "region": "East",
                    "order_fulfillment_time": 2.1,
                    "shipping_accuracy": 99.1,
                    "return_rate": 1.8,
                    "customer_satisfaction": 4.7,
                },
                "customer_service": {
                    "region": "East",
                    "avg_response_time_minutes": 7.5,
                    "resolution_rate": 89.3,
                    "escalation_rate": 3.8,
                    "csat_score": 4.6,
                },
            },
            "west": {
                "sales": {
                    "region": "West",
                    "conversion_rate": 2.9,
                    "avg_deal_size": 1180.00,
                    "sales_cycle_days": 20,
                    "win_rate": 39.8,
                },
                "operations": {
                    "region": "West",
                    "order_fulfillment_time": 2.5,
                    "shipping_accuracy": 98.3,
                    "return_rate": 2.4,
                    "customer_satisfaction": 4.5,
                },
                "customer_service": {
                    "region": "West",
                    "avg_response_time_minutes": 9.5,
                    "resolution_rate": 85.3,
                    "escalation_rate": 4.6,
                    "csat_score": 4.4,
                },
            },
            "central": {
                "sales": {
                    "region": "Central",
                    "conversion_rate": 3.2,
                    "avg_deal_size": 1250.00,
                    "sales_cycle_days": 18,
                    "win_rate": 42.5,
                },
                "operations": {
                    "region": "Central",
                    "order_fulfillment_time": 2.3,
                    "shipping_accuracy": 98.7,
                    "return_rate": 2.1,
                    "customer_satisfaction": 4.6,
                },
                "customer_service": {
                    "region": "Central",
                    "avg_response_time_minutes": 8.5,
                    "resolution_rate": 87.3,
                    "escalation_rate": 4.2,
                    "csat_score": 4.5,
                },
            },
        }

        # Filter by user's region
        if user_region:
            region_lower = user_region.lower()
            if region_lower in regional_metrics:
                return regional_metrics[region_lower].get(metric_type, {})
            else:
                return {
                    "error": f"No performance data available for region: {user_region}"
                }

        # Aggregated metrics for admin users
        metrics = {
            "sales": {
                "conversion_rate": 3.2,
                "avg_deal_size": 1250.00,
                "sales_cycle_days": 18,
                "win_rate": 42.5,
            },
            "operations": {
                "order_fulfillment_time": 2.3,
                "shipping_accuracy": 98.7,
                "return_rate": 2.1,
                "customer_satisfaction": 4.6,
            },
            "customer_service": {
                "avg_response_time_minutes": 8.5,
                "resolution_rate": 87.3,
                "escalation_rate": 4.2,
                "csat_score": 4.5,
            },
        }
        return metrics.get(metric_type, {})


class CalculationTools:
    """Mathematical and financial calculation tools."""

    @staticmethod
    def calculate_roi(investment: float, return_amount: float) -> Dict[str, Any]:
        """
        Calculate Return on Investment.

        Args:
            investment: Initial investment amount
            return_amount: Total return amount

        Returns:
            Dictionary containing ROI calculation
        """
        roi = ((return_amount - investment) / investment) * 100
        return {
            "investment": investment,
            "return": return_amount,
            "roi_percentage": round(roi, 2),
            "profit": round(return_amount - investment, 2),
        }

    @staticmethod
    def forecast_revenue(
        current_revenue: float, growth_rate: float, periods: int
    ) -> Dict[str, Any]:
        """
        Forecast future revenue based on growth rate.

        Args:
            current_revenue: Current revenue amount
            growth_rate: Growth rate as percentage
            periods: Number of periods to forecast

        Returns:
            Dictionary containing revenue forecast
        """
        forecasts = []
        revenue = current_revenue

        for period in range(1, periods + 1):
            revenue = revenue * (1 + growth_rate / 100)
            forecasts.append(
                {"period": period, "forecasted_revenue": round(revenue, 2)}
            )

        return {
            "current_revenue": current_revenue,
            "growth_rate": growth_rate,
            "periods": periods,
            "forecasts": forecasts,
            "total_projected": round(
                sum(f["forecasted_revenue"] for f in forecasts), 2
            ),
        }

    @staticmethod
    def calculate_carrying_costs(
        inventory_value: float,
        carrying_rate: float = 25.0,
        time_period_days: int = 365
    ) -> Dict[str, Any]:
        """
        Calculate inventory carrying costs.

        Args:
            inventory_value: Total value of aged inventory
            carrying_rate: Annual carrying cost rate as percentage (default: 25%)
            time_period_days: Number of days inventory has been held (default: 365)

        Returns:
            Dictionary containing carrying cost breakdown
        """
        # Adjust for partial year if needed
        annual_factor = time_period_days / 365.0
        
        # Calculate total carrying cost
        total_cost = inventory_value * (carrying_rate / 100) * annual_factor
        
        # Industry standard breakdown of carrying costs
        breakdown = {
            "storage_costs": round(inventory_value * 0.08 * annual_factor, 2),  # 8% - warehouse, utilities
            "depreciation": round(inventory_value * 0.07 * annual_factor, 2),  # 7% - value deterioration
            "insurance": round(inventory_value * 0.03 * annual_factor, 2),  # 3% - insurance premiums
            "obsolescence": round(inventory_value * 0.04 * annual_factor, 2),  # 4% - risk of becoming outdated
            "opportunity_cost": round(inventory_value * 0.03 * annual_factor, 2),  # 3% - capital tied up
        }
        
        return {
            "inventory_value": inventory_value,
            "carrying_rate_percentage": carrying_rate,
            "time_period_days": time_period_days,
            "total_carrying_cost": round(total_cost, 2),
            "cost_breakdown": breakdown,
            "daily_cost": round(total_cost / time_period_days, 2),
            "recommendation": (
                f"Carrying {inventory_value:,.0f} in aged inventory costs approximately ${total_cost:,.2f} over {time_period_days} days. "
                f"Consider liquidation strategies, promotions, or bundling to reduce carrying costs."
            )
        }


class PowerBITools:
    """Power BI integration tools."""

    @staticmethod
    def query_powerbi_data(
        question: str, report_context: str = "general"
    ) -> Dict[str, Any]:
        """
        Query Power BI data using natural language.

        Args:
            question: Natural language question about the data
            report_context: Context or domain of the report

        Returns:
            Dictionary containing query results and insights
        """
        # This would integrate with actual Power BI Q&A API
        # For now, return structured response that agents can work with
        mock_responses = {
            "sales": {
                "top_regions": [
                    "North America: $2.1M",
                    "Europe: $1.8M",
                    "Asia Pacific: $1.2M",
                ],
                "growth_rate": 12.5,
                "key_insights": "Q3 showed 12.5% growth driven by North American market expansion",
            },
            "demographics": {
                "age_groups": {"25-34": 35, "35-44": 28, "45-54": 22, "18-24": 15},
                "key_insights": "Primary customer base is 25-44 age group representing 63% of total customers",
            },
            "performance": {
                "kpis": {
                    "revenue": 8500000,
                    "customers": 15420,
                    "conversion_rate": 3.2,
                },
                "trends": "Steady growth across all metrics with strong customer acquisition",
            },
        }

        # Simple keyword matching for demo purposes
        if any(
            word in question.lower() for word in ["sales", "revenue", "top", "region"]
        ):
            context = "sales"
        elif any(
            word in question.lower() for word in ["demographic", "age", "customer"]
        ):
            context = "demographics"
        else:
            context = "performance"

        response = mock_responses.get(context, mock_responses["performance"])

        return {
            "question": question,
            "context": report_context,
            "data": response,
            "insights": response.get("key_insights", "Data retrieved successfully"),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def get_report_summary(report_type: str = "executive") -> Dict[str, Any]:
        """
        Get executive summary from Power BI reports.

        Args:
            report_type: Type of summary ("executive", "operational", "financial")

        Returns:
            Dictionary containing report summary
        """
        summaries = {
            "executive": {
                "total_revenue": 8500000,
                "growth_rate": 12.5,
                "active_customers": 15420,
                "key_metrics": {
                    "customer_satisfaction": 4.6,
                    "market_share": 23.1,
                    "profit_margin": 18.2,
                },
                "highlights": [
                    "Q3 revenue exceeded targets by 8%",
                    "Customer acquisition up 15% YoY",
                    "Expansion into 3 new markets successful",
                ],
            },
            "operational": {
                "fulfillment_rate": 98.7,
                "avg_delivery_time": 2.3,
                "inventory_turnover": 8.2,
                "quality_score": 4.8,
                "highlights": [
                    "Operational efficiency improved 12%",
                    "Reduced delivery times by 0.5 days",
                    "Zero critical incidents this quarter",
                ],
            },
            "financial": {
                "gross_margin": 42.5,
                "operating_margin": 18.2,
                "cash_flow": 1200000,
                "debt_ratio": 0.23,
                "highlights": [
                    "Gross margin improved 2.1 points",
                    "Strong cash position maintained",
                    "Debt levels remain optimal",
                ],
            },
        }

        return summaries.get(report_type, summaries["executive"])


class WeatherTools:
    """Weather information tools."""

    @staticmethod
    def get_weather(location: str) -> Dict[str, Any]:
        """
        Get current weather for a location.

        Args:
            location: City or location name

        Returns:
            Dictionary containing weather data
        """
        # Mock weather data
        weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy"]
        return {
            "location": location,
            "temperature_f": random.randint(50, 85),
            "temperature_c": random.randint(10, 29),
            "condition": random.choice(weather_conditions),
            "humidity": random.randint(40, 80),
            "wind_speed_mph": random.randint(5, 25),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def get_forecast(location: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a location.

        Args:
            location: City or location name
            days: Number of days to forecast

        Returns:
            Dictionary containing forecast data
        """
        weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy"]
        forecasts = []

        for day in range(days):
            date = datetime.now() + timedelta(days=day)
            forecasts.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "high_f": random.randint(60, 85),
                    "low_f": random.randint(45, 65),
                    "condition": random.choice(weather_conditions),
                    "precipitation_chance": random.randint(0, 60),
                }
            )

        return {"location": location, "forecast_days": days, "forecasts": forecasts}


# Tool definitions for Local Sales Tools with RLS Support
SALES_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": "Get sales summary and metrics for a specified time period with Row-Level Security (RLS) filtering based on user permissions",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_period": {
                        "type": "string",
                        "description": "Time period to analyze (e.g., 'last_quarter', 'last_month', 'ytd')",
                        "enum": ["last_quarter", "last_month", "last_year", "ytd"],
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_demographics",
            "description": "Get customer demographic information with RLS filtering",
            "parameters": {
                "type": "object",
                "properties": {
                    "segment": {
                        "type": "string",
                        "description": "Optional customer segment to filter by",
                    }
                },
                "required": [],
            },
        },
    },
]

# Tool definitions for Azure AI Agents (Fabric - No RLS)
FABRIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": "Get sales summary and metrics for a specified time period from Microsoft Fabric",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_period": {
                        "type": "string",
                        "description": "Time period to analyze (e.g., 'last_quarter', 'last_month', 'ytd')",
                        "enum": ["last_quarter", "last_month", "last_year", "ytd"],
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_demographics",
            "description": "Get customer demographic information from Microsoft Fabric",
            "parameters": {
                "type": "object",
                "properties": {
                    "segment": {
                        "type": "string",
                        "description": "Optional customer segment to filter by",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_inventory_status",
            "description": "Get current inventory status and alerts from Microsoft Fabric",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_category": {
                        "type": "string",
                        "description": "Optional product category to filter by",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_performance_metrics",
            "description": "Get performance metrics for various business areas from Microsoft Fabric",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_type": {
                        "type": "string",
                        "description": "Type of metrics to retrieve",
                        "enum": ["sales", "operations", "customer_service"],
                    }
                },
                "required": ["metric_type"],
            },
        },
    },
]

CALCULATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_roi",
            "description": "Calculate Return on Investment (ROI) percentage",
            "parameters": {
                "type": "object",
                "properties": {
                    "investment": {
                        "type": "number",
                        "description": "Initial investment amount in dollars",
                    },
                    "return_amount": {
                        "type": "number",
                        "description": "Total return amount in dollars",
                    },
                },
                "required": ["investment", "return_amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_revenue",
            "description": "Forecast future revenue based on growth rate",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_revenue": {
                        "type": "number",
                        "description": "Current revenue amount",
                    },
                    "growth_rate": {
                        "type": "number",
                        "description": "Expected growth rate as percentage",
                    },
                    "periods": {
                        "type": "integer",
                        "description": "Number of periods to forecast",
                    },
                },
                "required": ["current_revenue", "growth_rate", "periods"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_carrying_costs",
            "description": "Calculate inventory carrying costs for aged inventory. Includes storage, depreciation, insurance, obsolescence, and opportunity costs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "inventory_value": {
                        "type": "number",
                        "description": "Total value of aged inventory in dollars",
                    },
                    "carrying_rate": {
                        "type": "number",
                        "description": "Annual carrying cost rate as percentage (default: 25% which is industry standard)",
                        "default": 25,
                    },
                    "time_period_days": {
                        "type": "integer",
                        "description": "Number of days inventory has been held (default: 365 for annual)",
                        "default": 365,
                    },
                },
                "required": ["inventory_value"],
            },
        },
    },
]

WEATHER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather conditions for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or location name",
                    }
                },
                "required": ["location"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forecast",
            "description": "Get weather forecast for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City or location name",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to forecast (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["location"],
            },
        },
    },
]

POWERBI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_powerbi_data",
            "description": "Query Power BI data using natural language questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the Power BI data",
                    },
                    "report_context": {
                        "type": "string",
                        "description": "Context or domain of the report (e.g., 'sales', 'operations', 'finance')",
                        "enum": [
                            "sales",
                            "operations",
                            "finance",
                            "marketing",
                            "general",
                        ],
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_report_summary",
            "description": "Get executive summary from Power BI reports",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {
                        "type": "string",
                        "description": "Type of summary to generate",
                        "enum": ["executive", "operational", "financial"],
                    }
                },
                "required": [],
            },
        },
    },
]


class CustomerSupportTools:
    """Tools for customer support operations including tickets, orders, and knowledge base."""

    @staticmethod
    def search_knowledge_base(
        query: str, category: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search the knowledge base for help articles and troubleshooting guides.

        Args:
            query: Search query (e.g., "how to reset password", "return policy")
            category: Optional category filter (e.g., "account", "orders", "products", "billing")
            user_context: User context for RLS filtering

        Returns:
            Dictionary containing relevant knowledge base articles
        """
        # Mock knowledge base data - replace with actual KB/Fabric queries
        kb_articles = {
            "account": [
                {
                    "id": "KB001",
                    "title": "How to Reset Your Password",
                    "category": "Account",
                    "summary": "Step-by-step guide to reset your account password using email verification.",
                    "steps": [
                        "Click 'Forgot Password' on the login page",
                        "Enter your registered email address",
                        "Check your email for the reset link (valid for 1 hour)",
                        "Create a new strong password with at least 8 characters",
                        "Log in with your new password"
                    ],
                    "related_articles": ["KB002", "KB015"],
                    "helpful_count": 1247,
                },
                {
                    "id": "KB002",
                    "title": "Update Account Information",
                    "category": "Account",
                    "summary": "How to change your email, phone number, or shipping address.",
                    "steps": [
                        "Log into your account",
                        "Navigate to 'Account Settings'",
                        "Click 'Edit' next to the field you want to update",
                        "Enter new information and verify with OTP if required",
                        "Save changes"
                    ],
                    "helpful_count": 892,
                },
            ],
            "orders": [
                {
                    "id": "KB010",
                    "title": "Track Your Order",
                    "category": "Orders",
                    "summary": "Real-time order tracking from warehouse to doorstep.",
                    "steps": [
                        "Go to 'My Orders' in your account",
                        "Click on the order number",
                        "View tracking information and estimated delivery",
                        "Sign up for SMS/email notifications",
                        "Contact carrier directly for detailed updates"
                    ],
                    "helpful_count": 2156,
                },
                {
                    "id": "KB011",
                    "title": "Cancel or Modify an Order",
                    "category": "Orders",
                    "summary": "How to cancel or change your order before it ships.",
                    "steps": [
                        "Orders can be modified within 2 hours of placement",
                        "Go to 'My Orders' and select the order",
                        "Click 'Cancel Order' or 'Modify Items'",
                        "If already shipped, you'll need to initiate a return",
                        "Refunds processed within 5-7 business days"
                    ],
                    "helpful_count": 1634,
                },
                {
                    "id": "KB012",
                    "title": "Return & Refund Policy",
                    "category": "Orders",
                    "summary": "30-day return policy for most items with full refund.",
                    "steps": [
                        "Items can be returned within 30 days of delivery",
                        "Products must be unused in original packaging",
                        "Initiate return from 'My Orders' page",
                        "Print prepaid return label",
                        "Drop off at any carrier location",
                        "Refund issued within 5-7 days after we receive the item"
                    ],
                    "policy_exceptions": [
                        "Personalized items are non-returnable",
                        "Electronics must be returned within 14 days",
                        "Software and digital products are non-refundable"
                    ],
                    "helpful_count": 3421,
                },
            ],
            "products": [
                {
                    "id": "KB020",
                    "title": "Product Warranty Information",
                    "category": "Products",
                    "summary": "Warranty coverage and claim process for all products.",
                    "steps": [
                        "Most products include 1-year manufacturer warranty",
                        "Extended warranties available at checkout",
                        "Keep your receipt and product serial number",
                        "Contact manufacturer for warranty claims",
                        "We facilitate the process for defective items"
                    ],
                    "helpful_count": 987,
                },
                {
                    "id": "KB021",
                    "title": "Product Compatibility Check",
                    "category": "Products",
                    "summary": "How to verify product compatibility before purchase.",
                    "helpful_count": 765,
                },
            ],
            "billing": [
                {
                    "id": "KB030",
                    "title": "Payment Methods & Security",
                    "category": "Billing",
                    "summary": "Accepted payment methods and security measures.",
                    "details": [
                        "We accept Visa, Mastercard, American Express, PayPal",
                        "All transactions encrypted with SSL",
                        "3D Secure authentication for added security",
                        "Payment information never stored on our servers",
                        "PCI-DSS compliant payment processing"
                    ],
                    "helpful_count": 1543,
                },
                {
                    "id": "KB031",
                    "title": "Billing Discrepancies",
                    "category": "Billing",
                    "summary": "How to resolve billing issues or disputes.",
                    "helpful_count": 612,
                },
            ],
        }

        # Simple search logic
        query_lower = query.lower()
        results = []

        # Category-specific search
        if category and category.lower() in kb_articles:
            category_articles = kb_articles[category.lower()]
            for article in category_articles:
                if (
                    query_lower in article["title"].lower()
                    or query_lower in article["summary"].lower()
                ):
                    results.append(article)

        # Search all categories if no category specified or no results found
        if not results:
            for cat_articles in kb_articles.values():
                for article in cat_articles:
                    if (
                        query_lower in article["title"].lower()
                        or query_lower in article["summary"].lower()
                    ):
                        results.append(article)

        return {
            "query": query,
            "category": category,
            "total_results": len(results),
            "articles": results[:5] if results else [],
            "suggestion": "Try broadening your search or contact support for personalized help"
            if not results
            else None,
        }

    @staticmethod
    def get_order_status(
        order_id: str, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed order status and tracking information.

        Args:
            order_id: Order identifier
            user_context: User context for RLS filtering

        Returns:
            Dictionary containing order status and tracking details
        """
        # Mock order data - replace with actual order system/Fabric queries
        mock_orders = {
            "ORD-2024-001": {
                "order_id": "ORD-2024-001",
                "status": "Delivered",
                "order_date": "2024-11-15",
                "delivery_date": "2024-11-18",
                "tracking_number": "1Z999AA10123456784",
                "carrier": "UPS",
                "items": [
                    {"name": "Wireless Headphones Pro", "quantity": 1, "price": 129.99},
                    {"name": "USB-C Cable (2m)", "quantity": 2, "price": 14.99},
                ],
                "total": 159.97,
                "shipping_address": "123 Main St, New York, NY 10001",
            },
            "ORD-2024-002": {
                "order_id": "ORD-2024-002",
                "status": "In Transit",
                "order_date": "2024-11-28",
                "estimated_delivery": "2024-12-02",
                "tracking_number": "1Z999AA10123456785",
                "carrier": "FedEx",
                "current_location": "Distribution Center - Chicago, IL",
                "items": [
                    {"name": "Smart Watch Elite", "quantity": 1, "price": 299.99},
                ],
                "total": 299.99,
                "shipping_address": "456 Oak Ave, Los Angeles, CA 90001",
            },
            "ORD-2024-003": {
                "order_id": "ORD-2024-003",
                "status": "Processing",
                "order_date": "2024-11-30",
                "estimated_ship_date": "2024-12-02",
                "items": [
                    {"name": "Laptop Stand Adjustable", "quantity": 1, "price": 49.99},
                    {"name": "Wireless Mouse", "quantity": 1, "price": 29.99},
                ],
                "total": 79.98,
                "shipping_address": "789 Pine Rd, Seattle, WA 98101",
            },
        }

        if order_id in mock_orders:
            return mock_orders[order_id]
        else:
            # Generate a generic order status
            return {
                "order_id": order_id,
                "status": "Not Found",
                "message": "Order not found. Please verify the order ID or contact support.",
                "tip": "Order IDs typically start with 'ORD-' followed by the year.",
            }

    @staticmethod
    def create_support_ticket(
        issue_type: str,
        description: str,
        priority: str = "normal",
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new support ticket for complex issues.

        Args:
            issue_type: Type of issue (e.g., "technical", "billing", "shipping", "product")
            description: Detailed description of the issue
            priority: Priority level (low, normal, high, urgent)
            user_context: User context for ticket assignment

        Returns:
            Dictionary containing ticket confirmation details
        """
        # Generate ticket ID
        ticket_id = f"TKT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

        # Assign to appropriate team based on issue type
        team_assignment = {
            "technical": "Technical Support Team",
            "billing": "Billing & Accounts Team",
            "shipping": "Logistics & Fulfillment Team",
            "product": "Product Support Team",
            "account": "Customer Care Team",
        }

        assigned_team = team_assignment.get(issue_type.lower(), "General Support Team")

        # Calculate SLA response time based on priority
        sla_hours = {"urgent": 2, "high": 8, "normal": 24, "low": 48}
        response_sla = sla_hours.get(priority.lower(), 24)

        return {
            "ticket_id": ticket_id,
            "status": "Open",
            "issue_type": issue_type,
            "priority": priority,
            "assigned_to": assigned_team,
            "created_at": datetime.now().isoformat(),
            "expected_response": f"Within {response_sla} hours",
            "description": description,
            "next_steps": [
                f"Your ticket {ticket_id} has been created and assigned to {assigned_team}",
                f"You'll receive an initial response within {response_sla} hours",
                "Check your email for updates and ticket correspondence",
                "You can view ticket status in 'My Support Tickets'",
            ],
            "contact_methods": {
                "email": "support@company.com",
                "phone": "1-800-SUPPORT",
                "chat": "Available 24/7 for urgent issues",
            },
        }

    @staticmethod
    def get_common_issues(
        category: Optional[str] = None, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get list of common issues and quick resolutions.

        Args:
            category: Optional category to filter (e.g., "login", "payment", "shipping")
            user_context: User context for RLS filtering

        Returns:
            Dictionary containing common issues and solutions
        """
        common_issues = {
            "login": [
                {
                    "issue": "Forgot Password",
                    "solution": "Use 'Forgot Password' link on login page. Reset link sent to registered email.",
                    "success_rate": 98.5,
                },
                {
                    "issue": "Account Locked",
                    "solution": "Account locks after 5 failed login attempts. Wait 15 minutes or reset password.",
                    "success_rate": 95.2,
                },
                {
                    "issue": "Email Not Recognized",
                    "solution": "Verify email spelling. Check if you used social login (Google/Facebook). Try username instead.",
                    "success_rate": 87.3,
                },
            ],
            "payment": [
                {
                    "issue": "Payment Declined",
                    "solution": "Check card details, expiration date, and billing address. Contact your bank if issue persists.",
                    "success_rate": 92.1,
                },
                {
                    "issue": "Refund Status",
                    "solution": "Refunds take 5-7 business days to appear on your statement after processing.",
                    "success_rate": 89.7,
                },
                {
                    "issue": "Promo Code Not Working",
                    "solution": "Check expiration date, minimum purchase requirement, and exclusions. Code is case-sensitive.",
                    "success_rate": 91.4,
                },
            ],
            "shipping": [
                {
                    "issue": "Order Not Arrived",
                    "solution": "Check tracking info. Contact carrier if past delivery date. We'll investigate after carrier deadline.",
                    "success_rate": 85.6,
                },
                {
                    "issue": "Wrong Item Received",
                    "solution": "Initiate return from My Orders. We'll send correct item with free expedited shipping.",
                    "success_rate": 94.8,
                },
                {
                    "issue": "Damaged Package",
                    "solution": "Take photos of damage. Report within 48 hours. We'll send replacement immediately.",
                    "success_rate": 96.2,
                },
            ],
            "product": [
                {
                    "issue": "Product Not Working",
                    "solution": "Check user manual and troubleshooting guide. Verify warranty status for replacement.",
                    "success_rate": 78.9,
                },
                {
                    "issue": "Missing Parts/Accessories",
                    "solution": "Check all packaging materials. Contact support with product SKU for replacement parts.",
                    "success_rate": 92.5,
                },
            ],
        }

        if category and category.lower() in common_issues:
            return {
                "category": category,
                "issues": common_issues[category.lower()],
                "total_issues": len(common_issues[category.lower()]),
            }

        return {
            "all_categories": list(common_issues.keys()),
            "total_issues": sum(len(issues) for issues in common_issues.values()),
            "top_issues_overall": [
                {"issue": "Forgot Password", "category": "login"},
                {"issue": "Payment Declined", "category": "payment"},
                {"issue": "Order Not Arrived", "category": "shipping"},
            ],
            "tip": "Specify a category for detailed issue list",
        }


SUPPORT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search help articles and troubleshooting guides in the knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (e.g., 'reset password', 'return policy', 'shipping time')",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter",
                        "enum": ["account", "orders", "products", "billing", "shipping"],
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up detailed order status and tracking information",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID (format: ORD-YYYY-###)",
                    },
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket for complex issues that need investigation",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "description": "Type of issue",
                        "enum": ["technical", "billing", "shipping", "product", "account"],
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue",
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level",
                        "enum": ["low", "normal", "high", "urgent"],
                        "default": "normal",
                    },
                },
                "required": ["issue_type", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_common_issues",
            "description": "Get list of common issues and their quick resolutions",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter",
                        "enum": ["login", "payment", "shipping", "product"],
                    },
                },
                "required": [],
            },
        },
    },
]


def execute_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    user_context: Optional[Dict[str, Any]] = None,
    execution_mode: str = "local"
) -> Any:
    """
    Execute a tool function call.

    Args:
        tool_name: Name of the tool function
        arguments: Dictionary of function arguments
        user_context: User context for RLS filtering (region, data_scope, roles, etc.)
        execution_mode: "local" or "mcp" - for logging/tracing purposes

    Returns:
        Result of the function call
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log execution mode for demo visibility
    mode_display = "🌐 MCP SERVER" if execution_mode == "mcp" else "💻 LOCAL"
    logger.info(f"⚡ Executing tool '{tool_name}' via {mode_display}")
    
    # Add user_context to arguments for tools that support RLS
    if user_context:
        arguments["user_context"] = user_context

    tool_map = {
        # Fabric tools
        "get_sales_summary": FabricDataTools.get_sales_summary,
        "get_customer_demographics": FabricDataTools.get_customer_demographics,
        "get_inventory_status": FabricDataTools.get_inventory_status,
        "get_performance_metrics": FabricDataTools.get_performance_metrics,
        # Calculation tools
        "calculate_roi": CalculationTools.calculate_roi,
        "forecast_revenue": CalculationTools.forecast_revenue,
        "calculate_carrying_costs": CalculationTools.calculate_carrying_costs,
        # Weather tools
        "get_weather": WeatherTools.get_weather,
        "get_forecast": WeatherTools.get_forecast,
        # Power BI tools
        "query_powerbi_data": PowerBITools.query_powerbi_data,
        "get_report_summary": PowerBITools.get_report_summary,
        # Support tools
        "search_knowledge_base": CustomerSupportTools.search_knowledge_base,
        "get_order_status": CustomerSupportTools.get_order_status,
        "create_support_ticket": CustomerSupportTools.create_support_ticket,
        "get_common_issues": CustomerSupportTools.get_common_issues,
    }

    if tool_name in tool_map:
        result = tool_map[tool_name](**arguments)
        logger.info(f"✅ Tool '{tool_name}' executed successfully via {mode_display}")
        return result
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
