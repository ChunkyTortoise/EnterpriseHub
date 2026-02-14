"""
Strategy Pattern Integration Module

Provides seamless integration between Repository Pattern and existing Strategy Pattern.
Replaces hardcoded data loading with flexible repository-based data access.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the parent directory to the path to import Strategy Pattern modules
current_dir = Path(__file__).parent
services_dir = current_dir.parent
sys.path.insert(0, str(services_dir))

try:
    # Import from ghl_real_estate_ai.services.scoring module
    from ghl_real_estate_ai.services.scoring import (
        PropertyMatcherContext,
        ScoringContext,
        ScoringResult,
        create_property_matcher,
        get_scoring_factory,
    )

    STRATEGY_PATTERN_AVAILABLE = True
except ImportError:
    try:
        # Fallback to relative import
        sys.path.insert(0, str(services_dir))
        from scoring import (
            PropertyMatcherContext,
            ScoringContext,
            ScoringResult,
            create_property_matcher,
            get_scoring_factory,
        )

        STRATEGY_PATTERN_AVAILABLE = True
    except ImportError:
        STRATEGY_PATTERN_AVAILABLE = False
        print("Strategy Pattern modules not available, using fallback")

try:
    from .interfaces import PropertyQuery, SortOrder
    from .property_data_service import PropertyDataService, PropertyDataServiceFactory
    from .query_builder import PropertyQueryBuilder
except ImportError:
    from property_data_service import PropertyDataService, PropertyDataServiceFactory


class RepositoryPropertyMatcher:
    """
    Enhanced PropertyMatcherContext that integrates Repository Pattern.

    This class extends the existing Strategy Pattern with Repository Pattern
    data loading capabilities, providing flexible data sources while maintaining
    the same interface.
    """

    def __init__(
        self,
        property_data_service: PropertyDataService,
        strategy_name: str = "enhanced",
        fallback_strategy: str = "basic",
        enable_monitoring: bool = True,
        enable_caching: bool = True,
    ):
        """
        Initialize repository-backed property matcher.

        Args:
            property_data_service: Repository service for data loading
            strategy_name: Primary scoring strategy
            fallback_strategy: Backup scoring strategy
            enable_monitoring: Enable performance monitoring
            enable_caching: Enable result caching
        """
        self.data_service = property_data_service
        self.strategy_name = strategy_name
        self.fallback_strategy = fallback_strategy
        self.enable_monitoring = enable_monitoring
        self.enable_caching = enable_caching

        # Initialize Strategy Pattern matcher if available
        if STRATEGY_PATTERN_AVAILABLE:
            self.strategy_matcher = create_property_matcher(
                strategy_name=strategy_name,
                fallback_strategy=fallback_strategy,
                enable_monitoring=enable_monitoring,
                enable_caching=enable_caching,
            )
        else:
            self.strategy_matcher = None

    async def score_properties_with_repository(
        self, lead_preferences: Dict[str, Any], context: Optional[Dict[str, Any]] = None, max_properties: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Score properties using Repository Pattern data loading + Strategy Pattern scoring.

        This method replaces the manual property loading in property_matcher_ai.py
        with Repository Pattern data access.

        Args:
            lead_preferences: Lead preferences for filtering and scoring
            context: Additional context for scoring
            max_properties: Maximum number of properties to score

        Returns:
            List of scored properties with detailed reasoning
        """
        try:
            # Load properties using Repository Pattern
            properties = await self.data_service.load_properties_for_strategy_pattern(lead_preferences)

            if not properties:
                return self._get_empty_fallback()

            # If Strategy Pattern is available, use it for scoring
            if self.strategy_matcher and STRATEGY_PATTERN_AVAILABLE:
                return await self._score_with_strategy_pattern(properties, lead_preferences, context, max_properties)
            else:
                # Use basic scoring fallback
                return await self._score_with_basic_fallback(properties, lead_preferences, max_properties)

        except Exception as e:
            print(f"Repository-based scoring failed: {e}")
            return self._get_error_fallback(str(e))

    async def _score_with_strategy_pattern(
        self,
        properties: List[Dict[str, Any]],
        lead_preferences: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        max_properties: int,
    ) -> List[Dict[str, Any]]:
        """Score properties using existing Strategy Pattern"""

        # Create scoring context
        scoring_context = ScoringContext(
            lead_id=context.get("lead_id") if context else None,
            agent_id=context.get("agent_id") if context else None,
            market_area=lead_preferences.get("location", "rancho_cucamonga"),
            performance_priority="balanced",
            enable_learning=True,
            min_confidence=60.0,
            max_properties=max_properties,
        )

        # Score using Strategy Pattern
        scored_properties = self.strategy_matcher.score_multiple_properties(
            properties=properties, lead_preferences=lead_preferences, context=scoring_context, max_workers=2
        )

        # Convert to UI format expected by property_matcher_ai.py
        formatted_matches = []
        for property_data in scored_properties[:max_properties]:
            formatted_match = self._format_property_for_ui(property_data, lead_preferences)
            formatted_matches.append(formatted_match)

        return formatted_matches

    async def _score_with_basic_fallback(
        self, properties: List[Dict[str, Any]], lead_preferences: Dict[str, Any], max_properties: int
    ) -> List[Dict[str, Any]]:
        """Basic scoring fallback when Strategy Pattern is not available"""
        scored_properties = []

        for prop in properties[:max_properties]:
            # Basic scoring logic
            score = self._calculate_basic_score(prop, lead_preferences)

            # Add scoring metadata
            prop["overall_score"] = score
            prop["match_reasons"] = self._generate_basic_match_reasons(prop, lead_preferences)
            prop["confidence_level"] = "medium" if score > 75 else "low"

            # Format for UI
            formatted = self._format_property_for_ui(prop, lead_preferences)
            scored_properties.append(formatted)

        # Sort by score
        scored_properties.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_properties

    def _calculate_basic_score(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> float:
        """Basic scoring algorithm fallback"""
        score = 50.0  # Base score

        # Price matching
        budget = lead_preferences.get("budget", 800000)
        price = property_data.get("price", 0)
        if price <= budget:
            score += 20
        elif price <= budget * 1.1:  # 10% over budget
            score += 10
        else:
            score -= 10

        # Bedroom matching
        desired_beds = lead_preferences.get("bedrooms", 3)
        property_beds = property_data.get("bedrooms", 0)
        if property_beds == desired_beds:
            score += 15
        elif abs(property_beds - desired_beds) == 1:
            score += 5

        # Location matching
        desired_location = lead_preferences.get("location", "").lower()
        property_location = property_data.get("neighborhood", "").lower()
        if desired_location in property_location or property_location in desired_location:
            score += 15

        # Amenities matching
        must_haves = lead_preferences.get("must_haves", [])
        property_amenities = property_data.get("amenities", [])
        if isinstance(property_amenities, str):
            property_amenities = [a.strip() for a in property_amenities.split(",")]

        amenity_matches = sum(
            1
            for amenity in must_haves
            if any(amenity.lower() in str(prop_amenity).lower() for prop_amenity in property_amenities)
        )
        if must_haves:
            score += (amenity_matches / len(must_haves)) * 10

        return min(max(score, 0), 100)

    def _generate_basic_match_reasons(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> List[str]:
        """Generate basic match reasons"""
        reasons = []

        budget = lead_preferences.get("budget", 800000)
        price = property_data.get("price", 0)

        if price <= budget:
            reasons.append(f"Within budget (${budget:,})")
        elif price <= budget * 1.1:
            reasons.append(f"Close to budget (${budget:,})")

        desired_beds = lead_preferences.get("bedrooms", 3)
        property_beds = property_data.get("bedrooms", 0)
        if property_beds == desired_beds:
            reasons.append(f"Exact bedroom count ({desired_beds} beds)")

        location = lead_preferences.get("location", "")
        if location.lower() in property_data.get("neighborhood", "").lower():
            reasons.append(f"Perfect location ({location})")

        return reasons or ["Property matches basic criteria"]

    def _format_property_for_ui(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format property for UI consumption (matches property_matcher_ai.py format)"""

        # Extract scoring metadata
        overall_score = property_data.get("overall_score", 75)
        match_reasons = property_data.get("match_reasons", ["Property matched"])
        confidence_level = property_data.get("confidence_level", "medium")

        # Budget analysis
        budget = lead_preferences.get("budget", 800000)
        price = property_data.get("price", 0)
        budget_match = price <= budget

        # Location analysis
        desired_location = lead_preferences.get("location", "").lower()
        property_location = property_data.get("neighborhood", "").lower()
        location_match = desired_location in property_location

        # Features analysis (simplified)
        features_match = overall_score > 70

        return {
            "address": property_data.get("address", "Property Address"),
            "price": price,
            "beds": property_data.get("bedrooms", property_data.get("beds", 3)),
            "baths": property_data.get("bathrooms", property_data.get("baths", 2.5)),
            "sqft": property_data.get("sqft", property_data.get("square_feet", 2100)),
            "neighborhood": property_data.get("neighborhood", "Rancho Cucamonga Area"),
            "icon": self._get_property_icon(property_data),
            "match_score": int(overall_score),
            "budget_match": budget_match,
            "location_match": location_match,
            "features_match": features_match,
            "match_reasons": match_reasons,
            "confidence_level": confidence_level,
            "strategy_metadata": property_data.get("scoring_metadata", {}),
            "_source_repository": property_data.get("_source", "unknown"),
        }

    def _get_property_icon(self, property_data: Dict[str, Any]) -> str:
        """Get appropriate icon for property type"""
        property_type = property_data.get("property_type", "").lower()
        if "condo" in property_type:
            return "🏢"
        elif "townhome" in property_type:
            return "🏘️"
        elif "multi" in property_type:
            return "🏬"
        else:
            return "🏡"

    def _get_empty_fallback(self) -> List[Dict[str, Any]]:
        """Return empty result when no properties found"""
        return []

    def _get_error_fallback(self, error_msg: str) -> List[Dict[str, Any]]:
        """Return error fallback properties"""
        return [
            {
                "address": "Error Loading Properties",
                "price": 0,
                "beds": 0,
                "baths": 0,
                "sqft": 0,
                "neighborhood": "N/A",
                "icon": "⚠️",
                "match_score": 0,
                "budget_match": False,
                "location_match": False,
                "features_match": False,
                "match_reasons": [f"Error: {error_msg}"],
                "confidence_level": "error",
            }
        ]

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get combined performance metrics"""
        metrics = {"repository_metrics": await self.data_service.get_performance_metrics(), "strategy_metrics": {}}

        if self.strategy_matcher:
            try:
                strategy_metrics = self.strategy_matcher.get_performance_metrics()
                metrics["strategy_metrics"] = strategy_metrics
            except Exception as e:
                metrics["strategy_metrics"] = {"error": str(e)}

        return metrics


async def create_repository_property_matcher(
    data_sources_config: Dict[str, Any], strategy_name: str = "enhanced", fallback_strategy: str = "basic"
) -> RepositoryPropertyMatcher:
    """
    Factory function to create integrated Repository + Strategy Pattern matcher.

    Args:
        data_sources_config: Configuration for data sources
        strategy_name: Primary scoring strategy
        fallback_strategy: Fallback scoring strategy

    Returns:
        Configured RepositoryPropertyMatcher

    Example:
        config = {
            "type": "demo",  # or "production", "hybrid"
            "json_data_dir": "./data/knowledge_base",
            "mls_config": {...},
            "rag_config": {...}
        }
    """

    # Create data service based on configuration
    config_type = data_sources_config.get("type", "demo")

    if config_type == "demo":
        data_dir = data_sources_config.get(
            "json_data_dir", "/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base"
        )
        data_service = await PropertyDataServiceFactory.create_demo_service(data_dir)

    elif config_type == "production":
        mls_config = data_sources_config.get("mls_config", {})
        fallback_paths = data_sources_config.get("json_fallback_paths", [])
        data_service = await PropertyDataServiceFactory.create_production_service(mls_config, fallback_paths)

    elif config_type == "hybrid":
        json_paths = data_sources_config.get("json_paths", [])
        mls_config = data_sources_config.get("mls_config")
        rag_config = data_sources_config.get("rag_config")
        data_service = await PropertyDataServiceFactory.create_hybrid_service(json_paths, mls_config, rag_config)

    else:
        raise ValueError(f"Unknown data source type: {config_type}")

    # Create integrated matcher
    return RepositoryPropertyMatcher(
        property_data_service=data_service,
        strategy_name=strategy_name,
        fallback_strategy=fallback_strategy,
        enable_monitoring=True,
        enable_caching=True,
    )


# Convenience functions for replacing existing property_matcher_ai.py functions
async def enhanced_generate_property_matches(
    lead_context: Dict, data_sources_config: Optional[Dict[str, Any]] = None
) -> List[Dict]:
    """
    Enhanced version of generate_property_matches() that uses Repository Pattern.

    Drop-in replacement for the function in property_matcher_ai.py with
    Repository Pattern data loading and Strategy Pattern scoring.

    Args:
        lead_context: Lead context from UI (same format as original)
        data_sources_config: Optional repository configuration

    Returns:
        Formatted property matches for UI (same format as original)
    """

    # Use default demo configuration if not provided
    if data_sources_config is None:
        data_sources_config = {
            "type": "demo",
            "json_data_dir": "/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base",
        }

    try:
        # Create repository matcher
        matcher = await create_repository_property_matcher(
            data_sources_config=data_sources_config, strategy_name="enhanced", fallback_strategy="basic"
        )

        # Extract lead preferences (same as original)
        extracted = lead_context.get("extracted_preferences", {})
        lead_preferences = {
            "budget": extracted.get("budget", 800000),
            "location": extracted.get("location", "Downtown"),
            "bedrooms": extracted.get("bedrooms", 3),
            "bathrooms": extracted.get("bathrooms", 2),
            "property_type": extracted.get("property_type", "Single Family"),
            "must_haves": extracted.get("must_haves", ["garage"]),
            "nice_to_haves": extracted.get("nice_to_haves", ["pool", "good_schools"]),
            "work_location": extracted.get("work_location", "downtown"),
            "has_children": extracted.get("has_children", False),
            "min_sqft": extracted.get("min_sqft", 1800),
        }

        # Score properties using Repository + Strategy Pattern
        scored_properties = await matcher.score_properties_with_repository(
            lead_preferences=lead_preferences, context=lead_context, max_properties=10
        )

        return scored_properties[:5]  # Return top 5 matches

    except Exception as e:
        print(f"Enhanced property matching failed: {e}")
        # Return fallback using original method if available
        return _get_fallback_properties(lead_context)


def _get_fallback_properties(lead_context: Dict) -> List[Dict]:
    """Fallback to static demo data (from original implementation)"""
    extracted = lead_context.get("extracted_preferences", {})
    budget = extracted.get("budget", 800000)
    location = extracted.get("location", "Downtown")
    beds = extracted.get("bedrooms", 3)

    return [
        {
            "address": "123 Oak Street",
            "price": 750000,
            "beds": 3,
            "baths": 2.5,
            "sqft": 2100,
            "neighborhood": "Downtown",
            "icon": "🏡",
            "match_score": 92,
            "budget_match": True,
            "location_match": True,
            "features_match": True,
            "match_reasons": [
                f"Within budget (${budget:,})",
                f"Perfect location ({location})",
                f"Exact bedroom count ({beds} beds)",
                "Newly renovated kitchen",
                "Walk to shops and restaurants",
            ],
        }
    ]


# Export main integration points
__all__ = ["RepositoryPropertyMatcher", "create_repository_property_matcher", "enhanced_generate_property_matches"]
