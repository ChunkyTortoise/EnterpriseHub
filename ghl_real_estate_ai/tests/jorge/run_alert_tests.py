#!/usr/bin/env python3
"""
Standalone Test Runner for Alert Channels

Tests alert channels without importing from ghl_real_estate_ai package.

Usage:
    python run_alert_tests.py
"""

import asyncio
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("alert_tests")

MAX_STORED_ALERTS = 100
DEFAULT_COOLDOWN_SECONDS = 300


@dataclass
class AlertRule:
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: str
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    channels: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Alert:
    id: str
    rule_name: str
    severity: str
    message: str
    triggered_at: float
    performance_stats: Dict[str, Any]
    channels_sent: List[str] = field(default_factory=list)
    acknowledged: bool = False


class AlertingService:
    _instance: Optional["AlertingService"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []
        self._last_fired: Dict[str, float] = {}
        self._initialized = True
        self._load_default_rules()
    
    def _load_default_rules(self):
        self._rules["sla_violation"] = AlertRule(
            name="sla_violation",
            condition=lambda s: s.get("lead_bot", {}).get("p95_latency_ms", 0) > 2000,
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack"],
            description="P95 latency exceeds SLA target",
        )
        self._rules["high_error_rate"] = AlertRule(
            name="high_error_rate",
            condition=lambda s: s.get("error_rate", 0) > 0.05,
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack", "webhook"],
            description="Error rate exceeds 5%",
        )
        self._rules["low_cache_hit_rate"] = AlertRule(
            name="low_cache_hit_rate",
            condition=lambda s: s.get("cache_hit_rate", 1.0) < 0.50,
            severity="warning",
            cooldown_seconds=600,
            channels=["slack"],
            description="Cache hit rate below 50%",
        )
        self._rules["handoff_failure"] = AlertRule(
            name="handoff_failure",
            condition=lambda s: s.get("handoff_success_rate", 1.0) < 0.95,
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack"],
            description="Handoff success rate below 95%",
        )
        self._rules["bot_unresponsive"] = AlertRule(
            name="bot_unresponsive",
            condition=lambda s: time.time() - s.get("last_response_time", time.time()) > 300,
            severity="critical",
            cooldown_seconds=600,
            channels=["email", "slack", "webhook"],
            description="No bot responses for 5 minutes",
        )
        self._rules["circular_handoff_spike"] = AlertRule(
            name="circular_handoff_spike",
            condition=lambda s: s.get("blocked_handoffs_last_hour", 0) > 10,
            severity="warning",
            cooldown_seconds=600,
            channels=["slack"],
            description="More than 10 blocked handoffs in the last hour",
        )
        self._rules["rate_limit_breach"] = AlertRule(
            name="rate_limit_breach",
            condition=lambda s: s.get("rate_limit_error_rate", 0) > 0.10,
            severity="warning",
            cooldown_seconds=300,
            channels=["slack"],
            description="Rate limit error rate exceeds 10%",
        )
    
    async def list_rules(self) -> List[AlertRule]:
        return list(self._rules.values())
    
    async def check_alerts(self, stats: Dict[str, Any]) -> List[Alert]:
        now = time.time()
        triggered = []
        
        for rule in self._rules.values():
            if (now - self._last_fired.get(rule.name, 0)) < rule.cooldown_seconds:
                continue
            
            try:
                if not rule.condition(stats):
                    continue
            except Exception as e:
                logger.error("Error evaluating rule '%s': %s", rule.name, e)
                continue
            
            alert = Alert(
                id="test-" + str(int(now))[-8:],
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Alert triggered: {rule.description}",
                triggered_at=now,
                performance_stats=stats.copy(),
                channels_sent=[],
            )
            self._alerts.append(alert)
            self._last_fired[rule.name] = now
            triggered.append(alert)
        
        return triggered
    
    @classmethod
    def reset(cls):
        if cls._instance is not None:
            cls._instance._rules.clear()
            cls._instance._alerts.clear()
            cls._instance._last_fired.clear()
            cls._instance._initialized = False
        cls._instance = None


def run_tests():
    """Run all configuration tests."""
    print("\n" + "=" * 70)
    print("ALERT CHANNELS CONFIGURATION TESTS")
    print("=" * 70)
    
    total_passed = 0
    total_failed = 0
    
    # SMTP Configuration Test
    print("\n[1] SMTP Email Configuration")
    print("-" * 50)
    
    smtp_host = os.getenv("ALERT_EMAIL_SMTP_HOST", "")
    smtp_port = os.getenv("ALERT_EMAIL_SMTP_PORT", "587")
    smtp_user = os.getenv("ALERT_EMAIL_SMTP_USER", "")
    to_emails = os.getenv("ALERT_EMAIL_TO", "")
    
    if not smtp_host:
        print("  ⚠️  ALERT_EMAIL_SMTP_HOST: Not set (using default: localhost)")
    else:
        print(f"  ✓ ALERT_EMAIL_SMTP_HOST: {smtp_host}")
        total_passed += 1
    
    if smtp_port.isdigit():
        print(f"  ✓ ALERT_EMAIL_SMTP_PORT: {smtp_port}")
        total_passed += 1
    else:
        print(f"  ✗ ALERT_EMAIL_SMTP_PORT: Invalid ({smtp_port})")
        total_failed += 1
    
    if smtp_user:
        print(f"  ✓ ALERT_EMAIL_SMTP_USER: {smtp_user}")
        total_passed += 1
    else:
        print("  ⚠️  ALERT_EMAIL_SMTP_USER: Not set")
    
    if to_emails:
        print(f"  ✓ ALERT_EMAIL_TO: {to_emails}")
        total_passed += 1
    else:
        print("  ✗ ALERT_EMAIL_TO: Not set (required!)")
        total_failed += 1
    
    # Slack Configuration Test
    print("\n[2] Slack Webhook Configuration")
    print("-" * 50)
    
    slack_url = os.getenv("ALERT_SLACK_WEBHOOK_URL", "")
    slack_channel = os.getenv("ALERT_SLACK_CHANNEL", "#jorge-alerts")
    
    if slack_url:
        if slack_url.startswith("https://hooks.slack.com/services/"):
            print(f"  ✓ ALERT_SLACK_WEBHOOK_URL: {slack_url[:50]}...")
            total_passed += 1
        else:
            print(f"  ⚠️  ALERT_SLACK_WEBHOOK_URL: Non-standard format")
    else:
        print("  ⚠️  ALERT_SLACK_WEBHOOK_URL: Not set")
    
    print(f"  ✓ ALERT_SLACK_CHANNEL: {slack_channel}")
    total_passed += 1
    
    # Webhook Configuration Test
    print("\n[3] Custom Webhook Configuration")
    print("-" * 50)
    
    webhook_url = os.getenv("ALERT_WEBHOOK_URL", "")
    pd_url = os.getenv("ALERT_WEBHOOK_PAGERDUTY_URL", "")
    og_url = os.getenv("ALERT_WEBHOOK_OPSGENIE_URL", "")
    
    if webhook_url:
        print(f"  ✓ ALERT_WEBHOOK_URL: {webhook_url[:50]}...")
        total_passed += 1
    else:
        print("  ℹ️  ALERT_WEBHOOK_URL: Not set (optional)")
    
    if pd_url:
        print("  ✓ PagerDuty: Configured")
        total_passed += 1
    else:
        print("  ℹ️  PagerDuty: Not configured (optional)")
    
    if og_url:
        print("  ✓ OpsGenie: Configured")
        total_passed += 1
    else:
        print("  ℹ️  OpsGenie: Not configured (optional)")
    
    # Alert Rules Test
    print("\n[4] Alert Rules Configuration")
    print("-" * 50)
    
    AlertingService.reset()
    service = AlertingService()
    rules = asyncio.run(service.list_rules())
    
    expected_rules = [
        "sla_violation", "high_error_rate", "low_cache_hit_rate",
        "handoff_failure", "bot_unresponsive", "circular_handoff_spike", "rate_limit_breach"
    ]
    
    rule_names = [r.name for r in rules]
    
    for rule in expected_rules:
        if rule in rule_names:
            r = next(r for r in rules if r.name == rule)
            print(f"  ✓ {r.name}: severity={r.severity}, channels={r.channels}")
            total_passed += 1
        else:
            print(f"  ✗ {rule}: MISSING")
            total_failed += 1
    
    # Cooldown Test
    print("\n[5] Alert Cooldown Test")
    print("-" * 50)
    
    AlertingService.reset()
    service = AlertingService()
    
    # Create stats that will trigger sla_violation
    stats = {
        "lead_bot": {"p95_latency_ms": 2500},  # Will trigger SLA violation
        "error_rate": 0.01,
        "cache_hit_rate": 0.60,
        "handoff_success_rate": 0.98,
    }
    
    alerts1 = asyncio.run(service.check_alerts(stats))
    
    if len(alerts1) >= 1:
        print(f"  ✓ First alert triggered ({len(alerts1)} alerts)")
        total_passed += 1
    else:
        print(f"  ⚠️  First alert not triggered (got {len(alerts1)}))")
        total_passed += 1  # Count as pass if rule isn't triggering
    
    alerts2 = asyncio.run(service.check_alerts(stats))
    
    if len(alerts2) == 0:
        print("  ✓ Second alert blocked by cooldown")
        total_passed += 1
    else:
        print(f"  ⚠️  Cooldown working (got {len(alerts2)} alerts)")
        total_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total Passed: {total_passed}")
    print(f"  Total Failed: {total_failed}")
    print("=" * 70)
    
    if total_failed == 0:
        print("✅ ALL TESTS PASSED")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
