"""
Integration Example: Property Scoring Strategy Pattern with Existing PropertyMatcher

This file demonstrates how to integrate the new Strategy Pattern-based
property scoring system with the existing PropertyMatcher implementation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import the new strategy pattern components
from . import EnhancedPropertyScorer, LeadPreferences, PropertyMatcherContext, ScoringContext, ScoringFactory

logger = logging.getLogger(__name__)


class EnhancedPropertyMatcherAI:
    """
    Enhanced PropertyMatcher using Strategy Pattern for scoring

    This class demonstrates how to integrate the new scoring system
    with the existing PropertyMatcher while maintaining backward compatibility.
    """

    def __init__(self, strategy_name: str = "enhanced", market_data: Optional[Dict] = None):
        """
        Initialize enhanced property matcher

        Args:
            strategy_name: Name of scoring strategy to use
            market_data: Optional market data for enhanced strategies
        """
        self.factory = ScoringFactory()
        self.scoring_context = PropertyMatcherContext()

        # Create and set strategy
        if strategy_name == "enhanced" and market_data:
            strategy = self.factory.create_strategy(strategy_name, market_data=market_data)
        else:
            strategy = self.factory.create_strategy(strategy_name)

        self.scoring_context.set_strategy(strategy)
        self.current_strategy_name = strategy_name

        logger.info(f"Initialized PropertyMatcher with {strategy_name} strategy")

    def generate_property_matches(self, lead_context: Dict, limit: int = 5, min_confidence: float = 60.0) -> List[Dict]:
        """
        Enhanced property matching using Strategy Pattern

        This method replaces the original generate_property_matches()
        while maintaining full backward compatibility.

        Args:
            lead_context: Original lead context format
            limit: Maximum number of matches to return
            min_confidence: Minimum confidence score to include

        Returns:
            List of properties in original format with enhanced scoring
        """
        try:
            # Extract preferences from lead context
            extracted_prefs = lead_context.get("extracted_preferences", {})

            # Load properties (integrate with existing property loading)
            properties = self._load_properties()

            # Create enhanced scoring context
            scoring_context = ScoringContext(
                quality_threshold=min_confidence / 100.0, scoring_purpose="lead_matching", enable_caching=True
            )

            # Score properties using strategy pattern
            scored_properties = self.scoring_context.score_multiple_properties(
                properties=properties, lead_preferences=extracted_prefs, context=scoring_context, limit=limit
            )

            # Convert to legacy format for UI compatibility
            legacy_matches = []
            for scored_prop in scored_properties:
                legacy_match = self._convert_to_legacy_format(scored_prop, extracted_prefs)
                legacy_matches.append(legacy_match)

            logger.info(f"Generated {len(legacy_matches)} property matches using {self.current_strategy_name} strategy")
            return legacy_matches

        except Exception as e:
            logger.error(f"Property matching failed: {e}")
            # Fallback to basic strategy
            return self._fallback_matching(lead_context, limit)

    def _convert_to_legacy_format(
        self, scored_property: Dict[str, Any], lead_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert new scoring format to legacy format for UI compatibility

        Args:
            scored_property: Property with new scoring format
            lead_preferences: Lead preferences for context

        Returns:
            Property in legacy format
        """
        scoring_result = scored_property["scoring_result"]

        # Extract original property data
        property_data = {
            k: v
            for k, v in scored_property.items()
            if k not in ["scoring_result", "confidence_score", "match_score", "match_reasons"]
        }

        # Create legacy format
        legacy_property = {
            "address": property_data.get("address", {}).get("street", "Unknown Address"),
            "price": property_data.get("price", 0),
            "beds": property_data.get("bedrooms", 0),
            "baths": property_data.get("bathrooms", 0),
            "sqft": property_data.get("sqft", 0),
            "neighborhood": property_data.get("address", {}).get("neighborhood", "Unknown"),
            "icon": self._get_property_icon(property_data),
            "match_score": int(scoring_result.overall_score),
            "budget_match": scoring_result.budget_score > 80,
            "location_match": scoring_result.location_score > 80,
            "features_match": scoring_result.feature_score > 80,
            "match_reasons": scoring_result.reasoning[:5],  # Limit for UI
            "confidence_level": scoring_result.confidence_level.value,
            # Enhanced fields from new system
            "ml_breakdown": {
                "budget_confidence": scoring_result.budget_score,
                "location_confidence": scoring_result.location_score,
                "feature_confidence": scoring_result.feature_score,
                "market_confidence": scoring_result.market_score,
            },
            # Risk and opportunity insights
            "risk_factors": scoring_result.risk_factors,
            "opportunities": scoring_result.opportunities,
            "match_insights": scoring_result.match_insights,
        }

        return legacy_property

    def _get_property_icon(self, property_data: Dict) -> str:
        """Get appropriate icon for property type"""
        property_type = property_data.get("property_type", "").lower()
        if "condo" in property_type:
            return "🏢"
        elif "townhome" in property_type:
            return "🏘️"
        elif "multi" in property_type:
            return "🏬"
        else:
            return "🏡"  # Default single family

    def _load_properties(self) -> List[Dict[str, Any]]:
        """
        Load properties from data source

        This method should integrate with your existing property loading logic.
        For now, it returns demo data that matches the expected format.
        """
        # In production, this would load from your actual data source
        # For demo, return properties that work with the new scoring system
        return [
            {
                "id": "prop_001",
                "price": 750000,
                "address": {"street": "123 Oak Street", "neighborhood": "Downtown", "city": "Austin", "zip": "78701"},
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2100,
                "property_type": "Single Family",
                "year_built": 2015,
                "amenities": ["pool", "garage", "garden"],
                "school_rating": 8.5,
                "crime_score": 7.2,
                "walkability_score": 85,
                "days_on_market": 15,
                "price_per_sqft": 357.14,
            },
            {
                "id": "prop_002",
                "price": 680000,
                "address": {"street": "456 Maple Avenue", "neighborhood": "Mueller", "city": "Austin", "zip": "78723"},
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1950,
                "property_type": "Single Family",
                "year_built": 2018,
                "amenities": ["garage", "modern", "energy_efficient"],
                "school_rating": 7.8,
                "crime_score": 8.1,
                "walkability_score": 78,
                "days_on_market": 8,
                "price_per_sqft": 348.72,
            },
            {
                "id": "prop_003",
                "price": 825000,
                "address": {"street": "789 Cedar Lane", "neighborhood": "Westlake", "city": "Austin", "zip": "78746"},
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2800,
                "property_type": "Single Family",
                "year_built": 2020,
                "amenities": ["pool", "garage", "view", "luxury"],
                "school_rating": 9.2,
                "crime_score": 9.5,
                "walkability_score": 65,
                "days_on_market": 22,
                "price_per_sqft": 294.64,
            },
        ]

    def _fallback_matching(self, lead_context: Dict, limit: int) -> List[Dict]:
        """
        Fallback to basic matching if enhanced matching fails

        Args:
            lead_context: Lead context
            limit: Number of matches to return

        Returns:
            Basic property matches
        """
        logger.warning("Using fallback matching strategy")

        try:
            # Switch to basic strategy
            basic_strategy = self.factory.create_strategy("basic")
            self.scoring_context.set_strategy(basic_strategy)

            # Retry with basic strategy
            extracted_prefs = lead_context.get("extracted_preferences", {})
            properties = self._load_properties()

            scored_properties = self.scoring_context.score_multiple_properties(
                properties=properties, lead_preferences=extracted_prefs, limit=limit
            )

            return [self._convert_to_legacy_format(prop, extracted_prefs) for prop in scored_properties]

        except Exception as e:
            logger.error(f"Fallback matching also failed: {e}")
            # Return empty list as last resort
            return []

    def switch_strategy(self, strategy_name: str, **kwargs) -> bool:
        """
        Switch to a different scoring strategy

        Args:
            strategy_name: Name of strategy to switch to
            **kwargs: Additional arguments for strategy creation

        Returns:
            True if switch successful
        """
        try:
            new_strategy = self.factory.create_strategy(strategy_name, **kwargs)
            self.scoring_context.set_strategy(new_strategy)
            self.current_strategy_name = strategy_name

            logger.info(f"Successfully switched to {strategy_name} strategy")
            return True

        except Exception as e:
            logger.error(f"Failed to switch to {strategy_name} strategy: {e}")
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the current strategy"""
        return self.scoring_context.get_performance_metrics()

    def get_strategy_recommendations(self, lead_context: Dict) -> List[str]:
        """
        Get strategy recommendations based on lead context

        Args:
            lead_context: Lead context to analyze

        Returns:
            List of recommended strategy names
        """
        extracted_prefs = lead_context.get("extracted_preferences", {})

        requirements = {
            "performance_priority": "balanced",
            "complexity_tolerance": "medium",
            "features_needed": [],
            "data_availability": "medium",
        }

        # Analyze lead preferences to adjust requirements
        budget = extracted_prefs.get("budget", 0)
        must_haves = extracted_prefs.get("must_haves", [])

        if budget > 1_000_000:
            requirements["complexity_tolerance"] = "high"
            requirements["performance_priority"] = "accuracy"

        if len(must_haves) > 3:
            requirements["features_needed"] = ["weighted_feature_matching"]

        # Get recommendation from factory
        recommended_strategy = self.factory.recommend_strategy(requirements)
        available_strategies = [s["name"] for s in self.factory.list_strategies()]

        return [recommended_strategy] + [s for s in available_strategies if s != recommended_strategy]

    def compare_strategies(self, lead_context: Dict, property_id: str = None) -> Dict[str, Any]:
        """
        Compare different strategies on the same lead/property combination

        Args:
            lead_context: Lead context
            property_id: Optional specific property ID to test

        Returns:
            Comparison results
        """
        extracted_prefs = lead_context.get("extracted_preferences", {})
        properties = self._load_properties()

        # Use first property if no specific ID provided
        test_property = properties[0] if properties and not property_id else None
        if property_id:
            test_property = next((p for p in properties if p.get("id") == property_id), None)

        if not test_property:
            return {"error": "No property found for comparison"}

        # Get all available strategies
        available_strategies = [self.factory.create_strategy(s["name"]) for s in self.factory.list_strategies()]

        # Compare strategies
        comparison_results = self.scoring_context.compare_strategies(
            property_data=test_property, lead_preferences=extracted_prefs, strategies=available_strategies
        )

        # Format results for analysis
        formatted_results = {}
        for strategy_name, result in comparison_results.items():
            formatted_results[strategy_name] = {
                "overall_score": result.overall_score,
                "confidence_level": result.confidence_level.value,
                "component_scores": {
                    "budget": result.budget_score,
                    "location": result.location_score,
                    "features": result.feature_score,
                    "market": result.market_score,
                },
                "reasoning_count": len(result.reasoning),
                "risk_factors_count": len(result.risk_factors),
                "opportunities_count": len(result.opportunities),
            }

        return {
            "property_tested": test_property.get("id"),
            "lead_budget": extracted_prefs.get("budget"),
            "strategy_results": formatted_results,
            "best_strategy": max(comparison_results.items(), key=lambda x: x[1].overall_score)[0],
        }


# Integration utility functions


def upgrade_existing_property_matcher():
    """
    Utility function to demonstrate upgrading existing PropertyMatcher

    This shows how to enhance the existing generate_property_matches function
    with minimal code changes.
    """

    def enhanced_generate_property_matches(lead_context: Dict) -> List[Dict]:
        """
        Drop-in replacement for original generate_property_matches

        This function maintains the exact same interface as the original
        but uses the new Strategy Pattern scoring system internally.
        """
        # Initialize enhanced matcher (could be a singleton)
        matcher = EnhancedPropertyMatcherAI(strategy_name="enhanced")

        # Use new system with legacy interface
        return matcher.generate_property_matches(lead_context)

    return enhanced_generate_property_matches


def create_adaptive_property_matcher(lead_id: str):
    """
    Create a property matcher that adapts to specific lead behavior

    Args:
        lead_id: Unique lead identifier for personalization

    Returns:
        Configured PropertyMatcher instance
    """
    # This would use the AdaptiveScorer when implemented
    matcher = EnhancedPropertyMatcherAI(strategy_name="enhanced")

    # Configure for specific lead (placeholder for adaptive features)
    # In full implementation, this would load lead history and preferences
    logger.info(f"Created adaptive matcher for lead {lead_id}")

    return matcher


def benchmark_strategies(sample_leads: List[Dict], sample_properties: List[Dict]) -> Dict[str, Any]:
    """
    Benchmark different strategies against sample data

    Args:
        sample_leads: List of lead contexts
        sample_properties: List of property data

    Returns:
        Benchmark results
    """
    factory = ScoringFactory()
    available_strategies = factory.list_strategies()

    results = {"strategy_performance": {}, "accuracy_metrics": {}, "timing_results": {}}

    for strategy_info in available_strategies:
        strategy_name = strategy_info["name"]
        matcher = EnhancedPropertyMatcherAI(strategy_name=strategy_name)

        # Benchmark timing and accuracy
        import time

        start_time = time.time()

        total_scores = 0
        total_matches = 0

        for lead_context in sample_leads[:10]:  # Limit for benchmark
            matches = matcher.generate_property_matches(lead_context, limit=3)
            total_matches += len(matches)
            total_scores += sum(m["match_score"] for m in matches)

        end_time = time.time()

        results["strategy_performance"][strategy_name] = {
            "total_time": end_time - start_time,
            "avg_time_per_lead": (end_time - start_time) / len(sample_leads[:10]),
            "total_matches": total_matches,
            "avg_score": total_scores / total_matches if total_matches > 0 else 0,
        }

    return results


# Example usage demonstration
if __name__ == "__main__":
    # Example lead context (matches existing format)
    example_lead_context = {
        "extracted_preferences": {
            "budget": 800000,
            "location": "Downtown",
            "bedrooms": 3,
            "property_type": "Single Family",
            "must_haves": ["garage", "pool"],
            "nice_to_haves": ["good_schools", "walkable"],
        }
    }

    # Create enhanced matcher
    matcher = EnhancedPropertyMatcherAI(strategy_name="enhanced")

    # Generate matches (same interface as original)
    matches = matcher.generate_property_matches(example_lead_context)

    print(f"Found {len(matches)} property matches:")
    for i, match in enumerate(matches[:3]):
        print(f"\n{i + 1}. {match['address']} - {match['match_score']}% match")
        print(
            f"   Budget: {'✓' if match['budget_match'] else '✗'}, "
            f"Location: {'✓' if match['location_match'] else '✗'}, "
            f"Features: {'✓' if match['features_match'] else '✗'}"
        )
        print(f"   Reasons: {match['match_reasons'][:2]}")

    # Demonstrate strategy comparison
    print("\n" + "=" * 50)
    print("Strategy Comparison:")
    comparison = matcher.compare_strategies(example_lead_context)
    for strategy, results in comparison["strategy_results"].items():
        print(f"{strategy}: {results['overall_score']:.1f}% ({results['confidence_level']})")

    # Show performance metrics
    print("\n" + "=" * 50)
    print("Performance Metrics:")
    metrics = matcher.get_performance_metrics()
    for strategy, perf in metrics.items():
        print(f"{strategy}: {perf['avg_time']:.3f}s avg, {perf['success_rate']:.2%} success rate")
