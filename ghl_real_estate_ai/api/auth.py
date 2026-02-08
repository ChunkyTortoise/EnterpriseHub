"""
Compatibility re-exports for authentication utilities.

Routes that import from ``ghl_real_estate_ai.api.auth`` are redirected
to the canonical implementations in the middleware package.
"""

from ghl_real_estate_ai.api.middleware.jwt_auth import (
    JWTAuth,
    get_current_user,
    verify_jwt_token,
)

__all__ = ["get_current_user", "verify_jwt_token", "JWTAuth"]
