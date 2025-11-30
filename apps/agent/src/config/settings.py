"""Application settings using pydantic-settings.

All configuration is loaded from environment variables.
"""

from functools import lru_cache

from pydantic import Field
from pydantic import SecretStr
from pydantic import computed_field
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
        database_host: PostgreSQL host.
        database_port: PostgreSQL port.
        database_user: PostgreSQL user.
        database_password: PostgreSQL password.
        database_name: PostgreSQL database name.
        s3_endpoint: S3/MinIO endpoint URL.
        s3_access_key: S3/MinIO access key.
        s3_secret_key: S3/MinIO secret key.
        s3_bucket_recordings: S3 bucket for recordings.
        s3_region: S3 region.
        egress_output_width: Egress video output width.
        egress_output_height: Egress video output height.
        egress_segment_duration: HLS segment duration in seconds.
        recording_enabled_by_default: Whether recording is enabled by default.
        presigned_url_expiry_seconds: Presigned URL expiry time in seconds.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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

    # Database
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_user: str = Field(default="echosphere")
    database_password: SecretStr = Field(default_factory=lambda: SecretStr("echosphere_dev"))
    database_name: str = Field(default="echosphere")

    # S3/MinIO Configuration
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: SecretStr = Field(default_factory=lambda: SecretStr("minioadmin"))
    s3_bucket_recordings: str = Field(default="echosphere-recordings")
    s3_region: str = Field(default="us-east-1")

    # Egress Configuration
    egress_output_width: int = Field(default=1280)
    egress_output_height: int = Field(default=720)
    egress_segment_duration: int = Field(default=4)

    # Recording Configuration
    recording_enabled_by_default: bool = Field(default=True)
    presigned_url_expiry_seconds: int = Field(default=3600)

    # Logging
    log_level: str = Field(default="INFO")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Build async PostgreSQL connection URL.

        Returns:
            Async PostgreSQL connection URL for SQLAlchemy.
        """
        password = self.database_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.database_user}:{password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings.
    """
    return Settings()
