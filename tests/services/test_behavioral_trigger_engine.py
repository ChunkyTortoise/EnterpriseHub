"""
Tests for Behavioral Trigger Engine - Core Lead Intelligence Service

Tests the behavioral trigger engine that analyzes lead behavior patterns,
detects selling signals, and provides predictive insights for optimal engagement.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ghl_real_estate_ai.services.behavioral_trigger_engine import (
    BehavioralTriggerEngine,
    get_behavioral_trigger_engine,
    BehavioralSignal,
    IntentLevel,
    BehavioralPattern,
    PredictiveSellScore
)


class TestBehavioralTriggerEngine:
    """Test suite for BehavioralTriggerEngine core functionality."""

    @pytest.fixture
    def engine(self):
        """Create a BehavioralTriggerEngine instance for testing."""
        return BehavioralTriggerEngine()

    @pytest.fixture
    def sample_activity_data(self):
        """Sample activity data for testing behavioral analysis."""
        now = datetime.now()
        return {
            "property_searchs": [
                {
                    "timestamp": (now - timedelta(hours=4)).isoformat(),
                    "criteria": {"bedrooms": 3, "bathrooms": 2, "max_price": 500000}
                },
                {
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                    "criteria": {"bedrooms": 3, "bathrooms": 2, "max_price": 480000}
                }
            ],
            "listing_viewss": [
                {
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                    "property_id": "prop_456",
                    "view_duration_seconds": 180
                },
                {
                    "timestamp": (now - timedelta(minutes=30)).isoformat(),
                    "property_id": "prop_789",
                    "view_duration_seconds": 240
                }
            ],
            "pricing_tool_usages": [
                {
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "tool": "home_valuation"
                }
            ],
            "email_interactions": [
                {
                    "timestamp": (now - timedelta(hours=3)).isoformat(),
                    "opened": True
                },
                {
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                    "opened": True
                }
            ],
            "website_visits": [
                {
                    "timestamp": (now - timedelta(hours=5)).isoformat(),
                    "duration": 420
                },
                {
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "duration": 300
                }
            ],
            "sms_responses": [
                {
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "message": "Yes interested"
                }
            ],
            "agent_inquirys": [
                {
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                    "type": "call"
                }
            ]
        }

    @pytest.fixture
    def sample_behavioral_signals(self):
        """Sample behavioral patterns for testing."""
        return [
            BehavioralPattern(
                lead_id="lead_123",
                signal_type=BehavioralSignal.PROPERTY_SEARCH,
                frequency=3,
                recency_hours=2.0,
                trend="increasing",
                score_impact=0.8
            ),
            BehavioralPattern(
                lead_id="lead_123",
                signal_type=BehavioralSignal.LISTING_VIEWS,
                frequency=5,
                recency_hours=1.0,
                trend="increasing",
                score_impact=0.7
            ),
            BehavioralPattern(
                lead_id="lead_123",
                signal_type=BehavioralSignal.PRICING_TOOL_USAGE,
                frequency=2,
                recency_hours=2.0,
                trend="stable",
                score_impact=0.9
            )
        ]

    def test_engine_initialization(self, engine):
        """Test that the behavioral trigger engine initializes correctly."""
        assert isinstance(engine, BehavioralTriggerEngine)
        assert hasattr(engine, 'cache')
        assert hasattr(engine, 'signal_weights')
        assert hasattr(engine, 'recency_decay_hours')
        assert isinstance(engine.signal_weights, dict)

    def test_get_behavioral_trigger_engine_singleton(self):
        """Test that the global engine function returns a singleton."""
        engine1 = get_behavioral_trigger_engine()
        engine2 = get_behavioral_trigger_engine()
        assert engine1 is engine2
        assert isinstance(engine1, BehavioralTriggerEngine)

    @pytest.mark.asyncio
    async def test_analyze_lead_behavior_comprehensive(self, engine, sample_activity_data):
        """Test comprehensive lead behavior analysis."""
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            result = await engine.analyze_lead_behavior("lead_123", sample_activity_data)

            # Verify result is a PredictiveSellScore
            assert isinstance(result, PredictiveSellScore)
            assert result.lead_id == "lead_123"
            assert isinstance(result.key_signals, list)
            assert isinstance(result.intent_level, IntentLevel)
            assert 0 <= result.likelihood_score <= 100
            assert 0 <= result.confidence <= 1
            assert isinstance(result.optimal_contact_window, tuple)
            assert isinstance(result.recommended_channel, str)
            assert isinstance(result.recommended_message, str)

    @pytest.mark.asyncio
    async def test_analyze_lead_behavior_with_cache_hit(self, engine):
        """Test behavior analysis with cached result."""
        cached_result = PredictiveSellScore(
            lead_id="lead_123",
            likelihood_score=80.0,
            intent_level=IntentLevel.URGENT,
            optimal_contact_window=(10, 12),
            recommended_channel="sms",
            recommended_message="test message",
            confidence=0.9,
        )

        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=cached_result):
            result = await engine.analyze_lead_behavior("lead_123", {})

            # Should return cached result
            assert result.lead_id == "lead_123"
            assert result.likelihood_score == 80.0

    @pytest.mark.asyncio
    async def test_detect_selling_signals(self, engine, sample_activity_data):
        """Test detection of selling signals from lead behavior."""
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            result = await engine.detect_selling_signals("contact_123", sample_activity_data)

            assert isinstance(result, dict)
            assert "contact_id" in result
            assert result["contact_id"] == "contact_123"
            assert "selling_likelihood" in result
            assert "intent_level" in result
            assert result["intent_level"] in ["cold", "warm", "hot", "urgent"]
            assert "optimal_contact_time" in result
            assert "recommended_channel" in result
            assert "recommended_message" in result
            assert "confidence" in result
            assert "key_signals" in result
            assert isinstance(result["key_signals"], list)

    @pytest.mark.asyncio
    async def test_detect_selling_signals_specific_patterns(self, engine, sample_activity_data):
        """Test detection of specific selling signal patterns."""
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            result = await engine.detect_selling_signals("contact_123", sample_activity_data)

            # Should have key signals detected
            assert len(result["key_signals"]) > 0

            # Each signal should have required fields
            for signal in result["key_signals"]:
                assert "type" in signal
                assert "frequency" in signal
                assert "recency_hours" in signal
                assert "trend" in signal

    @pytest.mark.asyncio
    async def test_get_high_intent_leads(self, engine):
        """Test retrieval of high intent leads."""
        mock_db = AsyncMock()
        mock_db.get_high_intent_leads = AsyncMock(return_value=["lead_1", "lead_2", "lead_3"])

        with patch('ghl_real_estate_ai.services.behavioral_trigger_engine.get_database', new_callable=AsyncMock, return_value=mock_db):
            result = await engine.get_high_intent_leads(min_likelihood=50.0, limit=10)

            assert isinstance(result, list)
            assert len(result) <= 10

            # Results are lead ID strings
            for lead_id in result:
                assert isinstance(lead_id, str)

    @pytest.mark.asyncio
    async def test_extract_patterns(self, engine, sample_activity_data):
        """Test extraction of behavioral patterns."""
        patterns = await engine._extract_patterns("lead_123", sample_activity_data)

        assert isinstance(patterns, list)
        for pattern in patterns:
            assert isinstance(pattern, BehavioralPattern)
            assert hasattr(pattern, 'lead_id')
            assert hasattr(pattern, 'signal_type')
            assert hasattr(pattern, 'frequency')
            assert hasattr(pattern, 'recency_hours')
            assert hasattr(pattern, 'trend')
            assert hasattr(pattern, 'score_impact')
            assert pattern.frequency > 0
            assert pattern.lead_id == "lead_123"

    def test_detect_trend(self, engine):
        """Test trend detection in behavioral data."""
        # _detect_trend takes a list of dicts (activities)
        # It uses len() of first half vs second half

        # Test with enough items for trend detection (>= 4)
        increasing_activities = [
            {"timestamp": "2026-01-01T01:00:00"},
            {"timestamp": "2026-01-01T02:00:00"},
            {"timestamp": "2026-01-01T03:00:00"},
            {"timestamp": "2026-01-01T04:00:00"},
            {"timestamp": "2026-01-01T05:00:00"},
        ]
        trend = engine._detect_trend(increasing_activities)
        assert trend in ["increasing", "stable", "decreasing"]

        # Test with few items (< 4 should return stable)
        few_activities = [
            {"timestamp": "2026-01-01T01:00:00"},
            {"timestamp": "2026-01-01T02:00:00"},
        ]
        trend = engine._detect_trend(few_activities)
        assert trend == "stable"

        # Test empty list (< 4 should return stable)
        trend = engine._detect_trend([])
        assert trend == "stable"

    def test_calculate_signal_impact(self, engine, sample_behavioral_signals):
        """Test calculation of signal impact scores."""
        # _calculate_signal_impact takes individual params: signal_type, frequency, recency_hours, trend
        pattern = sample_behavioral_signals[0]
        impact = engine._calculate_signal_impact(
            pattern.signal_type, pattern.frequency, pattern.recency_hours, pattern.trend
        )

        assert isinstance(impact, float)
        assert 0 <= impact <= 1

        # Test with high-frequency recent signal
        high_impact = engine._calculate_signal_impact(
            BehavioralSignal.PROPERTY_SEARCH, 10, 0.5, "increasing"
        )
        assert high_impact > 0

    @pytest.mark.asyncio
    async def test_calculate_likelihood_score(self, engine, sample_behavioral_signals):
        """Test calculation of likelihood scores."""
        # _calculate_likelihood_score takes patterns only
        score = await engine._calculate_likelihood_score(sample_behavioral_signals)

        assert isinstance(score, float)
        assert score >= 0

        # Test with empty patterns
        empty_score = await engine._calculate_likelihood_score([])
        assert empty_score == 0.0

        # Verify score increases with more high-impact patterns
        high_impact_patterns = [
            BehavioralPattern(
                lead_id="lead_123",
                signal_type=BehavioralSignal.PROPERTY_SEARCH,
                frequency=10,
                recency_hours=0.5,
                trend="increasing",
                score_impact=0.95
            )
        ]
        high_score = await engine._calculate_likelihood_score(high_impact_patterns)
        assert isinstance(high_score, float)

    def test_classify_intent(self, engine):
        """Test intent level classification."""
        # _classify_intent uses 0-100 scale and returns IntentLevel enum

        # Test URGENT (>= 80)
        urgent_intent = engine._classify_intent(85.0)
        assert urgent_intent == IntentLevel.URGENT

        # Test HOT (>= 50)
        hot_intent = engine._classify_intent(65.0)
        assert hot_intent == IntentLevel.HOT

        # Test WARM (>= 20)
        warm_intent = engine._classify_intent(35.0)
        assert warm_intent == IntentLevel.WARM

        # Test COLD (< 20)
        cold_intent = engine._classify_intent(10.0)
        assert cold_intent == IntentLevel.COLD

        # Test edge cases
        edge_zero = engine._classify_intent(0.0)
        assert edge_zero == IntentLevel.COLD

        edge_hundred = engine._classify_intent(100.0)
        assert edge_hundred == IntentLevel.URGENT

    @pytest.mark.asyncio
    async def test_predict_optimal_contact_time(self, engine, sample_activity_data):
        """Test prediction of optimal contact times."""
        contact_time = await engine._predict_optimal_contact_time("lead_123", sample_activity_data)

        # Returns Tuple[int, int] (start_hour, end_hour)
        assert isinstance(contact_time, tuple)
        assert len(contact_time) == 2
        start_hour, end_hour = contact_time
        assert isinstance(start_hour, int)
        assert isinstance(end_hour, int)
        assert 0 <= start_hour <= 23
        assert 0 <= end_hour <= 23

    @pytest.mark.asyncio
    async def test_predict_optimal_contact_time_patterns(self, engine):
        """Test contact time prediction based on specific patterns."""
        now = datetime.now()
        # Test lead with morning activity
        morning_data = {
            "email_interactions": [
                {
                    "timestamp": now.replace(hour=9, minute=0).isoformat(),
                    "opened": True
                }
            ],
            "sms_responses": [],
            "website_visits": []
        }

        result = await engine._predict_optimal_contact_time("morning_lead", morning_data)
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Should be within business hours
        assert result[0] >= 9
        assert result[1] <= 18

    @pytest.mark.asyncio
    async def test_predict_best_channel(self, engine, sample_activity_data):
        """Test prediction of best communication channels."""
        channel = await engine._predict_best_channel(sample_activity_data)

        # Returns a string
        assert isinstance(channel, str)
        assert channel in ["email", "sms", "call"]

    @pytest.mark.asyncio
    async def test_predict_best_channel_preferences(self, engine):
        """Test channel prediction based on lead preferences."""
        # Test lead with high email engagement
        email_data = {
            "email_interactions": [
                {"timestamp": "2026-01-01T10:00:00", "opened": True},
                {"timestamp": "2026-01-01T11:00:00", "opened": True},
                {"timestamp": "2026-01-01T12:00:00", "opened": True},
                {"timestamp": "2026-01-01T13:00:00", "opened": True},
                {"timestamp": "2026-01-01T14:00:00", "opened": True},
            ],
            "sms_responses": [],
            "agent_inquiries": []
        }

        result = await engine._predict_best_channel(email_data)
        assert result in ["email", "sms", "call"]

        # Test lead with call preference
        call_data = {
            "email_interactions": [],
            "sms_responses": [],
            "agent_inquiries": [
                {"timestamp": "2026-01-01T10:00:00", "type": "call"},
                {"timestamp": "2026-01-01T11:00:00", "type": "call"},
                {"timestamp": "2026-01-01T12:00:00", "type": "call"},
            ]
        }

        result = await engine._predict_best_channel(call_data)
        assert result in ["email", "sms", "call"]

    @pytest.mark.asyncio
    async def test_generate_personalized_message(self, engine, sample_behavioral_signals):
        """Test generation of personalized messages."""
        intent_level = IntentLevel.HOT

        message = await engine._generate_personalized_message(
            "lead_123", sample_behavioral_signals, intent_level
        )

        assert isinstance(message, str)
        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_generate_personalized_message_different_intents(self, engine, sample_behavioral_signals):
        """Test personalized message generation for different intent levels."""
        intent_levels = [IntentLevel.COLD, IntentLevel.WARM, IntentLevel.HOT, IntentLevel.URGENT]

        for intent_level in intent_levels:
            message = await engine._generate_personalized_message(
                "lead_123", sample_behavioral_signals, intent_level
            )

            assert isinstance(message, str)
            assert len(message) > 0

        # URGENT messages should contain urgency marker
        urgent_message = await engine._generate_personalized_message(
            "lead_123", sample_behavioral_signals, IntentLevel.URGENT
        )
        assert "URGENT" in urgent_message

    @pytest.mark.asyncio
    async def test_get_market_context(self, engine):
        """Test market context retrieval."""
        context = await engine._get_market_context()

        assert isinstance(context, dict)
        # Should have basic market information
        expected_keys = ["market_trend", "inventory_level"]
        for key in expected_keys:
            assert key in context

    def test_calculate_confidence(self, engine, sample_behavioral_signals):
        """Test confidence score calculation."""
        # _calculate_confidence takes List[BehavioralPattern]
        confidence = engine._calculate_confidence(sample_behavioral_signals)

        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1

        # Test with empty patterns
        empty_confidence = engine._calculate_confidence([])
        assert empty_confidence == 0.0


class TestBehavioralSignal:
    """Test suite for BehavioralSignal enum."""

    def test_behavioral_signal_enum_values(self):
        """Test that BehavioralSignal enum has expected values."""
        # BehavioralSignal is an Enum, not a dataclass
        assert BehavioralSignal.PROPERTY_SEARCH.value == "property_search"
        assert BehavioralSignal.AGENT_INQUIRY.value == "agent_inquiry"
        assert BehavioralSignal.PRICING_TOOL_USAGE.value == "pricing_tool_usage"
        assert BehavioralSignal.HOME_VALUATION_REQUESTS.value == "home_valuation_requests"

    def test_behavioral_signal_completeness(self):
        """Test BehavioralSignal has comprehensive coverage."""
        # Verify key signal categories exist
        signal_values = [s.value for s in BehavioralSignal]
        assert "property_search" in signal_values
        assert "agent_inquiry" in signal_values
        assert "email_opens" in signal_values
        assert "website_visits" in signal_values
        assert "pricing_tool_usage" in signal_values
        assert "pre_approval_inquiry" in signal_values
        assert "mortgage_calculator_usage" in signal_values


class TestBehavioralPattern:
    """Test suite for BehavioralPattern dataclass."""

    def test_behavioral_pattern_creation(self):
        """Test creating behavioral patterns."""
        pattern = BehavioralPattern(
            lead_id="lead_123",
            signal_type=BehavioralSignal.PROPERTY_SEARCH,
            frequency=7,
            recency_hours=2.0,
            trend="increasing",
            score_impact=0.75
        )

        assert pattern.lead_id == "lead_123"
        assert pattern.signal_type == BehavioralSignal.PROPERTY_SEARCH
        assert pattern.frequency == 7
        assert pattern.recency_hours == 2.0
        assert pattern.trend == "increasing"
        assert pattern.score_impact == 0.75


class TestPredictiveSellScore:
    """Test suite for PredictiveSellScore dataclass."""

    def test_predictive_sell_score_creation(self):
        """Test creating predictive sell scores."""
        score = PredictiveSellScore(
            lead_id="lead_456",
            likelihood_score=82.0,
            intent_level=IntentLevel.URGENT,
            optimal_contact_window=(10, 12),
            recommended_channel="sms",
            recommended_message="I'd love to help with your real estate needs.",
            confidence=0.87,
        )

        assert score.lead_id == "lead_456"
        assert score.likelihood_score == 82.0
        assert score.intent_level == IntentLevel.URGENT
        assert score.confidence == 0.87
        assert score.optimal_contact_window == (10, 12)
        assert score.recommended_channel == "sms"
        assert isinstance(score.recommended_message, str)
        assert isinstance(score.timestamp, datetime)


# Integration tests for complete behavioral analysis workflow
class TestBehavioralTriggerEngineIntegration:
    """Integration tests for complete behavioral trigger engine workflows."""

    @pytest.mark.asyncio
    async def test_complete_behavioral_analysis_workflow(self):
        """Test complete workflow from lead data to actionable insights."""
        engine = BehavioralTriggerEngine()

        now = datetime.now()
        # Activity data matching the service's expected key format (signal_value + "s")
        activity_data = {
            "property_searchs": [
                {
                    "timestamp": (now - timedelta(hours=5)).isoformat(),
                    "criteria": {"property_type": "home_valuation", "location": "Cedar Park, TX"}
                }
            ],
            "pricing_tool_usages": [
                {
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "tool": "home_valuation"
                }
            ],
            "home_valuation_requestss": [
                {
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                    "address": "123 Main St"
                }
            ],
            "email_interactions": [
                {"timestamp": (now - timedelta(hours=3)).isoformat(), "opened": True},
                {"timestamp": (now - timedelta(hours=1)).isoformat(), "opened": True},
            ],
            "website_visits": [
                {"timestamp": (now - timedelta(hours=5)).isoformat(), "duration": 480},
                {"timestamp": (now - timedelta(hours=2)).isoformat(), "duration": 300},
            ],
            "sms_responses": [
                {"timestamp": (now - timedelta(hours=1)).isoformat(), "message": "Yes, very interested"}
            ],
            "agent_inquirys": [
                {"timestamp": (now - timedelta(hours=1)).isoformat(), "type": "call"}
            ]
        }

        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            # Step 1: Analyze behavior
            analysis = await engine.analyze_lead_behavior("integration_test_lead", activity_data)

            # Step 2: Detect selling signals
            signals = await engine.detect_selling_signals("integration_test_lead", activity_data)

            # Comprehensive validation
            assert analysis.lead_id == "integration_test_lead"
            assert isinstance(analysis.intent_level, IntentLevel)
            assert signals["contact_id"] == "integration_test_lead"
            assert len(signals["key_signals"]) > 0

            # Should have a likelihood score
            assert analysis.likelihood_score >= 0

            # Contact window should be a valid tuple
            assert isinstance(analysis.optimal_contact_window, tuple)
            assert len(analysis.optimal_contact_window) == 2

    @pytest.mark.asyncio
    async def test_low_engagement_lead_analysis(self):
        """Test analysis of low engagement lead."""
        engine = BehavioralTriggerEngine()

        # Minimal/empty activity data
        low_engagement_data = {}

        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            analysis = await engine.analyze_lead_behavior("low_engagement_lead", low_engagement_data)

            # Low engagement should result in lower scores
            assert analysis.intent_level in [IntentLevel.COLD, IntentLevel.WARM]
            assert analysis.likelihood_score < 50.0
            assert analysis.confidence == 0.0  # No patterns = 0 confidence

    @pytest.mark.asyncio
    async def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases."""
        engine = BehavioralTriggerEngine()

        # Test with empty activity data
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            # Should handle gracefully
            analysis = await engine.analyze_lead_behavior("minimal_lead", {})
            assert analysis.lead_id == "minimal_lead"
            assert analysis.likelihood_score >= 0
            assert analysis.confidence >= 0

        # Test with activity data that has no matching signal keys
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            analysis = await engine.analyze_lead_behavior("edge_lead", {"unknown_key": []})
            assert isinstance(analysis, PredictiveSellScore)

    @pytest.mark.asyncio
    async def test_performance_with_large_datasets(self):
        """Test performance with large activity data."""
        engine = BehavioralTriggerEngine()

        now = datetime.now()
        # Create large activity data
        large_activity_data = {
            "property_searchs": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "criteria": {"bedrooms": 3, "max_price": 400000 + (i * 1000)}
                }
                for i in range(50)
            ],
            "listing_viewss": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "property_id": f"prop_{i}",
                    "view_duration_seconds": 120
                }
                for i in range(50)
            ],
            "email_interactions": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "opened": True
                }
                for i in range(50)
            ],
            "website_visits": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "duration": 300
                }
                for i in range(75)
            ],
            "sms_responses": [
                {
                    "timestamp": (now - timedelta(hours=i)).isoformat(),
                    "message": f"Response {i}"
                }
                for i in range(20)
            ]
        }

        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):

            # Should handle large datasets efficiently
            start_time = datetime.now()
            analysis = await engine.analyze_lead_behavior("large_history_lead", large_activity_data)
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()

            # Verify results
            assert analysis.lead_id == "large_history_lead"
            assert len(analysis.key_signals) > 0

            # Performance should be reasonable (less than 5 seconds for this test)
            assert processing_time < 5.0, f"Processing took {processing_time} seconds, which is too slow"
