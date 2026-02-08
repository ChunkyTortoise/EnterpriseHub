"""
Vertical Market Extensions for EnterpriseHub Platform

This module contains specialized implementations for different industry verticals:
- Healthcare: Medical practices, hospitals, senior living facilities
- Commercial Finance: Office buildings, retail spaces, industrial properties
- Manufacturing/Logistics: Warehouses, distribution centers

Each vertical provides:
- Industry-specific property analysis algorithms
- Compliance and regulatory framework support
- Specialized UI components and dashboards
- Vertical-specific AI models and training data
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Vertical registry for dynamic loading
AVAILABLE_VERTICALS = {
    "healthcare": {
        "name": "Healthcare Real Estate",
        "module": "ghl_real_estate_ai.verticals.healthcare",
        "revenue_target": 39_000_000,  # $39M ARR
        "launch_priority": 1,
    },
    "commercial_finance": {
        "name": "Commercial Finance",
        "module": "ghl_real_estate_ai.verticals.commercial_finance",
        "revenue_target": 35_000_000,  # $35M ARR
        "launch_priority": 2,
    },
    "manufacturing": {
        "name": "Manufacturing & Logistics",
        "module": "ghl_real_estate_ai.verticals.manufacturing",
        "revenue_target": 30_000_000,  # $30M ARR
        "launch_priority": 3,
    },
}


def get_vertical_config(vertical_name: str) -> Dict[str, Any]:
    """Get configuration for a specific vertical market."""
    return AVAILABLE_VERTICALS.get(vertical_name, {})


def list_available_verticals() -> List[str]:
    """List all available vertical markets."""
    return list(AVAILABLE_VERTICALS.keys())
