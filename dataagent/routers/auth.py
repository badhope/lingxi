"""
DataAgent - 认证路由
包含登录、注册、登出、用户信息管理、密码修改等端点
"""

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional

from core import auth_manager, UserRole, Permission
from core.logging import get_logger, security_logger

router = APIRouter()
logger = get_logger("auth_api")


def get_current_user(authorization: Optional[str] = Header(None)):
    """从请求头中获取当前用户（辅助函数）"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    user = auth_manager.verify_session(token)
    return user


@router.post("/api/auth/login")
async def login(request: Request):
    """用户登录"""
    data = await request.json()
    username_or_email = data.get("username", "")
    password = data.get("password", "")
    
    # 获取客户端信息
    client_host = request.client.host if request.client else "unknown"
    
    # 尝试认证
    session = auth_manager.authenticate(username_or_email, password, ip_address=client_host)
    
    if not session:
        security_logger.warning(f"登录失败: {username_or_email} (IP: {client_host})")
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user = auth_manager.get_user(session.user_id)
    
    security_logger.info(f"用户登录成功: {user.username} (IP: {client_host})")
    
    return JSONResponse({
        "success": True,
        "token": session.token,
        "user": user.to_safe_dict(),
        "message": "登录成功"
    })


@router.post("/api/auth/register")
async def register(request: Request):
    """用户注册"""
    data = await request.json()
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")
    display_name = data.get("display_name", username)
    
    # 基础验证
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少需要3个字符")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要6个字符")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="请提供有效的邮箱地址")
    
    try:
        user = auth_manager.create_user(username, email, password, UserRole.USER, display_name)
        security_logger.info(f"新用户注册: {username}")
        
        # 自动登录
        client_host = request.client.host if request.client else "unknown"
        session = auth_manager.authenticate(username, password, ip_address=client_host)
        
        return JSONResponse({
            "success": True,
            "token": session.token if session else None,
            "user": user.to_safe_dict(),
            "message": "注册成功"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/auth/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """用户登出"""
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse({"success": True, "message": "已登出"})
    
    token = authorization[7:]
    auth_manager.revoke_session(token)
    
    return JSONResponse({"success": True, "message": "登出成功"})


@router.get("/api/auth/me")
async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """获取当前用户信息"""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    return JSONResponse(user.to_safe_dict())


@router.put("/api/auth/me")
async def update_current_user(request: Request, authorization: Optional[str] = Header(None)):
    """更新当前用户信息"""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    data = await request.json()
    
    # 只允许更新特定字段
    allowed_fields = ["display_name", "email", "avatar_url"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    updated_user = auth_manager.update_user(user.id, **update_data)
    
    if not updated_user:
        raise HTTPException(status_code=400, detail="用户信息更新失败")
    
    security_logger.info(f"用户更新信息: {user.username}")
    return JSONResponse({"success": True, "user": updated_user.to_safe_dict()})


@router.post("/api/auth/change-password")
async def change_password(request: Request, authorization: Optional[str] = Header(None)):
    """修改密码"""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    
    data = await request.json()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少需要6个字符")
    
    success = auth_manager.change_password(user.id, current_password, new_password)
    
    if not success:
        raise HTTPException(status_code=400, detail="密码修改失败，请检查当前密码是否正确")
    
    security_logger.info(f"用户修改密码: {user.username}")
    return JSONResponse({"success": True, "message": "密码修改成功"})


# ==================== 管理员功能 ====================

@router.get("/api/admin/users")
async def list_all_users(authorization: Optional[str] = Header(None), include_inactive: bool = False):
    """列出所有用户（仅管理员）"""
    user = get_current_user(authorization)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足")
    
    users = auth_manager.list_users(include_inactive=include_inactive)
    
    return JSONResponse({
        "success": True,
        "users": [u.to_safe_dict() for u in users]
    })


@router.post("/api/admin/users")
async def create_user_as_admin(request: Request, authorization: Optional[str] = Header(None)):
    """管理员创建用户"""
    user = get_current_user(authorization)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足")
    
    data = await request.json()
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")
    role_str = data.get("role", "user")
    display_name = data.get("display_name", username)
    
    try:
        role = UserRole(role_str)
        new_user = auth_manager.create_user(username, email, password, role, display_name)
        security_logger.info(f"管理员 {user.username} 创建用户: {username}")
        return JSONResponse({"success": True, "user": new_user.to_safe_dict()})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/admin/users/{user_id}")
async def update_user_as_admin(user_id: str, request: Request, authorization: Optional[str] = Header(None)):
    """管理员更新用户信息"""
    current_user = get_current_user(authorization)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足")
    
    data = await request.json()
    allowed_fields = ["display_name", "email", "avatar_url", "is_active", "role"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    # 转换role字符串为枚举
    if "role" in update_data and isinstance(update_data["role"], str):
        update_data["role"] = UserRole(update_data["role"])
    
    updated_user = auth_manager.update_user(user_id, **update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    security_logger.info(f"管理员 {current_user.username} 更新用户: {updated_user.username}")
    return JSONResponse({"success": True, "user": updated_user.to_safe_dict()})


@router.delete("/api/admin/users/{user_id}")
async def delete_user_as_admin(user_id: str, authorization: Optional[str] = Header(None)):
    """管理员删除用户"""
    current_user = get_current_user(authorization)
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 不能删除自己
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    
    success = auth_manager.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    security_logger.info(f"管理员 {current_user.username} 删除用户: {user_id}")
    return JSONResponse({"success": True, "message": "用户已删除"})


@router.get("/api/auth/roles")
async def get_roles():
    """获取所有可用角色"""
    return JSONResponse({
        "success": True,
        "roles": [
            {"id": role.value, "name": role.value.capitalize()}
            for role in UserRole
        ]
    })


@router.get("/api/auth/permissions")
async def get_permissions():
    """获取所有权限定义"""
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
