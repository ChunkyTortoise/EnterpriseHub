"""
Shared Infrastructure Foundation for EnterpriseHub Products.

This module provides common utilities, models, and patterns used across
all 5 products in the EnterpriseHub ecosystem.

Version: 1.0.0
"""

__version__ = "1.0.0"

# Public exports
from shared.auth.api_key import APIKeyDependency, verify_api_key
from shared.billing.stripe_metered import StripeUsageMeter
from shared.cache.namespace import build_key, parse_key
from shared.config.settings import BaseSettings
from shared.database.rls import TenantContextManager, TenantMixin, set_tenant_context
from shared.models.base import APIKeyBase, TenantBase, UsageRecord

__all__ = [
    # Version
    "__version__",
    # Models
    "TenantBase",
    "APIKeyBase",
    "UsageRecord",
    # Auth
    "verify_api_key",
    "APIKeyDependency",
    # Billing
    "StripeUsageMeter",
    # Database
    "TenantContextManager",
    "set_tenant_context",
    "TenantMixin",
    # Cache
    "build_key",
    "parse_key",
    # Config
    "BaseSettings",
]
