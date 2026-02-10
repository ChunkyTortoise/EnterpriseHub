#!/usr/bin/env python3
"""
Assertive standalone validation for Jorge bot package.

This script exits non-zero on any failed runtime check.
"""

import asyncio
import json
import os
import sys
from pathlib import Path


os.environ.setdefault("TESTING_MODE", "true")
os.environ.setdefault("GHL_ACCESS_TOKEN", "test-ghl-token")
os.environ.setdefault("CLAUDE_API_KEY", "test-claude-key")
os.environ.setdefault("GHL_LOCATION_ID", "test-location")
os.environ.setdefault("GHL_WEBHOOK_SECRET", "test-webhook-secret")


def assert_required_imports() -> None:
    from conversation_manager import ConversationManager  # noqa: F401
    from ghl_client import GHLClient  # noqa: F401
    from jorge_engines_optimized import JorgeLeadEngineOptimized, JorgeSellerEngineOptimized  # noqa: F401
    from jorge_fastapi_lead_bot import _compute_webhook_signature, _verify_webhook_signature  # noqa: F401


def assert_ghl_contract_surface() -> None:
    from ghl_client import GHLClient

    expected = [
        "send_sms",
        "update_contact_custom_fields",
        "add_contact_tags",
    ]
    for method_name in expected:
        assert hasattr(GHLClient, method_name), f"Missing GHLClient method: {method_name}"


def assert_webhook_signature_helpers() -> None:
    from jorge_fastapi_lead_bot import _compute_webhook_signature, _verify_webhook_signature

    payload = {"type": "contact.updated", "contact_id": "contact-1"}
    payload_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    secret = "test-webhook-secret"
    signature = _compute_webhook_signature(secret, payload_raw)

    assert _verify_webhook_signature(payload_raw, signature, secret) is True
    assert _verify_webhook_signature(payload_raw, "bad-signature", secret) is False


async def assert_context_persistence_runtime() -> None:
    from conversation_manager import ConversationManager
    from jorge_engines_optimized import JorgeLeadEngineOptimized, OptimizedResponse

    class DummyGHL:
        pass

    storage_dir = Path(__file__).resolve().parent / "data" / "conversations" / "standalone_checks"
    manager = ConversationManager(storage_dir=str(storage_dir))
    engine = JorgeLeadEngineOptimized(manager, DummyGHL())

    response = OptimizedResponse(
        message="Test response",
        confidence_score=0.9,
        tone_quality="test",
        business_context={},
    )

    await engine._safe_update_context(
        contact_id="standalone-contact",
        location_id="standalone-location",
        user_message="Need a home in Plano",
        response=response,
        lead_data={"timeline": "30_days", "budget_max": 600000, "financing_status": "pre_approved"},
        lead_score=88.0,
    )

    context = await manager.get_context("standalone-contact", "standalone-location")
    assert context["lead_score"] == 88.0
    assert context["lead_temperature"] == "hot"
    assert len(context["conversation_history"]) >= 1


async def main() -> int:
    assert_required_imports()
    assert_ghl_contract_surface()
    assert_webhook_signature_helpers()
    await assert_context_persistence_runtime()

    print("Standalone validation passed: runtime integrity checks are green.")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except AssertionError as exc:
        print(f"Standalone validation failed: {exc}")
        exit_code = 1
    except Exception as exc:
        print(f"Standalone validation error: {exc}")
        exit_code = 1

    sys.exit(exit_code)
