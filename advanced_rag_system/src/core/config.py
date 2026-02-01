"""Configuration management for Advanced RAG System.

This module provides Pydantic v2-based settings management with
environment variable support, validation, and type safety.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables
    using the prefix RAG_. For example:
    - RAG_OPENAI_API_KEY
    - RAG_VECTOR_STORE_PATH
    - RAG_LOG_LEVEL

    Attributes:
        # Application
        app_name: Application name
        app_version: Application version
        debug: Debug mode flag
        log_level: Logging level

        # OpenAI
        openai_api_key: OpenAI API key
        openai_base_url: Optional custom OpenAI base URL
        openai_embedding_model: Embedding model name
        openai_embedding_dimensions: Embedding vector dimensions
        openai_max_retries: Maximum API retry attempts
        openai_timeout: API timeout in seconds

        # Vector Store
        vector_store_type: Type of vector store (chroma, pinecone)
        vector_store_path: Path for local vector store
        vector_store_collection: Default collection name
        vector_store_distance_metric: Distance metric (cosine, euclidean, dot)

        # Cache
        cache_enabled: Enable caching layer
        cache_type: Cache type (redis, memory)
        cache_ttl_seconds: Default cache TTL
        redis_url: Redis connection URL

        # Performance
        embedding_batch_size: Batch size for embedding generation
        max_concurrent_requests: Maximum concurrent API requests
        request_timeout_seconds: Request timeout
    """

    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="Advanced RAG System")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # OpenAI Settings
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: Optional[str] = Field(default=None)
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_embedding_dimensions: int = Field(default=1536)
    openai_max_retries: int = Field(default=3)
    openai_timeout: float = Field(default=30.0)

    # Vector Store Settings
    vector_store_type: str = Field(default="chroma")
    vector_store_path: str = Field(default="./chroma_db")
    vector_store_collection: str = Field(default="default")
    vector_store_distance_metric: str = Field(default="cosine")

    # Cache Settings
    cache_enabled: bool = Field(default=True)
    cache_type: str = Field(default="memory")
    cache_ttl_seconds: int = Field(default=3600)
    redis_url: Optional[str] = Field(default=None)

    # Performance Settings
    embedding_batch_size: int = Field(default=100)
    max_concurrent_requests: int = Field(default=10)
    request_timeout_seconds: float = Field(default=30.0)

    # Security Settings
    api_key_header: str = Field(default="X-API-Key")
    allowed_hosts: List[str] = Field(default_factory=lambda: ["*"])

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper_v = v.upper()
        if upper_v not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return upper_v

    @field_validator("openai_embedding_dimensions")
    @classmethod
    def _validate_embedding_dimensions(cls, v: int) -> int:
        """Validate embedding dimensions are reasonable."""
        if v < 1 or v > 10000:
            raise ValueError("embedding_dimensions must be between 1 and 10000")
        return v

    @field_validator("embedding_batch_size")
    @classmethod
    def _validate_batch_size(cls, v: int) -> int:
        """Validate batch size is positive and reasonable."""
        if v < 1 or v > 1000:
            raise ValueError("embedding_batch_size must be between 1 and 1000")
        return v

    @field_validator("vector_store_path")
    @classmethod
    def _validate_vector_store_path(cls, v: str) -> str:
        """Ensure vector store path is valid."""
        path = Path(v)
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        return str(path.resolve())

    @field_validator("cache_type")
    @classmethod
    def _validate_cache_type(cls, v: str) -> str:
        """Validate cache type is supported."""
        allowed = ["memory", "redis"]
        lower_v = v.lower()
        if lower_v not in allowed:
            raise ValueError(f"cache_type must be one of {allowed}")
        return lower_v

    @field_validator("vector_store_distance_metric")
    @classmethod
    def _validate_distance_metric(cls, v: str) -> str:
        """Validate distance metric is supported."""
        allowed = ["cosine", "euclidean", "dot"]
        lower_v = v.lower()
        if lower_v not in allowed:
            raise ValueError(f"distance_metric must be one of {allowed}")
        return lower_v

    def get_openai_api_key(self) -> str:
        """Get OpenAI API key with validation.

        Returns:
            The OpenAI API key

        Raises:
            ValueError: If API key is not configured
        """
        key = self.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Set RAG_OPENAI_API_KEY or OPENAI_API_KEY environment variable."
            )
        return key

    def is_redis_configured(self) -> bool:
        """Check if Redis is properly configured.

        Returns:
            True if Redis URL is set and cache type is redis
        """
        return self.cache_type == "redis" and self.redis_url is not None

    def get_cache_ttl(self, custom_ttl: Optional[int] = None) -> int:
        """Get cache TTL with optional override.

        Args:
            custom_ttl: Optional custom TTL in seconds

        Returns:
            TTL value to use
        """
        return custom_ttl if custom_ttl is not None else self.cache_ttl_seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary (excluding secrets).

        Returns:
            Dictionary of safe settings
        """
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "log_level": self.log_level,
            "openai_embedding_model": self.openai_embedding_model,
            "openai_embedding_dimensions": self.openai_embedding_dimensions,
            "vector_store_type": self.vector_store_type,
            "vector_store_path": self.vector_store_path,
            "cache_enabled": self.cache_enabled,
            "cache_type": self.cache_type,
            "embedding_batch_size": self.embedding_batch_size,
            "max_concurrent_requests": self.max_concurrent_requests,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Uses LRU cache to avoid re-reading environment variables
    on every call.

    Returns:
        Settings instance
    """
    return Settings()