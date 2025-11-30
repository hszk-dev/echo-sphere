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
        aws_region: AWS region for AI services.
        stt_language: Language for speech-to-text (Amazon Transcribe).
        llm_model: Model ID for LLM (Amazon Bedrock).
        tts_voice: Voice name for text-to-speech (Amazon Polly).
        tts_language: Language for text-to-speech.
        agent_instructions: System prompt for the AI agent.
        agent_greeting_prompt: Prompt for generating agent greeting.
        max_response_tokens: Maximum tokens for LLM response.
        log_level: Logging level.
        database_host: PostgreSQL host.
        database_port: PostgreSQL port.
        database_user: PostgreSQL user.
        database_password: PostgreSQL password.
        database_name: PostgreSQL database name.
        s3_endpoint_url: S3/MinIO endpoint URL (None for AWS S3).
        s3_access_key: S3 access key.
        s3_secret_key: S3 secret key.
        s3_bucket_recordings: S3 bucket for recordings.
        s3_region: S3 region.
        egress_output_width: Egress video output width.
        egress_output_height: Egress video output height.
        egress_segment_duration: HLS segment duration in seconds.
        recording_enabled_by_default: Whether recording is enabled by default.
        presigned_url_expiry_seconds: Presigned URL expiry time in seconds.
        http_host: HTTP server host.
        http_port: HTTP server port.
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

    # AWS Configuration
    aws_region: str = Field(default="ap-northeast-1")

    # AI Models (AWS)
    stt_language: str = Field(
        default="ja-JP",
        description="Language code for Amazon Transcribe STT",
    )
    llm_model: str = Field(
        default="jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
        description="Model ID for Amazon Bedrock LLM",
    )
    tts_voice: str = Field(
        default="Kazuha",
        description="Voice name for Amazon Polly TTS (Japanese neural voice)",
    )
    tts_language: str = Field(
        default="ja-JP",
        description="Language code for Amazon Polly TTS",
    )

    # Agent Behavior
    agent_instructions: str = Field(
        default=(
            "You are a helpful voice AI assistant for EchoSphere. "
            "You assist users with their questions in a friendly and professional manner. "
            "Your responses are concise, clear, and natural for spoken conversation. "
            "You speak Japanese unless the user speaks in another language."
        ),
        description="System prompt for the AI agent",
    )
    agent_greeting_prompt: str = Field(
        default="Greet the user warmly in Japanese and offer your assistance.",
        description="Prompt for generating the agent's initial greeting",
    )
    max_response_tokens: int = Field(
        default=256,
        description="Maximum tokens for LLM response",
    )

    # Database
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_user: str = Field(default="echosphere")
    database_password: SecretStr = Field(default_factory=lambda: SecretStr("echosphere_dev"))
    database_name: str = Field(default="echosphere")

    # S3/MinIO Storage
    s3_endpoint_url: str | None = Field(
        default="http://localhost:9000",
        description="S3/MinIO endpoint URL. Set to None for AWS S3.",
    )
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

    # HTTP Server
    http_host: str = Field(default="0.0.0.0")
    http_port: int = Field(default=8080)

    # Logging
    log_level: str = Field(default="INFO")

    # OpenTelemetry
    otel_enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing",
    )
    otel_service_name: str = Field(
        default="echo-sphere-agent",
        description="Service name for OpenTelemetry",
    )
    otel_exporter_otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="OTLP exporter endpoint URL",
    )

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
