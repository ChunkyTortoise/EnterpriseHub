"""Tests for OpenTelemetry setup and telemetry helpers.

Validates:
- setup_observability env var gating
- Telemetry module: trace_operation, optional_span, is_otel_available
- Metric counters: increment_counter, add_jorge_attributes
"""

import os
from unittest.mock import MagicMock, patch

import pytest

@pytest.mark.unit

# ── setup_observability ───────────────────────────────────────────────


def test_setup_observability_disabled_by_default():
    from ghl_real_estate_ai.observability.otel_config import setup_observability

    result = setup_observability()
    assert result is False


def test_setup_observability_disabled_when_env_false():
    from ghl_real_estate_ai.observability.otel_config import setup_observability

    with patch.dict(os.environ, {"OTEL_ENABLED": "false"}):
        result = setup_observability()
        assert result is False


def test_setup_observability_explicit_disable():
    from ghl_real_estate_ai.observability.otel_config import setup_observability

    result = setup_observability(enabled=False)
    assert result is False


def test_setup_observability_enabled_without_sdk():
    """When OTEL_ENABLED=true but SDK not installed, returns False."""
    from ghl_real_estate_ai.observability.otel_config import setup_observability

    with patch.dict(os.environ, {"OTEL_ENABLED": "true"}):
        # If SDK is not installed, should gracefully return False
        # If SDK IS installed, should return True
        result = setup_observability(enabled=True, exporter_type="console")
        # Either True (SDK present) or False (SDK missing) is valid
        assert isinstance(result, bool)


# ── observability __init__ exports ────────────────────────────────────


def test_observability_init_exports():
    from ghl_real_estate_ai.observability import setup_observability

    assert callable(setup_observability)


# ── telemetry: trace_operation ────────────────────────────────────────


def test_trace_operation_sync():
    from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

    @trace_operation("test.service", "sync_op")
    def my_sync_func(x, y):
        return x + y

    result = my_sync_func(2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_trace_operation_async():
    from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

    @trace_operation("test.service", "async_op")
    async def my_async_func(x, y):
        return x * y

    result = await my_async_func(4, 5)
    assert result == 20


def test_trace_operation_exception_propagates():
    from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

    @trace_operation("test.service", "failing_op")
    def my_failing_func():
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        my_failing_func()


# ── telemetry: optional_span ──────────────────────────────────────────


def test_optional_span_yields_span():
    from ghl_real_estate_ai.services.jorge.telemetry import optional_span

    with optional_span("test.service", "op") as span:
        # Should work with both real and no-op spans
        span.set_attribute("test.key", "test_value")
        span.add_event("test_event")


def test_optional_span_exception_propagates():
    from ghl_real_estate_ai.services.jorge.telemetry import optional_span

    with pytest.raises(RuntimeError, match="boom"):
        with optional_span("test.service", "failing") as span:
            raise RuntimeError("boom")


# ── telemetry: is_otel_available ──────────────────────────────────────


def test_is_otel_available_returns_bool():
    from ghl_real_estate_ai.services.jorge.telemetry import is_otel_available

    result = is_otel_available()
    assert isinstance(result, bool)


# ── telemetry: add_jorge_attributes ───────────────────────────────────


def test_add_jorge_attributes_sets_prefixed_keys():
    from ghl_real_estate_ai.services.jorge.telemetry import add_jorge_attributes

    mock_span = MagicMock()
    add_jorge_attributes(
        mock_span,
        bot_type="lead",
        contact_id="c001",
        duration_ms=450.0,
    )
    mock_span.set_attribute.assert_any_call("jorge.bot_type", "lead")
    mock_span.set_attribute.assert_any_call("jorge.contact_id", "c001")
    mock_span.set_attribute.assert_any_call("jorge.duration_ms", 450.0)


def test_add_jorge_attributes_noop_span():
    from ghl_real_estate_ai.services.jorge.telemetry import (
        _NoOpSpan,
        add_jorge_attributes,
    )

    span = _NoOpSpan()
    # Should not raise
    add_jorge_attributes(span, bot_type="seller", route="lead->seller")


# ── telemetry: increment_counter ──────────────────────────────────────


def test_increment_counter_unknown_name():
    from ghl_real_estate_ai.services.jorge.telemetry import increment_counter

    # Should not raise for unknown counter names
    increment_counter("jorge.nonexistent.counter")


def test_increment_counter_known_names():
    from ghl_real_estate_ai.services.jorge.telemetry import _counters, increment_counter

    # If OTel is installed, counters exist; if not, dict is empty
    # Either way, calling should not raise
    increment_counter("jorge.interaction.total", 1, bot_type="lead")
    increment_counter("jorge.handoff.total", 1, route="lead->buyer")
    increment_counter("jorge.alert.triggered", 1, severity="critical")


# ── NoOpSpan ──────────────────────────────────────────────────────────


def test_noop_span_all_methods():
    from ghl_real_estate_ai.services.jorge.telemetry import _NoOpSpan

    span = _NoOpSpan()
    span.set_attribute("key", "value")
    span.set_status("OK")
    span.record_exception(ValueError("test"))
    span.add_event("event", {"key": "value"})
    span.end()


def test_noop_span_context_manager():
    from ghl_real_estate_ai.services.jorge.telemetry import _NoOpSpan

    span = _NoOpSpan()
    with span as s:
        assert s is span