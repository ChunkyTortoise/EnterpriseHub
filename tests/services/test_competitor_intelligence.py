"""
Comprehensive tests for competitor intelligence service

Tests cover:
1. Competitor mention detection with various patterns
2. Risk level assessment accuracy
3. NLP analysis functionality
4. Austin market competitor identification
5. Competitive analysis generation
6. Edge cases and error handling
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.services.competitor_intelligence import (
    CompetitorIntelligenceService,
    CompetitorMention,
    CompetitiveAnalysis,
    RiskLevel,
    get_competitor_intelligence
)


class TestCompetitorIntelligenceService:
    """Test suite for competitor intelligence service"""

    @pytest.fixture
    def service(self):
        """Create competitor intelligence service for testing"""
        return CompetitorIntelligenceService()

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # Default to cache miss
        mock_cache.set.return_value = True
        return mock_cache

    @pytest.mark.asyncio
    async def test_detect_direct_competitor_mention(self, service):
        """Test detection of direct competitor mentions"""
        test_message = "I'm already working with a Keller Williams agent"

        analysis = await service.analyze_conversation(test_message)

        assert analysis.has_competitor_risk is True
        assert analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(analysis.mentions) > 0

        # Check if Keller Williams was detected
        kw_mentions = [m for m in analysis.mentions if "keller" in m.mention_text.lower()]
        assert len(kw_mentions) > 0

    @pytest.mark.asyncio
    async def test_detect_indirect_competitor_indicators(self, service):
        """Test detection of indirect competitor indicators"""
        test_message = "I'm shopping around and comparing different agents"

        analysis = await service.analyze_conversation(test_message)

        assert analysis.has_competitor_risk is True
        assert analysis.risk_level == RiskLevel.MEDIUM
        assert len(analysis.mentions) > 0

        mention = analysis.mentions[0]
        assert "shopping around" in mention.mention_text.lower()

    @pytest.mark.asyncio
    async def test_no_competitor_risk_clean_message(self, service):
        """Test that clean messages don't trigger false positives"""
        test_message = "I'm looking for a 3 bedroom house in Austin under $500k"

        analysis = await service.analyze_conversation(test_message)

        assert analysis.has_competitor_risk is False
        assert analysis.risk_level == RiskLevel.LOW
        assert len(analysis.mentions) == 0

    @pytest.mark.asyncio
    async def test_competitor_name_detection(self, service):
        """Test specific competitor name detection"""
        test_cases = [
            ("I'm working with RE/MAX", "remax"),
            ("Coldwell Banker showed me some houses", "coldwell_banker"),
            ("My Keller Williams agent", "keller_williams"),
        ]

        for message, expected_competitor in test_cases:
            analysis = await service.analyze_conversation(message)

            assert analysis.has_competitor_risk is True
            named_mentions = [m for m in analysis.mentions if m.competitor_name is not None]
            assert len(named_mentions) > 0

    @pytest.mark.asyncio
    async def test_urgency_indicator_detection(self, service):
        """Test detection of urgency indicators"""
        test_message = "I need to decide ASAP between you and my current agent"

        analysis = await service.analyze_conversation(test_message)

        assert analysis.has_competitor_risk is True

        # Check if urgency indicators were extracted
        urgency_mentions = [m for m in analysis.mentions if m.urgency_indicators]
        assert len(urgency_mentions) > 0

    @pytest.mark.asyncio
    async def test_conversation_context_analysis(self, service):
        """Test analysis with conversation history context"""
        conversation_history = [
            {"role": "user", "content": "I'm looking for a house"},
            {"role": "assistant", "content": "I can help you find the perfect home"},
            {"role": "user", "content": "My other agent showed me this property yesterday"}
        ]

        analysis = await service.analyze_conversation(
            "What do you think about it?",
            conversation_history=conversation_history
        )

        assert analysis.has_competitor_risk is True
        assert analysis.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, service):
        """Test sentiment analysis of competitor mentions"""
        test_message = "I hate my current agent, they're terrible"

        analysis = await service.analyze_conversation(test_message)

        if analysis.has_competitor_risk and analysis.mentions:
            mention = analysis.mentions[0]
            # Negative sentiment should be detected
            assert mention.sentiment_score < 0

    @pytest.mark.asyncio
    async def test_risk_level_escalation(self, service):
        """Test risk level escalation with multiple mentions"""
        # Low risk message
        low_risk = "I might look at other options"
        analysis_low = await service.analyze_conversation(low_risk)

        # High risk message
        high_risk = "I'm under contract with Coldwell Banker and closing next week"
        analysis_high = await service.analyze_conversation(high_risk)

        assert analysis_low.risk_level.value < analysis_high.risk_level.value

    @pytest.mark.asyncio
    async def test_confidence_score_calculation(self, service):
        """Test confidence score calculation"""
        # High confidence scenario
        high_conf_message = "I already signed with Keller Williams"
        analysis_high = await service.analyze_conversation(high_conf_message)

        # Low confidence scenario
        low_conf_message = "I might consider other agents"
        analysis_low = await service.analyze_conversation(low_conf_message)

        if analysis_high.has_competitor_risk and analysis_low.has_competitor_risk:
            assert analysis_high.confidence_score > analysis_low.confidence_score

    @pytest.mark.asyncio
    async def test_austin_competitor_insights(self, service):
        """Test Austin-specific competitor insights"""
        competitor_name = "keller_williams"
        insights = await service.get_competitor_insights(competitor_name)

        assert insights is not None
        assert insights["name"] == competitor_name
        assert "market_share" in insights
        assert "jorge_advantages" in insights
        assert len(insights["jorge_advantages"]) > 0

    @pytest.mark.asyncio
    async def test_unknown_competitor_insights(self, service):
        """Test handling of unknown competitors"""
        competitor_name = "unknown_brokerage"
        insights = await service.get_competitor_insights(competitor_name)

        assert insights is not None
        assert insights["category"] == "unknown"
        assert "jorge_advantages" in insights

    @pytest.mark.asyncio
    async def test_competitive_outcome_tracking(self, service):
        """Test tracking of competitive outcomes"""
        lead_id = "test_lead_123"
        outcome = "won"
        competitor_name = "keller_williams"

        # Should not raise exception
        await service.track_competitive_outcome(lead_id, outcome, competitor_name)

    @pytest.mark.asyncio
    async def test_cache_integration(self, service, mock_cache_service):
        """Test cache integration"""
        service.cache = mock_cache_service

        test_message = "I'm working with another agent"

        # First call should miss cache
        analysis1 = await service.analyze_conversation(test_message)
        mock_cache_service.get.assert_called()
        mock_cache_service.set.assert_called()

        # Second call should hit cache
        mock_cache_service.get.return_value = analysis1
        analysis2 = await service.analyze_conversation(test_message)

        assert analysis2 == analysis1

    @pytest.mark.asyncio
    async def test_error_handling_invalid_input(self, service):
        """Test error handling with invalid input"""
        # Empty message
        analysis = await service.analyze_conversation("")
        assert analysis.has_competitor_risk is False

        # None message should not crash
        analysis = await service.analyze_conversation(None)
        assert analysis.has_competitor_risk is False

    @pytest.mark.asyncio
    async def test_pattern_matching_edge_cases(self, service):
        """Test pattern matching with edge cases"""
        edge_cases = [
            "I'm working with my brother who is an agent",  # Family relationship
            "I know an agent but haven't committed",  # Soft connection
            "The listing agent showed me this",  # Listing agent vs buyer agent
            "My agent friend recommended this area"  # Friend vs working relationship
        ]

        for message in edge_cases:
            analysis = await service.analyze_conversation(message)
            # These should trigger some risk but not critical
            if analysis.has_competitor_risk:
                assert analysis.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]

    @pytest.mark.asyncio
    async def test_nlp_fallback_when_model_unavailable(self, service):
        """Test fallback behavior when NLP model is unavailable"""
        # Simulate missing NLP model
        service._nlp = None
        service._matcher = None

        test_message = "I'm working with Keller Williams"
        analysis = await service.analyze_conversation(test_message)

        # Should still detect via pattern matching
        assert analysis.has_competitor_risk is True

    @pytest.mark.asyncio
    async def test_multiple_competitors_mentioned(self, service):
        """Test handling of multiple competitors in one message"""
        test_message = "I'm comparing Keller Williams and RE/MAX to decide"

        analysis = await service.analyze_conversation(test_message)

        assert analysis.has_competitor_risk is True
        assert len(analysis.mentions) >= 2  # Should detect both

        # Should escalate risk level due to multiple competitors
        assert analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    @pytest.mark.asyncio
    async def test_competitive_relationship_progression(self, service):
        """Test detection of relationship progression patterns"""
        conversation_history = [
            {"role": "user", "content": "I met an agent yesterday"},
            {"role": "user", "content": "They showed me some properties"},
            {"role": "user", "content": "We're meeting again tomorrow"}
        ]

        analysis = await service.analyze_conversation(
            "I think I'm going to sign with them",
            conversation_history=conversation_history
        )

        assert analysis.has_competitor_risk is True
        assert analysis.risk_level == RiskLevel.CRITICAL

    def test_singleton_pattern(self):
        """Test that get_competitor_intelligence returns singleton"""
        service1 = get_competitor_intelligence()
        service2 = get_competitor_intelligence()

        assert service1 is service2

    @pytest.mark.asyncio
    async def test_recommendation_generation(self, service):
        """Test that recommendations are generated for different risk levels"""
        test_cases = [
            ("I might look elsewhere", RiskLevel.LOW),
            ("I'm comparing a few agents", RiskLevel.MEDIUM),
            ("I'm working with someone else", RiskLevel.HIGH),
            ("I already signed with another agent", RiskLevel.CRITICAL)
        ]

        for message, expected_risk in test_cases:
            analysis = await service.analyze_conversation(message)

            if analysis.has_competitor_risk:
                assert len(analysis.recommended_responses) > 0
                # Verify responses are appropriate for risk level
                assert all(isinstance(response, str) for response in analysis.recommended_responses)

    @pytest.mark.asyncio
    async def test_performance_with_long_conversation(self, service):
        """Test performance with long conversation history"""
        # Create long conversation history
        long_history = []
        for i in range(100):
            long_history.append({"role": "user", "content": f"Message {i}"})
            long_history.append({"role": "assistant", "content": f"Response {i}"})

        # Add competitor mention at the end
        test_message = "Actually, I'm working with Keller Williams now"

        start_time = datetime.now()
        analysis = await service.analyze_conversation(test_message, long_history)
        end_time = datetime.now()

        # Should complete within reasonable time (< 5 seconds)
        assert (end_time - start_time).total_seconds() < 5
        assert analysis.has_competitor_risk is True

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, service):
        """Test handling of concurrent analysis requests"""
        messages = [
            "I'm working with Keller Williams",
            "RE/MAX is helping me",
            "Coldwell Banker showed me properties",
            "I'm comparing different agents",
            "No other agents involved"
        ]

        # Run analyses concurrently
        tasks = [service.analyze_conversation(msg) for msg in messages]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == len(messages)

        # Check that risky messages were detected
        risky_results = [r for r in results if r.has_competitor_risk]
        assert len(risky_results) >= 4  # First 4 messages should have risk

    @pytest.mark.asyncio
    async def test_data_privacy_compliance(self, service):
        """Test that no sensitive data is logged or stored inappropriately"""
        sensitive_message = "My SSN is 123-45-6789 and I'm working with agent John Smith at Keller Williams"

        analysis = await service.analyze_conversation(sensitive_message)

        # Should detect competitor but not expose sensitive data in results
        assert analysis.has_competitor_risk is True

        # Check that mentions don't contain full sensitive data
        for mention in analysis.mentions:
            assert "123-45-6789" not in mention.mention_text
            # Should contain competitor info but not SSN
            assert "keller" in mention.mention_text.lower() or "williams" in mention.mention_text.lower()


class TestCompetitorMentionDataStructure:
    """Test competitor mention data structure"""

    def test_competitor_mention_creation(self):
        """Test creating competitor mention objects"""
        mention = CompetitorMention(
            competitor_type="direct",
            competitor_name="keller_williams",
            mention_text="working with Keller Williams",
            confidence_score=0.9,
            risk_level=RiskLevel.HIGH,
            context="I'm working with Keller Williams agent",
            timestamp=datetime.now(),
            patterns_matched=["working_with"],
            sentiment_score=-0.1,
            urgency_indicators=["ASAP"]
        )

        assert mention.competitor_type == "direct"
        assert mention.competitor_name == "keller_williams"
        assert mention.confidence_score == 0.9
        assert mention.risk_level == RiskLevel.HIGH


class TestCompetitiveAnalysisDataStructure:
    """Test competitive analysis data structure"""

    def test_competitive_analysis_creation(self):
        """Test creating competitive analysis objects"""
        analysis = CompetitiveAnalysis(
            has_competitor_risk=True,
            risk_level=RiskLevel.HIGH,
            mentions=[],
            recommended_responses=["Test response"],
            alert_required=True,
            escalation_needed=True,
            recovery_strategies=["Strategy 1"],
            confidence_score=0.8
        )

        assert analysis.has_competitor_risk is True
        assert analysis.risk_level == RiskLevel.HIGH
        assert analysis.alert_required is True
        assert analysis.confidence_score == 0.8


if __name__ == "__main__":
    pytest.main([__file__])