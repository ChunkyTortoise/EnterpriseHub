"""Billing route package.

Decomposed from billing.py (1,599 lines) into domain-specific modules:
- _helpers.py: Shared dependencies, retry logic, billing event tracking
- subscriptions.py: Subscription CRUD (create, read, update, cancel)
- usage.py: Usage tracking and metering
- payments.py: Invoice processing, payment, billing history
- analytics.py: Revenue analytics and tier distribution
- stripe_webhooks.py: Stripe webhook handler (separate auth)

The original billing.py is preserved during the strangler fig migration.
"""

from ghl_real_estate_ai.api.routes.billing_pkg._helpers import (
    get_billing_service,
    get_monitoring_service,
    get_subscription_manager,
)

__all__ = [
    "get_billing_service",
    "get_monitoring_service",
    "get_subscription_manager",
]
