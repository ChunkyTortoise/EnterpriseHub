"""
EnterpriseHub Configuration Package

Exports the industry-agnostic IndustryConfig for bot configuration.
"""

from ghl_real_estate_ai.config.industry_config import (
    BotPersonality,
    HandoffConfig,
    IndustryConfig,
    IntentConfig,
    IntentMarkers,
    MarketConfig,
    QuestionConfig,
)

__all__ = [
    "BotPersonality",
    "HandoffConfig",
    "IndustryConfig",
    "IntentConfig",
    "IntentMarkers",
    "MarketConfig",
    "QuestionConfig",
]
