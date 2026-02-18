"""
Tests for Churn Detection & Recovery Service

This module contains tests for the churn detection service,
including all 5 churn detection signals, weighted scoring,
and recovery strategies.
"""

import pytest
from datetime import datetime, timedelta, timezone

from ghl_real_estate_ai.services.churn_detection_service import (
    ChurnDetectionService,
    ChurnRiskLevel,
    RecoveryStrategy,
    ChurnRiskAssessment,
    RecoveryAction,
)


@pytest.fixture
def churn_service():
    """Create a churn detection service instance for testing."""
    return ChurnDetectionService()


@pytest.fixture
def sample_conversation_history():
    """Create a sample conversation history for testing."""
    return [
        {"role": "user", "content": "I'm interested in buying a home", "timestamp": (datetime.now() - timedelta(days=25)).isoformat()},
        {"role": "assistant", "content": "Great! I can help you with that. What's your budget?", "timestamp": (datetime.now() - timedelta(days=25)).isoformat()},
        {"role": "user", "content": "Around $500k", "timestamp": (datetime.now() - timedelta(days=24)).isoformat()},
        {"role": "assistant", "content": "Perfect! We have many options in that range. Would you like to see some listings?", "timestamp": (datetime.now() - timedelta(days=24)).isoformat()},
    ]


class TestChurnDetectionSignals:
    """Tests for the 5 churn detection signals."""
    
    @pytest.mark.asyncio
    async def test_no_response_time_signal_low_risk(self, churn_service):
        """Test no response time signal for low risk (<= 7 days)."""
        last_activity = datetime.now() - timedelta(days=5)
        signal_value = churn_service._analyze_no_response_time(5)
        
        assert signal_value == 0.0
    
    @pytest.mark.asyncio
    async def test_no_response_time_signal_medium_risk(self, churn_service):
        """Test no response time signal for medium risk (8-14 days)."""
        last_activity = datetime.now() - timedelta(days=10)
        signal_value = churn_service._analyze_no_response_time(10)
        
        assert signal_value == 0.5
    
    @pytest.mark.asyncio
    async def test_no_response_time_signal_high_risk(self, churn_service):
        """Test no response time signal for high risk (15-28 days)."""
        last_activity = datetime.now() - timedelta(days=20)
        signal_value = churn_service._analyze_no_response_time(20)
        
        assert signal_value == 0.75
    
    @pytest.mark.asyncio
    async def test_no_response_time_signal_critical_risk(self, churn_service):
        """Test no response time signal for critical risk (> 28 days)."""
        last_activity = datetime.now() - timedelta(days=35)
        signal_value = churn_service._analyze_no_response_time(35)
        
        assert signal_value == 1.0
    
    @pytest.mark.asyncio
    async def test_response_velocity_signal_low_risk(self, churn_service):
        """Test response velocity signal for low risk (<= 48 hours)."""
        conversation_history = [
            {"role": "assistant", "content": "Hello", "timestamp": (datetime.now() - timedelta(hours=24)).isoformat()},
            {"role": "user", "content": "Hi", "timestamp": datetime.now().isoformat()},
        ]
        signal_value = await churn_service._analyze_response_velocity(conversation_history)
        
        assert signal_value == 0.0
    
    @pytest.mark.asyncio
    async def test_response_velocity_signal_high_risk(self, churn_service):
        """Test response velocity signal for high risk (> 96 hours)."""
        conversation_history = [
            {"role": "assistant", "content": "Hello", "timestamp": (datetime.now() - timedelta(hours=120)).isoformat()},
            {"role": "user", "content": "Hi", "timestamp": datetime.now().isoformat()},
        ]
        signal_value = await churn_service._analyze_response_velocity(conversation_history)
        
        assert signal_value == 0.75
    
    @pytest.mark.asyncio
    async def test_sentiment_trend_signal_stable(self, churn_service):
        """Test sentiment trend signal for stable sentiment."""
        conversation_history = [
            {"role": "user", "content": "I'm happy with this", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "This is great", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "I love it", "timestamp": datetime.now().isoformat()},
        ]
        signal_value = await churn_service._analyze_sentiment_trend(conversation_history)
        
        # Stable or improving sentiment should have low risk
        assert signal_value <= 0.3
    
    @pytest.mark.asyncio
    async def test_sentiment_trend_signal_declining(self, churn_service):
        """Test sentiment trend signal for declining sentiment."""
        conversation_history = [
            {"role": "user", "content": "I love this", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "This is okay", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "I'm not sure about this", "timestamp": datetime.now().isoformat()},
        ]
        signal_value = await churn_service._analyze_sentiment_trend(conversation_history)
        
        # Declining sentiment should have higher risk
        assert signal_value >= 0.3
    
    @pytest.mark.asyncio
    async def test_pcs_decline_signal_no_decline(self, churn_service):
        """Test PCS score decline signal for no decline."""
        conversation_history = [
            {"role": "assistant", "content": "Hello", "metadata": {"pcs_score": 80}},
            {"role": "assistant", "content": "Hi there", "metadata": {"pcs_score": 85}},
        ]
        signal_value = await churn_service._analyze_pcs_decline(conversation_history)
        
        # No decline should have low risk
        assert signal_value == 0.0
    
    @pytest.mark.asyncio
    async def test_pcs_decline_signal_moderate_decline(self, churn_service):
        """Test PCS score decline signal for moderate decline (20 points)."""
        conversation_history = [
            {"role": "assistant", "content": "Hello", "metadata": {"pcs_score": 80}},
            {"role": "assistant", "content": "Hi there", "metadata": {"pcs_score": 60}},
        ]
        signal_value = await churn_service._analyze_pcs_decline(conversation_history)
        
        # 20 point decline should have medium risk
        assert signal_value == 0.5
    
    @pytest.mark.asyncio
    async def test_pcs_decline_signal_severe_decline(self, churn_service):
        """Test PCS score decline signal for severe decline (> 40 points)."""
        conversation_history = [
            {"role": "assistant", "content": "Hello", "metadata": {"pcs_score": 80}},
            {"role": "assistant", "content": "Hi there", "metadata": {"pcs_score": 30}},
        ]
        signal_value = await churn_service._analyze_pcs_decline(conversation_history)
        
        # > 40 point decline should have high risk
        assert signal_value == 1.0
    
    @pytest.mark.asyncio
    async def test_stalled_conversation_signal_not_stalled(self, churn_service):
        """Test stalled conversation signal for not stalled (<= 7 days)."""
        signal_value = churn_service._analyze_stalled_conversation(5)
        
        assert signal_value == 0.0
    
    @pytest.mark.asyncio
    async def test_stalled_conversation_signal_stalled(self, churn_service):
        """Test stalled conversation signal for stalled (> 7 days)."""
        signal_value = churn_service._analyze_stalled_conversation(15)
        
        assert signal_value >= 0.5


class TestChurnRiskScoring:
    """Tests for weighted churn risk scoring."""
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score_low(self, churn_service):
        """Test risk score calculation for low risk."""
        signals = {
            "no_response_time": 0.0,
            "response_velocity": 0.0,
            "sentiment_trend": 0.0,
            "pcs_score_decline": 0.0,
            "stalled_conversation": 0.0,
        }
        risk_score = churn_service._calculate_risk_score(signals)
        
        assert risk_score == 0.0
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score_medium(self, churn_service):
        """Test risk score calculation for medium risk."""
        signals = {
            "no_response_time": 0.5,
            "response_velocity": 0.5,
            "sentiment_trend": 0.5,
            "pcs_score_decline": 0.5,
            "stalled_conversation": 0.5,
        }
        risk_score = churn_service._calculate_risk_score(signals)
        
        # Weighted sum should be around 50
        assert 40 <= risk_score <= 60
    
    @pytest.mark.asyncio
    async def test_calculate_risk_score_high(self, churn_service):
        """Test risk score calculation for high risk."""
        signals = {
            "no_response_time": 1.0,
            "response_velocity": 1.0,
            "sentiment_trend": 1.0,
            "pcs_score_decline": 1.0,
            "stalled_conversation": 1.0,
        }
        risk_score = churn_service._calculate_risk_score(signals)
        
        # Weighted sum should be 100
        assert risk_score == 100.0
    
    @pytest.mark.asyncio
    async def test_determine_risk_level_low(self, churn_service):
        """Test risk level determination for low risk."""
        risk_level = churn_service._determine_risk_level(20)
        
        assert risk_level == ChurnRiskLevel.LOW
    
    @pytest.mark.asyncio
    async def test_determine_risk_level_medium(self, churn_service):
        """Test risk level determination for medium risk."""
        risk_level = churn_service._determine_risk_level(45)
        
        assert risk_level == ChurnRiskLevel.MEDIUM
    
    @pytest.mark.asyncio
    async def test_determine_risk_level_high(self, churn_service):
        """Test risk level determination for high risk."""
        risk_level = churn_service._determine_risk_level(70)
        
        assert risk_level == ChurnRiskLevel.HIGH
    
    @pytest.mark.asyncio
    async def test_determine_risk_level_critical(self, churn_service):
        """Test risk level determination for critical risk."""
        risk_level = churn_service._determine_risk_level(90)
        
        assert risk_level == ChurnRiskLevel.CRITICAL


class TestRecoveryStrategies:
    """Tests for recovery strategies."""
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_value_reminder(self, churn_service):
        """Test recovery strategy for 7 days inactive."""
        strategy = churn_service._get_recovery_strategy(7, ChurnRiskLevel.MEDIUM)
        
        assert strategy == RecoveryStrategy.VALUE_REMINDER
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_question_re_engagement(self, churn_service):
        """Test recovery strategy for 14 days inactive."""
        strategy = churn_service._get_recovery_strategy(14, ChurnRiskLevel.HIGH)
        
        assert strategy == RecoveryStrategy.QUESTION_RE_ENGAGEMENT
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_new_information(self, churn_service):
        """Test recovery strategy for 21 days inactive."""
        strategy = churn_service._get_recovery_strategy(21, ChurnRiskLevel.HIGH)
        
        assert strategy == RecoveryStrategy.NEW_INFORMATION
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_incentive_offer(self, churn_service):
        """Test recovery strategy for 30 days inactive."""
        strategy = churn_service._get_recovery_strategy(30, ChurnRiskLevel.HIGH)
        
        assert strategy == RecoveryStrategy.INCENTIVE_OFFER
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_final_check_in(self, churn_service):
        """Test recovery strategy for 45 days inactive."""
        strategy = churn_service._get_recovery_strategy(45, ChurnRiskLevel.HIGH)
        
        assert strategy == RecoveryStrategy.FINAL_CHECK_IN
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_archive(self, churn_service):
        """Test recovery strategy for 60 days inactive."""
        strategy = churn_service._get_recovery_strategy(60, ChurnRiskLevel.HIGH)
        
        assert strategy == RecoveryStrategy.ARCHIVE
    
    @pytest.mark.asyncio
    async def test_get_recovery_strategy_critical_risk(self, churn_service):
        """Test recovery strategy for critical risk."""
        strategy = churn_service._get_recovery_strategy(10, ChurnRiskLevel.CRITICAL)
        
        # Critical risk should trigger final check-in
        assert strategy == RecoveryStrategy.FINAL_CHECK_IN
    
    @pytest.mark.asyncio
    async def test_schedule_recovery_action(self, churn_service):
        """Test scheduling a recovery action."""
        contact_data = {
            "name": "John Doe",
            "topic": "buying a home",
            "market": "Rancho Cucamonga",
            "incentive": "a free consultation",
            "days_inactive": 14,
        }
        
        action = await churn_service.schedule_recovery_action(
            contact_id="test-contact",
            strategy=RecoveryStrategy.QUESTION_RE_ENGAGEMENT,
            contact_data=contact_data,
        )
        
        assert action.contact_id == "test-contact"
        assert action.strategy == RecoveryStrategy.QUESTION_RE_ENGAGEMENT
        assert action.channel == "sms"
        assert action.status == "pending"
        assert "John Doe" in action.message_template
    
    @pytest.mark.asyncio
    async def test_execute_recovery_action(self, churn_service):
        """Test executing a recovery action."""
        action = RecoveryAction(
            contact_id="test-contact",
            strategy=RecoveryStrategy.VALUE_REMINDER,
            message_template="Test message",
            channel="email",
            scheduled_at=datetime.now(),
            status="pending",
        )
        
        success = await churn_service.execute_recovery_action(action)
        
        assert success is True
        assert action.status == "sent"
        assert action.result == "Message sent successfully"


class TestChurnRiskAssessment:
    """Tests for complete churn risk assessment."""
    
    @pytest.mark.asyncio
    async def test_assess_churn_risk_low(self, churn_service, sample_conversation_history):
        """Test churn risk assessment for low risk."""
        last_activity = datetime.now() - timedelta(days=3)
        
        assessment = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=sample_conversation_history,
            last_activity=last_activity,
        )
        
        assert assessment.contact_id == "test-contact"
        assert assessment.risk_level == ChurnRiskLevel.LOW
        assert assessment.risk_score < 30
        assert assessment.days_inactive == 3
    
    @pytest.mark.asyncio
    async def test_assess_churn_risk_high(self, churn_service, sample_conversation_history):
        """Test churn risk assessment for high risk."""
        last_activity = datetime.now() - timedelta(days=25)
        
        assessment = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=sample_conversation_history,
            last_activity=last_activity,
        )
        
        assert assessment.contact_id == "test-contact"
        assert assessment.risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]
        assert assessment.risk_score >= 60
        assert assessment.days_inactive == 25

    @pytest.mark.asyncio
    async def test_assess_churn_risk_accepts_timezone_aware_last_activity(self, churn_service):
        """Regression: timezone-aware datetimes should not raise and should compute inactivity correctly."""
        last_activity = datetime.now(timezone.utc) - timedelta(days=5, hours=3)

        assessment = await churn_service.assess_churn_risk(
            contact_id="aware-contact",
            conversation_history=[],
            last_activity=last_activity,
            use_cache=False,
        )

        assert assessment.days_inactive == 5
        assert assessment.assessed_at.tzinfo is not None
    
    @pytest.mark.asyncio
    async def test_assess_churn_risk_with_cache(self, churn_service, sample_conversation_history):
        """Test churn risk assessment with caching."""
        last_activity = datetime.now() - timedelta(days=10)
        
        # First call
        assessment1 = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=sample_conversation_history,
            last_activity=last_activity,
            use_cache=True,
        )
        
        # Second call should use cache
        assessment2 = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=sample_conversation_history,
            last_activity=last_activity,
            use_cache=True,
        )
        
        assert assessment1.risk_score == assessment2.risk_score
        assert assessment1.risk_level == assessment2.risk_level


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_empty_conversation_history(self, churn_service):
        """Test churn risk assessment with empty conversation history."""
        last_activity = datetime.now() - timedelta(days=10)
        
        assessment = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=[],
            last_activity=last_activity,
        )
        
        # Should still return an assessment
        assert assessment.contact_id == "test-contact"
        assert assessment.risk_score >= 0
    
    @pytest.mark.asyncio
    async def test_single_message_conversation(self, churn_service):
        """Test churn risk assessment with single message."""
        conversation_history = [
            {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
        ]
        last_activity = datetime.now()
        
        assessment = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=conversation_history,
            last_activity=last_activity,
        )
        
        # Should still return an assessment
        assert assessment.contact_id == "test-contact"
        assert assessment.risk_score >= 0
    
    @pytest.mark.asyncio
    async def test_very_long_inactive_period(self, churn_service):
        """Test churn risk assessment with very long inactive period."""
        last_activity = datetime.now() - timedelta(days=365)
        
        assessment = await churn_service.assess_churn_risk(
            contact_id="test-contact",
            conversation_history=[],
            last_activity=last_activity,
        )
        
        # Should have critical risk
        assert assessment.risk_level == ChurnRiskLevel.CRITICAL
        assert assessment.risk_score >= 80
    
    @pytest.mark.asyncio
    async def test_batch_assess_contacts(self, churn_service):
        """Test batch assessment of multiple contacts."""
        contact_ids = ["contact-1", "contact-2", "contact-3"]
        
        assessments = await churn_service.batch_assess_contacts(contact_ids)
        
        assert len(assessments) == 3
        for assessment in assessments:
            assert assessment.contact_id in contact_ids
            assert assessment.risk_score >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
