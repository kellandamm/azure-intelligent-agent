"""
Microsoft Agent Framework with Fabric Integration - Main Application
Showcases agent capabilities with Microsoft Fabric data integration.
"""
import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Try to import FabricTool - it may not be available if fabric-data-agent-sdk is not installed
# Try to import FabricTool from the new projects SDK
try:
    from azure.ai.projects.models import FabricTool
    FABRIC_AVAILABLE = True
except ImportError:
    FABRIC_AVAILABLE = False
    print("⚠️  FabricTool not available via projects SDK. Fabric integration will be limited.")

from config import settings
from utils.logging_config import setup_logging, logger
from utils.telemetry import setup_telemetry
from utils.db_connection import DatabaseConnection
from utils.auth import AuthManager, get_current_user, require_admin
from app.rls_middleware import RLSMiddleware
from app.powerbi_integration import powerbi_embedding, powerbi_analytics

# Select the active agent backend through the neutral selector module
from app.agent_backend_manager import AGENT_BACKEND_LABEL, agent_backend_manager
from app.routes_auth import auth_router, admin_router
from app.routes_admin_agents import admin_agent_router, admin_dashboard_router, log_agent_request
from app.telemetry import trace_agent_response
from app.routes_graphrag_proxy import graphrag_proxy_router
from app.routes_ecommerce import router as ecommerce_router
from app.routes_test_fabric import router as fabric_test_router
from app.routes_sales import router as sales_router
from app.routes_analytics import router as analytics_router
from app.routes_diagnostic import diagnostic_router
from app.routes_api_keys import router as api_keys_router

# Import Three-Factor Architecture route modules
from app.routes_pages import router as pages_router
from app.routes_chat import router as chat_router
from app.routes_admin_api import router as admin_api_router
from app.routes_analytics_api import router as analytics_api_router

# Import new production-ready features
from app.observability import ObservabilityMiddleware, metrics_endpoint
from app.health import router as health_router
from app.api_keys import api_key_manager

# CosmosDB cache is optional — disabled gracefully when azure-cosmos is not installed
# or COSMOSDB_ENDPOINT env var is not set
try:
    from app.cache import cache_manager
    _cache_available = True
except ImportError:
    cache_manager = None
    _cache_available = False

# Setup logging and telemetry
setup_logging()
if settings.enable_tracing:
    setup_telemetry()

# Log Fabric availability after logger is configured
if not FABRIC_AVAILABLE:
    logger.warning("⚠️  FabricTool not available. Install azure-ai-agents with Fabric support or create Fabric connection in Azure AI Foundry.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Contoso Sales agent platform")
    logger.info(f"📍 Project Endpoint: {settings.project_endpoint}")
    logger.info(f"🤖 Agent backend: {AGENT_BACKEND_LABEL}")
    logger.info(f"📊 Fabric Workspace: {settings.fabric_workspace_id}")
    logger.info(f"🔐 Authentication: {'Enabled' if settings.enable_authentication else 'Disabled'}")
    
    # Initialize database connection and auth manager
    if settings.enable_authentication:
        try:
            # Validate auth configuration
            settings.validate_auth_config()
            
            # Use access token for local development with Azure AD
            import os
            use_token = settings.sql_use_azure_auth and not any([
                os.getenv('WEBSITE_INSTANCE_ID'),  # App Service/Functions
                os.getenv('IDENTITY_ENDPOINT'),     # Managed Identity
            ])
            
            db_connection = DatabaseConnection(
                settings.database_connection_string,
                use_access_token=use_token
            )
            if db_connection.test_connection():
                logger.info("✅ Database connection established")
                app.state.db_connection = db_connection
                
                # Initialize AuthManager with debug logging
                logger.info("🔧 Initializing AuthManager...")
                logger.debug(f"🔑 JWT_ALGORITHM: {settings.jwt_algorithm}")
                logger.debug(f"⏱️  JWT_EXPIRY_HOURS: {settings.jwt_expiry_hours}")
                
                app.state.auth_manager = AuthManager(
                    db_connection=db_connection,
                    jwt_secret=settings.jwt_secret,
                    jwt_algorithm=settings.jwt_algorithm,
                    jwt_expiry_hours=settings.jwt_expiry_hours
                )
                logger.info("✅ Authentication system initialized")
                logger.info(f"🔐 AuthManager instance: {type(app.state.auth_manager).__name__}")
                
                # Initialize RLS Middleware if enabled
                if settings.enable_rls:
                    app.state.rls_middleware = RLSMiddleware(
                        db_connection=db_connection,
                        auth_manager=app.state.auth_manager
                    )
                    logger.info("✅ Row-Level Security (RLS) middleware initialized")
                    logger.info(f"🔐 RLS Status: Enabled - User data will be automatically filtered")
                else:
                    logger.info("ℹ️  Row-Level Security (RLS) is disabled")
            else:
                logger.warning("⚠️  Database connection failed. Authentication will be disabled.")
                settings.enable_authentication = False
        except ValueError as e:
            logger.warning(f"⚠️  Authentication configuration error: {e}")
            logger.warning("⚠️  Authentication will be disabled. Set SQL_SERVER, SQL_DATABASE, and JWT_SECRET in .env to enable.")
            settings.enable_authentication = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize authentication: {e}")
            logger.warning("⚠️  Authentication will be disabled.")
            settings.enable_authentication = False
    else:
        logger.info("ℹ️  Authentication is disabled. All endpoints are publicly accessible.")
    
    yield
    logger.info("👋 Shutting down Contoso Sales agent platform")

# Initialize FastAPI app
app = FastAPI(
    title="Contoso Sales agent platform",
    description="Contoso Sales demo with Foundry-hosted agents, Microsoft Agent Framework orchestration, and Fabric analytics",
    version="1.0.0",
    lifespan=lifespan
)

# Add observability middleware FIRST (to track all requests)
app.add_middleware(ObservabilityMiddleware)

# Add CORS middleware — allowed origins are the localhost defaults plus any
# production domains listed in the APP_ALLOWED_ORIGINS env var (comma-separated).
# Example: APP_ALLOWED_ORIGINS=https://myapp.azurewebsites.net,https://myapp.com
_default_origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
_extra_origins = [
    o.strip()
    for o in os.environ.get("APP_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
_allowed_origins = _default_origins + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
    max_age=3600,
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;"
    return response

# Mount static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include health check and metrics routers (before auth to allow public access)
app.include_router(health_router, tags=["Health"])

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return await metrics_endpoint()

# Include Three-Factor Architecture routers
# These use the new services layer for better separation of concerns
app.include_router(pages_router, tags=["Pages"])  # HTML page routes
app.include_router(chat_router, tags=["Chat"])  # Chat API routes
app.include_router(admin_api_router, tags=["Admin API"])  # Admin API routes
app.include_router(analytics_api_router, tags=["Analytics API"])  # Analytics API routes

# Include authentication and admin routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(api_keys_router)  # API key management
app.include_router(admin_agent_router)
app.include_router(graphrag_proxy_router)
app.include_router(admin_dashboard_router)
app.include_router(ecommerce_router)  # E-commerce routes
app.include_router(sales_router)  # Sales dashboard routes with RLS
app.include_router(analytics_router)  # Analytics dashboard routes for Admin/Analyst
app.include_router(diagnostic_router)  # Diagnostic endpoints for testing
app.include_router(fabric_test_router)  # Fabric connection testing

# Pydantic Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    agent_type: str = "orchestrator"
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    thread_id: str
    agent_id: str
    run_id: str

class DemoInfo(BaseModel):
    """Demo information model."""
    name: str
    title: str
    description: str
    category: str
    fabric_integration: bool

# Demo Registry
DEMOS: Dict[str, DemoInfo] = {
    "fabric-sales": DemoInfo(
        name="fabric-sales",
        title="Sales Intelligence Queries",
        description="Ask questions about sales data, top products, and revenue trends - routes to SalesAssistant with Fabric data",
        category="Fabric Integration",
        fabric_integration=True
    ),
    "fabric-realtime": DemoInfo(
        name="fabric-realtime",
        title="Real-time Operations Queries",
        description="Ask about system status, uptime, and operational metrics - routes to OperationsAssistant",
        category="Fabric Integration",
        fabric_integration=True
    ),
    "fabric-analytics": DemoInfo(
        name="fabric-analytics",
        title="Data Analytics & Business Intelligence",
        description="Deep analysis of customer demographics, trends, and performance metrics - routes to AnalyticsAssistant with Fabric tools",
        category="Advanced Analytics",
        fabric_integration=True
    ),
    "financial-advisor": DemoInfo(
        name="financial-advisor",
        title="Financial Planning & Forecasting",
        description="ROI calculations, revenue forecasting, and financial planning - routes to FinancialAdvisor with calculation tools",
        category="Financial Services",
        fabric_integration=False
    ),
    "customer-support": DemoInfo(
        name="customer-support",
        title="Customer Support & Help Desk",
        description="Product questions, troubleshooting, and customer service - routes to CustomerSupportAssistant",
        category="Customer Service",
        fabric_integration=False
    ),
    "operations-coord": DemoInfo(
        name="operations-coord",
        title="Operations & Logistics Coordination",
        description="Inventory management, shipping logistics, and supply chain optimization - routes to OperationsCoordinator",
        category="Operations",
        fabric_integration=True
    ),
    "orchestrator": DemoInfo(
        name="orchestrator",
        title="Intelligent Multi-Agent Orchestration",
        description="Ask any question - RetailAssistantOrchestrator automatically selects from 6 specialist agents",
        category="Orchestration",
        fabric_integration=True
    ),
}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main shop/storefront page."""
    return FileResponse(str(static_dir / "shop.html"))

@app.get("/chat", response_class=HTMLResponse)
async def chat():
    """Serve chat interface at /chat route."""
    return FileResponse(str(static_dir / "contoso-sales-chat.html"))

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve login page."""
    return FileResponse(str(static_dir / "login.html"))

@app.get("/admin", response_class=HTMLResponse)
async def admin_portal():
    """Serve admin dashboard page."""
    return FileResponse(str(static_dir / "admin.html"))

@app.get("/powerbi", response_class=HTMLResponse)
async def powerbi_page():
    """Serve dedicated Power BI reports page."""
    return FileResponse(str(static_dir / "powerbi.html"))

@app.get("/admin/test-auth", response_class=HTMLResponse)
async def admin_test_auth(current_user: dict = Depends(require_admin)):
    """Serve authentication test page - Admin only."""
    return FileResponse(str(static_dir / "test-auth.html"))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "fabric_workspace": settings.fabric_workspace_id,
        "project_endpoint": settings.project_endpoint,
        "authentication_enabled": settings.enable_authentication
    }

# Admin API Endpoints
@app.get("/api/admin/config")
async def get_admin_config():
    """Get sanitized configuration for admin portal."""
    return {
        "Azure OpenAI Endpoint": settings.azure_openai_endpoint.replace("https://", "").split(".")[0] + ".openai.azure.com",
        "Deployment": settings.azure_openai_deployment,
        "API Version": settings.azure_openai_api_version,
        "Fabric Workspace": settings.fabric_workspace_id[:8] + "..." if settings.fabric_workspace_id else "Not configured",
        "App Port": settings.app_port,
        "Log Level": settings.log_level,
        "Tracing Enabled": settings.enable_tracing,
        "Environment": "Development" if settings.log_level == "DEBUG" else "Production"
    }

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Get real-time statistics for admin dashboard."""
    # TODO: Implement actual tracking
    return {
        "total_conversations": 1247,
        "active_agents": 6,
        "avg_response_time": 1.2,
        "token_usage_24h": 42300,
        "success_rate": 98.4,
        "most_used_agent": "AnalyticsAssistant"
    }

# ============================================================================
# Power BI Endpoints
# ============================================================================

@app.get("/api/powerbi/reports")
async def get_powerbi_reports():
    """Get available Power BI reports."""
    try:
        if not settings.powerbi_workspace_id:
            return {"error": "Power BI not configured"}
        
        reports = await powerbi_embedding.get_workspace_reports()
        return reports
    except Exception as e:
        logger.error(f"❌ Failed to get Power BI reports: {e}")
        return {"error": str(e)}

@app.get("/api/powerbi/embed/{report_id}")
async def get_powerbi_embed_config(report_id: str):
    """Get Power BI embed configuration for a specific report."""
    try:
        # Check if Power BI is properly configured
        if not settings.powerbi_workspace_id or not settings.powerbi_tenant_id:
            return {
                "error": "Power BI not fully configured",
                "message": "Please set POWERBI_WORKSPACE_ID and POWERBI_TENANT_ID in .env file"
            }
        
        embed_config = await powerbi_embedding.get_embed_config(report_id)
        return embed_config
    except ValueError as e:
        logger.error(f"❌ Configuration error for report {report_id}: {e}")
        return {
            "error": "Configuration Error",
            "message": str(e),
            "troubleshooting": {
                "steps": [
                    "1. Verify report ID is correct in Power BI service",
                    "2. Ensure you have 'View' permissions on the report",
                    "3. Check that workspace ID matches the report's workspace",
                    "4. Verify Azure AD authentication is working (try 'az login')"
                ]
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get embed config for report {report_id}: {e}")
        return {
            "error": "Power BI Integration Error", 
            "message": str(e),
            "fallback": "Using mock visualization for development"
        }

@app.post("/api/powerbi/insights/{report_id}")
async def get_powerbi_insights(report_id: str, question: dict):
    """Get insights from Power BI report using Q&A."""
    try:
        question_text = question.get("question", "")
        insights = await powerbi_analytics.get_report_insights(report_id, question_text)
        return insights
    except Exception as e:
        logger.error(f"❌ Failed to get insights for report {report_id}: {e}")
        return {"error": str(e)}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest, req: Request):
    """
    Send a message to an agent and get a response.
    Requires authentication if enabled in settings.
    RLS context is automatically applied for authenticated users.
    """
    start_time = datetime.utcnow()
    user_id = None
    user_data = None
    agent_key = None
    
    # Check authentication if enabled
    if settings.enable_authentication:
        try:
            # Get auth manager from app state
            auth_manager: AuthManager = req.app.state.auth_manager
            
            # Get token from Authorization header
            auth_header = req.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token = auth_header.split(" ")[1]
            user_data = auth_manager.verify_jwt_token(token)
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            user_id = user_data.get("user_id")
            
            # Set RLS context if enabled
            if settings.enable_rls and user_data:
                try:
                    rls_middleware: RLSMiddleware = req.app.state.rls_middleware
                    db_connection: DatabaseConnection = req.app.state.db_connection
                    
                    with db_connection.get_connection() as conn:
                        await rls_middleware.set_user_context(user_data, conn)
                        logger.debug(f"🔐 RLS context set for user: {user_data.get('username')}")
                        
                        # Get user's data scope for logging
                        data_scope = await rls_middleware.get_user_data_scope(user_id, conn)
                        user_data['data_scope'] = data_scope
                        
                except Exception as rls_error:
                    logger.error(f"❌ Failed to set RLS context: {rls_error}")
                    # Continue without RLS - better to allow access than fail
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    try:
        result = await agent_backend_manager.chat(
            message=request.message,
            agent_type=request.agent_type,
            thread_id=request.thread_id,
        )
        
        # Calculate response time
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        # Determine which agent was used (from result.agent_id or agent_type)
        agent_key = request.agent_type or "orchestrator"
        
        # Log successful request and data access audit
        if user_id:
            try:
                await log_agent_request(
                    agent_key=agent_key,
                    message=request.message,
                    response=result.response[:2000],  # Truncate
                    user_id=user_id,
                    response_time=response_time,
                    success=True
                )
            except Exception as log_error:
                logger.warning(f"Failed to log request: {log_error}")
            
            # Log data access audit if RLS is enabled
            if settings.enable_audit_logging and user_data:
                try:
                    rls_middleware: RLSMiddleware = req.app.state.rls_middleware
                    await rls_middleware.log_data_access(
                        user_data=user_data,
                        access_type="Chat",
                        table_accessed="AgentChat",
                        query_text=request.message[:500],  # Truncate for storage
                        rows_returned=None,
                        request=req
                    )
                except Exception as audit_error:
                    logger.warning(f"Failed to log data access audit: {audit_error}")

        return ChatResponse(
            response=result.response,
            thread_id=result.thread_id,
            agent_id=result.agent_id,
            run_id=result.run_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Log failed request
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds()
        
        if user_id:
            try:
                await log_agent_request(
                    agent_key=agent_key or "unknown",
                    message=request.message,
                    response="",
                    user_id=user_id,
                    response_time=response_time,
                    success=False,
                    error=str(exc)
                )
            except Exception as log_error:
                logger.warning(f"Failed to log error: {log_error}")
        
        logger.error("❌ Chat error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
