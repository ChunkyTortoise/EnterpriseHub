"""
MLS/Attom Property Data Integration Client

Provides real property data (listing history, valuations, comparable sales)
for seller psychology analysis and CMA generation.

Data sources (priority order):
1. Attom API — property valuation, listing history, comparable sales
2. MLS RETS feed — direct MLS data (requires board membership)
3. Fallback — contact-provided data (handled by caller)
"""

import logging
import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional

import httpx

from ghl_real_estate_ai.api.schemas.negotiation import ListingHistory

logger = logging.getLogger(__name__)


@dataclass
class PropertyValuation:
    """AVM (Automated Valuation Model) estimate."""

    address: str
    estimated_value: Decimal
    confidence_score: float  # 0.0-1.0
    valuation_date: str
    value_range_low: Optional[Decimal] = None
    value_range_high: Optional[Decimal] = None
    source: str = "attom"


@dataclass
class ComparableSale:
    """Recent comparable sale for CMA generation."""

    address: str
    sale_price: Decimal
    sale_date: str
    bedrooms: int
    bathrooms: float
    sqft: int
    distance_miles: float
    days_on_market: int = 0


class MLSClient:
    """Client for MLS/Attom property data integration."""

    def __init__(self):
        self.attom_api_key = os.getenv("ATTOM_API_KEY", "")
        self.attom_base_url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0"
        self.enabled = os.getenv("ENABLE_MLS_INTEGRATION", "false").lower() == "true"
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=10.0,
                headers={
                    "apikey": self.attom_api_key,
                    "Accept": "application/json",
                },
            )
        return self._http_client

    async def get_listing_history(self, property_address: str) -> Optional[ListingHistory]:
        """Fetch listing history from Attom data feed.

        Returns None if MLS integration is disabled or lookup fails.
        """
        if not self.enabled or not self.attom_api_key:
            return None

        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.attom_base_url}/sale/snapshot",
                params={"address1": property_address, "orderby": "SaleSearchDate desc"},
            )
            response.raise_for_status()
            data = response.json()

            sale_history = data.get("property", [{}])
            if not sale_history:
                return None

            prop = sale_history[0] if isinstance(sale_history, list) else sale_history
            sale_info = prop.get("sale", {}).get("amount", {})
            listing_info = prop.get("sale", {})

            original_price = Decimal(str(sale_info.get("saleamt", 0)))
            current_price = original_price

            # Calculate price drops from history
            price_drops: List[Dict[str, Any]] = []
            if isinstance(sale_history, list) and len(sale_history) > 1:
                for i in range(1, len(sale_history)):
                    prev_price = Decimal(str(sale_history[i - 1].get("sale", {}).get("amount", {}).get("saleamt", 0)))
                    curr_price = Decimal(str(sale_history[i].get("sale", {}).get("amount", {}).get("saleamt", 0)))
                    if curr_price < prev_price and prev_price > 0:
                        pct = float((prev_price - curr_price) / prev_price * 100)
                        price_drops.append({
                            "old_price": float(prev_price),
                            "new_price": float(curr_price),
                            "percentage": round(pct, 1),
                        })

            dom = int(listing_info.get("calculation", {}).get("daysonmarket", 0))

            return ListingHistory(
                original_list_price=original_price,
                current_price=current_price,
                price_drops=price_drops,
                days_on_market=dom,
            )

        except httpx.HTTPStatusError as e:
            logger.warning(f"Attom API error for {property_address}: {e.response.status_code}")
            return None
        except Exception as e:
            logger.warning(f"MLS lookup failed for {property_address}: {e}")
            return None

    async def get_property_valuation(self, property_address: str) -> Optional[PropertyValuation]:
        """Fetch AVM (Automated Valuation Model) estimate."""
        if not self.enabled or not self.attom_api_key:
            return None

        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.attom_base_url}/valuation/homeequity",
                params={"address1": property_address},
            )
            response.raise_for_status()
            data = response.json()

            prop = data.get("property", [{}])
            if isinstance(prop, list):
                prop = prop[0] if prop else {}

            avm = prop.get("avm", {})
            amount = avm.get("amount", {})

            estimated = Decimal(str(amount.get("value", 0)))
            if not estimated:
                return None

            return PropertyValuation(
                address=property_address,
                estimated_value=estimated,
                confidence_score=float(amount.get("confidence", 0.5)),
                valuation_date=avm.get("eventDate", ""),
                value_range_low=Decimal(str(amount.get("low", 0))) or None,
                value_range_high=Decimal(str(amount.get("high", 0))) or None,
            )

        except Exception as e:
            logger.warning(f"Property valuation failed for {property_address}: {e}")
            return None

    async def get_comparable_sales(
        self, property_address: str, radius_miles: float = 1.0
    ) -> List[ComparableSale]:
        """Fetch recent comparable sales for CMA generation."""
        if not self.enabled or not self.attom_api_key:
            return []

        try:
            client = await self._get_client()
            response = await client.get(
                f"{self.attom_base_url}/sale/snapshot",
                params={
                    "address1": property_address,
                    "radius": str(radius_miles),
                    "orderby": "SaleSearchDate desc",
                    "pagesize": "10",
                },
            )
            response.raise_for_status()
            data = response.json()

            comps: List[ComparableSale] = []
            for prop in data.get("property", []):
                sale = prop.get("sale", {})
                address_info = prop.get("address", {})
                building = prop.get("building", {}).get("rooms", {})

                addr = f"{address_info.get('line1', '')} {address_info.get('line2', '')}".strip()
                price = Decimal(str(sale.get("amount", {}).get("saleamt", 0)))
                if not price:
                    continue

                comps.append(ComparableSale(
                    address=addr,
                    sale_price=price,
                    sale_date=sale.get("saleTransDate", ""),
                    bedrooms=int(building.get("beds", 0)),
                    bathrooms=float(building.get("bathstotal", 0)),
                    sqft=int(prop.get("building", {}).get("size", {}).get("livingsize", 0)),
                    distance_miles=0.0,  # Attom doesn't return distance directly
                    days_on_market=int(sale.get("calculation", {}).get("daysonmarket", 0)),
                ))

            return comps

        except Exception as e:
            logger.warning(f"Comparable sales lookup failed for {property_address}: {e}")
            return []

    async def close(self):
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
