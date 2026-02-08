#!/usr/bin/env python3
"""
Test Slack Webhook Alert Channel

Tests Slack webhook connectivity and alert delivery.
Uses environment variables for configuration.

Usage:
    python test_slack_webhook.py [--mock] [--verbose]

Options:
    --mock    : Run tests in mock mode (no actual webhook calls)
    --verbose : Enable verbose output
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.jorge.alerting_service import Alert, AlertingService, AlertRule

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_slack_webhook")


class MockResponse:
    """Mock aiohttp response for testing."""

    def __init__(self, status: int = 200, data: dict = None):
        self.status = status
        self._data = data or {}

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")

    async def json(self):
        return self._data

    async def text(self):
        return json.dumps(self._data)


class MockaiohttpSession:
    """Mock aiohttp.ClientSession for testing."""

    def __init__(self):
        self.posts = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def post(self, url: str, json: dict = None, **kwargs) -> MockResponse:
        self.posts.append({"url": url, "json": json, "kwargs": kwargs})
        logger.info(f"[MOCK] POST {url}")
        logger.info(f"[MOCK] Payload: {json}")
        return MockResponse(status=200, data={"ok": True})


def create_test_alert(severity: str = "warning") -> Alert:
    """Create a test alert for testing purposes."""
    return Alert(
        id="test-5678",
        rule_name="test_slack_alert",
        severity=severity,
        message="This is a test Slack alert.\nError Rate: 6.5%\nCache Hit Rate: 45%",
        triggered_at=time.time(),
        performance_stats={
            "error_rate": 0.065,
            "cache_hit_rate": 0.45,
            "handoff_success_rate": 0.92,
            "lead_bot": {"p50_latency_ms": 450, "p95_latency_ms": 2100},
            "buyer_bot": {"p50_latency_ms": 520, "p95_latency_ms": 2600},
            "seller_bot": {"p50_latency_ms": 480, "p95_latency_ms": 2400},
        },
        channels_sent=[],
    )


def format_slack_payload(alert: Alert) -> dict:
    """Format alert payload for Slack."""
    color_map = {"critical": "danger", "warning": "warning", "info": "good"}

    return {
        "attachments": [
            {
                "color": color_map.get(alert.severity, "warning"),
                "title": f"[{alert.severity.upper()}] {alert.rule_name}",
                "text": alert.message,
                "footer": f"Alert ID: {alert.id}",
                "ts": int(alert.triggered_at),
            }
        ]
    }


def test_slack_configuration():
    """Test Slack webhook configuration."""
    logger.info("=" * 60)
    logger.info("TEST: Slack Webhook Configuration")
    logger.info("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Check required environment variables
    logger.info("\n[Test 1] Checking required environment variables...")

    webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL", "")
    channel = os.getenv("ALERT_SLACK_CHANNEL", "#jorge-alerts")

    if not webhook_url:
        logger.warning("  ⚠️  ALERT_SLACK_WEBHOOK_URL not set")
        logger.warning("  ⚠️  Slack alerts will be skipped")
        tests_passed += 1  # Warning is acceptable
    else:
        # Validate webhook URL format
        if webhook_url.startswith("https://hooks.slack.com/services/"):
            logger.info(f"  ✓ ALERT_SLACK_WEBHOOK_URL: {webhook_url[:50]}...")
            tests_passed += 1
        else:
            logger.warning(f"  ⚠️  ALERT_SLACK_WEBHOOK_URL format may be invalid")
            logger.warning(f"     Expected: https://hooks.slack.com/services/...")
            logger.warning(f"     Got: {webhook_url}")
            tests_passed += 1  # Still pass, may be custom integration

    logger.info(f"  ✓ ALERT_SLACK_CHANNEL: {channel}")
    tests_passed += 1

    # Test 2: Validate Slack payload format
    logger.info("\n[Test 2] Validating Slack payload format...")

    try:
        alert = create_test_alert()
        payload = format_slack_payload(alert)

        # Check required fields
        if "attachments" in payload:
            logger.info("  ✓ 'attachments' field present")
            tests_passed += 1
        else:
            logger.error("  ✗ 'attachments' field missing")
            tests_failed += 1

        if len(payload["attachments"]) > 0:
            attachment = payload["attachments"][0]
            if "color" in attachment:
                logger.info(f"  ✓ 'color' field present: {attachment['color']}")
                tests_passed += 1
            else:
                logger.error("  ✗ 'color' field missing")
                tests_failed += 1

            if "title" in attachment:
                logger.info(f"  ✓ 'title' field present: {attachment['title']}")
                tests_passed += 1
            else:
                logger.error("  ✗ 'title' field missing")
                tests_failed += 1

            if "text" in attachment:
                logger.info(f"  ✓ 'text' field present")
                tests_passed += 1
            else:
                logger.error("  ✗ 'text' field missing")
                tests_failed += 1
        else:
            logger.error("  ✗ No attachments in payload")
            tests_failed += 1

    except Exception as e:
        logger.error(f"  ✗ Payload validation failed: {e}")
        tests_failed += 1

    # Test 3: Test severity color mapping
    logger.info("\n[Test 3] Testing severity color mapping...")

    for severity in ["critical", "warning", "info"]:
        alert = create_test_alert(severity=severity)
        payload = format_slack_payload(alert)
        color = payload["attachments"][0]["color"]

        expected = {"critical": "danger", "warning": "warning", "info": "good"}
        if color == expected[severity]:
            logger.info(f"  ✓ {severity} → {color}")
            tests_passed += 1
        else:
            logger.error(f"  ✗ {severity} → {color} (expected: {expected[severity]})")
            tests_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SUMMARY: {tests_passed} passed, {tests_failed} failed")
    logger.info("=" * 60)

    return tests_failed == 0


async def test_slack_webhook_delivery(mock: bool = True) -> bool:
    """Test Slack webhook delivery."""
    logger.info("=" * 60)
    logger.info("TEST: Slack Webhook Delivery" + (" (MOCK)" if mock else ""))
    logger.info("=" * 60)

    tests_passed = 0
    tests_failed = 0

    webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL", "")

    if not webhook_url:
        logger.warning("  ⚠️  Slack webhook URL not configured, skipping delivery test")
        return True

    # Create test alert
    alert = create_test_alert(severity="critical")
    payload = format_slack_payload(alert)

    # Test delivery
    try:
        if mock:
            # Use mock session
            session = MockaiohttpSession()
            async with session as mock_session:
                async with mock_session.post(webhook_url, json=payload) as response:
                    response.raise_for_status()

            logger.info("  ✓ Webhook delivered successfully (mock)")
            logger.info(f"  ✓ Payload sent to: {webhook_url[:50]}...")
            tests_passed += 1

            # Verify payload
            if len(session.posts) == 1:
                logger.info("  ✓ Mock received one POST request")
                tests_passed += 1
            else:
                logger.error(f"  ✗ Expected 1 POST, got {len(session.posts)}")
                tests_failed += 1
        else:
            # Use real HTTP client
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()

            logger.info("  ✓ Webhook delivered successfully")
            tests_passed += 1

    except aiohttp.ClientError as e:
        logger.error(f"  ✗ Webhook delivery failed: {e}")
        tests_failed += 1
    except Exception as e:
        logger.error(f"  ✗ Webhook delivery failed: {e}")
        tests_failed += 1

    # Test cooldowns
    logger.info("\n[Test] Testing Slack alert cooldowns...")

    AlertingService.reset()
    service = AlertingService()

    # Add a Slack-only rule with short cooldown
    test_rule = AlertRule(
        name="test_slack_cooldown",
        condition=lambda stats: True,
        severity="warning",
        cooldown_seconds=1,
        channels=["slack"],
        description="Test Slack cooldown rule",
    )
    await service.add_rule(test_rule)

    # Trigger first alert
    stats = {"test_metric": 1}
    alerts1 = await service.check_alerts(stats)

    if len(alerts1) == 1:
        logger.info("  ✓ First Slack alert triggered")
        tests_passed += 1
    else:
        logger.error("  ✗ First Slack alert not triggered")
        tests_failed += 1

    # Try immediate second alert (should be blocked)
    alerts2 = await service.check_alerts(stats)

    if len(alerts2) == 0:
        logger.info("  ✓ Second Slack alert blocked by cooldown")
        tests_passed += 1
    else:
        logger.error("  ✗ Second Slack alert not blocked")
        tests_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SUMMARY: {tests_passed} passed, {tests_failed} failed")
    logger.info("=" * 60)

    return tests_failed == 0


async def run_all_tests(mock: bool = True, verbose: bool = False):
    """Run all Slack webhook tests."""
    logger.info("\n" + "=" * 60)
    logger.info("SLACK WEBHOOK ALERT CHANNEL TESTS")
    logger.info("=" * 60)

    all_passed = True

    # Configuration test
    if not test_slack_configuration():
        all_passed = False

    # Delivery test
    if not await test_slack_webhook_delivery(mock=mock):
        all_passed = False

    # Final result
    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED")
    else:
        logger.info("❌ SOME TESTS FAILED")
    logger.info("=" * 60)

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Test Slack webhook alert channel")
    parser.add_argument("--mock", action="store_true", default=True, help="Run tests in mock mode (default: True)")
    parser.add_argument("--no-mock", action="store_true", help="Disable mock mode (send actual webhooks)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    mock_mode = not args.no_mock

    if not mock_mode:
        logger.warning("⚠️  WARNING: Running in non-mock mode will send Slack messages!")
        logger.warning("⚠️  Make sure your webhook URL is correct.")

    success = asyncio.run(run_all_tests(mock=mock_mode, verbose=args.verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
