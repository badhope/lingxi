"""
DataAgent - Unified Configuration System
统一配置管理模块，整合所有配置功能
"""
import json
import os
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

# Load environment variables
dotenv_path = Path(__file__).parent.parent.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)


# ==================== Path Configuration ====================
class PathConfig(BaseModel):
    """路径配置"""
    base_dir: Path
    config_dir: Path
    data_dir: Path
    knowledge_dir: Path
    skills_dir: Path
    databases_dir: Path
    output_dir: Path
    
    @classmethod
    def create(cls) -> 'PathConfig':
        base_dir = Path(__file__).parent.parent
        config_dir = base_dir / "config"
        data_dir = base_dir / "data"
        knowledge_dir = data_dir / "knowledge_bases"
        skills_dir = data_dir / "skills"
        databases_dir = data_dir / "databases"
        output_dir = base_dir / "output"
        
        # Create directories if they don't exist
        for dir_path in [config_dir, data_dir, knowledge_dir, skills_dir, databases_dir, output_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return cls(
            base_dir=base_dir,
            config_dir=config_dir,
            data_dir=data_dir,
            knowledge_dir=knowledge_dir,
            skills_dir=skills_dir,
            databases_dir=databases_dir,
            output_dir=output_dir
        )


# ==================== LLM Configuration ====================
class LLMSettings(BaseModel):
    """LLM 配置"""
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    max_input_tokens: Optional[int] = Field(
        None,
        description="Maximum input tokens to use across all requests (None for unlimited)",
    )
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field("openai", description="Azure, Openai, or Ollama")
    api_version: Optional[str] = Field(None, description="Azure Openai version if AzureOpenai")
    provider: str = Field("openai", description="LLM provider name")


# ==================== Security Configuration ====================
class SecuritySettings(BaseModel):
    """安全配置"""
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:8000"])
    rate_limit_max_requests: int = Field(60, description="Max requests per window")
    rate_limit_window: int = Field(60, description="Window in seconds")
    max_file_size_mb: int = Field(10, description="Maximum file upload size")
    allowed_file_extensions: List[str] = Field(
        default_factory=lambda: [".txt", ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".csv", ".json", ".md"]
    )


# ==================== Proxy Configuration ====================
class ProxySettings(BaseModel):
    """代理配置"""
    server: Optional[str] = Field(None, description="Proxy server address")
    username: Optional[str] = Field(None, description="Proxy username")
    password: Optional[str] = Field(None, description="Proxy password")


# ==================== Search Configuration ====================
class SearchSettings(BaseModel):
    """搜索配置"""
    engine: str = Field(default="Google", description="Search engine the llm to use")
    fallback_engines: List[str] = Field(
        default_factory=lambda: ["DuckDuckGo", "Baidu", "Bing"],
        description="Fallback search engines to try if the primary engine fails",
    )
    retry_delay: int = Field(
        default=60,
        description="Seconds to wait before retrying all engines again after they all fail",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of times to retry all engines when all fail",
    )
    lang: str = Field(
        default="en",
        description="Language code for search results (e.g., en, zh, fr)",
    )
    country: str = Field(
        default="us",
        description="Country code for search results (e.g., us, cn, uk)",
    )


# ==================== Browser Configuration ====================
class BrowserSettings(BaseModel):
    """浏览器配置"""
    headless: bool = Field(True, description="Whether to run browser in headless mode")
    disable_security: bool = Field(
        True, description="Disable browser security features"
    )
    extra_chromium_args: List[str] = Field(
        default_factory=list, description="Extra arguments to pass to the browser"
    )
    chrome_instance_path: Optional[str] = Field(
        None, description="Path to a Chrome instance to use"
    )
    wss_url: Optional[str] = Field(
        None, description="Connect to a browser instance via WebSocket"
    )
    cdp_url: Optional[str] = Field(
        None, description="Connect to a browser instance via CDP"
    )
    proxy: Optional[ProxySettings] = Field(
        None, description="Proxy settings for the browser"
    )
    max_content_length: int = Field(
        2000, description="Maximum length for content retrieval operations"
    )


# ==================== Sandbox Configuration ====================
class SandboxSettings(BaseModel):
    """沙箱配置"""
    use_sandbox: bool = Field(False, description="Whether to use the sandbox")
    image: str = Field("python:3.12-slim", description="Base image")
    work_dir: str = Field("/workspace", description="Container working directory")
    memory_limit: str = Field("512m", description="Memory limit")
    cpu_limit: float = Field(1.0, description="CPU limit")
    timeout: int = Field(300, description="Default command timeout (seconds)")
    network_enabled: bool = Field(
        False, description="Whether network access is allowed"
    )


# ==================== Daytona Configuration ====================
class DaytonaSettings(BaseModel):
    """Daytona 配置"""
    daytona_api_key: Optional[str] = Field(None, description="Daytona API key")
    daytona_server_url: Optional[str] = Field(
        "https://app.daytona.io/api", description="Daytona server URL"
    )
    daytona_target: Optional[str] = Field("us", description="Target region ['eu', 'us']")
    sandbox_image_name: Optional[str] = Field("whitezxj/sandbox:0.1.0", description="Sandbox image")
    sandbox_entrypoint: Optional[str] = Field(
        "/usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf",
        description="Sandbox entrypoint command"
    )
    vnc_password: Optional[str] = Field(
        "123456", description="VNC password for the vnc service in sandbox"
    )


# ==================== MCP Configuration ====================
class MCPServerConfig(BaseModel):
    """单个 MCP 服务器配置"""
    type: str = Field(..., description="Server connection type (sse or stdio)")
    url: Optional[str] = Field(None, description="Server URL for SSE connections")
    command: Optional[str] = Field(None, description="Command for stdio connections")
    args: List[str] = Field(
        default_factory=list, description="Arguments for stdio command"
    )
    enabled: bool = Field(True, description="Whether this server is enabled")
    name: str = Field("MCP Server", description="Server display name")
    icon: str = Field("🔌", description="Server icon")


class MCPSettings(BaseModel):
    """MCP 配置"""
    server_reference: str = Field(
        "app.mcp.server", description="Module reference for the MCP server"
    )
    servers: Dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )


# ==================== Runflow Configuration ====================
class RunflowSettings(BaseModel):
    """运行流程配置"""
    use_data_analysis_agent: bool = Field(
        default=False, description="Enable data analysis agent in run flow"
    )


# ==================== Logging Configuration ====================
class LoggingSettings(BaseModel):
    """日志配置"""
    level: str = Field("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    format: str = Field(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        description="Log format string"
    )
    file_path: Optional[str] = Field(None, description="Log file path (None for console only)")
    max_file_size_mb: int = Field(10, description="Max log file size before rotation")
    backup_count: int = Field(5, description="Number of backup log files to keep")


# ==================== Main Configuration Model ====================
class AppConfig(BaseModel):
    """应用主配置"""
    paths: PathConfig
    llm: Dict[str, LLMSettings]
    security: SecuritySettings
    search: Optional[SearchSettings] = None
    browser: Optional[BrowserSettings] = None
    sandbox: SandboxSettings
    daytona: DaytonaSettings
    mcp: MCPSettings
    runflow: RunflowSettings
    logging: LoggingSettings


# ==================== Singleton Configuration Manager ====================
class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config: Optional[AppConfig] = None
                    self._load_config()
                    self._initialized = True
    
    def _load_config(self):
        """加载配置"""
        paths = PathConfig.create()
        
        # Load TOML config
        toml_config = self._load_toml_config(paths.config_dir)
        
        # Load environment variables
        env_config = self._load_env_config()
        
        # Merge configurations
        self._config = self._merge_configs(paths, toml_config, env_config)
    
    def _load_toml_config(self, config_dir: Path) -> dict:
        """加载 TOML 配置文件"""
        config_path = config_dir / "config.toml"
        example_path = config_dir / "config.example.toml"
        
        if config_path.exists():
            with config_path.open("rb") as f:
                return tomllib.load(f)
        elif example_path.exists():
            with example_path.open("rb") as f:
                return tomllib.load(f)
        return {}
    
    def _load_env_config(self) -> dict:
        """加载环境变量配置"""
        return {
            "api_key": os.getenv("API_KEY"),
            "api_base_url": os.getenv("API_BASE_URL"),
            "api_model": os.getenv("API_MODEL"),
            "cors_origins": os.getenv("CORS_ALLOWED_ORIGINS"),
            "max_file_size_mb": os.getenv("MAX_FILE_SIZE_MB"),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }
    
    def _merge_configs(self, paths: PathConfig, toml_data: dict, env_data: dict) -> AppConfig:
        """合并所有配置来源"""
        # LLM Configuration
        llm_base = toml_data.get("llm", {})
        
        # Use environment variables if available
        if env_data.get("api_key"):
            llm_base["api_key"] = env_data["api_key"]
        if env_data.get("api_base_url"):
            llm_base["base_url"] = env_data["api_base_url"]
        if env_data.get("api_model"):
            llm_base["model"] = env_data["api_model"]
        
        llm_overrides = {
            k: v for k, v in toml_data.get("llm", {}).items() if isinstance(v, dict)
        }
        
        default_llm_settings = {
            "model": llm_base.get("model", "gpt-4o"),
            "base_url": llm_base.get("base_url", "https://api.openai.com/v1"),
            "api_key": llm_base.get("api_key", ""),
            "max_tokens": llm_base.get("max_tokens", 4096),
            "max_input_tokens": llm_base.get("max_input_tokens"),
            "temperature": llm_base.get("temperature", 1.0),
            "api_type": llm_base.get("api_type", "openai"),
            "api_version": llm_base.get("api_version"),
            "provider": llm_base.get("provider", "openai"),
        }
        
        llm_config = {
            "default": default_llm_settings,
            **{
                name: {**default_llm_settings, **override}
                for name, override in llm_overrides.items()
            },
        }
        
        # Security Configuration
        cors_origins = env_data.get("cors_origins")
        if cors_origins:
            cors_list = [o.strip() for o in cors_origins.split(",")]
        else:
            cors_list = ["http://localhost:8000", "http://127.0.0.1:8000"]
        
        security_settings = SecuritySettings(
            cors_origins=cors_list,
            rate_limit_max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", 60)),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", 60)),
            max_file_size_mb=int(env_data.get("max_file_size_mb", 10)),
        )
        
        # Search Configuration
        search_config = toml_data.get("search")
        search_settings = SearchSettings(**search_config) if search_config else None
        
        # Browser Configuration
        browser_config = toml_data.get("browser", {})
        browser_settings = self._parse_browser_settings(browser_config)
        
        # Sandbox Configuration
        sandbox_config = toml_data.get("sandbox", {})
        sandbox_settings = SandboxSettings(**sandbox_config)
        
        # Daytona Configuration
        daytona_config = toml_data.get("daytona", {})
        daytona_settings = DaytonaSettings(**daytona_config)
        
        # MCP Configuration
        mcp_config = toml_data.get("mcp", {})
        mcp_settings = self._parse_mcp_settings(paths.config_dir, mcp_config)
        
        # Runflow Configuration
        runflow_config = toml_data.get("runflow", {})
        runflow_settings = RunflowSettings(**runflow_config)
        
        # Logging Configuration
        logging_settings = LoggingSettings(
            level=env_data.get("log_level", "INFO"),
        )
        
        return AppConfig(
            paths=paths,
            llm=llm_config,
            security=security_settings,
            search=search_settings,
            browser=browser_settings,
            sandbox=sandbox_settings,
            daytona=daytona_settings,
            mcp=mcp_settings,
            runflow=runflow_settings,
            logging=logging_settings,
        )
    
    def _parse_browser_settings(self, browser_config: dict) -> Optional[BrowserSettings]:
        """解析浏览器配置"""
        if not browser_config:
            return None
        
        proxy_config = browser_config.get("proxy", {})
        proxy_settings = None
        
        if proxy_config and proxy_config.get("server"):
            proxy_settings = ProxySettings(
                server=proxy_config.get("server"),
                username=proxy_config.get("username"),
                password=proxy_config.get("password"),
            )
        
        valid_params = {
            k: v for k, v in browser_config.items()
            if k in BrowserSettings.__annotations__ and v is not None
        }
        
        if proxy_settings:
            valid_params["proxy"] = proxy_settings
        
        return BrowserSettings(**valid_params)
    
    def _parse_mcp_settings(self, config_dir: Path, mcp_config: dict) -> MCPSettings:
        """解析 MCP 配置"""
        servers = self._load_mcp_servers(config_dir)
        
        return MCPSettings(
            server_reference=mcp_config.get("server_reference", "app.mcp.server"),
            servers=servers,
        )
    
    def _load_mcp_servers(self, config_dir: Path) -> Dict[str, MCPServerConfig]:
        """加载 MCP 服务器配置"""
        mcp_json_path = config_dir / "mcp.json"
        
        if not mcp_json_path.exists():
            return {}
        
        try:
            with mcp_json_path.open() as f:
                data = json.load(f)
                servers = {}
                
                for server_id, server_config in data.get("mcpServers", {}).items():
                    servers[server_id] = MCPServerConfig(
                        type=server_config.get("type", "stdio"),
                        url=server_config.get("url"),
                        command=server_config.get("command"),
                        args=server_config.get("args", []),
                        enabled=server_config.get("enabled", True),
                        name=server_config.get("name", f"MCP Server {server_id}"),
                        icon=server_config.get("icon", "🔌"),
                    )
                return servers
        except Exception:
            return {}
    
    def reload(self):
        """重新加载配置"""
        self._initialized = False
        self._config = None
        self.__init__()
    
    @property
    def config(self) -> AppConfig:
        """获取配置"""
        return self._config
    
    # Convenience properties
    @property
    def paths(self) -> PathConfig:
        return self._config.paths
    
    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm
    
    @property
    def security(self) -> SecuritySettings:
        return self._config.security
    
    @property
    def search(self) -> Optional[SearchSettings]:
        return self._config.search
    
    @property
    def browser(self) -> Optional[BrowserSettings]:
        return self._config.browser
    
    @property
    def sandbox(self) -> SandboxSettings:
        return self._config.sandbox
    
    @property
    def daytona(self) -> DaytonaSettings:
        return self._config.daytona
    
    @property
    def mcp(self) -> MCPSettings:
        return self._config.mcp
    
    @property
    def runflow(self) -> RunflowSettings:
        return self._config.runflow
    
    @property
    def logging(self) -> LoggingSettings:
        return self._config.logging


# Global configuration instance
config_manager = ConfigManager()
