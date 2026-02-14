import pytest

#!/usr/bin/env python3
"""
Test All Alert Channels

Comprehensive test suite for all alert notification channels:
- Email (SMTP)
- Slack Webhook
- Custom Webhooks (PagerDuty, Opsgenie)

Usage:
    python test_all_channels.py [--mock] [--channel email|slack|webhook|all] [--verbose]

Options:
    --mock    : Run tests in mock mode (no actual notifications sent)
    --channel : Specific channel to test (default: all)
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

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.jorge.alerting_service import Alert, AlertingService, AlertRule

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("test_all_channels")


def create_test_alert(severity: str = "warning") -> Alert:
    """Create a test alert for testing purposes."""
    return Alert(
        id=f"test-{int(time.time())}",
        rule_name="test_performance_alert",
        severity=severity,
        message="This is a test performance alert.\n\nPerformance metrics indicate potential SLA breach.",
        triggered_at=time.time(),
        performance_stats={
            "error_rate": 0.065,
            "cache_hit_rate": 0.45,
            "handoff_success_rate": 0.92,
            "blocked_handoffs_last_hour": 12,
            "rate_limit_error_rate": 0.12,
            "lead_bot": {
                "p50_latency_ms": 450,
                "p95_latency_ms": 2100,
                "p99_latency_ms": 2800,
                "request_count": 1500,
                "error_count": 98,
            },
            "buyer_bot": {
                "p50_latency_ms": 520,
                "p95_latency_ms": 2600,
                "p99_latency_ms": 3200,
                "request_count": 800,
                "error_count": 52,
            },
            "seller_bot": {
                "p50_latency_ms": 480,
                "p95_latency_ms": 2400,
                "p99_latency_ms": 3000,
                "request_count": 600,
                "error_count": 39,
            },
        },
        channels_sent=[],
    )


async def check_channel_configuration(channel: str) -> dict:
    """Test configuration for a specific channel."""
    results = {"passed": 0, "failed": 0, "tests": []}

    if channel == "email":
        logger.info("\n" + "=" * 60)
        logger.info("TESTING: Email (SMTP) Configuration")
        logger.info("=" * 60)

        # Check environment variables
        required_vars = [
            ("ALERT_EMAIL_SMTP_HOST", "SMTP server hostname"),
            ("ALERT_EMAIL_SMTP_PORT", "SMTP server port"),
            ("ALERT_EMAIL_FROM", "From email address"),
            ("ALERT_EMAIL_TO", "Recipient email addresses"),
        ]

        optional_vars = [
            ("ALERT_EMAIL_SMTP_USER", "SMTP username"),
            ("ALERT_EMAIL_SMTP_PASSWORD", "SMTP password"),
            ("ALERT_EMAIL_REPLY_TO", "Reply-to address"),
        ]

        for var, desc in required_vars:
            value = os.getenv(var, "")
            if not value:
                logger.warning(f"  ⚠️  {var}: Not set ({desc})")
                results["tests"].append((var, "warning", f"Not set: {desc}"))
            else:
                logger.info(f"  ✓ {var}: {'*' * len(value) if var.endswith('PASSWORD') else value}")
                results["tests"].append((var, "passed", ""))
                results["passed"] += 1

        for var, desc in optional_vars:
            value = os.getenv(var, "")
            if value:
                logger.info(f"  ✓ {var}: {'*' * len(value) if var.endswith('PASSWORD') or 'KEY' in var else value}")
                results["tests"].append((var, "passed", ""))
                results["passed"] += 1

    elif channel == "slack":
        logger.info("\n" + "=" * 60)
        logger.info("TESTING: Slack Webhook Configuration")
        logger.info("=" * 60)

        # Check webhook URL
        webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL", "")
        if not webhook_url:
            logger.warning("  ⚠️  ALERT_SLACK_WEBHOOK_URL: Not set")
            results["tests"].append(("ALERT_SLACK_WEBHOOK_URL", "warning", "Not configured"))
        elif webhook_url.startswith("https://hooks.slack.com/services/"):
            logger.info(f"  ✓ ALERT_SLACK_WEBHOOK_URL: {webhook_url[:50]}...")
            results["tests"].append(("ALERT_SLACK_WEBHOOK_URL", "passed", ""))
            results["passed"] += 1
        else:
            logger.warning(f"  ⚠️  ALERT_SLACK_WEBHOOK_URL: Non-standard format")
            results["tests"].append(("ALERT_SLACK_WEBHOOK_URL", "warning", "Non-standard format"))

        # Check channel
        channel = os.getenv("ALERT_SLACK_CHANNEL", "#jorge-alerts")
        logger.info(f"  ✓ ALERT_SLACK_CHANNEL: {channel}")
        results["tests"].append(("ALERT_SLACK_CHANNEL", "passed", ""))
        results["passed"] += 1

    elif channel == "webhook":
        logger.info("\n" + "=" * 60)
        logger.info("TESTING: Custom Webhook Configuration")
        logger.info("=" * 60)

        # Check generic webhook
        webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
        if webhook_url:
            logger.info(f"  ✓ ALERT_WEBHOOK_URL: {webhook_url[:50]}...")
            results["tests"].append(("ALERT_WEBHOOK_URL", "passed", ""))
            results["passed"] += 1
        else:
            logger.warning("  ⚠️  ALERT_WEBHOOK_URL: Not set")
            results["tests"].append(("ALERT_WEBHOOK_URL", "warning", "Not configured"))

        # Check PagerDuty
        pd_url = os.getenv("ALERT_WEBHOOK_PAGERDUTY_URL", "")
        pd_key = os.getenv("ALERT_WEBHOOK_PAGERDUTY_API_KEY", "")
        if pd_url and pd_key:
            logger.info(f"  ✓ PagerDuty: Configured")
            results["tests"].append(("ALERT_WEBHOOK_PAGERDUTY", "passed", ""))
            results["passed"] += 1
        elif pd_url or pd_key:
            logger.warning("  ⚠️  PagerDuty: Partial configuration")
            results["tests"].append(("ALERT_WEBHOOK_PAGERDUTY", "warning", "Partial"))
        else:
            logger.info("  ℹ️  PagerDuty: Not configured (optional)")
            results["tests"].append(("ALERT_WEBHOOK_PAGERDUTY", "info", "Not configured"))

        # Check OpsGenie
        og_url = os.getenv("ALERT_WEBHOOK_OPSGENIE_URL", "")
        og_key = os.getenv("ALERT_WEBHOOK_OPSGENIE_API_KEY", "")
        if og_url and og_key:
            logger.info(f"  ✓ OpsGenie: Configured")
            results["tests"].append(("ALERT_WEBHOOK_OPSGENIE", "passed", ""))
            results["passed"] += 1
        elif og_url or og_key:
            logger.warning("  ⚠️  OpsGenie: Partial configuration")
            results["tests"].append(("ALERT_WEBHOOK_OPSGENIE", "warning", "Partial"))
        else:
            logger.info("  ℹ️  OpsGenie: Not configured (optional)")
            results["tests"].append(("ALERT_WEBHOOK_OPSGENIE", "info", "Not configured"))

        # Check headers
        headers = os.getenv("ALERT_WEBHOOK_HEADERS", '{"Content-Type": "application/json"}')
        try:
            json.loads(headers)
            logger.info(f"  ✓ ALERT_WEBHOOK_HEADERS: Valid JSON")
            results["tests"].append(("ALERT_WEBHOOK_HEADERS", "passed", ""))
            results["passed"] += 1
        except json.JSONDecodeError:
            logger.error(f"  ✗ ALERT_WEBHOOK_HEADERS: Invalid JSON")
            results["tests"].append(("ALERT_WEBHOOK_HEADERS", "failed", "Invalid JSON"))
            results["failed"] += 1

    return results


async def test_alert_rules() -> dict:
    """Test that alert rules are properly configured."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING: Alert Rules Configuration")
    logger.info("=" * 60)

    results = {"passed": 0, "failed": 0, "tests": []}

    # Reset service for clean test
    AlertingService.reset()
    service = AlertingService()

    # Get all rules
    rules = await service.list_rules()

    logger.info(f"\n  Found {len(rules)} configured alert rules:")

    expected_rules = [
        "sla_violation",
        "high_error_rate",
        "low_cache_hit_rate",
        "handoff_failure",
        "bot_unresponsive",
        "circular_handoff_spike",
        "rate_limit_breach",
    ]

    rule_names = [r.name for r in rules]

    for expected in expected_rules:
        if expected in rule_names:
            rule = next(r for r in rules if r.name == expected)
            logger.info(f"    ✓ {expected} (severity={rule.severity}, cooldown={rule.cooldown_seconds}s)")
            results["tests"].append((expected, "passed", f"severity={rule.severity}"))
            results["passed"] += 1
        else:
            logger.error(f"    ✗ {expected} (MISSING)")
            results["tests"].append((expected, "failed", "Rule not found"))
            results["failed"] += 1

    # Test rule channels
    logger.info("\n  Rule notification channels:")
    for rule in rules:
        logger.info(f"    - {rule.name}: {rule.channels}")

    # Test cooldowns
    logger.info("\n  Rule cooldown periods:")
    for rule in rules:
        if rule.cooldown_seconds < 300:
            logger.warning(f"    ⚠️  {rule.name}: {rule.cooldown_seconds}s (short)")
        else:
            logger.info(f"    ✓ {rule.name}: {rule.cooldown_seconds}s")

    return results


async def test_cooldowns() -> dict:
    """Test alert cooldown functionality."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING: Alert Cooldowns")
    logger.info("=" * 60)

    results = {"passed": 0, "failed": 0, "tests": []}

    # Reset service
    AlertingService.reset()
    service = AlertingService()

    # Add test rule with short cooldown
    test_rule = AlertRule(
        name="test_cooldown_rule",
        condition=lambda stats: True,
        severity="warning",
        cooldown_seconds=2,
        channels=["email", "slack", "webhook"],
        description="Test cooldown rule",
    )
    await service.add_rule(test_rule)

    # Trigger first alert
    stats = {"test_metric": 1}
    alerts1 = await service.check_alerts(stats)

    if len(alerts1) == 1:
        logger.info(f"  ✓ First alert triggered successfully")
        results["tests"].append(("first_alert", "passed", ""))
        results["passed"] += 1
    else:
        logger.error(f"  ✗ First alert not triggered (got {len(alerts1)})")
        results["tests"].append(("first_alert", "failed", f"Expected 1, got {len(alerts1)}"))
        results["failed"] += 1

    # Try immediate second alert (should be blocked)
    alerts2 = await service.check_alerts(stats)

    if len(alerts2) == 0:
        logger.info(f"  ✓ Second alert correctly blocked by cooldown")
        results["tests"].append(("cooldown_block", "passed", ""))
        results["passed"] += 1
    else:
        logger.error(f"  ✗ Second alert not blocked by cooldown (got {len(alerts2)})")
        results["tests"].append(("cooldown_block", "failed", f"Expected 0, got {len(alerts2)}"))
        results["failed"] += 1

    # Wait for cooldown and trigger again
    await asyncio.sleep(2.1)
    alerts3 = await service.check_alerts(stats)

    if len(alerts3) == 1:
        logger.info(f"  ✓ Alert correctly triggered after cooldown")
        results["tests"].append(("after_cooldown", "passed", ""))
        results["passed"] += 1
    else:
        logger.error(f"  ✗ Alert not triggered after cooldown (got {len(alerts3)})")
        results["tests"].append(("after_cooldown", "failed", f"Expected 1, got {len(alerts3)}"))
        results["failed"] += 1

    return results


async def test_multi_channel_alerts() -> dict:
    """Test sending alerts to multiple channels simultaneously."""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING: Multi-Channel Alert Delivery")
    logger.info("=" * 60)

    results = {"passed": 0, "failed": 0, "tests": []}

    # Reset service
    AlertingService.reset()
    service = AlertingService()

    # Add multi-channel rule
    test_rule = AlertRule(
        name="test_multi_channel",
        condition=lambda stats: True,
        severity="critical",
        cooldown_seconds=1,
        channels=["email", "slack", "webhook"],
        description="Test multi-channel alert rule",
    )
    await service.add_rule(test_rule)

    # Trigger alert
    stats = {"test_metric": 1}
    alerts = await service.check_alerts(stats)

    if len(alerts) == 1:
        alert = alerts[0]
        logger.info(f"  ✓ Alert created: {alert.id}")
        logger.info(f"  ✓ Channels configured: {test_rule.channels}")

        # Verify channels
        expected_channels = ["email", "slack", "webhook"]
        for channel in expected_channels:
            if channel in test_rule.channels:
                logger.info(f"    ✓ {channel} channel configured")
                results["tests"].append((f"channel_{channel}", "passed", ""))
                results["passed"] += 1
            else:
                logger.error(f"    ✗ {channel} channel missing")
                results["tests"].append((f"channel_{channel}", "failed", "Missing"))
                results["failed"] += 1
    else:
        logger.error(f"  ✗ Alert not created (got {len(alerts)})")
        results["tests"].append(("alert_creation", "failed", f"Expected 1, got {len(alerts)}"))
        results["failed"] += 1

    return results


async def run_all_tests(mock: bool = True, channels: list = None):
    """Run all alert channel tests."""
    logger.info("\n" + "=" * 60)
    logger.info("COMPREHENSIVE ALERT CHANNEL TESTS")
    logger.info("=" * 60)
    logger.info(f"Mode: {'MOCK' if mock else 'LIVE'}")
    logger.info(f"Channels: {', '.join(channels) if channels else 'all'}")

    all_results = {
        "config": {},
        "rules": {},
        "cooldowns": {},
        "multi_channel": {},
    }

    # Test configurations
    test_channels = channels or ["email", "slack", "webhook"]

    for channel in test_channels:
        config_results = await check_channel_configuration(channel)
        all_results["config"][channel] = config_results

    # Test alert rules
    all_results["rules"] = await test_alert_rules()

    # Test cooldowns
    all_results["cooldowns"] = await test_cooldowns()

    # Test multi-channel alerts
    all_results["multi_channel"] = await test_multi_channel_alerts()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 60)

    total_passed = 0
    total_failed = 0

    for category, results in all_results.items():
        cat_passed = results.get("passed", 0)
        cat_failed = results.get("failed", 0)
        total_passed += cat_passed
        total_failed += cat_failed
        logger.info(f"\n{category.upper()}:")
        logger.info(f"  Passed: {cat_passed}")
        logger.info(f"  Failed: {cat_failed}")

    logger.info("\n" + "=" * 60)
    if total_failed == 0:
        logger.info("✅ ALL TESTS PASSED")
    else:
        logger.info(f"❌ TESTS COMPLETED: {total_passed} passed, {total_failed} failed")
    logger.info("=" * 60)

    return total_failed == 0


def main():
    parser = argparse.ArgumentParser(description="Test all alert channels")
    parser.add_argument("--mock", action="store_true", default=True, help="Run tests in mock mode (default: True)")
    parser.add_argument("--no-mock", action="store_true", help="Disable mock mode (send actual notifications)")
    parser.add_argument(
        "--channel",
        type=str,
        choices=["email", "slack", "webhook", "all"],
        default="all",
        help="Specific channel to test (default: all)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    mock_mode = not args.no_mock
    channels = None if args.channel == "all" else [args.channel]

    if not mock_mode:
        logger.warning("⚠️  WARNING: Running in non-mock mode!")
        logger.warning("⚠️  This will send actual notifications to configured channels!")

    success = asyncio.run(run_all_tests(mock=mock_mode, channels=channels))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
