"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Voice AI Platform settings loaded from environment variables."""

    # Application
    app_name: str = "Voice AI Platform"
    debug: bool = False
    base_url: str = "localhost:8000"

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/voice_ai",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Deepgram STT
    deepgram_api_key: str = Field(default="", alias="DEEPGRAM_API_KEY")

    # ElevenLabs TTS
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    elevenlabs_default_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM", alias="ELEVENLABS_DEFAULT_VOICE_ID"
    )

    # Twilio
    twilio_account_sid: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", alias="TWILIO_PHONE_NUMBER")

    # Stripe
    stripe_api_key: str = Field(default="", alias="STRIPE_SECRET_KEY")

    # LLM
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    llm_model: str = "claude-sonnet-4-5-20250929"

    # Pipeline
    stt_endpointing_ms: int = 300
    tts_model: str = "eleven_flash_v2_5"
    vad_silence_threshold_ms: int = 1000

    # Billing rates (per minute)
    rate_payg: float = 0.20
    rate_growth: float = 0.15
    rate_enterprise: float = 0.12
    rate_whitelabel: float = 0.10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
