import pytest

pytestmark = pytest.mark.integration

"""End-to-end integration tests for OpenTelemetry tracing.

Verifies:
- Full trace capture with console exporter -- spans are created
- Span attributes include jorge.service, jorge.operation, jorge.success, jorge.duration_ms
- Graceful degradation when OTel is not installed
- Multiple operations create separate spans
"""

from unittest.mock import patch

import pytest



def _otel_sdk_available() -> bool:
    """Check if the OTel SDK is importable with span capture support."""
    try:
        from opentelemetry import trace  # noqa: F401
        from opentelemetry.sdk.trace import TracerProvider  # noqa: F401
        from opentelemetry.sdk.trace.export import (  # noqa: F401
            SimpleSpanProcessor,
            SpanExporter,
            SpanExportResult,
        )

        return True
    except ImportError:
        return False


def _make_in_memory_exporter():
    """Create an in-memory span exporter compatible with SDK 1.39+."""
    # Try the standard location first
    try:
        from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter

        return InMemorySpanExporter()
    except ImportError:
        pass

    try:
        from opentelemetry.sdk.trace.export import InMemorySpanExporter

        return InMemorySpanExporter()
    except ImportError:
        pass

    # Fallback: build a minimal in-memory exporter
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    class _InMemorySpanExporter(SpanExporter):
        """Lightweight in-memory span exporter for testing."""

        def __init__(self):
            self._spans = []
            self._stopped = False

        def export(self, spans):
            if self._stopped:
                return SpanExportResult.FAILURE
            self._spans.extend(spans)
            return SpanExportResult.SUCCESS

        def get_finished_spans(self):
            return list(self._spans)

        def clear(self):
            self._spans.clear()

        def shutdown(self):
            self._stopped = True

        def force_flush(self, timeout_millis=30000):
            return True

    return _InMemorySpanExporter()


needs_otel = pytest.mark.skipif(
    not _otel_sdk_available(),
    reason="opentelemetry-sdk not installed",
)


@needs_otel
class TestOtelTracingE2E:
    """End-to-end tracing tests using an in-memory span exporter.

    OTel SDK 1.39+ disallows resetting the global TracerProvider, so these tests
    create an isolated TracerProvider and patch the telemetry module's _tracer
    directly rather than calling trace.set_tracer_provider().
    """

    @pytest.fixture(autouse=True)
    def setup_tracer(self):
        """Set up a fresh TracerProvider with in-memory exporter for each test.

        Patches ``telemetry._tracer`` and ``telemetry._otel_available`` directly
        so that ``optional_span`` and ``@trace_operation`` use our test provider.
        """
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        self.memory_exporter = _make_in_memory_exporter()
        resource = Resource.create({"service.name": "test-jorge"})
        self.provider = TracerProvider(resource=resource)
        self.provider.add_span_processor(SimpleSpanProcessor(self.memory_exporter))

        # Get a tracer from our test provider
        self.test_tracer = self.provider.get_tracer("jorge-services", "1.0.0")

        yield

        self.provider.shutdown()

    def _patch_telemetry(self):
        """Reload telemetry module and patch its _tracer with our test tracer."""
        import importlib

        import ghl_real_estate_ai.services.jorge.telemetry as telemetry_mod

        # Reload to get fresh module state
        importlib.reload(telemetry_mod)
        # Override with our test-specific tracer
        telemetry_mod._tracer = self.test_tracer
        telemetry_mod._otel_available = True
        return telemetry_mod

    def test_optional_span_creates_real_span(self):
        """optional_span creates a real span with correct attributes."""
        telemetry_mod = self._patch_telemetry()

        with telemetry_mod.optional_span("jorge.handoff", "evaluate") as span:
            span.set_attribute("test.key", "test_value")

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1

        span = spans[0]
        attrs = dict(span.attributes)
        assert attrs["jorge.service"] == "jorge.handoff"
        assert attrs["jorge.operation"] == "evaluate"
        assert attrs["jorge.success"] is True
        assert "jorge.duration_ms" in attrs
        assert isinstance(attrs["jorge.duration_ms"], float)
        assert attrs["jorge.duration_ms"] >= 0.0

    def test_optional_span_records_exception(self):
        """optional_span records exception and sets jorge.success=False."""
        telemetry_mod = self._patch_telemetry()

        with pytest.raises(ValueError, match="test error"):
            with telemetry_mod.optional_span("jorge.metrics", "compute") as span:
                raise ValueError("test error")

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1

        span = spans[0]
        attrs = dict(span.attributes)
        assert attrs["jorge.success"] is False
        assert attrs["jorge.service"] == "jorge.metrics"
        assert attrs["jorge.operation"] == "compute"

        # Verify exception was recorded as an event
        events = span.events
        assert len(events) >= 1
        assert any("ValueError" in str(e.attributes) for e in events)

    def test_trace_operation_decorator_sync(self):
        """@trace_operation creates a span for synchronous functions."""
        telemetry_mod = self._patch_telemetry()

        @telemetry_mod.trace_operation("jorge.alerting", "check_rules")
        def check_rules(threshold: float) -> bool:
            return threshold > 0.5

        result = check_rules(0.8)
        assert result is True

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        attrs = dict(spans[0].attributes)
        assert attrs["jorge.service"] == "jorge.alerting"
        assert attrs["jorge.operation"] == "check_rules"
        assert attrs["jorge.success"] is True

    @pytest.mark.asyncio
    async def test_trace_operation_decorator_async(self):
        """@trace_operation creates a span for async functions."""
        telemetry_mod = self._patch_telemetry()

        @telemetry_mod.trace_operation("jorge.performance", "track_latency")
        async def track_latency(bot_name: str, duration: float) -> dict:
            return {"bot": bot_name, "duration": duration}

        result = await track_latency("lead_bot", 150.0)
        assert result == {"bot": "lead_bot", "duration": 150.0}

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        attrs = dict(spans[0].attributes)
        assert attrs["jorge.service"] == "jorge.performance"
        assert attrs["jorge.operation"] == "track_latency"
        assert attrs["jorge.success"] is True

    def test_multiple_operations_create_separate_spans(self):
        """Each operation creates its own span."""
        telemetry_mod = self._patch_telemetry()

        with telemetry_mod.optional_span("jorge.handoff", "evaluate"):
            pass

        with telemetry_mod.optional_span("jorge.metrics", "record"):
            pass

        with telemetry_mod.optional_span("jorge.alerting", "check"):
            pass

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 3

        span_names = [s.name for s in spans]
        assert "jorge.handoff.evaluate" in span_names
        assert "jorge.metrics.record" in span_names
        assert "jorge.alerting.check" in span_names

    def test_span_duration_is_positive(self):
        """jorge.duration_ms should be a positive number."""
        from unittest.mock import patch

        telemetry_mod = self._patch_telemetry()

        # Mock perf_counter to simulate 15ms elapsed (no wall-clock delay)
        call_count = [0]
        def mock_perf_counter():
            call_count[0] += 1
            return call_count[0] * 0.015  # 15ms per call

        with patch.object(telemetry_mod, "time") as mock_time:
            mock_time.perf_counter = mock_perf_counter
            with telemetry_mod.optional_span("jorge.test", "slow_op"):
                pass  # No sleep needed

        spans = self.memory_exporter.get_finished_spans()
        assert len(spans) == 1
        duration = spans[0].attributes["jorge.duration_ms"]
        assert duration >= 5.0  # At least 5ms (from mocked perf_counter)


class TestGracefulDegradationE2E:
    """Test graceful degradation when OTel SDK is not available."""

    def test_setup_observability_returns_false_when_disabled(self):
        """setup_observability returns False when not enabled."""
        from ghl_real_estate_ai.observability import setup_observability

        result = setup_observability(enabled=False)
        assert result is False

    def test_telemetry_noop_when_otel_unavailable(self):
        """telemetry module works in no-op mode without OTel SDK."""
        from ghl_real_estate_ai.services.jorge.telemetry import (
            _NoOpSpan,
            optional_span,
        )

        # When OTel is not configured, optional_span should yield a _NoOpSpan
        # or a real span depending on SDK availability. Either way, no exception.
        with optional_span("jorge.test", "noop_test") as span:
            span.set_attribute("key", "value")
            span.add_event("test_event")

    def test_trace_operation_decorator_works_without_otel(self):
        """@trace_operation works as transparent pass-through without OTel."""
        from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

        @trace_operation("jorge.test", "decorated_fn")
        def my_function(x: int) -> int:
            return x * 2

        result = my_function(21)
        assert result == 42

    @pytest.mark.asyncio
    async def test_trace_operation_async_works_without_otel(self):
        """@trace_operation async variant works without OTel."""
        from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

        @trace_operation("jorge.test", "async_fn")
        async def my_async_function(x: int) -> int:
            return x + 1

        result = await my_async_function(41)
        assert result == 42


@needs_otel
class TestSetupObservabilityE2E:
    """End-to-end tests for setup_observability with real SDK."""

    def test_console_exporter_setup(self):
        """Full setup with console exporter succeeds."""
        from ghl_real_estate_ai.observability import setup_observability

        result = setup_observability(
            enabled=True,
            exporter_type="console",
            service_name="e2e-test",
        )
        # Returns True regardless of whether the global provider was already set,
        # because setup_observability creates and assigns a new provider.
        assert result is True

    @patch.dict(
        "os.environ",
        {
            "OTEL_ENABLED": "true",
            "OTEL_SERVICE_NAME": "e2e-integration",
            "OTEL_EXPORTER_TYPE": "console",
        },
    )
    def test_env_var_driven_setup(self):
        """setup_observability configures from environment variables."""
        from ghl_real_estate_ai.observability import setup_observability

        result = setup_observability()
        assert result is True