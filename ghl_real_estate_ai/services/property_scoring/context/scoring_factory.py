"""
Scoring Strategy Factory
Factory Pattern implementation for creating and managing scoring strategies
"""

import logging
from typing import Any, Dict, List, Optional, Type

from ..interfaces.property_scorer import AdaptiveScorer, PropertyScorer, TrainableScorer
from ..strategies.basic_property_scorer import BasicPropertyScorer
from ..strategies.enhanced_property_scorer import EnhancedPropertyScorer

logger = logging.getLogger(__name__)


class ScoringFactory:
    """
    Factory for creating and managing property scoring strategies

    This factory provides a centralized way to create, configure,
    and manage different scoring strategies while maintaining
    loose coupling and easy extensibility.

    Features:
    - Strategy registration and discovery
    - Configuration management
    - Lazy loading for performance
    - Validation and error handling
    - Strategy recommendations
    """

    def __init__(self):
        """Initialize the scoring factory"""
        self._registered_strategies: Dict[str, Type[PropertyScorer]] = {}
        self._strategy_instances: Dict[str, PropertyScorer] = {}
        self._strategy_configs: Dict[str, Dict[str, Any]] = {}
        self._default_strategy_name: Optional[str] = None

        # Register built-in strategies
        self._register_builtin_strategies()

    def _register_builtin_strategies(self) -> None:
        """Register built-in scoring strategies"""
        self.register_strategy(
            name="basic",
            strategy_class=BasicPropertyScorer,
            config={
                "description": "Simple rule-based scoring",
                "performance": "fast",
                "complexity": "low",
                "features": ["budget_matching", "basic_location", "simple_features"],
            },
        )

        self.register_strategy(
            name="enhanced",
            strategy_class=EnhancedPropertyScorer,
            config={
                "description": "Advanced rule-based scoring with market analysis",
                "performance": "medium",
                "complexity": "medium",
                "features": ["advanced_budget", "geographic_analysis", "market_timing"],
            },
        )

        # Set default strategy
        self._default_strategy_name = "enhanced"

    def register_strategy(
        self, name: str, strategy_class: Type[PropertyScorer], config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new scoring strategy

        Args:
            name: Unique name for the strategy
            strategy_class: PropertyScorer class
            config: Optional configuration for the strategy

        Raises:
            ValueError: If strategy name is already registered or class is invalid
        """
        if name in self._registered_strategies:
            raise ValueError(f"Strategy '{name}' is already registered")

        if not issubclass(strategy_class, PropertyScorer):
            raise ValueError("Strategy class must inherit from PropertyScorer")

        self._registered_strategies[name] = strategy_class
        self._strategy_configs[name] = config or {}

        logger.info(f"Registered strategy: {name}")

    def create_strategy(self, name: str, **kwargs) -> PropertyScorer:
        """
        Create a strategy instance

        Args:
            name: Name of the registered strategy
            **kwargs: Additional arguments for strategy constructor

        Returns:
            Configured PropertyScorer instance

        Raises:
            ValueError: If strategy name is not registered
        """
        if name not in self._registered_strategies:
            available = list(self._registered_strategies.keys())
            raise ValueError(f"Strategy '{name}' not registered. Available: {available}")

        strategy_class = self._registered_strategies[name]
        config = self._strategy_configs[name]

        try:
            # Merge config with kwargs
            init_args = config.copy()
            init_args.update(kwargs)

            # Remove non-constructor arguments
            non_constructor_args = ["description", "performance", "complexity", "features"]
            for arg in non_constructor_args:
                init_args.pop(arg, None)

            # Create strategy instance
            if name == "basic":
                strategy = strategy_class()
            elif name == "enhanced":
                market_data = init_args.pop("market_data", None)
                strategy = strategy_class(market_data=market_data)
            else:
                # For custom strategies, pass all remaining args
                strategy = strategy_class(**init_args)

            logger.info(f"Created strategy instance: {name}")
            return strategy

        except Exception as e:
            logger.error(f"Failed to create strategy '{name}': {e}")
            raise

    def get_strategy(self, name: str, cached: bool = True) -> PropertyScorer:
        """
        Get a strategy instance (cached by default)

        Args:
            name: Strategy name
            cached: Whether to use cached instance

        Returns:
            PropertyScorer instance
        """
        if cached and name in self._strategy_instances:
            return self._strategy_instances[name]

        strategy = self.create_strategy(name)

        if cached:
            self._strategy_instances[name] = strategy

        return strategy

    def get_default_strategy(self) -> PropertyScorer:
        """Get the default strategy instance"""
        if not self._default_strategy_name:
            raise ValueError("No default strategy configured")

        return self.get_strategy(self._default_strategy_name)

    def set_default_strategy(self, name: str) -> None:
        """
        Set the default strategy

        Args:
            name: Name of registered strategy to use as default

        Raises:
            ValueError: If strategy name is not registered
        """
        if name not in self._registered_strategies:
            available = list(self._registered_strategies.keys())
            raise ValueError(f"Strategy '{name}' not registered. Available: {available}")

        self._default_strategy_name = name
        logger.info(f"Default strategy set to: {name}")

    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        List all registered strategies with their metadata

        Returns:
            List of strategy information dictionaries
        """
        strategies = []

        for name, strategy_class in self._registered_strategies.items():
            config = self._strategy_configs[name]

            strategy_info = {
                "name": name,
                "class": strategy_class.__name__,
                "module": strategy_class.__module__,
                "is_default": name == self._default_strategy_name,
                "is_trainable": issubclass(strategy_class, TrainableScorer),
                "is_adaptive": issubclass(strategy_class, AdaptiveScorer),
                **config,
            }

            strategies.append(strategy_info)

        return strategies

    def recommend_strategy(self, requirements: Dict[str, Any]) -> str:
        """
        Recommend optimal strategy based on requirements

        Args:
            requirements: Dictionary with requirements like:
                - performance_priority: 'speed' or 'accuracy'
                - complexity_tolerance: 'low', 'medium', 'high'
                - features_needed: List of required features
                - data_availability: 'limited' or 'rich'

        Returns:
            Name of recommended strategy
        """
        performance_priority = requirements.get("performance_priority", "balanced")
        complexity_tolerance = requirements.get("complexity_tolerance", "medium")
        features_needed = requirements.get("features_needed", [])
        data_availability = requirements.get("data_availability", "medium")

        scores = {}

        for name, config in self._strategy_configs.items():
            score = 0

            # Performance scoring
            strategy_performance = config.get("performance", "medium")
            if performance_priority == "speed":
                if strategy_performance == "fast":
                    score += 3
                elif strategy_performance == "medium":
                    score += 1
            elif performance_priority == "accuracy":
                if strategy_performance == "slow":
                    score += 3
                elif strategy_performance == "medium":
                    score += 2
                elif strategy_performance == "fast":
                    score += 1

            # Complexity scoring
            strategy_complexity = config.get("complexity", "medium")
            if complexity_tolerance == "low" and strategy_complexity == "low":
                score += 2
            elif complexity_tolerance == "medium" and strategy_complexity in ["low", "medium"]:
                score += 2
            elif complexity_tolerance == "high":
                score += 1  # All complexities acceptable

            # Feature matching
            strategy_features = config.get("features", [])
            feature_matches = len(set(features_needed) & set(strategy_features))
            score += feature_matches

            # Data requirements
            if data_availability == "limited" and strategy_complexity == "low":
                score += 1
            elif data_availability == "rich" and strategy_complexity == "high":
                score += 1

            scores[name] = score

        # Return strategy with highest score
        recommended = max(scores.items(), key=lambda x: x[1])
        logger.info(f"Recommended strategy: {recommended[0]} (score: {recommended[1]})")

        return recommended[0]

    def create_strategy_chain(self, strategy_names: List[str]) -> List[PropertyScorer]:
        """
        Create a chain of strategies for comparison or ensemble methods

        Args:
            strategy_names: List of strategy names to chain

        Returns:
            List of strategy instances
        """
        strategies = []

        for name in strategy_names:
            try:
                strategy = self.get_strategy(name)
                strategies.append(strategy)
            except Exception as e:
                logger.error(f"Failed to create strategy '{name}' in chain: {e}")
                continue

        return strategies

    def validate_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all registered strategies

        Returns:
            Dictionary mapping strategy names to validation results
        """
        results = {}

        for name in self._registered_strategies.keys():
            try:
                strategy = self.create_strategy(name)

                # Basic validation
                validation_result = {"is_valid": True, "errors": [], "warnings": []}

                # Test strategy creation
                test_property = {"price": 500000, "bedrooms": 3}
                test_preferences = {"budget": 600000}

                try:
                    strategy.validate_inputs(test_property, test_preferences)
                except Exception as e:
                    validation_result["errors"].append(f"Input validation failed: {e}")

                # Test scoring
                try:
                    result = strategy.calculate_score(test_property, test_preferences)
                    if not hasattr(result, "overall_score"):
                        validation_result["errors"].append("Invalid scoring result format")
                except Exception as e:
                    validation_result["errors"].append(f"Scoring failed: {e}")

                validation_result["is_valid"] = len(validation_result["errors"]) == 0
                results[name] = validation_result

            except Exception as e:
                results[name] = {"is_valid": False, "errors": [f"Strategy creation failed: {e}"], "warnings": []}

        return results

    def clear_cache(self) -> None:
        """Clear all cached strategy instances"""
        # Clean up strategies
        for strategy in self._strategy_instances.values():
            try:
                strategy.cleanup()
            except Exception as e:
                logger.warning(f"Strategy cleanup failed: {e}")

        self._strategy_instances.clear()
        logger.info("Strategy cache cleared")

    def get_strategy_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a strategy

        Args:
            name: Strategy name

        Returns:
            Strategy information dictionary
        """
        if name not in self._registered_strategies:
            raise ValueError(f"Strategy '{name}' not registered")

        strategy_class = self._registered_strategies[name]
        config = self._strategy_configs[name]

        return {
            "name": name,
            "class": strategy_class.__name__,
            "module": strategy_class.__module__,
            "config": config,
            "is_default": name == self._default_strategy_name,
            "is_trainable": issubclass(strategy_class, TrainableScorer),
            "is_adaptive": issubclass(strategy_class, AdaptiveScorer),
            "docstring": strategy_class.__doc__,
        }

    def export_configurations(self) -> Dict[str, Any]:
        """
        Export all strategy configurations

        Returns:
            Dictionary with all configurations
        """
        return {
            "strategies": self._strategy_configs.copy(),
            "default_strategy": self._default_strategy_name,
            "registered_count": len(self._registered_strategies),
        }

    def import_configurations(self, config: Dict[str, Any]) -> None:
        """
        Import strategy configurations

        Args:
            config: Configuration dictionary to import
        """
        if "default_strategy" in config:
            default = config["default_strategy"]
            if default in self._registered_strategies:
                self._default_strategy_name = default

        if "strategies" in config:
            # Update existing configurations
            for name, strategy_config in config["strategies"].items():
                if name in self._strategy_configs:
                    self._strategy_configs[name].update(strategy_config)

        logger.info("Imported strategy configurations")


# Global factory instance
_factory_instance: Optional[ScoringFactory] = None


def get_scoring_factory() -> ScoringFactory:
    """Get global scoring factory instance (singleton pattern)"""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = ScoringFactory()
    return _factory_instance


def create_strategy(name: str, **kwargs) -> PropertyScorer:
    """Convenience function to create a strategy"""
    factory = get_scoring_factory()
    return factory.create_strategy(name, **kwargs)


def get_default_strategy() -> PropertyScorer:
    """Convenience function to get default strategy"""
    factory = get_scoring_factory()
    return factory.get_default_strategy()
