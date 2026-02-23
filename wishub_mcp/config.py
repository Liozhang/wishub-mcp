"""
WisHub MCP Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "wishub-mcp"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # 认证配置
    AUTH_REQUIRED: bool = True
    AUTH_HEADER: str = "X-API-Key"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # WisHub Core 配置
    WISHUB_CORE_URL: str = "http://localhost:8000"
    WISHUB_CORE_TIMEOUT: int = 30

    # AI 模型配置
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
