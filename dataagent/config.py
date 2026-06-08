"""pydantic-settings root config.

Reads from environment variables (and `.env` if present). Used by main.py / cli.py.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = "data-agent"
    app_version: str = "0.1.0"
    debug: bool = True

    # LLM
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4-turbo"
    default_temperature: float = 0.7

    # Paths
    base_dir: Path = Path(__file__).parent
    data_dir: Path = Path("./data")
    config_dir: Path = Path("./config")

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
