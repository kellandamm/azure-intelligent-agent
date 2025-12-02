"""
Authentication and Admin routes for Agent Framework.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, Field

from utils.auth import AuthManager, get_current_user, require_admin, require_permission

# Create routers
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/api/admin", tags=["Administration"])


# ========================================
# Pydantic Models
# ========================================


class LoginRequest(BaseModel):
    """Login request model."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str = "bearer"
    user: dict


class RegisterRequest(BaseModel):
    """User registration request model."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""

    user_id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    roles: List[str]


class CreateUserRequest(BaseModel):
    """Admin create user request."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_ids: List[int] = []


class UpdateUserRequest(BaseModel):
    """Admin update user request."""

    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None


class AssignRoleRequest(BaseModel):
    """Assign role to user request."""

    user_id: int
    role_id: int


class ResetPasswordRequest(BaseModel):
    """Admin reset user password request."""

    new_password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    """User change own password request."""

    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


# ========================================
# Authentication Routes
# ========================================


@auth_router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate user and return JWT token.
    Sets token as HTTP-only cookie for server-side authentication.
    """
    from fastapi.responses import JSONResponse

    auth_manager: AuthManager = request.app.state.auth_manager

    # Authenticate user
    user = auth_manager.authenticate_user(login_data.username, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    token = auth_manager.create_jwt_token(user)

    # Prepare user data (exclude sensitive info)
    user_data = {
        "user_id": user["UserID"],
        "username": user["Username"],
        "email": user["Email"],
        "first_name": user.get("FirstName"),
        "last_name": user.get("LastName"),
        "roles": user.get("Roles", "").split(",") if user.get("Roles") else [],
    }

    # Create response with token in cookie for server-side auth
    response_data = LoginResponse(access_token=token, user=user_data)

    response = JSONResponse(content=response_data.model_dump())

    # Set HTTP-only cookie for server-side authentication checks
    # This prevents the guest window vulnerability
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=True,  # Only sent over HTTPS
        samesite="lax",  # CSRF protection
        max_age=86400,  # 24 hours (matches JWT expiry)
    )

    return response


@auth_router.post("/register", response_model=dict)
async def register(request: Request, register_data: RegisterRequest):
    """
    Register a new user (public registration - assigns User role by default).
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    # Create user
    user_id = auth_manager.create_user(
        username=register_data.username,
        email=register_data.email,
        password=register_data.password,
        first_name=register_data.first_name,
        last_name=register_data.last_name,
    )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    # Assign default "User" role (RoleID = 4)
    auth_manager.assign_role(user_id, 4)

    return {
        "message": "User registered successfully",
        "user_id": user_id,
        "username": register_data.username,
    }


@auth_router.get("/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "roles": current_user.get("roles", []),
        "permissions": current_user.get("permissions", []),
    }


@auth_router.post("/logout")
async def logout():
    """
    Logout endpoint - clears authentication cookie.
    """
    from fastapi.responses import JSONResponse

    response = JSONResponse(content={"message": "Logged out successfully"})
    # Clear the authentication cookie
    response.delete_cookie(key="auth_token")
    return response


@auth_router.post("/change-password")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Change current user's password (requires current password).
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    success = auth_manager.change_own_password(
        user_id=current_user["user_id"],
        current_password=password_data.current_password,
        new_password=password_data.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password. Please verify your current password.",
        )

    return {"message": "Password changed successfully"}


# ========================================
# Admin Routes
# ========================================


@admin_router.get("/users", dependencies=[Depends(require_admin)])
async def get_all_users(request: Request):
    """
    Get all users (admin only).
    """
    from utils.logging_config import logger

    auth_manager: AuthManager = request.app.state.auth_manager
    users = auth_manager.get_all_users()

    logger.info(f"get_all_users called - found {len(users)} users in database")

    # Format response
    formatted_users = []
    for user in users:
        formatted_users.append(
            {
                "user_id": user["UserID"],
                "username": user["Username"],
                "email": user["Email"],
                "first_name": user.get("FirstName"),
                "last_name": user.get("LastName"),
                "is_active": user["IsActive"],
                "last_login": user.get("LastLoginDate").isoformat()
                if user.get("LastLoginDate")
                else None,
                "created_date": user.get("CreatedDate").isoformat()
                if user.get("CreatedDate")
                else None,
                "roles": user.get("Roles", "").split(",") if user.get("Roles") else [],
            }
        )

    logger.info(f"Returning {len(formatted_users)} formatted users")

    return {"users": formatted_users}


@admin_router.get("/users/{user_id}", dependencies=[Depends(require_admin)])
async def get_user(request: Request, user_id: int):
    """
    Get user by ID (admin only).
    """
    auth_manager: AuthManager = request.app.state.auth_manager
    user = auth_manager.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {
        "user_id": user["UserID"],
        "username": user["Username"],
        "email": user["Email"],
        "first_name": user.get("FirstName"),
        "last_name": user.get("LastName"),
        "is_active": user["IsActive"],
        "is_email_verified": user.get("IsEmailVerified"),
        "last_login": user.get("LastLoginDate").isoformat()
        if user.get("LastLoginDate")
        else None,
        "roles": user.get("Roles", "").split(",") if user.get("Roles") else [],
        "permissions": user.get("Permissions", "").split(",")
        if user.get("Permissions")
        else [],
    }


@admin_router.post("/users", dependencies=[Depends(require_admin)])
async def create_user(
    request: Request,
    user_data: CreateUserRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Create a new user (admin only).
    """
    from utils.logging_config import logger

    auth_manager: AuthManager = request.app.state.auth_manager

    logger.info(f"Creating user: {user_data.username} (email: {user_data.email})")

    # Create user
    user_id = auth_manager.create_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        created_by=current_user["user_id"],
    )

    if not user_id:
        logger.warning(
            f"Failed to create user {user_data.username} - username or email already exists"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )

    logger.info(f"User created successfully with ID: {user_id}")

    # Assign roles
    for role_id in user_data.role_ids:
        logger.info(f"Assigning role {role_id} to user {user_id}")
        auth_manager.assign_role(user_id, role_id, current_user["user_id"])

    logger.info(f"User creation complete: {user_data.username} (ID: {user_id})")

    return {
        "message": "User created successfully",
        "user_id": user_id,
        "username": user_data.username,
    }


@admin_router.put("/users/{user_id}", dependencies=[Depends(require_admin)])
async def update_user(
    request: Request,
    user_id: int,
    user_data: UpdateUserRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Update user information (admin only).
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    success = auth_manager.update_user(
        user_id=user_id,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active,
        modified_by=current_user["user_id"],
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update user"
        )

    return {"message": "User updated successfully"}


@admin_router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(request: Request, user_id: int):
    """
    Delete user (soft delete) (admin only).
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    success = auth_manager.delete_user(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete user"
        )

    return {"message": "User deleted successfully"}


@admin_router.get("/roles", dependencies=[Depends(require_admin)])
async def get_all_roles(request: Request):
    """
    Get all available roles (admin only).
    """
    auth_manager: AuthManager = request.app.state.auth_manager
    roles = auth_manager.get_all_roles()

    return {"roles": roles}


@admin_router.post("/users/{user_id}/roles", dependencies=[Depends(require_admin)])
async def assign_role_to_user(
    request: Request,
    user_id: int,
    role_data: dict,
    current_user: dict = Depends(require_admin),
):
    """
    Assign a role to a user (admin only).
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    role_id = role_data.get("role_id")
    if not role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="role_id is required"
        )

    success = auth_manager.assign_role(user_id, role_id, current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign role"
        )

    return {"message": "Role assigned successfully"}


@admin_router.delete(
    "/users/{user_id}/roles/{role_id}", dependencies=[Depends(require_admin)]
)
async def remove_role_from_user(request: Request, user_id: int, role_id: int):
    """
    Remove a role from a user (admin only).
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    success = auth_manager.remove_user_role(user_id, role_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to remove role"
        )

    return {"message": "Role removed successfully"}


@admin_router.post(
    "/users/{user_id}/reset-password", dependencies=[Depends(require_admin)]
)
async def reset_user_password(
    request: Request,
    user_id: int,
    password_data: ResetPasswordRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Reset a user's password (admin only).

    This allows admins to set a new password for any user without
    requiring the current password. The user's failed login attempts
    will be reset and account will be unlocked if locked.
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    # Check if target user exists
    target_user = auth_manager.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Reset password
    success = auth_manager.reset_user_password(
        user_id=user_id,
        new_password=password_data.new_password,
        modified_by=current_user["user_id"],
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to reset password"
        )

    return {
        "message": f"Password reset successfully for user: {target_user['Username']}",
        "user_id": user_id,
        "username": target_user["Username"],
    }


@admin_router.post(
    "/users/{user_id}/change-password", dependencies=[Depends(require_admin)]
)
async def change_user_password(
    request: Request,
    user_id: int,
    password_data: ResetPasswordRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Change a user's password (admin only).

    This endpoint allows admins to change any user's password without
    requiring the current password. This is useful for password reset
    scenarios in the admin portal.
    """
    auth_manager: AuthManager = request.app.state.auth_manager

    # Check if target user exists
    target_user = auth_manager.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Change password using the same reset method
    success = auth_manager.reset_user_password(
        user_id=user_id,
        new_password=password_data.new_password,
        modified_by=current_user["user_id"],
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to change password"
        )

    return {
        "message": f"Password changed successfully for user: {target_user['Username']}",
        "user_id": user_id,
        "username": target_user["Username"],
    }
