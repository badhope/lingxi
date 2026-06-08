"""routers - FastAPI 路由模块

所有 router 都通过包级导入对外暴露，未实现的 router 直接省略，
不在此处做 try/except，避免 import 时掩盖真实的接线错误。
"""

from . import api, auth, conversations, knowledge, settings, skills, workspace

__all__ = [
    "api",
    "auth",
    "conversations",
    "knowledge",
    "settings",
    "skills",
    "workspace",
]
