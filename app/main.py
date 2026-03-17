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
try:
    from azure.ai.agents.models import FabricTool, ListSortOrder
    FABRIC_AVAILABLE = True
except ImportError:
    from azure.ai.agents.models import ListSortOrder
    FABRIC_AVAILABLE = False
    print("⚠️  FabricTool not available. Fabric integration will be limited.")

from config import settings
from utils.logging_config import setup_logging, logger
from utils.telemetry import setup_telemetry
from utils.db_connection import DatabaseConnection
from utils.auth import AuthManager, get_current_user, require_admin
from app.rls_middleware import RLSMiddleware
from app.powerbi_integration import powerbi_embedding, powerbi_analytics
from app.agent_framework_manager import agent_framework_manager
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
    logger.info("🚀 Starting Agent Framework with Fabric Integration")
    logger.info(f"📍 Project Endpoint: {settings.project_endpoint}")
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
    logger.info("👋 Shutting down Agent Framework")


# Initialize FastAPI app
app = FastAPI(
    title="Microsoft Agent Framework with Fabric Integration",
    description="Intelligent agents powered by Azure AI and Microsoft Fabric",
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

# Keep the old embedded HTML code below for reference (can be removed later)
_old_embedded_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contoso Sales - AI-Powered Sales Assistant</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
                display: flex;
                flex-direction: column;
                height: calc(100vh - 40px);
            }
            .header {
                background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
                color: white;
                padding: 30px 40px;
                text-align: center;
                flex-shrink: 0;
            }
            .header h1 { 
                font-size: 2.2em; 
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
            }
            .header p { 
                font-size: 1.1em; 
                opacity: 0.95; 
            }
            .admin-link {
                position: absolute;
                top: 20px;
                right: 20px;
                padding: 10px 20px;
                background: rgba(255,255,255,0.2);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .admin-link:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }
            .conversation-status {
                position: absolute;
                top: 20px;
                left: 20px;
                padding: 8px 16px;
                background: rgba(255,255,255,0.2);
                color: white;
                border-radius: 8px;
                font-size: 0.9em;
                font-weight: 600;
                display: none;
                align-items: center;
                gap: 8px;
            }
            .conversation-status.active {
                display: flex;
                background: rgba(76,175,80,0.3);
            }
            .conversation-status .dot {
                width: 8px;
                height: 8px;
                background: #4caf50;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .content { 
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .suggested-questions {
                padding: 20px 40px;
                background: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                flex-shrink: 0;
            }
            .suggested-questions h3 {
                color: #333;
                margin-bottom: 12px;
                font-size: 1em;
            }
            .question-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            .question-tag {
                background: white;
                color: #0078d4;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s;
                border: 1px solid #0078d4;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .question-tag:hover {
                background: #0078d4;
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .chat-section {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                padding: 20px 40px;
            }
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 15px;
                overflow-y: auto;
                padding: 10px;
                margin-bottom: 20px;
            }
            .message {
                padding: 15px 20px;
                border-radius: 12px;
                max-width: 85%;
                line-height: 1.6;
            }
            .message.user {
                background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
                color: white;
                align-self: flex-end;
                margin-left: auto;
            }
            .message.agent {
                background: white;
                border: 1px solid #e0e0e0;
                align-self: flex-start;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .message.agent h3 {
                margin-top: 15px;
                margin-bottom: 8px;
                color: #333;
                font-size: 1.1em;
            }
            .message.agent h4 {
                margin-top: 12px;
                margin-bottom: 6px;
                color: #555;
                font-size: 1em;
            }
            .message.agent ul, .message.agent ol {
                margin-left: 20px;
                margin-top: 8px;
                margin-bottom: 8px;
            }
            .message.agent li {
                margin-bottom: 4px;
            }
            .message.agent table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            .message.agent table th,
            .message.agent table td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #e0e0e0;
            }
            .message.agent table th {
                background: #f8f9fa;
                font-weight: 600;
                color: #333;
            }
            .message.agent strong {
                color: #0078d4;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .agent-badge {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                margin-bottom: 8px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            .input-group {
                display: flex;
                gap: 10px;
                flex-shrink: 0;
            }
            .button-group {
                display: flex;
                gap: 10px;
            }
            button.secondary {
                background: #6c757d;
            }
            button.secondary:hover {
                background: #5a6268;
            }
            input {
                flex: 1;
                padding: 15px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                font-size: 1em;
                transition: border-color 0.3s;
            }
            input:focus {
                outline: none;
                border-color: #0078d4;
            }
            button {
                padding: 15px 30px;
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                transition: all 0.3s;
                box-shadow: 0 2px 8px rgba(0,120,212,0.3);
            }
            button:hover { 
                background: #005a9e;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0,120,212,0.4);
            }
            button:disabled { 
                background: #ccc; 
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            .specialist-icon {
                font-size: 1.5em;
                vertical-align: middle;
            }
            
            /* Scrollbar styling */
            .chat-container::-webkit-scrollbar {
                width: 8px;
            }
            .chat-container::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 10px;
            }
            .chat-container::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 10px;
            }
            .chat-container::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
            
            /* Tab Navigation */
            .tab-navigation {
                display: flex;
                background: #f8f9fa;
                border-bottom: 2px solid #e0e0e0;
                flex-shrink: 0;
            }
            .tab-button {
                flex: 1;
                padding: 15px 20px;
                background: transparent;
                border: none;
                font-size: 1em;
                font-weight: 600;
                color: #666;
                cursor: pointer;
                transition: all 0.3s;
                position: relative;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            .tab-button:hover {
                background: rgba(0,120,212,0.05);
                color: #0078d4;
            }
            .tab-button.active {
                color: #0078d4;
                background: white;
            }
            .tab-button.active::after {
                content: '';
                position: absolute;
                bottom: -2px;
                left: 0;
                right: 0;
                height: 2px;
                background: #0078d4;
            }
            .tab-content {
                display: none;
                flex: 1;
                flex-direction: column;
                overflow: hidden;
            }
            .tab-content.active {
                display: flex;
            }
            
            /* Power BI Section */
            .powerbi-section {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .powerbi-header {
                padding: 20px 40px;
                background: #f8f9fa;
                border-bottom: 1px solid #e0e0e0;
                flex-shrink: 0;
            }
            .powerbi-header h2 {
                color: #333;
                margin-bottom: 10px;
            }
            .powerbi-header p {
                color: #666;
                font-size: 0.95em;
            }
            .powerbi-container {
                flex: 1;
                padding: 20px 40px;
                overflow-y: auto;
            }
            .report-selector {
                margin-bottom: 20px;
                padding: 15px;
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
            .report-selector label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
            }
            .report-selector select {
                width: 100%;
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 1em;
                background: white;
            }
            #powerbi-embed-container {
                width: 100%;
                height: 600px;
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .loading-message {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #666;
                font-size: 1.1em;
            }
            .error-message {
                padding: 20px;
                background: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 8px;
                color: #856404;
                margin-bottom: 20px;
            }
            .error-message h4 {
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="conversation-status" id="conversationStatus">
                    <span class="dot"></span>
                    <span>Conversation Active</span>
                </div>
                <a href="/admin" class="admin-link" style="right: 20px;">⚡ Admin Portal</a>
                <a href="/powerbi" class="admin-link" style="right: 180px;">📊 Full Reports</a>
                <h1>
                    Contoso Sales
                </h1>
                <p>AI-powered sales intelligence and business insights</p>
            </div>
            
            <!-- Tab Navigation -->
            <div class="tab-navigation">
                <button class="tab-button active" onclick="switchTab('chat')">
                    💬 Chat Assistant
                </button>
                <button class="tab-button" onclick="switchTab('powerbi')">
                    📊 Power BI Reports
                </button>
            </div>
            
            <!-- Chat Tab Content -->
            <div id="chat-tab" class="tab-content active">
            <!-- Chat Tab Content -->
            <div id="chat-tab" class="tab-content active">
                <div class="suggested-questions">
                    <h3>💡 Ask me about:</h3>
                    <div class="question-tags">
                        <span class="question-tag" onclick="insertQuestion(this)">What are our best-selling products this quarter?</span>
                        <span class="question-tag" onclick="insertQuestion(this)">Show me sales performance by region</span>
                        <span class="question-tag" onclick="insertQuestion(this)">Who are our top customers?</span>
                        <span class="question-tag" onclick="insertQuestion(this)">Calculate ROI for $100k investment</span>
                        <span class="question-tag" onclick="insertQuestion(this)">What's our sales forecast for next quarter?</span>
                        <span class="question-tag" onclick="insertQuestion(this)">Compare this year vs last year revenue</span>
                    </div>
                </div>
                
                <div class="chat-section">
                    <div class="chat-container" id="chatContainer"></div>
                    <div class="input-group">
                        <input type="text" id="messageInput" placeholder="Ask about sales performance, customer insights, forecasts, or financial analysis..." />
                        <div class="button-group">
                            <button onclick="sendMessage()" id="sendBtn">
                                <span>Send</span>
                            </button>
                            <button onclick="newChat()" class="secondary" id="newChatBtn">
                                <span>New Chat</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Power BI Tab Content -->
            <div id="powerbi-tab" class="tab-content">
                <div class="powerbi-header">
                    <h2>📊 Power BI Reports</h2>
                    <p>View and interact with embedded Power BI reports and dashboards</p>
                </div>
                <div class="powerbi-container">
                    <div class="report-selector">
                        <label for="report-select">Select a report:</label>
                        <select id="report-select" onchange="loadReport()">
                            <option value="">Loading reports...</option>
                        </select>
                    </div>
                    <div id="powerbi-embed-container">
                        <div class="loading-message">
                            Select a report to view
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"></script>
        <script>
            let threadId = null;
            let currentReport = null;
            let availableReports = [];

            // Tab Switching
            function switchTab(tabName) {
                // Update tab buttons
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                // Update tab content
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.getElementById(tabName + '-tab').classList.add('active');
                
                // Load Power BI reports when switching to that tab
                if (tabName === 'powerbi' && availableReports.length === 0) {
                    loadAvailableReports();
                }
            }

            // Power BI Functions
            async function loadAvailableReports() {
                try {
                    const response = await fetch('/api/powerbi/reports');
                    const data = await response.json();
                    
                    if (data.error) {
                        showPowerBIError(data.error, data.message);
                        return;
                    }
                    
                    availableReports = data.value || [];
                    const select = document.getElementById('report-select');
                    
                    if (availableReports.length === 0) {
                        select.innerHTML = '<option value="">No reports available</option>';
                        return;
                    }
                    
                    select.innerHTML = '<option value="">-- Select a report --</option>';
                    availableReports.forEach(report => {
                        const option = document.createElement('option');
                        option.value = report.id;
                        option.textContent = report.name;
                        select.appendChild(option);
                    });
                    
                } catch (error) {
                    console.error('Failed to load reports:', error);
                    showPowerBIError('Failed to load reports', error.message);
                }
            }

            async function loadReport() {
                const select = document.getElementById('report-select');
                const reportId = select.value;
                
                if (!reportId) {
                    document.getElementById('powerbi-embed-container').innerHTML = 
                        '<div class="loading-message">Select a report to view</div>';
                    return;
                }
                
                document.getElementById('powerbi-embed-container').innerHTML = 
                    '<div class="loading-message">Loading report...</div>';
                
                try {
                    const response = await fetch(`/api/powerbi/embed/${reportId}`);
                    const embedConfig = await response.json();
                    
                    if (embedConfig.error) {
                        showPowerBIError(embedConfig.error, embedConfig.message);
                        return;
                    }
                    
                    // Embed the report
                    const embedContainer = document.getElementById('powerbi-embed-container');
                    embedContainer.innerHTML = ''; // Clear loading message
                    
                    const models = window['powerbi-client'].models;
                    const config = {
                        type: 'report',
                        id: embedConfig.id,
                        embedUrl: embedConfig.embedUrl,
                        accessToken: embedConfig.accessToken,
                        tokenType: models.TokenType.Embed,
                        settings: {
                            panes: {
                                filters: {
                                    expanded: false,
                                    visible: true
                                },
                                pageNavigation: {
                                    visible: true
                                }
                            },
                            background: models.BackgroundType.Transparent,
                            layoutType: models.LayoutType.Custom,
                            customLayout: {
                                displayOption: models.DisplayOption.FitToWidth
                            }
                        }
                    };
                    
                    currentReport = powerbi.embed(embedContainer, config);
                    
                    // Handle events
                    currentReport.on('loaded', function() {
                        console.log('Report loaded successfully');
                    });
                    
                    currentReport.on('rendered', function() {
                        console.log('Report rendered successfully');
                    });
                    
                    currentReport.on('error', function(event) {
                        console.error('Report error:', event.detail);
                        showPowerBIError('Report Error', event.detail.message);
                    });
                    
                } catch (error) {
                    console.error('Failed to load report:', error);
                    showPowerBIError('Failed to load report', error.message);
                }
            }

            function showPowerBIError(title, message) {
                const container = document.getElementById('powerbi-embed-container');
                container.innerHTML = `
                    <div class="error-message">
                        <h4>⚠️ ${title}</h4>
                        <p>${message || 'An unexpected error occurred.'}</p>
                        <p style="margin-top: 10px; font-size: 0.9em;">
                            Please check your Power BI configuration in the .env file:
                            <br>• POWERBI_WORKSPACE_ID
                            <br>• POWERBI_TENANT_ID
                            <br>• POWERBI_CLIENT_ID (optional)
                            <br>• POWERBI_CLIENT_SECRET (optional)
                        </p>
                    </div>
                `;
            }

            // Chat Functions (existing)
            function insertQuestion(element) {
                const input = document.getElementById('messageInput');
                input.value = element.textContent;
                input.focus();
            }

            // Send message
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Disable input
                input.disabled = true;
                document.getElementById('sendBtn').disabled = true;
                document.getElementById('newChatBtn').disabled = true;
                
                // Add user message
                addMessage(message, 'user');
                input.value = '';
                
                // Add loading indicator
                const loadingId = addMessage('🤔 Analyzing your request...', 'agent', null, true);
                
                try {
                    // Get auth token if authentication is enabled
                    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
                    const headers = { 'Content-Type': 'application/json' };
                    if (token) {
                        headers['Authorization'] = `Bearer ${token}`;
                    }
                    
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: headers,
                        body: JSON.stringify({
                            message: message,
                            thread_id: threadId
                        })
                    });
                    
                    // Remove loading indicator
                    const loadingMsg = document.getElementById(loadingId);
                    if (loadingMsg) loadingMsg.remove();
                    
                    if (!response.ok) {
                        if (response.status === 401) {
                            // Unauthorized - redirect to login
                            window.location.href = '/login';
                            return;
                        }
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    threadId = data.thread_id;
                    console.log('Thread ID:', threadId); // Debug: Show thread continuity
                    
                    // Show conversation status indicator
                    document.getElementById('conversationStatus').classList.add('active');
                    
                    // Render response with markdown and HTML support
                    addMessage(data.response, 'agent', data.agent_id);
                } catch (error) {
                    // Remove loading indicator
                    const loadingMsg = document.getElementById(loadingId);
                    if (loadingMsg) loadingMsg.remove();
                    
                    addMessage('❌ Error: ' + error.message + '. Please try again.', 'agent');
                } finally {
                    input.disabled = false;
                    document.getElementById('sendBtn').disabled = false;
                    document.getElementById('newChatBtn').disabled = false;
                    input.focus();
                }
            }

            function addMessage(text, sender, agentId = null, isLoading = false) {
                const container = document.getElementById('chatContainer');
                const message = document.createElement('div');
                const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
                message.id = messageId;
                message.className = `message ${sender}`;
                
                // Add pulsing animation for loading
                if (isLoading) {
                    message.style.animation = 'pulse 1.5s ease-in-out infinite';
                }
                
                // Add agent badge if this is from an agent
                if (sender === 'agent' && agentId && !isLoading) {
                    const agentNames = {
                        'asst_YXmaCOM5JdgKQLhte0Xs2Yib': '🎯 Orchestrator',
                        'asst_dW0oVcgujQZQviiKN8fIHYjr': '💼 Sales',
                        'asst_Efk1OcPxVlWlQ4trfAWcvpPU': '⚙️ Operations',
                        'asst_9bXg6KFWF9BdXSbKnTfV8CYX': '📊 Analytics',
                        'asst_8dgI65ENOCEgVllT3KvkIau2': '💰 Financial',
                        'asst_ZzVT30x521SwXzxGELOviRjo': '🎧 Support',
                        'asst_Z0o8ehX74ojQPsSwaxMdvAUr': '📦 Operations Coord'
                    };
                    const agentName = agentNames[agentId] || '🤖 Agent';
                    const badge = document.createElement('div');
                    badge.className = 'agent-badge';
                    badge.textContent = agentName;
                    message.appendChild(badge);
                }
                
                // Render content with markdown and HTML support
                if (sender === 'agent' && !isLoading && typeof marked !== 'undefined') {
                    // Check if response contains HTML (for charts/metric cards)
                    if (text.includes('<div')) {
                        // Mixed markdown and HTML
                        const div = document.createElement('div');
                        div.innerHTML = marked.parse(text);
                        message.appendChild(div);
                    } else {
                        // Pure markdown
                        const div = document.createElement('div');
                        div.innerHTML = marked.parse(text);
                        message.appendChild(div);
                    }
                } else {
                    const textNode = document.createTextNode(text);
                    message.appendChild(textNode);
                }
                
                container.appendChild(message);
                container.scrollTop = container.scrollHeight;
                
                return messageId;
            }
            
            function newChat() {
                threadId = null;
                const container = document.getElementById('chatContainer');
                container.innerHTML = '';
                document.getElementById('messageInput').value = '';
                document.getElementById('messageInput').focus();
                
                // Hide conversation status indicator
                document.getElementById('conversationStatus').classList.remove('active');
            }

            // Enter key to send
            document.getElementById('messageInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Authentication check
            window.addEventListener('load', () => {
                const authEnabled = """ + str(settings.enable_authentication).lower() + """;
                if (authEnabled) {
                    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
                    if (!token) {
                        window.location.href = '/login';
                        return;
                    }
                    
                    // Verify token
                    fetch('/api/auth/me', {
                        headers: {
                            'Authorization': `Bearer ${token}`
                        }
                    })
                    .then(response => {
                        if (!response.ok) {
                            window.location.href = '/login';
                        } else {
                            return response.json();
                        }
                    })
                    .then(userData => {
                        if (userData) {
                            // Show user info in header
                            const header = document.querySelector('.header');
                            const userInfo = document.createElement('div');
                            userInfo.style.cssText = 'position: absolute; top: 20px; left: 20px; display: flex; align-items: center; gap: 10px; color: white; background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; font-size: 0.9em;';
                            userInfo.innerHTML = `<span>👤</span><span>${userData.username}</span>`;
                            header.appendChild(userInfo);
                            
                            // Add logout button
                            const logoutBtn = document.createElement('button');
                            logoutBtn.textContent = 'Logout';
                            logoutBtn.style.cssText = 'position: absolute; top: 20px; left: 180px; background: rgba(255,255,255,0.2); color: white; border: 2px solid white; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-weight: 600;';
                            logoutBtn.onclick = () => {
                                localStorage.removeItem('auth_token');
                                sessionStorage.removeItem('auth_token');
                                localStorage.removeItem('user_data');
                                sessionStorage.removeItem('user_data');
                                window.location.href = '/login';
                            };
                            header.appendChild(logoutBtn);
                        }
                    })
                    .catch(() => {
                        window.location.href = '/login';
                    });
                }
            });
            
            // Focus input on load
            document.getElementById('messageInput').focus();
        </script>
    </body>
    </html>
    """

@app.get("/chat", response_class=HTMLResponse)
async def chat():
    """Serve chat interface at /chat route."""
    return FileResponse(str(static_dir / "contoso-sales-chat.html"))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "fabric_workspace": settings.fabric_workspace_id,
        "project_endpoint": settings.project_endpoint
    }


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


# Keep original admin portal as /admin-old for now
@app.get("/admin-old", response_class=HTMLResponse)
async def admin_portal_old():
    """Admin portal for managing agents and viewing analytics."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Portal - Agent Framework</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                min-height: 100vh;
            }
            .admin-container {
                display: flex;
                height: 100vh;
            }
            .sidebar {
                width: 250px;
                background: linear-gradient(180deg, #0f2027 0%, #203a43 100%);
                color: white;
                padding: 20px;
                overflow-y: auto;
            }
            .sidebar h2 {
                margin-bottom: 30px;
                font-size: 1.5em;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .nav-item {
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .nav-item:hover {
                background: rgba(255,255,255,0.1);
            }
            .nav-item.active {
                background: rgba(102, 126, 234, 0.3);
                border-left: 4px solid #667eea;
            }
            .main-content {
                flex: 1;
                padding: 30px;
                overflow-y: auto;
            }
            .header {
                background: white;
                padding: 20px 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header h1 {
                color: #333;
                font-size: 2em;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                border-left: 4px solid;
            }
            .stat-card.blue { border-color: #667eea; }
            .stat-card.green { border-color: #43e97b; }
            .stat-card.orange { border-color: #f093fb; }
            .stat-card.purple { border-color: #764ba2; }
            .stat-label {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 10px;
            }
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                color: #333;
            }
            .stat-change {
                font-size: 0.85em;
                margin-top: 5px;
            }
            .stat-change.up { color: #43e97b; }
            .stat-change.down { color: #f56565; }
            .section {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .section h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.5em;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .agent-list {
                display: grid;
                gap: 15px;
            }
            .agent-card {
                padding: 20px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.3s;
            }
            .agent-card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }
            .agent-info {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .agent-icon {
                font-size: 2em;
                width: 60px;
                height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .agent-details h3 {
                color: #333;
                margin-bottom: 5px;
            }
            .agent-details p {
                color: #666;
                font-size: 0.9em;
            }
            .agent-stats {
                display: flex;
                gap: 20px;
                text-align: center;
            }
            .agent-stat-item {
                padding: 10px 15px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            .agent-stat-label {
                font-size: 0.75em;
                color: #666;
                margin-bottom: 5px;
            }
            .agent-stat-value {
                font-size: 1.2em;
                font-weight: bold;
                color: #333;
            }
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
            }
            .status-badge.active {
                background: #d4edda;
                color: #155724;
            }
            .status-badge.idle {
                background: #fff3cd;
                color: #856404;
            }
            .chart-container {
                position: relative;
                height: 300px;
                margin-top: 20px;
            }
            .config-grid {
                display: grid;
                gap: 15px;
            }
            .config-item {
                display: flex;
                justify-content: space-between;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            .config-label {
                color: #666;
                font-weight: 500;
            }
            .config-value {
                color: #333;
                font-family: monospace;
                font-size: 0.9em;
            }
            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s;
            }
            .btn-primary {
                background: #667eea;
                color: white;
            }
            .btn-primary:hover {
                background: #5568d3;
            }
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
            .tab-hidden {
                display: none;
            }
            .activity-log {
                max-height: 400px;
                overflow-y: auto;
            }
            .activity-item {
                padding: 15px;
                border-bottom: 1px solid #e0e0e0;
                display: flex;
                gap: 15px;
            }
            .activity-time {
                color: #999;
                font-size: 0.85em;
                min-width: 100px;
            }
            .activity-content {
                flex: 1;
            }
            .activity-agent {
                font-weight: 600;
                color: #667eea;
            }
        </style>
    </head>
    <body>
        <div class="admin-container">
            <div class="sidebar">
                <h2>⚡ Admin Portal</h2>
                <div class="nav-item active" onclick="showTab('dashboard')">
                    📊 Dashboard
                </div>
                <div class="nav-item" onclick="showTab('agents')">
                    🤖 Agent Management
                </div>
                <div class="nav-item" onclick="showTab('analytics')">
                    📈 Analytics
                </div>
                <div class="nav-item" onclick="showTab('configuration')">
                    ⚙️ Configuration
                </div>
                <div class="nav-item" onclick="showTab('activity')">
                    📋 Activity Log
                </div>
                <div class="nav-item" onclick="window.location.href='/'">
                    💬 Back to Chat
                </div>
            </div>
            
            <div class="main-content">
                <!-- Dashboard Tab -->
                <div id="dashboard-tab" class="tab-content">
                    <div class="header">
                        <h1>Dashboard Overview</h1>
                        <button class="btn btn-primary" onclick="refreshData()">🔄 Refresh</button>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card blue">
                            <div class="stat-label">Total Conversations</div>
                            <div class="stat-value" id="total-conversations">1,247</div>
                            <div class="stat-change up">▲ 12% from last week</div>
                        </div>
                        <div class="stat-card green">
                            <div class="stat-label">Active Agents</div>
                            <div class="stat-value">6</div>
                            <div class="stat-change up">All systems operational</div>
                        </div>
                        <div class="stat-card orange">
                            <div class="stat-label">Avg Response Time</div>
                            <div class="stat-value">1.2s</div>
                            <div class="stat-change up">▲ 15% faster</div>
                        </div>
                        <div class="stat-card purple">
                            <div class="stat-label">Token Usage (24h)</div>
                            <div class="stat-value">42.3K</div>
                            <div class="stat-change">~$1.27 cost</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>📊 Usage Trends</h2>
                        <div class="chart-container">
                            <canvas id="usageChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🎯 Agent Performance</h2>
                        <div class="chart-container">
                            <canvas id="performanceChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Agents Tab -->
                <div id="agents-tab" class="tab-content tab-hidden">
                    <div class="header">
                        <h1>Agent Management</h1>
                        <button class="btn btn-primary" onclick="alert('Create New Agent')">+ New Agent</button>
                    </div>
                    
                    <div class="section">
                        <h2>🤖 Active Agents</h2>
                        <div class="agent-list" id="agentList">
                            <!-- Agents will be loaded here -->
                        </div>
                    </div>
                </div>
                
                <!-- Analytics Tab -->
                <div id="analytics-tab" class="tab-content tab-hidden">
                    <div class="header">
                        <h1>Analytics & Insights</h1>
                    </div>
                    
                    <div class="stats-grid">
                        <div class="stat-card blue">
                            <div class="stat-label">Most Used Agent</div>
                            <div class="stat-value" style="font-size: 1.5em;">📊 Analytics</div>
                            <div class="stat-change">42% of requests</div>
                        </div>
                        <div class="stat-card green">
                            <div class="stat-label">Success Rate</div>
                            <div class="stat-value">98.4%</div>
                            <div class="stat-change up">▲ 2.1%</div>
                        </div>
                        <div class="stat-card orange">
                            <div class="stat-label">Peak Hour</div>
                            <div class="stat-value" style="font-size: 1.8em;">2-3 PM</div>
                            <div class="stat-change">EST timezone</div>
                        </div>
                        <div class="stat-card purple">
                            <div class="stat-label">Avg Session Length</div>
                            <div class="stat-value">8.5</div>
                            <div class="stat-change">messages</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>📈 Request Distribution</h2>
                        <div class="chart-container">
                            <canvas id="distributionChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Configuration Tab -->
                <div id="configuration-tab" class="tab-content tab-hidden">
                    <div class="header">
                        <h1>System Configuration</h1>
                        <button class="btn btn-secondary" onclick="alert('Export Config')">📤 Export</button>
                    </div>
                    
                    <div class="section">
                        <h2>⚙️ Environment Settings</h2>
                        <div class="config-grid" id="configList">
                            <!-- Config will be loaded here -->
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>🔌 Integrations</h2>
                        <div class="config-grid">
                            <div class="config-item">
                                <span class="config-label">Azure OpenAI</span>
                                <span class="status-badge active">Connected</span>
                            </div>
                            <div class="config-item">
                                <span class="config-label">Microsoft Fabric</span>
                                <span class="status-badge active">Connected</span>
                            </div>
                            <div class="config-item">
                                <span class="config-label">Power BI</span>
                                <span class="status-badge idle">Configured</span>
                            </div>
                            <div class="config-item">
                                <span class="config-label">Application Insights</span>
                                <span class="status-badge active">Tracing Enabled</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Activity Log Tab -->
                <div id="activity-tab" class="tab-content tab-hidden">
                    <div class="header">
                        <h1>Activity Log</h1>
                        <button class="btn btn-secondary" onclick="alert('Export Log')">📥 Download</button>
                    </div>
                    
                    <div class="section">
                        <h2>📋 Recent Activity</h2>
                        <div class="activity-log" id="activityLog">
                            <!-- Activity will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Tab management
            function showTab(tabName) {
                // Hide all tabs
                document.querySelectorAll('.tab-content').forEach(tab => {
                    tab.classList.add('tab-hidden');
                });
                
                // Remove active from all nav items
                document.querySelectorAll('.nav-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // Show selected tab
                document.getElementById(tabName + '-tab').classList.remove('tab-hidden');
                
                // Mark nav item as active
                event.target.classList.add('active');
            }
            
            // Initialize charts
            let usageChart, performanceChart, distributionChart;
            
            function initCharts() {
                // Usage Trends Chart
                const usageCtx = document.getElementById('usageChart').getContext('2d');
                usageChart = new Chart(usageCtx, {
                    type: 'line',
                    data: {
                        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        datasets: [{
                            label: 'Conversations',
                            data: [156, 189, 203, 178, 221, 145, 155],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
                
                // Agent Performance Chart
                const perfCtx = document.getElementById('performanceChart').getContext('2d');
                performanceChart = new Chart(perfCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Sales', 'Operations', 'Analytics', 'Financial', 'Support', 'Coordinator'],
                        datasets: [{
                            label: 'Requests',
                            data: [342, 289, 523, 187, 412, 234],
                            backgroundColor: [
                                '#667eea',
                                '#764ba2',
                                '#f093fb',
                                '#4facfe',
                                '#43e97b',
                                '#fa709a'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
                
                // Distribution Chart
                const distCtx = document.getElementById('distributionChart').getContext('2d');
                distributionChart = new Chart(distCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Analytics', 'Support', 'Sales', 'Operations', 'Financial', 'Coordinator'],
                        datasets: [{
                            data: [42, 23, 15, 10, 7, 3],
                            backgroundColor: [
                                '#667eea',
                                '#43e97b',
                                '#f093fb',
                                '#4facfe',
                                '#fa709a',
                                '#764ba2'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            }
            
            // Load agent data
            function loadAgents() {
                const agents = [
                    { icon: '💼', name: 'SalesAssistant', status: 'active', requests: 342, avgTime: '1.1s', accuracy: '98%' },
                    { icon: '⚙️', name: 'OperationsAssistant', status: 'active', requests: 289, avgTime: '0.9s', accuracy: '99%' },
                    { icon: '📊', name: 'AnalyticsAssistant', status: 'active', requests: 523, avgTime: '1.4s', accuracy: '97%' },
                    { icon: '💰', name: 'FinancialAdvisor', status: 'active', requests: 187, avgTime: '1.3s', accuracy: '99%' },
                    { icon: '🎧', name: 'CustomerSupportAssistant', status: 'active', requests: 412, avgTime: '1.0s', accuracy: '98%' },
                    { icon: '📦', name: 'OperationsCoordinator', status: 'active', requests: 234, avgTime: '1.2s', accuracy: '98%' }
                ];
                
                const container = document.getElementById('agentList');
                container.innerHTML = agents.map(agent => `
                    <div class="agent-card">
                        <div class="agent-info">
                            <div class="agent-icon">${agent.icon}</div>
                            <div class="agent-details">
                                <h3>${agent.name}</h3>
                                <p><span class="status-badge ${agent.status}">${agent.status.toUpperCase()}</span></p>
                            </div>
                        </div>
                        <div class="agent-stats">
                            <div class="agent-stat-item">
                                <div class="agent-stat-label">Requests</div>
                                <div class="agent-stat-value">${agent.requests}</div>
                            </div>
                            <div class="agent-stat-item">
                                <div class="agent-stat-label">Avg Time</div>
                                <div class="agent-stat-value">${agent.avgTime}</div>
                            </div>
                            <div class="agent-stat-item">
                                <div class="agent-stat-label">Accuracy</div>
                                <div class="agent-stat-value">${agent.accuracy}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
            
            // Load configuration
            async function loadConfig() {
                try {
                    const response = await fetch('/api/admin/config');
                    const config = await response.json();
                    
                    const container = document.getElementById('configList');
                    container.innerHTML = Object.entries(config).map(([key, value]) => `
                        <div class="config-item">
                            <span class="config-label">${key}</span>
                            <span class="config-value">${value}</span>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Failed to load config:', error);
                }
            }
            
            // Load activity log
            function loadActivity() {
                const activities = [
                    { time: '2 min ago', agent: 'AnalyticsAssistant', action: 'Processed sales forecast request' },
                    { time: '5 min ago', agent: 'SalesAssistant', action: 'Generated quarterly report' },
                    { time: '8 min ago', agent: 'CustomerSupportAssistant', action: 'Handled product inquiry' },
                    { time: '12 min ago', agent: 'FinancialAdvisor', action: 'Calculated ROI projection' },
                    { time: '15 min ago', agent: 'OperationsCoordinator', action: 'Updated inventory status' },
                    { time: '18 min ago', agent: 'AnalyticsAssistant', action: 'Created demographic breakdown' },
                    { time: '22 min ago', agent: 'SalesAssistant', action: 'Analyzed top products' },
                    { time: '25 min ago', agent: 'OperationsAssistant', action: 'Monitored system metrics' }
                ];
                
                const container = document.getElementById('activityLog');
                container.innerHTML = activities.map(activity => `
                    <div class="activity-item">
                        <div class="activity-time">${activity.time}</div>
                        <div class="activity-content">
                            <span class="activity-agent">${activity.agent}</span> - ${activity.action}
                        </div>
                    </div>
                `).join('');
            }
            
            function refreshData() {
                loadConfig();
                loadActivity();
                // Animate stat cards
                document.querySelectorAll('.stat-value').forEach(el => {
                    el.style.transform = 'scale(1.1)';
                    setTimeout(() => el.style.transform = 'scale(1)', 200);
                });
            }
            
            // Initialize on load
            window.addEventListener('load', () => {
                initCharts();
                loadAgents();
                loadConfig();
                loadActivity();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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
        result = await agent_framework_manager.chat(
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
