# Changelog

All notable changes to the Azure Intelligent Agent application will be documented in this file.

## [Unreleased]

### Planned
- **[2026-02-17]** Replace mock data with Azure AI Foundry Data Agents
  - Use Data Agents to query Microsoft Fabric lakehouse directly
  - Remove hardcoded mock data and custom query code
  - Enable natural language queries for sales, inventory, customers, and performance metrics
  - Maintain RLS filtering through Fabric permissions
  - See agentsdemos implementation-plan.md for detailed approach

---

## [1.2.0] - 2026-02-17 (Sprint 3 - Ready for Merge)

### Added - Three-Factor Architecture Implementation
- **Created services/ layer** for business logic separation
  - `AuthService` (services/auth_service.py) - Authentication verification for API and page routes
  - `ChatService` (services/chat_service.py) - Chat processing, RLS context, logging, telemetry
  - `AdminService` (services/admin_service.py) - Configuration, stats, health checks
  - `AnalyticsService` (services/analytics_service.py) - Metrics, insights, cohort analysis
- **Created new route modules** for clean HTTP handling
  - `routes_pages.py` (app/app/routes_pages.py) - HTML page routes
  - `routes_chat.py` (app/app/routes_chat.py) - Chat API endpoint with validation
  - `routes_admin_api.py` (app/app/routes_admin_api.py) - Admin API endpoints
  - `routes_analytics_api.py` (app/app/routes_analytics_api.py) - Analytics API endpoints
- **Created unit test suite** - 14 test cases for services layer (tests/unit/)
- **Agents directory** (app/app/agents/) - Structured agent definitions

### Added - Azure Deployment Readiness
- **Registered new routers** in main.py for proper routing precedence
- **Added test dependencies** to requirements.txt (pytest, pytest-asyncio, pytest-mock)
- **Created Azure deployment validation capabilities**
- **Enhanced deployment documentation** with comprehensive guides

### Changed - Architecture Improvements
- **Refactored architecture** following Three-Factor pattern:
  - Factor 1: Routes (HTTP concerns only)
  - Factor 2: Services (business logic)
  - Factor 3: Configuration (startup and registration)
- **Improved maintainability** - Business logic isolated from HTTP framework
- **Enhanced testability** - Services use plain Python, no HTTP mocking needed
- **Azure compatibility verified** - All imports use absolute paths

### Documentation
- Established development workflow: → test → azure-intelligent-agent
- Created detailed Three-Factor Architecture guide
- Created comprehensive Azure deployment guide with validation
- Updated implementation plan with completed and planned tasks
- Added changelog tracking for both repositories

### Deployment
- ✅ Ready for Azure App Service deployment
- ✅ Managed Identity support configured
- ✅ Docker build and ACR push ready
- ✅ All validation checks pass

### Files Modified/Added
Modified files:
- app/.env.template
- app/Fabric/* (multiple database and function files)
- app/app/config.py
- app/app/routes_admin_agents.py
- app/app/routes_auth.py
- app/app/routes_graphrag_proxy.py
- app/main.py
- app/static/* (admin pages)
- bicep/main-foundry-mcp.bicep
- fabric/* (database and function updates)
- scripts/README.md

New files:
- .env.example
- CONFIGURATION.md
- CREATE_ADMIN_USER.md
- DEPLOYMENT.md
- app/Fabric/rls_security_policies.sql
- app/app/agents/ (directory)
- app/app/routes_admin_api.py
- app/app/routes_analytics_api.py
- app/app/routes_chat.py
- app/app/routes_pages.py
- app/main_refactored.py
- app/rate_limiter.py
- app/services/* (4 service files)
- app/static/contoso-sales-chat.html
- deploy.ps1
- docs/CHANGELOG.md
- docs/IMPLEMENTATION_PLAN.md
- docs/MERGE_SUMMARY.md
- tests/unit/ (directory)

---

## [1.1.0] - 2026-02-05

### Added
- **Merged improvements**: All UI and routing improvements integrated
- Created comprehensive implementation plan with detailed code quality roadmap
- Added CHANGELOG.md for tracking version history
- New contoso-sales-chat.html with consistent navigation across application

### Changed
- **Refactored /chat route**: Now serves contoso-sales-chat.html from static files instead of 1100+ lines of embedded HTML
- Improved code maintainability by separating presentation from logic
- Enhanced chat interface with consistent header design and navigation dropdown

### Documentation
- Created IMPLEMENTATION_PLAN.md with three-factor architecture guidance
- Added five essential settings pattern documentation
- Documented error handling framework requirements
- Added logging infrastructure specifications
- Defined comprehensive testing strategy (unit and integration tests)

---

## [1.0.0] - 2026-02-04

### Added
- Production-ready Azure Intelligent Agent starter template
- Infrastructure as Code using Bicep templates
- Azure Developer CLI (azd) deployment support
- Comprehensive security features (JWT auth, RLS, rate limiting)
- Multi-agent orchestration with specialized agents
- Microsoft Fabric integration for data analytics
- Power BI embedding for dashboards
- Row-Level Security (RLS) support
- Audit logging for compliance

### Security
- JWT authentication with HttpOnly cookies
- Rate limiting on authentication endpoints
- Input validation and prompt injection detection
- CORS protection with configurable domains
- Security headers (XSS, clickjacking protection)
- No default credentials - secure admin setup required
- Database-level Row-Level Security infrastructure

### Infrastructure
- Docker containerization
- Azure Container Registry integration
- Azure App Service deployment
- Automated health checks
- Application Insights integration
- Comprehensive logging and telemetry

---

## Template for Future Entries

### Added
- New features

### Fixed
- Bug fixes

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Security
- Security updates

### Performance
- Performance improvements

### Documentation
- Documentation updates
