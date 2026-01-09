"""
Property Scoring Strategy Pattern Package
Enterprise-grade property scoring with flexible algorithms

This package implements the Strategy Pattern for property scoring,
providing a clean, extensible architecture for multiple scoring algorithms.

Key Features:
- Strategy Pattern for algorithm flexibility
- Factory Pattern for strategy management
- SOLID principles compliance
- Comprehensive testing support
- Performance monitoring
- Legacy compatibility

Quick Start:
-----------
```python
from property_scoring import PropertyMatcherContext, ScoringFactory

# Create factory and get strategy
factory = ScoringFactory()
strategy = factory.get_default_strategy()

# Create context and score properties
context = PropertyMatcherContext(strategy)
result = context.score_property(property_data, lead_preferences)

print(f"Score: {result.overall_score}%")
print(f"Reasoning: {result.reasoning}")
```

Available Strategies:
--------------------
- basic: Fast rule-based scoring
- enhanced: Advanced algorithms with market analysis
- ml: Machine learning-enhanced scoring (requires training)
- adaptive: Learning-based personalization

Factory Usage:
--------------
```python
# Get recommended strategy
strategy_name = factory.recommend_strategy({
    'performance_priority': 'accuracy',
    'complexity_tolerance': 'high'
})

# Create strategy with configuration
strategy = factory.create_strategy('enhanced', market_data=market_data)
```

Integration with Legacy Code:
----------------------------
The package provides seamless integration with existing PropertyMatcher code:

```python
# Legacy function enhancement
def generate_property_matches(lead_context: Dict) -> List[Dict]:
    factory = ScoringFactory()
    context = PropertyMatcherContext(factory.get_default_strategy())

    # Score properties
    scored_properties = context.score_multiple_properties(
        properties=available_properties,
        lead_preferences=lead_context['extracted_preferences']
    )

    # Convert to legacy format (automatic compatibility)
    return [prop for prop in scored_properties]
```
"""

from .interfaces import (
    PropertyScorer,
    ScoringResult,
    ConfidenceLevel,
    TrainableScorer,
    AdaptiveScorer,
    ScoringContext,
    LeadPreferences
)

from .strategies import (
    BasicPropertyScorer,
    EnhancedPropertyScorer
)

from .context import (
    PropertyMatcherContext,
    ScoringFactory,
    get_scoring_factory,
    create_strategy,
    get_default_strategy
)

# Version information
__version__ = "1.0.0"
__author__ = "GHL Real Estate AI Team"
__email__ = "ai-team@ghlrealestate.com"

# Package metadata
__title__ = "Property Scoring Strategy Pattern"
__description__ = "Enterprise-grade property scoring with flexible algorithms"
__url__ = "https://github.com/ghl/real-estate-ai"

# Public API
__all__ = [
    # Core interfaces
    'PropertyScorer',
    'ScoringResult',
    'ConfidenceLevel',
    'TrainableScorer',
    'AdaptiveScorer',
    'ScoringContext',
    'LeadPreferences',

    # Strategy implementations
    'BasicPropertyScorer',
    'EnhancedPropertyScorer',

    # Context and factory
    'PropertyMatcherContext',
    'ScoringFactory',
    'get_scoring_factory',
    'create_strategy',
    'get_default_strategy',

    # Package metadata
    '__version__',
    '__author__',
    '__email__'
]


def get_package_info() -> dict:
    """Get comprehensive package information"""
    factory = get_scoring_factory()
    return {
        'version': __version__,
        'title': __title__,
        'description': __description__,
        'available_strategies': [s['name'] for s in factory.list_strategies()],
        'default_strategy': factory._default_strategy_name,
        'features': [
            'Strategy Pattern Architecture',
            'Multiple Scoring Algorithms',
            'Factory Pattern Management',
            'SOLID Principles Compliance',
            'Performance Monitoring',
            'Legacy Compatibility',
            'Comprehensive Testing',
            'Error Handling & Resilience'
        ]
    }


def validate_installation() -> dict:
    """Validate package installation and dependencies"""
    results = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'strategy_validation': {}
    }

    try:
        # Test factory creation
        factory = get_scoring_factory()

        # Validate all strategies
        validation_results = factory.validate_all_strategies()
        results['strategy_validation'] = validation_results

        # Check for any failed validations
        failed_strategies = [
            name for name, result in validation_results.items()
            if not result['is_valid']
        ]

        if failed_strategies:
            results['warnings'].append(
                f"Some strategies failed validation: {failed_strategies}"
            )

        # Test basic functionality
        try:
            strategy = factory.get_default_strategy()
            context = PropertyMatcherContext(strategy)

            # Test scoring with minimal data
            test_result = context.score_property(
                {'price': 500000, 'bedrooms': 3},
                {'budget': 600000}
            )

            if not hasattr(test_result, 'overall_score'):
                results['errors'].append("Basic scoring test failed")

        except Exception as e:
            results['errors'].append(f"Basic functionality test failed: {e}")

    except Exception as e:
        results['status'] = 'error'
        results['errors'].append(f"Package validation failed: {e}")

    if results['errors']:
        results['status'] = 'error'
    elif results['warnings']:
        results['status'] = 'warning'

    return results


# Initialize and validate on import
try:
    _validation_results = validate_installation()
    if _validation_results['status'] == 'error':
        import warnings
        warnings.warn(
            f"Property Scoring package validation failed: {_validation_results['errors']}",
            UserWarning
        )
except Exception as e:
    import warnings
    warnings.warn(
        f"Property Scoring package initialization failed: {e}",
        UserWarning
    )