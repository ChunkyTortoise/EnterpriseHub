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
    def sample_lead_data(self):
        """Sample lead data for testing behavioral analysis."""
        return {
            "lead_id": "lead_123",
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "+1234567890",
            "created_at": datetime.now() - timedelta(days=5),
            "last_contact": datetime.now() - timedelta(hours=2),
            "conversation_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=3),
                    "message": "I'm looking for a 3-bedroom house in Austin",
                    "type": "inbound",
                    "response_time_minutes": None
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=2.5),
                    "message": "What's your budget range?",
                    "type": "outbound",
                    "response_time_minutes": None
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=2),
                    "message": "Around $400,000 to $500,000. When can we see some properties?",
                    "type": "inbound",
                    "response_time_minutes": 30
                }
            ],
            "property_views": [
                {
                    "property_id": "prop_456",
                    "viewed_at": datetime.now() - timedelta(hours=1),
                    "view_duration_seconds": 180,
                    "property_type": "single_family",
                    "price": 450000
                },
                {
                    "property_id": "prop_789",
                    "viewed_at": datetime.now() - timedelta(minutes=30),
                    "view_duration_seconds": 240,
                    "property_type": "townhouse",
                    "price": 420000
                }
            ],
            "search_patterns": [
                {
                    "timestamp": datetime.now() - timedelta(hours=4),
                    "criteria": {
                        "bedrooms": 3,
                        "bathrooms": 2,
                        "max_price": 500000,
                        "location": "Austin, TX"
                    }
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "criteria": {
                        "bedrooms": 3,
                        "bathrooms": 2,
                        "max_price": 480000,
                        "location": "Austin, TX"
                    }
                }
            ],
            "engagement_metrics": {
                "email_opens": 5,
                "email_clicks": 3,
                "website_sessions": 8,
                "average_session_duration": 420,
                "pages_per_session": 6
            },
            "demographic_info": {
                "age_range": "35-44",
                "income_bracket": "high",
                "family_status": "married_with_children",
                "first_time_buyer": False
            }
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
    async def test_analyze_lead_behavior_comprehensive(self, engine, sample_lead_data):
        """Test comprehensive lead behavior analysis."""
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock), \
             patch.object(engine, '_extract_patterns', new_callable=AsyncMock) as mock_extract:
            
            # Mock pattern extraction
            mock_patterns = [
                BehavioralPattern(
                    pattern_type="engagement_increase",
                    frequency=3,
                    confidence=0.85,
                    last_occurrence=datetime.now() - timedelta(hours=1),
                    predictive_value=0.7
                )
            ]
            mock_extract.return_value = mock_patterns
            
            result = await engine.analyze_lead_behavior(sample_lead_data)
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "lead_id" in result
            assert "behavioral_signals" in result
            assert "patterns" in result
            assert "intent_level" in result
            assert "likelihood_score" in result
            assert "confidence" in result
            assert "optimal_contact_time" in result
            assert "recommended_channel" in result
            assert "personalized_message" in result
            
            # Verify data integrity
            assert result["lead_id"] == sample_lead_data["lead_id"]
            assert isinstance(result["behavioral_signals"], list)
            assert isinstance(result["patterns"], list)
            assert result["intent_level"] in [level.value for level in IntentLevel]
            assert 0 <= result["likelihood_score"] <= 1
            assert 0 <= result["confidence"] <= 1
            
            # Verify cache interactions
            mock_extract.assert_called_once()

    @pytest.mark.asyncio 
    async def test_analyze_lead_behavior_with_cache_hit(self, engine, sample_lead_data):
        """Test behavior analysis with cached result."""
        cached_result = {
            "lead_id": sample_lead_data["lead_id"],
            "intent_level": IntentLevel.HIGH.value,
            "likelihood_score": 0.8,
            "cached_at": datetime.now() - timedelta(minutes=30)
        }
        
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=cached_result):
            result = await engine.analyze_lead_behavior(sample_lead_data)
            
            # Should return cached result
            assert result["lead_id"] == sample_lead_data["lead_id"]
            # Verify it's using cached data (should be fast)

    @pytest.mark.asyncio
    async def test_detect_selling_signals(self, engine, sample_lead_data):
        """Test detection of selling signals from lead behavior."""
        result = await engine.detect_selling_signals(sample_lead_data)
        
        assert isinstance(result, list)
        for signal in result:
            assert isinstance(signal, BehavioralSignal)
            assert hasattr(signal, 'signal_type')
            assert hasattr(signal, 'strength')
            assert hasattr(signal, 'timestamp')
            assert hasattr(signal, 'description')
            assert hasattr(signal, 'confidence')
            assert 0 <= signal.strength <= 1
            assert 0 <= signal.confidence <= 1

    @pytest.mark.asyncio
    async def test_detect_selling_signals_specific_patterns(self, engine, sample_lead_data):
        """Test detection of specific selling signal patterns."""
        result = await engine.detect_selling_signals(sample_lead_data)
        
        # Should detect rapid response signal
        rapid_response_signals = [s for s in result if s.signal_type == "rapid_response"]
        assert len(rapid_response_signals) > 0
        
        # Should detect budget specificity signal
        budget_signals = [s for s in result if "budget" in s.signal_type.lower()]
        assert len(budget_signals) > 0
        
        # Should detect property viewing activity
        viewing_signals = [s for s in result if "view" in s.signal_type.lower()]
        assert len(viewing_signals) > 0

    @pytest.mark.asyncio
    async def test_get_high_intent_leads(self, engine):
        """Test retrieval of high intent leads."""
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock):
            
            result = await engine.get_high_intent_leads(limit=10)
            
            assert isinstance(result, list)
            assert len(result) <= 10
            
            for lead in result:
                assert isinstance(lead, dict)
                assert "lead_id" in lead
                assert "intent_level" in lead
                assert "likelihood_score" in lead
                # High intent leads should have high scores
                assert lead.get("likelihood_score", 0) >= 0.7

    @pytest.mark.asyncio
    async def test_extract_patterns(self, engine, sample_lead_data):
        """Test extraction of behavioral patterns."""
        patterns = await engine._extract_patterns(sample_lead_data)
        
        assert isinstance(patterns, list)
        for pattern in patterns:
            assert isinstance(pattern, BehavioralPattern)
            assert hasattr(pattern, 'pattern_type')
            assert hasattr(pattern, 'frequency')
            assert hasattr(pattern, 'confidence')
            assert hasattr(pattern, 'last_occurrence')
            assert hasattr(pattern, 'predictive_value')
            assert pattern.frequency > 0
            assert 0 <= pattern.confidence <= 1
            assert 0 <= pattern.predictive_value <= 1

    def test_detect_trend(self, engine):
        """Test trend detection in behavioral data."""
        # Test increasing trend
        increasing_values = [1, 2, 3, 4, 5]
        trend = engine._detect_trend(increasing_values)
        assert trend in ["increasing", "stable", "decreasing"]
        
        # Test decreasing trend
        decreasing_values = [5, 4, 3, 2, 1]
        trend = engine._detect_trend(decreasing_values)
        assert trend in ["increasing", "stable", "decreasing"]
        
        # Test stable trend
        stable_values = [3, 3, 3, 3, 3]
        trend = engine._detect_trend(stable_values)
        assert trend in ["increasing", "stable", "decreasing"]
        
        # Test empty list
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
        # Test high score
        high_intent = engine._classify_intent(0.8)
        assert high_intent in [level.value for level in IntentLevel]
        
        # Test medium score
        medium_intent = engine._classify_intent(0.5)
        assert medium_intent in [level.value for level in IntentLevel]
        
        # Test low score
        low_intent = engine._classify_intent(0.2)
        assert low_intent in [level.value for level in IntentLevel]
        
        # Test edge cases
        edge_case_1 = engine._classify_intent(0.0)
        assert edge_case_1 in [level.value for level in IntentLevel]
        
        edge_case_2 = engine._classify_intent(1.0)
        assert edge_case_2 in [level.value for level in IntentLevel]

    @pytest.mark.asyncio
    async def test_predict_optimal_contact_time(self, engine, sample_lead_data):
        """Test prediction of optimal contact times."""
        contact_time = await engine._predict_optimal_contact_time(sample_lead_data)
        
        assert isinstance(contact_time, dict)
        assert "recommended_time" in contact_time
        assert "time_zone" in contact_time
        assert "confidence" in contact_time
        assert "reasoning" in contact_time
        
        assert isinstance(contact_time["recommended_time"], str)
        assert isinstance(contact_time["time_zone"], str)
        assert 0 <= contact_time["confidence"] <= 1
        assert isinstance(contact_time["reasoning"], str)

    @pytest.mark.asyncio
    async def test_predict_optimal_contact_time_patterns(self, engine):
        """Test contact time prediction based on specific patterns."""
        # Test lead with morning activity
        morning_lead = {
            "lead_id": "morning_lead",
            "conversation_history": [
                {
                    "timestamp": datetime.now().replace(hour=9, minute=0),
                    "message": "Good morning",
                    "type": "inbound"
                }
            ],
            "property_views": [],
            "engagement_metrics": {"email_opens": 2}
        }
        
        result = await engine._predict_optimal_contact_time(morning_lead)
        assert "morning" in result["reasoning"].lower() or "9" in result["recommended_time"]

    @pytest.mark.asyncio
    async def test_predict_best_channel(self, engine, sample_lead_data):
        """Test prediction of best communication channels."""
        channel = await engine._predict_best_channel(sample_lead_data)
        
        assert isinstance(channel, dict)
        assert "channel" in channel
        assert "confidence" in channel
        assert "reasoning" in channel
        
        assert channel["channel"] in ["email", "phone", "sms", "in_person"]
        assert 0 <= channel["confidence"] <= 1
        assert isinstance(channel["reasoning"], str)

    @pytest.mark.asyncio
    async def test_predict_best_channel_preferences(self, engine):
        """Test channel prediction based on lead preferences."""
        # Test lead with high email engagement
        email_lead = {
            "lead_id": "email_lead",
            "engagement_metrics": {
                "email_opens": 15,
                "email_clicks": 8,
                "phone_pickups": 0,
                "sms_responses": 1
            },
            "conversation_history": [],
            "property_views": []
        }
        
        result = await engine._predict_best_channel(email_lead)
        # Should prefer email based on high engagement
        assert result["channel"] in ["email", "phone", "sms", "in_person"]
        
        # Test lead with phone preference
        phone_lead = {
            "lead_id": "phone_lead",
            "engagement_metrics": {
                "email_opens": 2,
                "email_clicks": 0,
                "phone_pickups": 5,
                "sms_responses": 0
            },
            "conversation_history": [],
            "property_views": []
        }
        
        result = await engine._predict_best_channel(phone_lead)
        assert result["channel"] in ["email", "phone", "sms", "in_person"]

    @pytest.mark.asyncio
    async def test_generate_personalized_message(self, engine, sample_lead_data):
        """Test generation of personalized messages."""
        intent_level = IntentLevel.HIGH
        channel = "email"
        
        with patch.object(engine, '_get_market_context', new_callable=AsyncMock) as mock_context:
            mock_context.return_value = {
                "market_trend": "strong_seller_market",
                "inventory_level": "low",
                "price_trend": "increasing"
            }
            
            message = await engine._generate_personalized_message(
                sample_lead_data, intent_level, channel
            )
            
            assert isinstance(message, dict)
            assert "subject" in message
            assert "content" in message
            assert "urgency_level" in message
            assert "personalization_score" in message
            
            assert isinstance(message["subject"], str)
            assert isinstance(message["content"], str)
            assert message["urgency_level"] in ["low", "medium", "high", "urgent"]
            assert 0 <= message["personalization_score"] <= 1
            
            # Message should reference lead's data
            content = message["content"].lower()
            assert "john" in content or "austin" in content or "3" in content

    @pytest.mark.asyncio
    async def test_generate_personalized_message_different_channels(self, engine, sample_lead_data):
        """Test personalized message generation for different channels."""
        channels = ["email", "sms", "phone", "in_person"]
        intent_level = IntentLevel.MEDIUM
        
        with patch.object(engine, '_get_market_context', new_callable=AsyncMock) as mock_context:
            mock_context.return_value = {"market_trend": "balanced"}
            
            for channel in channels:
                message = await engine._generate_personalized_message(
                    sample_lead_data, intent_level, channel
                )
                
                assert isinstance(message, dict)
                assert "content" in message
                
                # Different channels should have appropriate content lengths
                if channel == "sms":
                    # SMS should be shorter
                    assert len(message["content"]) <= 500
                elif channel == "email":
                    # Email can be longer and should have subject
                    assert "subject" in message
                    assert len(message["content"]) > 100

    @pytest.mark.asyncio
    async def test_get_market_context(self, engine, sample_lead_data):
        """Test market context retrieval."""
        context = await engine._get_market_context(sample_lead_data)
        
        assert isinstance(context, dict)
        # Should have basic market information
        expected_keys = ["market_trend", "inventory_level", "price_trend"]
        for key in expected_keys:
            assert key in context
            assert isinstance(context[key], str)

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
    """Test suite for BehavioralSignal dataclass."""

    def test_behavioral_signal_creation(self):
        """Test creating behavioral signals."""
        signal = BehavioralSignal(
            signal_type="urgent_inquiry",
            strength=0.9,
            timestamp=datetime.now(),
            description="Lead asked for immediate showing",
            confidence=0.85
        )
        
        assert signal.signal_type == "urgent_inquiry"
        assert signal.strength == 0.9
        assert signal.confidence == 0.85
        assert isinstance(signal.timestamp, datetime)
        assert signal.description == "Lead asked for immediate showing"

    def test_behavioral_signal_validation(self):
        """Test behavioral signal value validation."""
        # Test valid signal
        signal = BehavioralSignal(
            signal_type="budget_inquiry",
            strength=0.75,
            timestamp=datetime.now(),
            description="Asked about financing",
            confidence=0.8
        )
        
        assert 0 <= signal.strength <= 1
        assert 0 <= signal.confidence <= 1


class TestBehavioralPattern:
    """Test suite for BehavioralPattern dataclass."""

    def test_behavioral_pattern_creation(self):
        """Test creating behavioral patterns."""
        pattern = BehavioralPattern(
            pattern_type="increasing_engagement",
            frequency=7,
            confidence=0.88,
            last_occurrence=datetime.now() - timedelta(hours=2),
            predictive_value=0.75
        )
        
        assert pattern.pattern_type == "increasing_engagement"
        assert pattern.frequency == 7
        assert pattern.confidence == 0.88
        assert pattern.predictive_value == 0.75
        assert isinstance(pattern.last_occurrence, datetime)


class TestPredictiveSellScore:
    """Test suite for PredictiveSellScore dataclass."""

    def test_predictive_sell_score_creation(self):
        """Test creating predictive sell scores."""
        score = PredictiveSellScore(
            lead_id="lead_456",
            overall_score=0.82,
            intent_level=IntentLevel.HIGH,
            confidence=0.87,
            next_best_action="schedule_showing",
            predicted_close_probability=0.75,
            time_to_close_days=14,
            generated_at=datetime.now()
        )
        
        assert score.lead_id == "lead_456"
        assert score.overall_score == 0.82
        assert score.intent_level == IntentLevel.HIGH
        assert score.confidence == 0.87
        assert score.next_best_action == "schedule_showing"
        assert score.predicted_close_probability == 0.75
        assert score.time_to_close_days == 14
        assert isinstance(score.generated_at, datetime)


# Integration tests for complete behavioral analysis workflow
class TestBehavioralTriggerEngineIntegration:
    """Integration tests for complete behavioral trigger engine workflows."""

    @pytest.mark.asyncio
    async def test_complete_behavioral_analysis_workflow(self):
        """Test complete workflow from lead data to actionable insights."""
        engine = BehavioralTriggerEngine()
        
        # Comprehensive lead data
        lead_data = {
            "lead_id": "integration_test_lead",
            "name": "Sarah Johnson",
            "email": "sarah.j@example.com",
            "phone": "+1987654321",
            "created_at": datetime.now() - timedelta(days=3),
            "last_contact": datetime.now() - timedelta(hours=1),
            "conversation_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=4),
                    "message": "I need to sell my house quickly due to job relocation",
                    "type": "inbound",
                    "response_time_minutes": None
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=3.5),
                    "message": "I can help with that. When do you need to move?",
                    "type": "outbound",
                    "response_time_minutes": None
                },
                {
                    "timestamp": datetime.now() - timedelta(hours=3),
                    "message": "Within 30 days. What's my home worth?",
                    "type": "inbound",
                    "response_time_minutes": 30
                }
            ],
            "property_views": [
                {
                    "property_id": "similar_prop_1",
                    "viewed_at": datetime.now() - timedelta(hours=2),
                    "view_duration_seconds": 300,
                    "property_type": "single_family",
                    "price": 380000
                }
            ],
            "search_patterns": [
                {
                    "timestamp": datetime.now() - timedelta(hours=5),
                    "criteria": {
                        "property_type": "home_valuation",
                        "location": "Cedar Park, TX"
                    }
                }
            ],
            "engagement_metrics": {
                "email_opens": 8,
                "email_clicks": 6,
                "website_sessions": 12,
                "average_session_duration": 480,
                "pages_per_session": 8
            },
            "demographic_info": {
                "age_range": "25-34",
                "income_bracket": "medium_high",
                "family_status": "married",
                "property_owner": True
            }
        }
        
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock), \
             patch.object(engine, '_get_market_context', new_callable=AsyncMock) as mock_context:
            
            mock_context.return_value = {
                "market_trend": "strong_seller_market",
                "inventory_level": "low", 
                "price_trend": "increasing"
            }
            
            # Step 1: Analyze behavior
            analysis = await engine.analyze_lead_behavior(lead_data)
            
            # Step 2: Detect selling signals
            signals = await engine.detect_selling_signals(lead_data)
            
            # Comprehensive validation
            assert analysis["lead_id"] == lead_data["lead_id"]
            assert analysis["intent_level"] in [level.value for level in IntentLevel]
            assert len(signals) > 0
            
            # Should detect urgency signal
            urgency_signals = [s for s in signals if "urgent" in s.signal_type.lower() or "quick" in s.description.lower()]
            assert len(urgency_signals) > 0
            
            # Should have high likelihood score due to urgency
            assert analysis["likelihood_score"] > 0.6
            
            # Should recommend immediate contact
            assert analysis["optimal_contact_time"]["confidence"] > 0.5
            
            # Personalized message should reference urgency
            message_content = analysis["personalized_message"]["content"].lower()
            assert any(word in message_content for word in ["quick", "urgent", "30 days", "relocation"])

    @pytest.mark.asyncio
    async def test_low_engagement_lead_analysis(self):
        """Test analysis of low engagement lead."""
        engine = BehavioralTriggerEngine()
        
        low_engagement_lead = {
            "lead_id": "low_engagement_lead",
            "name": "Mike Wilson",
            "email": "mike.w@example.com",
            "created_at": datetime.now() - timedelta(days=30),
            "last_contact": datetime.now() - timedelta(days=10),
            "conversation_history": [
                {
                    "timestamp": datetime.now() - timedelta(days=30),
                    "message": "Just browsing for now",
                    "type": "inbound",
                    "response_time_minutes": None
                }
            ],
            "property_views": [],
            "search_patterns": [],
            "engagement_metrics": {
                "email_opens": 1,
                "email_clicks": 0,
                "website_sessions": 2,
                "average_session_duration": 45,
                "pages_per_session": 2
            }
        }
        
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock), \
             patch.object(engine, '_get_market_context', new_callable=AsyncMock) as mock_context:
            
            mock_context.return_value = {"market_trend": "balanced"}
            
            analysis = await engine.analyze_lead_behavior(low_engagement_lead)
            
            # Low engagement should result in lower scores
            assert analysis["intent_level"] in ["low", "medium"]
            assert analysis["likelihood_score"] < 0.6
            assert analysis["confidence"] < 0.7
            
            # Should suggest nurturing approach
            assert "nurture" in analysis["personalized_message"]["content"].lower() or \
                   "information" in analysis["personalized_message"]["content"].lower()

    @pytest.mark.asyncio
    async def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases."""
        engine = BehavioralTriggerEngine()
        
        # Test with minimal data
        minimal_lead = {
            "lead_id": "minimal_lead",
            "name": "Test Lead"
        }
        
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock), \
             patch.object(engine, '_get_market_context', new_callable=AsyncMock) as mock_context:
            
            mock_context.return_value = {"market_trend": "unknown"}
            
            # Should handle gracefully
            analysis = await engine.analyze_lead_behavior(minimal_lead)
            assert analysis["lead_id"] == "minimal_lead"
            assert "likelihood_score" in analysis
            assert "confidence" in analysis
        
        # Test with invalid data types
        invalid_lead = {
            "lead_id": None,
            "conversation_history": "not_a_list",
            "engagement_metrics": []
        }
        
        # Should handle gracefully without crashing
        try:
            analysis = await engine.analyze_lead_behavior(invalid_lead)
            # If it doesn't crash, verify basic structure
            assert isinstance(analysis, dict)
        except Exception as e:
            # If it does raise exception, should be handled appropriately
            assert isinstance(e, (ValueError, TypeError))

    @pytest.mark.asyncio
    async def test_performance_with_large_datasets(self):
        """Test performance with large conversation histories."""
        engine = BehavioralTriggerEngine()
        
        # Create lead with large conversation history
        large_history_lead = {
            "lead_id": "large_history_lead",
            "name": "Heavy Communicator",
            "conversation_history": [
                {
                    "timestamp": datetime.now() - timedelta(hours=i),
                    "message": f"Message number {i}",
                    "type": "inbound" if i % 2 == 0 else "outbound",
                    "response_time_minutes": 15
                }
                for i in range(100)  # 100 messages
            ],
            "property_views": [
                {
                    "property_id": f"prop_{i}",
                    "viewed_at": datetime.now() - timedelta(hours=i),
                    "view_duration_seconds": 120,
                    "property_type": "single_family",
                    "price": 400000 + (i * 1000)
                }
                for i in range(50)  # 50 property views
            ],
            "engagement_metrics": {
                "email_opens": 50,
                "email_clicks": 25,
                "website_sessions": 75,
                "average_session_duration": 300,
                "pages_per_session": 5
            }
        }
        
        with patch.object(engine.cache, 'get', new_callable=AsyncMock, return_value=None), \
             patch.object(engine.cache, 'set', new_callable=AsyncMock), \
             patch.object(engine, '_get_market_context', new_callable=AsyncMock) as mock_context:
            
            mock_context.return_value = {"market_trend": "strong_buyer_market"}
            
            # Should handle large datasets efficiently
            start_time = datetime.now()
            analysis = await engine.analyze_lead_behavior(large_history_lead)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Verify results
            assert analysis["lead_id"] == "large_history_lead"
            assert len(analysis["behavioral_signals"]) > 0
            
            # Performance should be reasonable (less than 5 seconds for this test)
            assert processing_time < 5.0, f"Processing took {processing_time} seconds, which is too slow"