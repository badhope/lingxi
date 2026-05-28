"""
DATA-Agent 配置管理
基于 CrewAI 的智能数据助手
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""
    
    # App
    app_name: str = "DATA-Agent"
    app_version: str = "2.0.0"
    debug: bool = True
    
    # LLM 配置
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4-turbo"
    default_temperature: float = 0.7
    
    # 路径配置
    base_dir: Path = Path(__file__).parent
    data_dir: Path = Path("./data")
    config_dir: Path = Path("./config")
    
    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 日志配置
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
