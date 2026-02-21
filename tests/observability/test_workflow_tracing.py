"""
Tests for OpenTelemetry workflow tracing

Validates:
- Span creation and context propagation
- Workflow node instrumentation
- Cross-bot handoff correlation
- Trace ID generation and extraction
- No-op behavior when OTel is disabled
"""

from typing import Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.observability import workflow_tracing


@pytest.fixture
def mock_state():
    """Sample LangGraph state dict."""
    return {
        "lead_id": "test_contact_123",
        "contact_id": "test_contact_123",
        "current_step": "day_3",
        "temperature": "hot",
        "conversation_history": [],
    }


@pytest.fixture
def reset_otel():
    """Reset OpenTelemetry module state before each test."""
    # Store original state
    original_available = workflow_tracing._otel_available
    original_tracer = workflow_tracing._tracer

    yield

    # Restore original state
    workflow_tracing._otel_available = original_available
    workflow_tracing._tracer = original_tracer


class TestNoOpBehavior:
    """Test graceful degradation when OpenTelemetry is not installed."""

    def test_noop_span_all_methods(self):
        """NoOp span accepts all method calls without error."""
        span = workflow_tracing._NoOpSpan()

        # Should not raise
        span.set_attribute("key", "value")
        span.set_status(Mock())
        span.record_exception(ValueError("test"))
        span.add_event("event_name", {"attr": "value"})
        span.end()

        # Context manager
        with span as s:
            assert s is span

    def test_workflow_span_when_disabled(self, reset_otel):
        """workflow_span returns no-op when OTel is disabled."""
        workflow_tracing._otel_available = False

        with workflow_tracing.workflow_span("lead_bot", "test_node") as span:
            assert isinstance(span, workflow_tracing._NoOpSpan)
            span.set_attribute("test", "value")  # Should not raise

    @pytest.mark.asyncio
    async def test_async_workflow_span_when_disabled(self, reset_otel):
        """async_workflow_span returns no-op when OTel is disabled."""
        workflow_tracing._otel_available = False

        async with workflow_tracing.async_workflow_span("seller_bot", "test_node") as span:
            assert isinstance(span, workflow_tracing._NoOpSpan)
            span.set_attribute("test", "value")  # Should not raise

    def test_trace_workflow_node_decorator_when_disabled(self, reset_otel, mock_state):
        """@trace_workflow_node works transparently when OTel disabled."""
        workflow_tracing._otel_available = False

        @workflow_tracing.trace_workflow_node("lead_bot", "test_node")
        def sync_node(state: Dict) -> Dict:
            state["processed"] = True
            return state

        result = sync_node(mock_state)
        assert result["processed"] is True

    @pytest.mark.asyncio
    async def test_trace_workflow_node_async_decorator_when_disabled(self, reset_otel, mock_state):
        """@trace_workflow_node works on async functions when OTel disabled."""
        workflow_tracing._otel_available = False

        @workflow_tracing.trace_workflow_node("buyer_bot", "test_node")
        async def async_node(state: Dict) -> Dict:
            state["async_processed"] = True
            return state

        result = await async_node(mock_state)
        assert result["async_processed"] is True

    def test_get_trace_id_when_disabled(self, reset_otel):
        """get_trace_id returns empty string when OTel disabled."""
        workflow_tracing._otel_available = False
        assert workflow_tracing.get_trace_id() == ""

    def test_is_tracing_enabled(self, reset_otel):
        """is_tracing_enabled reflects OTel availability."""
        workflow_tracing._otel_available = False
        assert workflow_tracing.is_tracing_enabled() is False

        workflow_tracing._otel_available = True
        assert workflow_tracing.is_tracing_enabled() is True


@pytest.mark.skipif(not workflow_tracing._otel_available, reason="OpenTelemetry SDK not installed")
class TestSpanCreation:
    """Test span creation when OpenTelemetry is available."""

    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    def test_workflow_span_creates_span(self, mock_tracer):
        """workflow_span creates a real span when OTel is available."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        with workflow_tracing.workflow_span("lead_bot", "analyze_intent", contact_id="test_123", custom_attr="value"):
            pass

        # Verify span was created with correct name
        mock_tracer.start_as_current_span.assert_called_once_with("lead_bot.analyze_intent")

        # Verify attributes were set
        mock_span.set_attribute.assert_any_call("workflow.bot_type", "lead_bot")
        mock_span.set_attribute.assert_any_call("workflow.node_name", "analyze_intent")
        mock_span.set_attribute.assert_any_call("workflow.contact_id", "test_123")
        mock_span.set_attribute.assert_any_call("workflow.custom_attr", "value")
        mock_span.set_attribute.assert_any_call("workflow.success", True)

    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    def test_workflow_span_records_exceptions(self, mock_tracer):
        """workflow_span records exceptions and marks span as error."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        with pytest.raises(ValueError):
            with workflow_tracing.workflow_span("seller_bot", "failing_node"):
                raise ValueError("test error")

        # Verify exception was recorded
        mock_span.record_exception.assert_called_once()
        mock_span.set_attribute.assert_any_call("workflow.success", False)

        # Verify error status was set
        from opentelemetry.trace import Status, StatusCode

        mock_span.set_status.assert_called()

    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    def test_workflow_span_duration_tracking(self, mock_tracer):
        """workflow_span tracks execution duration."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        with workflow_tracing.workflow_span("buyer_bot", "timed_node"):
            import time

            time.sleep(0.01)  # 10ms

        # Verify duration_ms was set (should be >= 10ms)
        duration_calls = [
            call for call in mock_span.set_attribute.call_args_list if call[0][0] == "workflow.duration_ms"
        ]
        assert len(duration_calls) == 1
        duration_ms = duration_calls[0][0][1]
        assert duration_ms >= 10.0


@pytest.mark.skipif(not workflow_tracing._otel_available, reason="OpenTelemetry SDK not installed")
class TestWorkflowNodeDecorator:
    """Test @trace_workflow_node decorator."""

    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    def test_decorator_extracts_contact_id_from_state(self, mock_tracer, mock_state):
        """Decorator extracts contact_id from state dict."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        @workflow_tracing.trace_workflow_node("lead_bot", "test_node")
        def node_func(state: Dict) -> Dict:
            return state

        node_func(mock_state)

        # Verify contact_id was extracted from state
        mock_span.set_attribute.assert_any_call("workflow.contact_id", "test_contact_123")

    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    def test_decorator_adds_state_metadata(self, mock_tracer, mock_state):
        """Decorator adds current_step and temperature from state."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        @workflow_tracing.trace_workflow_node("lead_bot", "test_node")
        def node_func(state: Dict) -> Dict:
            return state

        node_func(mock_state)

        # Verify state metadata was added
        mock_span.set_attribute.assert_any_call("workflow.current_step", "day_3")
        mock_span.set_attribute.assert_any_call("workflow.temperature", "hot")

    @pytest.mark.asyncio
    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    async def test_decorator_works_on_async_functions(self, mock_tracer, mock_state):
        """Decorator works on async workflow nodes."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

        @workflow_tracing.trace_workflow_node("seller_bot", "async_node")
        async def async_node(state: Dict) -> Dict:
            state["result"] = "processed"
            return state

        result = await async_node(mock_state)

        assert result["result"] == "processed"
        mock_span.set_attribute.assert_any_call("workflow.bot_type", "seller_bot")


@pytest.mark.skipif(not workflow_tracing._otel_available, reason="OpenTelemetry SDK not installed")
class TestHandoffTracing:
    """Test cross-bot handoff tracing."""

    @patch("ghl_real_estate_ai.observability.workflow_tracing._tracer")
    def test_create_handoff_span(self, mock_tracer):
        """create_handoff_span creates span with handoff attributes."""
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span

        span = workflow_tracing.create_handoff_span(
            source_bot="lead",
            target_bot="buyer",
            contact_id="test_123",
            confidence=0.85,
            reason="buyer_intent_detected",
        )

        # Verify span was created
        mock_tracer.start_as_current_span.assert_called_once_with("handoff.lead_to_buyer")

        # Verify handoff attributes
        mock_span.set_attribute.assert_any_call("handoff.source_bot", "lead")
        mock_span.set_attribute.assert_any_call("handoff.target_bot", "buyer")
        mock_span.set_attribute.assert_any_call("handoff.contact_id", "test_123")
        mock_span.set_attribute.assert_any_call("handoff.confidence", 0.85)
        mock_span.set_attribute.assert_any_call("handoff.reason", "buyer_intent_detected")

    @patch("opentelemetry.trace.get_current_span")
    def test_get_trace_id_from_active_span(self, mock_get_span):
        """get_trace_id extracts trace ID from active span."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = True
        mock_context.trace_id = 0x1A2B3C4D5E6F7890ABCDEF1234567890
        mock_span.get_span_context.return_value = mock_context
        mock_get_span.return_value = mock_span

        trace_id = workflow_tracing.get_trace_id()

        assert trace_id == "1a2b3c4d5e6f7890abcdef1234567890"

    @patch("opentelemetry.propagate.inject")
    def test_propagate_trace_context(self, mock_inject):
        """propagate_trace_context injects context into metadata."""
        metadata = {"contact_id": "test_123"}

        result = workflow_tracing.propagate_trace_context(metadata)

        # Verify inject was called with metadata
        mock_inject.assert_called_once_with(metadata)
        assert result is metadata

    @patch("opentelemetry.propagate.extract")
    def test_extract_trace_context(self, mock_extract):
        """extract_trace_context extracts context from metadata."""
        metadata = {"traceparent": "00-trace-span-01"}

        workflow_tracing.extract_trace_context(metadata)

        # Verify extract was called
        mock_extract.assert_called_once_with(metadata)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_add_workflow_event_when_disabled(self, reset_otel):
        """add_workflow_event is safe to call when OTel disabled."""
        workflow_tracing._otel_available = False

        # Should not raise
        workflow_tracing.add_workflow_event("test_event", attr1="value1")

    @patch("opentelemetry.trace.get_current_span")
    def test_add_workflow_event_when_enabled(self, mock_get_span):
        """add_workflow_event adds event to current span."""
        mock_span = MagicMock()
        mock_context = MagicMock()
        mock_context.is_valid = True
        mock_span.get_span_context.return_value = mock_context
        mock_get_span.return_value = mock_span

        workflow_tracing._otel_available = True
        workflow_tracing.add_workflow_event("intent_detected", confidence=0.9)

        # Verify event was added
        mock_span.add_event.assert_called_once_with("intent_detected", {"confidence": 0.9})


# Integration test (requires OTel SDK installed)
@pytest.mark.integration
@pytest.mark.skipif(not workflow_tracing._otel_available, reason="OpenTelemetry SDK not installed")
class TestIntegration:
    """Integration tests with real OTel SDK."""

    @pytest.mark.asyncio
    async def test_full_workflow_trace(self, mock_state):
        """Test full workflow with real OTel spans."""
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        # Setup real tracer
        provider = TracerProvider()
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Reload workflow_tracing to get new tracer
        import importlib

        importlib.reload(workflow_tracing)

        # Execute traced workflow
        @workflow_tracing.trace_workflow_node("lead_bot", "test_integration")
        async def workflow_node(state: Dict) -> Dict:
            workflow_tracing.add_workflow_event("processing_started")
            state["processed"] = True
            workflow_tracing.add_workflow_event("processing_completed")
            return state

        result = await workflow_node(mock_state)

        assert result["processed"] is True
        # Spans should be exported to console (visible in test output)
