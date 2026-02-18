"""Backward-compatible rate-limiting exports for legacy imports."""

from .rate_limiter import rate_limit

__all__ = ["rate_limit"]
