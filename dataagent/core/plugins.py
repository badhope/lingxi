"""
DataAgent - 插件系统
提供丰富的插件功能和扩展机制
"""
import asyncio
import hashlib
import inspect
import json
import os
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from core.config import config_manager
from core.logging import get_logger

plugins_logger = get_logger("plugins")


class PluginType(Enum):
    """插件类型"""
    TOOL = "tool"
    DATA_SOURCE = "data_source"
    ANALYTICS = "analytics"
    DOCUMENT = "document"
    VISUALIZATION = "visualization"
    AGENT = "agent"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class PluginStatus(Enum):
    """插件状态"""
    NOT_LOADED = "not_loaded"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMetadata:
    """插件元数据"""
    id: str
    name: str
    description: str
    version: str
    author: str
    type: PluginType
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)


class PluginError(Exception):
    """插件错误"""
    pass


class Plugin(ABC):
    """插件基类"""
    
    def __init__(self):
        self.metadata: Optional[PluginMetadata] = None
        self.status: PluginStatus = PluginStatus.NOT_LOADED
        self.config: PluginConfig = PluginConfig()
        self._hooks: Dict[str, List[Callable]] = {}
        self._is_initialized = False
        self._load_time: Optional[float] = None
    
    @abstractmethod
    async def initialize(self):
        """初始化插件"""
        pass
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """执行插件功能"""
        pass
    
    async def shutdown(self):
        """关闭插件"""
        plugins_logger.info(f"Shutting down plugin: {self.metadata.name if self.metadata else 'Unknown'}")
        self.status = PluginStatus.NOT_LOADED
    
    def register_hook(self, hook_name: str, callback: Callable):
        """注册钩子"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
        plugins_logger.debug(f"Registered hook: {hook_name}")
    
    async def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """触发钩子"""
        if hook_name not in self._hooks:
            return []
        
        results = []
        for callback in self._hooks[hook_name]:
            try:
                result = await callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                plugins_logger.error(f"Hook error: {hook_name} - {e}")
        
        return results
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "id": self.metadata.id if self.metadata else "unknown",
            "name": self.metadata.name if self.metadata else "unknown",
            "type": self.metadata.type.value if self.metadata else PluginType.CUSTOM.value,
            "version": self.metadata.version if self.metadata else "0.1.0",
            "status": self.status.value,
            "enabled": self.config.enabled,
            "load_time": self._load_time
        }
    
    def __str__(self):
        return f"<Plugin {self.metadata.name if self.metadata else 'Unknown'} v{self.metadata.version if self.metadata else '0.1.0'}>"


class ToolPlugin(Plugin):
    """工具插件基类"""
    
    def __init__(self):
        super().__init__()
        self._tools: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, func: Callable):
        """注册工具函数"""
        self._tools[name] = func
        plugins_logger.info(f"Registered tool: {name}")
    
    async def execute_tool(self, tool_name: str, *args, **kwargs) -> Any:
        """执行工具函数"""
        if tool_name not in self._tools:
            raise PluginError(f"Tool not found: {tool_name}")
        
        func = self._tools[tool_name]
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())


class DataSourcePlugin(Plugin):
    """数据源插件基类"""
    
    def __init__(self):
        super().__init__()
        self._data_sources: Dict[str, Callable] = {}
    
    def register_data_source(self, name: str, func: Callable):
        """注册数据源"""
        self._data_sources[name] = func
        plugins_logger.info(f"Registered data source: {name}")
    
    async def fetch_data(self, source_name: str, *args, **kwargs) -> Any:
        """获取数据"""
        if source_name not in self._data_sources:
            raise PluginError(f"Data source not found: {source_name}")
        
        func = self._data_sources[source_name]
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def list_data_sources(self) -> List[str]:
        """列出所有数据源"""
        return list(self._data_sources.keys())


class AnalyticsPlugin(Plugin):
    """数据分析插件基类"""
    
    def __init__(self):
        super().__init__()
        self._analytics: Dict[str, Callable] = {}
    
    def register_analytic(self, name: str, func: Callable):
        """注册分析方法"""
        self._analytics[name] = func
        plugins_logger.info(f"Registered analytic: {name}")
    
    async def run_analysis(self, analysis_name: str, data: Any, *args, **kwargs) -> Any:
        """运行分析"""
        if analysis_name not in self._analytics:
            raise PluginError(f"Analytics not found: {analysis_name}")
        
        func = self._analytics[analysis_name]
        if inspect.iscoroutinefunction(func):
            return await func(data, *args, **kwargs)
        else:
            return func(data, *args, **kwargs)
    
    def list_analytics(self) -> List[str]:
        """列出所有分析方法"""
        return list(self._analytics.keys())


class DocumentPlugin(Plugin):
    """文档处理插件基类"""
    
    def __init__(self):
        super().__init__()
        self._processors: Dict[str, Callable] = {}
    
    def register_processor(self, name: str, func: Callable):
        """注册文档处理器"""
        self._processors[name] = func
        plugins_logger.info(f"Registered document processor: {name}")
    
    async def process_document(self, processor_name: str, document: Any, *args, **kwargs) -> Any:
        """处理文档"""
        if processor_name not in self._processors:
            raise PluginError(f"Processor not found: {processor_name}")
        
        func = self._processors[processor_name]
        if inspect.iscoroutinefunction(func):
            return await func(document, *args, **kwargs)
        else:
            return func(document, *args, **kwargs)
    
    def list_processors(self) -> List[str]:
        """列出所有文档处理器"""
        return list(self._processors.keys())


class VisualizationPlugin(Plugin):
    """可视化插件基类"""
    
    def __init__(self):
        super().__init__()
        self._visualizations: Dict[str, Callable] = {}
    
    def register_visualization(self, name: str, func: Callable):
        """注册可视化方法"""
        self._visualizations[name] = func
        plugins_logger.info(f"Registered visualization: {name}")
    
    async def generate_visualization(self, viz_name: str, data: Any, *args, **kwargs) -> Any:
        """生成可视化"""
        if viz_name not in self._visualizations:
            raise PluginError(f"Visualization not found: {viz_name}")
        
        func = self._visualizations[viz_name]
        if inspect.iscoroutinefunction(func):
            return await func(data, *args, **kwargs)
        else:
            return func(data, *args, **kwargs)
    
    def list_visualizations(self) -> List[str]:
        """列出所有可视化方法"""
        return list(self._visualizations.keys())


class AgentPlugin(Plugin):
    """Agent插件基类"""
    
    def __init__(self):
        super().__init__()
        self._agents: Dict[str, Callable] = {}
    
    def register_agent(self, name: str, func: Callable):
        """注册Agent"""
        self._agents[name] = func
        plugins_logger.info(f"Registered agent: {name}")
    
    async def run_agent(self, agent_name: str, *args, **kwargs) -> Any:
        """运行Agent"""
        if agent_name not in self._agents:
            raise PluginError(f"Agent not found: {agent_name}")
        
        func = self._agents[agent_name]
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def list_agents(self) -> List[str]:
        """列出所有Agent"""
        return list(self._agents.keys())


class IntegrationPlugin(Plugin):
    """集成插件基类"""
    
    def __init__(self):
        super().__init__()
        self._integrations: Dict[str, Callable] = {}
    
    def register_integration(self, name: str, func: Callable):
        """注册集成"""
        self._integrations[name] = func
        plugins_logger.info(f"Registered integration: {name}")
    
    async def execute_integration(self, integration_name: str, *args, **kwargs) -> Any:
        """执行集成"""
        if integration_name not in self._integrations:
            raise PluginError(f"Integration not found: {integration_name}")
        
        func = self._integrations[integration_name]
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    def list_integrations(self) -> List[str]:
        """列出所有集成"""
        return list(self._integrations.keys())


class PluginManager:
    """插件管理器"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._plugins: Dict[str, Plugin] = {}
            self._plugin_configs: Dict[str, PluginConfig] = {}
            self._data_dir = config_manager.paths.data_dir / "plugins"
            self._data_dir.mkdir(parents=True, exist_ok=True)
            self._initialized = True
    
    async def register_plugin(self, plugin: Plugin):
        """注册插件"""
        if not plugin.metadata:
            raise PluginError("Plugin must have metadata")
        
        plugin_id = plugin.metadata.id
        self._plugins[plugin_id] = plugin
        plugin.status = PluginStatus.LOADED
        
        plugins_logger.info(f"Registered plugin: {plugin.metadata.name} v{plugin.metadata.version}")
    
    async def initialize_plugin(self, plugin_id: str):
        """初始化插件"""
        if plugin_id not in self._plugins:
            raise PluginError(f"Plugin not found: {plugin_id}")
        
        plugin = self._plugins[plugin_id]
        
        if plugin.status == PluginStatus.DISABLED:
            plugins_logger.warning(f"Plugin {plugin_id} is disabled")
            return
        
        try:
            start_time = time.time()
            await plugin.initialize()
            plugin._load_time = time.time() - start_time
            plugin.status = PluginStatus.INITIALIZED
            plugins_logger.info(f"Initialized plugin: {plugin_id} in {plugin._load_time:.2f}s")
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugins_logger.error(f"Failed to initialize plugin {plugin_id}: {e}")
            raise PluginError(f"Plugin initialization failed: {e}")
    
    async def initialize_all(self):
        """初始化所有插件"""
        for plugin_id in self._plugins:
            try:
                await self.initialize_plugin(plugin_id)
            except Exception as e:
                plugins_logger.error(f"Failed to initialize plugin {plugin_id}: {e}")
    
    async def execute_plugin(self, plugin_id: str, *args, **kwargs) -> Any:
        """执行插件功能"""
        if plugin_id not in self._plugins:
            raise PluginError(f"Plugin not found: {plugin_id}")
        
        plugin = self._plugins[plugin_id]
        
        if plugin.status != PluginStatus.INITIALIZED:
            raise PluginError(f"Plugin {plugin_id} is not initialized")
        
        if not plugin.config.enabled:
            raise PluginError(f"Plugin {plugin_id} is disabled")
        
        return await plugin.execute(*args, **kwargs)
    
    async def shutdown_plugin(self, plugin_id: str):
        """关闭插件"""
        if plugin_id not in self._plugins:
            return
        
        plugin = self._plugins[plugin_id]
        await plugin.shutdown()
    
    async def shutdown_all(self):
        """关闭所有插件"""
        for plugin_id in self._plugins:
            try:
                await self.shutdown_plugin(plugin_id)
            except Exception as e:
                plugins_logger.error(f"Error shutting down plugin {plugin_id}: {e}")
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """获取插件"""
        return self._plugins.get(plugin_id)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[Dict[str, Any]]:
        """列出所有插件"""
        results = []
        
        for plugin_id, plugin in self._plugins.items():
            if plugin_type and plugin.metadata and plugin.metadata.type != plugin_type:
                continue
            
            results.append(plugin.get_info())
        
        return results
    
    def enable_plugin(self, plugin_id: str):
        """启用插件"""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].config.enabled = True
            plugins_logger.info(f"Enabled plugin: {plugin_id}")
    
    def disable_plugin(self, plugin_id: str):
        """禁用插件"""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].config.enabled = False
            plugins_logger.info(f"Disabled plugin: {plugin_id}")
    
    def set_plugin_config(self, plugin_id: str, settings: Dict[str, Any]):
        """设置插件配置"""
        if plugin_id in self._plugins:
            self._plugins[plugin_id].config.settings.update(settings)
            plugins_logger.info(f"Updated config for plugin: {plugin_id}")
    
    def save_state(self):
        """保存插件状态"""
        state = {
            "plugins": {
                plugin_id: {
                    "enabled": plugin.config.enabled,
                    "settings": plugin.config.settings
                }
                for plugin_id, plugin in self._plugins.items()
            },
            "saved_at": datetime.now().isoformat()
        }
        
        state_file = self._data_dir / "state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        plugins_logger.info("Saved plugin state")
    
    def load_state(self):
        """加载插件状态"""
        state_file = self._data_dir / "state.json"
        
        if state_file.exists():
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                
                for plugin_id, plugin_state in state.get("plugins", {}).items():
                    if plugin_id in self._plugins:
                        self._plugins[plugin_id].config.enabled = plugin_state.get("enabled", True)
                        self._plugins[plugin_id].config.settings = plugin_state.get("settings", {})
                
                plugins_logger.info("Loaded plugin state")
            except Exception as e:
                plugins_logger.error(f"Failed to load plugin state: {e}")


# 全局插件管理器
plugin_manager = PluginManager()


# 便捷函数
def register_plugin(plugin: Plugin):
    """注册插件的便捷函数"""
    asyncio.create_task(plugin_manager.register_plugin(plugin))


def get_plugin(plugin_id: str) -> Optional[Plugin]:
    """获取插件的便捷函数"""
    return plugin_manager.get_plugin(plugin_id)


def list_plugins(plugin_type: Optional[PluginType] = None) -> List[Dict[str, Any]]:
    """列出插件的便捷函数"""
    return plugin_manager.list_plugins(plugin_type)


async def execute_plugin(plugin_id: str, *args, **kwargs) -> Any:
    """执行插件的便捷函数"""
    return await plugin_manager.execute_plugin(plugin_id, *args, **kwargs)


__all__ = [
    "PluginType",
    "PluginStatus",
    "PluginMetadata",
    "PluginConfig",
    "PluginError",
    "Plugin",
    "ToolPlugin",
    "DataSourcePlugin",
    "AnalyticsPlugin",
    "DocumentPlugin",
    "VisualizationPlugin",
    "AgentPlugin",
    "IntegrationPlugin",
    "PluginManager",
    "plugin_manager",
    "register_plugin",
    "get_plugin",
    "list_plugins",
    "execute_plugin"
]
