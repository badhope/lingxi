"""
DataAgent - Agent 市场系统
提供 Agent 模板管理、分享、评价等功能
"""
import asyncio
import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    List,
    Dict,
    Optional,
    Any,
)

from pydantic import BaseModel, Field

from core.config import config_manager
from core.logging import get_logger
from core.auth import User


agent_market_logger = get_logger("agent_market")


class AgentCategory(Enum):
    """Agent 分类"""
    GENERAL = "general"
    PROGRAMMING = "programming"
    WRITING = "writing"
    ANALYSIS = "analysis"
    DATA = "data"
    CREATIVE = "creative"
    EDUCATION = "education"
    BUSINESS = "business"
    RESEARCH = "research"
    OTHER = "other"


class AgentVisibility(Enum):
    """Agent 可见性"""
    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"


@dataclass
class AgentRating:
    """Agent 评分"""
    user_id: str
    score: float  # 1-5
    comment: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AgentTemplate:
    """Agent 模板"""
    id: str
    name: str
    description: str
    creator_id: str
    category: AgentCategory
    visibility: AgentVisibility
    created_at: str
    updated_at: str
    instructions: str
    system_prompt: str
    tags: List[str] = field(default_factory=list)
    ratings: List[AgentRating] = field(default_factory=list)
    download_count: int = 0
    view_count: int = 0
    version: str = "1.0.0"
    is_official: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def average_rating(self) -> float:
        """计算平均评分"""
        if not self.ratings:
            return 0.0
        return sum(r.score for r in self.ratings) / len(self.ratings)
    
    @property
    def rating_count(self) -> int:
        """评分数量"""
        return len(self.ratings)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "creator_id": self.creator_id,
            "category": self.category.value,
            "visibility": self.visibility.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "instructions": self.instructions,
            "system_prompt": self.system_prompt,
            "tags": self.tags,
            "download_count": self.download_count,
            "view_count": self.view_count,
            "average_rating": self.average_rating,
            "rating_count": self.rating_count,
            "version": self.version,
            "is_official": self.is_official,
            "metadata": self.metadata
        }


@dataclass
class UserAgent:
    """用户保存的 Agent"""
    id: str
    user_id: str
    name: str
    system_prompt: str
    instructions: str
    created_at: str
    updated_at: str
    template_id: Optional[str] = None
    is_public: bool = False
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "system_prompt": self.system_prompt,
            "instructions": self.instructions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "template_id": self.template_id,
            "is_public": self.is_public,
            "tags": self.tags,
            "metadata": self.metadata
        }


class AgentMarketManager:
    """Agent 市场管理器"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._templates: Dict[str, AgentTemplate] = {}
            self._user_agents: Dict[str, Dict[str, UserAgent]] = {}
            self._data_dir = config_manager.paths.data_dir / "agent_market"
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._load_data()
            self._initialized = True
    
    def _load_data(self):
        """加载数据"""
        # 加载模板
        templates_file = self._data_dir / "templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for tid, t_dict in data.items():
                        # 过滤掉计算属性
                        t_dict.pop('average_rating', None)
                        t_dict.pop('rating_count', None)
                        t_dict['category'] = AgentCategory(t_dict['category'])
                        t_dict['visibility'] = AgentVisibility(t_dict['visibility'])
                        t_dict['ratings'] = [AgentRating(**r) for r in t_dict.get('ratings', [])]
                        self._templates[tid] = AgentTemplate(**t_dict)
            except Exception as e:
                agent_market_logger.error(f"加载模板数据失败: {e}")
        
        # 加载用户 Agent
        user_agents_file = self._data_dir / "user_agents.json"
        if user_agents_file.exists():
            try:
                with open(user_agents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, agents_dict in data.items():
                        self._user_agents[user_id] = {}
                        for aid, a_dict in agents_dict.items():
                            self._user_agents[user_id][aid] = UserAgent(**a_dict)
            except Exception as e:
                agent_market_logger.error(f"加载用户 Agent 数据失败: {e}")
    
    def _save_data(self):
        """保存数据"""
        # 保存模板
        templates_file = self._data_dir / "templates.json"
        templates_data = {tid: t.to_dict() for tid, t in self._templates.items()}
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, ensure_ascii=False, indent=2)
        
        # 保存用户 Agent
        user_agents_file = self._data_dir / "user_agents.json"
        user_agents_data = {}
        for user_id, agents in self._user_agents.items():
            user_agents_data[user_id] = {aid: a.to_dict() for aid, a in agents.items()}
        
        with open(user_agents_file, 'w', encoding='utf-8') as f:
            json.dump(user_agents_data, f, ensure_ascii=False, indent=2)
    
    async def create_template(
        self,
        name: str,
        description: str,
        creator_id: str,
        instructions: str,
        system_prompt: str,
        category: AgentCategory = AgentCategory.OTHER,
        visibility: AgentVisibility = AgentVisibility.PRIVATE,
        tags: Optional[List[str]] = None,
        version: str = "1.0.0",
        is_official: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentTemplate:
        """创建 Agent 模板"""
        template_id = secrets.token_hex(16)
        now = datetime.now().isoformat()
        
        template = AgentTemplate(
            id=template_id,
            name=name,
            description=description,
            creator_id=creator_id,
            category=category,
            visibility=visibility,
            created_at=now,
            updated_at=now,
            instructions=instructions,
            system_prompt=system_prompt,
            tags=tags or [],
            version=version,
            is_official=is_official,
            metadata=metadata or {}
        )
        
        self._templates[template_id] = template
        self._save_data()
        agent_market_logger.info(f"创建 Agent 模板: {name}")
        return template
    
    async def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """获取模板"""
        return self._templates.get(template_id)
    
    async def list_templates(
        self,
        category: Optional[AgentCategory] = None,
        tag: Optional[str] = None,
        only_public: bool = True,
        search_query: Optional[str] = None,
        sort_by: str = "download_count"
    ) -> List[AgentTemplate]:
        """列出模板"""
        templates = list(self._templates.values())
        
        if only_public:
            templates = [t for t in templates if t.visibility == AgentVisibility.PUBLIC]
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tag:
            templates = [t for t in templates if tag in t.tags]
        
        if search_query:
            q = search_query.lower()
            templates = [
                t for t in templates
                if q in t.name.lower() or q in t.description.lower()
            ]
        
        if sort_by == "download_count":
            templates.sort(key=lambda t: t.download_count, reverse=True)
        elif sort_by == "rating":
            templates.sort(key=lambda t: t.average_rating, reverse=True)
        elif sort_by == "created_at":
            templates.sort(key=lambda t: t.created_at, reverse=True)
        
        return templates
    
    async def update_template(self, template_id: str, **kwargs) -> Optional[AgentTemplate]:
        """更新模板"""
        template = self._templates.get(template_id)
        if not template:
            return None
        
        allowed_fields = [
            'name', 'description', 'instructions', 'system_prompt',
            'category', 'visibility', 'tags', 'version', 'metadata'
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                if key == 'category' and isinstance(value, str):
                    value = AgentCategory(value)
                if key == 'visibility' and isinstance(value, str):
                    value = AgentVisibility(value)
                setattr(template, key, value)
        
        template.updated_at = datetime.now().isoformat()
        self._save_data()
        agent_market_logger.info(f"更新 Agent 模板: {template.name}")
        return template
    
    async def download_template(self, template_id: str) -> Optional[AgentTemplate]:
        """下载模板（增加计数）"""
        template = self._templates.get(template_id)
        if template:
            template.download_count += 1
            self._save_data()
            agent_market_logger.info(f"下载 Agent 模板: {template.name}")
        return template
    
    async def view_template(self, template_id: str) -> Optional[AgentTemplate]:
        """查看模板（增加计数）"""
        template = self._templates.get(template_id)
        if template:
            template.view_count += 1
            self._save_data()
        return template
    
    async def rate_template(
        self,
        template_id: str,
        user_id: str,
        score: float,
        comment: Optional[str] = None
    ) -> Optional[AgentTemplate]:
        """评分模板"""
        template = self._templates.get(template_id)
        if not template:
            return None
        
        # 移除该用户的旧评分
        template.ratings = [r for r in template.ratings if r.user_id != user_id]
        
        # 添加新评分
        template.ratings.append(AgentRating(user_id=user_id, score=score, comment=comment))
        template.updated_at = datetime.now().isoformat()
        self._save_data()
        agent_market_logger.info(f"评分 Agent 模板: {template.name}")
        return template
    
    async def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self._templates:
            del self._templates[template_id]
            self._save_data()
            agent_market_logger.info(f"删除 Agent 模板: {template_id}")
            return True
        return False
    
    # 用户 Agent 管理
    async def create_user_agent(
        self,
        user_id: str,
        name: str,
        system_prompt: str,
        instructions: str,
        template_id: Optional[str] = None,
        is_public: bool = False,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserAgent:
        """创建用户 Agent"""
        agent_id = secrets.token_hex(16)
        now = datetime.now().isoformat()
        
        agent = UserAgent(
            id=agent_id,
            user_id=user_id,
            name=name,
            system_prompt=system_prompt,
            instructions=instructions,
            created_at=now,
            updated_at=now,
            template_id=template_id,
            is_public=is_public,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        if user_id not in self._user_agents:
            self._user_agents[user_id] = {}
        
        self._user_agents[user_id][agent_id] = agent
        self._save_data()
        agent_market_logger.info(f"创建用户 Agent: {name}")
        return agent
    
    async def get_user_agent(self, user_id: str, agent_id: str) -> Optional[UserAgent]:
        """获取用户 Agent"""
        if user_id not in self._user_agents:
            return None
        return self._user_agents[user_id].get(agent_id)
    
    async def list_user_agents(self, user_id: str) -> List[UserAgent]:
        """列出用户的所有 Agent"""
        if user_id not in self._user_agents:
            return []
        return list(self._user_agents[user_id].values())
    
    async def update_user_agent(self, user_id: str, agent_id: str, **kwargs) -> Optional[UserAgent]:
        """更新用户 Agent"""
        if user_id not in self._user_agents:
            return None
        
        agent = self._user_agents[user_id].get(agent_id)
        if not agent:
            return None
        
        allowed_fields = ['name', 'system_prompt', 'instructions', 'is_public', 'tags', 'metadata']
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(agent, key, value)
        
        agent.updated_at = datetime.now().isoformat()
        self._save_data()
        return agent
    
    async def delete_user_agent(self, user_id: str, agent_id: str) -> bool:
        """删除用户 Agent"""
        if user_id in self._user_agents and agent_id in self._user_agents[user_id]:
            del self._user_agents[user_id][agent_id]
            self._save_data()
            agent_market_logger.info(f"删除用户 Agent: {agent_id}")
            return True
        return False
    
    async def publish_agent_to_market(
        self,
        user_id: str,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: AgentCategory = AgentCategory.OTHER,
        tags: Optional[List[str]] = None
    ) -> Optional[AgentTemplate]:
        """将用户 Agent 发布到市场"""
        agent = await self.get_user_agent(user_id, agent_id)
        if not agent:
            return None
        
        template = await self.create_template(
            name=name or agent.name,
            description=description or f"由用户发布的 Agent: {agent.name}",
            creator_id=user_id,
            instructions=agent.instructions,
            system_prompt=agent.system_prompt,
            category=category,
            visibility=AgentVisibility.PUBLIC,
            tags=tags or agent.tags
        )
        
        return template


# 全局实例
agent_market_manager = AgentMarketManager()


# 便捷函数
async def create_agent_template(
    name: str,
    description: str,
    creator_id: str,
    instructions: str,
    system_prompt: str,
    **kwargs
) -> AgentTemplate:
    """创建 Agent 模板"""
    return await agent_market_manager.create_template(
        name, description, creator_id, instructions, system_prompt, **kwargs
    )


async def list_agent_templates(**kwargs) -> List[AgentTemplate]:
    """列出 Agent 模板"""
    return await agent_market_manager.list_templates(**kwargs)


async def get_agent_template(template_id: str) -> Optional[AgentTemplate]:
    """获取 Agent 模板"""
    return await agent_market_manager.get_template(template_id)


async def create_user_agent(user_id: str, name: str, system_prompt: str, instructions: str, **kwargs) -> UserAgent:
    """创建用户 Agent"""
    return await agent_market_manager.create_user_agent(user_id, name, system_prompt, instructions, **kwargs)


async def list_user_agents(user_id: str) -> List[UserAgent]:
    """列出用户 Agent"""
    return await agent_market_manager.list_user_agents(user_id)


__all__ = [
    "AgentCategory",
    "AgentVisibility",
    "AgentRating",
    "AgentTemplate",
    "UserAgent",
    "AgentMarketManager",
    "agent_market_manager",
    "create_agent_template",
    "list_agent_templates",
    "get_agent_template",
    "create_user_agent",
    "list_user_agents",
]
