"""
Market Intelligence Tool - Financial Precision Engine.

Provides real-time market comps and valuation adjustments for Jorge's ROI defense.
"""

import logging
from typing import Any, Dict

from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

logger = logging.getLogger(__name__)


class MarketIntelligence:
    """
    Interface for pulling actual market comps and refined valuations.
    """

    def __init__(self):
        self.national_intel = get_national_market_intelligence()

    async def get_valuation(self, location: str, base_price: float) -> float:
        """
        Pull actual market comps or use refined appreciation metrics.
        """
        return await self.national_intel.get_market_valuation(location, base_price)

    async def get_market_metrics(self, location: str) -> Dict[str, Any]:
        """
        Fetch raw metrics for a given location.
        """
        metrics = await self.national_intel.get_market_metrics(location)
        if metrics:
            return metrics.__dict__
        return {"error": "Location not found in registry"}


# Singleton
_market_intelligence = None


def get_market_intelligence() -> MarketIntelligence:
    global _market_intelligence
    if _market_intelligence is None:
        _market_intelligence = MarketIntelligence()
    return _market_intelligence
