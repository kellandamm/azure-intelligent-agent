"""
Auto-create managed identity user in SQL database on startup
This script should be called during application initialization
"""
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)


def setup_managed_identity_user(connection_string: str, use_access_token: bool = True) -> bool:
    """
    Create managed identity user in database if it doesn't exist.
    This should be run when the app starts up with managed identity.
    
    Args:
        connection_string: SQL connection string  
        use_access_token: Whether to use Azure AD token
        
    Returns:
        True if setup successful or user already exists
    """
    if not use_access_token or not os.getenv('WEBSITE_INSTANCE_ID'):
        logger.info("Not running in Azure with managed identity, skipping user setup")
        return True
        
    try:
        from utils.db_connection import DatabaseConnection
        import pyodbc
        
        # Connect to master database to create login if needed
        master_conn_str = connection_string.replace("DATABASE=aiagentsdb", "DATABASE=master")
        db_conn = DatabaseConnection(master_conn_str, use_access_token=use_access_token)
        
        with db_conn.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists in the target database
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.database_principals 
                WHERE name = 'agentframework-demo-eastus2'
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                logger.info("Creating managed identity user in database...")
                try:
                    # Create user from external provider (managed identity)
                    cursor.execute("CREATE USER [agentframework-demo-eastus2] FROM EXTERNAL PROVIDER")
                    
                    # Grant necessary permissions
                    cursor.execute("ALTER ROLE db_datareader ADD MEMBER [agentframework-demo-eastus2]")
                    cursor.execute("ALTER ROLE db_datawriter ADD MEMBER [agentframework-demo-eastus2]")
                    cursor.execute("ALTER ROLE db_ddladmin ADD MEMBER [agentframework-demo-eastus2]")
                    cursor.execute("ALTER ROLE db_owner ADD MEMBER [agentframework-demo-eastus2]")
                    
                    conn.commit()
                    logger.info("✅ Managed identity user created and permissions granted")
                except Exception as e:
                    logger.warning(f"Could not create user (may already exist or lack permissions): {e}")
                    # Try to grant permissions anyway
                    try:
                        cursor.execute("ALTER ROLE db_datareader ADD MEMBER [agentframework-demo-eastus2]")
                        cursor.execute("ALTER ROLE db_datawriter ADD MEMBER [agentframework-demo-eastus2]")
                        cursor.execute("ALTER ROLE db_ddladmin ADD MEMBER [agentframework-demo-eastus2]")
                        conn.commit()
                        logger.info("✅ Permissions granted to existing user")
                    except:
                        pass
            else:
                logger.info("✅ Managed identity user already exists")
            
            cursor.close()
            return True
            
    except Exception as e:
        logger.error(f"Failed to setup managed identity user: {e}")
        logger.warning("Application will continue but database operations may fail")
        return False
