"""
Admin routes for Agent Management and System Monitoring.
Provides dashboard, agent configuration, and system analytics.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import json
import os

from utils.auth import (
    get_current_user,
    require_admin,
    require_permission,
    require_superadmin
)
from utils.db_connection import DatabaseConnection
from config import settings
from app.agents.admin_config_agent import AdminConfigAgent

# Create router
admin_agent_router = APIRouter(prefix="/api/admin/agents", tags=["Agent Management"])
admin_dashboard_router = APIRouter(prefix="/api/admin/dashboard", tags=["Admin Dashboard"])


# ========================================
# Pydantic Models
# ========================================

class AgentConfigModel(BaseModel):
    """Model for agent configuration."""
    agent_key: str = Field(..., description="Agent key (sales, analytics, etc.)")
    display_name: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=10)
    tools: List[str] = Field(default_factory=list, description="List of tool names")
    is_active: bool = Field(default=True)
    model: str = Field(default="gpt-4o")


class AgentTestRequest(BaseModel):
    """Model for testing an agent."""
    agent_key: str
    test_message: str = Field(..., min_length=1)


class ConfigUpdateRequest(BaseModel):
    """Model for natural language configuration updates."""
    request: str = Field(..., min_length=1, description="Natural language configuration request")


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""
    total_requests: int
    total_users: int
    active_agents: int
    avg_response_time: float
    requests_last_24h: int
    errors_last_24h: int
    top_agents: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]


# ========================================
# Helper Functions
# ========================================

def load_agent_configs() -> Dict[str, Any]:
    """Load agent configurations from file."""
    config_path = "agent_configs.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_agent_configs(configs: Dict[str, Any]) -> None:
    """Save agent configurations to file."""
    config_path = "agent_configs.json"
    with open(config_path, "w") as f:
        json.dump(configs, f, indent=2)


def get_default_agent_configs() -> Dict[str, Any]:
    """Get default agent configurations from agent_framework_manager.py"""
    from agent_framework_manager import AgentFrameworkManager
    
    # This will be populated from the actual specialist_profiles
    manager = AgentFrameworkManager()
    configs = {}
    
    for key, profile in manager.specialist_profiles.items():
        configs[key] = {
            "agent_key": key,
            "display_name": profile.get("display_name", key.title()),
            "prompt": profile.get("prompt", ""),
            "tools": [tool.__name__ if callable(tool) else str(tool) for tool in (profile.get("tools") or [])],
            "is_active": True,
            "model": "gpt-4o",
            "agent_id": profile.get("id", ""),
        }
    
    return configs


async def log_agent_request(
    agent_key: str,
    message: str,
    response: str,
    user_id: int,
    response_time: float,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """Log an agent request for analytics."""
    async with DatabaseConnection() as conn:
        query = """
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AgentRequestLogs')
        BEGIN
            CREATE TABLE AgentRequestLogs (
                LogID INT IDENTITY(1,1) PRIMARY KEY,
                AgentKey NVARCHAR(50) NOT NULL,
                Message NVARCHAR(MAX),
                Response NVARCHAR(MAX),
                UserID INT,
                ResponseTime FLOAT,
                Success BIT DEFAULT 1,
                Error NVARCHAR(MAX),
                CreatedDate DATETIME2 DEFAULT GETUTCDATE()
            );
            CREATE INDEX IX_AgentRequestLogs_AgentKey ON AgentRequestLogs(AgentKey);
            CREATE INDEX IX_AgentRequestLogs_CreatedDate ON AgentRequestLogs(CreatedDate);
        END
        
        INSERT INTO AgentRequestLogs (AgentKey, Message, Response, UserID, ResponseTime, Success, Error)
        VALUES (@AgentKey, @Message, @Response, @UserID, @ResponseTime, @Success, @Error)
        """
        
        await conn.execute(
            query,
            {
                "AgentKey": agent_key,
                "Message": message[:1000],  # Truncate if too long
                "Response": response[:2000] if response else None,
                "UserID": user_id,
                "ResponseTime": response_time,
                "Success": success,
                "Error": error,
            },
        )


# ========================================
# Agent Management Endpoints
# ========================================

@admin_agent_router.get("/list", dependencies=[Depends(require_superadmin)])
async def list_agents(current_user: dict = Depends(get_current_user)):
    """
    List all agent configurations.
    SuperAdmin only.
    """
    try:
        # Try to load from file, otherwise use defaults
        configs = load_agent_configs()
        if not configs:
            configs = get_default_agent_configs()
            save_agent_configs(configs)
        
        # Ensure configs is a dict and convert to list
        if isinstance(configs, dict):
            agents_list = list(configs.values())
        else:
            agents_list = []
        
        return {
            "agents": agents_list,
            "total": len(agents_list)
        }
    except Exception as e:
        print(f"Error loading agents: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to load agents: {str(e)}")



@admin_agent_router.get("/{agent_key}", dependencies=[Depends(require_superadmin)])
async def get_agent(agent_key: str, current_user: dict = Depends(get_current_user)):
    """
    Get specific agent configuration.
    SuperAdmin only.
    """
    configs = load_agent_configs()
    if not configs:
        configs = get_default_agent_configs()
    
    if agent_key not in configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_key}' not found"
        )
    
    return configs[agent_key]


@admin_agent_router.put("/{agent_key}", dependencies=[Depends(require_superadmin)])
async def update_agent(
    agent_key: str,
    agent_config: AgentConfigModel,
    current_user: dict = Depends(get_current_user)
):
    """
    Update agent configuration.
    SuperAdmin only.
    
    This updates the agent's prompt, tools, and settings.
    Changes take effect immediately for new requests.
    """
    configs = load_agent_configs()
    if not configs:
        configs = get_default_agent_configs()
    
    if agent_key not in configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_key}' not found"
        )
    
    # Update configuration
    configs[agent_key].update({
        "display_name": agent_config.display_name,
        "prompt": agent_config.prompt,
        "tools": agent_config.tools,
        "is_active": agent_config.is_active,
        "model": agent_config.model,
        "modified_by": current_user["user_id"],
        "modified_date": datetime.utcnow().isoformat(),
    })
    
    save_agent_configs(configs)
    
    # Log the change
    async with DatabaseConnection() as conn:
        await conn.execute(
            """
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AgentConfigChanges')
            BEGIN
                CREATE TABLE AgentConfigChanges (
                    ChangeID INT IDENTITY(1,1) PRIMARY KEY,
                    AgentKey NVARCHAR(50) NOT NULL,
                    Changes NVARCHAR(MAX),
                    ModifiedBy INT,
                    ModifiedDate DATETIME2 DEFAULT GETUTCDATE()
                );
            END
            
            INSERT INTO AgentConfigChanges (AgentKey, Changes, ModifiedBy)
            VALUES (@AgentKey, @Changes, @ModifiedBy)
            """,
            {
                "AgentKey": agent_key,
                "Changes": json.dumps(agent_config.dict()),
                "ModifiedBy": current_user["user_id"],
            },
        )
    
    return {
        "message": f"Agent '{agent_key}' updated successfully",
        "agent": configs[agent_key]
    }


@admin_agent_router.post("/test", dependencies=[Depends(require_superadmin)])
async def test_agent(
    test_request: AgentTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Test an agent with a sample message.
    SuperAdmin only.
    """
    from agent_framework_manager import AgentFrameworkManager
    
    manager = AgentFrameworkManager()
    
    # Check if agent exists
    if test_request.agent_key not in manager.specialist_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{test_request.agent_key}' not found"
        )
    
    try:
        # Create a test session
        session_id = f"test_{current_user['user_id']}_{datetime.utcnow().timestamp()}"
        
        # Send test message
        start_time = datetime.utcnow()
        response_text, history, usage = await manager._run_specialist(
            test_request.agent_key,
            test_request.test_message
        )
        end_time = datetime.utcnow()
        
        response_time = (end_time - start_time).total_seconds()
        
        return {
            "success": True,
            "agent_key": test_request.agent_key,
            "response": response_text,
            "response_time": response_time,
            "usage": usage,
            "message_count": len(history)
        }
        
    except Exception as e:
        return {
            "success": False,
            "agent_key": test_request.agent_key,
            "error": str(e)
        }


@admin_agent_router.post("/{agent_key}/toggle", dependencies=[Depends(require_superadmin)])
async def toggle_agent(
    agent_key: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Enable/disable an agent.
    SuperAdmin only.
    """
    configs = load_agent_configs()
    if not configs:
        configs = get_default_agent_configs()
    
    if agent_key not in configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_key}' not found"
        )
    
    configs[agent_key]["is_active"] = not configs[agent_key].get("is_active", True)
    save_agent_configs(configs)
    
    status_text = "enabled" if configs[agent_key]["is_active"] else "disabled"
    
    return {
        "message": f"Agent '{agent_key}' {status_text}",
        "is_active": configs[agent_key]["is_active"]
    }


# ========================================
# Dashboard Endpoints
# ========================================

@admin_dashboard_router.get("/stats", dependencies=[Depends(require_admin)])
async def get_dashboard_stats(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get dashboard statistics.
    Admin and SuperAdmin only.
    """
    from utils.logging_config import logger
    
    try:
        logger.info("Dashboard stats requested by user: " + str(current_user.get("user_id")))
        
        # Use database connection from app state
        if not hasattr(request.app.state, 'db_connection'):
            logger.warning("No database connection available")
            return {
                "total_requests": 0,
                "total_users": 0,
                "active_agents": 0,
                "avg_response_time": 0.0,
                "requests_last_24h": 0,
                "errors_last_24h": 0,
                "top_agents": [],
                "recent_activity": [],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        db = request.app.state.db_connection
        
        # Get total users
        users_query = "SELECT COUNT(*) as count FROM Users WHERE IsActive = 1"
        users_result = db.execute_query(users_query)
        total_users = users_result[0]["count"] if users_result else 0
        
        logger.info(f"Total users: {total_users}")
        
        # Get request stats (if table exists)
        try:
            # Total requests
            total_req_query = "SELECT COUNT(*) as count FROM AgentRequestLogs"
            total_req_result = db.execute_query(total_req_query)
            total_requests = total_req_result[0]["count"] if total_req_result else 0
            
            # Requests last 24h
            req_24h_query = """
                SELECT COUNT(*) as count FROM AgentRequestLogs
                WHERE CreatedDate >= DATEADD(HOUR, -24, GETUTCDATE())
            """
            req_24h_result = db.execute_query(req_24h_query)
            requests_24h = req_24h_result[0]["count"] if req_24h_result else 0
            
            # Errors last 24h
            errors_query = """
                SELECT COUNT(*) as count FROM AgentRequestLogs
                WHERE Success = 0 AND CreatedDate >= DATEADD(HOUR, -24, GETUTCDATE())
            """
            errors_result = db.execute_query(errors_query)
            errors_24h = errors_result[0]["count"] if errors_result else 0
            
            # Average response time
            avg_query = """
                SELECT AVG(ResponseTime) as avg_time FROM AgentRequestLogs
                WHERE CreatedDate >= DATEADD(HOUR, -24, GETUTCDATE())
            """
            avg_result = db.execute_query(avg_query)
            avg_response = float(avg_result[0]["avg_time"]) if avg_result and avg_result[0]["avg_time"] else 0.0
            
            # Top agents
            top_agents_query = """
                SELECT TOP 5
                    AgentKey,
                    COUNT(*) as RequestCount,
                    AVG(ResponseTime) as AvgResponseTime,
                    SUM(CASE WHEN Success = 0 THEN 1 ELSE 0 END) as ErrorCount
                FROM AgentRequestLogs
                WHERE CreatedDate >= DATEADD(DAY, -7, GETUTCDATE())
                GROUP BY AgentKey
                ORDER BY RequestCount DESC
            """
            top_agents_result = db.execute_query(top_agents_query)
            
            top_agents = [
                {
                    "agent_key": row["AgentKey"],
                    "request_count": row["RequestCount"],
                    "avg_response_time": float(row["AvgResponseTime"]) if row["AvgResponseTime"] else 0,
                    "error_count": row["ErrorCount"]
                }
                for row in (top_agents_result or [])
            ]
            
            # Recent activity
            recent_query = """
                SELECT TOP 10
                    AgentKey,
                    Message,
                    Success,
                    ResponseTime,
                    CreatedDate,
                    UserID
                FROM AgentRequestLogs
                ORDER BY CreatedDate DESC
            """
            recent_result = db.execute_query(recent_query)
            
            recent_activity = [
                {
                    "agent_key": row["AgentKey"],
                    "message": row["Message"][:100] + "..." if len(row["Message"]) > 100 else row["Message"],
                    "success": row["Success"],
                    "response_time": float(row["ResponseTime"]),
                    "timestamp": row["CreatedDate"].isoformat() if row["CreatedDate"] else None,
                    "user_id": row["UserID"]
                }
                for row in (recent_result or [])
            ]
            
            logger.info(f"Dashboard stats calculated: requests={total_requests}, users={total_users}")
            
        except Exception as e:
            # Tables don't exist yet or query failed
            logger.warning(f"Failed to get request stats: {e}")
            total_requests = 0
            requests_24h = 0
            errors_24h = 0
            avg_response = 0.0
            top_agents = []
            recent_activity = []
        
        # Get active agents count
        configs = load_agent_configs()
        if not configs:
            configs = get_default_agent_configs()
        active_agents = sum(1 for cfg in configs.values() if cfg.get("is_active", True))
        
        return {
            "total_requests": total_requests,
            "total_users": total_users,
            "active_agents": active_agents,
            "avg_response_time": float(avg_response),
            "requests_last_24h": requests_24h,
            "errors_last_24h": errors_24h,
            "top_agents": top_agents,
            "recent_activity": recent_activity,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@admin_dashboard_router.get("/agent-analytics/{agent_key}", dependencies=[Depends(require_admin)])
async def get_agent_analytics(
    agent_key: str,
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed analytics for a specific agent.
    Admin and SuperAdmin only.
    """
    async with DatabaseConnection() as conn:
        try:
            # Request volume over time
            volume_result = await conn.fetch_all(
                f"""
                SELECT
                    CAST(CreatedDate AS DATE) as Date,
                    COUNT(*) as RequestCount,
                    AVG(ResponseTime) as AvgResponseTime,
                    SUM(CASE WHEN Success = 0 THEN 1 ELSE 0 END) as ErrorCount
                FROM AgentRequestLogs
                WHERE AgentKey = @AgentKey
                  AND CreatedDate >= DATEADD(DAY, -@Days, GETUTCDATE())
                GROUP BY CAST(CreatedDate AS DATE)
                ORDER BY Date DESC
                """,
                {"AgentKey": agent_key, "Days": days}
            )
            
            volume_by_date = [
                {
                    "date": row["Date"].isoformat() if row["Date"] else None,
                    "request_count": row["RequestCount"],
                    "avg_response_time": float(row["AvgResponseTime"]) if row["AvgResponseTime"] else 0,
                    "error_count": row["ErrorCount"]
                }
                for row in (volume_result or [])
            ]
            
            # Success rate
            success_stats = await conn.fetch_one(
                """
                SELECT
                    COUNT(*) as Total,
                    SUM(CASE WHEN Success = 1 THEN 1 ELSE 0 END) as Successful,
                    SUM(CASE WHEN Success = 0 THEN 1 ELSE 0 END) as Failed
                FROM AgentRequestLogs
                WHERE AgentKey = @AgentKey
                  AND CreatedDate >= DATEADD(DAY, -@Days, GETUTCDATE())
                """,
                {"AgentKey": agent_key, "Days": days}
            )
            
            total = success_stats["Total"] if success_stats else 0
            successful = success_stats["Successful"] if success_stats else 0
            failed = success_stats["Failed"] if success_stats else 0
            success_rate = (successful / total * 100) if total > 0 else 0
            
            # Recent errors
            errors_result = await conn.fetch_all(
                """
                SELECT TOP 10
                    Message,
                    Error,
                    CreatedDate
                FROM AgentRequestLogs
                WHERE AgentKey = @AgentKey
                  AND Success = 0
                  AND CreatedDate >= DATEADD(DAY, -@Days, GETUTCDATE())
                ORDER BY CreatedDate DESC
                """,
                {"AgentKey": agent_key, "Days": days}
            )
            
            recent_errors = [
                {
                    "message": row["Message"][:100] if row["Message"] else "",
                    "error": row["Error"],
                    "timestamp": row["CreatedDate"].isoformat() if row["CreatedDate"] else None
                }
                for row in (errors_result or [])
            ]
            
            return {
                "agent_key": agent_key,
                "period_days": days,
                "total_requests": total,
                "successful_requests": successful,
                "failed_requests": failed,
                "success_rate": success_rate,
                "volume_by_date": volume_by_date,
                "recent_errors": recent_errors
            }
            
        except Exception as e:
            return {
                "agent_key": agent_key,
                "error": "Analytics not available yet. No requests logged.",
                "detail": str(e)
            }


@admin_dashboard_router.get("/system-health", dependencies=[Depends(require_admin)])
async def get_system_health(current_user: dict = Depends(get_current_user)):
    """
    Get system health information.
    Admin and SuperAdmin only.
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        async with DatabaseConnection() as conn:
            await conn.fetch_val("SELECT 1")
        health_data["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_data["components"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
        health_data["status"] = "degraded"
    
    # Check Azure OpenAI
    try:
        from agent_framework_manager import AgentFrameworkManager
        manager = AgentFrameworkManager()
        health_data["components"]["azure_openai"] = {
            "status": "healthy",
            "endpoint": settings.azure_openai_endpoint,
            "deployment": settings.azure_openai_deployment
        }
    except Exception as e:
        health_data["components"]["azure_openai"] = {
            "status": "unhealthy",
            "message": f"Azure OpenAI error: {str(e)}"
        }
        health_data["status"] = "degraded"
    
    # Check agents
    try:
        configs = load_agent_configs()
        if not configs:
            configs = get_default_agent_configs()
        active_count = sum(1 for cfg in configs.values() if cfg.get("is_active", True))
        health_data["components"]["agents"] = {
            "status": "healthy",
            "total_agents": len(configs),
            "active_agents": active_count
        }
    except Exception as e:
        health_data["components"]["agents"] = {
            "status": "unhealthy",
            "message": f"Agent config error: {str(e)}"
        }
        health_data["status"] = "degraded"
    
    return health_data


# ========================================
# Admin Configuration Agent Routes
# ========================================

@admin_agent_router.post("/config/natural-update")
async def natural_language_config_update(
    request: ConfigUpdateRequest,
    current_user: dict = Depends(require_superadmin)
):
    """
    Update any system configuration using natural language.
    SuperAdmin only.
    
    Examples:
    - "Update SalesAssistant to focus more on Azure products"
    - "Add web_search tool to AnalyticsAssistant"
    - "Disable the FinancialAdvisor agent"
    - "Change max request timeout to 120 seconds"
    - "Scale the web app to 3 instances"
    - "List all agent configurations"
    """
    try:
        db = DatabaseConnection(settings.fabric_connection_string)
        agent = AdminConfigAgent(user_id=current_user.get("email", "unknown"), db=db)
        result = await agent.process_request(request.request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration update failed: {str(e)}"
        )


@admin_agent_router.get("/config/history")
async def get_configuration_history(
    category: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(require_superadmin)
):
    """
    Get configuration change history.
    SuperAdmin only.
    
    Query parameters:
    - category: Filter by category (agent, app, infrastructure)
    - limit: Maximum number of records to return (default 50)
    """
    try:
        db = DatabaseConnection(settings.fabric_connection_string)
        
        query = """
        SELECT TOP (@limit)
            id, category, target, changed_by, 
            change_summary, timestamp, applied, rollback_available
        FROM configuration_changes
        """
        
        if category:
            query += " WHERE category = @category"
        
        query += " ORDER BY timestamp DESC"
        
        params = {"limit": limit}
        if category:
            params["category"] = category
        
        changes = db.execute_query(query, params)
        
        return {
            "success": True,
            "changes": [
                {
                    "id": row[0],
                    "category": row[1],
                    "target": row[2],
                    "changed_by": row[3],
                    "change_summary": row[4],
                    "timestamp": row[5],
                    "applied": row[6],
                    "rollback_available": row[7]
                }
                for row in changes
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )


@admin_agent_router.post("/config/rollback/{change_id}")
async def rollback_configuration(
    change_id: int,
    current_user: dict = Depends(require_superadmin)
):
    """
    Rollback a configuration change by ID.
    SuperAdmin only.
    """
    try:
        db = DatabaseConnection(settings.fabric_connection_string)
        
        # Get the change record
        query = """
        SELECT category, target, old_config, rollback_available
        FROM configuration_changes
        WHERE id = @change_id
        """
        
        result = db.execute_query(query, {"change_id": change_id})
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Change record not found"
            )
        
        category, target, old_config_str, rollback_available = result[0]
        
        if not rollback_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rollback not available for this change"
            )
        
        old_config = json.loads(old_config_str)
        
        # Apply rollback based on category
        if category == "agent":
            configs = load_agent_configs()
            configs[target] = old_config
            save_agent_configs(configs)
            message = f"✅ Rolled back agent configuration for {target}"
        
        elif category == "app":
            from pathlib import Path
            config_path = Path("config/app_config.json")
            with open(config_path, 'w') as f:
                json.dump(old_config, f, indent=2)
            message = f"✅ Rolled back app configuration. Restart required."
        
        elif category == "infrastructure":
            from pathlib import Path
            import yaml
            config_path = Path("infrastructure/config.yaml")
            with open(config_path, 'w') as f:
                yaml.dump(old_config, f, default_flow_style=False)
            message = f"✅ Rolled back infrastructure configuration. Deployment required."
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown category: {category}"
            )
        
        return {
            "success": True,
            "message": message,
            "category": category,
            "target": target
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )


# ========================================
# Export for main.py
# ========================================

__all__ = [
    "admin_agent_router",
    "admin_dashboard_router",
    "log_agent_request"
]
