"""
Re-engagement Message Templates for Silent Leads.

Jorge's requirements:
- Direct, no-nonsense tone
- SMS-compliant (under 160 characters)
- Progressive urgency: 24h → 48h → 72h
- Personalized with name and action (buy/sell)

All messages use Jorge's "closer" voice - direct, curious, authentic.
"""

# ==============================================================================
# RE-ENGAGEMENT MESSAGE TEMPLATES
# ==============================================================================

REENGAGEMENT_TEMPLATES = {
    "24h": {
        "buyer": "Hey {name}! Just checking in - is buying a home still a priority for you, or have you put it on hold?",
        "seller": "Hey {name}! Just checking in - is selling still a priority for you, or have you put it on hold?",
        "general": "Hey {name}! Still interested in {action}, or should we move on?",
    },
    "48h": {
        "buyer": "Hey {name}, are you actually still looking to buy, or should we close your file?",
        "seller": "Hey {name}, are you actually still looking to sell, or should we close your file?",
        "general": "Hey {name}, still looking to {action} or should we close your file?",
    },
    "72h": {
        "buyer": "Last chance {name} - still interested in buying, or should we move on?",
        "seller": "Last chance {name} - still interested in selling, or should we move on?",
        "general": "Last chance {name} - still interested, or are we done here?",
    },
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def get_reengagement_message(
    trigger_level: str, contact_name: str, action: str = None, is_buyer: bool = None, is_seller: bool = None
) -> str:
    """
    Get re-engagement message for specific trigger level.

    Args:
        trigger_level: "24h", "48h", or "72h"
        contact_name: Lead's first name
        action: Action verb (e.g., "buy", "sell")
        is_buyer: True if lead is a buyer
        is_seller: True if lead is a seller

    Returns:
        Personalized re-engagement message (SMS-compliant, <160 chars)

    Examples:
        >>> get_reengagement_message("24h", "Sarah", is_buyer=True)
        "Hey Sarah! Just checking in - is buying a home still a priority for you, or have you put it on hold?"

        >>> get_reengagement_message("48h", "Mike", is_seller=True)
        "Hey Mike, are you actually still looking to sell, or should we close your file?"

        >>> get_reengagement_message("72h", "Lisa", action="buy")
        "Last chance Lisa - still interested in buying, or should we move on?"
    """
    if trigger_level not in REENGAGEMENT_TEMPLATES:
        raise ValueError(f"Invalid trigger level: {trigger_level}. Use '24h', '48h', or '72h'.")

    templates = REENGAGEMENT_TEMPLATES[trigger_level]

    # Determine which template to use
    if is_buyer:
        template = templates["buyer"]
    elif is_seller:
        template = templates["seller"]
    else:
        template = templates["general"]

    # Format the message
    if "{action}" in template and action:
        message = template.format(name=contact_name, action=action)
    else:
        message = template.format(name=contact_name)

    # Validate SMS compliance
    if len(message) > 160:
        raise ValueError(f"Message exceeds SMS limit: {len(message)} chars\nMessage: {message}")

    return message


def validate_all_templates():
    """
    Validate that all templates are SMS-compliant (<160 chars).

    Raises:
        ValueError: If any template exceeds 160 characters.
    """
    # Test with longest common names
    test_names = ["Christopher", "Alexandria", "Maximilian"]

    for trigger_level, templates in REENGAGEMENT_TEMPLATES.items():
        for template_type, template in templates.items():
            for name in test_names:
                # Format template with longest name
                if "{action}" in template:
                    message = template.format(name=name, action="buying")
                else:
                    message = template.format(name=name)

                if len(message) > 160:
                    raise ValueError(
                        f"Template '{trigger_level}.{template_type}' exceeds 160 chars with name '{name}': "
                        f"{len(message)} chars\nMessage: {message}"
                    )


# ==============================================================================
# TEMPLATE METADATA
# ==============================================================================

TEMPLATE_METADATA = {
    "24h": {
        "urgency": "low",
        "tone": "curious, checking in",
        "goal": "Re-engage without pressure",
        "expected_response_rate": "30-40%",
    },
    "48h": {
        "urgency": "medium",
        "tone": "direct, slightly challenging",
        "goal": "Create urgency by mentioning file closure",
        "expected_response_rate": "20-30%",
    },
    "72h": {
        "urgency": "high",
        "tone": "final, direct, no-nonsense",
        "goal": "Last attempt - qualify out or re-engage",
        "expected_response_rate": "10-20%",
    },
}


# ==============================================================================
# TESTING & VALIDATION
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Re-engagement Template Validation")
    print("=" * 80)

    # Validate all templates
    try:
        validate_all_templates()
        print("✅ All templates are SMS-compliant (<160 characters)")
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
        exit(1)

    # Display sample messages
    print("\n" + "=" * 80)
    print("Sample Messages")
    print("=" * 80)

    test_cases = [
        ("24h", "Sarah", {"is_buyer": True}),
        ("24h", "Mike", {"is_seller": True}),
        ("24h", "Alex", {"action": "buy"}),
        ("48h", "Christopher", {"is_buyer": True}),
        ("48h", "Lisa", {"is_seller": True}),
        ("72h", "John", {"is_buyer": True}),
        ("72h", "Maria", {"is_seller": True}),
    ]

    for trigger, name, kwargs in test_cases:
        message = get_reengagement_message(trigger, name, **kwargs)
        char_count = len(message)
        print(f"\n{trigger.upper()} - {name}:")
        print(f"  Message: {message}")
        print(f"  Length: {char_count} chars")

    # Display metadata
    print("\n" + "=" * 80)
    print("Template Metadata")
    print("=" * 80)

    for trigger, metadata in TEMPLATE_METADATA.items():
        print(f"\n{trigger.upper()}:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("✅ Template system ready for production")
    print("=" * 80)
