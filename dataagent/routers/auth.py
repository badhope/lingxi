"""Auth routes: register, login, logout, me, password change."""
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional

from core import auth_manager, UserRole, Permission
from core.logging import get_logger, security_logger

router = APIRouter()
logger = get_logger("auth_api")


def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract current user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    user = auth_manager.verify_session(token)
    return user


@router.post("/api/auth/login")
async def login(request: Request):
    """User login."""
    data = await request.json()
    username_or_email = data.get("username", "")
    password = data.get("password", "")

    client_host = request.client.host if request.client else "unknown"

    session = auth_manager.authenticate(username_or_email, password, ip_address=client_host)

    if not session:
        security_logger.warning(f"Login failed: {username_or_email} (IP: {client_host})")
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = auth_manager.get_user(session.user_id)

    security_logger.info(f"User logged in: {user.username} (IP: {client_host})")

    return JSONResponse({
        "success": True,
        "token": session.token,
        "user": user.to_safe_dict(),
        "message": "Login successful"
    })


@router.post("/api/auth/register")
async def register(request: Request):
    """User registration."""
    data = await request.json()
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")
    display_name = data.get("display_name", username)

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email address is required")

    try:
        user = auth_manager.create_user(username, email, password, UserRole.USER, display_name)
        security_logger.info(f"New user registered: {username}")

        client_host = request.client.host if request.client else "unknown"
        session = auth_manager.authenticate(username, password, ip_address=client_host)

        return JSONResponse({
            "success": True,
            "token": session.token if session else None,
            "user": user.to_safe_dict(),
            "message": "Registration successful"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """User logout."""
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"success": True, "message": "Already logged out"})

    token = authorization[7:]
    auth_manager.revoke_session(token)

    return JSONResponse({"success": True, "message": "Logout successful"})


@router.get("/api/auth/me")
async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """Get current user info."""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return JSONResponse(user.to_safe_dict())


@router.put("/api/auth/me")
async def update_current_user(request: Request, authorization: Optional[str] = Header(None)):
    """Update current user info."""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()

    allowed_fields = ["display_name", "email", "avatar_url"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    updated_user = auth_manager.update_user(user.id, **update_data)

    if not updated_user:
        raise HTTPException(status_code=400, detail="Failed to update user info")

    security_logger.info(f"User updated info: {user.username}")
    return JSONResponse({"success": True, "user": updated_user.to_safe_dict()})


@router.post("/api/auth/change-password")
async def change_password(request: Request, authorization: Optional[str] = Header(None)):
    """Change password."""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    success = auth_manager.change_password(user.id, current_password, new_password)

    if not success:
        raise HTTPException(status_code=400, detail="Password change failed — check current password")

    security_logger.info(f"User changed password: {user.username}")
    return JSONResponse({"success": True, "message": "Password changed successfully"})


# ==================== Admin ====================

@router.get("/api/admin/users")
async def list_all_users(authorization: Optional[str] = Header(None), include_inactive: bool = False):
    """List all users (admin only)."""
    user = get_current_user(authorization)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    users = auth_manager.list_users(include_inactive=include_inactive)

    return JSONResponse({
        "success": True,
        "users": [u.to_safe_dict() for u in users]
    })


@router.post("/api/admin/users")
async def create_user_as_admin(request: Request, authorization: Optional[str] = Header(None)):
    """Admin create user."""
    user = get_current_user(authorization)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    data = await request.json()
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")
    role_str = data.get("role", "user")
    display_name = data.get("display_name", username)

    try:
        role = UserRole(role_str)
        new_user = auth_manager.create_user(username, email, password, role, display_name)
        security_logger.info(f"Admin {user.username} created user: {username}")
        return JSONResponse({"success": True, "user": new_user.to_safe_dict()})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/admin/users/{user_id}")
async def update_user_as_admin(user_id: str, request: Request, authorization: Optional[str] = Header(None)):
    """Admin update user."""
    current_user = get_current_user(authorization)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    data = await request.json()
    allowed_fields = ["display_name", "email", "avatar_url", "is_active", "role"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if "role" in update_data and isinstance(update_data["role"], str):
        update_data["role"] = UserRole(update_data["role"])

    updated_user = auth_manager.update_user(user_id, **update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    security_logger.info(f"Admin {current_user.username} updated user: {updated_user.username}")
    return JSONResponse({"success": True, "user": updated_user.to_safe_dict()})


@router.delete("/api/admin/users/{user_id}")
async def delete_user_as_admin(user_id: str, authorization: Optional[str] = Header(None)):
    """Admin delete user."""
    current_user = get_current_user(authorization)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    success = auth_manager.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    security_logger.info(f"Admin {current_user.username} deleted user: {user_id}")
    return JSONResponse({"success": True, "message": "User deleted"})


@router.get("/api/auth/roles")
async def get_roles():
    """List available roles."""
    return JSONResponse({
        "success": True,
        "roles": [
            {"id": role.value, "name": role.value.capitalize()}
            for role in UserRole
        ]
    })


@router.get("/api/auth/permissions")
async def get_permissions():
    """List all permissions."""
    return JSONResponse({
        "success": True,
        "permissions": [
            {"id": perm.value, "name": perm.value.replace("_", " ").title()}
            for perm in Permission
        ],
        "role_permissions": {
            role.value: [p.value for p in perms]
            for role, perms in auth_manager.ROLE_PERMISSIONS.items()
        } if hasattr(auth_manager, 'ROLE_PERMISSIONS') else {}
    })
