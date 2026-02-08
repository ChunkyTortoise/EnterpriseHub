"""
Market Registry for Multi-Market Geographic Expansion

Centralized registry for managing market configurations and services across
multiple geographic markets. Supports dynamic market discovery and service instantiation.
"""

import os

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base_market_service import BaseMarketService
from .concrete_services import (
    AustinMarketService,
    DallasMarketService,
    HoustonMarketService,
    RanchoCucamongaMarketService,
    SanAntonioMarketService,
)

logger = logging.getLogger(__name__)


class MarketRegistry:
    """
    Centralized registry for multi-market expansion.

    Manages market configurations, service discovery, and instantiation
    for geographic market expansion.
    """

    def __init__(self):
        self.markets: Dict[str, Dict[str, Any]] = {}
        self.services: Dict[str, BaseMarketService] = {}
        self.config_dir = Path(__file__).parent.parent / "config" / "markets"

        # Service mapping
        self.service_classes: Dict[str, Type[BaseMarketService]] = {
            "austin": AustinMarketService,
            "dallas": DallasMarketService,
            "houston": HoustonMarketService,
            "san_antonio": SanAntonioMarketService,
            "rancho_cucamonga": RanchoCucamongaMarketService,
        }

        self._load_market_configurations()
        logger.info(f"MarketRegistry initialized with {len(self.markets)} markets")

    def _load_market_configurations(self) -> None:
        """Load all market configurations from YAML files"""
        if not YAML_AVAILABLE:
            logger.warning("PyYAML not installed. Market configurations cannot be loaded.")
            return

        if not self.config_dir.exists():
            logger.warning(f"Market config directory not found: {self.config_dir}")
            return

        config_files = list(self.config_dir.glob("*.yaml"))

        for config_file in config_files:
            market_id = config_file.stem
            try:
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)

                # Validate configuration
                validation_warnings = self._validate_market_config(config_data)
                if validation_warnings:
                    logger.warning(f"Market config warnings for {market_id}: {validation_warnings}")

                self.markets[market_id] = config_data
                logger.info(f"Loaded market configuration: {market_id}")

            except Exception as e:
                logger.error(f"Failed to load market config {config_file}: {str(e)}")

    def _validate_market_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate market configuration completeness"""
        warnings = []

        # Check for required sections
        required_sections = ["market_name", "region", "neighborhoods", "employers"]
        for section in required_sections:
            if section not in config:
                warnings.append(f"Missing required section: {section}")

        # Validate neighborhood data completeness
        neighborhoods = config.get("neighborhoods", [])
        required_appeal_scores = {
            "value_appeal",
            "luxury_appeal",
            "executive_appeal",
            "commute_appeal",
            "family_appeal",
            "startup_appeal",
            "tech_appeal",
            "business_appeal",
            "arts_appeal",
            "convenience_appeal",
            "lifestyle_appeal",
            "sports_appeal",
            "culture_appeal",
            "growth_appeal",
            "healthcare_appeal",
            "military_appeal",
            "tourism_appeal",
            "sustainability_appeal",
        }

        valid_neighborhood_names = set(n.get("name", "") for n in neighborhoods)

        for neighborhood in neighborhoods:
            neighborhood_name = neighborhood.get("name", "Unknown")
            appeal_scores = set(neighborhood.get("appeal_scores", {}).keys())
            missing_appeals = required_appeal_scores - appeal_scores

            if missing_appeals and len(missing_appeals) < len(
                required_appeal_scores
            ):  # Only warn if partially complete
                warnings.append(f"Neighborhood {neighborhood_name} missing appeal scores: {missing_appeals}")

        # Validate employer neighborhood references
        employers = config.get("employers", [])
        for employer in employers:
            employer_name = employer.get("name", "Unknown")
            employer_neighborhoods = set(employer.get("neighborhoods", []))
            invalid_neighborhoods = employer_neighborhoods - valid_neighborhood_names

            if invalid_neighborhoods:
                warnings.append(f"Employer {employer_name} references invalid neighborhoods: {invalid_neighborhoods}")

        return warnings

    def list_markets(self) -> List[str]:
        """Get list of available market IDs"""
        return list(self.markets.keys())

    def get_market_config(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific market"""
        return self.markets.get(market_id)

    def get_market_service(self, market_id: str) -> Optional[BaseMarketService]:
        """Get or create market service instance"""
        if market_id in self.services:
            return self.services[market_id]

        if market_id not in self.markets:
            logger.error(f"Unknown market: {market_id}")
            return None

        service_class = self.service_classes.get(market_id)
        if not service_class:
            logger.error(f"No service class defined for market: {market_id}")
            return None

        try:
            market_config = self.markets[market_id]
            service = service_class(market_config)
            self.services[market_id] = service
            logger.info(f"Created market service for {market_id}")
            return service

        except Exception as e:
            logger.error(f"Failed to create market service for {market_id}: {str(e)}")
            return None

    def get_all_market_services(self) -> Dict[str, BaseMarketService]:
        """Get all available market services"""
        services = {}
        for market_id in self.markets.keys():
            service = self.get_market_service(market_id)
            if service:
                services[market_id] = service
        return services

    def register_market(self, market_id: str, config: Dict[str, Any], service_class: Type[BaseMarketService]) -> bool:
        """Dynamically register a new market"""
        try:
            # Validate configuration
            validation_warnings = self._validate_market_config(config)
            if validation_warnings:
                logger.warning(f"Registration warnings for {market_id}: {validation_warnings}")

            self.markets[market_id] = config
            self.service_classes[market_id] = service_class

            logger.info(f"Registered new market: {market_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register market {market_id}: {str(e)}")
            return False

    def get_market_summary(self) -> Dict[str, Any]:
        """Get summary of all markets and their status"""
        summary = {
            "total_markets": len(self.markets),
            "available_services": len([m for m in self.markets.keys() if m in self.service_classes]),
            "markets": {},
        }

        for market_id, config in self.markets.items():
            summary["markets"][market_id] = {
                "name": config.get("market_name", market_id),
                "region": config.get("region", "Unknown"),
                "neighborhoods": len(config.get("neighborhoods", [])),
                "employers": len(config.get("employers", [])),
                "service_available": market_id in self.service_classes,
                "median_home_price": config.get("median_home_price", "N/A"),
            }

        return summary


# Global registry instance
_registry = None


def get_market_registry() -> MarketRegistry:
    """Get the global market registry instance"""
    global _registry
    if _registry is None:
        _registry = MarketRegistry()
    return _registry


# Convenience function for backward compatibility
def get_market_service(market_id: str) -> Optional[BaseMarketService]:
    """Get market service instance (convenience function)"""
    registry = get_market_registry()
    return registry.get_market_service(market_id)
