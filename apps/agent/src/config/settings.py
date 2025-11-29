"""Application settings using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Name of the application.
        debug: Enable debug mode.
        livekit_url: LiveKit server URL.
        livekit_api_key: LiveKit API key.
        livekit_api_secret: LiveKit API secret.
        openai_api_key: OpenAI API key.
        log_level: Logging level.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "echo-sphere-agent"
    debug: bool = False

    # LiveKit
    livekit_url: str = Field(default="ws://localhost:7880")
    livekit_api_key: str = Field(default="devkey")
    livekit_api_secret: SecretStr = Field(default_factory=lambda: SecretStr("secret"))

    # OpenAI
    openai_api_key: SecretStr = Field(default_factory=lambda: SecretStr(""))

    # Logging
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings.
    """
    return Settings()
