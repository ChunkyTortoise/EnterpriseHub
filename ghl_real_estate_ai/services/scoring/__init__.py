"""
Property Scoring Strategy Pattern Implementation

Enterprise-grade Strategy Pattern for flexible property scoring algorithms.
Supports runtime strategy switching, performance monitoring, and enterprise features.
"""

# Core interfaces and results
from .property_scorer import (
    PropertyScorer,
    TrainableScorer,
    AdaptiveScorer,
    ScoringResult,
    ScoringContext,
    ConfidenceLevel
)

# Concrete strategy implementations
from .basic_scorer import BasicPropertyScorer
from .enhanced_scorer import EnhancedPropertyScorer

# Strategy Pattern context and factory
from .property_matcher_context import PropertyMatcherContext
from .scoring_factory import ScoringFactory, get_scoring_factory, create_strategy

# Convenience exports for common usage patterns
__all__ = [
    # Core interfaces
    'PropertyScorer',
    'TrainableScorer',
    'AdaptiveScorer',
    'ScoringResult',
    'ScoringContext',
    'ConfidenceLevel',

    # Concrete strategies
    'BasicPropertyScorer',
    'EnhancedPropertyScorer',

    # Pattern implementation
    'PropertyMatcherContext',
    'ScoringFactory',

    # Factory functions
    'get_scoring_factory',
    'create_strategy'
]


def create_property_matcher(
    strategy_name: str = "enhanced",
    fallback_strategy: str = "basic",
    enable_caching: bool = False,
    enable_monitoring: bool = True
) -> PropertyMatcherContext:
    """
    Create a complete property matcher with strategy and fallback.

    Convenience function for quick setup of production-ready property matcher.

    Args:
        strategy_name: Primary scoring strategy ('basic', 'enhanced')
        fallback_strategy: Backup strategy for error recovery
        enable_caching: Enable result caching for performance
        enable_monitoring: Enable performance metrics tracking

    Returns:
        Configured PropertyMatcherContext ready for use

    Example:
        >>> matcher = create_property_matcher("enhanced", fallback_strategy="basic")
        >>> result = matcher.score_property(property_data, lead_preferences)
    """
    factory = get_scoring_factory()

    # Create primary and fallback strategies
    primary = factory.create_strategy(strategy_name)
    fallback = factory.create_strategy(fallback_strategy) if fallback_strategy else None

    # Create context with enterprise features
    return PropertyMatcherContext(
        strategy=primary,
        fallback_strategy=fallback,
        enable_performance_monitoring=enable_monitoring,
        enable_caching=enable_caching
    )


def quick_score_property(
    property_data: dict,
    lead_preferences: dict,
    strategy: str = "enhanced"
) -> ScoringResult:
    """
    Quick property scoring with minimal setup.

    Convenience function for one-off scoring without context setup.

    Args:
        property_data: Property details dictionary
        lead_preferences: Lead requirements dictionary
        strategy: Strategy name to use ('basic', 'enhanced')

    Returns:
        ScoringResult with detailed scoring breakdown

    Example:
        >>> result = quick_score_property(property, preferences, "enhanced")
        >>> print(f"Score: {result.overall_score}% ({result.confidence_level.value})")
    """
    scorer = create_strategy(strategy)
    return scorer.calculate_score(property_data, lead_preferences)


def get_strategy_recommendations() -> dict:
    """
    Get strategy selection recommendations for different scenarios.

    Returns:
        Dictionary with scenario-based strategy recommendations
    """
    return {
        'high_volume': {
            'strategy': 'basic',
            'description': 'Fast scoring for 100+ properties',
            'throughput': '1000+ properties/second'
        },
        'balanced': {
            'strategy': 'enhanced',
            'description': 'Balanced accuracy and performance',
            'throughput': '200-500 properties/second'
        },
        'accuracy_focused': {
            'strategy': 'enhanced',
            'description': 'Maximum accuracy with 15-factor analysis',
            'throughput': '200-500 properties/second'
        },
        'real_time': {
            'strategy': 'basic',
            'description': 'Sub-second response time',
            'throughput': '1000+ properties/second'
        }
    }


# Version info
__version__ = "1.0.0"
__author__ = "GHL Real Estate AI Team"
__description__ = "Enterprise property scoring with Strategy Pattern architecture"