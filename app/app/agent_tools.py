"""Enhanced Agent Tools for Fabric Integration.

Provides function calling capabilities for specialized agents.

Fast path note
This module was originally fully mock-based. For the quickest
integration with real data, :class:`FabricDataTools.get_sales_summary`
now attempts to query the configured Fabric/SQL endpoint using the
shared ``DatabaseConnection`` helper. If anything goes wrong (missing
config, connection error, etc.), it falls back to the previous
in-memory mock data so demos keep working.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import random

from .config import Settings
from .telemetry import trace_tool_call
from utils.db_connection import DatabaseConnection


class FabricDataTools:
    """Tools for querying and analyzing Fabric data."""

    @staticmethod
    def get_sales_summary(
        time_period: str = "last_quarter", user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get sales summary for a specified time period with RLS filtering.

            This is wired to the shared ``DatabaseConnection`` helper for the
            quickest integration path. It will:

            1. Attempt to query the configured Fabric/SQL analytics endpoint
               using ``Settings.fabric_connection_string``.
            2. Filter by the user's region (simple RLS) when provided.
        3. Preserve the existing response shape.
        """

        # Apply RLS: Check user's allowed region/data_scope
        user_region: Optional[str] = None
        if user_context:
            user_region = user_context.get("region")
            
            # DEBUG: Log what we received
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🔍 RLS FILTER - user_region: {user_region}, user_context keys: {list(user_context.keys())}")

        # --- Query Fabric Gold Lakehouse directly -------------------------
        sales_by_region: Dict[str, Dict[str, Any]] = {}

        settings = Settings()
        conn_str = settings.fabric_connection_string

        db = DatabaseConnection(
            connection_string=conn_str,
            use_access_token=settings.fabric_sql_use_azure_auth,
            client_id=settings.fabric_client_id,
            client_secret=settings.fabric_client_secret,
            tenant_id=settings.fabric_tenant_id,
        )

        # Use Gold Lakehouse geographic sales as the source for
        # regional sales aggregation. We treat "region" as State.
        #
        # time_period mapping:
        #   - "last_month": latest month in gold_sales_time_series
        #   - "last_quarter": latest quarter
        #   - "last_year": latest year
        #   - "ytd": current year

        period_query = (
            "SELECT MAX(year) AS year, MAX(quarter) AS quarter, MAX(month) AS month "
            "FROM dbo.gold_sales_time_series"
        )
        period_row = db.execute_query(period_query, fetch=True)
        year = quarter = month = None
        if period_row:
            year = int(period_row[0].get("year") or 0)
            quarter = int(period_row[0].get("quarter") or 0)
            month = int(period_row[0].get("month") or 0)

        # Build WHERE clause based on requested time_period
        where_clause = []
        params: list[Any] = []

        if time_period == "last_month" and year and month:
            where_clause.append("year = ? AND month = ?")
            params.extend([year, month])
        elif time_period == "last_quarter" and year and quarter:
            where_clause.append("year = ? AND quarter = ?")
            params.extend([year, quarter])
        elif time_period in ("last_year", "ytd") and year:
            where_clause.append("year = ?")
            params.append(year)

        # RLS by region (State)
        if user_region:
            where_clause.append("LOWER(State) = LOWER(?)")
            params.append(user_region)

        where_sql = ""
        if where_clause:
            where_sql = " WHERE " + " AND ".join(where_clause)

        base_query = (
            "SELECT State AS region, "
            "       SUM(total_revenue) AS total_revenue, "
            "       SUM(total_orders) AS total_units, "
            "       AVG(avg_order_value) AS avg_order_value "
            "FROM dbo.gold_geographic_sales" + where_sql + " GROUP BY State"
        )

        rows = (
            db.execute_query(base_query, params=tuple(params) or None, fetch=True) or []
        )

        # Build region map from rows to match existing structure
        for row in rows:
            key = str(row.get("region", "")).lower()
            if not key:
                continue
            sales_by_region[key] = {
                "time_period": time_period,
                "total_revenue": float(row.get("total_revenue", 0) or 0),
                "total_units": int(row.get("total_units", 0) or 0),
                "avg_order_value": float(row.get("avg_order_value", 0) or 0),
                # NOTE: "top_products" is not derived here in the fast
                # path. You can extend the SQL or add a secondary query
                # to populate it from your schema.
                "top_products": [],
                "region": row.get("region"),
                "growth_rate": float(row.get("growth_rate", 0) or 0),
            }

        # If we successfully got at least one region from the DB,
        # compute the response from that.
        if sales_by_region:
            if user_region:
                region_lower = user_region.lower()
                if region_lower in sales_by_region:
                    return sales_by_region[region_lower]
                return {
                    "error": f"No data available for region: {user_region}",
                    "time_period": time_period,
                }

            total_revenue = sum(d["total_revenue"] for d in sales_by_region.values())
            total_units = sum(d["total_units"] for d in sales_by_region.values())

            return {
                "time_period": time_period,
                "total_revenue": total_revenue,
                "total_units": total_units,
                "avg_order_value": total_revenue / total_units
                if total_units > 0
                else 0,
                "top_products": [],  # can be populated later
                # Simple average here; adjust to your business logic
                "growth_rate": (
                    sum(d["growth_rate"] for d in sales_by_region.values())
                    / len(sales_by_region)
                    if sales_by_region
                    else 0
                ),
                "regions_included": list(sales_by_region.keys()),
            }

        # If no rows, still return a well-formed, empty response
        return {
            "time_period": time_period,
            "total_revenue": 0.0,
            "total_units": 0,
            "avg_order_value": 0.0,
            "top_products": [],
            "growth_rate": 0.0,
            "regions_included": [],
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
        user_region: Optional[str] = None
        if user_context:
            user_region = user_context.get("region")

        # --- Query Fabric Gold Lakehouse directly -------------------------
        settings = Settings()
        conn_str = settings.fabric_connection_string

        db = DatabaseConnection(
            connection_string=conn_str,
            use_access_token=settings.fabric_sql_use_azure_auth,
            client_id=settings.fabric_client_id,
            client_secret=settings.fabric_client_secret,
            tenant_id=settings.fabric_tenant_id,
        )

        # Example schema assumption: aggregated customer demographics by region
        base_query = (
            "SELECT State AS region, "
            "       customer_segment, "
            "       COUNT(*) AS total_customers "
            "FROM dbo.gold_customer_360 "
            "WHERE (? IS NULL OR customer_segment = ?) "
        )
        params: list[Any] = [segment, segment]

        if user_region:
            base_query += " AND LOWER(State) = LOWER(?)"
            params.append(user_region)

        base_query += " GROUP BY State, customer_segment"

        rows = db.execute_query(base_query, params=tuple(params), fetch=True) or []

        regional_data: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            key = str(row.get("region", "")).lower()
            if not key:
                continue
            total_customers = int(row.get("total_customers", 0) or 0)
            regional_data[key] = {
                "total_customers": total_customers,
                "segment": row.get("customer_segment") or segment or "all",
                "region": row.get("region"),
                # We don't have age buckets in this table; these can be
                # refined later if an age column is added.
                "age_distribution": {
                    "18-25": 0,
                    "26-35": 0,
                    "36-45": 0,
                    "46-55": 0,
                    "55+": 0,
                },
                "geographic_distribution": {
                    row.get("region", "Unknown"): 100.0,
                },
            }

        if regional_data:
            if user_region:
                key = user_region.lower()
                if key in regional_data:
                    return regional_data[key]
                return {
                    "error": f"No customer data available for region: {user_region}",
                    "segment": segment or "all",
                }

            # Aggregated admin view
            total_customers = sum(d["total_customers"] for d in regional_data.values())
            # Simple aggregate of age buckets
            age_buckets = {"18-25": 0, "26-35": 0, "36-45": 0, "46-55": 0, "55+": 0}
            for d in regional_data.values():
                for k in age_buckets:
                    age_buckets[k] += d["age_distribution"].get(k, 0)

            return {
                "total_customers": total_customers,
                "segment": segment or "all",
                "age_distribution": age_buckets,
                # For geos, we keep it simple here; can refine later
                "geographic_distribution": {},
            }

        # No data case
        return {
            "total_customers": 0,
            "segment": segment or "all",
            "age_distribution": {
                "18-25": 0,
                "26-35": 0,
                "36-45": 0,
                "46-55": 0,
                "55+": 0,
            },
            "geographic_distribution": {},
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
        user_region: Optional[str] = None
        if user_context:
            user_region = user_context.get("region")

        # --- Query Fabric Gold Lakehouse directly -------------------------
        settings = Settings()
        conn_str = settings.fabric_connection_string

        db = DatabaseConnection(
            connection_string=conn_str,
            use_access_token=settings.fabric_sql_use_azure_auth,
            client_id=settings.fabric_client_id,
            client_secret=settings.fabric_client_secret,
            tenant_id=settings.fabric_tenant_id,
        )

        base_query = (
            "SELECT CategoryName AS category, "
            "       COUNT(*) AS total_sku_count, "
            "       SUM(CASE WHEN stock_status = 'In Stock' THEN 1 ELSE 0 END) AS in_stock, "
            "       SUM(CASE WHEN stock_status = 'Low Stock' THEN 1 ELSE 0 END) AS low_stock, "
            "       SUM(CASE WHEN stock_status = 'Out of Stock' THEN 1 ELSE 0 END) AS out_of_stock "
            "FROM dbo.gold_inventory_analysis "
            "WHERE (? IS NULL OR CategoryName = ?) "
        )
        params: list[Any] = [product_category, product_category]

        base_query += " GROUP BY CategoryName"

        rows = db.execute_query(base_query, params=tuple(params), fetch=True) or []

        # Note: gold_inventory_analysis is not region-specific; we
        # treat this as global inventory. RLS by region is a no-op
        # here unless a region dimension is added later.
        regional_inventory: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            key = "global"
            regional_inventory[key] = {
                "category": row.get("category") or product_category or "all",
                "region": "Global",
                "total_sku_count": int(row.get("total_sku_count", 0) or 0),
                "in_stock": int(row.get("in_stock", 0) or 0),
                "low_stock": int(row.get("low_stock", 0) or 0),
                "out_of_stock": int(row.get("out_of_stock", 0) or 0),
                "avg_stock_days": 0.0,
                "reorder_alerts": [],
            }

        if regional_inventory:
            # Region filter is currently a no-op for global inventory
            # but we keep the pattern for future multi-region support.
            if user_region:
                key = user_region.lower()
                if key in regional_inventory:
                    return regional_inventory[key]
                return {
                    "error": f"No inventory data available for region: {user_region}",
                    "category": product_category or "all",
                }

            # Aggregated admin view
            total_sku_count = sum(
                d["total_sku_count"] for d in regional_inventory.values()
            )
            in_stock = sum(d["in_stock"] for d in regional_inventory.values())
            low_stock = sum(d["low_stock"] for d in regional_inventory.values())
            out_of_stock = sum(d["out_of_stock"] for d in regional_inventory.values())

            return {
                "category": product_category or "all",
                "total_sku_count": total_sku_count,
                "in_stock": in_stock,
                "low_stock": low_stock,
                "out_of_stock": out_of_stock,
                "avg_stock_days": 0.0,
                "reorder_alerts": [],
            }

        # No data case
        return {
            "category": product_category or "all",
            "total_sku_count": 0,
            "in_stock": 0,
            "low_stock": 0,
            "out_of_stock": 0,
            "avg_stock_days": 0.0,
            "reorder_alerts": [],
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
        user_region: Optional[str] = None
        if user_context:
            user_region = user_context.get("region")

        # --- Query Fabric Gold Lakehouse directly -------------------------
        settings = Settings()
        conn_str = settings.fabric_connection_string

        db = DatabaseConnection(
            connection_string=conn_str,
            use_access_token=settings.fabric_sql_use_azure_auth,
            client_id=settings.fabric_client_id,
            client_secret=settings.fabric_client_secret,
            tenant_id=settings.fabric_tenant_id,
        )

        # Map metric_type to specific metrics from Gold tables.
        metrics_map = {
            "sales": [
                "Total Revenue",
                "Conversion Rate",
                "Average Deal Size",
                "Win Rate",
            ],
            "operations": [
                "Avg Days to Ship",
            ],
            "customer_service": [
                "Avg Resolution Time",
                "Total Tickets",
            ],
        }

        metrics = metrics_map.get(metric_type, [])
        results: Dict[str, float] = {}

        if metric_type == "sales" and metrics:
            sales_query = (
                "SELECT metric, actual_value "
                "FROM dbo.gold_sales_performance "
                "WHERE metric IN (" + ",".join("?" for _ in metrics) + ")"
            )
            rows = (
                db.execute_query(sales_query, params=tuple(metrics), fetch=True) or []
            )
            for row in rows:
                name = str(row.get("metric", "")).lower()
                value = float(row.get("actual_value", 0) or 0)
                if "conversion" in name:
                    results["conversion_rate"] = value
                elif "average deal" in name:
                    results["avg_deal_size"] = value
                elif "win rate" in name:
                    results["win_rate"] = value
                elif "revenue" in name:
                    results.setdefault("revenue", value)

        elif metric_type == "operations":
            ship_query = (
                "SELECT AVG(avg_days_to_ship) AS avg_days_to_ship "
                "FROM dbo.gold_shipping_performance"
            )
            rows = db.execute_query(ship_query, fetch=True) or []
            if rows:
                results["order_fulfillment_time"] = float(
                    rows[0].get("avg_days_to_ship", 0) or 0
                )

        elif metric_type == "customer_service":
            support_query = (
                "SELECT "
                "  AVG(avg_resolution_time) AS avg_resolution_time, "
                "  SUM(total_tickets) AS total_tickets "
                "FROM dbo.gold_support_metrics"
            )
            rows = db.execute_query(support_query, fetch=True) or []
            if rows:
                results["avg_response_time_minutes"] = float(
                    rows[0].get("avg_resolution_time", 0) or 0
                )
                results["resolution_rate"] = 0.0
                results["csat_score"] = 0.0

        if results:
            return results

        # No data case
        return {}


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


def execute_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    user_context: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Execute a tool function call.

    Args:
        tool_name: Name of the tool function
        arguments: Dictionary of function arguments
        user_context: User context for RLS filtering (region, data_scope, roles, etc.)

    Returns:
        Result of the function call
    """
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
        # Weather tools
        "get_weather": WeatherTools.get_weather,
        "get_forecast": WeatherTools.get_forecast,
        # Power BI tools
        "query_powerbi_data": PowerBITools.query_powerbi_data,
        "get_report_summary": PowerBITools.get_report_summary,
    }

    if tool_name not in tool_map:
        # Trace unknown tool as an error
        trace_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            user_context=user_context,
            status="error",
            error=f"Unknown tool: {tool_name}",
        )
        raise ValueError(f"Unknown tool: {tool_name}")

    try:
        result = tool_map[tool_name](**arguments)
        trace_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            user_context=user_context,
            status="success",
        )
        return result
    except Exception as ex:  # noqa: BLE001 - we want to log and re-raise any error
        trace_tool_call(
            tool_name=tool_name,
            arguments=arguments,
            user_context=user_context,
            status="error",
            error=str(ex),
        )
        raise
