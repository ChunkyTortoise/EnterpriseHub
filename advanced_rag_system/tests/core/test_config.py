"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from src.core.config import Settings, get_settings


@pytest.mark.integration
class TestSettings:
    """Test cases for Settings."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "Advanced RAG System"
        assert settings.app_version == "0.1.0"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.openai_embedding_model == "text-embedding-3-small"
        assert settings.openai_embedding_dimensions == 1536
        assert settings.vector_store_type == "chroma"
        assert settings.cache_enabled is True
        assert settings.cache_type == "memory"

    def test_log_level_validation(self) -> None:
        """Test log level validation."""
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"

        settings = Settings(log_level="ERROR")
        assert settings.log_level == "ERROR"

        with pytest.raises(ValueError):
            Settings(log_level="invalid")

    def test_embedding_dimensions_validation(self) -> None:
        """Test embedding dimensions validation."""
        with pytest.raises(ValueError):
            Settings(openai_embedding_dimensions=0)

        with pytest.raises(ValueError):
            Settings(openai_embedding_dimensions=20000)

        settings = Settings(openai_embedding_dimensions=768)
        assert settings.openai_embedding_dimensions == 768

    def test_batch_size_validation(self) -> None:
        """Test batch size validation."""
        with pytest.raises(ValueError):
            Settings(embedding_batch_size=0)

        with pytest.raises(ValueError):
            Settings(embedding_batch_size=2000)

        settings = Settings(embedding_batch_size=50)
        assert settings.embedding_batch_size == 50

    def test_cache_type_validation(self) -> None:
        """Test cache type validation."""
        settings = Settings(cache_type="memory")
        assert settings.cache_type == "memory"

        settings = Settings(cache_type="REDIS")
        assert settings.cache_type == "redis"

        with pytest.raises(ValueError):
            Settings(cache_type="invalid")

    def test_distance_metric_validation(self) -> None:
        """Test distance metric validation."""
        settings = Settings(vector_store_distance_metric="cosine")
        assert settings.vector_store_distance_metric == "cosine"

        settings = Settings(vector_store_distance_metric="EUCLIDEAN")
        assert settings.vector_store_distance_metric == "euclidean"

        with pytest.raises(ValueError):
            Settings(vector_store_distance_metric="invalid")

    def test_get_openai_api_key_from_env(self) -> None:
        """Test getting OpenAI API key from environment."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            settings = Settings()
            assert settings.get_openai_api_key() == "test-key"

    def test_get_openai_api_key_missing(self) -> None:
        """Test error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(openai_api_key=None)
            with pytest.raises(ValueError):
                settings.get_openai_api_key()

    def test_is_redis_configured(self) -> None:
        """Test Redis configuration check."""
        settings = Settings(cache_type="memory")
        assert settings.is_redis_configured() is False

        settings = Settings(cache_type="redis", redis_url=None)
        assert settings.is_redis_configured() is False

        settings = Settings(cache_type="redis", redis_url="redis://localhost:6379")
        assert settings.is_redis_configured() is True

    def test_get_cache_ttl(self) -> None:
        """Test getting cache TTL."""
        settings = Settings(cache_ttl_seconds=3600)
        assert settings.get_cache_ttl() == 3600
        assert settings.get_cache_ttl(custom_ttl=1800) == 1800

    def test_to_dict_excludes_secrets(self) -> None:
        """Test to_dict excludes secret values."""
        settings = Settings(openai_api_key="secret")
        result = settings.to_dict()
        assert "openai_api_key" not in result
        assert "app_name" in result
        assert "log_level" in result


class TestGetSettings:
    """Test cases for get_settings function."""

    def test_returns_settings(self) -> None:
        """Test that get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_caching(self) -> None:
        """Test that get_settings caches the result."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
