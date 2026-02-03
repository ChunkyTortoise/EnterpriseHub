"""
Compatibility re-exports for API model types.

Routes that import from ``ghl_real_estate_ai.api.models`` are redirected
to the canonical implementations.
"""

from ghl_real_estate_ai.services.auth_service import User, UserRole

__all__ = ["User", "UserRole"]
