"""
Microsoft Agent Framework with Fabric Integration - Main Application
Showcases agent capabilities with Microsoft Fabric data integration.
Build: 2025-10-29T19:26:00Z
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# Ensure application package directory is first on sys.path so top-level imports (like
# `from rls_middleware import ...`) always resolve when gunicorn/uvicorn workers start.
import sys
from pathlib import Path as _Path

_app_root = str(_Path(__file__).resolve().parent)
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)
    print(f"Added app root to sys.path: {_app_root}")


from config import settings
from utils.logging_config import setup_logging, logger
from utils.telemetry import setup_telemetry
from utils.db_connection import DatabaseConnection
from utils.auth import AuthManager, get_current_user, require_admin
from app.rls_middleware import RLSMiddleware
from app.powerbi_integration import powerbi_embedding, powerbi_analytics
# Use Azure AI Foundry agent manager instead of agent framework
from app.agent_framework_manager import agent_framework_manager
from app.routes_auth import auth_router, admin_router
from app.routes_admin_agents import (
    admin_agent_router,
    admin_dashboard_router,
    log_agent_request,
)
from app.telemetry import trace_agent_response
from app.routes_graphrag_proxy import graphrag_proxy_router
from app.routes_ecommerce import router as ecommerce_router
from app.routes_test_fabric import router as fabric_test_router
from app.routes_sales import router as sales_router
from app.routes_analytics import router as analytics_router
from app.routes_diagnostic import diagnostic_router


# Setup logging and telemetry
setup_logging()
if settings.enable_tracing:
    setup_telemetry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Agent Framework with Fabric Integration")
    if settings.project_endpoint:
        logger.info(
            f"📍 Azure AI Foundry project detected (legacy): {settings.project_endpoint}"
        )
    else:
        logger.info(
            "🤖 Running in Microsoft Agent Framework mode (no Foundry project configured)"
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
            import os

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
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include authentication and admin routers
app.include_router(auth_router)
app.include_router(admin_router)
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
        fabric_integration=True,
    ),
    "fabric-realtime": DemoInfo(
        name="fabric-realtime",
        title="Real-time Operations Queries",
        description="Ask about system status, uptime, and operational metrics - routes to OperationsAssistant",
        category="Fabric Integration",
        fabric_integration=True,
    ),
    "fabric-analytics": DemoInfo(
        name="fabric-analytics",
        title="Data Analytics & Business Intelligence",
        description="Deep analysis of customer demographics, trends, and performance metrics - routes to AnalyticsAssistant with Fabric tools",
        category="Advanced Analytics",
        fabric_integration=True,
    ),
    "financial-advisor": DemoInfo(
        name="financial-advisor",
        title="Financial Planning & Forecasting",
        description="ROI calculations, revenue forecasting, and financial planning - routes to FinancialAdvisor with calculation tools",
        category="Financial Services",
        fabric_integration=False,
    ),
    "customer-support": DemoInfo(
        name="customer-support",
        title="Customer Support & Help Desk",
        description="Product questions, troubleshooting, and customer service - routes to CustomerSupportAssistant",
        category="Customer Service",
        fabric_integration=False,
    ),
    "operations-coord": DemoInfo(
        name="operations-coord",
        title="Operations & Logistics Coordination",
        description="Inventory management, shipping logistics, and supply chain optimization - routes to OperationsCoordinator",
        category="Operations",
        fabric_integration=True,
    ),
    "orchestrator": DemoInfo(
        name="orchestrator",
        title="Intelligent Multi-Agent Orchestration",
        description="Ask any question - RetailAssistantOrchestrator automatically selects from 6 specialist agents",
        category="Orchestration",
        fabric_integration=True,
    ),
}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve landing page with navigation to all apps."""
    # Simple landing page - redirect to chat for now
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/chat", status_code=302)


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """Serve interactive chat UI. Authentication enforced server-side if enabled."""
    # SECURITY FIX: Check authentication SERVER-SIDE before serving any content
    if settings.enable_authentication:
        # Check for token in cookies (more reliable for initial page load)
        token = request.cookies.get("auth_token")

        # If no cookie, check Authorization header (for API calls)
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        # If still no token, redirect to login
        if not token:
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/login", status_code=302)

        # Verify the token
        auth_manager = request.app.state.auth_manager
        user_data = auth_manager.verify_jwt_token(token)

        if not user_data:
            # Invalid/expired token - redirect to login
            from fastapi.responses import RedirectResponse

            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("auth_token")  # Clear invalid cookie
            return response

        # User is authenticated - continue to serve page
        logger.info(f"✅ User {user_data.get('username')} accessed chat page")

    html_content = (
        """
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
                position: relative;
                background: white;
                color: #333;
                padding: 20px 40px;
                flex-shrink: 0;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                z-index: 100;
            }

            .header-content {
                max-width: 1800px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: relative;
            }

            .header-left {
                display: flex;
                align-items: center;
                gap: 20px;
            }

            .header h1 { 
                font-size: 28px; 
                margin: 0;
                color: #0078d4;
                font-weight: 600;
            }

            .nav-dropdown {
                position: relative;
            }

            .nav-dropdown-btn {
                padding: 10px 20px;
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.3s;
                font-weight: 600;
            }

            .nav-dropdown-btn:hover {
                background: #005a9e;
            }

            .nav-dropdown-content {
                display: none;
                position: absolute;
                top: 100%;
                left: 0;
                margin-top: 5px;
                background: white;
                min-width: 200px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                border-radius: 5px;
                z-index: 1000;
                overflow: hidden;
            }

            .nav-dropdown-content.show {
                display: block;
            }

            .nav-dropdown-content a {
                display: block;
                padding: 12px 20px;
                color: #333;
                text-decoration: none;
                transition: background 0.2s;
            }

            .nav-dropdown-content a:hover {
                background: #f5f5f5;
            }

            .nav-dropdown-content a.active {
                background: #e6f2ff;
                color: #0078d4;
                font-weight: 600;
            }

            .header-actions {
                display: flex;
                gap: 15px;
                align-items: center;
                position: relative;
                z-index: 50;
            }

            .user-info {
                color: #666;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .user-icon {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 14px;
            }

            .btn {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
                font-weight: 600;
            }

            .btn-secondary {
                background: #f0f0f0;
                color: #333;
            }

            .btn-secondary:hover {
                background: #e0e0e0;
            }

            .page-title {
                background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
                color: white;
                padding: 40px 40px 30px 40px;
                text-align: center;
            }

            .page-title h2 {
                font-size: 2.2em;
                margin-bottom: 8px;
            }

            .page-title p {
                font-size: 1.1em;
                opacity: 0.95;
            }
            
            /* Remove old top nav styles */
            .top-nav {
                display: none;
            }
            
            .left-nav {
                display: none;
            }
            
            .right-nav {
                display: none;
            }
            
            .nav-link, .admin-link {
                display: none;
            }
            }
            
            .nav-link:hover, .admin-link:hover {
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }
            
            .conversation-status {
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
                min-height: 0; /* Critical for flex overflow */
                position: relative; /* For absolute positioning of scroll button */
            }
            .chat-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 15px;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 10px;
                padding-bottom: 20px; /* Extra padding at bottom for scroll comfort */
                margin-bottom: 20px;
                min-height: 0; /* Critical for flex overflow */
                scroll-behavior: smooth; /* Smooth scrolling */
                position: relative;
            }
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
            .suggested-questions {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid #e0e0e0;
            }
            .suggested-question-btn {
                background: linear-gradient(135deg, #f0f7ff 0%, #e6f2ff 100%);
                color: #0078d4;
                border: 1px solid #0078d4;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 2px 4px rgba(0,120,212,0.1);
            }
            .suggested-question-btn:hover {
                background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,120,212,0.3);
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-content">
                    <div class="header-left">
                        <h1>Contoso Sales</h1>
                        <div class="nav-dropdown">
                            <button class="nav-dropdown-btn" onclick="toggleNavDropdown(event)">
                                <span>Navigate</span>
                                <span>▼</span>
                            </button>
                            <div class="nav-dropdown-content" id="navDropdown">
                                <a href="/chat" class="active">AI Chat Assistant</a>
                                <a href="/static/analyst-dashboard.html">Analytics Dashboard</a>
                                <a href="/static/sales-dashboard.html">Sales Dashboard</a>
                                <a href="/static/shop.html">Shop</a>
                                <a href="/admin">Admin Portal</a>
                            </div>
                        </div>
                    </div>
                    <div class="header-actions">
                        <div class="conversation-status" id="conversationStatus">
                            <span class="dot"></span>
                            <span>Active Conversation</span>
                        </div>
                        <div class="user-info">
                            <div class="user-icon" id="userIcon">U</div>
                            <span id="userInfo">User</span>
                        </div>
                        <button class="btn btn-secondary" onclick="logout()">Logout</button>
                    </div>
                </div>
            </div>
            <div class="page-title">
                <h2>AI Chat Assistant</h2>
                <p>AI-powered sales intelligence and business insights</p>
            </div>
            
            <!-- Chat Content -->
            <div id="chat-tab" class="tab-content active">
                <div class="suggested-questions">
                    <h3>Ask me about:</h3>
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
        </div>
        <script>
            // Keep browser URL aligned with the chat route after redirects
            if (window.location.pathname !== "/chat") {
                window.history.replaceState(null, "", "/chat");
            }

            let threadId = null;
            let currentReport = null;
            let availableReports = [];

            // Get auth token
            function getAuthToken() {
                return localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token') || '';
            }

            // Load user info
            async function loadUserInfo() {
                console.log('Chat: Starting loadUserInfo');
                try {
                    const token = getAuthToken();
                    if (token) {
                        console.log('Chat: Token found, length=' + token.length);
                    } else {
                        console.log('Chat: No token found');
                    }
                    
                    if (!token) {
                        console.log('Chat: Redirecting to login');
                        window.location.href = '/login';
                        return;
                    }
                    
                    console.log('Chat: Calling API auth/me');
                    const response = await fetch('/api/auth/me', {
                        headers: {
                            'Authorization': 'Bearer ' + token
                        }
                    });
                    
                    console.log('Chat: API response status=' + response.status);
                    
                    if (response.ok) {
                        const data = await response.json();
                        console.log('Chat: User data received');
                        const userName = data.full_name || data.username || data.email || 'User';
                        document.getElementById('userInfo').textContent = userName;
                        console.log('Chat: Updated userInfo');
                        
                        // Set user icon with initials
                        const initials = userName.split(' ')
                            .map(n => n[0])
                            .join('')
                            .substring(0, 2)
                            .toUpperCase();
                        document.getElementById('userIcon').textContent = initials;
                        console.log('Chat: Updated userIcon');
                    } else {
                        console.log('Chat: Auth failed, redirecting to login');
                        window.location.href = '/login';
                    }
                } catch (error) {
                    console.error('Chat: Error loading user info', error);
                    window.location.href = '/login';
                }
            }

            // Logout function
            function logout() {
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_data');
                sessionStorage.removeItem('auth_token');
                sessionStorage.removeItem('user_data');
                window.location.href = '/login';
            }

            // Toggle navigation dropdown
            function toggleNavDropdown(event) {
                if (event) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                const dropdown = document.getElementById('navDropdown');
                if (dropdown) {
                    const isVisible = dropdown.classList.contains('show');
                    dropdown.classList.toggle('show');
                    console.log('Dropdown toggled:', !isVisible);
                } else {
                    console.error('Dropdown element not found');
                }
            }

            // Close dropdown when clicking outside
            document.addEventListener('click', function(event) {
                const dropdown = document.getElementById('navDropdown');
                const button = event.target.closest('.nav-dropdown-btn');
                
                if (!button && dropdown && !dropdown.contains(event.target)) {
                    dropdown.classList.remove('show');
                }
            });

            // Load user info on page load
            loadUserInfo();

            // Chat Functions
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
                        headers['Authorization'] = 'Bearer ' + token;
                    }
                    
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: headers,
                        credentials: 'include', // Include cookies for authentication
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
                        throw new Error('HTTP error! status: ' + response.status);
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
                message.className = 'message ' + sender;
                
                // Add pulsing animation for loading
                if (isLoading) {
                    message.style.animation = 'pulse 1.5s ease-in-out infinite';
                }
                
                // Add agent badge if this is from an agent
                if (sender === 'agent' && agentId && !isLoading) {
                    const agentNames = {
                        'asst_YXmaCOM5JdgKQLhte0Xs2Yib': 'Orchestrator',
                        'asst_dW0oVcgujQZQviiKN8fIHYjr': 'Sales',
                        'asst_Efk1OcPxVlWlQ4trfAWcvpPU': '⚙️ Operations',
                        'asst_9bXg6KFWF9BdXSbKnTfV8CYX': 'Analytics',
                        'asst_8dgI65ENOCEgVllT3KvkIau2': 'Financial',
                        'asst_ZzVT30x521SwXzxGELOviRjo': '🎧 Support',
                        'asst_Z0o8ehX74ojQPsSwaxMdvAUr': '📦 Operations Coord'
                    };
                    const agentName = agentNames[agentId] || 'Agent';
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
                    
                    // Add suggested follow-up questions
                    addSuggestedQuestions(message, text);
                } else {
                    const textNode = document.createTextNode(text);
                    message.appendChild(textNode);
                }
                
                container.appendChild(message);
                
                // Improved scroll to bottom - wait for content to render
                scrollToBottom(container);
                
                return messageId;
            }
            
            // Helper function to scroll to bottom smoothly and reliably
            function scrollToBottom(container) {
                // Use requestAnimationFrame to ensure DOM has updated
                requestAnimationFrame(() => {
                    container.scrollTop = container.scrollHeight;
                    
                    // Double-check after a brief delay for charts/images
                    setTimeout(() => {
                        container.scrollTop = container.scrollHeight;
                    }, 100);
                    
                    // Final check for Plotly charts which take longer
                    setTimeout(() => {
                        container.scrollTop = container.scrollHeight;
                    }, 500);
                });
            }
            
            function addSuggestedQuestions(messageElement, responseText) {
                // Generate contextual follow-up questions based on the response
                const suggestedQuestions = generateFollowUpQuestions(responseText);
                
                if (suggestedQuestions.length > 0) {
                    const questionsContainer = document.createElement('div');
                    questionsContainer.className = 'suggested-questions';
                    
                    suggestedQuestions.forEach(question => {
                        const btn = document.createElement('button');
                        btn.className = 'suggested-question-btn';
                        btn.textContent = question;
                        btn.onclick = () => {
                            document.getElementById('messageInput').value = question;
                            sendMessage();
                        };
                        questionsContainer.appendChild(btn);
                    });
                    
                    messageElement.appendChild(questionsContainer);
                }
            }
            
            function generateFollowUpQuestions(responseText) {
                const questions = [];
                const text = responseText.toLowerCase();
                
                // Track asked topics to avoid repetition
                const askedTopics = new Set();
                const chatMessages = document.querySelectorAll('.message.user');
                chatMessages.forEach(msg => {
                    const msgText = msg.textContent.toLowerCase();
                    if (msgText.includes('sales') || msgText.includes('revenue')) askedTopics.add('sales');
                    if (msgText.includes('customer') || msgText.includes('churn')) askedTopics.add('customer');
                    if (msgText.includes('product') || msgText.includes('inventory')) askedTopics.add('product');
                    if (msgText.includes('data') || msgText.includes('quality')) askedTopics.add('data');
                    if (msgText.includes('financial') || msgText.includes('profit')) askedTopics.add('financial');
                    if (msgText.includes('forecast') || msgText.includes('predict')) askedTopics.add('forecast');
                    if (msgText.includes('trend') || msgText.includes('compare')) askedTopics.add('trend');
                });
                
                // Sales-related follow-ups with variations
                if (text.includes('sales') || text.includes('revenue') || text.includes('deal')) {
                    const salesQuestions = [
                        'What are the top performing sales reps?',
                        'Show me sales forecast for next quarter',
                        'Compare this year vs last year performance',
                        'Which regions have the highest growth?',
                        'What deals are close to closing?',
                        'Show pipeline health by stage',
                        'What is our average deal size?',
                        'Which products drive most revenue?'
                    ];
                    questions.push(...getRandomQuestions(salesQuestions, 3, askedTopics));
                }
                // Customer-related follow-ups with variations
                else if (text.includes('customer') || text.includes('churn') || text.includes('retention')) {
                    const customerQuestions = [
                        'Which customer segments have highest churn?',
                        'What are the top customer concerns?',
                        'Show customer satisfaction trends',
                        'Who are our most valuable customers?',
                        'What drives customer loyalty?',
                        'Show customer lifetime value analysis',
                        'Which customers are at risk?',
                        'What are common support issues?'
                    ];
                    questions.push(...getRandomQuestions(customerQuestions, 3, askedTopics));
                }
                // Product-related follow-ups with variations
                else if (text.includes('product') || text.includes('inventory') || text.includes('stock')) {
                    const productQuestions = [
                        'What products have low stock levels?',
                        'Show product performance comparison',
                        'Which products have best profit margins?',
                        'What are the fastest moving products?',
                        'Show product category breakdown',
                        'Which products need restocking?',
                        'What new products should we consider?',
                        'Show seasonal product trends'
                    ];
                    questions.push(...getRandomQuestions(productQuestions, 3, askedTopics));
                }
                // Analytics/data quality follow-ups with variations
                else if (text.includes('data') || text.includes('quality') || text.includes('metric') || text.includes('analytics')) {
                    const analyticsQuestions = [
                        'Show data quality metrics',
                        'What tables need attention?',
                        'Display data completeness scores',
                        'Which datasets are most reliable?',
                        'Show data freshness by source',
                        'What metrics matter most?',
                        'Display KPI dashboard',
                        'Show anomaly detection results'
                    ];
                    questions.push(...getRandomQuestions(analyticsQuestions, 3, askedTopics));
                }
                // Financial follow-ups with variations
                else if (text.includes('financial') || text.includes('profit') || text.includes('cost') || text.includes('expense')) {
                    const financialQuestions = [
                        'What is our profit margin trend?',
                        'Show expense breakdown by category',
                        'Compare quarterly financial performance',
                        'What are our biggest cost drivers?',
                        'Show cash flow projections',
                        'Which departments are over budget?',
                        'Display ROI by initiative',
                        'What is our burn rate?'
                    ];
                    questions.push(...getRandomQuestions(financialQuestions, 3, askedTopics));
                }
                // Forecast/prediction follow-ups
                else if (text.includes('forecast') || text.includes('predict') || text.includes('projection')) {
                    const forecastQuestions = [
                        'What is next quarter revenue forecast?',
                        'Predict customer growth trends',
                        'Show demand forecasting for products',
                        'What are hiring projections?',
                        'Forecast market expansion opportunities',
                        'Predict seasonal variations'
                    ];
                    questions.push(...getRandomQuestions(forecastQuestions, 3, askedTopics));
                }
                // Default follow-ups with rotation
                else {
                    const defaultQuestions = [
                        'Show me sales performance overview',
                        'What are current customer trends?',
                        'Display key business metrics',
                        'What are todays priorities?',
                        'Show executive dashboard summary',
                        'What needs my attention?',
                        'Display team performance metrics',
                        'What opportunities exist?',
                        'Show competitive analysis',
                        'What risks should I know about?'
                    ];
                    questions.push(...getRandomQuestions(defaultQuestions, 3, askedTopics));
                }
                
                return questions;
            }
            
            // Helper function to get random varied questions
            function getRandomQuestions(questionPool, count, askedTopics) {
                // Shuffle and select random questions
                const shuffled = questionPool.sort(() => Math.random() - 0.5);
                return shuffled.slice(0, count);
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
                const authEnabled = """
        + str(settings.enable_authentication).lower()
        + """;
                // Note: Server-side authentication already validated before serving this page
                // No need for redundant client-side auth check that causes redirect loops
                if (authEnabled) {
                    // Get token from localStorage or sessionStorage for API calls
                    let token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
                    
                    // If no token in storage, try to get it from cookie (server validated this)
                    if (!token) {
                        // Don't redirect - server already validated auth via cookie
                        console.log('No token in localStorage, but server validated cookie auth');
                    }
                    
                    // Optionally verify token to get user info (but don't redirect on failure)
                    if (token) {
                        fetch('/api/auth/me', {
                            headers: {
                                'Authorization': 'Bearer ' + token
                            }
                        })
                        .then(response => {
                            if (response.ok) {
                                return response.json();
                            }
                        })
                        .then(userData => {
                            if (userData) {
                                console.log('User authenticated:', userData.username);
                            }
                        })
                        .catch(err => {
                            console.log('Token verification failed, but cookie auth is valid:', err);
                        });
                    }
                }
                
                // Set up MutationObserver to handle dynamic content changes (charts, images)
                const chatContainer = document.getElementById('chatContainer');
                if (chatContainer) {
                    const observer = new MutationObserver((mutations) => {
                        // Check if mutations added content that might affect scroll height
                        const hasNewContent = mutations.some(mutation => 
                            mutation.addedNodes.length > 0 || 
                            (mutation.type === 'attributes' && mutation.attributeName === 'style')
                        );
                        
                        if (hasNewContent) {
                            // Scroll to bottom when new content is added or resized
                            requestAnimationFrame(() => {
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                            });
                        }
                    });
                    
                    // Observe the chat container and all descendants
                    observer.observe(chatContainer, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeFilter: ['style', 'class']
                    });
                    
                    console.log('Chat container MutationObserver initialized');
                }
            });
            
            // Focus input on load
            document.getElementById('messageInput').focus();
        </script>
    </body>
    </html>
    """
    )
    return HTMLResponse(content=html_content)


def _health_payload() -> Dict[str, Any]:
    """Build health response shared by duplicate route definitions."""
    framework_mode = (
        "Azure AI Foundry"
        if settings.project_endpoint
        else "Agent Framework"
    )
    return {
        "status": "healthy",
        "version": "1.0.0",
        "fabric_workspace": settings.fabric_workspace_id,
        "project_endpoint": settings.project_endpoint or "",
        "framework_mode": framework_mode,
        "authentication_enabled": settings.enable_authentication,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return _health_payload()


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
    """Health check endpoint (duplicate definition retained for backwards compatibility)."""
    return _health_payload()


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
                <h2>Admin Portal</h2>
                <div class="nav-item active" onclick="showTab('dashboard')">
                    Dashboard
                </div>
                <div class="nav-item" onclick="showTab('agents')">
                    Agent Management
                </div>
                <div class="nav-item" onclick="showTab('analytics')">
                    Analytics
                </div>
                <div class="nav-item" onclick="showTab('configuration')">
                    ⚙️ Configuration
                </div>
                <div class="nav-item" onclick="showTab('activity')">
                    📋 Activity Log
                </div>
                <div class="nav-item" onclick="window.location.href='/'">
                    Back to Chat
                </div>
            </div>
            
            <div class="main-content">
                <!-- Dashboard Tab -->
                <div id="dashboard-tab" class="tab-content">
                    <div class="header">
                        <h1>Dashboard Overview</h1>
                        <button class="btn btn-primary" onclick="refreshData()">Refresh</button>
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
                        <h2>Usage Trends</h2>
                        <div class="chart-container">
                            <canvas id="usageChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>Agent Performance</h2>
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
                        <h2>Active Agents</h2>
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
                            <div class="stat-value" style="font-size: 1.5em;">Analytics</div>
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
                        <h2>Request Distribution</h2>
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
        "Azure OpenAI Endpoint": settings.azure_openai_endpoint.replace(
            "https://", ""
        ).split(".")[0]
        + ".openai.azure.com",
        "Deployment": settings.azure_openai_deployment,
        "API Version": settings.azure_openai_api_version,
        "Fabric Workspace": settings.fabric_workspace_id[:8] + "..."
        if settings.fabric_workspace_id
        else "Not configured",
        "App Port": settings.app_port,
        "Log Level": settings.log_level,
        "Tracing Enabled": settings.enable_tracing,
        "Environment": "Development" if settings.log_level == "DEBUG" else "Production",
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
        "most_used_agent": "AnalyticsAssistant",
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
                "message": "Please set POWERBI_WORKSPACE_ID and POWERBI_TENANT_ID in .env file",
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
                    "4. Verify Azure AD authentication is working (try 'az login')",
                ]
            },
        }
    except Exception as e:
        logger.error(f"❌ Failed to get embed config for report {report_id}: {e}")
        return {
            "error": "Power BI Integration Error",
            "message": str(e),
            "fallback": "Using mock visualization for development",
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


# ============================================================================
# Analytics Dashboard API Endpoints
# ============================================================================

@app.get("/api/analytics/metrics")
async def get_analytics_metrics(req: Request):
    """Get overview metrics for analytics dashboard with RLS filtering."""
    try:
        # Get user from auth
        user_data = None
        token = req.cookies.get("access_token") or req.headers.get("Authorization", "").replace("Bearer ", "")
        
        if token:
            auth_manager = req.app.state.auth_manager
            user_data = auth_manager.verify_jwt_token(token)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Check if user has analyst or admin role
        roles = user_data.get("roles", [])
        if "admin" not in roles and "analyst" not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mock data - replace with actual Fabric queries with RLS
        return {
            "total_customers": 2847,
            "total_revenue": 13260000.00,
            "total_opportunities": 342,
            "avg_deal_value": 38772.00,
            "conversion_rate": 24.5,
            "avg_sales_cycle_days": 45
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/predictive-insights")
async def get_predictive_insights(req: Request):
    """Get predictive insights for analytics dashboard."""
    try:
        # Get user from auth
        user_data = None
        token = req.cookies.get("access_token") or req.headers.get("Authorization", "").replace("Bearer ", "")
        
        if token:
            auth_manager = req.app.state.auth_manager
            user_data = auth_manager.verify_jwt_token(token)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check permissions
        roles = user_data.get("roles", [])
        if "admin" not in roles and "analyst" not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mock predictive insights
        return {
            "insights": [
                {
                    "title": "Revenue Growth Trend",
                    "description": "Based on current trajectory, expect 15.3% revenue growth next quarter",
                    "confidence": 87,
                    "impact": "high"
                },
                {
                    "title": "Customer Churn Risk",
                    "description": "23 high-value customers showing decreased engagement patterns",
                    "confidence": 92,
                    "impact": "medium"
                },
                {
                    "title": "Product Demand Forecast",
                    "description": "Optimize Digital Solutions projected to increase demand by 28%",
                    "confidence": 78,
                    "impact": "high"
                }
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictive insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/cohort-analysis")
async def get_cohort_analysis(req: Request):
    """Get cohort analysis data for analytics dashboard."""
    try:
        # Get user from auth
        user_data = None
        token = req.cookies.get("access_token") or req.headers.get("Authorization", "").replace("Bearer ", "")
        
        if token:
            auth_manager = req.app.state.auth_manager
            user_data = auth_manager.verify_jwt_token(token)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check permissions
        roles = user_data.get("roles", [])
        if "admin" not in roles and "analyst" not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mock cohort data
        return {
            "cohorts": [
                {"month": "Q1 2024", "customers": 245, "retention_rate": 78, "revenue": 2450000},
                {"month": "Q2 2024", "customers": 312, "retention_rate": 82, "revenue": 3120000},
                {"month": "Q3 2024", "customers": 387, "retention_rate": 85, "revenue": 3870000},
                {"month": "Q4 2024", "customers": 421, "retention_rate": 87, "revenue": 4210000}
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cohort analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            if (
                not hasattr(req.app.state, "auth_manager")
                or req.app.state.auth_manager is None
            ):
                # Authentication subsystem is not initialized; fail with 503 so callers know to retry or admin to check logs
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication system not initialized. Please check application startup logs.",
                )
            auth_manager: AuthManager = req.app.state.auth_manager

            # Get token from cookie first (HTTP-only), then fallback to Authorization header
            token = req.cookies.get("auth_token")

            if not token:
                # Fallback to Authorization header for API calls
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
                        logger.debug(
                            f"🔐 RLS context set for user: {user_data.get('username')}"
                        )

                        # Get user's data scope for logging
                        data_scope = await rls_middleware.get_user_data_scope(
                            user_id, conn
                        )
                        user_data["data_scope"] = data_scope
                        logger.info(f"🔍 DEBUG - data_scope: {data_scope}")
                        
                        # Extract primary region for tool RLS filtering
                        # Tools expect user_context.get("region") at top level
                        # data_scope structure: {"territories": [{"territory": "West", "region": "USA-West"}], ...}
                        territories = data_scope.get("territories", [])
                        logger.info(f"🔍 DEBUG - territories extracted: {territories}")
                        if territories and len(territories) > 0:
                            primary_territory = territories[0].get("territory", "")
                            logger.info(f"🔍 DEBUG - primary_territory: {primary_territory}")
                            if primary_territory:
                                user_data["region"] = primary_territory
                                logger.info(f"🔐 User region set to: {primary_territory}")

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
            user_context=user_data,  # Pass user context for RLS filtering
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
                    success=True,
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
                        request=req,
                    )
                except Exception as audit_error:
                    logger.warning(f"Failed to log data access audit: {audit_error}")

        # Emit telemetry for the agent response
        model_name: Optional[str] = None
        if result.metadata:
            usage = result.metadata.get("usage")
            if isinstance(usage, dict):
                model_name = usage.get("model")
            elif "model" in result.metadata:
                model_name = result.metadata.get("model")

        trace_agent_response(
            conversation_id=result.thread_id,
            user_id=str(user_id) if user_id else None,
            response_text=result.response,
            model_name=model_name,
            extra={
                "agent_id": result.agent_id,
                "agent_type": agent_key,
                "run_id": result.run_id,
                "response_time_sec": response_time,
            },
        )

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
                    error=str(exc),
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
        log_level=settings.log_level.lower(),
    )
