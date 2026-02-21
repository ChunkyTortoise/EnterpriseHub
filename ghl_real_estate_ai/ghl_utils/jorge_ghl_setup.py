"""GHL Setup Validation for Jorge Bots.

Validates and manages GHL custom fields, workflow IDs, and calendar
configuration for the Jorge bot system.

Usage:
    python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup                  # default: validate env vars
    python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=list     # list all GHL custom fields
    python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=create   # create missing fields
    python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=validate # validate field IDs in .env
    python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup --action=test     # end-to-end integration test
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]


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

# Additional Jorge-specific fields for handoff and scoring
JORGE_FIELDS: List[Tuple[str, str, str, str, bool]] = [
    # (env_var_name, ghl_display_name, ghl_type, bot, critical)
    ("GHL_CUSTOM_FIELD_FRS", "Financial Readiness Score", "NUMERICAL", "lead", True),
    ("GHL_CUSTOM_FIELD_PCS", "Psychological Commitment Score", "NUMERICAL", "lead", True),
    ("GHL_CUSTOM_FIELD_BUYER_INTENT", "Buyer Intent Confidence", "NUMERICAL", "lead", True),
    ("GHL_CUSTOM_FIELD_SELLER_INTENT", "Seller Intent Confidence", "NUMERICAL", "lead", True),
    ("GHL_CUSTOM_FIELD_TEMPERATURE", "Lead Temperature", "SINGLE_LINE", "lead", True),
    ("GHL_CUSTOM_FIELD_HANDOFF_HISTORY", "Handoff History", "LARGE_TEXT", "lead", False),
    ("GHL_CUSTOM_FIELD_LAST_BOT", "Last Bot Interaction", "SINGLE_LINE", "lead", True),
    ("GHL_CUSTOM_FIELD_CONVERSATION_CONTEXT", "Conversation Context", "LARGE_TEXT", "lead", False),
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

# GHL API v2 base URL and type mapping
GHL_BASE_URL = "https://services.leadconnectorhq.com"

# Map our type names to GHL API v2 dataType values
GHL_TYPE_MAP = {
    "NUMERICAL": "NUMERICAL",
    "SINGLE_LINE": "SINGLE_LINE",
    "LARGE_TEXT": "LARGE_TEXT",
    "CHECKBOX": "CHECKBOX",
    # Legacy type names from CUSTOM_FIELDS
    "number": "NUMERICAL",
    "text": "SINGLE_LINE",
    "dropdown": "SINGLE_LINE",
    "currency": "NUMERICAL",
    "boolean": "CHECKBOX",
    "datetime": "SINGLE_LINE",
}


# ========== Existing Validation (env var presence) ==========


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
        results["fields"].append(
            {
                "env_var": env_var,
                "ghl_type": ghl_type,
                "bot": bot,
                "critical": critical,
                "status": "set" if is_set else "missing",
            }
        )
        if critical and not is_set:
            critical_missing.append(env_var)

    # Check Jorge-specific fields
    for env_var, display_name, ghl_type, bot, critical in JORGE_FIELDS:
        value = os.getenv(env_var, "")
        is_set = bool(value.strip())
        results["fields"].append(
            {
                "env_var": env_var,
                "ghl_type": ghl_type,
                "bot": bot,
                "critical": critical,
                "status": "set" if is_set else "missing",
            }
        )
        if critical and not is_set:
            critical_missing.append(env_var)

    # Check workflow IDs
    for env_var, bot, critical in WORKFLOW_IDS:
        value = os.getenv(env_var, "")
        is_set = bool(value.strip())
        results["workflows"].append(
            {
                "env_var": env_var,
                "bot": bot,
                "critical": critical,
                "status": "set" if is_set else "missing",
            }
        )
        if critical and not is_set:
            critical_missing.append(env_var)

    # Check calendar IDs
    for env_var, bot, critical in CALENDAR_IDS:
        value = os.getenv(env_var, "")
        is_set = bool(value.strip())
        results["calendars"].append(
            {
                "env_var": env_var,
                "bot": bot,
                "critical": critical,
                "status": "set" if is_set else "missing",
            }
        )
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
    print(f"  SUMMARY: {summary['set_count']}/{summary['total']} configured, {summary['missing_count']} missing")
    if summary["critical_missing"]:
        print(f"  CRITICAL MISSING ({len(summary['critical_missing'])}):")
        for var in summary["critical_missing"]:
            print(f"    - {var}")
    else:
        print("  All critical fields are configured.")
    print("=" * 70)


# ========== GHL API Client (sync wrapper for CLI) ==========


class GHLSetupClient:
    """Synchronous GHL API client for the setup CLI tool."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GHL_API_KEY", "")
        self.location_id = os.getenv("GHL_LOCATION_ID", "")
        if not self.api_key or not self.location_id:
            print("ERROR: GHL_API_KEY and GHL_LOCATION_ID must be set in .env")
            sys.exit(1)
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Version": "2021-07-28",
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(
            headers=self.headers,
            timeout=httpx.Timeout(15.0),
        )

    def close(self) -> None:
        self.client.close()

    def _request(
        self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        url = f"{GHL_BASE_URL}/{endpoint}"
        try:
            response = self.client.request(method=method, url=url, json=data, params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json() if response.content else {}}
        except httpx.HTTPStatusError as e:
            error_data = {}
            try:
                if e.response.content:
                    error_data = e.response.json()
            except Exception:
                pass
            return {"success": False, "error": str(e), "status_code": e.response.status_code, "details": error_data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_custom_fields(self) -> Dict[str, Any]:
        return self._request("GET", "locations/{}/customFields".format(self.location_id))

    def create_custom_field(self, name: str, data_type: str) -> Dict[str, Any]:
        payload = {
            "name": name,
            "dataType": data_type,
        }
        return self._request(
            "POST",
            "locations/{}/customFields".format(self.location_id),
            data=payload,
        )

    def get_custom_field_by_id(self, field_id: str) -> Dict[str, Any]:
        return self._request(
            "GET",
            "locations/{}/customFields/{}".format(self.location_id, field_id),
        )

    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        contact_data["locationId"] = self.location_id
        return self._request("POST", "contacts", data=contact_data)

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"contacts/{contact_id}", data=updates)

    def add_tag(self, contact_id: str, tag: str) -> Dict[str, Any]:
        return self._request("POST", f"contacts/{contact_id}/tags", data={"tags": [tag]})

    def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"contacts/{contact_id}")

    def health_check(self) -> Dict[str, Any]:
        result = self._request(
            "GET",
            "contacts",
            params={
                "locationId": self.location_id,
                "limit": 1,
            },
        )
        return {
            "healthy": result.get("success", False),
            "location_id": self.location_id,
            "checked_at": datetime.now().isoformat(),
        }


# ========== Action: list ==========


def action_list(client: GHLSetupClient) -> int:
    """List all existing GHL custom fields."""
    print("=" * 70)
    print("  GHL Custom Fields - List All")
    print("=" * 70)

    result = client.get_custom_fields()
    if not result.get("success"):
        print(f"\nERROR: Failed to fetch custom fields: {result.get('error', 'Unknown error')}")
        if "details" in result:
            print(f"  Details: {json.dumps(result['details'], indent=2)}")
        return 1

    fields = result.get("data", {}).get("customFields", [])
    if not fields:
        print("\n  No custom fields found in this GHL location.")
        return 0

    print(f"\n  Found {len(fields)} custom field(s):\n")
    print(f"  {'Name':<35} {'ID':<30} {'Type':<15}")
    print(f"  {'-' * 35} {'-' * 30} {'-' * 15}")
    for field in fields:
        name = field.get("name", "N/A")[:35]
        field_id = field.get("id", "N/A")
        data_type = field.get("dataType", "N/A")
        print(f"  {name:<35} {field_id:<30} {data_type:<15}")

    # Show .env format for easy copy
    print(f"\n{'=' * 70}")
    print("  .env format (copy-paste ready):")
    print(f"{'=' * 70}")
    for field in fields:
        name = field.get("name", "").replace(" ", "_").upper()
        field_id = field.get("id", "")
        print(f"  GHL_CUSTOM_FIELD_{name}={field_id}")

    print(f"{'=' * 70}")
    return 0


# ========== Action: create ==========


def action_create(client: GHLSetupClient) -> int:
    """Create missing Jorge-specific custom fields in GHL."""
    print("=" * 70)
    print("  GHL Custom Fields - Create Missing Jorge Fields")
    print("=" * 70)

    # Fetch existing fields
    result = client.get_custom_fields()
    if not result.get("success"):
        print(f"\nERROR: Failed to fetch existing fields: {result.get('error')}")
        return 1

    existing_fields = result.get("data", {}).get("customFields", [])
    existing_names = {f.get("name", "").lower() for f in existing_fields}

    print(f"\n  Existing fields in GHL: {len(existing_fields)}")
    print(f"  Required Jorge fields: {len(JORGE_FIELDS)}\n")

    created = []
    skipped = []
    failed = []

    for env_var, display_name, data_type, bot, critical in JORGE_FIELDS:
        if display_name.lower() in existing_names:
            # Find existing field ID
            existing_id = next(
                (f.get("id") for f in existing_fields if f.get("name", "").lower() == display_name.lower()),
                None,
            )
            skipped.append((env_var, display_name, existing_id))
            print(f"  [SKIP] {display_name} (already exists: {existing_id})")
            continue

        ghl_data_type = GHL_TYPE_MAP.get(data_type, "SINGLE_LINE")
        create_result = client.create_custom_field(display_name, ghl_data_type)

        if create_result.get("success"):
            field_id = create_result.get("data", {}).get("customField", {}).get("id", "unknown")
            created.append((env_var, display_name, field_id))
            print(f"  [OK]   {display_name} -> {field_id}")
        else:
            failed.append((env_var, display_name, create_result.get("error", "Unknown error")))
            print(f"  [FAIL] {display_name}: {create_result.get('error')}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {len(created)} created, {len(skipped)} skipped, {len(failed)} failed")

    if created or skipped:
        print(f"\n  Add these to your .env file:")
        print(f"  {'=' * 60}")
        print(f"  # Jorge Bot Custom Field IDs (generated {datetime.now().strftime('%Y-%m-%d %H:%M')})")
        for env_var, display_name, field_id in created:
            print(f"  {env_var}={field_id}")
        for env_var, display_name, field_id in skipped:
            if field_id:
                print(f"  {env_var}={field_id}")
        print(f"  {'=' * 60}")

    if failed:
        print(f"\n  FAILED FIELDS:")
        for env_var, display_name, error in failed:
            print(f"    - {display_name}: {error}")
        return 1

    print("=" * 70)
    return 0


# ========== Action: validate ==========


def action_validate(client: GHLSetupClient) -> int:
    """Validate that all field IDs in .env actually exist in GHL."""
    print("=" * 70)
    print("  GHL Custom Fields - Validate Field IDs")
    print("=" * 70)

    # Health check first
    health = client.health_check()
    print(f"\n  API Health: {'OK' if health['healthy'] else 'FAILED'}")
    print(f"  Location: {health['location_id']}")

    if not health["healthy"]:
        print("\n  ERROR: Cannot connect to GHL API. Check credentials.")
        return 1

    # Fetch all fields from GHL
    result = client.get_custom_fields()
    if not result.get("success"):
        print(f"\nERROR: Failed to fetch fields: {result.get('error')}")
        return 1

    existing_fields = result.get("data", {}).get("customFields", [])
    existing_ids = {f.get("id") for f in existing_fields}

    print(f"  GHL fields found: {len(existing_fields)}\n")

    # Validate Jorge-specific field IDs
    valid_count = 0
    invalid_count = 0
    missing_count = 0

    print("  --- Jorge Field IDs ---\n")
    for env_var, display_name, data_type, bot, critical in JORGE_FIELDS:
        value = os.getenv(env_var, "").strip()
        crit_tag = " (CRITICAL)" if critical else ""

        if not value:
            status = "MISSING"
            missing_count += 1
        elif value in existing_ids:
            status = "VALID"
            valid_count += 1
        else:
            status = "INVALID"
            invalid_count += 1

        marker = {"VALID": "[OK]", "MISSING": "[--]", "INVALID": "[!!]"}[status]
        print(f"    {marker} {env_var}: {value or '(not set)'} -> {status}{crit_tag}")

    # Also validate standard custom fields
    print("\n  --- Standard Field IDs ---\n")
    for env_var, ghl_type, bot, critical in CUSTOM_FIELDS:
        value = os.getenv(env_var, "").strip()
        crit_tag = " (CRITICAL)" if critical else ""

        if not value:
            status = "MISSING"
            missing_count += 1
        elif value in existing_ids:
            status = "VALID"
            valid_count += 1
        else:
            status = "INVALID (not found in GHL)"
            invalid_count += 1

        marker = "[OK]" if "VALID" == status else "[--]" if "MISSING" == status else "[!!]"
        print(f"    {marker} {env_var}: {value or '(not set)'} -> {status}{crit_tag}")

    # Validate workflow IDs (env var presence only -- cannot verify via custom fields API)
    print("\n  --- Workflow IDs (env var check) ---\n")
    for env_var, bot, critical in WORKFLOW_IDS:
        value = os.getenv(env_var, "").strip()
        status = "SET" if value else "MISSING"
        crit_tag = " (CRITICAL)" if critical and not value else ""
        marker = "[OK]" if value else "[--]"
        print(f"    {marker} {env_var}: {value or '(not set)'}{crit_tag}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  VALIDATION SUMMARY:")
    print(f"    Valid field IDs:   {valid_count}")
    print(f"    Missing field IDs: {missing_count}")
    print(f"    Invalid field IDs: {invalid_count}")

    if invalid_count > 0:
        print(f"\n  WARNING: {invalid_count} field ID(s) in .env do not match any GHL field.")
        print(f"  Run --action=list to see actual field IDs, or --action=create to create missing fields.")

    print("=" * 70)
    return 1 if invalid_count > 0 else 0


# ========== Action: test ==========


def action_test(client: GHLSetupClient) -> int:
    """Run end-to-end integration test with GHL."""
    print("=" * 70)
    print("  GHL Integration Test - End-to-End")
    print("=" * 70)

    test_contact_id: Optional[str] = None
    passed = 0
    failed = 0

    def report(name: str, success: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if success:
            passed += 1
            print(f"  [PASS] {name}" + (f" ({detail})" if detail else ""))
        else:
            failed += 1
            print(f"  [FAIL] {name}" + (f" ({detail})" if detail else ""))

    try:
        # Test 1: Health check
        print("\n  --- Step 1: API Health Check ---")
        health = client.health_check()
        report("API connection", health["healthy"])

        if not health["healthy"]:
            print("\n  ABORTING: Cannot connect to GHL API.")
            return 1

        # Test 2: List custom fields
        print("\n  --- Step 2: List Custom Fields ---")
        fields_result = client.get_custom_fields()
        report(
            "Fetch custom fields",
            fields_result.get("success", False),
            f"{len(fields_result.get('data', {}).get('customFields', []))} fields",
        )

        # Test 3: Create test contact
        print("\n  --- Step 3: Create Test Contact ---")
        test_contact_data = {
            "firstName": "Jorge_Bot_Test",
            "lastName": f"Integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "email": f"jorge-test-{datetime.now().strftime('%H%M%S')}@test.example.com",
            "phone": "+10000000000",
            "tags": ["jorge-integration-test"],
        }
        create_result = client.create_contact(test_contact_data)
        contact_created = create_result.get("success", False)
        if contact_created:
            test_contact_id = create_result.get("data", {}).get("contact", {}).get("id")
            report("Create test contact", True, f"ID: {test_contact_id}")
        else:
            report("Create test contact", False, create_result.get("error", ""))

        if not test_contact_id:
            print("\n  ABORTING: Cannot create test contact for remaining tests.")
            return 1

        # Test 4: Update custom fields on contact
        print("\n  --- Step 4: Update Custom Fields ---")
        jorge_field_updates = []
        for env_var, display_name, data_type, bot, critical in JORGE_FIELDS:
            field_id = os.getenv(env_var, "").strip()
            if field_id:
                test_value = "42" if "NUMERICAL" in data_type else "test_value"
                jorge_field_updates.append({"id": field_id, "field_value": test_value})

        if jorge_field_updates:
            update_payload = {
                "customFields": [{"id": f["id"], "value": f["field_value"]} for f in jorge_field_updates],
            }
            update_result = client.update_contact(test_contact_id, update_payload)
            report("Update custom fields", update_result.get("success", False), f"{len(jorge_field_updates)} fields")
        else:
            report("Update custom fields", False, "No field IDs configured in .env")

        # Test 5: Add temperature tag
        print("\n  --- Step 5: Publish Temperature Tag ---")
        for tag_name in ["Hot-Lead", "jorge-integration-test"]:
            tag_result = client.add_tag(test_contact_id, tag_name)
            report(f"Add tag '{tag_name}'", tag_result.get("success", False))

    finally:
        # Cleanup: delete test contact
        if test_contact_id:
            print("\n  --- Cleanup: Remove Test Contact ---")
            delete_result = client.delete_contact(test_contact_id)
            report("Delete test contact", delete_result.get("success", False), test_contact_id)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  TEST RESULTS: {passed} passed, {failed} failed")
    if failed == 0:
        print("  All integration tests PASSED.")
    else:
        print(f"  {failed} test(s) FAILED. Review output above.")
    print("=" * 70)
    return 1 if failed > 0 else 0


# ========== CLI Entry Point ==========


def main() -> int:
    # Load .env file so credentials and field IDs are available
    if load_dotenv is not None:
        load_dotenv()

    parser = argparse.ArgumentParser(
        description="GHL Setup Validation & Management for Jorge Bots",
    )
    parser.add_argument(
        "--action",
        choices=["list", "create", "validate", "test"],
        default=None,
        help="Action to perform (default: env var validation only)",
    )

    args = parser.parse_args()

    if args.action is None:
        # Default: env var validation only (original behavior)
        results = validate_ghl_config()
        print_report(results)
        return 0 if results["valid"] else 1

    # Actions that require API access
    client = GHLSetupClient()
    try:
        if args.action == "list":
            return action_list(client)
        elif args.action == "create":
            return action_create(client)
        elif args.action == "validate":
            return action_validate(client)
        elif args.action == "test":
            return action_test(client)
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
