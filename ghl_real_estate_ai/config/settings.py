"""
EnterpriseHub Settings

Configuration settings for the GHL Real Estate AI platform.
"""

import os
from typing import Optional


class Settings:
    """Application settings"""

    # Claude AI Configuration
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    claude_max_tokens: int = int(os.getenv("CLAUDE_MAX_TOKENS", "1000"))
    claude_temperature: float = float(os.getenv("CLAUDE_TEMPERATURE", "0.7"))

    # GoHighLevel Configuration
    ghl_api_key: str = os.getenv("GHL_API_KEY", "")
    ghl_location_id: str = os.getenv("GHL_LOCATION_ID", "")
    ghl_webhook_secret: str = os.getenv("GHL_WEBHOOK_SECRET", "")

    # Redis Configuration
    redis_url: Optional[str] = os.getenv("REDIS_URL")
    redis_max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "20"))
    redis_retry_attempts: int = int(os.getenv("REDIS_RETRY_ATTEMPTS", "3"))
    redis_default_ttl: int = int(os.getenv("REDIS_DEFAULT_TTL", "3600"))

    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost:5432/enterprisehub")
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))

    # Application Configuration
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Performance Configuration
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "100"))

    # ML Model Configuration
    ml_model_cache_ttl: int = int(os.getenv("ML_MODEL_CACHE_TTL", "7200"))  # 2 hours
    ml_inference_timeout: int = int(os.getenv("ML_INFERENCE_TIMEOUT", "10"))  # 10 seconds

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()