# Changelog

All notable changes to the Azure Intelligent Agent application will be documented in this file.

## [Unreleased]

### Added - Published Agent Application Mode (Responses Protocol)
- Added `USE_PUBLISHED_AGENT_APPLICATIONS` configuration flag to support routing through published Agent Applications.
- Added published application name settings for orchestrator and specialists:
  - `ORCHESTRATOR_AGENT_APP_NAME`
  - `SALES_AGENT_APP_NAME`
  - `REALTIME_AGENT_APP_NAME`
  - `ANALYTICS_AGENT_APP_NAME`
  - `FINANCIAL_AGENT_APP_NAME`
  - `SUPPORT_AGENT_APP_NAME`
  - `OPERATIONS_AGENT_APP_NAME`
  - `CUSTOMER_SUCCESS_AGENT_APP_NAME`
  - `OPERATIONS_EXCELLENCE_AGENT_APP_NAME`

### Changed - Agent Settings Script and Docs
- `scripts/get-agent-ids.ps1` now supports `-EnablePublishedMode` during `-Apply`.
- Script now applies both `*_AGENT_ID` and `*_AGENT_APP_NAME` settings.
- Updated deployment guides to document published mode activation and settings.

### Changed - Microsoft AI Foundry as Primary Platform
- **All deployment documentation and infrastructure now prioritizes Microsoft AI Foundry over Azure OpenAI**
  - Azure OpenAI is now presented as an optional fallback component
  - Microsoft AI Foundry is required for agent functionality
  - Azure OpenAI only needed if deploying separate model resource
- **Updated documentation hierarchy**:
  - `docs/QUICK_START.md`: Restructured prerequisites to require Foundry, make Azure OpenAI optional
  - Section reordering: Foundry configuration shown first in all deployment phases
  - Clear labeling: "(Required)" for Foundry, "(Optional - only if not using Foundry models)" for Azure OpenAI
- **Updated infrastructure code**:
  - `bicep/main.bicep`: Reordered parameters to place Azure AI Foundry section before Azure OpenAI
  - All agent ID parameters now marked "(Required)" in descriptions
  - Section headers clarified: "Agent IDs (Azure AI Foundry) & Data Platform (Microsoft Fabric)"
  - `bicep/main.bicepparam`: Restructured with Foundry first, dedicated agent IDs section, Azure OpenAI moved to bottom
  - `bicep/main.json`: Recompiled with updated parameter order and descriptions
- **Updated configuration templates**:
  - `app/.env.template`: Microsoft AI Foundry section moved to top, clearly marked as required
  - Azure OpenAI section moved down, clearly marked as optional with empty defaults

### Planned
- **[2026-02-17]** Replace mock data with Azure AI Foundry Data Agents
  - Use Data Agents to query Microsoft Fabric lakehouse directly
  - Remove hardcoded mock data and custom query code
  - Enable natural language queries for sales, inventory, customers, and performance metrics
  - Maintain RLS filtering through Fabric permissions

---

## [1.4.0] - 2026-03-30

### Changed - Microsoft AI Foundry as Default Agent Backend

#### Agent Backend Defaults
- **`USE_FOUNDRY_AGENTS` now defaults to `true`** in all config files and bicep templates
- Application now uses **Microsoft AI Foundry native agents** by default (was code-based backend)
- Code-based backend remains available by setting `USE_FOUNDRY_AGENTS=false`

#### SDK Migration (Azure AI Foundry Backend)
- **Migrated from `azure.ai.projects` to `azure.ai.agents`** SDK
  - Replaced `AIProjectClient` with `AgentsClient`
  - Updated all API call patterns (`client.threads`, `client.messages`, `client.runs`)
  - Removed `PROJECT_CONNECTION_STRING` requirement (endpoint-only authentication)
  - Fixed critical `ImportError` bug that prevented Foundry backend from starting

#### Agent Configuration Cleanup
- **Removed `fabric_` prefix** from all agent ID environment variables:
  - `FABRIC_ORCHESTRATOR_AGENT_ID` → `ORCHESTRATOR_AGENT_ID`
  - `FABRIC_SALES_AGENT_ID` → `SALES_AGENT_ID`
  - All 9 agent IDs renamed for clarity (agents run in Foundry, not Fabric)
- Updated bicep files (`main.bicep`, `containerApps-foundry-mcp.bicep`) with new parameter names
- Updated deployment scripts (`set-agent-ids.ps1`) with new environment variables
- Added missing `OPERATIONS_AGENT_ID` parameter for Operations Coordinator agent

#### New Tools & Documentation
- **Enhanced script: `scripts/get-agent-ids.ps1`**
  - **Retrieves agent IDs from Microsoft AI Foundry** by agent name
  - Maps agents to application environment variables automatically
  - Can apply agent IDs directly to App Service settings with `-Apply` flag
  - Shows agent definitions (names + system prompts) with `-Create` flag for manual portal setup
  - Note: Automatic agent creation via API is not available - agents must be created manually in portal
  - Eliminates manual agent ID copy/paste workflow
- **Updated `docs/QUICK_START.md`**
  - **NEW: Complete step-by-step agent creation guide** with all 9 agent names and system prompts
  - Clear instructions for creating agents manually in Microsoft AI Foundry portal
  - Documents automated ID retrieval and App Service configuration workflow
  - Emphasizes exact naming requirements (case-sensitive) for script to work
  - Clarifies that Foundry is the primary backend (code-based is optional)
- **Updated `docs/AZURE_FOUNDRY_MCP_DEPLOYMENT.md`**
  - New portal navigation with updated endpoint format
  - System prompt suggestions for all 9 Foundry agents
  - Updated troubleshooting with new error messages

#### Infrastructure Updates
- All bicep templates set `USE_FOUNDRY_AGENTS=true` by default
- All `.env` templates document Foundry as the default backend
- Removed deprecated `PROJECT_CONNECTION_STRING` from all infrastructure files

#### Files Modified
**Configuration:**
- `app/app/config.py` - Agent IDs renamed, `use_foundry_agents=True` default, removed connection string
- `app/config.py` - Agent IDs renamed, removed connection string
- `.env.example` - Agent IDs renamed, `USE_FOUNDRY_AGENTS=true` added
- `app/.env.template` - Agent IDs renamed, `USE_FOUNDRY_AGENTS=true` added

**Infrastructure:**
- `bicep/main.bicep` - Parameters renamed, `USE_FOUNDRY_AGENTS=true` in app settings
- `bicep/main.json` - Recompiled with new parameters
- `bicep/modules/containerApps-foundry-mcp.bicep` - Parameters renamed, connection string removed

**Code:**
- `app/app/azure_foundry_agent_manager.py` - Full rewrite with `azure.ai.agents` SDK
- `app/app/agent_framework_manager.py` - Agent ID references updated
- `app/agent_framework_manager.py` - Agent ID references updated
- `app/demos/fabric_sales.py` - Removed broken endpoint property reference
- `app/demos/fabric_realtime.py` - Removed broken endpoint property reference
- `app/main.py` - Error message updated (removed connection string reference)

**Scripts:**
- `scripts/set-agent-ids.ps1` - New parameters with correct naming, removed connection string
- `scripts/get-agent-ids.ps1` - **NEW** automated agent retrieval tool

**Documentation:**
- `docs/QUICK_START.md` - Emphasizes Foundry as default, documents new workflow
- `docs/AZURE_FOUNDRY_MCP_DEPLOYMENT.md` - Complete rewrite with new SDK patterns

### Fixed
- Fixed `ImportError` when `USE_FOUNDRY_AGENTS=true` (was importing unavailable `azure.ai.projects` package)
- Fixed missing `OperationsCoordinatorAgentId` parameter in `set-agent-ids.ps1`
- Removed broken `fabric_sales_agent_endpoint` and `fabric_realtime_agent_endpoint` properties

---

## [1.3.0] - 2026-03-06

### Added - Azure Policy Compliance + Pre-Deployment Validation

#### Infrastructure (bicep/modules/sqlServer.bicep)
- `restrictOutboundNetworkAccess` parameter now defaults to `'Enabled'`, preventing SQL from making arbitrary outbound connections
- `AllowAllWindowsAzureIps` firewall rule is now conditional on `publicNetworkAccess == 'Enabled'` — omitted when private endpoint is used
- `administrators` block moved **inline** onto the SQL server resource (`properties.administrators`). ARM policy evaluates Azure AD-only authentication on the server resource at validation time; separate child resources (`/administrators`, `/azureADOnlyAuthentications`) are not inspected at that point
- `@maxLength(36)` constraint on `azureAdAdminSid` prevents placeholder values from causing `InvalidResourceIdSegment` at ARM validation

#### New: Pre-Deployment Policy Validator (scripts/validate-policy-compliance.ps1)
- **Parameter health checks** — catches unfilled placeholders, empty GUID fields, and mismatched AD login/SID pairs before hitting ARM
- **Template validation** — `az bicep build` for new resource groups; `az deployment group validate` for existing ones; surfaces `RequestDisallowedByPolicy` details
- **What-if preview** — shows planned resource diffs and highlights any policy blocks
- **Policy audit** — lists active deny assignments and highlights SQL/network/auth-related policies
- **9 static template checks** — verifies `publicNetworkAccess`, `restrictOutboundNetworkAccess`, `minimalTlsVersion`, firewall rule conditionality, inline administrators block, VNet integration, and param guards

#### Documentation
- README, CONFIGURATION.md, QUICK_REFERENCE.md updated with private endpoint architecture, policy guidance, and `azd init` workflow
- CHANGELOG.md updated

### Fixed
- SQL server Bicep deployment no longer blocked by Azure subscription-level policies requiring disabled public network access and Entra-only authentication
- `InvalidResourceIdSegment` error caused by placeholder values in `sqlAzureAdAdminSid`

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


## Backend naming and routing update

- Added a neutral backend selector module for shared imports.
- Standardized backend naming across docs and app logs.
- Renamed backend manager classes to make the routing model explicit.
- Documented the Foundry-hosted agent mode as app-driven routing.
