import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Test Custom Webhook Alert Channel

Tests custom webhook connectivity for PagerDuty, Opsgenie, and generic webhooks.
Uses environment variables for configuration.

Usage:
    python test_webhook.py [--mock] [--verbose]

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
logger = logging.getLogger("test_webhook")


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

    async def post(self, url: str, json: dict = None, headers: dict = None, **kwargs) -> MockResponse:
        self.posts.append({"url": url, "json": json, "headers": headers, "kwargs": kwargs})
        logger.info(f"[MOCK] POST {url}")
        logger.info(f"[MOCK] Headers: {headers}")
        logger.info(f"[MOCK] Payload: {json}")
        return MockResponse(status=200, data={"status": "success"})


def create_test_alert(severity: str = "warning") -> Alert:
    """Create a test alert for testing purposes."""
    return Alert(
        id="test-webhook-9012",
        rule_name="test_webhook_alert",
        severity=severity,
        message="This is a test custom webhook alert.\nError Rate: 6.5%",
        triggered_at=time.time(),
        performance_stats={
            "error_rate": 0.065,
            "cache_hit_rate": 0.45,
            "handoff_success_rate": 0.92,
            "lead_bot": {"p95_latency_ms": 2100},
            "buyer_bot": {"p95_latency_ms": 2600},
            "seller_bot": {"p95_latency_ms": 2400},
        },
        channels_sent=[],
    )


def format_pagerduty_payload(alert: Alert) -> dict:
    """Format alert payload for PagerDuty Events API v2."""
    return {
        "routing_key": os.getenv("ALERT_WEBHOOK_PAGERDUTY_API_KEY", ""),
        "event_action": "trigger",
        "dedup_key": f"jorge_{alert.rule_name}_{int(alert.triggered_at)}",
        "payload": {
            "summary": f"[{alert.severity.upper()}] {alert.rule_name} - Jorge Bot Alert",
            "severity": "critical"
            if alert.severity == "critical"
            else ("warning" if alert.severity == "warning" else "info"),
            "source": f"jorge-bot-{os.getenv('ENVIRONMENT', 'development')}",
            "timestamp": datetime.fromtimestamp(alert.triggered_at).isoformat(),
            "component": "jorge-bot",
            "group": "alerts",
            "class": "alert",
            "custom_details": {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "message": alert.message,
                "performance_stats": alert.performance_stats,
            },
        },
        "links": [{"href": f"https://dashboard.enterprisehub.com/jorge/alerts/{alert.id}", "text": "View Alert"}],
    }


def format_opsgenie_payload(alert: Alert) -> dict:
    """Format alert payload for OpsGenie."""
    return {
        "message": f"[{alert.severity.upper()}] {alert.rule_name}",
        "alias": f"jorge-alert-{alert.id}",
        "description": alert.message,
        "priority": "P1" if alert.severity == "critical" else ("P2" if alert.severity == "warning" else "P3"),
        "tags": ["jorge", alert.rule_name, os.getenv("ENVIRONMENT", "development")],
        "entity": f"jorge-bot-{os.getenv('ENVIRONMENT', 'development')}",
        "source": "Jorge Bot Alerting System",
        "timestamp": int(alert.triggered_at),
        "extra_details": {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "performance_stats": alert.performance_stats,
        },
        "actions": ["ViewDashboard", "Acknowledge"],
        "links": [
            {"title": "View in Dashboard", "url": f"https://dashboard.enterprisehub.com/jorge/alerts/{alert.id}"}
        ],
    }


def format_custom_payload(alert: Alert) -> dict:
    """Format alert payload for generic webhook."""
    return {
        "version": "1.0",
        "type": "alert",
        "timestamp": datetime.fromtimestamp(alert.triggered_at).isoformat(),
        "service": "jorge-bot",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "alert": {
            "id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "message": alert.message,
            "status": "firing",
        },
        "metrics": {
            "error_rate": alert.performance_stats.get("error_rate", 0),
            "cache_hit_rate": alert.performance_stats.get("cache_hit_rate", 0),
            "handoff_success_rate": alert.performance_stats.get("handoff_success_rate", 0),
        },
        "bots": {
            "lead": alert.performance_stats.get("lead_bot", {}),
            "buyer": alert.performance_stats.get("buyer_bot", {}),
            "seller": alert.performance_stats.get("seller_bot", {}),
        },
    }


def test_webhook_configuration():
    """Test custom webhook configuration."""
    logger.info("=" * 60)
    logger.info("TEST: Custom Webhook Configuration")
    logger.info("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Check required environment variables
    logger.info("\n[Test 1] Checking required environment variables...")

    webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
    pagerduty_url = os.getenv("ALERT_WEBHOOK_PAGERDUTY_URL", "")
    opsgenie_url = os.getenv("ALERT_WEBHOOK_OPSGENIE_URL", "")
    webhook_headers = os.getenv("ALERT_WEBHOOK_HEADERS", '{"Content-Type": "application/json"}')

    if not webhook_url:
        logger.warning("  ⚠️  ALERT_WEBHOOK_URL not set")
    else:
        logger.info(f"  ✓ ALERT_WEBHOOK_URL: {webhook_url[:50]}...")
        tests_passed += 1

    if not pagerduty_url:
        logger.warning("  ⚠️  ALERT_WEBHOOK_PAGERDUTY_URL not set")
    else:
        logger.info(f"  ✓ ALERT_WEBHOOK_PAGERDUTY_URL: {pagerduty_url[:50]}...")
        tests_passed += 1

    if not opsgenie_url:
        logger.warning("  ⚠️  ALERT_WEBHOOK_OPSGENIE_URL not set")
    else:
        logger.info(f"  ✓ ALERT_WEBHOOK_OPSGENIE_URL: {opsgenie_url[:50]}...")
        tests_passed += 1

    # Test webhook headers parsing
    try:
        headers = json.loads(webhook_headers)
        logger.info(f"  ✓ ALERT_WEBHOOK_HEADERS parsed: {list(headers.keys())}")
        tests_passed += 1
    except json.JSONDecodeError as e:
        logger.error(f"  ✗ ALERT_WEBHOOK_HEADERS parse error: {e}")
        tests_failed += 1

    # Test 2: Validate PagerDuty payload format
    logger.info("\n[Test 2] Validating PagerDuty payload format...")

    try:
        alert = create_test_alert(severity="critical")
        payload = format_pagerduty_payload(alert)

        required_fields = ["routing_key", "event_action", "dedup_key", "payload"]
        for field in required_fields:
            if field in payload:
                logger.info(f"  ✓ '{field}' field present")
                tests_passed += 1
            else:
                logger.error(f"  ✗ '{field}' field missing")
                tests_failed += 1

        payload_fields = payload.get("payload", {})
        payload_required = ["summary", "severity", "source"]
        for field in payload_required:
            if field in payload_fields:
                logger.info(f"  ✓ payload.'{field}' field present")
                tests_passed += 1
            else:
                logger.error(f"  ✗ payload.'{field}' field missing")
                tests_failed += 1

    except Exception as e:
        logger.error(f"  ✗ PagerDuty payload validation failed: {e}")
        tests_failed += 1

    # Test 3: Validate OpsGenie payload format
    logger.info("\n[Test 3] Validating OpsGenie payload format...")

    try:
        alert = create_test_alert(severity="warning")
        payload = format_opsgenie_payload(alert)

        required_fields = ["message", "priority", "description"]
        for field in required_fields:
            if field in payload:
                logger.info(f"  ✓ '{field}' field present")
                tests_passed += 1
            else:
                logger.error(f"  ✗ '{field}' field missing")
                tests_failed += 1

    except Exception as e:
        logger.error(f"  ✗ OpsGenie payload validation failed: {e}")
        tests_failed += 1

    # Test 4: Validate custom webhook payload format
    logger.info("\n[Test 4] Validating custom webhook payload format...")

    try:
        alert = create_test_alert(severity="info")
        payload = format_custom_payload(alert)

        required_fields = ["version", "type", "timestamp", "service", "alert"]
        for field in required_fields:
            if field in payload:
                logger.info(f"  ✓ '{field}' field present")
                tests_passed += 1
            else:
                logger.error(f"  ✗ '{field}' field missing")
                tests_failed += 1

    except Exception as e:
        logger.error(f"  ✗ Custom webhook payload validation failed: {e}")
        tests_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SUMMARY: {tests_passed} passed, {tests_failed} failed")
    logger.info("=" * 60)

    return tests_failed == 0


async def test_webhook_delivery(mock: bool = True) -> bool:
    """Test webhook delivery for different providers."""
    logger.info("=" * 60)
    logger.info("TEST: Custom Webhook Delivery" + (" (MOCK)" if mock else ""))
    logger.info("=" * 60)

    tests_passed = 0
    tests_failed = 0

    webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
    pagerduty_url = os.getenv("ALERT_WEBHOOK_PAGERDUTY_URL", "")
    opsgenie_url = os.getenv("ALERT_WEBHOOK_OPSGENIE_URL", "")

    # Parse headers
    try:
        headers = json.loads(os.getenv("ALERT_WEBHOOK_HEADERS", '{"Content-Type": "application/json"}'))
    except json.JSONDecodeError:
        headers = {"Content-Type": "application/json"}

    # Test 1: Custom webhook delivery
    if webhook_url:
        logger.info("\n[Test] Testing custom webhook delivery...")
        alert = create_test_alert(severity="critical")
        payload = format_custom_payload(alert)

        try:
            if mock:
                session = MockaiohttpSession()
                async with session as mock_session:
                    async with mock_session.post(webhook_url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                logger.info("  ✓ Custom webhook delivered (mock)")
                tests_passed += 1
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response.raise_for_status()
                logger.info("  ✓ Custom webhook delivered")
                tests_passed += 1
        except Exception as e:
            logger.error(f"  ✗ Custom webhook delivery failed: {e}")
            tests_failed += 1

    # Test 2: PagerDuty webhook delivery
    if pagerduty_url:
        logger.info("\n[Test] Testing PagerDuty webhook delivery...")
        alert = create_test_alert(severity="critical")
        payload = format_pagerduty_payload(alert)

        try:
            if mock:
                session = MockaiohttpSession()
                async with session as mock_session:
                    async with mock_session.post(pagerduty_url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                logger.info("  ✓ PagerDuty webhook delivered (mock)")
                tests_passed += 1
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        pagerduty_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response.raise_for_status()
                logger.info("  ✓ PagerDuty webhook delivered")
                tests_passed += 1
        except Exception as e:
            logger.error(f"  ✗ PagerDuty webhook delivery failed: {e}")
            tests_failed += 1

    # Test 3: OpsGenie webhook delivery
    if opsgenie_url:
        logger.info("\n[Test] Testing OpsGenie webhook delivery...")
        alert = create_test_alert(severity="warning")
        payload = format_opsgenie_payload(alert)

        try:
            if mock:
                session = MockaiohttpSession()
                async with session as mock_session:
                    async with mock_session.post(opsgenie_url, json=payload, headers=headers) as response:
                        response.raise_for_status()
                logger.info("  ✓ OpsGenie webhook delivered (mock)")
                tests_passed += 1
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        opsgenie_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response.raise_for_status()
                logger.info("  ✓ OpsGenie webhook delivered")
                tests_passed += 1
        except Exception as e:
            logger.error(f"  ✗ OpsGenie webhook delivery failed: {e}")
            tests_failed += 1

    # Test 4: Test webhook alert cooldowns
    logger.info("\n[Test] Testing webhook alert cooldowns...")

    AlertingService.reset()
    service = AlertingService()

    test_rule = AlertRule(
        name="test_webhook_cooldown",
        condition=lambda stats: True,
        severity="warning",
        cooldown_seconds=1,
        channels=["webhook"],
        description="Test webhook cooldown rule",
    )
    await service.add_rule(test_rule)

    stats = {"test_metric": 1}
    alerts1 = await service.check_alerts(stats)

    if len(alerts1) == 1:
        logger.info("  ✓ First webhook alert triggered")
        tests_passed += 1
    else:
        logger.error("  ✗ First webhook alert not triggered")
        tests_failed += 1

    alerts2 = await service.check_alerts(stats)

    if len(alerts2) == 0:
        logger.info("  ✓ Second webhook alert blocked by cooldown")
        tests_passed += 1
    else:
        logger.error("  ✗ Second webhook alert not blocked")
        tests_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SUMMARY: {tests_passed} passed, {tests_failed} failed")
    logger.info("=" * 60)

    return tests_failed == 0


async def run_all_tests(mock: bool = True, verbose: bool = False):
    """Run all webhook tests."""
    logger.info("\n" + "=" * 60)
    logger.info("CUSTOM WEBHOOK ALERT CHANNEL TESTS")
    logger.info("=" * 60)

    all_passed = True

    # Configuration test
    if not test_webhook_configuration():
        all_passed = False

    # Delivery test
    if not await test_webhook_delivery(mock=mock):
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
    parser = argparse.ArgumentParser(description="Test custom webhook alert channel")
    parser.add_argument("--mock", action="store_true", default=True, help="Run tests in mock mode (default: True)")
    parser.add_argument("--no-mock", action="store_true", help="Disable mock mode (send actual webhooks)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    mock_mode = not args.no_mock

    if not mock_mode:
        logger.warning("⚠️  WARNING: Running in non-mock mode will send actual webhooks!")
        logger.warning("⚠️  Make sure your webhook URLs are correct.")

    success = asyncio.run(run_all_tests(mock=mock_mode, verbose=args.verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
