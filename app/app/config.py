"""Configuration management for Agent Framework with Fabric Integration."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-08-01-preview"

    # Azure AI Foundry Project
    project_endpoint: Optional[str] = None
    model_deployment_name: str = "gpt-4o"
    use_published_agent_applications: bool = False

    # Microsoft Fabric Configuration (data platform)
    fabric_workspace_id: Optional[str] = None
    fabric_connection_id: Optional[str] = None

    # Azure AI Foundry Agent IDs (set these after creating agents in the Foundry portal)
    orchestrator_agent_id: Optional[str] = None
    orchestrator_agent_name: str = "RetailAssistantOrchestrator"
    orchestrator_agent_app_name: Optional[str] = None
    sales_agent_id: Optional[str] = None
    sales_agent_app_name: Optional[str] = None
    realtime_agent_id: Optional[str] = None
    realtime_agent_app_name: Optional[str] = None
    analytics_agent_id: Optional[str] = None
    analytics_agent_app_name: Optional[str] = None
    financial_agent_id: Optional[str] = None
    financial_agent_app_name: Optional[str] = None
    support_agent_id: Optional[str] = None
    support_agent_app_name: Optional[str] = None
    operations_agent_id: Optional[str] = None
    operations_agent_app_name: Optional[str] = None
    customer_success_agent_id: Optional[str] = None
    customer_success_agent_app_name: Optional[str] = None
    operations_excellence_agent_id: Optional[str] = None
    operations_excellence_agent_app_name: Optional[str] = None
    
    # Power BI Integration Configuration
    powerbi_workspace_id: Optional[str] = None
    powerbi_workspace_name: Optional[str] = None
    powerbi_report_id: Optional[str] = None
    powerbi_client_id: Optional[str] = None
    powerbi_client_secret: Optional[str] = None
    powerbi_tenant_id: Optional[str] = None
    powerbi_connection_url: Optional[str] = None
    
    # Azure Deployment
    azure_subscription_id: Optional[str] = None
    azure_resource_group: str = ""
    azure_location: str = "eastus2"
    azure_container_registry: str = ""
    application_insights_name: str = "agentframework-demos"
    
    # Application Configuration
    app_port: int = 8080
    log_level: str = "INFO"
    enable_tracing: bool = True

    # Agent backend selection (Azure AI Foundry is the recommended default)
    use_foundry_agents: bool = True  # Set USE_FOUNDRY_AGENTS=false to use code-based agent backend

    # MCP Server Configuration
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 3000
    enable_mcp: bool = True  # Enable MCP server for function calls

    
    
    # Database Configuration for Authentication (Optional - only needed if authentication is enabled)
    sql_server: Optional[str] = None  # e.g., 'myserver.database.windows.net'
    sql_database: Optional[str] = None  # e.g., 'your-database-name'
    sql_username: Optional[str] = None  # Optional if using Azure AD auth
    sql_password: Optional[str] = None  # Optional if using Azure AD auth
    sql_driver: str = "ODBC Driver 18 for SQL Server"
    sql_use_azure_auth: bool = True  # Use Azure AD authentication
    sql_encrypt: bool = True
    sql_trust_server_cert: bool = False
    
    # Fabric Lakehouse Configuration for Analytics (Separate from Auth DB)
    fabric_sql_server: Optional[str] = None  # Fabric SQL Analytics Endpoint
    fabric_sql_database: Optional[str] = None  # Fabric Lakehouse name
    fabric_sql_driver: str = "ODBC Driver 18 for SQL Server"
    fabric_sql_use_azure_auth: bool = True
    fabric_sql_encrypt: bool = True
    fabric_sql_trust_server_cert: bool = False
    fabric_client_id: Optional[str] = None  # Service principal client ID for Fabric
    fabric_client_secret: Optional[str] = None  # Service principal client secret for Fabric
    fabric_tenant_id: Optional[str] = None  # Tenant ID (defaults to powerbi_tenant_id)
    
    # Authentication Configuration (Optional - only needed if authentication is enabled)
    jwt_secret: Optional[str] = None  # Secret key for JWT token encoding
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24  # Token expiry in hours
    enable_authentication: bool = False  # Master switch for authentication (default: False)
    
    # Microsoft Purview Configuration (for Data Governance)
    purview_account_name: Optional[str] = None  # e.g., 'mypurview'
    enable_purview: bool = False  # Enable Purview integration for data governance
    enable_rls: bool = True  # Enable Row-Level Security (default: True when auth enabled)
    enable_audit_logging: bool = True  # Enable data access audit logging
    
    @property
    def database_connection_string(self) -> str:
        """Generate SQL Server connection string for authentication database."""
        if not self.enable_authentication:
            raise ValueError("Authentication is disabled. Database connection string not available.")
        if not self.sql_server or not self.sql_database:
            raise ValueError("SQL_SERVER and SQL_DATABASE must be set when authentication is enabled.")
        
        from utils.db_connection import build_connection_string
        return build_connection_string(
            server=self.sql_server,
            database=self.sql_database,
            username=self.sql_username,
            password=self.sql_password,
            driver=self.sql_driver,
            use_azure_auth=self.sql_use_azure_auth,
            encrypt=self.sql_encrypt,
            trust_server_cert=self.sql_trust_server_cert
        )
    
    @property
    def fabric_connection_string(self) -> str:
        """Generate Fabric SQL Analytics Endpoint connection string for analytics."""
        if not self.fabric_sql_server or not self.fabric_sql_database:
            # Fallback to regular SQL if Fabric not configured
            return self.database_connection_string
        
        from utils.db_connection import build_connection_string
        return build_connection_string(
            server=self.fabric_sql_server,
            database=self.fabric_sql_database,
            username=None,  # Fabric uses Managed Identity
            password=None,
            driver=self.fabric_sql_driver,
            use_azure_auth=self.fabric_sql_use_azure_auth,
            encrypt=self.fabric_sql_encrypt,
            trust_server_cert=self.fabric_sql_trust_server_cert
        )
    
    def validate_auth_config(self) -> bool:
        """Validate authentication configuration."""
        if not self.enable_authentication:
            return True
        
        if not self.sql_server:
            raise ValueError("SQL_SERVER is required when ENABLE_AUTHENTICATION=true")
        if not self.sql_database:
            raise ValueError("SQL_DATABASE is required when ENABLE_AUTHENTICATION=true")
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET is required when ENABLE_AUTHENTICATION=true")
        
        return True
    
    @property
    def effective_fabric_tenant_id(self) -> Optional[str]:
        """Get the effective tenant ID for Fabric (fabric_tenant_id or powerbi_tenant_id)."""
        return self.fabric_tenant_id or self.powerbi_tenant_id
    
    @property
    def mcp_server_url(self) -> str:
        """Generate MCP server URL."""
        return f"http://{self.mcp_server_host}:{self.mcp_server_port}"


# Global settings instance
settings = Settings()
