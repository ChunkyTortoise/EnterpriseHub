"""
Environment Variable Configuration for EnterpriseHub Products.

This module provides Pydantic Settings base classes for configuration
management across all products. Each product should create its own
settings class inheriting from ProductSettings.

Environment Variable Pattern:
    {PRODUCT}_DATABASE_URL   - PostgreSQL connection string
    {PRODUCT}_REDIS_URL      - Redis connection string
    {PRODUCT}_STRIPE_API_KEY - Stripe secret key
    {PRODUCT}_STRIPE_METER_ID - Stripe meter ID for billing
    {PRODUCT}_LOG_LEVEL      - Logging level (DEBUG, INFO, WARNING, ERROR)
    {PRODUCT}_SENTRY_DSN     - Sentry error tracking DSN

Example:
    # For Jorge product
    class JorgeSettings(ProductSettings):
        model_config = SettingsConfigDict(env_prefix="JORGE_")

        # Product-specific settings
        openai_api_key: str
        claude_api_key: str

    settings = JorgeSettings()
    # Reads from JORGE_DATABASE_URL, JORGE_REDIS_URL, etc.
"""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings
from pydantic_settings import SettingsConfigDict


class LogLevel(str, Enum):
    """Supported logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Deployment environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class BaseSettings(PydanticBaseSettings):
    """
    Base settings class with common configuration for all products.

    Provides shared configuration fields and validation that apply
    across all EnterpriseHub products.

    Attributes:
        environment: Current deployment environment.
        log_level: Logging verbosity level.
        debug: Enable debug mode (inferred from environment).

    Example:
        class MySettings(BaseSettings):
            my_setting: str

            model_config = SettingsConfigDict(
                env_prefix="MY_",
                env_file=".env",
                env_file_encoding="utf-8",
            )
    """

    # Environment configuration
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Current deployment environment")
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging verbosity level")

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.environment in (Environment.DEVELOPMENT, Environment.TESTING)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class ProductSettings(BaseSettings):
    """
    Product-specific settings with standard infrastructure configuration.

    Provides the standard set of infrastructure environment variables
    that all products need. Each product should inherit from this class
    and add product-specific settings.

    Environment Variables (with {PRODUCT} prefix):
        {PRODUCT}_DATABASE_URL: PostgreSQL connection string
            Example: postgresql+asyncpg://user:pass@host:5432/db

        {PRODUCT}_REDIS_URL: Redis connection string
            Example: redis://localhost:6379/0

        {PRODUCT}_STRIPE_API_KEY: Stripe secret key for billing
            Example: sk_live_xxx or sk_test_xxx

        {PRODUCT}_STRIPE_METER_ID: Stripe meter ID for usage billing
            Example: meter_xxx

        {PRODUCT}_LOG_LEVEL: Logging level
            Example: INFO, DEBUG, WARNING

        {PRODUCT}_SENTRY_DSN: Sentry error tracking DSN
            Example: https://xxx@sentry.io/xxx

    Example:
        class JorgeSettings(ProductSettings):
            model_config = SettingsConfigDict(env_prefix="JORGE_")

            # Product-specific
            openai_api_key: str
            claude_api_key: str
            ghl_api_key: str

        # Usage
        settings = JorgeSettings()
        print(settings.database_url)  # Reads from JORGE_DATABASE_URL
    """

    # Database configuration
    database_url: str = Field(..., description="PostgreSQL connection string (asyncpg driver)")

    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection string")

    # Stripe configuration
    stripe_api_key: Optional[str] = Field(default=None, description="Stripe secret key for billing")
    stripe_meter_id: Optional[str] = Field(default=None, description="Stripe meter ID for usage billing")

    # Error tracking
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses async driver."""
        if v.startswith("postgresql://"):
            # Convert to async driver
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not v.startswith("postgresql+asyncpg://"):
            raise ValueError(f"Database URL must use postgresql+asyncpg:// driver, got: {v[:30]}...")
        return v

    @field_validator("stripe_api_key")
    @classmethod
    def validate_stripe_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate Stripe key format if provided."""
        if v is None:
            return v
        if not (v.startswith("sk_live_") or v.startswith("sk_test_")):
            raise ValueError("Stripe API key must start with 'sk_live_' or 'sk_test_'")
        return v

    @property
    def stripe_is_live(self) -> bool:
        """Check if using live Stripe key."""
        if self.stripe_api_key is None:
            return False
        return self.stripe_api_key.startswith("sk_live_")

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic migrations)."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache()
def get_settings(settings_class: type[ProductSettings]) -> ProductSettings:
    """
    Get cached settings instance for a product.

    Uses LRU cache to ensure settings are only loaded once per process.

    Args:
        settings_class: The settings class to instantiate.

    Returns:
        Cached instance of the settings class.

    Example:
        class JorgeSettings(ProductSettings):
            model_config = SettingsConfigDict(env_prefix="JORGE_")
            openai_api_key: str

        settings = get_settings(JorgeSettings)
    """
    return settings_class()


def clear_settings_cache() -> None:
    """Clear the settings cache (useful for testing)."""
    get_settings.cache_clear()


# Pre-defined settings for common products
class JorgeSettings(ProductSettings):
    """Settings for Jorge (Real Estate AI Bots) product."""

    model_config = SettingsConfigDict(env_prefix="JORGE_")

    # AI Provider Keys
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # GoHighLevel Integration
    ghl_api_key: Optional[str] = None
    ghl_location_id: Optional[str] = None


class ContraSettings(ProductSettings):
    """Settings for Contra (Contractor Marketplace) product."""

    model_config = SettingsConfigDict(env_prefix="CONTRA_")


class CertificationSettings(ProductSettings):
    """Settings for Certification Platform product."""

    model_config = SettingsConfigDict(env_prefix="CERTIFICATION_")
