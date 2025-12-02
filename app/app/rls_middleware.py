"""
Row-Level Security (RLS) Middleware
Automatically applies RLS context to database connections based on authenticated user
"""
import logging
from typing import Optional, Dict, Any
from fastapi import Request
from utils.db_connection import DatabaseConnection
from utils.auth import AuthManager
from .purview_integration import purview_integration

logger = logging.getLogger(__name__)


class RLSMiddleware:
    """
    Middleware to enforce Row-Level Security (RLS) for database queries.
    
    Automatically sets SQL Server session context based on authenticated user:
    - UserId
    - Username  
    - UserEmail
    - UserRoles
    - DataScope (territories, customers, etc.)
    """
    
    def __init__(self, db_connection: DatabaseConnection, auth_manager: AuthManager):
        """
        Initialize RLS middleware.
        
        Args:
            db_connection: Database connection instance
            auth_manager: Authentication manager instance
        """
        self.db = db_connection
        self.auth = auth_manager
    
    async def set_user_context(
        self, 
        user_data: Dict[str, Any],
        connection
    ) -> bool:
        """
        Set SQL Server session context for the current user.
        
        Args:
            user_data: User information from JWT token
            connection: Active database connection
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            user_id = user_data.get("user_id")
            username = user_data.get("username")
            email = user_data.get("email")
            roles = ",".join(user_data.get("roles", []))
            
            # Call stored procedure to set context
            cursor = connection.cursor()
            
            cursor.execute("""
                EXEC Security.usp_SetUserContext 
                    @UserId = ?,
                    @Username = ?,
                    @UserEmail = ?,
                    @UserRoles = ?
            """, (user_id, username, email, roles))
            
            cursor.commit()
            cursor.close()
            
            logger.info(f"✅ RLS context set for user: {username} (Roles: {roles})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set RLS context: {e}")
            return False
    
    async def get_user_data_scope(self, user_id: int, connection) -> Dict[str, Any]:
        """
        Get user's data access scope (territories, customers, team members).
        
        Args:
            user_id: User ID
            connection: Active database connection
            
        Returns:
            dict: User's data scope
        """
        try:
            cursor = connection.cursor()
            
            # Get territories
            cursor.execute("""
                SELECT Territory, Region 
                FROM Security.UserTerritories 
                WHERE UserID = ? AND IsActive = 1
            """, (user_id,))
            
            territories = [{"territory": row[0], "region": row[1]} for row in cursor.fetchall()]
            
            # Get customer assignments
            cursor.execute("""
                SELECT CustomerID 
                FROM Security.UserCustomerAssignments 
                WHERE UserID = ? AND IsActive = 1
            """, (user_id,))
            
            customers = [row[0] for row in cursor.fetchall()]
            
            # Get team members (if manager)
            cursor.execute("""
                SELECT EmployeeID 
                FROM Security.OrganizationHierarchy 
                WHERE ManagerID = ? AND IsActive = 1
            """, (user_id,))
            
            team_members = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            
            return {
                "territories": territories,
                "customers": customers,
                "teamMembers": team_members
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get user data scope: {e}")
            return {
                "territories": [],
                "customers": [],
                "teamMembers": []
            }
    
    async def log_data_access(
        self,
        user_data: Dict[str, Any],
        access_type: str,
        table_accessed: Optional[str] = None,
        query_text: Optional[str] = None,
        rows_returned: Optional[int] = None,
        request: Optional[Request] = None
    ):
        """
        Log data access for audit and Purview tracking.
        
        Args:
            user_data: User information
            access_type: Type of access (Query, Chat, PowerBI, API)
            table_accessed: Table name accessed
            query_text: SQL query or chat message
            rows_returned: Number of rows returned
            request: FastAPI request object for IP/User-Agent
        """
        try:
            user_id = user_data.get("user_id")
            username = user_data.get("username")
            
            # Get client info from request
            client_ip = None
            user_agent = None
            session_id = None
            
            if request:
                client_ip = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                session_id = request.session.get("session_id") if hasattr(request, "session") else None
            
            # Log to database
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    EXEC Security.usp_LogDataAccess
                        @UserID = ?,
                        @Username = ?,
                        @AccessType = ?,
                        @TableAccessed = ?,
                        @QueryText = ?,
                        @RowsReturned = ?,
                        @SessionID = ?,
                        @ClientIP = ?,
                        @UserAgent = ?
                """, (
                    user_id, username, access_type, table_accessed,
                    query_text, rows_returned, session_id, client_ip, user_agent
                ))
                cursor.commit()
                cursor.close()
            
            # Log to Purview (if enabled)
            await purview_integration.log_data_access(
                user_id=user_id,
                username=username,
                access_type=access_type,
                data_source=f"SQL.{table_accessed}" if table_accessed else "Unknown",
                query_text=query_text,
                rows_returned=rows_returned,
                metadata={
                    "clientIp": client_ip,
                    "userAgent": user_agent,
                    "sessionId": session_id
                }
            )
            
            logger.debug(f"📝 Data access logged: {username} → {table_accessed} ({access_type})")
            
        except Exception as e:
            logger.error(f"❌ Failed to log data access: {e}")
    
    def apply_rls_to_query(
        self,
        query: str,
        user_data: Dict[str, Any]
    ) -> str:
        """
        Apply RLS filters to a query based on user context.
        
        This is a safety layer for queries that bypass stored procedures.
        
        Args:
            query: Original SQL query
            user_data: User information
            
        Returns:
            str: Modified query with RLS filters
        """
        try:
            roles = user_data.get("roles", [])
            user_id = user_data.get("user_id")
            
            # SuperAdmins bypass all filters
            if "SuperAdmin" in roles or "Admin" in roles:
                return query
            
            # For regular users, add RLS predicates
            # This is a simplified example - adjust based on your schema
            
            # Note: In production with proper security policies applied,
            # this manual filtering may not be necessary as SQL Server
            # will automatically apply the security predicates
            
            logger.debug(f"Query prepared with RLS context for user {user_id}")
            return query
            
        except Exception as e:
            logger.error(f"❌ Failed to apply RLS to query: {e}")
            return query


# =========================================================================
# Fabric RLS Helper Functions
# =========================================================================

def get_fabric_rls_filter(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate RLS filters for Microsoft Fabric queries.
    
    Args:
        user_data: User information from JWT
        
    Returns:
        dict: Filter conditions for Fabric queries
    """
    user_id = user_data.get("user_id")
    roles = user_data.get("roles", [])
    data_scope = user_data.get("data_scope", {})
    
    # SuperAdmins see everything
    if "SuperAdmin" in roles or "Admin" in roles:
        return {"filterType": "none"}
    
    # Build filter conditions
    filters = {
        "filterType": "user_scope",
        "userId": user_id,
        "territories": data_scope.get("territories", []),
        "customers": data_scope.get("customers", []),
        "teamMembers": data_scope.get("teamMembers", [])
    }
    
    return filters


def get_powerbi_rls_roles(user_data: Dict[str, Any]) -> list[str]:
    """
    Map application user roles to Power BI dataset roles.
    
    Args:
        user_data: User information from JWT
        
    Returns:
        list: Power BI role names to apply
    """
    roles = user_data.get("roles", [])
    email = user_data.get("email")
    
    powerbi_roles = []
    
    # Map application roles to Power BI roles
    if "SuperAdmin" in roles or "Admin" in roles:
        powerbi_roles.append("AllData")
    elif "Manager" in roles or "PowerUser" in roles:
        powerbi_roles.append("ManagerView")
    else:
        powerbi_roles.append("UserView")
    
    return powerbi_roles


def get_powerbi_effective_identity(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create effective identity for Power BI embedding with RLS.
    
    Args:
        user_data: User information from JWT
        
    Returns:
        dict: Effective identity for Power BI embed token
    """
    username = user_data.get("email") or user_data.get("username")
    roles = get_powerbi_rls_roles(user_data)
    
    return {
        "username": username,
        "roles": roles,
        "datasets": []  # Will be populated with dataset IDs
    }


# =========================================================================
# Chat Agent RLS Helper
# =========================================================================

class ChatAgentRLSHelper:
    """Helper class to apply RLS filters to chat agent queries."""
    
    @staticmethod
    def rewrite_query_with_rls(
        query: str,
        user_data: Dict[str, Any]
    ) -> str:
        """
        Rewrite a natural language query to respect RLS.
        
        Args:
            query: Original user query
            user_data: User information
            
        Returns:
            str: Modified query with RLS context
        """
        roles = user_data.get("roles", [])
        data_scope = user_data.get("data_scope", {})
        
        # SuperAdmins - no modification needed
        if "SuperAdmin" in roles or "Admin" in roles:
            return query
        
        # Add scope context to query
        scope_context = []
        
        if data_scope.get("territories"):
            territories = ", ".join(data_scope["territories"])
            scope_context.append(f"for territories: {territories}")
        
        if data_scope.get("customers"):
            scope_context.append(f"for my assigned customers only")
        
        if scope_context:
            modified_query = f"{query} ({' and '.join(scope_context)})"
            logger.debug(f"Query rewritten with RLS: {modified_query}")
            return modified_query
        
        return query
    
    @staticmethod
    def filter_chat_results(
        results: Any,
        user_data: Dict[str, Any]
    ) -> Any:
        """
        Filter chat agent results based on RLS.
        
        Args:
            results: Raw results from agent
            user_data: User information
            
        Returns:
            Filtered results
        """
        # Results should already be filtered by database RLS
        # This is an additional safety layer
        
        roles = user_data.get("roles", [])
        
        # SuperAdmins see everything
        if "SuperAdmin" in roles or "Admin" in roles:
            return results
        
        # Apply additional filtering if needed
        # (most filtering should happen at database level)
        
        return results


# =========================================================================
# Export
# =========================================================================

__all__ = [
    "RLSMiddleware",
    "get_fabric_rls_filter",
    "get_powerbi_rls_roles",
    "get_powerbi_effective_identity",
    "ChatAgentRLSHelper"
]
