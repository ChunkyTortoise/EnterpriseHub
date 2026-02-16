"""Application configuration via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """RAG-as-a-Service configuration."""

    model_config = {"env_prefix": "RAG_"}

    # Database
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag_service"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Stripe
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_starter_price_id: str = "price_starter"
    stripe_pro_price_id: str = "price_pro"
    stripe_business_price_id: str = "price_business"

    # Embedding
    embedding_provider: str = "openai"  # openai, cohere, local
    embedding_model: str = "text-embedding-3-small"
    embedding_api_key: str = ""
    embedding_dimension: int = 1536

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""

    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50

    # Retrieval
    top_k: int = 10
    rerank_top_k: int = 5

    # Tier limits
    starter_queries_per_month: int = 5_000
    starter_storage_mb: int = 1_000
    pro_queries_per_month: int = 50_000
    pro_storage_mb: int = 10_000
    business_queries_per_month: int = 500_000
    business_storage_mb: int = 100_000

    # Auth
    jwt_secret: str = "change-me-in-production"

    # App
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
