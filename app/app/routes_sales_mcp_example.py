"""
Example: Using MCP Server in routes_sales.py
This shows how to integrate MCP client for RLS filtering without SESSION_CONTEXT

Add this to your routes_sales.py or create a new routes_sales_mcp.py
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Dict, Any
from app.mcp_client import get_mcp_client
from utils.auth import get_current_user

router = APIRouter(prefix="/api/sales", tags=["Sales with MCP"])

# Flag to enable/disable MCP (can be environment variable)
USE_MCP = os.getenv("ENABLE_MCP", "false").lower() == "true"


@router.get("/deals/detail-mcp")
async def get_deal_details_mcp(
    customer: str,
    product: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Get deal details using MCP Server for RLS filtering.
    This version doesn't require SESSION_CONTEXT in SQL Server.

    Alternative to the original /deals/detail endpoint.
    """
    try:
        if not USE_MCP:
            raise HTTPException(
                status_code=503,
                detail="MCP server not enabled. Set ENABLE_MCP=true"
            )

        # Get MCP client
        mcp = get_mcp_client()

        # Call MCP server with user context
        # MCP server will automatically apply RLS filters
        result = await mcp.get_deal_details(
            customer=customer,
            product=product,
            user_context=current_user
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found or access denied"
            )

        # Extract deal and related deals from MCP response
        deal = result.get("deal")
        related_deals = result.get("related_deals", [])

        # Build customer profile from deal data
        customer_profile = {
            "customer_id": str(deal["CustomerID"]),
            "name": deal["customer_name"],
            "email": deal.get("Email", "email@example.com"),
            "phone": deal.get("Phone", "N/A"),
            "region": deal.get("Region", "Unknown"),
            "segment": deal.get("customer_segment", "Standard"),
            "lifetime_value": float(deal.get("lifetime_value", 0)),
            "account_age_days": int(deal.get("account_age", 0))
        }

        # Generate mock data (same as original endpoint)
        from datetime import datetime, timedelta

        timeline = [
            {
                "date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "stage": "Prospecting",
                "note": "Initial contact made via LinkedIn",
                "user": current_user.get("username", "Sales Rep")
            },
            {
                "date": (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d"),
                "stage": "Qualification",
                "note": "Discovery call completed, identified key needs",
                "user": current_user.get("username", "Sales Rep")
            },
            {
                "date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "stage": "Proposal",
                "note": "Custom proposal sent to decision makers",
                "user": current_user.get("username", "Sales Rep")
            }
        ]

        if deal["status"] == "negotiating":
            timeline.append({
                "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "stage": "Negotiation",
                "note": "Contract terms being reviewed by legal",
                "user": current_user.get("username", "Sales Rep")
            })
        elif deal["status"] == "won":
            timeline.append({
                "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "stage": "Negotiation",
                "note": "Final terms agreed upon",
                "user": current_user.get("username", "Sales Rep")
            })
            timeline.append({
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "stage": "Won",
                "note": "Contract signed!",
                "user": current_user.get("username", "Sales Rep")
            })

        activities = [
            {
                "type": "call",
                "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "subject": "Follow-up call with stakeholders",
                "duration": "45 minutes",
                "outcome": "Positive - moving to next stage"
            },
            {
                "type": "meeting",
                "date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "subject": "Product demo for technical team",
                "duration": "90 minutes",
                "outcome": "Technical requirements confirmed"
            },
            {
                "type": "email",
                "date": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
                "subject": "Initial proposal sent",
                "status": "Read"
            }
        ]

        communications = [
            {
                "type": "email",
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                "subject": "Re: Pricing questions",
                "from": customer_profile["email"],
                "to": current_user.get("email", "sales@contoso.com"),
                "preview": "Thank you for clarifying the pricing structure..."
            },
            {
                "type": "email",
                "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
                "subject": "Meeting notes - Product demo",
                "from": current_user.get("email", "sales@contoso.com"),
                "to": customer_profile["email"],
                "preview": "Following up on our demo session..."
            }
        ]

        documents = [
            {
                "name": f"Proposal - {product}",
                "type": "PDF",
                "date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                "size": "2.4 MB",
                "status": "Sent"
            },
            {
                "name": "Product Specifications",
                "type": "PDF",
                "date": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
                "size": "1.8 MB",
                "status": "Viewed"
            }
        ]

        # Calculate insights
        upsell_score = float(deal.get("upsell_score", 0.5))
        win_probability = 95.0 if deal["status"] == "won" else (65.0 if deal["status"] == "negotiating" else 35.0)

        insights = {
            "health_score": int(upsell_score * 100),
            "win_probability": win_probability,
            "days_in_pipeline": 30,
            "engagement_level": "High" if upsell_score > 0.7 else "Medium",
            "next_best_action": "Schedule executive briefing" if deal["status"] == "negotiating" else "Send proposal"
        }

        # Format related deals
        formatted_related_deals = [
            {
                "customer": rd["customer"],
                "product": rd["product"],
                "value": float(rd["value"]),
                "status": rd["status"],
                "close_date": rd["close_date"]
            }
            for rd in related_deals
        ]

        # Return in same format as original endpoint
        return {
            "customer": deal["customer_name"],
            "product": deal["product"],
            "value": float(deal["value"]),
            "status": deal["status"],
            "close_date": deal["close_date"],
            "customer_profile": customer_profile,
            "timeline": timeline,
            "activities": activities,
            "related_deals": formatted_related_deals,
            "communications": communications,
            "documents": documents,
            "insights": insights
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP deal details failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch deal details via MCP: {str(e)}"
        )


@router.get("/deals/list-mcp")
async def get_deals_list_mcp(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of deals using MCP Server.
    Automatically filtered by user's region via RLS.
    """
    try:
        if not USE_MCP:
            raise HTTPException(
                status_code=503,
                detail="MCP server not enabled"
            )

        mcp = get_mcp_client()

        # Query deals via MCP - RLS filters applied automatically
        query = f"""
            SELECT TOP {limit}
                c.FirstName + ' ' + c.LastName as customer,
                u.recommended_action as product,
                u.upsell_score * 1000 as value,
                CASE
                    WHEN u.upsell_score > 0.8 THEN 'won'
                    WHEN u.upsell_score > 0.5 THEN 'negotiating'
                    ELSE 'prospecting'
                END as status,
                CONVERT(varchar, GETDATE(), 23) as close_date
            FROM dbo.gold_upsell_opportunities u
            INNER JOIN dbo.gold_customer_360 c ON u.CustomerID = c.CustomerID
            ORDER BY u.upsell_score DESC
        """

        deals = await mcp.query_fabric(
            query=query,
            user_context=current_user,
            apply_territory_filter=True,
            table_alias="c"
        )

        return deals

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP deals list failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch deals via MCP: {str(e)}"
        )
