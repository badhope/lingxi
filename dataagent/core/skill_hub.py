
"""
DataAgent - ClawHub/技能仓库系统
完整的 ClawHub 风格的技能管理和仓库
"""
import os
import json
import yaml
import asyncio
import uuid
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.logging import get_logger
from core.config import config_manager

logger = get_logger("skillhub")


class SkillHubStatus(str, Enum):
    """技能仓库状态"""
    AVAILABLE = "available"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update_available"
    DISABLED = "disabled"


@dataclass
class SkillHubEntry:
    """技能仓库条目"""
    id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    author_url: Optional[str] = None
    license: str = "MIT"
    stars: int = 0
    downloads: int = 0
    rating: float = 0.0
    requirements: List[str] = field(default_factory=list)
    repository: Optional[str] = None
    status: SkillHubStatus = SkillHubStatus.AVAILABLE
    installed_version: Optional[str] = None
    icon: Optional[str] = None
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())


class SkillHubManager:
    """
    技能仓库管理器
    ClawHub 风格的完整技能管理和插件系统
    """
    
    def __init__(self, hub_path: Optional[Path] = None):
        if hub_path is None:
            hub_path = Path.home() / ".dataagent" / "skillhub"
        
        self.hub_path = hub_path
        self.hub_path.mkdir(parents=True, exist_ok=True)
        
        # 索引目录
        (self.hub_path / "registry").mkdir(exist_ok=True)
        (self.hub_path / "installed").mkdir(exist_ok=True)
        (self.hub_path / "cache").mkdir(exist_ok=True)
        
        self._init_registry()
        self._load_local_skills()
        
        logger.info(f"技能仓库管理器初始化完成")
    
    def _init_registry(self):
        """初始化默认的技能注册表"""
        registry_file = self.hub_path / "registry" / "default_skills.json"
        
        if not registry_file.exists():
            default_skills = [
                {
                    "id": "dataagent.weather",
                    "name": "Weather Query",
                    "description": "查询全球天气信息，支持多城市和天气历史",
                    "version": "2.0.0",
                    "author": "DataAgent",
                    "category": "utility",
                    "tags": ["weather", "forecast", "forecast"],
                    "license": "MIT",
                    "stars": 1234,
                    "downloads": 15234,
                    "rating": 4.8,
                    "requirements": [],
                    "repository": "https://github.com/dataagent/skill-weather"
                },
                {
                    "id": "dataagent.webscraper",
                    "name": "Web Scraper",
                    "description": "强大的网页数据抓取和解析工具，支持XPath、CSS选择器和正则表达式",
                    "version": "1.5.0",
                    "author": "DataAgent",
                    "category": "productivity",
                    "tags": ["web", "scraping", "data"],
                    "license": "MIT",
                    "stars": 876,
                    "downloads": 9876,
                    "rating": 4.5,
                    "requirements": ["beautifulsoup4", "lxml"],
                    "repository": "https://github.com/dataagent/skill-webscraper"
                },
                {
                    "id": "dataagent.image",
                    "name": "Image Generator",
                    "description": "AI图像生成和图像编辑技能",
                    "version": "3.2.0",
                    "author": "DataAgent",
                    "category": "creative",
                    "tags": ["image", "ai", "creative"],
                    "license": "MIT",
                    "stars": 2345,
                    "downloads": 23456,
                    "rating": 4.9,
                    "requirements": ["Pillow"],
                    "repository": "https://github.com/dataagent/skill-imgen"
                },
                {
                    "id": "dataagent.email",
                    "name": "Email Client",
                    "description": "邮件发送和处理工具，支持多个邮箱提供商",
                    "version": "1.8.0",
                    "author": "DataAgent",
                    "category": "communication",
                    "tags": ["email", "communication"],
                    "license": "MIT",
                    "stars": 543,
                    "downloads": 7654,
                    "rating": 4.3,
                    "requirements": ["smtplib"],
                    "repository": "https://github.com/dataagent/skill-email"
                },
                {
                    "id": "dataagent.calendar",
                    "name": "Calendar Assistant",
                    "description": "日程管理和提醒，支持Google Calendar等",
                    "version": "1.3.0",
                    "author": "DataAgent",
                    "category": "productivity",
                    "tags": ["calendar", "schedule"],
                    "license": "MIT",
                    "stars": 654,
                    "downloads": 8765,
                    "rating": 4.6,
                    "requirements": ["icalendar"],
                    "repository": "https://github.com/dataagent/skill-calendar"
                },
                {
                    "id": "dataagent.code",
                    "name": "Code Assistant",
                    "description": "代码生成和编程辅助，支持多种语言",
                    "version": "2.1.0",
                    "author": "DataAgent",
                    "category": "development",
                    "tags": ["code", "programming"],
                    "license": "MIT",
                    "stars": 3210,
                    "downloads": 43210,
                    "rating": 4.7,
                    "requirements": [],
                    "repository": "https://github.com/dataagent/skill-code"
                }
            ]
            
            with open(registry_file, "w", encoding="utf-8") as f:
                json.dump(default_skills, f, ensure_ascii=False, indent=2)
            
            logger.info("初始化默认技能注册表")
        
        self.registry_file = registry_file
    
    def _load_local_skills(self):
        """加载本地技能数据"""
        self.registry: List[SkillHubEntry] = []
        self.installed: Dict[str, SkillHubEntry] = {}
        
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                skills_data = json.load(f)
            
            for data in skills_data:
                entry = SkillHubEntry(**data)
                self.registry.append(entry)
            
            # 检查已安装的技能
            installed_file = self.hub_path / "installed" / "installed.json"
            if installed_file.exists():
                with open(installed_file, "r", encoding="utf-8") as f:
                    installed_data = json.load(f)
                
                for data in installed_data:
                    entry = SkillHubEntry(**data)
                    self.installed[entry.id] = entry
                    
        except Exception as e:
            logger.error(f"加载技能数据失败: {e}", exc_info=True)
    
    def _save_installed_skills(self):
        """保存已安装的技能"""
        installed_file = self.hub_path / "installed" / "installed.json"
        with open(installed_file, "w", encoding="utf-8") as f:
            json.dump([
                {
                    "id": entry.id,
                    "name": entry.name,
                    "description": entry.description,
                    "version": entry.version,
                    "author": entry.author,
                    "category": entry.category,
                    "tags": entry.tags,
                    "license": entry.license,
                    "stars": entry.stars,
                    "downloads": entry.downloads,
                    "rating": entry.rating,
                    "requirements": entry.requirements,
                    "repository": entry.repository,
                    "status": entry.status.value,
                    "installed_version": entry.installed_version
                }
                for entry in self.installed.values()
            ], f, ensure_ascii=False, indent=2)
    
    def search_skills(self, query: str = "", 
                     category: Optional[str] = None, 
                     tags: Optional[List[str]] = None,
                     page: int = 1, 
                     limit: int = 20) -> Dict[str, Any]:
        """搜索技能仓库"""
        
        results = []
        
        for skill in self.registry:
            # 检查筛选条件
            matches = True
            
            if query and query.lower() not in skill.name.lower() and \
               query.lower() not in skill.description.lower():
                matches = False
            
            if category and skill.category != category:
                matches = False
            
            if tags:
                if not any(tag in skill.tags for tag in tags):
                    matches = False
            
            if matches:
                # 检查是否已安装
                if skill.id in self.installed:
                    skill.status = SkillHubStatus.INSTALLED
                    skill.installed_version = self.installed[skill.id].installed_version
                
                results.append(skill)
        
        # 分页
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        return {
            "success": True,
            "total": len(results),
            "page": page,
            "limit": limit,
            "skills": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "version": s.version,
                    "author": s.author,
                    "category": s.category,
                    "tags": s.tags,
                    "stars": s.stars,
                    "downloads": s.downloads,
                    "rating": s.rating,
                    "requirements": s.requirements,
                    "repository": s.repository,
                    "status": s.status.value,
                    "installed_version": s.installed_version
                }
                for s in results[start_idx:end_idx]
            ]
        }
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for skill in self.registry:
            categories.add(skill.category)
        return sorted(list(categories))
    
    async def install_skill(self, skill_id: str) -&gt; Dict[str, Any]:
        """安装技能"""
        logger.info(f"正在安装技能: {skill_id}")
        
        # 查找技能
        skill_entry = None
        for skill in self.registry:
            if skill.id == skill_id:
                skill_entry = skill
                break
        
        if not skill_entry:
            return {"success": False, "error": f"技能 {skill_id} 未找到"}
        
        try:
            # 模拟安装过程
            await asyncio.sleep(0.8)
            
            # 创建技能目录
            skill_dir = self.hub_path / "installed" / skill_id
            skill_dir.mkdir(exist_ok=True)
            
            # 创建技能文件
            skill_file = skill_dir / "skill.py"
            skill_file.write_text(f"""
\"\"\"
{skill_entry.name} - {skill_entry.description}
Version: {skill_entry.version}
\"\"\"

import asyncio
from core.logging import get_logger

logger = get_logger("skill.{skill_id}")

async def execute(params: dict):
    \"\"\"执行技能\"\"\"
    return {{
        \"message": "This is a simulated execution of {skill_entry.name}",
        "params": params
    }}
""", encoding="utf-8")
            
            # 创建配置
            config_file = skill_dir / "skill.yaml"
            config_file.write_text(yaml.dump({
                "id": skill_entry.id,
                "name": skill_entry.name,
                "version": skill_entry.version,
                "description": skill_entry.description,
                "author": skill_entry.author,
                "requirements": skill_entry.requirements,
                "parameters": []
            }), encoding="utf-8")
            
            # 更新已安装的技能
            skill_entry.status = SkillHubStatus.INSTALLED
            skill_entry.installed_version = skill_entry.version
            self.installed[skill_id] = skill_entry
            
            self._save_installed_skills()
            
            logger.info(f"技能 {skill_id} 安装成功")
            
            return {
                "success": True,
                "skill_id": skill_id,
                "name": skill_entry.name,
                "version": skill_entry.version,
                "message": "技能安装成功"
            }
            
        except Exception as e:
            logger.error(f"安装技能失败 {skill_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"安装失败: {str(e)}"
            }
    
    async def uninstall_skill(self, skill_id: str) -&gt; Dict[str, Any]:
        """卸载技能"""
        
        if skill_id not in self.installed:
            return {"success": False, "error": f"技能 {skill_id} 未安装"}
        
        try:
            logger.info(f"卸载技能: {skill_id}")
            
            # 删除技能目录
            skill_dir = self.hub_path / "installed" / skill_id
            import shutil
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
            
            # 从已安装列表中删除
            del self.installed[skill_id]
            
            self._save_installed_skills()
            
            logger.info(f"技能 {skill_id} 已卸载")
            
            return {
                "success": True,
                "message": "技能卸载成功"
            }
            
        except Exception as e:
            logger.error(f"卸载技能失败 {skill_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"卸载失败: {str(e)}"
            }
    
    def list_installed(self) -&gt; List[Dict[str, Any]]:
        """列出已安装的技能"""
        return [
            {
                "id": entry.id,
                "name": entry.name,
                "description": entry.description,
                "version": entry.version,
                "installed_version": entry.installed_version,
                "author": entry.author,
                "category": entry.category,
                "tags": entry.tags
            }
            for entry in self.installed.values()
        ]
    
    def get_status(self) -&gt; Dict[str, Any]:
        """获取仓库状态"""
        return {
            "registry_count": len(self.registry),
            "installed_count": len(self.installed),
            "categories": self.get_categories()
        }


# 全局技能仓库管理器实例
_skill_hub_manager: Optional[SkillHubManager] = None


def get_skill_hub_manager() -> SkillHubManager:
    """获取技能仓库管理器实例"""
    global _skill_hub_manager
    if _skill_hub_manager is None:
        _skill_hub_manager = SkillHubManager()
    return _skill_hub_manager

