"""GHL webhook endpoints — main message processing.

This module re-exports the primary /webhook and /tag-webhook routes from
the original webhook.py during the strangler fig migration. As the main
handle_ghl_webhook handler is decomposed into smaller functions, they
will be moved here directly.

The original webhook.py remains the source of truth for the main /webhook
handler (~1,500 lines) until it is fully decomposed.
"""

# During migration, the original webhook.py router handles /webhook and /tag-webhook.
# This file exists to document the decomposition structure and will absorb the
# main handler logic in subsequent PRs.
#
# Usage: the original webhook.py router is included in main.py directly.
# This module is imported by webhooks/__init__.py for the package API.

from ghl_real_estate_ai.api.routes.webhook import router

__all__ = ["router"]
