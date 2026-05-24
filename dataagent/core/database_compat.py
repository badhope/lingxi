"""
数据库兼容性模块
提供向后兼容的接口，同时使用新的核心数据库系统
"""
from core.database import (
    init_database,
    get_settings,
    save_settings,
    get_conversation,
    save_conversation,
    delete_conversation,
    get_all_conversations,
    get_skill,
    save_skill,
    delete_skill,
    get_all_skills,
    get_knowledge_base,
    save_knowledge_base,
    delete_knowledge_base,
    get_all_knowledge_bases,
    get_mcp_server,
    save_mcp_server,
    delete_mcp_server,
    get_all_mcp_servers,
    get_database,
    save_database,
    delete_database,
    get_all_databases
)

# 向后兼容的全局变量接口
class GlobalStateCompat:
    """全局状态兼容类"""
    
    @property
    def current_settings(self):
        return get_settings()
    
    @property
    def knowledge_bases(self):
        return get_all_knowledge_bases()
    
    @property
    def skills(self):
        return get_all_skills()
    
    @property
    def mcp_servers(self):
        return get_all_mcp_servers()
    
    @property
    def conversations(self):
        return get_all_conversations()
    
    @property
    def databases(self):
        return get_all_databases()

global_compat = GlobalStateCompat()

# 导出兼容性变量
current_settings = global_compat.current_settings
knowledge_bases = global_compat.knowledge_bases
skills = global_compat.skills
mcp_servers = global_compat.mcp_servers
conversations = global_compat.conversations
databases = global_compat.databases

__all__ = [
    'init_database',
    'current_settings',
    'knowledge_bases',
    'skills',
    'mcp_servers',
    'conversations',
    'databases',
    'get_settings',
    'save_settings',
    'get_conversation',
    'save_conversation',
    'delete_conversation',
    'get_all_conversations',
    'get_skill',
    'save_skill',
    'delete_skill',
    'get_all_skills',
    'get_knowledge_base',
    'save_knowledge_base',
    'delete_knowledge_base',
    'get_all_knowledge_bases',
    'get_mcp_server',
    'save_mcp_server',
    'delete_mcp_server',
    'get_all_mcp_servers',
    'get_database',
    'save_database',
    'delete_database',
    'get_all_databases'
]
