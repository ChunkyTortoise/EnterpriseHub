"""Shared authentication utilities."""

from shared.auth.api_key import APIKeyDependency, verify_api_key

__all__ = ["verify_api_key", "APIKeyDependency"]
