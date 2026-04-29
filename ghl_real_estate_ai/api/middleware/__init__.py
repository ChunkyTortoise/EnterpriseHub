"""Middleware package exports.

Keep imports lazy so tests and lightweight submodules can import without
initializing authentication settings or optional production dependencies.
"""

__all__ = [
    "RateLimitMiddleware",
    "SecurityHeadersMiddleware",
    "JWTAuth",
    "get_current_user",
    "APIKeyAuth",
    "verify_api_key",
    "ErrorHandlerMiddleware",
]

_EXPORT_MODULES = {
    "APIKeyAuth": ".api_key_auth",
    "verify_api_key": ".api_key_auth",
    "ErrorHandlerMiddleware": ".error_handler",
    "JWTAuth": ".jwt_auth",
    "get_current_user": ".jwt_auth",
    "RateLimitMiddleware": ".rate_limiter",
    "SecurityHeadersMiddleware": ".security_headers",
}


def __getattr__(name: str):
    if name not in _EXPORT_MODULES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    module = import_module(_EXPORT_MODULES[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
