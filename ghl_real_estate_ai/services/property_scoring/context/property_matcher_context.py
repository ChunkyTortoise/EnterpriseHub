"""
Property Matcher Context - Strategy Pattern Context Implementation
Orchestrates property scoring using different strategies
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..interfaces.property_scorer import PropertyScorer, ScoringResult
from ..interfaces.scoring_context import LeadPreferences, ScoringContext

logger = logging.getLogger(__name__)


class PropertyMatcherContext:
    """
    Context class for the Strategy Pattern implementation

    This class orchestrates property scoring using different strategies
    while maintaining a consistent interface for clients.

    Key Responsibilities:
    - Manage scoring strategy selection
    - Coordinate scoring operations
    - Handle result aggregation and comparison
    - Provide fallback mechanisms
    - Manage performance and caching
    """

    def __init__(self, default_strategy: Optional[PropertyScorer] = None):
        """
        Initialize the property matcher context

        Args:
            default_strategy: Default scoring strategy to use
        """
        self._strategy = default_strategy
        self._strategy_history: List[Dict[str, Any]] = []
        self._performance_metrics: Dict[str, Any] = {}
        self._cache: Dict[str, ScoringResult] = {}

    def set_strategy(self, strategy: PropertyScorer) -> None:
        """
        Set the scoring strategy

        Args:
            strategy: PropertyScorer implementation to use
        """
        if not isinstance(strategy, PropertyScorer):
            raise ValueError("Strategy must implement PropertyScorer interface")

        # Warm up the new strategy
        try:
            strategy.warm_up()
        except Exception as e:
            logger.warning(f"Strategy warm-up failed: {e}")

        # Clean up previous strategy
        if self._strategy:
            try:
                self._strategy.cleanup()
            except Exception as e:
                logger.warning(f"Strategy cleanup failed: {e}")

        self._strategy = strategy
        logger.info(f"Strategy changed to: {strategy.name}")

    def get_strategy(self) -> Optional[PropertyScorer]:
        """Get the current scoring strategy"""
        return self._strategy

    def score_property(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any], context: Optional[ScoringContext] = None
    ) -> ScoringResult:
        """
        Score a single property using the current strategy

        Args:
            property_data: Property information
            lead_preferences: Lead preferences (legacy format)
            context: Optional scoring context

        Returns:
            ScoringResult with detailed scoring

        Raises:
            ValueError: If no strategy is set or validation fails
        """
        if not self._strategy:
            raise ValueError("No scoring strategy set")

        # Convert legacy preferences if needed
        if isinstance(lead_preferences, dict):
            structured_prefs = LeadPreferences.from_legacy_format(lead_preferences)
        else:
            structured_prefs = lead_preferences

        # Generate cache key
        cache_key = self._generate_cache_key(property_data, lead_preferences)

        # Check cache if enabled
        if context and context.enable_caching and cache_key in self._cache:
            cached_result = self._cache[cache_key]
            # Validate cache TTL
            if self._is_cache_valid(cached_result, context.cache_ttl):
                logger.debug(f"Cache hit for property {property_data.get('id', 'unknown')}")
                return cached_result

        # Record performance start
        start_time = datetime.now()

        try:
            # Execute scoring
            result = self._strategy.calculate_score(property_data, lead_preferences)

            # Apply context adjustments if provided
            if context:
                result = self._apply_context_adjustments(result, context)

            # Cache result if enabled
            if context and context.enable_caching:
                self._cache[cache_key] = result

            # Record performance metrics
            end_time = datetime.now()
            scoring_time = (end_time - start_time).total_seconds()
            self._update_performance_metrics(self._strategy.name, scoring_time, True)

            # Record strategy usage
            self._record_strategy_usage(property_data, result)

            return result

        except Exception as e:
            # Record performance metrics for failure
            end_time = datetime.now()
            scoring_time = (end_time - start_time).total_seconds()
            self._update_performance_metrics(self._strategy.name, scoring_time, False)

            logger.error(f"Scoring failed with {self._strategy.name}: {e}")
            raise

    def score_multiple_properties(
        self,
        properties: List[Dict[str, Any]],
        lead_preferences: Dict[str, Any],
        context: Optional[ScoringContext] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score multiple properties and return ranked results

        Args:
            properties: List of property data
            lead_preferences: Lead preferences
            context: Optional scoring context
            limit: Maximum number of results to return

        Returns:
            List of properties with scoring results, ranked by score
        """
        if not self._strategy:
            raise ValueError("No scoring strategy set")

        scored_properties = []

        for prop_data in properties:
            try:
                scoring_result = self.score_property(prop_data, lead_preferences, context)

                # Create enriched property data
                enriched_property = prop_data.copy()
                enriched_property.update(
                    {
                        "scoring_result": scoring_result,
                        "confidence_score": scoring_result,  # Legacy compatibility
                        "match_score": int(scoring_result.overall_score),  # Legacy compatibility
                        "match_reasons": scoring_result.reasoning,  # Legacy compatibility
                    }
                )

                # Apply quality threshold if specified
                if context and scoring_result.overall_score >= context.quality_threshold * 100:
                    scored_properties.append(enriched_property)
                elif not context:
                    scored_properties.append(enriched_property)

            except Exception as e:
                logger.error(f"Failed to score property {prop_data.get('id', 'unknown')}: {e}")
                continue

        # Sort by score (descending)
        scored_properties.sort(key=lambda x: x["scoring_result"].overall_score, reverse=True)

        # Apply limit if specified
        if limit:
            scored_properties = scored_properties[:limit]

        return scored_properties

    def compare_strategies(
        self,
        property_data: Dict[str, Any],
        lead_preferences: Dict[str, Any],
        strategies: List[PropertyScorer],
        context: Optional[ScoringContext] = None,
    ) -> Dict[str, ScoringResult]:
        """
        Compare multiple strategies on the same property

        Args:
            property_data: Property to score
            lead_preferences: Lead preferences
            strategies: List of strategies to compare
            context: Optional scoring context

        Returns:
            Dict mapping strategy name to scoring result
        """
        results = {}

        original_strategy = self._strategy

        try:
            for strategy in strategies:
                try:
                    self.set_strategy(strategy)
                    result = self.score_property(property_data, lead_preferences, context)
                    results[strategy.name] = result
                except Exception as e:
                    logger.error(f"Strategy comparison failed for {strategy.name}: {e}")
                    continue

        finally:
            # Restore original strategy
            if original_strategy:
                self.set_strategy(original_strategy)

        return results

    def get_strategy_recommendations(
        self, lead_preferences: Dict[str, Any], available_strategies: List[PropertyScorer]
    ) -> List[PropertyScorer]:
        """
        Recommend optimal strategies based on lead preferences

        Args:
            lead_preferences: Lead preferences to analyze
            available_strategies: Available scoring strategies

        Returns:
            List of recommended strategies in order of preference
        """
        recommendations = []

        # Analyze lead preferences to determine optimal strategy
        budget = lead_preferences.get("budget", 0)
        must_haves = lead_preferences.get("must_haves", [])
        location_specificity = len(lead_preferences.get("location", "").split())

        for strategy in available_strategies:
            score = 0

            # Score based on strategy capabilities
            if "advanced_budget_analysis" in strategy.get_supported_features() and budget > 500_000:
                score += 3

            if "weighted_feature_matching" in strategy.get_supported_features() and len(must_haves) > 2:
                score += 3

            if "geographic_scoring" in strategy.get_supported_features() and location_specificity > 1:
                score += 2

            if hasattr(strategy, "is_trained") and strategy.is_trained:
                score += 2

            recommendations.append((strategy, score))

        # Sort by score and return strategies
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [strategy for strategy, _ in recommendations]

    def _apply_context_adjustments(self, result: ScoringResult, context: ScoringContext) -> ScoringResult:
        """Apply context-specific adjustments to scoring result"""
        if not context:
            return result

        # Apply weight adjustments if provided
        if context.score_weights:
            # Recalculate overall score with custom weights
            default_weights = {"budget": 0.35, "location": 0.30, "features": 0.25, "market": 0.10}
            effective_weights = context.get_effective_weights(default_weights)

            new_overall_score = (
                result.budget_score * effective_weights.get("budget", 0.35) / 100
                + result.location_score * effective_weights.get("location", 0.30) / 100
                + result.feature_score * effective_weights.get("features", 0.25) / 100
                + result.market_score * effective_weights.get("market", 0.10) / 100
            ) * 100

            result.overall_score = round(new_overall_score, 1)

        # Apply feature boosts if provided
        if context.feature_boosts:
            for boost_feature, boost_amount in context.feature_boosts.items():
                if boost_feature in " ".join(result.reasoning).lower():
                    result.overall_score = min(100.0, result.overall_score + boost_amount)

        return result

    def _generate_cache_key(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> str:
        """Generate cache key for scoring result"""
        prop_id = property_data.get("id", str(hash(str(property_data))))
        pref_hash = str(hash(str(sorted(lead_preferences.items()))))
        strategy_name = self._strategy.name if self._strategy else "unknown"
        return f"{strategy_name}:{prop_id}:{pref_hash}"

    def _is_cache_valid(self, cached_result: ScoringResult, cache_ttl: int) -> bool:
        """Check if cached result is still valid"""
        if not cached_result.scoring_timestamp:
            return False

        try:
            cached_time = datetime.fromisoformat(cached_result.scoring_timestamp)
            age_seconds = (datetime.now() - cached_time).total_seconds()
            return age_seconds < cache_ttl
        except Exception:
            return False

    def _update_performance_metrics(self, strategy_name: str, scoring_time: float, success: bool) -> None:
        """Update performance metrics for strategy"""
        if strategy_name not in self._performance_metrics:
            self._performance_metrics[strategy_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "success_rate": 0.0,
            }

        metrics = self._performance_metrics[strategy_name]
        metrics["total_calls"] += 1
        metrics["total_time"] += scoring_time

        if success:
            metrics["successful_calls"] += 1

        metrics["avg_time"] = metrics["total_time"] / metrics["total_calls"]
        metrics["success_rate"] = metrics["successful_calls"] / metrics["total_calls"]

    def _record_strategy_usage(self, property_data: Dict[str, Any], result: ScoringResult) -> None:
        """Record strategy usage for analytics"""
        usage_record = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": self._strategy.name,
            "property_id": property_data.get("id", "unknown"),
            "overall_score": result.overall_score,
            "confidence_level": result.confidence_level.value,
        }

        self._strategy_history.append(usage_record)

        # Keep only recent history (last 1000 entries)
        if len(self._strategy_history) > 1000:
            self._strategy_history = self._strategy_history[-1000:]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all strategies"""
        return self._performance_metrics.copy()

    def get_strategy_usage_stats(self) -> Dict[str, Any]:
        """Get strategy usage statistics"""
        if not self._strategy_history:
            return {}

        # Aggregate statistics
        strategy_counts = {}
        for record in self._strategy_history:
            strategy_name = record["strategy_name"]
            if strategy_name not in strategy_counts:
                strategy_counts[strategy_name] = 0
            strategy_counts[strategy_name] += 1

        return {
            "total_scorings": len(self._strategy_history),
            "strategy_distribution": strategy_counts,
            "recent_activity": self._strategy_history[-10:] if self._strategy_history else [],
        }

    def clear_cache(self) -> None:
        """Clear the scoring cache"""
        self._cache.clear()
        logger.info("Scoring cache cleared")

    def validate_strategy(self, strategy: PropertyScorer) -> Dict[str, Any]:
        """
        Validate a strategy before use

        Args:
            strategy: Strategy to validate

        Returns:
            Validation results
        """
        validation_result = {"is_valid": True, "errors": [], "warnings": [], "metadata": strategy.get_metadata()}

        try:
            # Check if strategy supports required methods
            required_methods = ["calculate_score", "validate_inputs"]
            for method in required_methods:
                if not hasattr(strategy, method):
                    validation_result["errors"].append(f"Missing required method: {method}")

            # Check if strategy can handle basic inputs
            test_property = {"price": 500000, "bedrooms": 3}
            test_preferences = {"budget": 600000}

            try:
                strategy.validate_inputs(test_property, test_preferences)
            except Exception as e:
                validation_result["errors"].append(f"Input validation failed: {e}")

            # Performance check - warm up should complete quickly
            start_time = datetime.now()
            strategy.warm_up()
            warm_up_time = (datetime.now() - start_time).total_seconds()

            if warm_up_time > 5.0:  # More than 5 seconds
                validation_result["warnings"].append(f"Slow warm-up time: {warm_up_time:.2f}s")

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {e}")

        validation_result["is_valid"] = len(validation_result["errors"]) == 0

        return validation_result
