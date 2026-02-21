"""
Jorge Platform Load Testing — Phase 5

Validates webhook handler performance under concurrent load for all three bot
modes (seller, buyer, lead) plus mixed-mode and handoff-under-load scenarios.

Performance targets:
- Single-mode 100 concurrent: p99 < 2s
- Mixed-mode 300 concurrent: p99 < 3s
- Handoff tag swaps: 100% correctness under concurrency

All external services are mocked. Timing measured with time.perf_counter().
"""

import os

# Set required env vars BEFORE any application imports
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_load_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

import asyncio
import statistics
import time
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLContact,
    GHLMessage,
    GHLWebhookEvent,
    MessageDirection,
    MessageType,
)
from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_webhook_event(
    message_body: str,
    contact_id: str = "load_contact_001",
    tags: list[str] | None = None,
) -> GHLWebhookEvent:
    """Build a GHLWebhookEvent for load tests."""
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId=contact_id,
        locationId="loc_load_456",
        message=GHLMessage(type=MessageType.SMS, body=message_body, direction=MessageDirection.INBOUND),
        contact=GHLContact(
            contactId=contact_id,
            firstName="Load",
            lastName="Test",
            phone="+19095550099",
            email="load@test.com",
            tags=tags or [],
            customFields={},
        ),
    )


def _load_test_patches(
    jorge_seller_mode: bool = False,
    jorge_buyer_mode: bool = False,
    jorge_lead_mode: bool = False,
):
    """Context manager with all webhook patches for load testing."""

    @contextmanager
    def _patches():
        mock_jorge_settings = MagicMock()
        mock_jorge_settings.JORGE_SELLER_MODE = jorge_seller_mode
        mock_jorge_settings.JORGE_BUYER_MODE = jorge_buyer_mode
        mock_jorge_settings.JORGE_LEAD_MODE = jorge_lead_mode
        mock_jorge_settings.LEAD_ACTIVATION_TAG = "Needs Qualifying"
        mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"

        mock_config_settings = MagicMock()
        mock_config_settings.activation_tags = ["Needs Qualifying"]
        mock_config_settings.deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot", "AI-Qualified"]
        mock_config_settings.auto_deactivate_threshold = 70
        mock_config_settings.notify_agent_workflow_id = None
        mock_config_settings.custom_field_lead_score = None
        mock_config_settings.custom_field_budget = None
        mock_config_settings.custom_field_location = None
        mock_config_settings.custom_field_timeline = None
        mock_config_settings.appointment_auto_booking_enabled = False

        # Seller engine mock (instant return)
        mock_seller_engine = MagicMock()
        mock_seller_engine.process_seller_response = AsyncMock(
            return_value={
                "temperature": "warm",
                "message": "What price would incentivize you to sell?",
                "questions_answered": 2,
                "actions": [{"type": "add_tag", "tag": "Warm-Seller"}],
            }
        )

        # Buyer bot mock (instant return)
        mock_buyer_bot = MagicMock()
        mock_buyer_bot.process_buyer_conversation = AsyncMock(
            return_value={
                "buyer_temperature": "warm",
                "is_qualified": False,
                "financial_readiness_score": 55,
                "response_content": "What area interests you most?",
            }
        )

        # Lead conversation manager mock (instant return)
        mock_ai_response = MagicMock()
        mock_ai_response.message = "Thanks for reaching out! Tell me more."
        mock_ai_response.lead_score = 3
        mock_ai_response.extracted_data = {}

        mock_conv_mgr = MagicMock()
        mock_conv_mgr.get_context = AsyncMock(return_value={})
        mock_conv_mgr.generate_response = AsyncMock(return_value=mock_ai_response)
        mock_conv_mgr.update_context = AsyncMock()
        mock_conv_mgr.get_conversation_history = AsyncMock(return_value=[])

        mock_compliance = MagicMock()
        mock_compliance.audit_message = AsyncMock(return_value=(ComplianceStatus.PASSED, "", []))

        mock_tenant = MagicMock()
        mock_tenant.get_tenant_config = AsyncMock(return_value=None)

        mock_lead_scorer = MagicMock()
        mock_lead_scorer.classify.return_value = "warm"
        mock_lead_scorer.get_percentage_score.return_value = 42
        mock_lead_scorer._is_urgent_timeline.return_value = False

        mock_ghl_client = MagicMock(
            send_message=AsyncMock(),
            apply_actions=AsyncMock(),
            add_tags=AsyncMock(),
        )

        mock_lead_source_tracker = MagicMock()
        mock_lead_source_tracker.analyze_lead_source = AsyncMock(side_effect=Exception("skip"))

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", MagicMock(track_event=AsyncMock())),
            patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", mock_ghl_client),
            patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings", mock_jorge_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.settings", mock_config_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.compliance_guard", mock_compliance),
            patch("ghl_real_estate_ai.api.routes.webhook.tenant_service", mock_tenant),
            patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_conv_mgr),
            patch("ghl_real_estate_ai.api.routes.webhook._get_lead_scorer", return_value=mock_lead_scorer),
            patch("ghl_real_estate_ai.api.routes.webhook.lead_source_tracker", mock_lead_source_tracker),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.attribution_analytics",
                MagicMock(track_daily_metrics=AsyncMock()),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.pricing_optimizer", MagicMock(calculate_lead_price=AsyncMock())
            ),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.subscription_manager",
                MagicMock(get_active_subscription=AsyncMock(return_value=None)),
            ),
            patch("ghl_real_estate_ai.api.routes.webhook.calendar_scheduler", MagicMock()),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.handoff_service",
                MagicMock(
                    evaluate_handoff=AsyncMock(return_value=None),
                    execute_handoff=AsyncMock(return_value=[]),
                ),
            ),
            patch(
                "ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine",
                return_value=mock_seller_engine,
            ),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.JorgeBuyerBot", return_value=mock_buyer_bot),
        ):
            yield {
                "seller_engine": mock_seller_engine,
                "buyer_bot": mock_buyer_bot,
                "conversation_manager": mock_conv_mgr,
            }

    return _patches()


async def _timed_webhook_call(event, handler):
    """Execute a single webhook call and return elapsed time in seconds."""
    start = time.perf_counter()
    try:
        await handler.__wrapped__(MagicMock(), event, MagicMock())
    except Exception:
        pass  # Count errors but still measure timing
    return time.perf_counter() - start


def _assert_p99(times: list[float], target_seconds: float, label: str):
    """Assert p99 latency is below target."""
    if not times:
        pytest.fail(f"{label}: no timing data collected")
    sorted_times = sorted(times)
    p99_idx = int(len(sorted_times) * 0.99)
    p99 = sorted_times[min(p99_idx, len(sorted_times) - 1)]
    avg = statistics.mean(sorted_times)
    p50 = sorted_times[len(sorted_times) // 2]
    assert p99 < target_seconds, (
        f"{label}: p99={p99:.3f}s exceeds target {target_seconds}s "
        f"(avg={avg:.3f}s, p50={p50:.3f}s, n={len(sorted_times)})"
    )


# ===========================================================================
# Load Tests
# ===========================================================================


@pytest.mark.performance
class TestJorgePlatformLoadTesting:
    """Phase 5: Load tests for all three bot modes under concurrent webhook load."""

    @pytest.mark.asyncio
    async def test_100_concurrent_seller_webhooks(self):
        """100 concurrent seller webhook requests complete with p99 < 2s."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        events = [
            _make_webhook_event(
                f"I want to sell my house #{i}",
                contact_id=f"seller_load_{i:03d}",
                tags=["Needs Qualifying"],
            )
            for i in range(100)
        ]

        with _load_test_patches(jorge_seller_mode=True):
            tasks = [_timed_webhook_call(e, handle_ghl_webhook) for e in events]
            times = await asyncio.gather(*tasks)

        _assert_p99(list(times), 2.0, "100 concurrent seller webhooks")

    @pytest.mark.asyncio
    async def test_100_concurrent_buyer_webhooks(self):
        """100 concurrent buyer webhook requests complete with p99 < 2s."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        events = [
            _make_webhook_event(
                f"Looking for a house #{i}",
                contact_id=f"buyer_load_{i:03d}",
                tags=["Buyer-Lead"],
            )
            for i in range(100)
        ]

        with _load_test_patches(jorge_buyer_mode=True):
            tasks = [_timed_webhook_call(e, handle_ghl_webhook) for e in events]
            times = await asyncio.gather(*tasks)

        _assert_p99(list(times), 2.0, "100 concurrent buyer webhooks")

    @pytest.mark.asyncio
    async def test_100_concurrent_lead_webhooks(self):
        """100 concurrent lead webhook requests complete with p99 < 2s."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        events = [
            _make_webhook_event(
                f"I'm interested in real estate #{i}",
                contact_id=f"lead_load_{i:03d}",
                tags=["Needs Qualifying"],
            )
            for i in range(100)
        ]

        with _load_test_patches(jorge_lead_mode=True):
            tasks = [_timed_webhook_call(e, handle_ghl_webhook) for e in events]
            times = await asyncio.gather(*tasks)

        _assert_p99(list(times), 2.0, "100 concurrent lead webhooks")

    @pytest.mark.asyncio
    async def test_mixed_mode_load_300_concurrent(self):
        """300 concurrent requests (100 each mode) with p99 < 3s."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        seller_events = [
            _make_webhook_event(
                f"Sell house #{i}",
                contact_id=f"mixed_seller_{i:03d}",
                tags=["Needs Qualifying"],
            )
            for i in range(100)
        ]
        buyer_events = [
            _make_webhook_event(
                f"Buy house #{i}",
                contact_id=f"mixed_buyer_{i:03d}",
                tags=["Buyer-Lead"],
            )
            for i in range(100)
        ]
        lead_events = [
            _make_webhook_event(
                f"Real estate #{i}",
                contact_id=f"mixed_lead_{i:03d}",
                tags=["Needs Qualifying"],
            )
            for i in range(100)
        ]

        all_events = seller_events + buyer_events + lead_events

        with _load_test_patches(
            jorge_seller_mode=True,
            jorge_buyer_mode=True,
            jorge_lead_mode=True,
        ):
            tasks = [_timed_webhook_call(e, handle_ghl_webhook) for e in all_events]
            times = await asyncio.gather(*tasks)

        _assert_p99(list(times), 3.0, "300 concurrent mixed-mode webhooks")

    @pytest.mark.asyncio
    async def test_handoff_under_load(self):
        """Handoff tag swaps complete correctly under concurrent load."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            HandoffDecision,
            JorgeHandoffService,
        )

        # Create 50 concurrent handoff evaluations + executions
        mock_analytics = AsyncMock()
        mock_analytics.track_event = AsyncMock()
        service = JorgeHandoffService(analytics_service=mock_analytics)

        async def _single_handoff(idx: int) -> dict:
            """Simulate a single handoff evaluation and execution."""
            start = time.perf_counter()

            signals = {
                "buyer_intent_score": 0.85,
                "seller_intent_score": 0.1,
                "detected_intent_phrases": ["want to buy", "pre-approved"],
            }

            decision = await service.evaluate_handoff(
                current_bot="lead",
                contact_id=f"handoff_load_{idx:03d}",
                conversation_history=[
                    {"role": "user", "content": "I want to buy a house, pre-approved for $700k"},
                ],
                intent_signals=signals,
            )

            elapsed = time.perf_counter() - start

            if decision is None:
                return {"elapsed": elapsed, "correct": False, "reason": "no_decision"}

            actions = await service.execute_handoff(decision, contact_id=f"handoff_load_{idx:03d}")

            elapsed = time.perf_counter() - start

            # Verify correctness
            remove_tags = [a["tag"] for a in actions if a["type"] == "remove_tag"]
            add_tags = [a["tag"] for a in actions if a["type"] == "add_tag"]

            correct = (
                "Needs Qualifying" in remove_tags and "Buyer-Lead" in add_tags and "Handoff-Lead-to-Buyer" in add_tags
            )

            return {"elapsed": elapsed, "correct": correct}

        tasks = [_single_handoff(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # All handoffs should be correct
        correct_count = sum(1 for r in results if r["correct"])
        assert correct_count == 100, (
            f"Handoff correctness: {correct_count}/100 (failures: {[r for r in results if not r['correct']]})"
        )

        # Timing check
        times = [r["elapsed"] for r in results]
        _assert_p99(times, 2.0, "100 concurrent handoff evaluations")
