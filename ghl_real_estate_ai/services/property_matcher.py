"""
Property Matcher Service for GHL Real Estate AI.

Matches lead preferences to available property listings.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.jorge_config import CURRENT_MARKET
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.property_matching_strategy import (
    AISemanticSearchStrategy,
    BasicFilteringStrategy,
    PropertyMatchingStrategy,
)
from ghl_real_estate_ai.services.weaviate_client import get_weaviate_client

logger = get_logger(__name__)


class PropertyMatcher:
    """
    Service to match leads with property listings based on preferences.
    Upgraded to Agentic Reasoning in Phase 2 with Performance Caching.
    Refactored in 2026 for Multi-Tenant Resource Pooling.
    """

    # SHARED RESOURCE POOL: Static instances shared across all tenant-specific Matchers
    _shared_valuation_engine = None
    _weaviate_client = None
    _service_registry = {}

    # Class-level cache for property listings (shared across instances)
    _listings_cache: Optional[List[Dict[str, Any]]] = None
    _cache_timestamp: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(minutes=30)  # Cache for 30 minutes
    _loading_lock: asyncio.Lock = asyncio.Lock()

    def __init__(self, listings_path: Optional[str] = None):
        """
        Initialize the Property Matcher.
        """
        self.listings_path = self._resolve_listings_path(listings_path)
        self._sample_data_path = Path(__file__).parent.parent / "data" / "sample_properties.json"
        self.llm_client = LLMClient(provider="claude", model=settings.claude_model)
        self.analytics = AnalyticsService()
        self.strategy: PropertyMatchingStrategy = BasicFilteringStrategy()

        # Initialize Shared Resource Pool
        self._init_shared_resources()

    def _resolve_listings_path(self, listings_path: Optional[str]) -> Path:
        """Resolve listings path with env overrides and market defaults."""
        if listings_path:
            return Path(listings_path)

        env_path = os.getenv("JORGE_PROPERTY_LISTINGS_PATH")
        if env_path:
            return Path(env_path)

        if CURRENT_MARKET == "rancho_cucamonga":
            return Path(__file__).parent.parent / "data" / "knowledge_base" / "property_listings_rancho.json"

        return Path(__file__).parent.parent / "data" / "knowledge_base" / "property_listings.json"

    def _init_shared_resources(self):
        """
        Implements Service Discovery pattern to locate centralized compute resources.
        Reduces per-tenant overhead by sharing AVM compute logic.
        """
        if PropertyMatcher._shared_valuation_engine is not None:
            return

        try:
            # 2026 Pattern: Discover services via MCP Registry

            # Simulate service discovery
            # In a real 2026 environment, this would call the MCP tool
            # registry = asyncio.run(discover_services())
            # For now, we perform dynamic discovery/import
            from ghl_real_estate_ai.services.dynamic_valuation_engine import get_dynamic_valuation_engine

            PropertyMatcher._shared_valuation_engine = get_dynamic_valuation_engine()
            PropertyMatcher._weaviate_client = get_weaviate_client()
            logger.info("PropertyMatcher: Centralized AVM and Weaviate Services Linked to Shared Pool")
        except Exception as e:
            logger.error(f"Failed to discover shared AVM service: {e}")

    @property
    def weaviate_client(self):
        return PropertyMatcher._weaviate_client

    async def get_property_valuation(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Centralized AVM call using the shared resource pool.
        """
        if PropertyMatcher._shared_valuation_engine:
            result = await PropertyMatcher._shared_valuation_engine.generate_comprehensive_valuation(property_data)
            return {
                "estimated_value": result.estimated_value,
                "confidence": result.confidence_level.value,
                "valuation_date": result.valuation_date.isoformat(),
                "audit_trail_id": f"AVM-{result.property_id}",
            }
        return {"error": "Valuation service unavailable"}

    def set_strategy(self, strategy_type: str = "basic"):
        """
        Runtime switch for matching algorithm.
        options: 'basic', 'ai'
        """
        if strategy_type == "ai":
            self.strategy = AISemanticSearchStrategy()
            logger.info("Switched PropertyMatcher to AI Semantic Search Strategy")
        else:
            self.strategy = BasicFilteringStrategy()
            logger.info("Switched PropertyMatcher to Basic Filtering Strategy")

    async def _ensure_listings_loaded(self) -> None:
        """Ensure listings are loaded with intelligent caching."""
        if self._is_cache_valid():
            return

        async with self._loading_lock:
            # Double-check after acquiring lock
            if self._is_cache_valid():
                return

            await self._load_listings_async()

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if self._listings_cache is None or self._cache_timestamp is None:
            return False

        return datetime.now() - self._cache_timestamp < self._cache_ttl

    async def _load_listings_async(self) -> None:
        """Load listings from JSON file asynchronously with caching."""
        try:
            if self.listings_path.exists():
                async with aiofiles.open(self.listings_path, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    self._listings_cache = data.get("listings", [])
                    self._cache_timestamp = datetime.now()
                    logger.info(f"Loaded {len(self._listings_cache)} properties (cached for {self._cache_ttl})")
            else:
                logger.warning(f"Property listings file not found at {self.listings_path}")
                self._load_sample_data()
        except Exception as e:
            logger.error(f"Error loading property listings: {e}")
            if self._listings_cache is None:
                self._load_sample_data()

    @property
    def listings(self) -> List[Dict[str, Any]]:
        """Get cached listings with auto-refresh."""
        if not self._is_cache_valid():
            # For synchronous access, return cached data if available
            # and trigger async refresh if loop is running
            if self._listings_cache is not None:
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        asyncio.create_task(self._ensure_listings_loaded())
                except RuntimeError:
                    # No running loop, skipping async refresh
                    pass
                return self._listings_cache
            else:
                # First time load - fallback to sync for compatibility
                return self._load_listings_sync()

        return self._listings_cache or []

    def _load_listings_sync(self) -> List[Dict[str, Any]]:
        """Synchronous fallback for initial load. Falls back to sample data if primary source unavailable."""
        try:
            if self.listings_path.exists():
                with open(self.listings_path, "r") as f:
                    data = json.load(f)
                    fallback_listings = data.get("listings", [])
                    # Update cache for future use
                    self._listings_cache = fallback_listings
                    self._cache_timestamp = datetime.now()
                    logger.info(f"Sync loaded {len(fallback_listings)} properties")
                    return fallback_listings
            else:
                logger.warning(f"Property listings file not found at {self.listings_path}")
                return self._load_sample_data()
        except Exception as e:
            logger.error(f"Failed to load property listings: {e}")
            return self._load_sample_data()

    def _load_sample_data(self) -> List[Dict[str, Any]]:
        """Load sample Rancho Cucamonga properties as fallback data source."""
        try:
            if self._sample_data_path.exists():
                with open(self._sample_data_path, "r") as f:
                    data = json.load(f)
                    # Handle both array and {"listings": [...]} formats
                    sample_listings = data if isinstance(data, list) else data.get("listings", [])
                    self._listings_cache = sample_listings
                    self._cache_timestamp = datetime.now()
                    logger.info(f"Loaded {len(sample_listings)} sample properties as fallback")
                    return sample_listings
        except Exception as e:
            logger.error(f"Failed to load sample properties: {e}")
        return []

    def find_matches(self, preferences: Dict[str, Any], limit: int = 3, min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find property listings that match lead preferences using the active strategy.
        """
        # Delegate to the strategy
        matches = self.strategy.find_matches(self.listings, preferences, limit)

        # Filter by min_score if the strategy didn't (strategies return sorted list)
        return [m for m in matches if m.get("match_score", 0) >= min_score]

    def _calculate_match_score(self, property: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Deprecated: Logic moved to BasicFilteringStrategy."""
        return 0.0

    def generate_match_reasoning(self, property: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        """
        Generate the 'Why' - a human-readable reason for the match.
        """
        reasons = []

        # Budget
        budget = preferences.get("budget", 0)
        price = property.get("price", 0)
        if budget and price <= budget:
            savings = budget - price
            if savings > 50000:
                reasons.append(f"it's ${savings / 1000:.0f}k under your budget")
            else:
                reasons.append("it fits your price range")

        # Location
        loc = preferences.get("location")
        if loc and isinstance(loc, str) and loc.lower() in str(property.get("address")).lower():
            reasons.append(f"it's in {loc}")

        # Features/Bedrooms
        beds = preferences.get("bedrooms")
        if beds and property.get("bedrooms", 0) >= beds:
            reasons.append(f"has the {beds}+ bedrooms you needed")

        if not reasons:
            return "it's a strong overall match for your criteria"

        return f"I picked this because {', and '.join(reasons)}."

    async def agentic_explain_match(self, property: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        """
        🆕 Phase 2: Agentic Match Explanation
        Uses Claude to provide strategic, psychological, and financial reasoning.
        """
        prompt = f"""You are a senior Real Estate Investment Strategist. Explain why this property is a strategic match for this specific lead.

PROPERTY DATA:
{json.dumps(property, indent=2)}

LEAD PREFERENCES:
{json.dumps(preferences, indent=2)}

YOUR GOAL:
1. Provide a "Psychological Hook" (why it fits their life/goals).
2. Provide a "Financial Logic" (value, ROI, or budget fit).
3. Be professional, direct, and authoritative.
4. Keep it under 3 sentences for SMS/Chat consumption.

Example: "This South Lamar home is a strategic capture; it sits 5% below your budget while offering the modern renovation you prioritized. The high walkability score aligns with your request for an active neighborhood lifestyle."
"""
        try:
            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are an expert Real Estate Strategist. Speak with authority and precision.",
                temperature=0.7,
                max_tokens=200,
            )

            # Record usage
            location_id = preferences.get("location_id", "unknown")
            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=response.model,
                provider=response.provider.value,
                input_tokens=response.input_tokens or 0,
                output_tokens=response.output_tokens or 0,
                cached=False,
            )

            return response.content.strip()
        except Exception as e:
            logger.error(f"Agentic explanation failed: {e}")
            return self.generate_match_reasoning(property, preferences)

    def find_buyer_matches(
        self, budget: int, beds: Optional[int] = None, neighborhood: Optional[str] = None, limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find properties matching buyer criteria from sample data.
        Filters by: price range (budget ± 20%), beds, neighborhood preference.
        Returns top matches sorted by match score.
        """
        listings = self.listings
        if not listings:
            listings = self._load_sample_data()

        scored = []
        budget_min = int(budget * 0.8)
        budget_max = int(budget * 1.2)

        for prop in listings:
            price = prop.get("price", 0)
            if not (budget_min <= price <= budget_max):
                continue

            score = 1.0

            # Bedroom match
            prop_beds = prop.get("beds", prop.get("bedrooms", 0))
            if beds and prop_beds >= beds:
                score += 0.3
            elif beds and prop_beds < beds:
                continue  # Hard filter: must meet minimum beds

            # Neighborhood preference
            prop_neighborhood = prop.get("neighborhood", "")
            if neighborhood and neighborhood.lower() in prop_neighborhood.lower():
                score += 0.5

            # Closer to budget center scores higher
            budget_distance = abs(price - budget) / budget
            score += (1.0 - budget_distance) * 0.2

            scored.append({**prop, "match_score": round(score, 2)})

        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored[:limit]

    def format_match_for_sms(self, property: Dict[str, Any]) -> str:
        """Format a property match for an SMS message."""
        # Handle both sample data format (address as string) and legacy format (address as dict)
        addr = property.get("address", "")
        price = property.get("price", 0)

        if isinstance(addr, dict):
            beds = property.get("bedrooms", 0)
            baths = property.get("bathrooms", 0)
            neighborhood = addr.get("neighborhood", addr.get("city", ""))
            return f"${price:,} in {neighborhood}: {beds}br/{baths}ba home. Check it out: {property.get('listing_url', 'N/A')}"

        # Sample data format
        beds = property.get("beds", property.get("bedrooms", 0))
        baths = property.get("baths", property.get("bathrooms", 0))
        description = property.get("description", "")
        return f"${price:,} | {beds}bd/{baths}ba | {description}"
