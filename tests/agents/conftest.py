"""
Shared Test Fixtures for Jorge Bot Test Suite
==============================================

Common fixtures for Lead Bot, Buyer Bot, and Seller Bot tests.
Reduces duplication and ensures consistent test patterns.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# ==============================
# Common Mock Data Fixtures
# ==============================


@pytest.fixture
def mock_conversation_history() -> List[Dict[str, str]]:
    """Standard conversation history for testing."""
    return [
        {"role": "user", "content": "I'm interested in buying a home"},
        {"role": "assistant", "content": "Great! I can help with that. What's your budget?"},
        {"role": "user", "content": "Around $400k, pre-approved"},
    ]


@pytest.fixture
def mock_lead_metadata():
    """Standard lead metadata for testing."""
    return {
        "contact_id": "test_contact_123",
        "location_id": "test_location_456",
        "source": "web_chat",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_ghl_contact():
    """Mock GHL contact data."""
    return {
        "id": "test_contact_123",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "phone": "+15555551234",
        "tags": ["web-lead", "warm"],
        "customFields": {
            "lead_temperature": "warm",
            "lead_score": "65",
            "last_interaction": datetime.utcnow().isoformat(),
        },
    }


# ==============================
# Service Mock Fixtures
# ==============================


@pytest.fixture
def mock_ghl_client():
    """Mock GoHighLevel client."""
    client = AsyncMock()
    client.get_contact = AsyncMock(
        return_value={
            "id": "test_contact_123",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@example.com",
            "phone": "+15555551234",
        }
    )
    client.send_message = AsyncMock()
    client.update_contact = AsyncMock()
    client.add_tag = AsyncMock()
    return client


@pytest.fixture
def mock_claude_assistant():
    """Mock Claude assistant for response generation."""
    assistant = AsyncMock()
    assistant.generate_response = AsyncMock(
        return_value={
            "response": "I'd be happy to help you with that!",
            "confidence": 0.85,
        }
    )
    return assistant


@pytest.fixture
def mock_event_publisher():
    """Mock event publisher for bot events."""
    publisher = Mock()
    publisher.publish_lead_temperature_update = AsyncMock()
    publisher.publish_buyer_qualification_complete = AsyncMock()
    publisher.publish_seller_listing_initiated = AsyncMock()
    return publisher


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def mock_performance_tracker():
    """Mock performance tracker."""
    tracker = AsyncMock()
    tracker.track_operation = AsyncMock()
    tracker.get_metrics = AsyncMock(
        return_value={
            "p50": 120.0,
            "p95": 350.0,
            "p99": 500.0,
        }
    )
    return tracker


@pytest.fixture
def mock_metrics_collector():
    """Mock bot metrics collector."""
    collector = Mock()
    collector.record_bot_interaction = Mock()
    collector.record_handoff_attempt = Mock()
    collector.feed_to_alerting = Mock()
    return collector


@pytest.fixture
def mock_alerting_service():
    """Mock alerting service."""
    alerting = AsyncMock()
    alerting.check_and_alert = AsyncMock()
    alerting.get_active_alerts = AsyncMock(return_value=[])
    return alerting


# ==============================
# Bot-Specific Fixtures
# ==============================


@pytest.fixture
def mock_lead_intent_decoder():
    """Mock lead intent decoder."""
    decoder = AsyncMock()
    decoder.analyze_lead_with_ghl = AsyncMock(
        return_value={
            "lead_score": 75.0,
            "temperature": "warm",
            "confidence": 0.85,
            "next_step": "qualify_timeline",
            "key_signals": ["budget_mentioned", "pre_approval", "timeline_specific"],
        }
    )
    return decoder


@pytest.fixture
def mock_buyer_intent_decoder():
    """Mock buyer intent decoder."""
    decoder = AsyncMock()
    decoder.analyze_buyer_with_ghl = AsyncMock(
        return_value={
            "financial_readiness": 80.0,
            "urgency_score": 70.0,
            "buyer_temperature": "hot",
            "next_qualification_step": "property_search",
        }
    )
    return decoder


@pytest.fixture
def mock_seller_intent_decoder():
    """Mock seller intent decoder."""
    decoder = AsyncMock()
    decoder.analyze_seller = AsyncMock(
        return_value={
            "frs_score": 75.0,
            "pcs_score": 65.0,
            "seller_temperature": "warm",
            "motivation_level": "high",
        }
    )
    return decoder


# ==============================
# External Service Fixtures
# ==============================


@pytest.fixture
def mock_retell_client():
    """Mock Retell AI client for voice calls."""
    client = AsyncMock()
    client.create_call = AsyncMock(
        return_value={
            "call_id": "call_123",
            "status": "scheduled",
        }
    )
    return client


@pytest.fixture
def mock_lyrio_client():
    """Mock Lyrio client for calendar booking."""
    client = AsyncMock()
    client.get_availability = AsyncMock(
        return_value=[
            {"slot_id": "slot_1", "start_time": "2024-03-15T10:00:00Z"},
            {"slot_id": "slot_2", "start_time": "2024-03-15T14:00:00Z"},
        ]
    )
    client.book_appointment = AsyncMock(
        return_value={
            "booking_id": "booking_123",
            "confirmed": True,
        }
    )
    return client


@pytest.fixture
def mock_property_matcher():
    """Mock property matcher service."""
    matcher = AsyncMock()
    matcher.find_matching_properties = AsyncMock(
        return_value=[
            {"id": "prop_1", "price": 385000, "bedrooms": 3},
            {"id": "prop_2", "price": 395000, "bedrooms": 3},
        ]
    )
    return matcher


# ==============================
# Edge Case Data Fixtures
# ==============================


@pytest.fixture
def empty_conversation_history() -> List[Dict[str, str]]:
    """Empty conversation for edge case testing."""
    return []


@pytest.fixture
def max_length_message() -> str:
    """Maximum length message for boundary testing."""
    return "X" * 10_000


@pytest.fixture
def unicode_message() -> str:
    """Unicode message for internationalization testing."""
    return "Hola! ¿Cómo estás? 你好! こんにちは! 🏠🔑"


@pytest.fixture
def malformed_conversation_history() -> List[Dict]:
    """Malformed conversation data for error handling tests."""
    return [
        {"role": "user"},  # Missing content
        {"content": "No role"},  # Missing role
        {},  # Empty message
    ]


# ==============================
# Performance Testing Fixtures
# ==============================


@pytest.fixture
def concurrent_requests():
    """Generate concurrent request scenarios."""
    return [{"conversation_id": f"conv_{i}", "message": f"Message {i}"} for i in range(10)]


# ==============================
# Configuration Fixtures (Hybrid Isolation Strategy)
# ==============================


@pytest.fixture(scope="session")
def session_config():
    """
    Load config once per test session (fast, shared state).

    Use this for read-only tests that don't modify environment.
    ~5ms overhead per test run.
    """
    from ghl_real_estate_ai.config.jorge_config_loader import get_config

    return get_config()


@pytest.fixture(scope="function")
def isolated_config(monkeypatch):
    """
    Reload config for tests that modify environment (slower, full isolation).

    Use this for:
    - Environment override tests
    - Config mutation tests
    - Tests requiring fresh config state

    ~50-100ms overhead per test (YAML parse + dataclass instantiation).
    """
    import os

    from ghl_real_estate_ai.config.jorge_config_loader import get_config, reload_config

    # Save original env
    original_env = os.environ.get("DEPLOYMENT_ENV")

    yield get_config()

    # Restore original env and reload
    if original_env:
        monkeypatch.setenv("DEPLOYMENT_ENV", original_env)
    else:
        monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)
    reload_config()


@pytest.fixture
def mock_minimal_config():
    """
    Minimal config for unit tests without file I/O.

    Uses dataclass defaults, no YAML parsing.
    Fastest option for pure unit tests.
    """
    from ghl_real_estate_ai.config.jorge_config_loader import JorgeBotsConfig

    return JorgeBotsConfig()


@pytest.fixture
def temp_thresholds(session_config):
    """Lead bot temperature thresholds from config."""
    return session_config.lead_bot.temperature_thresholds


@pytest.fixture
def handoff_config(session_config):
    """Handoff configuration from unified config."""
    return session_config.shared.handoff


@pytest.fixture
def sla_config(session_config):
    """Performance SLA configuration."""
    return session_config.shared.performance
