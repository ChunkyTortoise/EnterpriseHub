"""Unified configuration for the AI DevOps Suite."""

from __future__ import annotations

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings


class Tier(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    TEAM = "team"


TIER_LIMITS: dict[str, dict] = {
    Tier.STARTER: {
        "agents": 5,
        "pipelines": 3,
        "prompts": 50,
        "events_per_day": 10_000,
        "pipeline_runs_per_day": 50,
        "prompt_renders_per_day": 500,
        "retention_days": 7,
    },
    Tier.PRO: {
        "agents": 25,
        "pipelines": 15,
        "prompts": 500,
        "events_per_day": 100_000,
        "pipeline_runs_per_day": 500,
        "prompt_renders_per_day": 5_000,
        "retention_days": 30,
    },
    Tier.TEAM: {
        "agents": None,  # Unlimited
        "pipelines": None,
        "prompts": None,
        "events_per_day": 1_000_000,
        "pipeline_runs_per_day": None,
        "prompt_renders_per_day": None,
        "retention_days": 90,
    },
}

STRIPE_PRODUCTS: dict[str, dict] = {
    "starter": {"price_id": "price_starter_monthly", "amount": 4900},
    "pro": {"price_id": "price_pro_monthly", "amount": 9900},
    "team": {"price_id": "price_team_monthly", "amount": 19900},
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "AI DevOps Suite"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/devops_suite"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Stripe
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Feature flags
    enable_monitoring: bool = True
    enable_prompt_registry: bool = True
    enable_data_pipeline: bool = True

    # Scraper defaults
    scraper_rate_limit: float = Field(default=1.0, description="Requests per second")
    scraper_respect_robots: bool = True

    # Anomaly detection
    anomaly_sensitivity: float = Field(default=2.5, description="Z-score threshold")

    model_config = {"env_prefix": "DEVOPS_", "env_file": ".env", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
