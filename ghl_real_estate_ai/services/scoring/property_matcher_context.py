"""
Property Matcher Context - Strategy Pattern Implementation

Context class that orchestrates property scoring strategies with enterprise-grade
features including fallback handling, performance monitoring, and batch processing.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Union

try:
    from .property_scorer import PropertyScorer, ScoringContext, ScoringResult
except ImportError:
    from property_scorer import PropertyScorer, ScoringContext, ScoringResult


class PropertyMatcherContext:
    """
    Context class for the Strategy Pattern property scoring system.

    Provides enterprise features:
    - Runtime strategy switching
    - Automatic fallback on failures
    - Performance monitoring
    - Batch processing optimization
    - Caching layer integration
    """

    def __init__(
        self,
        strategy: PropertyScorer,
        fallback_strategy: Optional[PropertyScorer] = None,
        enable_performance_monitoring: bool = True,
        enable_caching: bool = False,
    ):
        """
        Initialize the property matcher context.

        Args:
            strategy: Primary scoring strategy
            fallback_strategy: Backup strategy for error recovery
            enable_performance_monitoring: Track performance metrics
            enable_caching: Enable result caching (requires cache backend)
        """
        self._strategy = strategy
        self._fallback_strategy = fallback_strategy
        self._enable_monitoring = enable_performance_monitoring
        self._enable_caching = enable_caching

        # Performance tracking
        self._performance_metrics = {
            "total_scores": 0,
            "total_time": 0.0,
            "errors": 0,
            "fallbacks_used": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Setup logging
        self._logger = logging.getLogger(__name__)

        # Cache backend (would be Redis in production)
        self._cache = {} if enable_caching else None

    def set_strategy(self, strategy: PropertyScorer) -> None:
        """
        Switch to a different scoring strategy at runtime.

        Args:
            strategy: New scoring strategy to use
        """
        self._strategy = strategy
        self._logger.info(f"Switched to strategy: {strategy.get_strategy_name()}")

    def score_property(
        self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any], context: Optional[ScoringContext] = None
    ) -> ScoringResult:
        """
        Score a single property using the current strategy.

        Args:
            property_data: Property details
            lead_preferences: Lead requirements and preferences
            context: Additional scoring context and configuration

        Returns:
            ScoringResult with detailed scoring breakdown

        Raises:
            ValueError: If both primary and fallback strategies fail
        """
        start_time = time.time() if self._enable_monitoring else None

        # Check cache first
        cache_key = self._generate_cache_key(property_data, lead_preferences)
        if self._enable_caching and cache_key in self._cache:
            self._performance_metrics["cache_hits"] += 1
            return self._cache[cache_key]

        try:
            # Attempt scoring with primary strategy
            result = self._strategy.calculate_score(property_data, lead_preferences)

            # Cache the result
            if self._enable_caching:
                self._cache[cache_key] = result
                self._performance_metrics["cache_misses"] += 1

            # Update performance metrics
            if self._enable_monitoring:
                self._update_performance_metrics(start_time, success=True)

            return result

        except Exception as primary_error:
            self._logger.warning(f"Primary strategy {self._strategy.get_strategy_name()} failed: {primary_error}")
            self._performance_metrics["errors"] += 1

            # Attempt fallback strategy
            if self._fallback_strategy:
                try:
                    self._logger.info(f"Using fallback strategy: {self._fallback_strategy.get_strategy_name()}")
                    result = self._fallback_strategy.calculate_score(property_data, lead_preferences)

                    # Cache fallback result with lower TTL
                    if self._enable_caching:
                        self._cache[cache_key] = result

                    self._performance_metrics["fallbacks_used"] += 1
                    if self._enable_monitoring:
                        self._update_performance_metrics(start_time, success=True, used_fallback=True)

                    return result

                except Exception as fallback_error:
                    self._logger.error(f"Fallback strategy also failed: {fallback_error}")

            # Both strategies failed
            if self._enable_monitoring:
                self._update_performance_metrics(start_time, success=False)

            raise ValueError(f"All scoring strategies failed. Primary: {primary_error}")

    def score_multiple_properties(
        self,
        properties: List[Dict[str, Any]],
        lead_preferences: Dict[str, Any],
        context: Optional[ScoringContext] = None,
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Score multiple properties with optimized batch processing.

        Args:
            properties: List of property data dictionaries
            lead_preferences: Lead requirements and preferences
            context: Scoring configuration context
            max_workers: Maximum concurrent workers for parallel processing

        Returns:
            List of properties with added scoring results, sorted by score
        """
        if not properties:
            return []

        scored_properties = []
        use_parallel = len(properties) > 10 and max_workers > 1

        if use_parallel:
            # Parallel processing for large batches
            scored_properties = self._score_batch_parallel(properties, lead_preferences, context, max_workers)
        else:
            # Sequential processing for small batches
            scored_properties = self._score_batch_sequential(properties, lead_preferences, context)

        # Sort by overall score (highest first)
        scored_properties.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        # Apply context filters if specified
        if context:
            scored_properties = self._apply_context_filters(scored_properties, context)

        return scored_properties

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for monitoring and optimization.

        Returns:
            Dictionary with performance statistics
        """
        metrics = self._performance_metrics.copy()

        if metrics["total_scores"] > 0:
            metrics["average_time_per_score"] = metrics["total_time"] / metrics["total_scores"]
            metrics["error_rate"] = metrics["errors"] / metrics["total_scores"]
            metrics["fallback_rate"] = metrics["fallbacks_used"] / metrics["total_scores"]

        if self._enable_caching and metrics["cache_hits"] + metrics["cache_misses"] > 0:
            metrics["cache_hit_rate"] = metrics["cache_hits"] / (metrics["cache_hits"] + metrics["cache_misses"])

        metrics["current_strategy"] = self._strategy.get_strategy_name()
        metrics["fallback_available"] = self._fallback_strategy is not None

        return metrics

    def reset_performance_metrics(self) -> None:
        """Reset performance tracking metrics"""
        self._performance_metrics = {
            "total_scores": 0,
            "total_time": 0.0,
            "errors": 0,
            "fallbacks_used": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def clear_cache(self) -> None:
        """Clear the scoring results cache"""
        if self._cache:
            self._cache.clear()
            self._logger.info("Scoring cache cleared")

    def _score_batch_sequential(
        self, properties: List[Dict[str, Any]], lead_preferences: Dict[str, Any], context: Optional[ScoringContext]
    ) -> List[Dict[str, Any]]:
        """Score properties sequentially"""
        scored_properties = []

        for property_data in properties:
            try:
                scoring_result = self.score_property(property_data, lead_preferences, context)

                # Merge scoring result with property data
                scored_property = property_data.copy()
                scored_property.update(
                    {
                        "overall_score": scoring_result.overall_score,
                        "confidence_level": scoring_result.confidence_level.value,
                        "budget_match": scoring_result.budget_match > 80,
                        "location_match": scoring_result.location_match > 80,
                        "features_match": scoring_result.feature_match > 80,
                        "match_reasons": scoring_result.reasoning,
                        "scoring_metadata": scoring_result.metadata,
                    }
                )

                scored_properties.append(scored_property)

            except Exception as e:
                self._logger.warning(f"Failed to score property {property_data.get('id', 'unknown')}: {e}")
                # Include property with default score for transparency
                scored_property = property_data.copy()
                scored_property.update(
                    {
                        "overall_score": 0,
                        "confidence_level": "low",
                        "budget_match": False,
                        "location_match": False,
                        "features_match": False,
                        "match_reasons": ["Scoring temporarily unavailable"],
                        "scoring_metadata": {"error": str(e)},
                    }
                )
                scored_properties.append(scored_property)

        return scored_properties

    def _score_batch_parallel(
        self,
        properties: List[Dict[str, Any]],
        lead_preferences: Dict[str, Any],
        context: Optional[ScoringContext],
        max_workers: int,
    ) -> List[Dict[str, Any]]:
        """Score properties in parallel using thread pool"""
        scored_properties = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scoring tasks
            future_to_property = {
                executor.submit(self.score_property, prop, lead_preferences, context): prop for prop in properties
            }

            # Collect results as they complete
            for future in as_completed(future_to_property):
                property_data = future_to_property[future]

                try:
                    scoring_result = future.result()

                    # Merge scoring result with property data
                    scored_property = property_data.copy()
                    scored_property.update(
                        {
                            "overall_score": scoring_result.overall_score,
                            "confidence_level": scoring_result.confidence_level.value,
                            "budget_match": scoring_result.budget_match > 80,
                            "location_match": scoring_result.location_match > 80,
                            "features_match": scoring_result.feature_match > 80,
                            "match_reasons": scoring_result.reasoning,
                            "scoring_metadata": scoring_result.metadata,
                        }
                    )

                    scored_properties.append(scored_property)

                except Exception as e:
                    self._logger.warning(f"Parallel scoring failed for property: {e}")
                    # Include property with default score
                    scored_property = property_data.copy()
                    scored_property.update(
                        {
                            "overall_score": 0,
                            "confidence_level": "low",
                            "budget_match": False,
                            "location_match": False,
                            "features_match": False,
                            "match_reasons": ["Parallel scoring failed"],
                            "scoring_metadata": {"error": str(e)},
                        }
                    )
                    scored_properties.append(scored_property)

        return scored_properties

    def _apply_context_filters(self, properties: List[Dict[str, Any]], context: ScoringContext) -> List[Dict[str, Any]]:
        """Apply context-based filtering"""
        filtered = properties

        # Apply minimum confidence filter
        if context.min_confidence > 0:
            filtered = [p for p in filtered if p.get("overall_score", 0) >= context.min_confidence]

        # Apply maximum properties limit
        if context.max_properties > 0:
            filtered = filtered[: context.max_properties]

        return filtered

    def _generate_cache_key(self, property_data: Dict[str, Any], lead_preferences: Dict[str, Any]) -> str:
        """Generate cache key for property/preference combination"""
        property_id = property_data.get("id", str(hash(str(property_data))))
        preferences_hash = str(hash(str(sorted(lead_preferences.items()))))
        strategy_name = self._strategy.get_strategy_name()

        return f"{strategy_name}:{property_id}:{preferences_hash}"

    def _update_performance_metrics(
        self, start_time: Optional[float], success: bool, used_fallback: bool = False
    ) -> None:
        """Update performance tracking metrics"""
        if not self._enable_monitoring or start_time is None:
            return

        execution_time = time.time() - start_time

        self._performance_metrics["total_scores"] += 1
        self._performance_metrics["total_time"] += execution_time

        if not success:
            self._performance_metrics["errors"] += 1

        if used_fallback:
            self._performance_metrics["fallbacks_used"] += 1
