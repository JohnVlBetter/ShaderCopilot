"""
LLM configuration loading from environment.

Provides configuration management for LLM API access.
"""

import logging
import os
import sys
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelSettings(BaseModel):
    """Settings for individual models."""

    router_model: str = "qwen-turbo"
    code_model: str = "qwen-max"
    vl_model: str = "qwen-vl-plus"


class LLMConfig(BaseSettings):
    """
    LLM configuration loaded from environment variables.

    Supports .env file loading via pydantic-settings.
    """

    # API Configuration
    api_base: str = Field(
        default="https://api.openai.com/v1",
        alias="LLM_API_BASE",
    )
    api_key: str = Field(
        default="",
        alias="LLM_API_KEY",
    )

    # Model names
    router_model: str = Field(default="qwen-turbo", alias="ROUTER_MODEL")
    code_model: str = Field(default="qwen-max", alias="CODE_MODEL")
    vl_model: str = Field(default="qwen-vl-plus", alias="VL_MODEL")

    # Generation settings
    code_temperature: float = Field(default=0.2, alias="CODE_TEMPERATURE")
    router_temperature: float = Field(default=0.0, alias="ROUTER_TEMPERATURE")

    # Timeouts
    llm_timeout: int = Field(default=120, alias="LLM_TIMEOUT")
    max_retry_count: int = Field(default=3, alias="MAX_RETRY_COUNT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key and self.api_key != "sk-your-api-key-here")

    def get_model_settings(self) -> ModelSettings:
        """Get model settings as a ModelSettings object."""
        return ModelSettings(
            router_model=self.router_model,
            code_model=self.code_model,
            vl_model=self.vl_model,
        )


class ServerConfig(BaseSettings):
    """WebSocket server configuration."""

    host: str = Field(default="localhost", alias="WEBSOCKET_HOST")
    port: int = Field(default=8765, alias="WEBSOCKET_PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def uri(self) -> str:
        """Get the WebSocket URI."""
        return f"ws://{self.host}:{self.port}"


class LogConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", alias="LOG_LEVEL")
    file: Optional[str] = Field(default=None, alias="LOG_FILE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_llm_config() -> LLMConfig:
    """Get cached LLM configuration."""
    return LLMConfig()


@lru_cache()
def get_server_config() -> ServerConfig:
    """Get cached server configuration."""
    return ServerConfig()


@lru_cache()
def get_log_config() -> LogConfig:
    """Get cached log configuration."""
    return LogConfig()


def reload_config() -> None:
    """Clear config cache to reload from environment."""
    get_llm_config.cache_clear()
    get_server_config.cache_clear()
    get_log_config.cache_clear()


def setup_logging(config: Optional[LogConfig] = None) -> None:
    """
    Configure logging for the application.

    Args:
        config: Optional log configuration. If None, loads from environment.
    """
    if config is None:
        config = get_log_config()

    # Parse log level
    level = getattr(logging, config.level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if configured
    if config.file:
        try:
            file_handler = logging.FileHandler(config.file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except IOError as e:
            logging.warning(f"Could not create log file {config.file}: {e}")

    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    logging.info(f"Logging configured at level {config.level}")
