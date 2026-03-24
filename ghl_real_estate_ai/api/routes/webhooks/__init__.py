"""GHL webhook route package.

Decomposed from the monolithic webhook.py (2,698 lines) into:
- _helpers.py: Shared utilities (dependency injection, intent detection, mode flags)
- ghl.py: Main /webhook and /tag-webhook endpoints
- qualification.py: /initiate-qualification endpoint + background tasks

The original webhook.py is preserved as a thin re-export layer for
backward compatibility during migration.
"""

from ghl_real_estate_ai.api.routes.webhooks.ghl import router as ghl_router
from ghl_real_estate_ai.api.routes.webhooks.qualification import (
    router as qualification_router,
)

__all__ = ["ghl_router", "qualification_router"]
