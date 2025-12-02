"""
Database connection utility for Microsoft Fabric SQL Database.
Handles connection pooling and query execution.
"""
import pyodbc
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging
import struct
import subprocess
import json

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages connections to Microsoft Fabric SQL Database."""
    
    def __init__(self, connection_string: str, use_access_token: bool = False, 
                 client_id: Optional[str] = None, client_secret: Optional[str] = None, 
                 tenant_id: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            connection_string: SQL Server connection string
            use_access_token: Whether to use Azure access token for authentication
            client_id: Service principal client ID (for ClientSecretCredential)
            client_secret: Service principal client secret (for ClientSecretCredential)
            tenant_id: Azure tenant ID (for ClientSecretCredential)
        """
        self.connection_string = connection_string
        self.use_access_token = use_access_token
        self._access_token = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        
    def _get_azure_token(self) -> bytes:
        """Get Azure AD access token using ClientSecretCredential or DefaultAzureCredential."""
        try:
            # If service principal credentials provided, use ClientSecretCredential
            if self.client_id and self.client_secret and self.tenant_id:
                from azure.identity import ClientSecretCredential
                
                logger.info("Obtaining Azure access token using ClientSecretCredential (Service Principal)...")
                credential = ClientSecretCredential(
                    tenant_id=self.tenant_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
            else:
                # Use DefaultAzureCredential for Managed Identity or local dev
                from azure.identity import DefaultAzureCredential
                
                logger.info("Obtaining Azure access token using DefaultAzureCredential...")
                credential = DefaultAzureCredential()
            
            token = credential.get_token("https://database.windows.net/.default")
            token_bytes = token.token.encode('utf-8')
            
            # Format token for ODBC
            token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
            logger.info("✅ Successfully obtained Azure access token")
            return token_struct
        except Exception as e:
            logger.error(f"Failed to get Azure access token: {e}")
            logger.info("Attempting fallback to Azure CLI (for local development)...")
            try:
                import platform
                # On Windows, use az.cmd; on Linux/Mac, use az
                az_command = 'az.cmd' if platform.system() == 'Windows' else 'az'
                
                result = subprocess.run(
                    [az_command, 'account', 'get-access-token', '--resource', 'https://database.windows.net'],
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=False
                )
                token_data = json.loads(result.stdout)
                token = token_data['accessToken'].encode('utf-8')
                
                # Format token for ODBC
                token_struct = struct.pack(f'<I{len(token)}s', len(token), token)
                logger.info("✅ Successfully obtained Azure CLI access token")
                return token_struct
            except Exception as cli_error:
                logger.error(f"Failed to get Azure CLI access token: {cli_error}")
                raise RuntimeError("Could not obtain Azure access token from DefaultAzureCredential or Azure CLI")
        
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            pyodbc.Connection: Database connection
        """
        conn = None
        try:
            # Check if connection string already has Authentication parameter
            has_authentication = 'Authentication=' in self.connection_string
            
            if self.use_access_token and not has_authentication:
                # Only use manual access token if Authentication is not already in connection string
                logger.info("Obtaining Azure access token...")
                token_bytes = self._get_azure_token()
                logger.info(f"Connecting with access token to: {self.connection_string}")
                conn = pyodbc.connect(
                    self.connection_string, 
                    attrs_before={1256: token_bytes},  # SQL_COPT_SS_ACCESS_TOKEN
                    timeout=30
                )
                logger.info("✅ Database connection successful with access token")
            else:
                # Use connection string as-is (may include Authentication=ActiveDirectoryMsi)
                logger.info(f"Connecting to: {self.connection_string}")
                conn = pyodbc.connect(self.connection_string, timeout=30)
                logger.info("✅ Database connection successful")
            yield conn
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {e}")
            logger.error(f"Connection string: {self.connection_string}")
            logger.error(f"Using access token: {self.use_access_token}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None, 
        fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query to execute
            params: Query parameters (optional)
            fetch: Whether to fetch results (default: True)
            
        Returns:
            List of dictionaries with query results, or None if fetch=False
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch:
                    # Get column names
                    columns = [column[0] for column in cursor.description]
                    # Fetch all rows and convert to list of dicts
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                else:
                    conn.commit()
                    return None
            except pyodbc.Error as e:
                logger.error(f"Query execution error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_stored_procedure(
        self, 
        proc_name: str, 
        params: Optional[tuple] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a stored procedure.
        
        Args:
            proc_name: Name of the stored procedure
            params: Procedure parameters (optional)
            
        Returns:
            List of dictionaries with procedure results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(f"EXEC {proc_name} {','.join(['?'] * len(params))}", params)
                else:
                    cursor.execute(f"EXEC {proc_name}")
                
                # Check if there are results to fetch
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results = []
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
                    return results
                else:
                    conn.commit()
                    return None
            except pyodbc.Error as e:
                logger.error(f"Stored procedure execution error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute_many(
        self, 
        query: str, 
        params_list: List[tuple]
    ) -> None:
        """
        Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
            except pyodbc.Error as e:
                logger.error(f"Batch execution error: {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                logger.info("✅ Database connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False


def build_connection_string(
    server: str,
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    driver: str = "ODBC Driver 18 for SQL Server",
    use_azure_auth: bool = True,
    encrypt: bool = True,
    trust_server_cert: bool = False
) -> str:
    """
    Build a SQL Server connection string.
    
    Args:
        server: Server name (e.g., 'myserver.database.windows.net')
        database: Database name
        username: SQL authentication username (optional if using Azure AD)
        password: SQL authentication password (optional if using Azure AD)
        driver: ODBC driver name
        use_azure_auth: Use Azure AD authentication instead of SQL auth
        encrypt: Use encrypted connection
        trust_server_cert: Trust server certificate
        
    Returns:
        str: Connection string
    """
    import os
    conn_str_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}"
    ]
    
    if use_azure_auth:
        # In Azure (Managed Identity available), use ActiveDirectoryMsi
        # Locally, DatabaseConnection will use access tokens instead
        if any([
            os.getenv('WEBSITE_INSTANCE_ID'),  # App Service/Functions
            os.getenv('IDENTITY_ENDPOINT'),     # Managed Identity available
        ]):
            conn_str_parts.append("Authentication=ActiveDirectoryMsi")
    elif username and password:
        # SQL authentication
        conn_str_parts.append(f"UID={username}")
        conn_str_parts.append(f"PWD={password}")
    
    if encrypt:
        conn_str_parts.append("Encrypt=yes")
    
    if trust_server_cert:
        conn_str_parts.append("TrustServerCertificate=yes")
    
    return ";".join(conn_str_parts)
