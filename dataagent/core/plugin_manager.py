"""
DataAgent - 增强插件管理器
提供插件仓库、热加载、依赖管理等功能
"""
import asyncio
import importlib
import importlib.util
import os
import pkgutil
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type
from dataclasses import dataclass, field
from datetime import datetime

from core.logging import get_logger
from core.plugins import Plugin, PluginMetadata, PluginStatus, PluginType, PluginConfig

logger = get_logger("plugin_manager")


@dataclass
class PluginInfo:
    """插件信息"""
    metadata: PluginMetadata
    plugin_class: Type[Plugin]
    path: str
    loaded: bool = False
    instance: Optional[Plugin] = None
    last_loaded_at: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class PluginRepository:
    """插件仓库"""
    id: str
    name: str
    url: str
    enabled: bool = True
    priority: int = 0
    plugins: List[str] = field(default_factory=list)


class EnhancedPluginManager:
    """
    增强插件管理器
    支持插件仓库、热加载、依赖管理等
    """
    
    def __init__(
        self,
        plugin_dirs: Optional[List[Path]] = None,
        auto_reload: bool = True
    ):
        if plugin_dirs is None:
            plugin_dirs = [Path.home() / ".dataagent" / "plugins"]
        
        self.plugin_dirs = plugin_dirs
        self.auto_reload = auto_reload
        
        # 插件存储
        self._plugins: Dict[str, PluginInfo] = {}
        self._repositories: Dict[str, PluginRepository] = {}
        
        # 插件依赖图
        self._dependencies: Dict[str, Set[str]] = {}
        
        # 文件修改监控
        self._file_mtimes: Dict[str, float] = {}
        
        # 初始化插件目录
        for plugin_dir in self.plugin_dirs:
            plugin_dir.mkdir(parents=True, exist_ok=True)
            init_file = plugin_dir / "__init__.py"
            if not init_file.exists():
                init_file.touch()
        
        logger.info("增强插件管理器初始化完成")
    
    # ========== 插件发现 ==========
    
    def discover_plugins(self, plugin_dir: Optional[Path] = None) -> List[PluginMetadata]:
        """发现插件"""
        discovered = []
        
        scan_dirs = [plugin_dir] if plugin_dir else self.plugin_dirs
        
        for plugin_dir in scan_dirs:
            if not plugin_dir.exists():
                continue
            
            sys.path.insert(0, str(plugin_dir.parent))
            
            for (finder, name, is_pkg in pkgutil.iter_modules([str(plugin_dir)]):
                try:
                    if is_pkg:
                        plugin_path = plugin_dir / name
                        spec = importlib.util.spec_from_file_location(
                            name, str(plugin_path / "__init__.py")
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[name] = module
                            spec.loader.exec_module(module)
                            
                            for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and 
                                    issubclass(attr, Plugin) and 
                                    attr != Plugin):
                                    
                                    # 尝试获取插件元数据
                                    try:
                                        # 检查模块级别的 metadata
                                        metadata = None
                                        if hasattr(module, 'metadata'):
                                            metadata = module.metadata
                                        else:
                                            # 创建默认元数据
                                            metadata = PluginMetadata(
                                                id=name,
                                                name=name.replace('_', ' ').title(),
                                                description=f"{name} plugin",
                                                version="1.0.0",
                                                author="Unknown",
                                                type=PluginType.CUSTOM
                                            )
                                        
                                        plugin_info = PluginInfo(
                                            metadata=metadata,
                                            plugin_class=attr,
                                            path=str(plugin_path)
                                        )
                                        
                                        self._plugins[metadata.id] = plugin_info
                                        discovered.append(metadata)
                                        logger.info(f"发现插件: {metadata.name} ({metadata.id})")
                                        
                                    except Exception as e:
                                        logger.error(f"加载插件 {name} 失败: {e}")
                
                except Exception as e:
                    logger.error(f"处理模块 {name} 失败: {e}")
        
        return discovered
    
    # ========== 插件加载 ==========
    
    async def load_plugin(self, plugin_id: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """加载插件"""
        if plugin_id not in self._plugins:
            logger.error(f"插件不存在: {plugin_id}")
            return False
        
        plugin_info = self._plugins[plugin_id]
        
        # 检查依赖
        for dep_id in plugin_info.metadata.dependencies:
            if dep_id not in self._plugins:
                logger.error(f"依赖插件缺失: {dep_id}")
                plugin_info.error_message = f"Missing dependency: {dep_id}"
                return False
        
        try:
            # 实例化插件
            plugin_instance = plugin_info.plugin_class()
            plugin_instance.metadata = plugin_info.metadata
            
            if config:
                plugin_instance.config = PluginConfig(settings=config)
            
            # 初始化插件
            await plugin_instance.initialize()
            plugin_instance.status = PluginStatus.INITIALIZED
            
            # 更新状态
            plugin_info.instance = plugin_instance
            plugin_info.loaded = True
            plugin_info.last_loaded_at = datetime.now().timestamp()
            
            logger.info(f"插件加载成功: {plugin_info.metadata.name}")
            return True
        
        except Exception as e:
            error_msg = f"加载插件失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            plugin_info.error_message = str(e)
            if plugin_info.instance:
                plugin_info.instance.status = PluginStatus.ERROR
            return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self._plugins:
            return False
        
        plugin_info = self._plugins[plugin_id]
        
        if plugin_info.instance:
            try:
                await plugin_info.instance.shutdown()
            except Exception as e:
                logger.error(f"关闭插件 {plugin_id} 失败: {e}")
            
            # 从模块缓存中移除
            module_name = None
            for name, module in sys.modules.items():
                if (hasattr(module, '__file__') and 
                    module.__file__ and 
                    plugin_info.path in str(module.__file__)):
                    module_name = name
                    break
            
            if module_name and module_name in sys.modules:
                del sys.modules[module_name]
        
        plugin_info.instance = None
        plugin_info.loaded = False
        
        logger.info(f"插件已卸载: {plugin_id}")
        return True
    
    async def reload_plugin(self, plugin_id: str) -> bool:
        """重新加载插件"""
        await self.unload_plugin(plugin_id)
        return await self.load_plugin(plugin_id)
    
    # ========== 批量操作 ==========
    
    async def load_all_plugins(self) -> Dict[str, bool]:
        """加载所有插件"""
        results = {}
        
        # 先发现插件
        self.discover_plugins()
        
        # 拓扑排序（按依赖关系）
        sorted_plugin_ids = self._topological_sort()
        
        for plugin_id in sorted_plugin_ids:
            success = await self.load_plugin(plugin_id)
            results[plugin_id] = success
        
        return results
    
    async def unload_all_plugins(self) -> int:
        """卸载所有插件"""
        count = 0
        for plugin_id in list(self._plugins.keys()):
            if await self.unload_plugin(plugin_id):
                count += 1
        return count
    
    def _topological_sort(self) -> List[str]:
        """拓扑排序（按依赖关系）"""
        visited = set()
        order = []
        
        def dfs(plugin_id: str):
            if plugin_id in visited:
                return
            
            visited.add(plugin_id)
            
            if plugin_id in self._plugins:
                for dep in self._plugins[plugin_id].metadata.dependencies:
                    dfs(dep)
            
            order.append(plugin_id)
        
        for plugin_id in self._plugins.keys():
            dfs(plugin_id)
        
        return order
    
    # ========== 插件仓库 ==========
    
    def register_repository(self, repo: PluginRepository) -> None:
        """注册插件仓库"""
        self._repositories[repo.id] = repo
        logger.info(f"注册插件仓库: {repo.name}")
    
    def unregister_repository(self, repo_id: str) -> bool:
        """注销插件仓库"""
        if repo_id in self._repositories:
            del self._repositories[repo_id]
            return True
        return False
    
    # ========== 查询接口 ==========
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件"""
        return self._plugins.get(plugin_id)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInfo]:
        """按类型获取插件"""
        return [
            info for info in self._plugins.values()
            if info.metadata.type == plugin_type
        ]
    
    def list_plugins(
        self,
        loaded_only: bool = False
    ) -> List[PluginInfo]:
        """列出所有插件"""
        plugins = list(self._plugins.values())
        
        if loaded_only:
            plugins = [p for p in plugins if p.loaded]
        
        return sorted(
            plugins,
            key=lambda x: x.metadata.name
        )
    
    # ========== 监控系统 ==========
    
    def check_for_updates(self) -> List[str]:
        """检查插件文件是否有更新"""
        updated = []
        
        for plugin_id, info in self._plugins.items():
            plugin_path = Path(info.path)
            
            if plugin_path.exists():
                mtime = plugin_path.stat().st_mtime
                
                if plugin_id in self._file_mtimes:
                    if self._file_mtimes[plugin_id] < mtime:
                        updated.append(plugin_id)
                        self._file_mtimes[plugin_id] = mtime
                else:
                    self._file_mtimes[plugin_id] = mtime
        
        return updated
    
    async def auto_reload_updates(self) -> List[str]:
        """自动重载更新的插件"""
        updated = self.check_for_updates()
        
        for plugin_id in updated:
            await self.reload_plugin(plugin_id)
        
        return updated
    
    def get_stats(self) -> Dict[str, Any]:
        """获取插件统计"""
        total = len(self._plugins)
        loaded = sum(1 for p in self._plugins.values() if p.loaded)
        error_count = sum(1 for p in self._plugins.values() if p.error_message)
        
        return {
            'total_plugins': total,
            'loaded_plugins': loaded,
            'error_plugins': error_count,
            'repositories': len(self._repositories),
            'by_type': {
                t.value: len([p for p in self._plugins.values() if p.metadata.type == t])
                for t in PluginType
            }
        }


# 全局增强插件管理器
_enhanced_plugin_manager: Optional[EnhancedPluginManager] = None


def get_enhanced_plugin_manager() -> EnhancedPluginManager:
    """获取增强插件管理器"""
    global _enhanced_plugin_manager
    if _enhanced_plugin_manager is None:
        _enhanced_plugin_manager = EnhancedPluginManager()
    return _enhanced_plugin_manager
