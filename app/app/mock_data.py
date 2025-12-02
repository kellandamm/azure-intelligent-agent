"""
Mock data generators for Analytics and Sales dashboards
Provides realistic sample data when Fabric tables are empty or unavailable
"""

from datetime import datetime, timedelta
import random
from typing import List, Dict, Any


def generate_mock_products(limit: int = 20) -> List[Dict[str, Any]]:
    """Generate mock product analytics data"""
    products = [
        "Surface Laptop 5",
        "Surface Pro 9",
        "Surface Studio 2+",
        "Xbox Series X",
        "Xbox Series S",
        "Microsoft 365 Business",
        "Azure Cloud Credits",
        "Power BI Pro",
        "Dynamics 365 Sales",
        "Microsoft Teams Phone",
        "Windows 11 Pro",
        "Office 2021",
        "Surface Go 3",
        "Surface Duo 2",
        "Xbox Elite Controller",
        "Surface Pen",
        "Surface Dock 2",
        "Xbox Game Pass Ultimate",
        "Microsoft Defender",
        "Azure DevOps",
    ]

    result = []
    total_revenue = sum([random.uniform(5000, 50000) for _ in range(limit)])

    for i, product in enumerate(products[:limit]):
        revenue = random.uniform(5000, 50000)
        units = random.randint(50, 500)

        result.append(
            {
                "product_name": product,
                "total_revenue": round(revenue, 2),
                "units_sold": units,
                "avg_price": round(revenue / units, 2),
                "market_share": round((revenue / total_revenue) * 100, 2),
                "growth_rate": round(random.uniform(-15, 35), 1),
            }
        )

    # Sort by revenue descending
    result.sort(key=lambda x: x["total_revenue"], reverse=True)
    return result


def generate_mock_sales_reps(limit: int = 15) -> List[Dict[str, Any]]:
    """Generate mock sales rep performance data"""
    reps = [
        "Sarah Johnson",
        "Michael Chen",
        "Emily Rodriguez",
        "David Kim",
        "Jennifer Martinez",
        "Robert Taylor",
        "Lisa Anderson",
        "James Wilson",
        "Maria Garcia",
        "Christopher Lee",
        "Amanda Brown",
        "Daniel Moore",
        "Jessica Davis",
        "Matthew Miller",
        "Ashley Thompson",
    ]

    result = []
    for rep in reps[:limit]:
        deals = random.randint(15, 75)
        revenue = random.uniform(50000, 500000)

        result.append(
            {
                "rep_name": rep,
                "deals_closed": deals,
                "total_revenue": round(revenue, 2),
                "win_rate": round(random.uniform(45, 85), 2),
                "avg_deal_size": round(revenue / deals, 2),
                "quota_attainment": round(random.uniform(60, 135), 2),
            }
        )

    # Sort by revenue descending
    result.sort(key=lambda x: x["total_revenue"], reverse=True)
    return result


def generate_mock_deals(limit: int = 10) -> List[Dict[str, Any]]:
    """Generate mock deals data for 'My Deals' tab"""
    customers = [
        "Contoso Ltd",
        "Fabrikam Inc",
        "Adventure Works",
        "Northwind Traders",
        "Wide World Importers",
        "Tailspin Toys",
        "Proseware Inc",
        "Litware Inc",
        "Fourth Coffee",
        "Coho Winery",
        "Blue Yonder Airlines",
        "Lamna Healthcare",
        "Relecloud",
        "VanArsdel Ltd",
        "Woodgrove Bank",
    ]

    products = [
        "Enterprise License Agreement",
        "Azure Migration Project",
        "Microsoft 365 E5",
        "Dynamics 365 Suite",
        "Power Platform Enterprise",
        "Security & Compliance Bundle",
        "Surface Device Fleet",
        "Azure AI Services",
        "DevOps Transformation",
        "Data Platform Modernization",
    ]

    statuses = [
        {"status": "won", "weight": 3},
        {"status": "negotiating", "weight": 5},
        {"status": "prospecting", "weight": 2},
    ]

    result = []
    for i in range(limit):
        status = random.choices(
            [s["status"] for s in statuses], weights=[s["weight"] for s in statuses]
        )[0]

        value = random.uniform(25000, 500000)
        days_offset = random.randint(0, 90)
        close_date = (datetime.now() + timedelta(days=days_offset)).strftime("%Y-%m-%d")

        result.append(
            {
                "customer": random.choice(customers),
                "product": random.choice(products),
                "value": round(value, 2),
                "status": status,
                "close_date": close_date,
            }
        )

    # Sort by value descending
    result.sort(key=lambda x: x["value"], reverse=True)
    return result


def generate_mock_data_quality() -> List[Dict[str, Any]]:
    """Generate mock data quality metrics"""
    tables = [
        {"name": "Products", "records": 2547, "nulls": 12, "dupes": 3},
        {"name": "Customers", "records": 15432, "nulls": 89, "dupes": 7},
        {"name": "Orders", "records": 45678, "nulls": 156, "dupes": 2},
        {"name": "OrderItems", "records": 128456, "nulls": 234, "dupes": 5},
        {"name": "gold_customer_360", "records": 15430, "nulls": 45, "dupes": 0},
        {"name": "gold_sales_time_series", "records": 1825, "nulls": 0, "dupes": 0},
    ]

    result = []
    for table in tables:
        completeness = ((table["records"] - table["nulls"]) / table["records"]) * 100
        last_updated = (
            datetime.now() - timedelta(hours=random.randint(1, 48))
        ).isoformat()

        result.append(
            {
                "table_name": table["name"],
                "total_records": table["records"],
                "null_count": table["nulls"],
                "duplicate_count": table["dupes"],
                "completeness_score": round(completeness, 2),
                "last_updated": last_updated,
            }
        )

    return result


def generate_mock_customer_segments() -> List[Dict[str, Any]]:
    """Generate mock customer segmentation data"""
    segments = [
        {
            "name": "VIP Customers",
            "customers": 1250,
            "revenue": 2500000,
            "retention": 92,
        },
        {"name": "High Value", "customers": 3450, "revenue": 4200000, "retention": 85},
        {"name": "Regular", "customers": 8750, "revenue": 3100000, "retention": 72},
        {
            "name": "New/Low Activity",
            "customers": 2980,
            "revenue": 450000,
            "retention": 45,
        },
    ]

    result = []
    for seg in segments:
        result.append(
            {
                "segment_name": seg["name"],
                "customer_count": seg["customers"],
                "total_revenue": float(seg["revenue"]),
                "avg_revenue": round(seg["revenue"] / seg["customers"], 2),
                "churn_rate": float(100 - seg["retention"]),
            }
        )

    return result


def generate_mock_top_products_sales(limit: int = 10) -> List[Dict[str, Any]]:
    """Generate mock top products for sales dashboard"""
    products = [
        "Microsoft 365 Business Premium",
        "Azure Consumption",
        "Dynamics 365 Sales",
        "Power BI Premium",
        "Microsoft Teams Rooms",
        "Surface Laptop 5",
        "Windows Server CALs",
        "SQL Server Enterprise",
        "Visual Studio Enterprise",
        "GitHub Enterprise",
        "Microsoft Defender Suite",
        "Azure DevOps Server",
    ]

    result = []
    for product in products[:limit]:
        revenue = random.uniform(25000, 150000)
        prev_revenue = revenue * random.uniform(0.7, 1.3)
        deals = random.randint(5, 45)

        change = ((revenue - prev_revenue) / prev_revenue) * 100

        result.append(
            {
                "name": product,
                "revenue": round(revenue, 2),
                "deals": deals,
                "change": round(change, 1),
            }
        )

    # Sort by revenue descending
    result.sort(key=lambda x: x["revenue"], reverse=True)
    return result
