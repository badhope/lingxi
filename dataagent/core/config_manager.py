"""
DataAgent - 增强配置管理器
支持多种配置格式、环境变量、热重载等功能
"""
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from core.logging import get_logger

logger = get_logger("config_manager")


class ConfigSource(Enum):
    """配置来源"""
    DEFAULT = "default"
    FILE = "file"
    ENVIRONMENT = "environment"
    DATABASE = "database"
    REMOTE = "remote"


@dataclass
class ConfigOption:
    """配置选项"""
    key: str
    value: Any
    description: str = ""
    source: ConfigSource = ConfigSource.DEFAULT
    required: bool = False
    validator: Optional[Any] = None
    default: Optional[Any] = None
    type_hint: Optional[str] = None


class EnhancedConfigManager:
    """
    增强配置管理器
    支持多种格式、环境变量、热重载、验证等
    """
    
    def __init__(
        self,
        config_dir: Optional[Path] = None,
        auto_reload: bool = True
    ):
        if config_dir is None:
            # 优先使用环境变量，其次使用项目目录，最后使用用户目录
            env_config_dir = os.getenv("DATAAGENT_CONFIG_DIR")
            if env_config_dir:
                config_dir = Path(env_config_dir)
            else:
                # 使用项目目录下的 .dataagent 文件夹，容器兼容性更好
                try:
                    config_dir = Path(__file__).parent.parent / ".dataagent"
                except:
                    config_dir = Path.home() / ".dataagent"
        
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.auto_reload = auto_reload
        
        # 配置存储
        self._configs: Dict[str, ConfigOption] = {}
        self._file_mtimes: Dict[str, float] = {}
        
        # 加载默认配置
        self._load_default_configs()
        
        logger.info("增强配置管理器初始化完成")
    
    def _load_default_configs(self):
        """加载默认配置"""
        # 使用相对路径或基于 config_dir 的路径，容器兼容性更好
        defaults = {
            # 服务配置
            "server.host": "0.0.0.0",
            "server.port": 8000,
            "server.debug": False,
            "server.https": False,
            
            # LLM 配置
            "llm.provider": "openai",
            "llm.api_key": "",
            "llm.api_base": "",
            "llm.model": "gpt-4",
            "llm.temperature": 0.7,
            "llm.max_tokens": 4096,
            "llm.max_retries": 3,
            "llm.timeout": 60,
            
            # 安全配置
            "security.secret_key": "",
            "security.auth_enabled": True,
            "security.rate_limit_enabled": True,
            "security.rate_limit_max": 100,
            "security.rate_limit_window": 60,
            
            # 数据库配置
            "database.type": "sqlite",
            "database.path": str(self.config_dir / "data.db"),
            "database.host": "",
            "database.port": 5432,
            "database.name": "",
            "database.user": "",
            "database.password": "",
            
            # 缓存配置
            "cache.enabled": True,
            "cache.default_ttl": 3600,
            "cache.use_file_cache": True,
            "cache.memory_cache_max": 1000,
            
            # 日志配置
            "logging.level": "INFO",
            "logging.file_path": str(self.config_dir / "logs"),
            "logging.max_size_mb": 10,
            "logging.backup_count": 5,
            "logging.console": True,
            
            # 工作流配置
            "workflows.enabled": True,
            "workflows.max_steps": 100,
            "workflows.timeout": 3600,
            
            # 插件配置
            "plugins.auto_load": True,
            "plugins.directory": str(self.config_dir / "plugins"),
            "plugins.auto_reload": False,
        }
        
        for key, value in defaults.items():
            self._configs[key] = ConfigOption(
                key=key,
                value=value,
                default=value,
                source=ConfigSource.DEFAULT,
                type_hint=str(type(value).__name__)
            )
        
        # 加载文件配置
        self._load_file_configs()
        
        # 加载环境变量
        self._load_env_configs()
    
    def _load_file_configs(self):
        """加载文件配置"""
        config_files = [
            self.config_dir / "config.json",
            self.config_dir / "settings.json",
            self.config_dir / "dataagent.json"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    self._update_from_dict(config_data, ConfigSource.FILE)
                    self._file_mtimes[str(config_file)] = config_file.stat().st_mtime
                    
                    logger.info(f"加载配置文件: {config_file}")
                    
                except Exception as e:
                    logger.error(f"读取配置文件 {config_file} 失败: {e}")
    
    def _load_env_configs(self):
        """从环境变量加载配置"""
        for key, value in os.environ.items():
            if key.startswith("DATAAGENT_"):
                # 转换环境变量到配置键
                config_key = key[10:].lower().replace("__", ".")
                
                # 尝试解析类型
                try:
                    if value.lower() in ("true", "false"):
                        parsed_value = value.lower() == "true"
                    elif value.replace(".", "").isdigit():
                        if "." in value:
                            parsed_value = float(value)
                        else:
                            parsed_value = int(value)
                    else:
                        parsed_value = value
                    
                    self._configs[config_key] = ConfigOption(
                        key=config_key,
                        value=parsed_value,
                        source=ConfigSource.ENVIRONMENT,
                        type_hint=str(type(parsed_value).__name__)
                    )
                    
                except Exception as e:
                    logger.warning(f"解析环境变量 {key} 失败: {e}")
    
    def _update_from_dict(self, config_data: Dict[str, Any], source: ConfigSource, prefix: str = ""):
        """从字典更新配置"""
        for key, value in config_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._update_from_dict(value, source, full_key)
            else:
                self._configs[full_key] = ConfigOption(
                    key=full_key,
                    value=value,
                    source=source,
                    type_hint=str(type(value).__name__)
                )
    
    # ========== 获取配置 ==========
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        if key in self._configs:
            return self._configs[key].value
        return default
    
    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串配置"""
        value = self.get(key, default)
        return str(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        try:
            value = self.get(key, default)
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        try:
            value = self.get(key, default)
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置"""
        value = self.get(key, default)
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)
    
    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """获取列表配置"""
        value = self.get(key, default or [])
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return [v.strip() for v in value.split(",") if v.strip()]
        return list(value) if value else []
    
    # ========== 设置配置 ==========
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.DEFAULT, save: bool = True):
        """设置配置"""
        self._configs[key] = ConfigOption(
            key=key,
            value=value,
            source=source,
            type_hint=str(type(value).__name__)
        )
        
        if save and source != ConfigSource.ENVIRONMENT:
            self._save_to_file()
        
        logger.debug(f"设置配置: {key} = {value}")
    
    # ========== 保存/加载 ==========
    
    def _save_to_file(self, file_path: Optional[Path] = None):
        """保存到文件"""
        if file_path is None:
            file_path = self.config_dir / "config.json"
        
        # 构建要保存的配置（只保存非默认值或来自文件的配置）
        to_save = {}
        
        for key, option in self._configs.items():
            if (option.source != ConfigSource.DEFAULT or 
                (option.value != option.default and option.default is not None)):
                parts = key.split(".")
                current = to_save
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = option.value
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(to_save, f, ensure_ascii=False, indent=2)
            
            self._file_mtimes[str(file_path)] = time.time()
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
    
    def save(self, file_path: Optional[Path] = None):
        """保存配置"""
        self._save_to_file(file_path)
        logger.info("配置已保存")
    
    # ========== 验证和检查 ==========
    
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        return key in self._configs
    
    def list_configs(self, prefix: Optional[str] = None) -> List[ConfigOption]:
        """列出配置"""
        configs = list(self._configs.values())
        
        if prefix:
            configs = [c for c in configs if c.key.startswith(prefix)]
        
        return sorted(configs, key=lambda x: x.key)
    
    def export_dict(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """导出配置字典"""
        result = {}
        
        for key, option in self._configs.items():
            if prefix and not key.startswith(prefix):
                continue
            
            parts = key.split(".")
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = option.value
        
        return result
    
    # ========== 热重载 ==========
    
    def check_for_updates(self) -> List[str]:
        """检查配置文件是否有更新"""
        updated = []
        
        for file_path, mtime in self._file_mtimes.items():
            path = Path(file_path)
            if path.exists():
                new_mtime = path.stat().st_mtime
                if new_mtime > mtime:
                    updated.append(file_path)
                    self._file_mtimes[file_path] = new_mtime
        
        return updated
    
    def reload(self):
        """重新加载配置"""
        logger.info("重新加载配置...")
        
        self._file_mtimes.clear()
        self._load_file_configs()
        self._load_env_configs()
        
        logger.info("配置已重新加载")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取配置统计"""
        counts = {}
        for option in self._configs.values():
            source = option.source.value
            counts[source] = counts.get(source, 0) + 1
        
        return {
            'total_configs': len(self._configs),
            'by_source': counts
        }


# 全局配置管理器
_enhanced_config_manager: Optional[EnhancedConfigManager] = None


def get_enhanced_config_manager() -> EnhancedConfigManager:
    """获取增强配置管理器"""
    global _enhanced_config_manager
    if _enhanced_config_manager is None:
        _enhanced_config_manager = EnhancedConfigManager()
    return _enhanced_config_manager
