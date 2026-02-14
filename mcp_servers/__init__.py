"""
EnterpriseHub Custom MCP Servers

This package contains custom MCP (Model Context Protocol) servers for EnterpriseHub:
- Real Estate API: Property data from Zillow, Redfin, MLS
- Voice/Twilio: Voice calls, SMS, transcription
- Marketing Automation: Email campaigns, lead nurturing, analytics

Usage:
    # Run individual servers:
    python -m mcp_servers.real_estate_mcp
    python -m mcp_servers.voice_twilio_mcp
    python -m mcp_servers.marketing_automation_mcp

    # Or import and use in your application:
    from mcp_servers import real_estate_mcp, voice_twilio_mcp, marketing_automation_mcp
"""

import importlib
import os
from typing import Dict, List, Tuple

# Version
__version__ = "1.0.0"


# Lazy imports — modules are loaded on first access, not at import time
def _lazy_import(module_name: str):
    """Lazily import a submodule."""
    return importlib.import_module(f"mcp_servers.{module_name}")


def __getattr__(name: str):
    """Lazy module loader for submodules."""
    _modules = {
        "real_estate_mcp": "real_estate_mcp",
        "voice_twilio_mcp": "voice_twilio_mcp",
        "marketing_automation_mcp": "marketing_automation_mcp",
    }
    if name in _modules:
        return _lazy_import(_modules[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Server names for reference
SERVER_NAMES: Dict[str, str] = {
    "real_estate": "RealEstateAPI",
    "voice": "VoiceTwilio",
    "marketing": "MarketingAutomation"
}

# Environment variables required for each server
REQUIRED_ENV_VARS: Dict[str, List[str]] = {
    "real_estate": [
        "ZILLOW_API_KEY",
        "REDFIN_API_KEY",
        "MLS_API_KEY",
        "GREAT_SCHOOLS_API_KEY",
        "NICHES_API_KEY"
    ],
    "voice": [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "OPENAI_API_KEY"
    ],
    "marketing": [
        "HUBSPOT_API_KEY",
        "MAILCHIMP_API_KEY",
        "SENDGRID_API_KEY"
    ]
}


def get_server_info(server_name: str) -> Dict[str, object]:
    """Get information about a specific server"""
    info = {
        "real_estate": {
            "name": "RealEstateAPI",
            "description": "Real estate data integration from Zillow, Redfin, MLS",
            "tools": [
                "get_property_details",
                "get_market_comparables",
                "get_market_trends",
                "get_school_districts",
                "estimate_property_value",
                "search_properties"
            ]
        },
        "voice": {
            "name": "VoiceTwilio",
            "description": "Voice calls, SMS, and transcription via Twilio",
            "tools": [
                "make_call",
                "get_call_details",
                "send_sms",
                "send_sms_template",
                "transcribe_call_recording",
                "analyze_voicemail",
                "route_call"
            ]
        },
        "marketing": {
            "name": "MarketingAutomation",
            "description": "Email campaigns, lead nurturing, and analytics",
            "tools": [
                "create_email_campaign",
                "schedule_campaign",
                "get_campaign_performance",
                "create_contact",
                "enroll_in_sequence",
                "get_analytics_dashboard"
            ]
        }
    }
    return info.get(server_name, {})


def validate_environment(server_name: str) -> Tuple[bool, List[str]]:
    """
    Validate that required environment variables are set.

    Returns:
        (is_valid, missing_vars)
    """
    required = REQUIRED_ENV_VARS.get(server_name, [])
    missing = [var for var in required if not os.getenv(var)]

    return len(missing) == 0, missing
