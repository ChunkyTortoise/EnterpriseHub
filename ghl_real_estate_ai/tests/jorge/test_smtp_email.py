#!/usr/bin/env python3
"""
Test SMTP Email Alert Channel

Tests SMTP email connectivity and alert delivery.
Uses environment variables for configuration.

Usage:
    python test_smtp_email.py [--mock] [--verbose]

Options:
    --mock    : Run tests in mock mode (no actual email sent)
    --verbose : Enable verbose output
"""

import asyncio
import argparse
import logging
import os
import smtplib
import sys
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghl_real_estate_ai.services.jorge.alerting_service import Alert, AlertRule, AlertingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_smtp_email")


class MockSMTP:
    """Mock SMTP server for testing without sending actual emails."""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.messages = []
        self.connected = False
    
    def __enter__(self):
        self.connected = True
        logger.info(f"[MOCK] Connected to SMTP server {self.host}:{self.port}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connected = False
        logger.info("[MOCK] Disconnected from SMTP server")
    
    def starttls(self):
        logger.info("[MOCK] STARTTLS initiated")
    
    def login(self, user: str, password: str):
        logger.info(f"[MOCK] Authenticated as {user}")
    
    def send_message(self, msg: MIMEMultipart):
        self.messages.append(msg)
        logger.info(f"[MOCK] Email sent to {msg['To']}")


def create_test_alert(severity: str = "warning") -> Alert:
    """Create a test alert for testing purposes."""
    return Alert(
        id="test-1234",
        rule_name="test_alert_rule",
        severity=severity,
        message="This is a test alert message for SMTP testing.\nError Rate: 6.5%\nCache Hit Rate: 45%",
        triggered_at=time.time(),
        performance_stats={
            "error_rate": 0.065,
            "cache_hit_rate": 0.45,
            "handoff_success_rate": 0.92,
            "lead_bot": {
                "p50_latency_ms": 450,
                "p95_latency_ms": 2100,
                "p99_latency_ms": 2800,
            },
            "buyer_bot": {
                "p50_latency_ms": 520,
                "p95_latency_ms": 2600,
                "p99_latency_ms": 3200,
            },
            "seller_bot": {
                "p50_latency_ms": 480,
                "p95_latency_ms": 2400,
                "p99_latency_ms": 3000,
            },
        },
        channels_sent=[],
    )


def test_smtp_configuration():
    """Test that SMTP configuration is properly set."""
    logger.info("=" * 60)
    logger.info("TEST: SMTP Configuration")
    logger.info("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check required environment variables
    logger.info("\n[Test 1] Checking required environment variables...")
    
    smtp_host = os.getenv("ALERT_EMAIL_SMTP_HOST", "")
    smtp_port = os.getenv("ALERT_EMAIL_SMTP_PORT", "587")
    smtp_user = os.getenv("ALERT_EMAIL_SMTP_USER", "")
    from_email = os.getenv("ALERT_EMAIL_FROM", "")
    to_emails = os.getenv("ALERT_EMAIL_TO", "")
    
    if not smtp_host:
        logger.warning("  ⚠️  ALERT_EMAIL_SMTP_HOST not set (using default: localhost)")
        tests_passed += 1
    else:
        logger.info(f"  ✓ ALERT_EMAIL_SMTP_HOST: {smtp_host}")
        tests_passed += 1
    
    if not smtp_port.isdigit():
        logger.error(f"  ✗ ALERT_EMAIL_SMTP_PORT invalid: {smtp_port}")
        tests_failed += 1
    else:
        logger.info(f"  ✓ ALERT_EMAIL_SMTP_PORT: {smtp_port}")
        tests_passed += 1
    
    if not smtp_user:
        logger.warning("  ⚠️  ALERT_EMAIL_SMTP_USER not set (anonymous auth)")
        tests_passed += 1
    else:
        logger.info(f"  ✓ ALERT_EMAIL_SMTP_USER: {smtp_user}")
        tests_passed += 1
    
    if not from_email:
        logger.warning("  ⚠️  ALERT_EMAIL_FROM not set (using default)")
        tests_passed += 1
    else:
        logger.info(f"  ✓ ALERT_EMAIL_FROM: {from_email}")
        tests_passed += 1
    
    if not to_emails:
        logger.error("  ✗ ALERT_EMAIL_TO not set (required!)")
        tests_failed += 1
    else:
        logger.info(f"  ✓ ALERT_EMAIL_TO: {to_emails}")
        tests_passed += 1
    
    # Test 2: Test SMTP connection (mock)
    logger.info("\n[Test 2] Testing SMTP connection (mock)...")
    
    try:
        with MockSMTP(smtp_host or "localhost", int(smtp_port)) as server:
            if smtp_user and os.getenv("ALERT_EMAIL_SMTP_PASSWORD"):
                server.starttls()
                server.login(smtp_user, os.getenv("ALERT_EMAIL_SMTP_PASSWORD", ""))
            logger.info("  ✓ SMTP connection successful (mock)")
            tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ SMTP connection failed: {e}")
        tests_failed += 1
    
    # Test 3: Test email message creation
    logger.info("\n[Test 3] Testing email message creation...")
    
    try:
        alert = create_test_alert()
        msg = MIMEMultipart()
        msg["From"] = from_email or "alerts@enterprisehub.com"
        msg["To"] = ", ".join([e.strip() for e in to_emails.split(",") if e.strip()])
        msg["Subject"] = f"[{alert.severity.upper()}] Jorge Bot Alert: {alert.rule_name}"
        body = alert.message
        msg.attach(MIMEText(body, "plain"))
        
        logger.info(f"  ✓ Email message created successfully")
        logger.info(f"    From: {msg['From']}")
        logger.info(f"    To: {msg['To']}")
        logger.info(f"    Subject: {msg['Subject']}")
        tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Email message creation failed: {e}")
        tests_failed += 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SUMMARY: {tests_passed} passed, {tests_failed} failed")
    logger.info("=" * 60)
    
    return tests_failed == 0


async def test_email_alert_delivery(mock: bool = True) -> bool:
    """Test actual email alert delivery."""
    logger.info("=" * 60)
    logger.info("TEST: Email Alert Delivery" + (" (MOCK)" if mock else ""))
    logger.info("=" * 60)
    
    tests_passed = 0
    tests_failed = 0
    
    # Create test alert
    alert = create_test_alert(severity="critical")
    
    # Get configuration
    smtp_host = os.getenv("ALERT_EMAIL_SMTP_HOST", "localhost")
    smtp_port = int(os.getenv("ALERT_EMAIL_SMTP_PORT", "587"))
    smtp_user = os.getenv("ALERT_EMAIL_SMTP_USER", "")
    smtp_password = os.getenv("ALERT_EMAIL_SMTP_PASSWORD", "")
    from_email = os.getenv("ALERT_EMAIL_FROM", "alerts@enterprisehub.com")
    to_emails = os.getenv("ALERT_EMAIL_TO", "").split(",")
    
    if not to_emails or not to_emails[0]:
        logger.warning("  ⚠️  No recipients configured, skipping delivery test")
        return True
    
    # Create message
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = f"[{alert.severity.upper()}] Jorge Bot Alert: {alert.rule_name}"
    body = alert.message
    msg.attach(MIMEText(body, "plain"))
    
    # Test delivery
    try:
        if mock:
            # Use mock
            with MockSMTP(smtp_host, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
                logger.info(f"  ✓ Email delivered successfully (mock)")
                tests_passed += 1
        else:
            # Use real SMTP
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                if smtp_user and smtp_password:
                    server.starttls()
                    server.ehlo()
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
                logger.info(f"  ✓ Email delivered successfully")
                tests_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Email delivery failed: {e}")
        tests_failed += 1
    
    # Test cooldowns
    logger.info("\n[Test] Testing alert cooldowns...")
    
    AlertingService.reset()
    service = AlertingService()
    
    # Create rule with short cooldown for testing
    test_rule = AlertRule(
        name="test_cooldown_rule",
        condition=lambda stats: True,
        severity="warning",
        cooldown_seconds=1,  # Short cooldown for testing
        channels=["email"],
        description="Test cooldown rule",
    )
    await service.add_rule(test_rule)
    
    # Trigger first alert
    stats = {"test_metric": 1}
    alerts1 = await service.check_alerts(stats)
    
    if len(alerts1) == 1:
        logger.info("  ✓ First alert triggered successfully")
        tests_passed += 1
    else:
        logger.error("  ✗ First alert not triggered")
        tests_failed += 1
    
    # Try to trigger second alert immediately (should be blocked by cooldown)
    alerts2 = await service.check_alerts(stats)
    
    if len(alerts2) == 0:
        logger.info("  ✓ Second alert correctly blocked by cooldown")
        tests_passed += 1
    else:
        logger.error("  ✗ Second alert not blocked by cooldown")
        tests_failed += 1
    
    # Wait for cooldown and trigger again
    await asyncio.sleep(1.1)
    alerts3 = await service.check_alerts(stats)
    
    if len(alerts3) == 1:
        logger.info("  ✓ Alert triggered after cooldown expired")
        tests_passed += 1
    else:
        logger.error("  ✗ Alert not triggered after cooldown")
        tests_failed += 1
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info(f"SUMMARY: {tests_passed} passed, {tests_failed} failed")
    logger.info("=" * 60)
    
    return tests_failed == 0


async def run_all_tests(mock: bool = True, verbose: bool = False):
    """Run all SMTP email tests."""
    logger.info("\n" + "=" * 60)
    logger.info("SMTP EMAIL ALERT CHANNEL TESTS")
    logger.info("=" * 60)
    
    all_passed = True
    
    # Configuration test
    if not test_smtp_configuration():
        all_passed = False
    
    # Delivery test
    if not await test_email_alert_delivery(mock=mock):
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
    parser = argparse.ArgumentParser(
        description="Test SMTP email alert channel"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Run tests in mock mode (default: True)"
    )
    parser.add_argument(
        "--no-mock",
        action="store_true",
        help="Disable mock mode (send actual emails)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    mock_mode = not args.no_mock
    
    if not mock_mode:
        logger.warning("⚠️  WARNING: Running in non-mock mode will send actual emails!")
        logger.warning("⚠️  Make sure your SMTP configuration is correct.")
    
    success = asyncio.run(run_all_tests(mock=mock_mode, verbose=args.verbose))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
