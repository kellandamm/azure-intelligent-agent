"""
Auto-create managed identity user in SQL database on startup.
Called during application initialization when running in Azure App Service.
"""
import logging
import os

logger = logging.getLogger(__name__)


def setup_managed_identity_user(connection_string: str, use_access_token: bool = True) -> bool:
    """
    Create the App Service managed identity as a database user and grant it
    read/write/ddl/owner roles.  Runs once on first startup; subsequent
    startups detect the existing user and return immediately.

    Args:
        connection_string: SQL connection string for the application database.
        use_access_token:  Whether to authenticate via Azure AD token.

    Returns:
        True if the user already exists or was successfully created.
        False if setup failed (app continues with degraded DB access).
    """
    if not use_access_token or not os.getenv('WEBSITE_INSTANCE_ID'):
        logger.info("Not running in Azure App Service — skipping managed identity user setup")
        return True

    # WEBSITE_SITE_NAME is set by the platform to the App Service name, which is
    # also the managed identity display name used as the SQL contained-database user.
    app_name = os.getenv('WEBSITE_SITE_NAME')
    if not app_name:
        logger.warning("WEBSITE_SITE_NAME env var not set — cannot determine managed identity name")
        return False

    try:
        from utils.db_connection import DatabaseConnection

        # AAD contained-database users must be created in the target database,
        # not in master.  Connect directly with the supplied connection string.
        db_conn = DatabaseConnection(connection_string, use_access_token=use_access_token)

        with db_conn.get_connection() as conn:
            cursor = conn.cursor()

            # Check whether the user already exists in this database
            cursor.execute(
                "SELECT COUNT(*) FROM sys.database_principals WHERE name = ?",
                app_name,
            )
            exists = cursor.fetchone()[0]

            if not exists:
                logger.info("Creating managed identity user [%s] in database...", app_name)
                try:
                    cursor.execute(f"CREATE USER [{app_name}] FROM EXTERNAL PROVIDER")
                    cursor.execute(f"ALTER ROLE db_datareader ADD MEMBER [{app_name}]")
                    cursor.execute(f"ALTER ROLE db_datawriter ADD MEMBER [{app_name}]")
                    cursor.execute(f"ALTER ROLE db_ddladmin ADD MEMBER [{app_name}]")
                    cursor.execute(f"ALTER ROLE db_owner ADD MEMBER [{app_name}]")
                    conn.commit()
                    logger.info("✅ Managed identity user [%s] created and roles granted", app_name)
                except Exception as create_err:
                    logger.warning("Could not create user (may already exist): %s", create_err)
                    # User may exist under a different creation path — try granting roles anyway
                    try:
                        cursor.execute(f"ALTER ROLE db_datareader ADD MEMBER [{app_name}]")
                        cursor.execute(f"ALTER ROLE db_datawriter ADD MEMBER [{app_name}]")
                        cursor.execute(f"ALTER ROLE db_ddladmin ADD MEMBER [{app_name}]")
                        conn.commit()
                        logger.info("✅ Roles granted to existing user [%s]", app_name)
                    except Exception:
                        pass
            else:
                logger.info("✅ Managed identity user [%s] already exists — no action needed", app_name)

            cursor.close()
            return True

    except Exception as e:
        logger.error("Failed to set up managed identity user: %s", e)
        logger.warning("Application will continue but database operations may fail until access is granted manually")
        return False
