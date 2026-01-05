"""
Tests for Analytics Engine (Agent C3)

Validates:
- Metrics collection accuracy
- Conversion funnel tracking
- Response time analysis
- SMS compliance monitoring
- Topic/keyword distribution
- Performance overhead (<50ms target)
"""
import pytest
import asyncio
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.analytics_engine import (
    AnalyticsEngine,
    MetricsCollector,
    ConversionTracker,
    ResponseTimeAnalyzer,
    ComplianceMonitor,
    TopicDistributionAnalyzer,
    ConversationMetrics,
    ConversionFunnel
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory."""
    return str(tmp_path / "metrics")


@pytest.fixture
def metrics_collector(temp_storage):
    """Create metrics collector with temp storage."""
    return MetricsCollector(storage_dir=temp_storage)


@pytest.fixture
def analytics_engine(temp_storage):
    """Create analytics engine with temp storage."""
    return AnalyticsEngine(storage_dir=temp_storage)


class TestMetricsCollector:
    """Test metrics collection functionality."""

    @pytest.mark.asyncio
    async def test_record_conversation_event(self, metrics_collector):
        """Test recording a conversation event."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": [{"role": "user", "content": "Hi"}],
            "extracted_preferences": {"pathway": "wholesale"},
            "is_returning_lead": False
        }

        metrics = await metrics_collector.record_conversation_event(
            contact_id="c123",
            location_id="loc456",
            lead_score=75,
            previous_score=50,
            message="I'm looking for a 3-bedroom home in Austin",
            response="Great! What's your budget?",
            response_time_ms=250.5,
            context=context,
            appointment_scheduled=False
        )

        assert metrics.contact_id == "c123"
        assert metrics.location_id == "loc456"
        assert metrics.lead_score == 75
        assert metrics.previous_score == 50
        assert metrics.score_delta == 25
        assert metrics.classification == "hot"
        assert metrics.response_time_ms == 250.5
        assert not metrics.appointment_scheduled
        assert metrics.sms_compliant  # Response is under 160 chars

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, metrics_collector):
        """Test keyword extraction from messages."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Test budget keyword
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c1",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="My budget is $500,000",
            response="Got it!",
            response_time_ms=100,
            context=context
        )

        assert "budget" in metrics.keywords_detected

        # Test location keyword
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c2",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="I want a home in the Austin area",
            response="Great area!",
            response_time_ms=100,
            context=context
        )

        assert "location" in metrics.keywords_detected
        # Test timeline keyword
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c3",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="I need to move ASAP",
            response="Understood!",
            response_time_ms=100,
            context=context
        )

        assert "timeline" in metrics.keywords_detected

    @pytest.mark.asyncio
    async def test_topic_classification(self, metrics_collector):
        """Test topic classification."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Test buyer topic
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c1",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="I'm looking to buy a house",
            response="Let me help!",
            response_time_ms=100,
            context=context
        )

        assert "buyer" in metrics.topics

        # Test seller topic
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c2",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="I need to sell my home quickly",
            response="I can help!",
            response_time_ms=100,
            context=context
        )

        assert "seller" in metrics.topics

        # Test wholesale topic
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c3",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="Looking for a cash offer, sell as-is",
            response="We can do that!",
            response_time_ms=100,
            context=context
        )

        assert "wholesale" in metrics.topics

    @pytest.mark.asyncio
    async def test_sms_compliance_check(self, metrics_collector):
        """Test SMS compliance detection."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Compliant message (under 160 chars)
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c1",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="Test",
            response="Short response",
            response_time_ms=100,
            context=context
        )

        assert metrics.sms_compliant
        assert metrics.sms_length < 160

        # Non-compliant message (over 160 chars)
        long_response = "A" * 200
        metrics = await metrics_collector.record_conversation_event(
            contact_id="c2",
            location_id="loc1",
            lead_score=50,
            previous_score=40,
            message="Test",
            response=long_response,
            response_time_ms=100,
            context=context
        )

        assert not metrics.sms_compliant
        assert metrics.sms_length > 160

    @pytest.mark.asyncio
    async def test_tone_analysis(self, metrics_collector):
        """Test tone scoring."""
        # Professional tone should score high
        professional_keywords = metrics_collector._analyze_tone(
            "Thank you for reaching out. I would be happy to help you find the perfect home."
        )
        assert professional_keywords >= 0.9

        # Casual tone should score lower
        casual_keywords = metrics_collector._analyze_tone(
            "lol omg haha that's crazy!!! btw idk"
        )
        assert casual_keywords < 0.7

    @pytest.mark.asyncio
    async def test_metrics_persistence(self, metrics_collector):
        """Test that metrics persist to disk."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record metric
        await metrics_collector.record_conversation_event(
            contact_id="c1",
            location_id="test_loc",
            lead_score=60,
            previous_score=50,
            message="Test message",
            response="Test response",
            response_time_ms=100,
            context=context
        )

        # Force flush
        await metrics_collector._flush_buffer("test_loc")

        # Verify file exists
        metrics_file = metrics_collector._get_metrics_file("test_loc")
        assert metrics_file.exists()

        # Verify content
        with open(metrics_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["contact_id"] == "c1"
            assert data["lead_score"] == 60

    @pytest.mark.asyncio
    async def test_get_metrics(self, metrics_collector):
        """Test retrieving metrics."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record multiple metrics
        for i in range(5):
            await metrics_collector.record_conversation_event(
                contact_id=f"c{i}",
                location_id="test_loc",
                lead_score=50 + (i * 5),
                previous_score=40,
                message=f"Message {i}",
                response=f"Response {i}",
                response_time_ms=100 + (i * 10),
                context=context
            )

        # Retrieve metrics
        today = datetime.utcnow().strftime("%Y-%m-%d")
        metrics = await metrics_collector.get_metrics("test_loc", today, today)

        assert len(metrics) == 5
        assert all(isinstance(m, ConversationMetrics) for m in metrics)


class TestConversionTracker:
    """Test conversion funnel tracking."""

    @pytest.mark.asyncio
    async def test_calculate_funnel(self, metrics_collector):
        """Test conversion funnel calculation."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Create leads at different stages
        # Cold leads
        for i in range(10):
            await metrics_collector.record_conversation_event(
                contact_id=f"cold_{i}",
                location_id="test_loc",
                lead_score=30,
                previous_score=20,
                message="Test",
                response="Response",
                response_time_ms=100,
                context=context
            )

        # Warm leads
        for i in range(5):
            await metrics_collector.record_conversation_event(
                contact_id=f"warm_{i}",
                location_id="test_loc",
                lead_score=55,
                previous_score=50,
                message="Test",
                response="Response",
                response_time_ms=100,
                context=context
            )

        # Hot leads
        for i in range(3):
            await metrics_collector.record_conversation_event(
                contact_id=f"hot_{i}",
                location_id="test_loc",
                lead_score=80,
                previous_score=70,
                message="Test",
                response="Response",
                response_time_ms=100,
                context=context,
                appointment_scheduled=(i < 2)  # 2 out of 3 scheduled
            )

        # Calculate funnel
        tracker = ConversionTracker(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        funnel = await tracker.calculate_funnel("test_loc", today, today)

        assert funnel.cold_leads == 10
        assert funnel.warm_leads == 5
        assert funnel.hot_leads == 3
        assert funnel.appointments_scheduled == 2

        # Check conversion rates
        assert funnel.hot_to_appointment_rate == pytest.approx(2/3, rel=0.01)

    @pytest.mark.asyncio
    async def test_empty_funnel(self, metrics_collector):
        """Test funnel with no data."""
        tracker = ConversionTracker(metrics_collector)
        funnel = await tracker.calculate_funnel("empty_loc")

        assert funnel.cold_leads == 0
        assert funnel.warm_leads == 0
        assert funnel.hot_leads == 0
        assert funnel.appointments_scheduled == 0


class TestResponseTimeAnalyzer:
    """Test response time analysis."""

    @pytest.mark.asyncio
    async def test_analyze_response_times(self, metrics_collector):
        """Test response time analysis."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record metrics with varying response times
        response_times = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

        for i, rt in enumerate(response_times):
            await metrics_collector.record_conversation_event(
                contact_id=f"c{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="Test",
                response="Response",
                response_time_ms=rt,
                context=context
            )

        # Analyze
        analyzer = ResponseTimeAnalyzer(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        analysis = await analyzer.analyze_response_times("test_loc", today, today)

        assert "avg_response_time_ms" in analysis
        assert "median_response_time_ms" in analysis
        assert "p95_response_time_ms" in analysis
        assert "p99_response_time_ms" in analysis

        # Check values
        assert analysis["avg_response_time_ms"] == 550  # Mean of 100-1000
        assert analysis["median_response_time_ms"] == 550  # Median
        assert analysis["p95_response_time_ms"] >= 900  # 95th percentile

    @pytest.mark.asyncio
    async def test_response_times_by_classification(self, metrics_collector):
        """Test response time breakdown by lead classification."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Cold leads - slower response
        for i in range(5):
            await metrics_collector.record_conversation_event(
                contact_id=f"cold_{i}",
                location_id="test_loc",
                lead_score=30,
                previous_score=20,
                message="Test",
                response="Response",
                response_time_ms=500,
                context=context
            )

        # Hot leads - faster response
        for i in range(5):
            await metrics_collector.record_conversation_event(
                contact_id=f"hot_{i}",
                location_id="test_loc",
                lead_score=80,
                previous_score=70,
                message="Test",
                response="Response",
                response_time_ms=200,
                context=context
            )

        # Analyze
        analyzer = ResponseTimeAnalyzer(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        analysis = await analyzer.analyze_response_times("test_loc", today, today)

        assert "by_classification" in analysis
        assert "cold" in analysis["by_classification"]
        assert "hot" in analysis["by_classification"]

        # Hot leads should have faster avg response time
        assert analysis["by_classification"]["hot"]["avg"] < analysis["by_classification"]["cold"]["avg"]


class TestComplianceMonitor:
    """Test SMS compliance monitoring."""

    @pytest.mark.asyncio
    async def test_check_compliance(self, metrics_collector):
        """Test compliance checking."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Compliant messages
        for i in range(8):
            await metrics_collector.record_conversation_event(
                contact_id=f"c{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="Test",
                response="Short response",  # Under 160 chars
                response_time_ms=100,
                context=context
            )

        # Non-compliant messages
        for i in range(2):
            await metrics_collector.record_conversation_event(
                contact_id=f"nc{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="Test",
                response="A" * 200,  # Over 160 chars
                response_time_ms=100,
                context=context
            )

        # Check compliance
        monitor = ComplianceMonitor(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        compliance = await monitor.check_compliance("test_loc", today, today)

        assert compliance["total_messages"] == 10
        assert compliance["compliant_messages"] == 8
        assert compliance["compliance_rate"] == 0.8
        assert len(compliance["violations"]) == 2

    @pytest.mark.asyncio
    async def test_compliance_violations(self, metrics_collector):
        """Test compliance violation tracking."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record violation
        await metrics_collector.record_conversation_event(
            contact_id="violator",
            location_id="test_loc",
            lead_score=50,
            previous_score=40,
            message="Test",
            response="A" * 250,  # 250 chars
            response_time_ms=100,
            context=context
        )

        # Check violations
        monitor = ComplianceMonitor(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        compliance = await monitor.check_compliance("test_loc", today, today)

        assert len(compliance["violations"]) == 1
        violation = compliance["violations"][0]

        assert violation["contact_id"] == "violator"
        assert violation["length"] == 250
        assert violation["exceeded_by"] == 90  # 250 - 160


class TestTopicDistributionAnalyzer:
    """Test topic and keyword distribution analysis."""

    @pytest.mark.asyncio
    async def test_analyze_topics(self, metrics_collector):
        """Test topic distribution analysis."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Budget-related messages
        for i in range(5):
            await metrics_collector.record_conversation_event(
                contact_id=f"b{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="What's my budget range?",
                response="Tell me more",
                response_time_ms=100,
                context=context
            )

        # Location-related messages
        for i in range(3):
            await metrics_collector.record_conversation_event(
                contact_id=f"l{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="I want a house in the Austin area",
                response="Great area!",
                response_time_ms=100,
                context=context
            )
        # Analyze
        analyzer = TopicDistributionAnalyzer(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        analysis = await analyzer.analyze_topics("test_loc", today, today)

        assert "keywords" in analysis
        assert "topics" in analysis

        # Check keyword distribution
        assert "budget" in analysis["keywords"]
        assert analysis["keywords"]["budget"]["count"] == 5
        assert analysis["keywords"]["budget"]["percentage"] == pytest.approx(62.5, rel=0.1)  # 5/8 * 100

        assert "location" in analysis["keywords"]
        assert analysis["keywords"]["location"]["count"] == 3

    @pytest.mark.asyncio
    async def test_pathway_distribution(self, metrics_collector):
        """Test pathway (wholesale/listing) distribution."""
        context_wholesale = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": [],
            "extracted_preferences": {"pathway": "wholesale"}
        }

        context_listing = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": [],
            "extracted_preferences": {"pathway": "listing"}
        }

        # Wholesale contacts
        for i in range(7):
            await metrics_collector.record_conversation_event(
                contact_id=f"w{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="Test",
                response="Response",
                response_time_ms=100,
                context=context_wholesale
            )

        # Listing contacts
        for i in range(3):
            await metrics_collector.record_conversation_event(
                contact_id=f"l{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="Test",
                response="Response",
                response_time_ms=100,
                context=context_listing
            )

        # Analyze
        analyzer = TopicDistributionAnalyzer(metrics_collector)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        analysis = await analyzer.analyze_topics("test_loc", today, today)

        assert "pathways" in analysis
        assert analysis["pathways"]["wholesale"] == 7
        assert analysis["pathways"]["listing"] == 3


class TestAnalyticsEngine:
    """Test main analytics engine integration."""

    @pytest.mark.asyncio
    async def test_record_event(self, analytics_engine):
        """Test recording event through engine."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        metrics = await analytics_engine.record_event(
            contact_id="c123",
            location_id="loc456",
            lead_score=75,
            previous_score=50,
            message="I'm looking for a home",
            response="I can help!",
            response_time_ms=250.5,
            context=context
        )

        assert metrics.contact_id == "c123"
        assert metrics.lead_score == 75

    @pytest.mark.asyncio
    async def test_get_comprehensive_report(self, analytics_engine):
        """Test comprehensive report generation."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record some events
        for i in range(10):
            await analytics_engine.record_event(
                contact_id=f"c{i}",
                location_id="test_loc",
                lead_score=50 + (i * 3),
                previous_score=40,
                message=f"Looking for a home with budget $500k",
                response="Great! Let me help you.",
                response_time_ms=100 + (i * 10),
                context=context
            )

        # Get report
        today = datetime.utcnow().strftime("%Y-%m-%d")
        report = await analytics_engine.get_comprehensive_report("test_loc", today, today)

        assert "conversion_funnel" in report
        assert "response_times" in report
        assert "compliance" in report
        assert "topics" in report
        assert "location_id" in report
        assert "date_range" in report

    @pytest.mark.asyncio
    async def test_ab_test_tracking(self, analytics_engine):
        """Test A/B test experiment tracking."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record event with experiment data
        experiment_data = {
            "experiment_id": "exp_001",
            "variant": "a"
        }

        metrics = await analytics_engine.record_event(
            contact_id="c123",
            location_id="test_loc",
            lead_score=60,
            previous_score=50,
            message="Test",
            response="Response",
            response_time_ms=100,
            context=context,
            experiment_data=experiment_data
        )

        assert metrics.experiment_id == "exp_001"
        assert metrics.variant == "a"


class TestPerformance:
    """Test performance requirements."""

    @pytest.mark.asyncio
    async def test_collection_performance(self, analytics_engine):
        """Test that metrics collection is under 50ms."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Measure collection time
        start_time = time.time()

        await analytics_engine.record_event(
            contact_id="c123",
            location_id="test_loc",
            lead_score=60,
            previous_score=50,
            message="I'm looking for a 3-bedroom home in Austin with a budget of $500,000",
            response="Great! I can help you find the perfect home. What's your timeline?",
            response_time_ms=250,
            context=context
        )

        collection_time_ms = (time.time() - start_time) * 1000

        # Should be well under 50ms
        assert collection_time_ms < 50, f"Collection took {collection_time_ms:.2f}ms (target: <50ms)"

    @pytest.mark.asyncio
    async def test_bulk_collection_performance(self, analytics_engine):
        """Test performance with bulk operations."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Collect 100 metrics
        start_time = time.time()

        for i in range(100):
            await analytics_engine.record_event(
                contact_id=f"c{i}",
                location_id="test_loc",
                lead_score=50,
                previous_score=40,
                message="Test message",
                response="Test response",
                response_time_ms=100,
                context=context
            )

        total_time_ms = (time.time() - start_time) * 1000
        avg_time_per_event = total_time_ms / 100

        # Average should still be under 50ms
        assert avg_time_per_event < 50, f"Avg collection time: {avg_time_per_event:.2f}ms (target: <50ms)"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_message(self, analytics_engine):
        """Test handling of empty messages."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        metrics = await analytics_engine.record_event(
            contact_id="c123",
            location_id="test_loc",
            lead_score=50,
            previous_score=40,
            message="",
            response="",
            response_time_ms=100,
            context=context
        )

        assert metrics is not None
        assert metrics.message_length == 0
        assert metrics.keywords_detected == []

    @pytest.mark.asyncio
    async def test_missing_context_fields(self, analytics_engine):
        """Test handling of missing context fields."""
        # Minimal context
        context = {}

        metrics = await analytics_engine.record_event(
            contact_id="c123",
            location_id="test_loc",
            lead_score=50,
            previous_score=40,
            message="Test",
            response="Response",
            response_time_ms=100,
            context=context
        )

        assert metrics is not None
        assert metrics.conversation_duration_seconds == 0.0

    @pytest.mark.asyncio
    async def test_date_range_retrieval(self, analytics_engine):
        """Test retrieving metrics across date range."""
        context = {
            "created_at": datetime.utcnow().isoformat(),
            "conversation_history": []
        }

        # Record event
        await analytics_engine.record_event(
            contact_id="c123",
            location_id="test_loc",
            lead_score=50,
            previous_score=40,
            message="Test",
            response="Response",
            response_time_ms=100,
            context=context
        )

        # Get metrics for yesterday through tomorrow
        today = datetime.utcnow()
        yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")

        funnel = await analytics_engine.get_conversion_funnel("test_loc", yesterday, tomorrow)

        assert isinstance(funnel, ConversionFunnel)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
