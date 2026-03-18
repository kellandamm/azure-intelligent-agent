"""
MCP Server for Agent Framework
Provides centralized tools with Row-Level Security (RLS) filtering
Runs as internal service on port 3000
"""
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from utils.logging_config import setup_logging
from utils.db_connection import DatabaseConnection

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


# ============================================================================
# Models
# ============================================================================

class UserContext(BaseModel):
    """User context for RLS filtering"""
    user_id: int
    username: str
    email: Optional[str] = None
    role: str
    roles: List[str] = []
    region: Optional[str] = None
    regions: List[str] = []
    assigned_customers: List[int] = []
    managed_users: List[int] = []


class ToolRequest(BaseModel):
    """Tool execution request"""
    tool_name: str
    parameters: Dict[str, Any]
    user_context: UserContext


class ToolResponse(BaseModel):
    """Tool execution response"""
    success: bool
    result: Any
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# RLS Filter Builder
# ============================================================================

class RLSFilterBuilder:
    """
    Build SQL WHERE clause filters based on user context.
    This replaces SESSION_CONTEXT approach with application-layer filtering.
    """

    @staticmethod
    def is_admin(user_context: UserContext) -> bool:
        """Check if user has admin privileges"""
        admin_roles = {"SuperAdmin", "Admin"}
        return any(role in admin_roles for role in user_context.roles)

    @staticmethod
    def is_analyst(user_context: UserContext) -> bool:
        """Check if user is analyst (can see all data read-only)"""
        return "Analyst" in user_context.roles or "PowerUser" in user_context.roles

    @staticmethod
    def build_territory_filter(user_context: UserContext, alias: str = "") -> str:
        """
        Build territory/region filter based on user's role.

        Args:
            user_context: User information
            alias: Table alias (e.g., 'c' for 'c.Region')

        Returns:
            SQL WHERE clause fragment (e.g., " AND c.Region = 'West'")
        """
        # Add dot to alias if provided
        prefix = f"{alias}." if alias else ""

        # Admins and Analysts see everything
        if RLSFilterBuilder.is_admin(user_context) or RLSFilterBuilder.is_analyst(user_context):
            return ""

        # Users with multiple regions
        if user_context.regions:
            regions_str = ",".join(f"'{r}'" for r in user_context.regions)
            return f" AND {prefix}Region IN ({regions_str})"

        # Users with single region
        if user_context.region:
            return f" AND {prefix}Region = '{user_context.region}'"

        # No region assigned - no access
        return " AND 1=0"

    @staticmethod
    def build_customer_filter(user_context: UserContext, alias: str = "") -> str:
        """
        Build customer filter based on user's assigned customers.

        Args:
            user_context: User information
            alias: Table alias (e.g., 'c' for 'c.CustomerID')

        Returns:
            SQL WHERE clause fragment
        """
        prefix = f"{alias}." if alias else ""

        # Admins and Analysts see all customers
        if RLSFilterBuilder.is_admin(user_context) or RLSFilterBuilder.is_analyst(user_context):
            return ""

        # Users with assigned customers
        if user_context.assigned_customers:
            customers_str = ",".join(str(c) for c in user_context.assigned_customers)
            return f" AND {prefix}CustomerID IN ({customers_str})"

        # No customers assigned - no access
        return " AND 1=0"

    @staticmethod
    def build_user_filter(user_context: UserContext, user_id_column: str = "UserID") -> str:
        """
        Build filter for user-specific data (e.g., activities, notes).

        Args:
            user_context: User information
            user_id_column: Name of the user ID column

        Returns:
            SQL WHERE clause fragment
        """
        # Admins see all records
        if RLSFilterBuilder.is_admin(user_context):
            return ""

        # Managers see their team's records
        if user_context.managed_users:
            user_ids = [user_context.user_id] + user_context.managed_users
            users_str = ",".join(str(u) for u in user_ids)
            return f" AND {user_id_column} IN ({users_str})"

        # Regular users see only their own records
        return f" AND {user_id_column} = {user_context.user_id}"


# ============================================================================
# Database Helper
# ============================================================================

class MCPDatabase:
    """Database helper with RLS filtering"""

    def __init__(self):
        self.db_connection: Optional[DatabaseConnection] = None

    def initialize(self):
        """Initialize database connection"""
        try:
            if not settings.enable_authentication:
                logger.warning("⚠️ Authentication disabled - MCP server may not have database access")
                return

            # Use access token for local development
            use_token = settings.sql_use_azure_auth and not any([
                os.getenv('WEBSITE_INSTANCE_ID'),
                os.getenv('IDENTITY_ENDPOINT'),
            ])

            self.db_connection = DatabaseConnection(
                settings.database_connection_string,
                use_access_token=use_token
            )

            if self.db_connection.test_connection():
                logger.info("✅ MCP Server database connection established")
            else:
                logger.warning("⚠️ Database connection test failed")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            self.db_connection = None

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results as list of dicts"""
        if not self.db_connection:
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )

        try:
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)

                # Get column names
                columns = [column[0] for column in cursor.description]

                # Fetch rows and convert to dicts
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                cursor.close()
                return results

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Database query failed: {str(e)}"
            )


# ============================================================================
# Application Lifecycle
# ============================================================================

db_helper = MCPDatabase()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting MCP Server")
    logger.info(f"🔐 Authentication: {'Enabled' if settings.enable_authentication else 'Disabled'}")

    # Initialize database
    db_helper.initialize()

    yield

    logger.info("👋 Shutting down MCP Server")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Agent Framework MCP Server",
    description="Internal tool server with Row-Level Security",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for internal services
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Internal only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Audit Logging Middleware
# ============================================================================

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all tool executions for audit trail"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log request (basic info)
    logger.info(
        f"Tool: {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {duration:.3f}s"
    )

    return response


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db_helper.db_connection else "disconnected"

    return {
        "status": "healthy",
        "service": "mcp-server",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Tool: Sales Data Query
# ============================================================================

@app.post("/tools/sales/query", response_model=ToolResponse)
async def sales_query_tool(request: ToolRequest):
    """
    Query sales data with automatic RLS filtering.

    Parameters:
        - query: SQL query (will be filtered)
        - table: Table name (optional, for validation)
    """
    try:
        user_context = request.user_context
        params = request.parameters

        query = params.get("query", "")

        # Apply RLS filters
        territory_filter = RLSFilterBuilder.build_territory_filter(user_context)

        # Modify query to include filters
        if "WHERE" in query.upper():
            filtered_query = query + territory_filter
        else:
            filtered_query = query + " WHERE 1=1" + territory_filter

        # Execute query
        results = db_helper.execute_query(filtered_query)

        return ToolResponse(
            success=True,
            result=results,
            metadata={
                "rows_returned": len(results),
                "filtered": bool(territory_filter),
                "user_role": user_context.role,
                "user_region": user_context.region
            }
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Sales query tool failed: {e}")
        return ToolResponse(
            success=False,
            result=None,
            error=str(e)
        )


# ============================================================================
# Tool: Deal Details
# ============================================================================

@app.post("/tools/deals/detail", response_model=ToolResponse)
async def deal_detail_tool(request: ToolRequest):
    """
    Get deal details with RLS applied.

    Parameters:
        - customer: Customer name
        - product: Product/recommended action
    """
    try:
        user_context = request.user_context
        customer = request.parameters.get("customer")
        product = request.parameters.get("product")

        if not customer or not product:
            raise HTTPException(
                status_code=400,
                detail="customer and product parameters are required"
            )

        # Apply RLS filters
        territory_filter = RLSFilterBuilder.build_territory_filter(user_context, alias="c")

        # Query deal data
        query = f"""
            SELECT
                c.CustomerID,
                c.FirstName + ' ' + c.LastName as customer_name,
                c.Email,
                c.Phone,
                c.Region,
                c.customer_segment,
                c.lifetime_value,
                DATEDIFF(day, c.first_purchase_date, GETDATE()) as account_age,
                u.recommended_action as product,
                u.upsell_score * 1000 as value,
                CASE
                    WHEN u.upsell_score > 0.8 THEN 'won'
                    WHEN u.upsell_score > 0.5 THEN 'negotiating'
                    ELSE 'prospecting'
                END as status,
                CONVERT(varchar, GETDATE(), 23) as close_date,
                u.upsell_score
            FROM dbo.gold_customer_360 c
            INNER JOIN dbo.gold_upsell_opportunities u ON c.CustomerID = u.CustomerID
            WHERE c.FirstName + ' ' + c.LastName = ?
              AND u.recommended_action = ?
              {territory_filter}
        """

        results = db_helper.execute_query(query, (customer, product))

        if not results:
            return ToolResponse(
                success=False,
                result=None,
                error="Deal not found or access denied",
                metadata={"status_code": 404}
            )

        deal = results[0]

        # Get related deals
        related_query = f"""
            SELECT TOP 5
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
            WHERE u.CustomerID = ?
              AND u.recommended_action != ?
              {territory_filter}
            ORDER BY u.upsell_score DESC
        """

        related_deals = db_helper.execute_query(
            related_query,
            (deal['CustomerID'], product)
        )

        return ToolResponse(
            success=True,
            result={
                "deal": deal,
                "related_deals": related_deals
            },
            metadata={
                "filtered": bool(territory_filter),
                "user_region": user_context.region
            }
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Deal detail tool failed: {e}")
        return ToolResponse(
            success=False,
            result=None,
            error=str(e)
        )


# ============================================================================
# Tool: Fabric Query (Generic)
# ============================================================================

@app.post("/tools/fabric/query", response_model=ToolResponse)
async def fabric_query_tool(request: ToolRequest):
    """
    Execute generic Fabric query with RLS filtering.

    Parameters:
        - query: SQL query
        - apply_territory_filter: bool (default True)
        - apply_customer_filter: bool (default False)
        - table_alias: Table alias for filters (optional)
    """
    try:
        user_context = request.user_context
        params = request.parameters

        query = params.get("query", "")
        apply_territory = params.get("apply_territory_filter", True)
        apply_customer = params.get("apply_customer_filter", False)
        alias = params.get("table_alias", "")

        # Build filters
        filters = []

        if apply_territory:
            territory_filter = RLSFilterBuilder.build_territory_filter(user_context, alias)
            if territory_filter:
                filters.append(territory_filter)

        if apply_customer:
            customer_filter = RLSFilterBuilder.build_customer_filter(user_context, alias)
            if customer_filter:
                filters.append(customer_filter)

        # Apply filters to query
        filtered_query = query
        for filter_clause in filters:
            if "WHERE" in filtered_query.upper():
                filtered_query += filter_clause
            else:
                filtered_query += " WHERE 1=1" + filter_clause

        # Execute
        results = db_helper.execute_query(filtered_query)

        return ToolResponse(
            success=True,
            result=results,
            metadata={
                "rows_returned": len(results),
                "filters_applied": len(filters),
                "user_role": user_context.role
            }
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Fabric query tool failed: {e}")
        return ToolResponse(
            success=False,
            result=None,
            error=str(e)
        )


# ============================================================================
# Tool: User Data Scope
# ============================================================================

@app.post("/tools/user/scope", response_model=ToolResponse)
async def user_scope_tool(request: ToolRequest):
    """
    Get user's data access scope (territories, customers, team members).
    Useful for debugging and showing users what they can access.
    """
    try:
        user_context = request.user_context
        user_id = user_context.user_id

        # Get territories
        territories_query = """
            SELECT Territory, Region
            FROM Security.UserTerritories
            WHERE UserID = ? AND IsActive = 1
        """
        territories = db_helper.execute_query(territories_query, (user_id,))

        # Get customer assignments
        customers_query = """
            SELECT CustomerID
            FROM Security.UserCustomerAssignments
            WHERE UserID = ? AND IsActive = 1
        """
        customers = db_helper.execute_query(customers_query, (user_id,))

        # Get team members (if manager)
        team_query = """
            SELECT EmployeeID
            FROM Security.OrganizationHierarchy
            WHERE ManagerID = ? AND IsActive = 1
        """
        team_members = db_helper.execute_query(team_query, (user_id,))

        return ToolResponse(
            success=True,
            result={
                "territories": territories,
                "customers": [c["CustomerID"] for c in customers],
                "team_members": [t["EmployeeID"] for t in team_members],
                "is_admin": RLSFilterBuilder.is_admin(user_context),
                "is_analyst": RLSFilterBuilder.is_analyst(user_context)
            }
        )

    except Exception as e:
        logger.error(f"User scope tool failed: {e}")
        return ToolResponse(
            success=False,
            result=None,
            error=str(e)
        )


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_SERVER_PORT", "3000"))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")

    logger.info(f"🚀 Starting MCP Server on {host}:{port}")

    uvicorn.run(
        "mcp_server_app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
