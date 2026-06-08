"""
User auth, password hashing (PBKDF2), role/permission checks, session tokens.
"""
import json
import hashlib
import secrets
import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from core.config import config_manager
from core.logging import get_logger, security_logger
from core.database import db_manager

auth_logger = get_logger("auth")


class UserRole(str, Enum):
    """用户角色定义"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class Permission(str, Enum):
    """权限定义"""
    # 用户管理
    MANAGE_USERS = "manage_users"
    
    # 技能管理
    MANAGE_SKILLS = "manage_skills"
    
    # 知识库管理
    MANAGE_KNOWLEDGE_BASES = "manage_knowledge_bases"
    
    # 数据库管理
    MANAGE_DATABASES = "manage_databases"
    
    # 对话管理
    MANAGE_CONVERSATIONS = "manage_conversations"
    
    # MCP 管理
    MANAGE_MCP = "manage_mcp"
    
    # 财务分析
    USE_FINANCIAL_ANALYSIS = "use_financial_analysis"
    
    # 数据分析
    USE_DATA_ANALYSIS = "use_data_analysis"
    
    # Agent 使用
    USE_AGENT = "use_agent"
    
    # 文件操作
    UPLOAD_FILES = "upload_files"
    
    # 系统设置
    MANAGE_SETTINGS = "manage_settings"
    
    # 工作流管理
    MANAGE_WORKFLOWS = "manage_workflows"
    EXECUTE_WORKFLOWS = "execute_workflows"
    
    # LLMOps 管理
    MANAGE_LLMOPS = "manage_llmops"
    VIEW_LLMOPS = "view_llmops"


# 角色权限映射
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [p for p in Permission],
    UserRole.USER: [
        Permission.USE_AGENT,
        Permission.USE_DATA_ANALYSIS,
        Permission.USE_FINANCIAL_ANALYSIS,
        Permission.UPLOAD_FILES,
        Permission.MANAGE_CONVERSATIONS,
        Permission.EXECUTE_WORKFLOWS,
        Permission.VIEW_LLMOPS,
    ],
    UserRole.GUEST: [
        Permission.USE_AGENT,
    ],
}


@dataclass
class User:
    """用户模型"""
    id: str
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    is_active: bool = True
    is_verified: bool = False
    extra_metadata: Dict = field(default_factory=dict)
    
    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否具有指定权限"""
        if self.role == UserRole.ADMIN:
            return True
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name or self.username,
            "role": self.role.value,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(self.role, [])],
        }
    
    def to_safe_dict(self) -> Dict:
        """转换为安全的字典（不包含敏感信息）"""
        return {k: v for k, v in self.to_dict().items() if k != "password_hash"}


@dataclass
class UserSession:
    """用户会话模型"""
    id: str
    user_id: str
    token: str
    created_at: str
    expires_at: str
    last_accessed: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_revoked: bool = False
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        if self.is_revoked:
            return True
        now = datetime.datetime.now()
        expires = datetime.datetime.fromisoformat(self.expires_at)
        return now > expires
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "token": self.token[:10] + "..." if len(self.token) > 10 else self.token,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_accessed": self.last_accessed,
            "is_revoked": self.is_revoked,
        }


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """密码哈希处理"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{hashed.hex()}", salt


def verify_password(password: str, stored_hash: str) -> bool:
    """验证密码"""
    try:
        salt, hashed = stored_hash.split(':', 1)
        computed_hash, _ = hash_password(password, salt)
        stored_computed = computed_hash.split(':', 1)[1]
        return stored_computed == hashed
    except Exception:
        return False


def generate_token() -> str:
    """生成安全的访问令牌"""
    return secrets.token_urlsafe(32)


def generate_id() -> str:
    """生成唯一 ID"""
    return secrets.token_hex(16)


class AuthManager:
    """认证管理器"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.user_tokens: Dict[str, str] = {}
        self._load_data()
    
    def _get_data_path(self) -> Path:
        """获取数据存储路径"""
        return config_manager.paths.data_dir / "auth"
    
    def _get_users_path(self) -> Path:
        """获取用户数据文件路径"""
        return self._get_data_path() / "users.json"
    
    def _get_sessions_path(self) -> Path:
        """获取会话数据文件路径"""
        return self._get_data_path() / "sessions.json"
    
    def _load_data(self):
        """加载数据"""
        data_path = self._get_data_path()
        data_path.mkdir(parents=True, exist_ok=True)
        
        # 加载用户
        users_path = self._get_users_path()
        if users_path.exists():
            try:
                with open(users_path, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    for user_id, user_dict in users_data.items():
                        user_dict['role'] = UserRole(user_dict.get('role', 'user'))
                        self.users[user_id] = User(**user_dict)
            except Exception as e:
                auth_logger.error(f"加载用户数据失败: {e}")
        
        # 加载会话
        sessions_path = self._get_sessions_path()
        if sessions_path.exists():
            try:
                with open(sessions_path, 'r', encoding='utf-8') as f:
                    sessions_data = json.load(f)
                    for session_id, session_dict in sessions_data.items():
                        session = UserSession(**session_dict)
                        self.sessions[session_id] = session
                        self.user_tokens[session.token] = session_id
            except Exception as e:
                auth_logger.error(f"加载会话数据失败: {e}")
        
        # 如果没有用户，创建默认管理员
        if not self.users:
            self._create_default_admin()
    
    def _save_data(self):
        """保存数据"""
        # 保存用户
        users_data = {user_id: {
            **user.__dict__,
            'role': user.role.value
        } for user_id, user in self.users.items()}
        
        users_path = self._get_users_path()
        with open(users_path, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
        
        # 保存会话
        sessions_data = {session_id: session.__dict__ 
                        for session_id, session in self.sessions.items()}
        
        sessions_path = self._get_sessions_path()
        with open(sessions_path, 'w', encoding='utf-8') as f:
            json.dump(sessions_data, f, ensure_ascii=False, indent=2)
    
    def _create_default_admin(self):
        """创建默认管理员账户"""
        auth_logger.info("创建默认管理员账户")
        
        admin_id = generate_id()
        password_hash, _ = hash_password("admin123")
        
        admin = User(
            id=admin_id,
            username="admin",
            email="admin@dataagent.local",
            password_hash=password_hash,
            role=UserRole.ADMIN,
            display_name="系统管理员",
            is_active=True,
            is_verified=True
        )
        
        self.users[admin_id] = admin
        self._save_data()
        
        security_logger.warning("默认管理员账户已创建，请立即修改密码！")
    
    def create_user(self, username: str, email: str, password: str, 
                   role: UserRole = UserRole.USER,
                   display_name: Optional[str] = None) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        for user in self.users.values():
            if user.username == username:
                raise ValueError(f"用户名 '{username}' 已存在")
            if user.email == email:
                raise ValueError(f"邮箱 '{email}' 已被注册")
        
        user_id = generate_id()
        password_hash, _ = hash_password(password)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            display_name=display_name or username
        )
        
        self.users[user_id] = user
        self._save_data()
        
        security_logger.info(f"创建新用户: {username} (角色: {role.value})")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """根据 ID 获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    def list_users(self, include_inactive: bool = False) -> List[User]:
        """列出所有用户"""
        return [user for user in self.users.values() 
                if include_inactive or user.is_active]
    
    def authenticate(self, username_or_email: str, password: str,
                    ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None) -> Optional[UserSession]:
        """用户认证"""
        user = self.get_user_by_username(username_or_email)
        if not user:
            user = self.get_user_by_email(username_or_email)
        
        if not user:
            security_logger.warning(f"认证失败: 未找到用户 '{username_or_email}'")
            return None
        
        if not user.is_active:
            security_logger.warning(f"认证失败: 用户 '{username_or_email}' 已被禁用")
            return None
        
        if not verify_password(password, user.password_hash):
            security_logger.warning(f"认证失败: 用户 '{username_or_email}' 密码错误")
            return None
        
        # 认证成功，创建会话
        return self._create_session(user, ip_address, user_agent)
    
    def _create_session(self, user: User, ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None) -> UserSession:
        """创建用户会话"""
        session_id = generate_id()
        token = generate_token()
        now = datetime.datetime.now()
        expires = now + datetime.timedelta(days=7)  # 7天有效期
        
        session = UserSession(
            id=session_id,
            user_id=user.id,
            token=token,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            last_accessed=now.isoformat(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        self.user_tokens[token] = session_id
        self._save_data()
        
        security_logger.info(f"用户 '{user.username}' 登录成功")
        return session
    
    def verify_session(self, token: str) -> Optional[User]:
        """验证会话令牌"""
        session_id = self.user_tokens.get(token)
        if not session_id:
            return None
        
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        if session.is_expired():
            return None
        
        # 更新最后访问时间
        session.last_accessed = datetime.datetime.now().isoformat()
        self._save_data()
        
        return self.get_user(session.user_id)
    
    def revoke_session(self, token: str) -> bool:
        """撤销会话"""
        session_id = self.user_tokens.get(token)
        if session_id and session_id in self.sessions:
            self.sessions[session_id].is_revoked = True
            self._save_data()
            return True
        return False
    
    def revoke_all_user_sessions(self, user_id: str) -> int:
        """撤销用户的所有会话"""
        count = 0
        for session in self.sessions.values():
            if session.user_id == user_id and not session.is_revoked:
                session.is_revoked = True
                count += 1
        if count > 0:
            self._save_data()
        return count
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """更新用户信息"""
        user = self.get_user(user_id)
        if not user:
            return None
        
        allowed_fields = ['display_name', 'email', 'avatar_url', 'is_active', 'role']
        
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(user, key):
                if key == 'role' and isinstance(value, str):
                    value = UserRole(value)
                setattr(user, key, value)
        
        user.updated_at = datetime.datetime.now().isoformat()
        self._save_data()
        
        security_logger.info(f"更新用户信息: {user.username}")
        return user
    
    def change_password(self, user_id: str, current_password: str, 
                       new_password: str) -> bool:
        """修改密码"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        if not verify_password(current_password, user.password_hash):
            security_logger.warning(f"修改密码失败: 当前密码错误 - {user.username}")
            return False
        
        user.password_hash, _ = hash_password(new_password)
        user.updated_at = datetime.datetime.now().isoformat()
        
        # 撤销所有会话，强制重新登录
        self.revoke_all_user_sessions(user_id)
        self._save_data()
        
        security_logger.info(f"用户 '{user.username}' 修改密码成功")
        return True
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        # 撤销该用户的所有会话
        self.revoke_all_user_sessions(user_id)
        
        # 删除用户
        del self.users[user_id]
        self._save_data()
        
        security_logger.info(f"删除用户: {user.username}")
        return True


# 全局认证管理器实例
auth_manager = AuthManager()


def require_permission(permission: Permission):
    """权限装饰器 - 用于 API 端点"""
    def decorator(func):
        func._required_permission = permission
        return func
    return decorator


def get_auth_manager() -> AuthManager:
    """获取认证管理器实例"""
    return auth_manager


__all__ = [
    'User',
    'UserSession',
    'UserRole',
    'Permission',
    'AuthManager',
    'auth_manager',
    'get_auth_manager',
    'require_permission',
    'hash_password',
    'verify_password',
    'generate_token',
    'ROLE_PERMISSIONS',
]
