"""
MCP Server for Agent Framework Tools
Exposes all agent tools as MCP endpoints for use with Azure AI Foundry Agents.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import all tool functions
from agent_tools import (
    FabricDataTools,
    CalculationTools,
    WeatherTools,
    PowerBITools,
    FABRIC_TOOLS,
    CALCULATION_TOOLS,
    WEATHER_TOOLS,
    POWERBI_TOOLS,
)
from config import settings
from utils.logging_config import setup_logging, logger


# Setup logging
setup_logging()

# Create FastAPI app for MCP server
mcp_app = FastAPI(
    title="Agent Tools MCP Server",
    description="Model Context Protocol server exposing agent function calling tools",
    version="1.0.0"
)

# Add CORS middleware
mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for MCP protocol
class MCPToolCallRequest(BaseModel):
    """Request to call an MCP tool."""
    name: str
    arguments: Dict[str, Any]
    user_context: Optional[Dict[str, Any]] = None


class MCPToolCallResponse(BaseModel):
    """Response from an MCP tool call."""
    result: Any
    error: Optional[str] = None


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPToolsListResponse(BaseModel):
    """Response containing list of available MCP tools."""
    tools: List[MCPTool]


# Tool execution map
TOOL_EXECUTION_MAP = {
    # Fabric Data Tools
    "get_sales_summary": FabricDataTools.get_sales_summary,
    "get_customer_demographics": FabricDataTools.get_customer_demographics,
    "get_inventory_status": FabricDataTools.get_inventory_status,
    "get_performance_metrics": FabricDataTools.get_performance_metrics,
    
    # Calculation Tools
    "calculate_roi": CalculationTools.calculate_roi,
    "forecast_revenue": CalculationTools.forecast_revenue,
    
    # Weather Tools
    "get_weather": WeatherTools.get_weather,
    "get_forecast": WeatherTools.get_forecast,
    
    # Power BI Tools
    "query_powerbi_data": PowerBITools.query_powerbi_data,
    "get_report_summary": PowerBITools.get_report_summary,
}


def convert_agent_tool_to_mcp(agent_tool: Dict[str, Any]) -> MCPTool:
    """Convert Agent Framework tool definition to MCP tool format."""
    function_def = agent_tool.get("function", {})
    return MCPTool(
        name=function_def.get("name", ""),
        description=function_def.get("description", ""),
        inputSchema=function_def.get("parameters", {})
    )


@mcp_app.get("/")
async def root():
    """Root endpoint with server info."""
    return {
        "server": "Agent Tools MCP Server",
        "version": "1.0.0",
        "protocol": "MCP",
        "status": "running",
        "tools_count": len(TOOL_EXECUTION_MAP)
    }


@mcp_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "tools_available": len(TOOL_EXECUTION_MAP)}


@mcp_app.get("/mcp/tools", response_model=MCPToolsListResponse)
async def list_mcp_tools():
    """
    List all available MCP tools.
    This endpoint follows the MCP protocol for tool discovery.
    """
    all_tools = FABRIC_TOOLS + CALCULATION_TOOLS + WEATHER_TOOLS + POWERBI_TOOLS
    mcp_tools = [convert_agent_tool_to_mcp(tool) for tool in all_tools]
    
    logger.info(f"MCP: Listed {len(mcp_tools)} available tools")
    return MCPToolsListResponse(tools=mcp_tools)


@mcp_app.post("/mcp/call", response_model=MCPToolCallResponse)
async def call_mcp_tool(request: MCPToolCallRequest):
    """
    Execute an MCP tool call.
    This endpoint follows the MCP protocol for tool execution.
    """
    tool_name = request.name
    arguments = request.arguments
    user_context = request.user_context
    
    logger.info(f"MCP: Calling tool '{tool_name}' with arguments: {arguments}")
    
    # Check if tool exists
    if tool_name not in TOOL_EXECUTION_MAP:
        logger.error(f"MCP: Tool '{tool_name}' not found")
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found"
        )
    
    try:
        # Add user context to arguments for RLS-enabled tools
        if user_context:
            arguments["user_context"] = user_context
        
        # Execute the tool
        tool_func = TOOL_EXECUTION_MAP[tool_name]
        result = tool_func(**arguments)
        
        logger.info(f"MCP: Tool '{tool_name}' executed successfully")
        return MCPToolCallResponse(result=result)
        
    except TypeError as e:
        logger.error(f"MCP: Invalid arguments for tool '{tool_name}': {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid arguments for tool '{tool_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"MCP: Error executing tool '{tool_name}': {e}")
        return MCPToolCallResponse(
            result=None,
            error=f"Error executing tool: {str(e)}"
        )


@mcp_app.get("/mcp/tools/{tool_name}")
async def get_tool_definition(tool_name: str):
    """Get detailed definition for a specific tool."""
    all_tools = FABRIC_TOOLS + CALCULATION_TOOLS + WEATHER_TOOLS + POWERBI_TOOLS
    
    for tool in all_tools:
        if tool.get("function", {}).get("name") == tool_name:
            return convert_agent_tool_to_mcp(tool)
    
    raise HTTPException(
        status_code=404,
        detail=f"Tool '{tool_name}' not found"
    )


# Convenience endpoint for debugging
@mcp_app.get("/tools/list")
async def list_all_tools():
    """List all tools in a simple format (for debugging)."""
    return {
        "fabric_tools": [t["function"]["name"] for t in FABRIC_TOOLS],
        "calculation_tools": [t["function"]["name"] for t in CALCULATION_TOOLS],
        "weather_tools": [t["function"]["name"] for t in WEATHER_TOOLS],
        "powerbi_tools": [t["function"]["name"] for t in POWERBI_TOOLS],
        "total_count": len(TOOL_EXECUTION_MAP)
    }


def start_mcp_server():
    """Start the MCP server."""
    logger.info(f"🚀 Starting MCP Server on {settings.mcp_server_host}:{settings.mcp_server_port}")
    logger.info(f"📡 MCP Tools endpoint: {settings.mcp_server_url}/mcp/tools")
    logger.info(f"🔧 Total tools available: {len(TOOL_EXECUTION_MAP)}")
    
    uvicorn.run(
        mcp_app,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    start_mcp_server()
