"""
MCP Client Library
Easy interface for calling MCP Server tools from main application
"""
import os
import logging
from typing import Dict, Any, List, Optional
import httpx

from config import settings

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for calling MCP Server tools.

    Usage:
        mcp = MCPClient()
        result = await mcp.call_tool("deals/detail", {...}, user_context)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        timeout: float = 30.0
    ):
        """
        Initialize MCP client.

        Args:
            host: MCP server hostname (defaults to MCP_SERVER_HOST env var)
            port: MCP server port (defaults to MCP_SERVER_PORT env var)
            timeout: Request timeout in seconds
        """
        self.host = host or os.getenv("MCP_SERVER_HOST", "localhost")
        self.port = port or int(os.getenv("MCP_SERVER_PORT", "3000"))
        self.base_url = f"http://{self.host}:{self.port}"
        self.timeout = timeout

        logger.info(f"🔧 MCP Client initialized: {self.base_url}")

    async def health_check(self) -> Dict[str, Any]:
        """Check if MCP server is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call an MCP tool with parameters and user context.

        Args:
            tool_name: Tool endpoint (e.g., "deals/detail", "sales/query")
            parameters: Tool-specific parameters
            user_context: User information for RLS filtering

        Returns:
            Tool response dictionary

        Raises:
            HTTPException: If tool call fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Prepare request
                request_data = {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "user_context": {
                        "user_id": user_context.get("user_id"),
                        "username": user_context.get("username"),
                        "email": user_context.get("email"),
                        "role": user_context.get("role", "User"),
                        "roles": user_context.get("roles", [user_context.get("role", "User")]),
                        "region": user_context.get("region"),
                        "regions": user_context.get("regions", [user_context.get("region")] if user_context.get("region") else []),
                        "assigned_customers": user_context.get("assigned_customers", []),
                        "managed_users": user_context.get("managed_users", [])
                    }
                }

                # Make request
                response = await client.post(
                    f"{self.base_url}/tools/{tool_name}",
                    json=request_data
                )

                # Handle response
                if response.status_code != 200:
                    logger.error(f"MCP tool '{tool_name}' failed: {response.status_code}")
                    raise Exception(f"MCP tool call failed: {response.text}")

                result = response.json()

                # Check if tool execution was successful
                if not result.get("success", True):
                    error = result.get("error", "Unknown error")
                    logger.error(f"MCP tool '{tool_name}' returned error: {error}")
                    raise Exception(error)

                return result.get("result")

        except httpx.TimeoutException:
            logger.error(f"MCP tool '{tool_name}' timed out after {self.timeout}s")
            raise Exception(f"MCP server timeout")
        except httpx.ConnectError:
            logger.error(f"Cannot connect to MCP server at {self.base_url}")
            raise Exception(f"MCP server unavailable")
        except Exception as e:
            logger.error(f"MCP tool '{tool_name}' failed: {e}")
            raise

    async def get_deal_details(
        self,
        customer: str,
        product: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convenience method for getting deal details.

        Args:
            customer: Customer name
            product: Product/recommended action
            user_context: User information

        Returns:
            Deal details with related deals
        """
        return await self.call_tool(
            "deals/detail",
            {"customer": customer, "product": product},
            user_context
        )

    async def query_sales_data(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convenience method for querying sales data.

        Args:
            query: SQL query
            user_context: User information

        Returns:
            List of result rows
        """
        return await self.call_tool(
            "sales/query",
            {"query": query},
            user_context
        )

    async def query_fabric(
        self,
        query: str,
        user_context: Dict[str, Any],
        apply_territory_filter: bool = True,
        apply_customer_filter: bool = False,
        table_alias: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Convenience method for generic Fabric queries with RLS.

        Args:
            query: SQL query
            user_context: User information
            apply_territory_filter: Apply region filtering
            apply_customer_filter: Apply customer filtering
            table_alias: Table alias for filters

        Returns:
            List of result rows
        """
        return await self.call_tool(
            "fabric/query",
            {
                "query": query,
                "apply_territory_filter": apply_territory_filter,
                "apply_customer_filter": apply_customer_filter,
                "table_alias": table_alias
            },
            user_context
        )

    async def get_user_scope(
        self,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get user's data access scope.

        Args:
            user_context: User information

        Returns:
            Dictionary with territories, customers, team members
        """
        return await self.call_tool(
            "user/scope",
            {},
            user_context
        )


# Singleton instance for easy access
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """
    Get singleton MCP client instance.

    Usage:
        from app.mcp_client import get_mcp_client

        mcp = get_mcp_client()
        result = await mcp.get_deal_details(...)
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
