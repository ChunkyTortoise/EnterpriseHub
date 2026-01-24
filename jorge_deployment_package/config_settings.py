#!/usr/bin/env python3
"""
Configuration Settings for Jorge's Bot System

Loads and validates configuration from environment variables.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BotSettings:
    """Configuration settings for Jorge's bot system"""

    def __init__(self):
        """Load settings from environment variables"""

        # Required settings
        self.ghl_access_token = os.getenv("GHL_ACCESS_TOKEN")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.ghl_location_id = os.getenv("GHL_LOCATION_ID")

        # Optional settings with defaults
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.webhook_secret = os.getenv("GHL_WEBHOOK_SECRET", "jorge_webhook_secret_2026")

        # Bot configuration
        self.bot_response_delay = float(os.getenv("BOT_RESPONSE_DELAY", "1.5"))
        self.auto_followup_enabled = os.getenv("AUTO_FOLLOWUP_ENABLED", "true").lower() == "true"
        self.hot_lead_score_threshold = int(os.getenv("HOT_LEAD_SCORE_THRESHOLD", "80"))
        self.warm_lead_score_threshold = int(os.getenv("WARM_LEAD_SCORE_THRESHOLD", "60"))

        # Seller bot settings
        self.jorge_confrontational_level = os.getenv("JORGE_CONFRONTATIONAL_LEVEL", "high")
        self.seller_qualification_timeout = int(os.getenv("SELLER_QUALIFICATION_TIMEOUT", "72"))

        # Follow-up settings
        self.initial_followup_delay = int(os.getenv("INITIAL_FOLLOWUP_DELAY", "4"))
        self.long_term_followup_days = int(os.getenv("LONG_TERM_FOLLOWUP_DAYS", "14"))
        self.max_followup_attempts = int(os.getenv("MAX_FOLLOWUP_ATTEMPTS", "5"))

        # System settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.testing_mode = os.getenv("TESTING_MODE", "false").lower() == "true"

        # Validate required settings
        self._validate_settings()

    def _validate_settings(self):
        """Validate that required settings are present"""

        missing_settings = []

        if not self.ghl_access_token:
            missing_settings.append("GHL_ACCESS_TOKEN")

        if not self.claude_api_key:
            missing_settings.append("CLAUDE_API_KEY")

        if not self.ghl_location_id:
            missing_settings.append("GHL_LOCATION_ID")

        if missing_settings and not self.testing_mode:
            raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")

    def get_claude_config(self) -> dict:
        """Get Claude API configuration"""
        return {
            "api_key": self.claude_api_key,
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "temperature": 0.3
        }

    def get_ghl_config(self) -> dict:
        """Get GHL API configuration"""
        return {
            "access_token": self.ghl_access_token,
            "location_id": self.ghl_location_id,
            "webhook_secret": self.webhook_secret
        }

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not (self.debug_mode or self.testing_mode)


# Global settings instance
settings = BotSettings()


# Helper functions for easy access
def get_ghl_token() -> str:
    """Get GHL access token"""
    return settings.ghl_access_token or ""


def get_claude_api_key() -> str:
    """Get Claude API key"""
    return settings.claude_api_key or ""


def get_location_id() -> str:
    """Get GHL location ID"""
    return settings.ghl_location_id or ""


def is_testing() -> bool:
    """Check if in testing mode"""
    return settings.testing_mode


def is_debug() -> bool:
    """Check if in debug mode"""
    return settings.debug_mode