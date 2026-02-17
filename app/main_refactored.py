"""
Microsoft Agent Framework with Fabric Integration - Main Application

THREE-FACTOR ARCHITECTURE:
Factor 1: Route Registration (this file imports and registers route modules)
Factor 2: Business Logic (delegated to services/ layer)  
Factor 3: Configuration and Startup (lifespan, middleware, settings)

Showcases agent capabilities with Microsoft Fabric data integration.
Build: 2026-02-05 - Three-Factor Refactoring
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path as _Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure application package directory is first on sys.path
_app_root = str(_Path(__file__).resolve().parent)
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)
    print(f"Added app root to sys.path: {_app_root}")

# Configuration
from config import settings
from utils.logging_config import setup_logging, logger
from utils.telemetry import setup_telemetry
from utils.db_connection import DatabaseConnection
from utils.auth import AuthManager
from app.rls_middleware import RLSMiddleware

# Route Modules (Factor 1: Route Registration)
from app.routes_auth import auth_router, admin_router
from app.routes_admin_agents import admin_agent_router, admin_dashboard_router
from app.routes_admin_api import router as admin_api_router
from app.routes_analytics_api import router as analytics_api_router
from app.routes_chat import router as chat_api_router
from app.routes_pages import router as pages_router
from app.routes_graphrag_proxy import graphrag_proxy_router
from app.routes_ecommerce import router as ecommerce_router
from app.routes_test_fabric import router as fabric_test_router
from app.routes_sales import router as sales_router
from app.routes_analytics import router as analytics_router
from app.routes_diagnostic import diagnostic_router
from app.powerbi_integration import powerbi_embedding, powerbi_analytics

# Setup logging and telemetry (Factor 3: Configuration)
setup_logging()
if settings.enable_tracing:
    setup_telemetry()


# ============================================================================
# FACTOR 3: Configuration and Startup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles initialization and cleanup of resources.
    """
    logger.info("🚀 Starting Agent Framework with Fabric Integration")
    if settings.project_endpoint:
        logger.info(
            f"📍 Azure AI Foundry project detected: {settings.project_endpoint}"
        )
    else:
        logger.info(
            "🤖 Running in Microsoft Agent Framework mode"
        )
    logger.info(f"Fabric Workspace: {settings.fabric_workspace_id}")
    logger.info(
        f"🔐 Authentication: {'Enabled' if settings.enable_authentication else 'Disabled'}"
    )

    # Initialize database connection and auth manager
    if settings.enable_authentication:
        try:
            # Validate auth configuration
            settings.validate_auth_config()

            # Use access token for local development with Azure AD
            # In Azure (Web App), let Managed Identity handle auth via connection string
            use_token = settings.sql_use_azure_auth and not any(
                [
                    os.getenv("WEBSITE_INSTANCE_ID"),  # App Service/Functions
                    os.getenv("IDENTITY_ENDPOINT"),  # Managed Identity available
                ]
            )

            db_connection = DatabaseConnection(
                settings.database_connection_string, use_access_token=use_token
            )
            if db_connection.test_connection():
                logger.info("✅ Database connection established")
                app.state.db_connection = db_connection
                app.state.auth_manager = AuthManager(
                    db_connection=db_connection,
                    jwt_secret=settings.jwt_secret,
                    jwt_algorithm=settings.jwt_algorithm,
                    jwt_expiry_hours=settings.jwt_expiry_hours,
                )
                logger.info("✅ Authentication system initialized")

                # Initialize RLS Middleware if enabled
                if settings.enable_rls:
                    app.state.rls_middleware = RLSMiddleware(
                        db_connection=db_connection, auth_manager=app.state.auth_manager
                    )
                    logger.info("✅ Row-Level Security (RLS) middleware initialized")
                    logger.info(
                        f"🔐 RLS Status: Enabled - User data will be automatically filtered"
                    )
                else:
                    logger.info("ℹ️  Row-Level Security (RLS) is disabled")
            else:
                logger.warning(
                    "⚠️  Database connection failed. Authentication will be disabled."
                )
                settings.enable_authentication = False
        except ValueError as e:
            logger.warning(f"⚠️  Authentication configuration error: {e}")
            logger.warning(
                "⚠️  Authentication will be disabled. Set SQL_SERVER, SQL_DATABASE, and JWT_SECRET in .env to enable."
            )
            settings.enable_authentication = False
        except Exception as e:
            logger.error(f"❌ Failed to initialize authentication: {e}")
            logger.warning("⚠️  Authentication will be disabled.")
            settings.enable_authentication = False
    else:
        logger.info(
            "ℹ️  Authentication is disabled. All endpoints are publicly accessible."
        )

    yield
    logger.info("👋 Shutting down Agent Framework")


# Initialize FastAPI app
app = FastAPI(
    title="Microsoft Agent Framework with Fabric Integration",
    description="Intelligent agents powered by Azure AI and Microsoft Fabric",
    version="1.1.0",
    lifespan=lifespan,
)

# Add CORS middleware - SECURITY: Restrict to specific domains in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        # Add your production domains here
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
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
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdn.plot.ly; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:;"
    )
    return response


# Mount static files directory
static_dir = _Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================================================
# FACTOR 1: Route Registration
# Routes are defined in separate modules, business logic in services/
# ============================================================================

# Page routes (HTML)
app.include_router(pages_router)

# Authentication routes
app.include_router(auth_router)
app.include_router(admin_router)

# Chat API
app.include_router(chat_api_router)

# Admin APIs
app.include_router(admin_agent_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_api_router)

# Analytics APIs
app.include_router(analytics_router)
app.include_router(analytics_api_router)

# Sales routes
app.include_router(sales_router)

# Other feature routes
app.include_router(graphrag_proxy_router)
app.include_router(ecommerce_router)
app.include_router(fabric_test_router)
app.include_router(diagnostic_router)


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
