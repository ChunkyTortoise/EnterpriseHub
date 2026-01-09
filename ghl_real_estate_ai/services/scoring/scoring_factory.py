"""
Scoring Factory - Strategy Pattern Factory Implementation

Factory class for creating and managing property scoring strategies with
dynamic registration, configuration management, and performance optimization.
"""

from typing import Dict, List, Any, Optional, Type, Callable
import logging
try:
    from .property_scorer import PropertyScorer, ScoringContext
    from .basic_scorer import BasicPropertyScorer
    from .enhanced_scorer import EnhancedPropertyScorer
except ImportError:
    from property_scorer import PropertyScorer, ScoringContext
    from basic_scorer import BasicPropertyScorer
    from enhanced_scorer import EnhancedPropertyScorer


class ScoringFactory:
    """
    Factory for creating and managing property scoring strategies.

    Features:
    - Dynamic strategy registration
    - Configuration-based strategy selection
    - Performance characteristic analysis
    - Strategy validation and health checks
    """

    def __init__(self):
        """Initialize factory with built-in strategies"""
        self._strategies: Dict[str, Type[PropertyScorer]] = {}
        self._strategy_configs: Dict[str, Dict[str, Any]] = {}
        self._strategy_instances: Dict[str, PropertyScorer] = {}
        self._logger = logging.getLogger(__name__)

        # Register built-in strategies
        self._register_builtin_strategies()

    def register_strategy(
        self,
        name: str,
        strategy_class: Type[PropertyScorer],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new scoring strategy.

        Args:
            name: Unique strategy identifier
            strategy_class: PropertyScorer implementation class
            config: Optional configuration parameters
        """
        if not issubclass(strategy_class, PropertyScorer):
            raise ValueError(f"Strategy class must inherit from PropertyScorer")

        self._strategies[name] = strategy_class
        self._strategy_configs[name] = config or {}

        self._logger.info(f"Registered strategy: {name}")

    def create_strategy(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        use_cached: bool = True
    ) -> PropertyScorer:
        """
        Create a strategy instance.

        Args:
            name: Strategy name to create
            config: Optional runtime configuration
            use_cached: Use cached instance if available

        Returns:
            Configured PropertyScorer instance

        Raises:
            ValueError: If strategy name is not registered
        """
        if name not in self._strategies:
            available = list(self._strategies.keys())
            raise ValueError(f"Unknown strategy '{name}'. Available: {available}")

        # Return cached instance if requested and available
        if use_cached and name in self._strategy_instances:
            return self._strategy_instances[name]

        # Merge default config with runtime config
        strategy_config = self._strategy_configs[name].copy()
        if config:
            strategy_config.update(config)

        # Create strategy instance
        strategy_class = self._strategies[name]
        try:
            if strategy_config:
                # Try to pass config to constructor
                strategy_instance = strategy_class(**strategy_config)
            else:
                strategy_instance = strategy_class()

            # Cache instance for reuse
            if use_cached:
                self._strategy_instances[name] = strategy_instance

            self._logger.info(f"Created strategy instance: {name}")
            return strategy_instance

        except Exception as e:
            self._logger.error(f"Failed to create strategy '{name}': {e}")
            raise ValueError(f"Strategy creation failed: {e}")

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategy names"""
        return list(self._strategies.keys())

    def get_strategy_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a strategy.

        Args:
            name: Strategy name

        Returns:
            Dictionary with strategy metadata and characteristics
        """
        if name not in self._strategies:
            raise ValueError(f"Unknown strategy: {name}")

        strategy_class = self._strategies[name]
        config = self._strategy_configs[name]

        # Get performance characteristics from a temporary instance
        try:
            temp_instance = strategy_class()
            characteristics = temp_instance.get_performance_characteristics()
        except:
            characteristics = {'error': 'Unable to determine characteristics'}

        return {
            'name': name,
            'class': strategy_class.__name__,
            'module': strategy_class.__module__,
            'config': config,
            'performance': characteristics,
            'documentation': strategy_class.__doc__ or 'No documentation available'
        }

    def get_all_strategies_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered strategies"""
        return {
            name: self.get_strategy_info(name)
            for name in self._strategies.keys()
        }

    def recommend_strategy(
        self,
        context: ScoringContext,
        property_count: int = 1
    ) -> str:
        """
        Recommend optimal strategy based on context and requirements.

        Args:
            context: Scoring context with preferences and requirements
            property_count: Number of properties to score

        Returns:
            Recommended strategy name
        """
        # High-volume scenarios - prioritize speed
        if property_count > 100 or context.performance_priority == "speed":
            return "basic"

        # Accuracy-focused scenarios - use enhanced features
        elif context.performance_priority == "accuracy":
            return "enhanced"

        # Balanced scenarios - consider urgency
        elif context.urgency_level in ["high", "urgent"]:
            return "basic"  # Fast response

        else:
            return "enhanced"  # Default to enhanced for best user experience

    def create_recommended_strategy(
        self,
        context: ScoringContext,
        property_count: int = 1
    ) -> PropertyScorer:
        """
        Create strategy instance using recommendation engine.

        Args:
            context: Scoring context
            property_count: Number of properties to score

        Returns:
            Optimally configured PropertyScorer instance
        """
        recommended_name = self.recommend_strategy(context, property_count)
        return self.create_strategy(recommended_name)

    def create_strategy_with_fallback(
        self,
        primary_name: str,
        fallback_name: str = "basic",
        primary_config: Optional[Dict[str, Any]] = None,
        fallback_config: Optional[Dict[str, Any]] = None
    ) -> tuple[PropertyScorer, PropertyScorer]:
        """
        Create primary and fallback strategy instances.

        Args:
            primary_name: Primary strategy name
            fallback_name: Fallback strategy name
            primary_config: Primary strategy configuration
            fallback_config: Fallback strategy configuration

        Returns:
            Tuple of (primary_strategy, fallback_strategy)
        """
        primary_strategy = self.create_strategy(primary_name, primary_config)
        fallback_strategy = self.create_strategy(fallback_name, fallback_config)

        return primary_strategy, fallback_strategy

    def validate_strategy(self, name: str) -> Dict[str, Any]:
        """
        Validate that a strategy is working correctly.

        Args:
            name: Strategy name to validate

        Returns:
            Validation results with status and details
        """
        validation_result = {
            'strategy': name,
            'status': 'unknown',
            'errors': [],
            'warnings': [],
            'performance': {}
        }

        try:
            # Create strategy instance
            strategy = self.create_strategy(name, use_cached=False)

            # Test basic functionality
            test_property = {
                'id': 'test-001',
                'price': 500000,
                'address': {'neighborhood': 'Test Area'},
                'bedrooms': 3,
                'bathrooms': 2,
                'sqft': 2000
            }

            test_preferences = {
                'budget': 600000,
                'location': ['Test Area'],
                'bedrooms': 3
            }

            # Validate inputs
            if not strategy.validate_inputs(test_property, test_preferences):
                validation_result['errors'].append("Input validation failed")

            # Test scoring
            import time
            start_time = time.time()
            result = strategy.calculate_score(test_property, test_preferences)
            execution_time = time.time() - start_time

            # Validate result structure
            if not hasattr(result, 'overall_score'):
                validation_result['errors'].append("Result missing overall_score")
            elif not 0 <= result.overall_score <= 100:
                validation_result['errors'].append(f"Invalid overall_score: {result.overall_score}")

            if not hasattr(result, 'reasoning') or not result.reasoning:
                validation_result['warnings'].append("No reasoning provided")

            # Performance check
            validation_result['performance'] = {
                'execution_time_ms': round(execution_time * 1000, 2),
                'characteristics': strategy.get_performance_characteristics()
            }

            # Determine overall status
            if validation_result['errors']:
                validation_result['status'] = 'failed'
            elif validation_result['warnings']:
                validation_result['status'] = 'warning'
            else:
                validation_result['status'] = 'passed'

        except Exception as e:
            validation_result['status'] = 'error'
            validation_result['errors'].append(f"Validation exception: {str(e)}")

        return validation_result

    def validate_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Validate all registered strategies"""
        return {
            name: self.validate_strategy(name)
            for name in self._strategies.keys()
        }

    def get_default_strategy(self) -> str:
        """Get the default strategy name"""
        # Prefer enhanced if available, fallback to basic
        if "enhanced" in self._strategies:
            return "enhanced"
        elif "basic" in self._strategies:
            return "basic"
        else:
            available = list(self._strategies.keys())
            return available[0] if available else None

    def clear_strategy_cache(self) -> None:
        """Clear cached strategy instances"""
        self._strategy_instances.clear()
        self._logger.info("Strategy instance cache cleared")

    def _register_builtin_strategies(self) -> None:
        """Register built-in scoring strategies"""
        # Basic rule-based scorer
        self.register_strategy(
            name="basic",
            strategy_class=BasicPropertyScorer,
            config={
                'budget_weight': 0.35,
                'location_weight': 0.30,
                'feature_weight': 0.25,
                'market_weight': 0.10
            }
        )

        # Enhanced multi-factor scorer
        self.register_strategy(
            name="enhanced",
            strategy_class=EnhancedPropertyScorer,
            config={}
        )

        # Optimized basic scorer for high-volume scenarios
        self.register_strategy(
            name="basic_fast",
            strategy_class=BasicPropertyScorer,
            config={
                'budget_weight': 0.50,  # Simplified weighting for speed
                'location_weight': 0.30,
                'feature_weight': 0.15,
                'market_weight': 0.05
            }
        )

        # Accuracy-focused enhanced scorer
        self.register_strategy(
            name="enhanced_accurate",
            strategy_class=EnhancedPropertyScorer,
            config={}
        )

        self._logger.info(f"Registered {len(self._strategies)} built-in strategies")


# Global factory instance for easy access
_global_factory = None


def get_scoring_factory() -> ScoringFactory:
    """
    Get the global scoring factory instance.

    Returns:
        Global ScoringFactory instance
    """
    global _global_factory
    if _global_factory is None:
        _global_factory = ScoringFactory()
    return _global_factory


def create_strategy(name: str, config: Optional[Dict[str, Any]] = None) -> PropertyScorer:
    """
    Convenience function to create a strategy using global factory.

    Args:
        name: Strategy name
        config: Optional configuration

    Returns:
        PropertyScorer instance
    """
    factory = get_scoring_factory()
    return factory.create_strategy(name, config)