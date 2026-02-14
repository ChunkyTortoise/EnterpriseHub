"""
Constants for buyer bot including compliance severity levels and opt-out phrases.
"""

# Compliance severity levels
COMPLIANCE_SEVERITY_MAP = {
    "fair_housing": "critical",
    "privacy": "high",
    "financial_regulation": "high",
    "licensing": "medium",
}

# TCPA opt-out phrases — mirrors webhook.py for consistent compliance handling
OPT_OUT_PHRASES = [
    "stop",
    "unsubscribe",
    "not interested",
    "opt out",
    "remove me",
    "cancel"
]

# Default limits
MAX_CONVERSATION_HISTORY = 50
SMS_MAX_LENGTH = 160
MAX_MESSAGE_LENGTH = 10_000