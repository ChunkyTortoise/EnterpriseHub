"""
GHL Integration Module for EnterpriseHub

Unified GoHighLevel webhook handling for Lead, Seller, and Buyer bots.
Provides signature validation, deduplication, retry logic, and bidirectional sync.
"""

__version__ = "1.0.0"

from ghl_integration.deduplicator import EventDeduplicator
from ghl_integration.integration import initialize_ghl_integration, shutdown_ghl_integration
from ghl_integration.retry_manager import WebhookRetryManager
from ghl_integration.router import router as ghl_router
from ghl_integration.state_sync import GHLStateSynchronizer
from ghl_integration.validators import WebhookValidator

__all__ = [
    "ghl_router",
    "WebhookValidator",
    "EventDeduplicator",
    "WebhookRetryManager",
    "GHLStateSynchronizer",
    "initialize_ghl_integration",
    "shutdown_ghl_integration",
]
