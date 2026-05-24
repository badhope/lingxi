"""
DataAgent - Skills 技能系统
类似于 OpenClaw 的 ClawHub 系统，提供模块化插件架构和技能仓库
"""
import asyncio
import json
import time
import uuid
import httpx
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from importlib import import_module

from core.logging import get_logger
from core.config import config_manager

logger = get_logger("skills")


class SkillStatus(str, Enum):
    """技能状态"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class SkillParameter:
    """技能参数定义"""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    default: Any = None
    options: List[Any] = field(default_factory=list)


@dataclass
class Skill:
    """技能定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    parameters: List[SkillParameter] = field(default_factory=list)
    status: SkillStatus = SkillStatus.INACTIVE
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    enabled: bool = True
    _execute_func: Optional[Callable] = None
    _module_path: Optional[str] = None


class SkillsEngine:
    """
    技能引擎 - 插件管理器
    类似于 OpenClaw 的 ClawHub 系统
    """
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._data_path: Optional[Path] = None
        self._init_data_path()
        self._register_builtin_skills()
        self._load_skills()
    
    def _init_data_path(self):
        """初始化数据存储路径"""
        try:
            self._data_path = config_manager.paths.data_dir / "skills"
            self._data_path.mkdir(parents=True, exist_ok=True)
            
            # 创建技能目录
            (self._data_path / "installed").mkdir(exist_ok=True)
            (self._data_path / "custom").mkdir(exist_ok=True)
        except Exception as e:
            logger.warning(f"无法初始化数据存储路径: {e}")
            self._data_path = Path.home() / ".dataagent" / "skills"
            self._data_path.mkdir(parents=True, exist_ok=True)
    
    def _register_builtin_skills(self):
        """注册内置技能"""
        # 1. 天气查询技能（示例）
        weather_params = [
            SkillParameter(name="city", type="string", description="城市名称", required=True),
            SkillParameter(name="unit", type="string", description="温度单位", options=["celsius", "fahrenheit"], default="celsius")
        ]
        
        weather_skill = Skill(
            id="builtin_weather",
            name="Weather Query",
            description="查询天气信息",
            version="1.0.0",
            author="DataAgent",
            category="utility",
            tags=["weather", "utility"],
            parameters=weather_params,
            status=SkillStatus.ACTIVE
        )
        weather_skill._execute_func = self._execute_weather_skill
        self.skills[weather_skill.id] = weather_skill
        
        # 2. 文件操作技能（示例）
        file_params = [
            SkillParameter(name="action", type="string", description="操作类型", required=True, options=["read", "write", "list"]),
            SkillParameter(name="path", type="string", description="文件路径", required=True),
            SkillParameter(name="content", type="string", description="写入内容")
        ]
        
        file_skill = Skill(
            id="builtin_file_ops",
            name="File Operations",
            description="文件读写操作",
            version="1.0.0",
            author="DataAgent",
            category="utility",
            tags=["file", "utility"],
            parameters=file_params,
            status=SkillStatus.ACTIVE
        )
        file_skill._execute_func = self._execute_file_skill
        self.skills[file_skill.id] = file_skill
        
        # 3. 计算器技能（示例）
        calc_params = [
            SkillParameter(name="expression", type="string", description="数学表达式", required=True)
        ]
        
        calc_skill = Skill(
            id="builtin_calculator",
            name="Calculator",
            description="数学计算",
            version="1.0.0",
            author="DataAgent",
            category="utility",
            tags=["math", "calculator"],
            parameters=calc_params,
            status=SkillStatus.ACTIVE
        )
        calc_skill._execute_func = self._execute_calculator_skill
        self.skills[calc_skill.id] = calc_skill
        
        # 4. 网络搜索技能（示例）
        search_params = [
            SkillParameter(name="query", type="string", description="搜索关键词", required=True),
            SkillParameter(name="num_results", type="number", description="结果数量", default=5)
        ]
        
        search_skill = Skill(
            id="builtin_web_search",
            name="Web Search",
            description="网络搜索",
            version="1.0.0",
            author="DataAgent",
            category="information",
            tags=["search", "web"],
            parameters=search_params,
            status=SkillStatus.ACTIVE
        )
        search_skill._execute_func = self._execute_search_skill
        self.skills[search_skill.id] = search_skill
        
        logger.info(f"注册了 {len(self.skills)} 个内置技能")
    
    async def execute_skill(self, skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        skill = self.skills.get(skill_id)
        if not skill:
            return {"success": False, "error": f"Skill not found: {skill_id}"}
        
        if not skill.enabled:
            return {"success": False, "error": f"Skill is disabled: {skill_id}"}
        
        # 验证参数
        validation = self._validate_params(skill, params)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        try:
            if skill._execute_func:
                if asyncio.iscoroutinefunction(skill._execute_func):
                    result = await skill._execute_func(params)
                else:
                    result = skill._execute_func(params)
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": "Skill has no execute function"}
        except Exception as e:
            logger.error(f"技能执行失败: {skill.name}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _validate_params(self, skill: Skill, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        for param in skill.parameters:
            if param.required and param.name not in params:
                return {"valid": False, "error": f"Missing required parameter: {param.name}"}
            
            if param.name in params and param.options:
                if params[param.name] not in param.options:
                    return {"valid": False, "error": f"Invalid value for {param.name}. Must be one of: {param.options}"}
        
        return {"valid": True}
    
    # === 内置技能实现 ===
    async def _execute_weather_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行天气查询技能"""
        city = params.get("city", "")
        unit = params.get("unit", "celsius")
        
        # 模拟天气数据
        return {
            "city": city,
            "temperature": 22 if unit == "celsius" else 72,
            "unit": unit,
            "condition": "Sunny",
            "humidity": 65,
            "wind_speed": 10
        }
    
    async def _execute_file_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行文件操作技能"""
        action = params.get("action", "")
        path = params.get("path", "")
        
        if action == "read":
            if Path(path).exists():
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                return {"path": path, "content": content}
            return {"error": "File not found"}
        elif action == "write":
            content = params.get("content", "")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"path": path, "status": "written"}
        elif action == "list":
            files = list(Path(path).glob("*"))
            return {"path": path, "files": [str(f.name) for f in files]}
        return {"error": "Unknown action"}
    
    async def _execute_calculator_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行计算器技能"""
        expression = params.get("expression", "")
        try:
            # 安全计算（仅允许简单数学运算）
            allowed_chars = "0123456789+-*/(). "
            if not all(c in allowed_chars for c in expression):
                return {"error": "Invalid expression"}
            
            # 使用 ast 或更安全的方法
            result = eval(expression, {"__builtins__": {}}, {})
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": f"Calculation failed: {str(e)}"}
    
    async def _execute_search_skill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索技能"""
        query = params.get("query", "")
        num_results = params.get("num_results", 5)
        
        # 模拟搜索结果
        results = []
        for i in range(num_results):
            results.append({
                "title": f"Search Result {i+1} for: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a simulated search result about {query}...",
                "relevance": 1.0 - (i * 0.1)
            })
        
        return {"query": query, "results": results}
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(skill_id)
    
    def list_skills(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Skill]:
        """列出所有技能"""
        skills = list(self.skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if tags:
            skills = [s for s in skills if any(t in s.tags for t in tags)]
        
        return skills
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for skill in self.skills.values():
            categories.add(skill.category)
        return sorted(list(categories))
    
    def enable_skill(self, skill_id: str) -> bool:
        """启用技能"""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = True
            self.skills[skill_id].status = SkillStatus.ACTIVE
            self._save_skills()
            return True
        return False
    
    def disable_skill(self, skill_id: str) -> bool:
        """禁用技能"""
        if skill_id in self.skills:
            self.skills[skill_id].enabled = False
            self.skills[skill_id].status = SkillStatus.INACTIVE
            self._save_skills()
            return True
        return False
    
    def register_custom_skill(self,
                             name: str,
                             description: str,
                             execute_func: Callable,
                             parameters: Optional[List[SkillParameter]] = None,
                             category: str = "custom",
                             tags: Optional[List[str]] = None) -> str:
        """注册自定义技能"""
        skill = Skill(
            name=name,
            description=description,
            category=category,
            tags=tags or [],
            parameters=parameters or [],
            status=SkillStatus.ACTIVE,
            _execute_func=execute_func
        )
        
        self.skills[skill.id] = skill
        self._save_skills()
        logger.info(f"注册自定义技能: {name}")
        return skill.id
    
    def _save_skills(self):
        """保存技能元数据"""
        if not self._data_path:
            return
        
        try:
            skills_data = []
            for skill in self.skills.values():
                skills_data.append({
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "version": skill.version,
                    "author": skill.author,
                    "category": skill.category,
                    "tags": skill.tags,
                    "parameters": [
                        {"name": p.name, "type": p.type, "description": p.description,
                         "required": p.required, "default": p.default, "options": p.options}
                        for p in skill.parameters
                    ],
                    "status": skill.status.value,
                    "config": skill.config,
                    "enabled": skill.enabled,
                    "created_at": skill.created_at,
                    "updated_at": skill.updated_at,
                    "_module_path": skill._module_path
                })
            
            skills_file = self._data_path / "skills.json"
            with open(skills_file, "w", encoding="utf-8") as f:
                json.dump(skills_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存技能失败: {e}")
    
    def _load_skills(self):
        """加载技能元数据"""
        if not self._data_path:
            return
        
        try:
            skills_file = self._data_path / "skills.json"
            if skills_file.exists():
                with open(skills_file, "r", encoding="utf-8") as f:
                    skills_data = json.load(f)
                
                # 只更新已存在技能的配置
                for skill_data in skills_data:
                    skill_id = skill_data["id"]
                    if skill_id in self.skills:
                        self.skills[skill_id].config = skill_data.get("config", {})
                        self.skills[skill_id].enabled = skill_data.get("enabled", True)
        except Exception as e:
            logger.error(f"加载技能失败: {e}")
    
    # === 技能仓库功能 ===
    async def search_skill_hub(self, query: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """搜索技能仓库"""
        # 模拟 ClawHub 的技能仓库
        mock_skills = [
            {
                "id": "com.example.weather",
                "name": "Weather Skill",
                "description": "查询全球天气信息",
                "version": "2.0.0",
                "author": "OpenClaw",
                "category": "utility",
                "tags": ["weather", "forecast"],
                "downloads": 15234,
                "rating": 4.8
            },
            {
                "id": "com.example.webscraper",
                "name": "Web Scraper",
                "description": "网页数据抓取和解析",
                "version": "1.5.0",
                "author": "OpenClaw",
                "category": "productivity",
                "tags": ["web", "scraping"],
                "downloads": 9876,
                "rating": 4.5
            },
            {
                "id": "com.example.imagen",
                "name": "Image Generator",
                "description": "AI 图像生成",
                "version": "3.2.0",
                "author": "OpenClaw",
                "category": "creative",
                "tags": ["image", "ai"],
                "downloads": 23456,
                "rating": 4.9
            },
            {
                "id": "com.example.email",
                "name": "Email Client",
                "description": "邮件处理和发送",
                "version": "1.8.0",
                "author": "OpenClaw",
                "category": "communication",
                "tags": ["email"],
                "downloads": 7654,
                "rating": 4.3
            }
        ]
        
        # 简单过滤
        filtered = [s for s in mock_skills if query.lower() in s["name"].lower() or query.lower() in s["description"].lower()]
        
        return {
            "success": True,
            "query": query,
            "total": len(filtered),
            "page": page,
            "limit": limit,
            "skills": filtered
        }
    
    async def install_skill_from_hub(self, skill_id: str) -> Dict[str, Any]:
        """从技能仓库安装技能"""
        logger.info(f"安装技能: {skill_id}")
        
        # 模拟安装过程
        try:
            # 模拟下载和安装
            await asyncio.sleep(0.5)
            
            # 创建一个模拟的已安装技能
            installed_skill = Skill(
                id=f"hub_{skill_id.replace('.', '_')}",
                name=f"Installed Skill: {skill_id}",
                description=f"从技能仓库安装的 {skill_id}",
                version="1.0.0",
                author="SkillHub",
                category="downloaded",
                tags=["installed", "hub"],
                status=SkillStatus.ACTIVE,
                _module_path=skill_id
            )
            
            installed_skill._execute_func = lambda params: {
                "message": f"Executed skill {skill_id}",
                "params": params
            }
            
            self.skills[installed_skill.id] = installed_skill
            self._save_skills()
            
            return {
                "success": True,
                "skill_id": installed_skill.id,
                "name": installed_skill.name,
                "message": "技能安装成功"
            }
        except Exception as e:
            logger.error(f"安装技能失败: {e}")
            return {
                "success": False,
                "error": f"Failed to install {skill_id}: {str(e)}"
            }
    
    async def uninstall_skill(self, skill_id: str) -> Dict[str, Any]:
        """卸载技能"""
        if skill_id.startswith("builtin_"):
            return {
                "success": False,
                "error": "Cannot uninstall built-in skills"
            }
        
        if skill_id in self.skills:
            del self.skills[skill_id]
            self._save_skills()
            return {
                "success": True,
                "message": f"Skill {skill_id} uninstalled"
            }
        else:
            return {
                "success": False,
                "error": f"Skill {skill_id} not found"
            }


# 全局技能引擎实例
_skills_engine: Optional[SkillsEngine] = None


def get_skills_engine() -> SkillsEngine:
    """获取技能引擎实例"""
    global _skills_engine
    if _skills_engine is None:
        _skills_engine = SkillsEngine()
    return _skills_engine


__all__ = [
    "SkillStatus",
    "SkillParameter",
    "Skill",
    "SkillsEngine",
    "get_skills_engine"
]
