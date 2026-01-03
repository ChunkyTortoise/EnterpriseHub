"""
Configuration module for GHL Real Estate AI.

Manages environment variables and application settings using Pydantic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Centralized application settings with environment variable support.

    All sensitive values (API keys, database URLs) are loaded from environment
    variables or .env file. Never hardcode secrets in this file.
    """

    # API Keys (Required)
    anthropic_api_key: str = "placeholder_key"
    ghl_api_key: str = "placeholder_key"
    ghl_location_id: str = "placeholder_id"

    # LLM Configuration
    claude_model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 500
    default_llm_provider: str = "claude"
    gemini_model: Optional[str] = None
    google_api_key: Optional[str] = None

    # Database Configuration
    database_url: Optional[str] = None  # PostgreSQL (Railway auto-provides)
    redis_url: Optional[str] = None  # Redis for session state

    # Vector Database
    chroma_persist_directory: str = "./data/embeddings/chroma_db"
    chroma_collection_name: str = "real_estate_kb"

    # Application Settings
    environment: str = "development"  # development, production
    log_level: str = "INFO"
    app_name: str = "GHL Real Estate AI"
    version: str = "1.0.0"

    # Default Agent Information
    default_agent_name: str = "Sarah Johnson"
    default_agent_phone: str = "+15125551234"
    default_agent_email: str = "agent@example.com"

    # Lead Scoring Thresholds (0-100 scale)
    hot_lead_threshold: int = 70
    warm_lead_threshold: int = 40
    cold_lead_threshold: int = 0

    # Performance Settings
    webhook_timeout_seconds: int = 3
    max_conversation_history_length: int = 20
    rag_top_k_results: int = 3

    # Security
    ghl_webhook_secret: Optional[str] = None  # For signature verification

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


# Global settings instance
# This will be imported throughout the application
settings = Settings()
