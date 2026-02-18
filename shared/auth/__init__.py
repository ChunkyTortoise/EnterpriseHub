"""Shared authentication utilities."""

from shared.auth.api_key import verify_api_key, APIKeyDependency

__all__ = ["verify_api_key", "APIKeyDependency"]
