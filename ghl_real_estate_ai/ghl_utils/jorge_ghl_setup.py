"""GHL Setup Validation for Jorge Bots.

Validates that all required GHL custom fields, workflow IDs, and calendar
configuration are properly set via environment variables.

Usage: python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup
"""

import os
import sys
from typing import Dict, List, Tuple


# --- Field definitions ---

# (env_var_name, ghl_type, bot, critical)
CUSTOM_FIELDS: List[Tuple[str, str, str, bool]] = [
    # Seller fields
    ("CUSTOM_FIELD_SELLER_TEMPERATURE", "dropdown", "seller", True),
    ("CUSTOM_FIELD_SELLER_MOTIVATION", "text", "seller", False),
    ("CUSTOM_FIELD_RELOCATION_DESTINATION", "text", "seller", False),
    ("CUSTOM_FIELD_TIMELINE_URGENCY", "dropdown", "seller", True),
    ("CUSTOM_FIELD_PROPERTY_CONDITION", "dropdown", "seller", False),
    ("CUSTOM_FIELD_PRICE_EXPECTATION", "currency", "seller", False),
    ("CUSTOM_FIELD_QUESTIONS_ANSWERED", "number", "seller", False),
    ("CUSTOM_FIELD_QUALIFICATION_SCORE", "number", "seller", False),
    ("CUSTOM_FIELD_EXPECTED_ROI", "number", "seller", False),
    ("CUSTOM_FIELD_LEAD_VALUE_TIER", "dropdown", "seller", False),
    ("CUSTOM_FIELD_AI_VALUATION_PRICE", "currency", "seller", False),
    ("CUSTOM_FIELD_DETECTED_PERSONA", "dropdown", "seller", False),
    ("CUSTOM_FIELD_PSYCHOLOGY_TYPE", "text", "seller", False),
    ("CUSTOM_FIELD_URGENCY_LEVEL", "dropdown", "seller", False),
    ("CUSTOM_FIELD_MORTGAGE_BALANCE", "currency", "seller", False),
    ("CUSTOM_FIELD_REPAIR_ESTIMATE", "currency", "seller", False),
    ("CUSTOM_FIELD_LISTING_HISTORY", "text", "seller", False),
    ("CUSTOM_FIELD_DECISION_MAKER_CONFIRMED", "boolean", "seller", False),
    ("CUSTOM_FIELD_PREFERRED_CONTACT_METHOD", "dropdown", "seller", False),
    ("CUSTOM_FIELD_PROPERTY_ADDRESS", "text", "seller", False),
    ("CUSTOM_FIELD_PROPERTY_TYPE", "dropdown", "seller", False),
    ("CUSTOM_FIELD_LAST_BOT_INTERACTION", "datetime", "seller", False),
    ("CUSTOM_FIELD_QUALIFICATION_COMPLETE", "boolean", "seller", False),
    # Buyer fields
    ("CUSTOM_FIELD_BUYER_TEMPERATURE", "dropdown", "buyer", True),
    ("CUSTOM_FIELD_PRE_APPROVAL_STATUS", "dropdown", "buyer", False),
    ("CUSTOM_FIELD_PROPERTY_PREFERENCES", "text", "buyer", False),
    ("CUSTOM_FIELD_BUDGET", "currency", "buyer", True),
    # Lead fields
    ("CUSTOM_FIELD_LEAD_SCORE", "number", "lead", True),
    ("CUSTOM_FIELD_LOCATION", "text", "lead", False),
    ("CUSTOM_FIELD_TIMELINE", "dropdown", "lead", False),
]

WORKFLOW_IDS: List[Tuple[str, str, bool]] = [
    ("HOT_SELLER_WORKFLOW_ID", "seller", True),
    ("WARM_SELLER_WORKFLOW_ID", "seller", False),
    ("NOTIFY_AGENT_WORKFLOW_ID", "general", True),
    ("HOT_BUYER_WORKFLOW_ID", "buyer", True),
    ("WARM_BUYER_WORKFLOW_ID", "buyer", False),
]

CALENDAR_IDS: List[Tuple[str, str, bool]] = [
    ("GHL_CALENDAR_ID", "general", False),
]


def validate_ghl_config() -> Dict:
    """Validate all GHL configuration and return a status report.

    Returns:
        dict with keys:
            valid: bool - True if all critical fields are set
            fields: list of dicts with env_var, ghl_type, bot, critical, status
            workflows: list of dicts with env_var, bot, critical, status
            calendars: list of dicts with env_var, bot, critical, status
            summary: dict with set_count, missing_count, critical_missing
    """
    results: Dict = {"fields": [], "workflows": [], "calendars": []}
    critical_missing: List[str] = []

    # Check custom fields
    for env_var, ghl_type, bot, critical in CUSTOM_FIELDS:
        value = os.getenv(env_var, "")
        is_set = bool(value.strip())
        results["fields"].append({
            "env_var": env_var,
            "ghl_type": ghl_type,
            "bot": bot,
            "critical": critical,
            "status": "set" if is_set else "missing",
        })
        if critical and not is_set:
            critical_missing.append(env_var)

    # Check workflow IDs
    for env_var, bot, critical in WORKFLOW_IDS:
        value = os.getenv(env_var, "")
        is_set = bool(value.strip())
        results["workflows"].append({
            "env_var": env_var,
            "bot": bot,
            "critical": critical,
            "status": "set" if is_set else "missing",
        })
        if critical and not is_set:
            critical_missing.append(env_var)

    # Check calendar IDs
    for env_var, bot, critical in CALENDAR_IDS:
        value = os.getenv(env_var, "")
        is_set = bool(value.strip())
        results["calendars"].append({
            "env_var": env_var,
            "bot": bot,
            "critical": critical,
            "status": "set" if is_set else "missing",
        })
        if critical and not is_set:
            critical_missing.append(env_var)

    all_items = results["fields"] + results["workflows"] + results["calendars"]
    set_count = sum(1 for item in all_items if item["status"] == "set")
    missing_count = sum(1 for item in all_items if item["status"] == "missing")

    results["summary"] = {
        "set_count": set_count,
        "missing_count": missing_count,
        "critical_missing": critical_missing,
        "total": len(all_items),
    }
    results["valid"] = len(critical_missing) == 0

    return results


def print_report(results: Dict) -> None:
    """Print a formatted validation report."""
    print("=" * 70)
    print("  GHL Configuration Validation Report - Jorge Bots")
    print("=" * 70)

    for section, label in [
        ("fields", "Custom Fields"),
        ("workflows", "Workflow IDs"),
        ("calendars", "Calendar IDs"),
    ]:
        items = results[section]
        if not items:
            continue

        print(f"\n--- {label} ---")
        # Group by bot
        bots_seen: List[str] = []
        for item in items:
            if item["bot"] not in bots_seen:
                bots_seen.append(item["bot"])

        for bot in bots_seen:
            bot_items = [i for i in items if i["bot"] == bot]
            print(f"\n  [{bot.upper()}]")
            for item in bot_items:
                marker = "[OK]" if item["status"] == "set" else "[!!]" if item["critical"] else "[--]"
                crit = " (CRITICAL)" if item["critical"] and item["status"] == "missing" else ""
                extra = f"  type={item['ghl_type']}" if "ghl_type" in item else ""
                print(f"    {marker} {item['env_var']}{extra}{crit}")

    summary = results["summary"]
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY: {summary['set_count']}/{summary['total']} configured, "
          f"{summary['missing_count']} missing")
    if summary["critical_missing"]:
        print(f"  CRITICAL MISSING ({len(summary['critical_missing'])}):")
        for var in summary["critical_missing"]:
            print(f"    - {var}")
    else:
        print("  All critical fields are configured.")
    print("=" * 70)


if __name__ == "__main__":
    results = validate_ghl_config()
    print_report(results)
    sys.exit(0 if results["valid"] else 1)
