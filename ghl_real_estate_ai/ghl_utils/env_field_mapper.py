#!/usr/bin/env python3
"""GHL Environment Field Mapper.

Audits .env file for all required GHL field IDs and reports status.
Covers API credentials, custom fields (seller/buyer/lead/jorge),
workflow IDs, calendar IDs, and pipeline/stage IDs.

Usage:
    python -m ghl_real_estate_ai.ghl_utils.env_field_mapper
    python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --env-file=.env.production
    python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --check-only
    python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --category=contact
"""

import argparse
import os
import sys
from pathlib import Path
from typing import NamedTuple


class FieldSpec(NamedTuple):
    """Specification for a single GHL environment variable."""

    env_var: str
    description: str
    category: str  # "api", "contact", "workflow", "calendar", "opportunity"
    required: bool


# ---------------------------------------------------------------------------
# All GHL field ID variables (41 total)
#
# Sources:
#   - ghl_real_estate_ai/ghl_utils/jorge_ghl_setup.py (CUSTOM_FIELDS, JORGE_FIELDS,
#     WORKFLOW_IDS, CALENDAR_IDS)
#   - .env.example (GHL section)
#   - ghl_real_estate_ai/services/jorge/calendar_booking_service.py
#   - ghl_real_estate_ai/services/ghl_webhook_service.py
# ---------------------------------------------------------------------------

GHL_FIELDS: list[FieldSpec] = [
    # ── API credentials (3) ──────────────────────────────────────────────
    FieldSpec("GHL_API_KEY", "GoHighLevel API key (v2 JWT)", "api", True),
    FieldSpec("GHL_LOCATION_ID", "GHL sub-account / location ID", "api", True),
    FieldSpec("GHL_WEBHOOK_SECRET", "Webhook signature verification secret", "api", True),
    # ── Seller custom fields (23) ────────────────────────────────────────
    FieldSpec(
        "CUSTOM_FIELD_SELLER_TEMPERATURE",
        "Hot/Warm/Cold seller classification (dropdown)",
        "contact",
        True,
    ),
    FieldSpec(
        "CUSTOM_FIELD_SELLER_MOTIVATION",
        "Seller motivation notes (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_RELOCATION_DESTINATION",
        "Where seller is relocating (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_TIMELINE_URGENCY",
        "Urgency level for selling (dropdown)",
        "contact",
        True,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PROPERTY_CONDITION",
        "Property condition assessment (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PRICE_EXPECTATION",
        "Expected sale price (currency)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_QUESTIONS_ANSWERED",
        "Count of qualification questions answered (number)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_QUALIFICATION_SCORE",
        "Overall qualification score (number)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_EXPECTED_ROI",
        "Expected return on investment (number)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_LEAD_VALUE_TIER",
        "Lead value classification (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_AI_VALUATION_PRICE",
        "AI-generated property valuation (currency)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_DETECTED_PERSONA",
        "Seller persona type (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PSYCHOLOGY_TYPE",
        "Psychological profile (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_URGENCY_LEVEL",
        "Urgency classification (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_MORTGAGE_BALANCE",
        "Outstanding mortgage balance (currency)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_REPAIR_ESTIMATE",
        "Estimated repair costs (currency)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_LISTING_HISTORY",
        "Previous listing details (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_DECISION_MAKER_CONFIRMED",
        "Whether decision maker is confirmed (boolean)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PREFERRED_CONTACT_METHOD",
        "SMS/Call/Email preference (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PROPERTY_ADDRESS",
        "Property street address (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PROPERTY_TYPE",
        "SFR/Condo/Townhouse/Multi (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_LAST_BOT_INTERACTION",
        "Timestamp of last bot message (datetime)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_QUALIFICATION_COMPLETE",
        "Whether full qualification is done (boolean)",
        "contact",
        False,
    ),
    # ── Buyer custom fields (4) ──────────────────────────────────────────
    FieldSpec(
        "CUSTOM_FIELD_BUYER_TEMPERATURE",
        "Hot/Warm/Cold buyer classification (dropdown)",
        "contact",
        True,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PRE_APPROVAL_STATUS",
        "Mortgage pre-approval status (dropdown)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_PROPERTY_PREFERENCES",
        "Desired property features (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_BUDGET",
        "Buyer's budget range (currency)",
        "contact",
        True,
    ),
    # ── Lead custom fields (3) ───────────────────────────────────────────
    FieldSpec(
        "CUSTOM_FIELD_LEAD_SCORE",
        "Overall lead score 0-100 (number)",
        "contact",
        True,
    ),
    FieldSpec(
        "CUSTOM_FIELD_LOCATION",
        "Lead's location / area (text)",
        "contact",
        False,
    ),
    FieldSpec(
        "CUSTOM_FIELD_TIMELINE",
        "Purchase/sale timeline (dropdown)",
        "contact",
        False,
    ),
    # ── Jorge bot custom fields (8) ──────────────────────────────────────
    FieldSpec(
        "GHL_CUSTOM_FIELD_FRS",
        "Financial Readiness Score 0-100 (NUMERICAL)",
        "contact",
        True,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_PCS",
        "Psychological Commitment Score 0-100 (NUMERICAL)",
        "contact",
        True,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_BUYER_INTENT",
        "Buyer intent confidence 0.0-1.0 (NUMERICAL)",
        "contact",
        True,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_SELLER_INTENT",
        "Seller intent confidence 0.0-1.0 (NUMERICAL)",
        "contact",
        True,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_TEMPERATURE",
        "Hot/Warm/Cold lead classification (SINGLE_LINE)",
        "contact",
        True,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_HANDOFF_HISTORY",
        "JSON log of cross-bot handoff events (LARGE_TEXT)",
        "contact",
        False,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_LAST_BOT",
        "Which bot last handled this contact (SINGLE_LINE)",
        "contact",
        True,
    ),
    FieldSpec(
        "GHL_CUSTOM_FIELD_CONVERSATION_CONTEXT",
        "JSON context passed during bot handoffs (LARGE_TEXT)",
        "contact",
        False,
    ),
    # ── Workflow IDs (5) ─────────────────────────────────────────────────
    FieldSpec(
        "HOT_SELLER_WORKFLOW_ID",
        "Workflow triggered when seller scores Hot",
        "workflow",
        True,
    ),
    FieldSpec(
        "WARM_SELLER_WORKFLOW_ID",
        "Nurture sequence for Warm sellers",
        "workflow",
        False,
    ),
    FieldSpec(
        "NOTIFY_AGENT_WORKFLOW_ID",
        "Sends SMS/email to agent for qualified leads",
        "workflow",
        True,
    ),
    FieldSpec(
        "HOT_BUYER_WORKFLOW_ID",
        "Workflow triggered when buyer scores Hot",
        "workflow",
        True,
    ),
    FieldSpec(
        "WARM_BUYER_WORKFLOW_ID",
        "Nurture sequence for Warm buyers",
        "workflow",
        False,
    ),
    # ── Calendar IDs (2) ─────────────────────────────────────────────────
    FieldSpec(
        "GHL_CALENDAR_ID",
        "Jorge's appointment calendar for auto-booking",
        "calendar",
        False,
    ),
    FieldSpec(
        "JORGE_CALENDAR_ID",
        "HOT seller appointment booking calendar",
        "calendar",
        False,
    ),
]

# Friendly labels for categories
CATEGORY_LABELS: dict[str, str] = {
    "api": "API Credentials",
    "contact": "Contact Custom Fields",
    "workflow": "Workflow IDs",
    "calendar": "Calendar IDs",
    "opportunity": "Pipeline & Opportunity Stages",
}

# ANSI color helpers (gracefully degrade on dumb terminals)
_USE_COLOR = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _USE_COLOR:
        return f"\033[{code}m{text}\033[0m"
    return text


def _green(text: str) -> str:
    return _c("32", text)


def _red(text: str) -> str:
    return _c("31", text)


def _yellow(text: str) -> str:
    return _c("33", text)


def _cyan(text: str) -> str:
    return _c("36", text)


def _bold(text: str) -> str:
    return _c("1", text)


class AuditResult:
    """Container for audit results."""

    def __init__(
        self,
        present: list[FieldSpec],
        missing_required: list[FieldSpec],
        missing_optional: list[FieldSpec],
    ) -> None:
        self.present = present
        self.missing_required = missing_required
        self.missing_optional = missing_optional

    @property
    def total(self) -> int:
        return len(self.present) + len(self.missing_required) + len(self.missing_optional)

    @property
    def is_healthy(self) -> bool:
        return len(self.missing_required) == 0


class EnvFieldMapper:
    """Reads .env file and reports GHL field ID status."""

    def __init__(self, env_path: str = ".env") -> None:
        self.env_path = Path(env_path)
        self.env_vars: dict[str, str] = {}
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Parse the .env file into env_vars dict.

        Supports:
          - KEY=VALUE
          - KEY="VALUE" / KEY='VALUE'
          - Comments (lines starting with #)
          - Blank lines
          - export KEY=VALUE
        """
        if not self.env_path.exists():
            return

        with open(self.env_path) as fh:
            for raw_line in fh:
                line = raw_line.strip()

                # Skip blanks and comments
                if not line or line.startswith("#"):
                    continue

                # Strip optional 'export ' prefix
                if line.startswith("export "):
                    line = line[7:]

                # Split on first '='
                if "=" not in line:
                    continue

                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()

                # Remove surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]

                self.env_vars[key] = value

    # ------------------------------------------------------------------
    # Auditing
    # ------------------------------------------------------------------

    def audit(self, category: str | None = None) -> AuditResult:
        """Return audit results: present, missing_required, missing_optional.

        Args:
            category: Optional filter -- only audit fields in this category.
        """
        present: list[FieldSpec] = []
        missing_required: list[FieldSpec] = []
        missing_optional: list[FieldSpec] = []

        fields = GHL_FIELDS
        if category:
            fields = [f for f in GHL_FIELDS if f.category == category]

        for field in fields:
            # Check .env file first, fall back to live os.environ
            value = self.env_vars.get(field.env_var, "") or os.environ.get(field.env_var, "")
            if value.strip():
                present.append(field)
            elif field.required:
                missing_required.append(field)
            else:
                missing_optional.append(field)

        return AuditResult(present, missing_required, missing_optional)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def print_report(self, category: str | None = None) -> None:
        """Print colored report to terminal."""
        result = self.audit(category)

        print()
        print(_bold("=" * 72))
        print(_bold("  GHL Environment Field Audit"))
        print(_bold(f"  .env file: {self.env_path.resolve()}"))
        print(_bold("=" * 72))

        # Group by category
        categories_seen: list[str] = []
        all_fields = GHL_FIELDS if not category else [f for f in GHL_FIELDS if f.category == category]
        for f in all_fields:
            if f.category not in categories_seen:
                categories_seen.append(f.category)

        for cat in categories_seen:
            label = CATEGORY_LABELS.get(cat, cat.title())
            cat_fields = [f for f in all_fields if f.category == cat]

            print()
            print(_cyan(f"  --- {label} ({len(cat_fields)} fields) ---"))
            print()

            for field in cat_fields:
                value = self.env_vars.get(field.env_var, "") or os.environ.get(
                    field.env_var, ""
                )
                is_set = bool(value.strip())

                if is_set:
                    # Mask sensitive values
                    display = _mask_value(field.env_var, value)
                    marker = _green("[OK]")
                else:
                    display = "(not set)"
                    if field.required:
                        marker = _red("[!!]")
                        display = _red(display + "  ** REQUIRED **")
                    else:
                        marker = _yellow("[--]")

                print(f"    {marker} {field.env_var}")
                print(f"         {field.description}")
                print(f"         Value: {display}")

        # Summary
        print()
        print(_bold("=" * 72))
        print(
            _bold(
                f"  SUMMARY: {len(result.present)}/{result.total} configured"
            )
        )
        if result.missing_required:
            print(
                _red(
                    f"  MISSING REQUIRED: {len(result.missing_required)} field(s)"
                )
            )
            for f in result.missing_required:
                print(_red(f"    - {f.env_var}  ({f.description})"))
        else:
            print(_green("  All required fields are configured."))

        if result.missing_optional:
            print(
                _yellow(
                    f"  MISSING OPTIONAL: {len(result.missing_optional)} field(s)"
                )
            )
        print(_bold("=" * 72))
        print()

    def print_setup_instructions(self) -> None:
        """Print step-by-step instructions for missing fields."""
        result = self.audit()

        if result.is_healthy and not result.missing_optional:
            print(_green("\n  All GHL fields are configured. Nothing to do.\n"))
            return

        print()
        print(_bold("=" * 72))
        print(_bold("  GHL Field Setup Instructions"))
        print(_bold("=" * 72))

        if result.missing_required:
            print()
            print(_red(f"  Step 1: Fix {len(result.missing_required)} REQUIRED field(s)"))
            print()
            print("  Option A - Automated (requires GHL API key):")
            print("    python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=create")
            print()
            print("  Option B - Manual:")
            print("    1. Go to GHL Dashboard > Settings > Custom Fields")
            print("    2. Create each missing field")
            print("    3. Copy the field ID into your .env file")
            print()

            for f in result.missing_required:
                cat_hint = ""
                if f.category == "workflow":
                    cat_hint = " (GHL > Automation > Workflows)"
                elif f.category == "calendar":
                    cat_hint = " (GHL > Calendars)"
                elif f.category == "api":
                    cat_hint = " (GHL > Settings > Business Profile)"
                print(f"    {f.env_var}=<your_value>{cat_hint}")
                print(f"      -> {f.description}")
                print()

        if result.missing_optional:
            print(
                _yellow(
                    f"  Step 2: Optionally configure {len(result.missing_optional)} field(s)"
                )
            )
            print()
            for f in result.missing_optional:
                print(f"    {f.env_var}=<your_value>")
                print(f"      -> {f.description}")
            print()

        print("  After updating .env, verify with:")
        print("    python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --check-only")
        print()
        print(_bold("=" * 72))
        print()


def _mask_value(env_var: str, value: str) -> str:
    """Mask sensitive values for display (API keys, secrets)."""
    sensitive_keywords = ("KEY", "SECRET", "TOKEN", "PASSWORD")
    if any(kw in env_var.upper() for kw in sensitive_keywords):
        if len(value) > 8:
            return value[:4] + "****" + value[-4:]
        return "****"
    # For field IDs, show full value (they are not secrets)
    return value


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GHL Environment Field Mapper - audit .env for GHL field IDs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m ghl_real_estate_ai.ghl_utils.env_field_mapper\n"
            "  python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --env-file=.env.production\n"
            "  python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --check-only\n"
            "  python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --category=workflow\n"
            "  python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --setup\n"
        ),
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Exit 1 if any required fields are missing (CI mode)",
    )
    parser.add_argument(
        "--category",
        choices=list(CATEGORY_LABELS.keys()),
        default=None,
        help="Only audit fields in this category",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Print step-by-step setup instructions for missing fields",
    )
    args = parser.parse_args()

    mapper = EnvFieldMapper(args.env_file)

    if args.setup:
        mapper.print_setup_instructions()
        return 0

    mapper.print_report(category=args.category)

    if args.check_only:
        result = mapper.audit(category=args.category)
        if not result.is_healthy:
            print(
                _red(
                    f"  FAILED: {len(result.missing_required)} required field(s) missing.\n"
                )
            )
            return 1
        print(_green("  PASSED: All required fields are configured.\n"))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
