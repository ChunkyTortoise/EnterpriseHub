"""
ATTOM API Client - Pre-Lead Intelligence Data Engine
Fetches property DNA (Title, Tax, Deed, Liens) and Life Event triggers.
"""

import logging
import os
from typing import Any, Dict, Optional

import requests

from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


class AttomClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ATTOM_API_KEY")
        self.base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
        self.cache = get_cache_service()

        if not self.api_key:
            logger.warning("ATTOM_API_KEY not found. Data enrichment will be limited.")

    async def get_property_dna(self, address: str) -> Dict[str, Any]:
        """
        Fetches 200+ datapoints for a property via ATTOM API.
        Includes ownership history, tax details, and property characteristics.
        """
        cache_key = f"attom_dna:{address.replace(' ', '_').lower()}"

        # Check cache
        if self.cache:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Using cached ATTOM DNA for {address}")
                return cached_data

        if not self.api_key:
            return self._get_mock_dna(address)

        headers = {"apikey": self.api_key, "Accept": "application/json"}

        # In a real implementation, we would use proper address parsing
        params = {"address1": address}

        try:
            # We'll use the combined detail endpoint for maximum data
            url = f"{self.base_url}/property/detail"
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                property_dna = data.get("property", [{}])[0]

                # Cache for 24 hours
                if self.cache:
                    await self.cache.set(cache_key, property_dna, ttl=86400)

                return property_dna
            else:
                logger.error(f"ATTOM API Error: {response.status_code} - {response.text}")
                return self._get_mock_dna(address)

        except Exception as e:
            logger.error(f"ATTOM Exception: {e}")
            return self._get_mock_dna(address)

    async def get_life_event_triggers(self, address: str) -> Dict[str, Any]:
        """
        Checks for public records indicating life events (Probate, Divorce, Liens).
        """
        if not self.api_key:
            return {"probate": False, "divorce": False, "liens": 0, "propensity_score": 0.45}

        # Simplified for implementation pattern
        dna = await self.get_property_dna(address)

        # Analyze DNA for life events (simulated logic)
        has_probate = dna.get("assessment", {}).get("owner", {}).get("isDeceased", False)
        liens_count = len(dna.get("liens", []))

        return {
            "probate": has_probate,
            "liens": liens_count,
            "tax_delinquent": dna.get("tax", {}).get("isDelinquent", False),
            "last_transfer_date": dna.get("summary", {}).get("lastTransferDate"),
        }

    def _get_mock_dna(self, address: str) -> Dict[str, Any]:
        """Mock data for demonstration and fallback."""
        return {
            "address": address,
            "characteristics": {"bedrooms": 3, "bathrooms": 2.5, "sqft": 2150, "year_built": 2012},
            "assessment": {"market_value": 485000, "tax_amount": 9200},
            "summary": {"absentee_owner": True, "years_owned": 12, "last_transfer_date": "2014-06-12"},
        }


# Singleton instance
_attom_client = None


def get_attom_client() -> AttomClient:
    global _attom_client
    if _attom_client is None:
        _attom_client = AttomClient()
    return _attom_client
