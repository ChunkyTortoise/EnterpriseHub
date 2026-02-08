"""
Multi-Market Geographic Expansion Module

This module provides the foundation for Jorge's multi-market expansion,
supporting configuration-driven market intelligence across multiple
geographic regions.
"""

from .base_market_service import BaseMarketService, MarketMetrics
from .concrete_services import (
    AustinMarketService,
    ConcreteMarketService,
    DallasMarketService,
    HoustonMarketService,
    RanchoCucamongaMarketService,
    SanAntonioMarketService,
)
from .config_schemas import EmployerConfig, MarketConfig, NeighborhoodConfig
from .registry import MarketRegistry, get_market_registry, get_market_service

__all__ = [
    # Base classes
    "BaseMarketService",
    "MarketMetrics",
    # Registry
    "MarketRegistry",
    "get_market_registry",
    "get_market_service",
    # Configuration
    "MarketConfig",
    "NeighborhoodConfig",
    "EmployerConfig",
    # Concrete services
    "ConcreteMarketService",
    "AustinMarketService",
    "DallasMarketService",
    "HoustonMarketService",
    "SanAntonioMarketService",
    "RanchoCucamongaMarketService",
]
