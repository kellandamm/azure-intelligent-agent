"""
API key management for programmatic access
"""
from fastapi import HTTPException, Header, Depends
from typing import Optional
import secrets
import hashlib
import pyodbc
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manage API keys for programmatic access to the service"""
    
    def __init__(self):
        self.table_initialized = False
    
    def _get_connection(self):
        """Get database connection"""
        server = os.getenv("SQL_SERVER")
        database = os.getenv("SQL_DATABASE")
        
        conn_str = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server={server};"
            f"Database={database};"
            "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
        )

        if os.getenv("SQL_USE_AZURE_AUTH") == "true":
            # Use an access token (Managed Identity or DefaultAzureCredential)
            from azure.identity import DefaultAzureCredential
            import struct

            credential = DefaultAzureCredential()
            token = credential.get_token("https://database.windows.net/.default")
            token_bytes = token.token.encode("utf-8")
            token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

            return pyodbc.connect(conn_str, attrs_before={1256: token_struct})

        username = os.getenv("SQL_USERNAME")
        password = os.getenv("SQL_PASSWORD")
        conn_str += f"UID={username};PWD={password};"
        return pyodbc.connect(conn_str)
    
    def _initialize_table(self):
        """Create API keys table if not exists"""
        if self.table_initialized:
            return
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create API keys table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ApiKeys')
                BEGIN
                    CREATE TABLE ApiKeys (
                        KeyID INT IDENTITY(1,1) PRIMARY KEY,
                        KeyHash NVARCHAR(64) NOT NULL UNIQUE,
                        UserID INT NOT NULL,
                        Name NVARCHAR(255) NOT NULL,
                        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                        ExpiresAt DATETIME2 NOT NULL,
                        LastUsedAt DATETIME2 NULL,
                        UsageCount INT NOT NULL DEFAULT 0,
                        Revoked BIT NOT NULL DEFAULT 0,
                        RevokedAt DATETIME2 NULL,
                        RevokedBy NVARCHAR(255) NULL,
                        Scopes NVARCHAR(MAX) NULL,
                        FOREIGN KEY (UserID) REFERENCES Users(UserID)
                    )
                    
                    CREATE INDEX IX_ApiKeys_KeyHash ON ApiKeys(KeyHash)
                    CREATE INDEX IX_ApiKeys_UserID ON ApiKeys(UserID)
                    CREATE INDEX IX_ApiKeys_ExpiresAt ON ApiKeys(ExpiresAt)
                END
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.table_initialized = True
            logger.info("API keys table initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize API keys table: {e}")
            raise
    
    async def generate_key(
        self,
        user_id: int,
        name: str,
        expires_days: int = 90,
        scopes: Optional[list] = None
    ) -> dict:
        """
        Generate a new API key
        
        Args:
            user_id: User ID the key belongs to
            name: Descriptive name for the key
            expires_days: Number of days until expiration (default: 90)
            scopes: List of permissions (e.g., ["chat:read", "chat:write"])
        
        Returns:
            dict with 'key' (show once) and metadata
        """
        self._initialize_table()
        
        try:
            # Generate secure random key
            key = f"sk_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
            scopes_json = ",".join(scopes) if scopes else None
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO ApiKeys (KeyHash, UserID, Name, ExpiresAt, Scopes)
                VALUES (?, ?, ?, ?, ?)
            """, key_hash, user_id, name, expires_at, scopes_json)
            
            key_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Generated API key for user {user_id}: {name}")
            
            return {
                "key": key,  # Show only once!
                "key_id": key_id,
                "name": name,
                "expires_at": expires_at.isoformat(),
                "scopes": scopes
            }
            
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise
    
    async def validate_key(self, key: str) -> dict:
        """
        Validate API key and return user context
        
        Returns:
            dict with user_id, scopes, and metadata
        
        Raises:
            HTTPException if invalid, expired, or revoked
        """
        self._initialize_table()
        
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT UserID, ExpiresAt, Revoked, Scopes, UsageCount
                FROM ApiKeys
                WHERE KeyHash = ?
            """, key_hash)
            
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                conn.close()
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            user_id, expires_at, revoked, scopes, usage_count = result
            
            # Check if revoked
            if revoked:
                cursor.close()
                conn.close()
                raise HTTPException(status_code=401, detail="API key has been revoked")
            
            # Check if expired
            if expires_at < datetime.utcnow():
                cursor.close()
                conn.close()
                raise HTTPException(status_code=401, detail="API key has expired")
            
            # Update last used timestamp and usage count
            cursor.execute("""
                UPDATE ApiKeys
                SET LastUsedAt = GETUTCDATE(),
                    UsageCount = UsageCount + 1
                WHERE KeyHash = ?
            """, key_hash)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            from app.observability import track_authentication
            track_authentication("apikey", "success", str(user_id))
            
            return {
                "user_id": user_id,
                "scopes": scopes.split(",") if scopes else [],
                "usage_count": usage_count + 1
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            raise HTTPException(status_code=500, detail="API key validation failed")
    
    async def revoke_key(self, key_id: int, revoked_by: str):
        """Revoke an API key"""
        self._initialize_table()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE ApiKeys
                SET Revoked = 1,
                    RevokedAt = GETUTCDATE(),
                    RevokedBy = ?
                WHERE KeyID = ?
            """, revoked_by, key_id)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Revoked API key {key_id} by {revoked_by}")
            
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            raise
    
    async def list_keys(self, user_id: int) -> list:
        """List all API keys for a user"""
        self._initialize_table()
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT KeyID, Name, CreatedAt, ExpiresAt, LastUsedAt, 
                       UsageCount, Revoked, Scopes
                FROM ApiKeys
                WHERE UserID = ?
                ORDER BY CreatedAt DESC
            """, user_id)
            
            keys = []
            for row in cursor.fetchall():
                keys.append({
                    "key_id": row[0],
                    "name": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                    "expires_at": row[3].isoformat() if row[3] else None,
                    "last_used_at": row[4].isoformat() if row[4] else None,
                    "usage_count": row[5],
                    "revoked": bool(row[6]),
                    "scopes": row[7].split(",") if row[7] else []
                })
            
            cursor.close()
            conn.close()
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list API keys: {e}")
            raise


# Global API key manager instance
api_key_manager = APIKeyManager()


async def get_current_user_or_api_key(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    Support both JWT tokens and API keys for authentication
    
    Usage:
        @app.post("/api/chat")
        async def chat(
            request: ChatRequest,
            user: dict = Depends(get_current_user_or_api_key)
        ):
            user_id = user["user_id"]
            ...
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if authorization.startswith("Bearer "):
        # JWT token authentication
        token = authorization.replace("Bearer ", "")
        from app.routes_auth import verify_jwt_token
        return await verify_jwt_token(token)
        
    elif authorization.startswith("ApiKey "):
        # API key authentication
        api_key = authorization.replace("ApiKey ", "")
        key_info = await api_key_manager.validate_key(api_key)
        
        # Return user context similar to JWT
        return {
            "user_id": key_info["user_id"],
            "scopes": key_info["scopes"],
            "auth_method": "apikey"
        }
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use 'Bearer <token>' or 'ApiKey <key>'"
        )
