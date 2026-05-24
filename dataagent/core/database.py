"""
DataAgent - Database Persistence Layer
数据库持久化层，支持多种数据库后端
"""
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar, Generic

from pydantic import BaseModel

from .config import config_manager
from .logging import db_logger

T = TypeVar('T', bound=BaseModel)


class DatabaseBackend(Generic[T]):
    """数据库后端抽象基类"""
    
    def __init__(self, collection_name: str, model_class: Type[T]):
        self.collection_name = collection_name
        self.model_class = model_class
        self._lock = threading.RLock()
    
    async def get(self, key: str) -> Optional[T]:
        """获取单个文档"""
        raise NotImplementedError
    
    async def get_all(self) -> Dict[str, T]:
        """获取所有文档"""
        raise NotImplementedError
    
    async def set(self, key: str, value: T):
        """设置文档"""
        raise NotImplementedError
    
    async def delete(self, key: str):
        """删除文档"""
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        """检查文档是否存在"""
        raise NotImplementedError
    
    async def clear(self):
        """清空所有文档"""
        raise NotImplementedError
    
    async def count(self) -> int:
        """获取文档数量"""
        raise NotImplementedError


class JSONFileBackend(DatabaseBackend[T]):
    """基于JSON文件的数据库后端"""
    
    def __init__(self, collection_name: str, model_class: Type[T], file_path: Path):
        super().__init__(collection_name, model_class)
        self.file_path = file_path
        self._data: Dict[str, T] = {}
        self._load()
    
    def _load(self):
        """从文件加载数据"""
        if not self.file_path.exists():
            db_logger.debug(f"Database file not found: {self.file_path}")
            self._data = {}
            return
        
        try:
            with self._lock:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # 解析数据
                self._data = {}
                for key, value in raw_data.items():
                    try:
                        self._data[key] = self.model_class(**value)
                    except Exception as e:
                        db_logger.warning(f"Failed to parse {self.collection_name} item {key}: {e}")
                
                db_logger.info(f"Loaded {len(self._data)} items from {self.collection_name}")
        except Exception as e:
            db_logger.error(f"Error loading {self.collection_name}: {e}")
            self._data = {}
    
    def _save(self):
        """保存到文件"""
        try:
            with self._lock:
                # 确保目录存在
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 统一使用 Pydantic v2 的 model_dump 序列化数据
                serialized = {}
                for key, value in self._data.items():
                    if isinstance(value, BaseModel):
                        serialized[key] = value.model_dump()
                    else:
                        serialized[key] = value
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(serialized, f, ensure_ascii=False, indent=2)
            
            db_logger.debug(f"Saved {len(self._data)} items to {self.collection_name}")
        except Exception as e:
            db_logger.error(f"Error saving {self.collection_name}: {e}")
    
    async def get(self, key: str) -> Optional[T]:
        """获取单个文档"""
        with self._lock:
            return self._data.get(key)
    
    async def get_all(self) -> Dict[str, T]:
        """获取所有文档"""
        with self._lock:
            return dict(self._data)
    
    async def set(self, key: str, value: T):
        """设置文档"""
        with self._lock:
            self._data[key] = value
        self._save()
    
    async def delete(self, key: str):
        """删除文档"""
        with self._lock:
            if key in self._data:
                del self._data[key]
        self._save()
    
    async def exists(self, key: str) -> bool:
        """检查文档是否存在"""
        with self._lock:
            return key in self._data
    
    async def clear(self):
        """清空所有文档"""
        with self._lock:
            self._data = {}
        self._save()
    
    async def count(self) -> int:
        """获取文档数量"""
        with self._lock:
            return len(self._data)


class MemoryBackend(DatabaseBackend[T]):
    """基于内存的数据库后端（临时存储）"""
    
    def __init__(self, collection_name: str, model_class: Type[T]):
        super().__init__(collection_name, model_class)
        self._data: Dict[str, T] = {}
    
    async def get(self, key: str) -> Optional[T]:
        """获取单个文档"""
        with self._lock:
            return self._data.get(key)
    
    async def get_all(self) -> Dict[str, T]:
        """获取所有文档"""
        with self._lock:
            return dict(self._data)
    
    async def set(self, key: str, value: T):
        """设置文档"""
        with self._lock:
            self._data[key] = value
    
    async def delete(self, key: str):
        """删除文档"""
        with self._lock:
            if key in self._data:
                del self._data[key]
    
    async def exists(self, key: str) -> bool:
        """检查文档是否存在"""
        with self._lock:
            return key in self._data
    
    async def clear(self):
        """清空所有文档"""
        with self._lock:
            self._data = {}
    
    async def count(self) -> int:
        """获取文档数量"""
        with self._lock:
            return len(self._data)


class DatabaseManager:
    """数据库管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._backends: Dict[str, DatabaseBackend] = {}
            self._initialized = True
    
    def register_backend(self, name: str, backend: DatabaseBackend):
        """注册数据库后端"""
        self._backends[name] = backend
    
    def get_backend(self, name: str) -> DatabaseBackend:
        """获取数据库后端"""
        if name not in self._backends:
            raise ValueError(f"Unknown database backend: {name}")
        return self._backends[name]
    
    async def get(self, collection: str, key: str) -> Optional[Any]:
        """获取文档"""
        backend = self.get_backend(collection)
        return await backend.get(key)
    
    async def get_all(self, collection: str) -> Dict[str, Any]:
        """获取所有文档"""
        backend = self.get_backend(collection)
        return await backend.get_all()
    
    async def set(self, collection: str, key: str, value: Any):
        """设置文档"""
        backend = self.get_backend(collection)
        await backend.set(key, value)
    
    async def delete(self, collection: str, key: str):
        """删除文档"""
        backend = self.get_backend(collection)
        await backend.delete(key)
    
    async def exists(self, collection: str, key: str) -> bool:
        """检查文档是否存在"""
        backend = self.get_backend(collection)
        return await backend.exists(key)
    
    async def clear(self, collection: str):
        """清空集合"""
        backend = self.get_backend(collection)
        await backend.clear()
    
    async def count(self, collection: str) -> int:
        """获取文档数量"""
        backend = self.get_backend(collection)
        return await backend.count()


# 全局数据库管理器实例
db_manager = DatabaseManager()


# ============================================================
# 便捷函数
# ============================================================

def init_database():
    """初始化数据库"""
    db_logger.info("Initializing database backends...")
    
    from models import Settings, KnowledgeBase, Document, Skill, MCPServer, Database
    
    paths = config_manager.paths
    
    # 注册各种集合的后端
    db_manager.register_backend(
        "settings",
        JSONFileBackend("settings", Settings, paths.config_dir / "web_config.json")
    )
    
    db_manager.register_backend(
        "knowledge_bases",
        JSONFileBackend("knowledge_bases", KnowledgeBase, paths.knowledge_dir / "index.json")
    )
    
    db_manager.register_backend(
        "documents",
        JSONFileBackend("documents", Document, paths.data_dir / "documents.json")
    )
    
    db_manager.register_backend(
        "skills",
        JSONFileBackend("skills", Skill, paths.skills_dir / "index.json")
    )
    
    db_manager.register_backend(
        "mcp_servers",
        JSONFileBackend("mcp_servers", MCPServer, paths.config_dir / "mcp.json")
    )
    
    db_manager.register_backend(
        "databases",
        JSONFileBackend("databases", Database, paths.data_dir / "databases.json")
    )
    
    db_manager.register_backend(
        "conversations",
        JSONFileBackend("conversations", dict, paths.data_dir / "conversations.json")
    )
    
    db_logger.info("Database backends initialized successfully")


async def get_settings() -> Settings:
    """获取设置"""
    result = await db_manager.get("settings", "default")
    if result is None:
        from models import Settings
        return Settings()
    return result


async def save_settings(settings: Settings):
    """保存设置"""
    await db_manager.set("settings", "default", settings)


async def get_conversation(conversation_id: str) -> Optional[dict]:
    """获取会话"""
    return await db_manager.get("conversations", conversation_id)


async def save_conversation(conversation_id: str, conversation: dict):
    """保存会话"""
    await db_manager.set("conversations", conversation_id, conversation)


async def delete_conversation(conversation_id: str):
    """删除会话"""
    await db_manager.delete("conversations", conversation_id)


async def get_all_conversations() -> Dict[str, dict]:
    """获取所有会话"""
    return await db_manager.get_all("conversations")


async def get_skill(skill_id: str) -> Optional[Skill]:
    """获取技能"""
    return await db_manager.get("skills", skill_id)


async def save_skill(skill_id: str, skill: Skill):
    """保存技能"""
    await db_manager.set("skills", skill_id, skill)


async def delete_skill(skill_id: str):
    """删除技能"""
    await db_manager.delete("skills", skill_id)


async def get_all_skills() -> Dict[str, Skill]:
    """获取所有技能"""
    return await db_manager.get_all("skills")


async def get_knowledge_base(kb_id: str) -> Optional[KnowledgeBase]:
    """获取知识库"""
    return await db_manager.get("knowledge_bases", kb_id)


async def save_knowledge_base(kb_id: str, kb: KnowledgeBase):
    """保存知识库"""
    await db_manager.set("knowledge_bases", kb_id, kb)


async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    await db_manager.delete("knowledge_bases", kb_id)


async def get_all_knowledge_bases() -> Dict[str, KnowledgeBase]:
    """获取所有知识库"""
    return await db_manager.get_all("knowledge_bases")


async def get_mcp_server(server_id: str) -> Optional[MCPServer]:
    """获取MCP服务器"""
    return await db_manager.get("mcp_servers", server_id)


async def save_mcp_server(server_id: str, server: MCPServer):
    """保存MCP服务器"""
    await db_manager.set("mcp_servers", server_id, server)


async def delete_mcp_server(server_id: str):
    """删除MCP服务器"""
    await db_manager.delete("mcp_servers", server_id)


async def get_all_mcp_servers() -> Dict[str, MCPServer]:
    """获取所有MCP服务器"""
    return await db_manager.get_all("mcp_servers")


async def get_database(db_id: str) -> Optional[Database]:
    """获取数据库连接"""
    return await db_manager.get("databases", db_id)


async def save_database(db_id: str, db: Database):
    """保存数据库连接"""
    await db_manager.set("databases", db_id, db)


async def delete_database(db_id: str):
    """删除数据库连接"""
    await db_manager.delete("databases", db_id)


async def get_all_databases() -> Dict[str, Database]:
    """获取所有数据库连接"""
    return await db_manager.get_all("databases")
