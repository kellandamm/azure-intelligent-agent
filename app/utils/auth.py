"""
Authentication and authorization module for Agent Framework.
Handles user authentication, JWT tokens, and permission checking.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from utils.db_connection import DatabaseConnection

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


class AuthManager:
    """Manages authentication and authorization."""
    
    def __init__(
        self, 
        db_connection: DatabaseConnection,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expiry_hours: int = 24
    ):
        """
        Initialize authentication manager.
        
        Args:
            db_connection: Database connection instance
            jwt_secret: Secret key for JWT encoding
            jwt_algorithm: JWT algorithm (default: HS256)
            jwt_expiry_hours: JWT token expiry in hours (default: 24)
        """
        self.db = db_connection
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiry_hours = jwt_expiry_hours
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create a JWT token for a user.
        
        Args:
            user_data: User information to encode in token
            
        Returns:
            str: JWT token
        """
        expiry = datetime.utcnow() + timedelta(hours=self.jwt_expiry_hours)
        
        payload = {
            "user_id": user_data["UserID"],
            "username": user_data["Username"],
            "email": user_data["Email"],
            "roles": user_data.get("Roles", "").split(",") if user_data.get("Roles") else [],
            "permissions": user_data.get("Permissions", "").split(",") if user_data.get("Permissions") else [],
            "exp": expiry,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict with user data if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            return payload
        except InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Dict with user data if authenticated, None otherwise
        """
        try:
            # Get user from database
            results = self.db.execute_stored_procedure(
                "dbo.sp_GetUserByUsername",
                (username,)
            )
            
            if not results or len(results) == 0:
                logger.warning(f"User not found: {username}")
                return None
            
            user = results[0]
            
            # Check if account is locked
            if user.get("AccountLockedUntil"):
                if user["AccountLockedUntil"] > datetime.utcnow():
                    logger.warning(f"Account locked: {username}")
                    return None
            
            # Check if user is active
            if not user.get("IsActive"):
                logger.warning(f"Inactive user attempted login: {username}")
                return None
            
            # Verify password
            if not self.verify_password(password, user["PasswordHash"]):
                # Record failed login attempt
                self.db.execute_stored_procedure(
                    "dbo.sp_RecordFailedLogin",
                    (username,)
                )
                logger.warning(f"Invalid password for user: {username}")
                return None
            
            # Update last login
            self.db.execute_stored_procedure(
                "dbo.sp_UpdateLastLogin",
                (user["UserID"],)
            )
            
            logger.info(f"✅ User authenticated: {username}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Optional[int]:
        """
        Create a new user.
        
        Args:
            username: Username
            email: Email address
            password: Plain text password
            first_name: First name (optional)
            last_name: Last name (optional)
            created_by: UserID of creator (optional)
            
        Returns:
            int: New user ID if successful, None otherwise
        """
        try:
            hashed_password = self.hash_password(password)
            
            query = """
                INSERT INTO dbo.Users 
                (Username, Email, PasswordHash, FirstName, LastName, CreatedBy)
                OUTPUT INSERTED.UserID
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            results = self.db.execute_query(
                query,
                (username, email, hashed_password, first_name, last_name, created_by),
                fetch=True
            )
            
            if results:
                user_id = results[0]["UserID"]
                logger.info(f"✅ User created: {username} (ID: {user_id})")
                return user_id
            return None
            
        except Exception as e:
            logger.error(f"User creation error: {e}")
            return None
    
    def assign_role(self, user_id: int, role_id: int, assigned_by: Optional[int] = None) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            assigned_by: UserID of assigner (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO dbo.UserRoles (UserID, RoleID, AssignedBy)
                VALUES (?, ?, ?)
            """
            
            self.db.execute_query(query, (user_id, role_id, assigned_by), fetch=False)
            logger.info(f"✅ Role {role_id} assigned to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Role assignment error: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID with roles and permissions.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict with user data if found, None otherwise
        """
        try:
            query = """
                SELECT 
                    u.UserID, u.Username, u.Email, u.FirstName, u.LastName,
                    u.IsActive, u.IsEmailVerified, u.LastLoginDate,
                    STRING_AGG(r.RoleName, ',') AS Roles,
                    (
                        SELECT STRING_AGG(p.PermissionName, ',')
                        FROM dbo.UserRoles ur2
                        INNER JOIN dbo.RolePermissions rp ON ur2.RoleID = rp.RoleID
                        INNER JOIN dbo.Permissions p ON rp.PermissionID = p.PermissionID
                        WHERE ur2.UserID = u.UserID
                    ) AS Permissions
                FROM dbo.Users u
                LEFT JOIN dbo.UserRoles ur ON u.UserID = ur.UserID
                LEFT JOIN dbo.Roles r ON ur.RoleID = r.RoleID
                WHERE u.UserID = ?
                GROUP BY 
                    u.UserID, u.Username, u.Email, u.FirstName, u.LastName,
                    u.IsActive, u.IsEmailVerified, u.LastLoginDate
            """
            
            results = self.db.execute_query(query, (user_id,))
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users with their roles.
        
        Returns:
            List of user dictionaries
        """
        try:
            query = """
                SELECT 
                    u.UserID, u.Username, u.Email, u.FirstName, u.LastName,
                    u.IsActive, u.IsEmailVerified, u.LastLoginDate, u.CreatedDate,
                    STRING_AGG(r.RoleName, ',') AS Roles
                FROM dbo.Users u
                LEFT JOIN dbo.UserRoles ur ON u.UserID = ur.UserID
                LEFT JOIN dbo.Roles r ON ur.RoleID = r.RoleID
                GROUP BY 
                    u.UserID, u.Username, u.Email, u.FirstName, u.LastName,
                    u.IsActive, u.IsEmailVerified, u.LastLoginDate, u.CreatedDate
                ORDER BY u.CreatedDate DESC
            """
            
            logger.info("Executing get_all_users query...")
            result = self.db.execute_query(query) or []
            logger.info(f"get_all_users returned {len(result)} users")
            if result:
                usernames = [u.get('Username') for u in result]
                logger.info(f"Usernames in result: {usernames}")
            return result
            
        except Exception as e:
            logger.error(f"Get all users error: {e}", exc_info=True)
            return []
    
    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        modified_by: Optional[int] = None
    ) -> bool:
        """
        Update user information.
        
        Args:
            user_id: User ID
            email: New email (optional)
            first_name: New first name (optional)
            last_name: New last name (optional)
            is_active: Active status (optional)
            modified_by: UserID of modifier (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updates = []
            params = []
            
            if email is not None:
                updates.append("Email = ?")
                params.append(email)
            if first_name is not None:
                updates.append("FirstName = ?")
                params.append(first_name)
            if last_name is not None:
                updates.append("LastName = ?")
                params.append(last_name)
            if is_active is not None:
                updates.append("IsActive = ?")
                params.append(is_active)
            if modified_by is not None:
                updates.append("ModifiedBy = ?")
                params.append(modified_by)
            
            updates.append("ModifiedDate = GETUTCDATE()")
            params.append(user_id)
            
            query = f"""
                UPDATE dbo.Users 
                SET {', '.join(updates)}
                WHERE UserID = ?
            """
            
            self.db.execute_query(query, tuple(params), fetch=False)
            logger.info(f"✅ User updated: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user (soft delete by setting IsActive = 0).
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = "UPDATE dbo.Users SET IsActive = 0 WHERE UserID = ?"
            self.db.execute_query(query, (user_id,), fetch=False)
            logger.info(f"✅ User deleted: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Delete user error: {e}")
            return False
    
    def get_all_roles(self) -> List[Dict[str, Any]]:
        """
        Get all available roles.
        
        Returns:
            List of role dictionaries
        """
        try:
            query = "SELECT RoleID, RoleName, Description FROM dbo.Roles WHERE IsActive = 1"
            return self.db.execute_query(query) or []
        except Exception as e:
            logger.error(f"Get roles error: {e}")
            return []
    
    def remove_user_role(self, user_id: int, role_id: int) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = "DELETE FROM dbo.UserRoles WHERE UserID = ? AND RoleID = ?"
            self.db.execute_query(query, (user_id, role_id), fetch=False)
            logger.info(f"✅ Role {role_id} removed from user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Remove role error: {e}")
            return False
    
    def has_permission(self, user_data: Dict[str, Any], permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_data: User data dictionary (from JWT token)
            permission: Permission name to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        permissions = user_data.get("permissions", [])
        return permission in permissions
    
    def reset_user_password(
        self, 
        user_id: int, 
        new_password: str,
        modified_by: Optional[int] = None
    ) -> bool:
        """
        Reset a user's password (admin function).
        
        Args:
            user_id: User ID to reset password for
            new_password: New plain text password
            modified_by: ID of user making the change
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Hash the new password
            password_hash = self.hash_password(new_password)
            
            # Update password in database
            query = """
                UPDATE dbo.Users 
                SET PasswordHash = ?, 
                    ModifiedDate = GETUTCDATE(),
                    ModifiedBy = ?,
                    FailedLoginAttempts = 0,
                    AccountLockedUntil = NULL
                WHERE UserID = ?
            """
            
            params = (password_hash, modified_by, user_id)
            
            cursor = self.db.execute_query(query, params)
            affected_rows = cursor.rowcount if cursor else 0
            
            if affected_rows > 0:
                logger.info(f"Password reset successful for user_id={user_id} by user_id={modified_by}")
                return True
            else:
                logger.warning(f"Password reset failed - user_id={user_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Password reset error for user_id={user_id}: {e}")
            return False
    
    def change_own_password(
        self, 
        user_id: int, 
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user's own password (requires current password verification).
        
        Args:
            user_id: User ID changing their password
            current_password: Current plain text password
            new_password: New plain text password
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First verify current password
            user = self.get_user_by_id(user_id)
            
            if not user:
                logger.warning(f"Password change failed - user_id={user_id} not found")
                return False
            
            if not self.verify_password(current_password, user["PasswordHash"]):
                logger.warning(f"Password change failed - invalid current password for user_id={user_id}")
                return False
            
            # Hash new password
            password_hash = self.hash_password(new_password)
            
            # Update password
            query = """
                UPDATE dbo.Users 
                SET PasswordHash = ?, 
                    ModifiedDate = GETUTCDATE(),
                    ModifiedBy = ?
                WHERE UserID = ?
            """
            
            params = (password_hash, user_id, user_id)
            
            cursor = self.db.execute_query(query, params)
            affected_rows = cursor.rowcount if cursor else 0
            
            if affected_rows > 0:
                logger.info(f"Password changed successfully for user_id={user_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Password change error for user_id={user_id}: {e}")
            return False
    
    def has_role(self, user_data: Dict[str, Any], role: str) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            user_data: User data dictionary (from JWT token)
            role: Role name to check
            
        Returns:
            bool: True if user has role, False otherwise
        """
        roles = user_data.get("roles", [])
        return role in roles


# Dependency for protected routes
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        request: FastAPI request object
        credentials: HTTP authorization credentials
        
    Returns:
        Dict with user data
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not hasattr(request.app.state, 'auth_manager') or request.app.state.auth_manager is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication system not initialized")
    auth_manager: AuthManager = request.app.state.auth_manager
    
    token = credentials.credentials
    user_data = auth_manager.verify_jwt_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data


# Dependency for admin-only routes
async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require admin role.
    
    Args:
        current_user: Current user data
        
    Returns:
        Dict with user data
        
    Raises:
        HTTPException: If user doesn't have admin role
    """
    roles = current_user.get("roles", [])
    if "Admin" not in roles and "SuperAdmin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


# Dependency for superadmin-only routes
async def require_superadmin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require SuperAdmin role.
    
    Args:
        current_user: Current user data
        
    Returns:
        Dict with user data
        
    Raises:
        HTTPException: If user doesn't have SuperAdmin role
    """
    roles = current_user.get("roles", [])
    if "SuperAdmin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SuperAdmin access required"
        )
    
    return current_user


def require_permission(permission: str):
    """
    Dependency factory to require a specific permission.
    
    Args:
        permission: Permission name required
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        auth_manager: AuthManager = request.app.state.auth_manager
        
        if not auth_manager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        
        return current_user
    
    return permission_checker
