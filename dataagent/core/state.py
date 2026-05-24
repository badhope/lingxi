"""
DataAgent - Global State Management
全局状态管理模块，提供线程安全的状态管理
"""
import json
import datetime
import threading
from pathlib import Path
from typing import Dict, Optional, Any, Type, TypeVar

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from .config import config_manager
from .logging import db_logger

T = TypeVar('T')


# 定义核心模型类
class Settings(BaseModel):
    """设置模型"""
    theme: str = "light"
    language: str = "zh-CN"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    api_keys: Dict[str, str] = Field(default_factory=dict)


class Skill(BaseModel):
    """技能模型"""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "DataAgent Team"
    category: str = "general"
    type: str = "built_in"
    icon: str = "📦"
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    prompts: Dict[str, str] = Field(default_factory=dict)


class StateStore:
    """状态存储抽象类"""
    
    def __init__(self, name: str, model_class: Type[BaseModel] = None):
        self.name = name
        self.model_class = model_class
        self._lock = threading.RLock()
    
    def load(self) -> Dict[str, Any]:
        """加载状态"""
        raise NotImplementedError
    
    def save(self, data: Dict[str, Any]):
        """保存状态"""
        raise NotImplementedError


class FileStateStore(StateStore):
    """基于文件的状态存储"""
    
    def __init__(self, name: str, file_path: Path, model_class: Type[BaseModel] = None):
        super().__init__(name, model_class)
        self.file_path = file_path
    
    def load(self) -> Dict[str, Any]:
        """从文件加载状态"""
        if not self.file_path.exists():
            db_logger.debug(f"State file not found: {self.file_path}")
            return {}
        
        try:
            with self._lock:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 如果有模型类，尝试解析
                if self.model_class:
                    return {k: self.model_class(**v) for k, v in data.items()}
                
                return data
        except Exception as e:
            db_logger.error(f"Error loading state from {self.file_path}: {e}")
            return {}
    
    def save(self, data: Dict[str, Any]):
        """保存状态到文件"""
        try:
            with self._lock:
                # 确保目录存在
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 转换为可序列化的格式
                serialized = {}
                for k, v in data.items():
                    if hasattr(v, 'model_dump'):
                        serialized[k] = v.model_dump()
                    elif isinstance(v, BaseModel):
                        serialized[k] = v.dict()
                    else:
                        serialized[k] = v
                
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(serialized, f, ensure_ascii=False, indent=2)
            
            db_logger.debug(f"State saved to {self.file_path}")
        except Exception as e:
            db_logger.error(f"Error saving state to {self.file_path}: {e}")


class MemoryStateStore(StateStore):
    """基于内存的状态存储（用于临时数据）"""
    
    def __init__(self, name: str, model_class: Type[BaseModel] = None):
        super().__init__(name, model_class)
        self._data: Dict[str, Any] = {}
    
    def load(self) -> Dict[str, Any]:
        return self._data.copy()
    
    def save(self, data: Dict[str, Any]):
        self._data = data.copy()


class StateManager:
    """状态管理器 - 提供线程安全的全局状态管理"""
    
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
            self._stores: Dict[str, StateStore] = {}
            self._states: Dict[str, Dict[str, Any]] = {}
            self._initialized = True
    
    def register_store(self, name: str, store: StateStore):
        """注册状态存储"""
        self._stores[name] = store
        self._states[name] = store.load()
    
    def get_state(self, name: str) -> Dict[str, Any]:
        """获取状态字典"""
        return self._states.get(name, {})
    
    def get_item(self, name: str, key: str, default: Any = None) -> Any:
        """获取状态中的单个项目"""
        with self._lock:
            state = self._states.get(name, {})
            return state.get(key, default)
    
    def set_item(self, name: str, key: str, value: Any):
        """设置状态中的单个项目"""
        with self._lock:
            if name not in self._states:
                self._states[name] = {}
            self._states[name][key] = value
            
            # 保存到持久化存储
            if name in self._stores:
                self._stores[name].save(self._states[name])
    
    def delete_item(self, name: str, key: str):
        """删除状态中的项目"""
        with self._lock:
            if name in self._states and key in self._states[name]:
                del self._states[name][key]
                
                # 保存到持久化存储
                if name in self._stores:
                    self._stores[name].save(self._states[name])
    
    def save_all(self):
        """保存所有状态"""
        with self._lock:
            for name, store in self._stores.items():
                if name in self._states:
                    store.save(self._states[name])
    
    def reload(self, name: str = None):
        """重新加载状态"""
        with self._lock:
            if name:
                if name in self._stores:
                    self._states[name] = self._stores[name].load()
            else:
                for name, store in self._stores.items():
                    self._states[name] = store.load()


# 全局状态管理器实例
state_manager = StateManager()


# ============================================================
# 具体状态管理类
# ============================================================

class SettingsManager:
    """设置管理器"""
    
    def __init__(self):
        self._settings = None
    
    @property
    def settings(self):
        if self._settings is None:
            self.load()
        return self._settings
    
    @settings.setter
    def settings(self, value):
        self._settings = value
        self.save()
    
    def load(self):
        """加载设置"""
        paths = config_manager.paths
        settings_file = paths.config_dir / "web_config.json"
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._settings = Settings(**data)
                    db_logger.info("Settings loaded successfully")
            except Exception as e:
                db_logger.error(f"Error loading settings: {e}")
                self._settings = Settings()
        else:
            self._settings = Settings()
    
    def save(self):
        """保存设置"""
        if self._settings:
            paths = config_manager.paths
            settings_file = paths.config_dir / "web_config.json"
            
            try:
                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(self._settings.model_dump(), f, ensure_ascii=False, indent=2)
                db_logger.info("Settings saved successfully")
            except Exception as e:
                db_logger.error(f"Error saving settings: {e}")


class ConversationManager:
    """会话管理器"""
    
    def __init__(self):
        self._conversations: Dict[str, dict] = {}
    
    @property
    def conversations(self):
        return self._conversations
    
    def load(self):
        """加载会话"""
        paths = config_manager.paths
        conv_file = paths.data_dir / "conversations.json"
        
        if conv_file.exists():
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    self._conversations = json.load(f)
                db_logger.info(f"Loaded {len(self._conversations)} conversations")
            except Exception as e:
                db_logger.error(f"Error loading conversations: {e}")
                self._conversations = {}
        else:
            self._conversations = {}
    
    def save(self):
        """保存会话"""
        paths = config_manager.paths
        conv_file = paths.data_dir / "conversations.json"
        
        try:
            conv_file.parent.mkdir(parents=True, exist_ok=True)
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(self._conversations, f, ensure_ascii=False, indent=2)
            db_logger.info(f"Saved {len(self._conversations)} conversations")
        except Exception as e:
            db_logger.error(f"Error saving conversations: {e}")
    
    def create_conversation(self, conversation_id: str, initial_data: dict = None):
        """创建新会话"""
        self._conversations[conversation_id] = initial_data or {
            'id': conversation_id,
            'messages': [],
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat()
        }
        self.save()
    
    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """获取会话"""
        return self._conversations.get(conversation_id)
    
    def update_conversation(self, conversation_id: str, updates: dict):
        """更新会话"""
        if conversation_id in self._conversations:
            self._conversations[conversation_id].update(updates)
            self._conversations[conversation_id]['updated_at'] = datetime.datetime.now().isoformat()
            self.save()
    
    def delete_conversation(self, conversation_id: str):
        """删除会话"""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            self.save()


class SkillManager:
    """技能管理器"""
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
    
    @property
    def skills(self):
        return self._skills
    
    def load(self):
        """加载技能"""
        paths = config_manager.paths
        skill_file = paths.skills_dir / "index.json"
        
        if skill_file.exists():
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._skills = {k: Skill(**v) for k, v in data.items()}
                db_logger.info(f"Loaded {len(self._skills)} skills")
            except Exception as e:
                db_logger.error(f"Error loading skills: {e}")
                self._skills = {}
        else:
            self._skills = {}
        
        # 如果没有技能，初始化内置技能
        if not self._skills:
            self._init_builtin_skills()
    
    def save(self):
        """保存技能"""
        paths = config_manager.paths
        skill_file = paths.skills_dir / "index.json"
        
        try:
            skill_file.parent.mkdir(parents=True, exist_ok=True)
            data = {k: v.model_dump() for k, v in self._skills.items()}
            with open(skill_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            db_logger.info(f"Saved {len(self._skills)} skills")
        except Exception as e:
            db_logger.error(f"Error saving skills: {e}")
    
    def _init_builtin_skills(self):
        """初始化内置技能"""
        
        builtin_skills = [
            Skill(
                id="code_reviewer",
                name="代码审查专家",
                description="智能代码审查，发现潜在问题并提供优化建议",
                version="1.0.0",
                author="DataAgent Team",
                category="code_generation",
                type="built_in",
                icon="🔍",
                created_at=datetime.datetime.now().isoformat(),
                updated_at=datetime.datetime.now().isoformat(),
                parameters=[
                    {"name": "code", "type": "string", "description": "待审查的代码", "required": True},
                    {"name": "language", "type": "string", "description": "编程语言", "required": False, "enum": ["python", "javascript", "typescript"]}
                ],
                prompts={
                    "system_prompt": "你是一位资深的代码审查专家，请按照以下标准审查代码：\n1. 检查语法错误和潜在bug\n2. 评估代码风格和最佳实践\n3. 提供性能优化建议\n4. 指出安全隐患"
                }
            ),
            Skill(
                id="data_analyzer",
                name="数据分析助手",
                description="执行数据分析和可视化",
                version="1.0.0",
                author="DataAgent Team",
                category="data_analysis",
                type="built_in",
                icon="📊",
                created_at=datetime.datetime.now().isoformat(),
                updated_at=datetime.datetime.now().isoformat(),
                parameters=[
                    {"name": "data", "type": "string", "description": "数据", "required": True},
                    {"name": "analysis_type", "type": "string", "description": "分析类型", "required": True, "enum": ["summary", "statistics", "visualization"]}
                ]
            ),
            Skill(
                id="document_processor",
                name="文档处理助手",
                description="提取、总结和分析文档内容",
                version="1.0.0",
                author="DataAgent Team",
                category="document_processing",
                type="built_in",
                icon="📄",
                created_at=datetime.datetime.now().isoformat(),
                updated_at=datetime.datetime.now().isoformat(),
                parameters=[
                    {"name": "content", "type": "string", "description": "文档内容", "required": True},
                    {"name": "task", "type": "string", "description": "任务类型", "required": True, "enum": ["summary", "key_points", "translation"]}
                ]
            )
        ]
        
        for skill in builtin_skills:
            self._skills[skill.id] = skill
        
        self.save()
        db_logger.info("Initialized built-in skills")


# ============================================================
# 全局管理器实例
# ============================================================

settings_manager = SettingsManager()
conversation_manager = ConversationManager()
skill_manager = SkillManager()


def init_all():
    """初始化所有管理器"""
    db_logger.info("Initializing all state managers...")
    
    settings_manager.load()
    conversation_manager.load()
    skill_manager.load()
    
    db_logger.info("All state managers initialized successfully")


def save_all():
    """保存所有状态"""
    db_logger.info("Saving all states...")
    
    settings_manager.save()
    conversation_manager.save()
    skill_manager.save()
    
    db_logger.info("All states saved successfully")
