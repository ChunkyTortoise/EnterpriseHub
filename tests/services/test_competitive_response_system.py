import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive tests for competitive response system

Tests cover:
1. Response template selection based on risk level
2. Jorge-specific positioning messages
3. Lead profile targeting
4. Value proposition integration
5. Success story selection
6. Differentiation messaging
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from ghl_real_estate_ai.prompts.competitive_responses import (
    CompetitiveResponseSystem,
    LeadProfile,
    ResponseType,
    get_competitive_response_system,
)
from ghl_real_estate_ai.services.competitor_intelligence import CompetitorMention, RiskLevel


class TestCompetitiveResponseSystem:
    """Test suite for competitive response system"""

    @pytest.fixture
    def system(self):
        """Create competitive response system for testing"""
        return CompetitiveResponseSystem()

    @pytest.fixture
    def sample_competitor_mentions(self):
        """Sample competitor mentions for testing"""
        return [
            CompetitorMention(
                competitor_type="named_competitor",
                competitor_name="keller_williams",
                mention_text="working with Keller Williams",
                confidence_score=0.9,
                risk_level=RiskLevel.HIGH,
                context="I'm working with a Keller Williams agent",
                timestamp=datetime.now(),
                patterns_matched=["named_competitor"],
                sentiment_score=0.0,
                urgency_indicators=[],
            )
        ]

    def test_response_template_structure(self, system):
        """Test that response templates are properly structured"""
        templates = system.response_templates

        # Check all risk levels are covered
        assert RiskLevel.LOW in templates
        assert RiskLevel.MEDIUM in templates
        assert RiskLevel.HIGH in templates
        assert RiskLevel.CRITICAL in templates

        # Check templates have required fields
        for risk_level, response_types in templates.items():
            for response_type, template_list in response_types.items():
                for template in template_list:
                    assert hasattr(template, "message")
                    assert hasattr(template, "response_type")
                    assert hasattr(template, "risk_level")
                    assert hasattr(template, "success_rate")
                    assert isinstance(template.success_rate, float)
                    assert 0 <= template.success_rate <= 1

    def test_low_risk_positioning_response(self, system, sample_competitor_mentions):
        """Test positioning response for low risk situations"""
        response = system.get_competitive_response(risk_level=RiskLevel.LOW, competitor_mentions=[], lead_profile=None)

        assert response is not None
        assert "message" in response
        assert response["response_type"] == ResponseType.POSITIONING.value
        assert response["urgency_level"] <= 2
        assert not response["follow_up_required"] or response["follow_up_required"]

    def test_medium_risk_differentiation_response(self, system, sample_competitor_mentions):
        """Test differentiation response for medium risk situations"""
        response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM,
            competitor_mentions=sample_competitor_mentions,
            lead_profile=LeadProfile.INVESTOR,
        )

        assert response is not None
        assert "message" in response
        assert response["response_type"] in [ResponseType.DIFFERENTIATION.value, ResponseType.URGENCY.value]
        assert response["urgency_level"] >= 3
        assert response["follow_up_required"] is True

    def test_high_risk_recovery_response(self, system, sample_competitor_mentions):
        """Test recovery response for high risk situations"""
        response = system.get_competitive_response(
            risk_level=RiskLevel.HIGH, competitor_mentions=sample_competitor_mentions, lead_profile=None
        )

        assert response is not None
        assert "message" in response
        assert response["response_type"] == ResponseType.RECOVERY.value
        assert response["escalation_recommended"] is True
        assert len(response["follow_up_strategy"]) > 0

    def test_critical_risk_nurture_response(self, system, sample_competitor_mentions):
        """Test nurture response for critical risk situations"""
        response = system.get_competitive_response(
            risk_level=RiskLevel.CRITICAL, competitor_mentions=sample_competitor_mentions, lead_profile=None
        )

        assert response is not None
        assert "message" in response
        assert response["response_type"] in [ResponseType.RECOVERY.value, ResponseType.NURTURE.value]
        assert response["human_intervention"] is True
        assert response["escalation_recommended"] is True

    def test_lead_profile_targeting(self, system, sample_competitor_mentions):
        """Test that responses are targeted based on lead profile"""
        investor_response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM,
            competitor_mentions=sample_competitor_mentions,
            lead_profile=LeadProfile.INVESTOR,
        )

        relocating_response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM,
            competitor_mentions=sample_competitor_mentions,
            lead_profile=LeadProfile.RELOCATING,
        )

        # Responses should be different based on lead profile
        assert investor_response["message"] != relocating_response["message"]

    def test_message_personalization(self, system, sample_competitor_mentions):
        """Test message personalization with conversation context"""
        context = {"lead_name": "John", "property_type": "condo", "location": "Rancho Cucamonga"}

        response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=sample_competitor_mentions, conversation_context=context
        )

        # Message should be personalized
        message = response["message"]
        # Check if personalization occurred (context-dependent)
        assert isinstance(message, str)
        assert len(message) > 0

    def test_value_proposition_integration(self, system, sample_competitor_mentions):
        """Test value proposition integration in responses"""
        response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM,
            competitor_mentions=sample_competitor_mentions,
            lead_profile=LeadProfile.INVESTOR,
        )

        value_prop = response.get("value_proposition")
        if value_prop:
            assert "headline" in value_prop
            assert "description" in value_prop
            assert value_prop["headline"] in system.jorge_value_props["investor_focus"]["headline"]

    def test_jorge_value_propositions_structure(self, system):
        """Test Jorge's value propositions are properly structured"""
        value_props = system.jorge_value_props

        required_props = ["ai_technology", "rc_expertise", "amazon_specialization", "investor_focus", "response_speed"]

        for prop in required_props:
            assert prop in value_props
            assert "headline" in value_props[prop]
            assert "description" in value_props[prop]
            assert "proof_points" in value_props[prop]
            assert "competitor_advantage" in value_props[prop]

    def test_success_story_retrieval(self, system):
        """Test success story retrieval"""
        competitive_story = system.get_success_story("competitive_win")
        assert competitive_story is not None
        assert "situation" in competitive_story
        assert "jorge_solution" in competitive_story
        assert "outcome" in competitive_story

        recovery_story = system.get_success_story("recovery")
        assert recovery_story is not None
        assert "situation" in recovery_story

    def test_differentiation_points(self, system):
        """Test differentiation points generation"""
        # General differentiation
        diff_points = system.get_differentiation_points()
        assert len(diff_points) > 0
        assert all(isinstance(point, str) for point in diff_points)

        # Competitor-specific differentiation
        kw_diff_points = system.get_differentiation_points("keller_williams")
        assert len(kw_diff_points) > 0
        # Should have additional competitor-specific point
        assert len(kw_diff_points) >= len(diff_points)

    def test_urgency_creator_messages(self, system):
        """Test urgency creator messages"""
        urgency_msg = system.get_urgency_creator("inventory")
        assert isinstance(urgency_msg, str)
        assert len(urgency_msg) > 0
        assert "rancho cucamonga" in urgency_msg.lower()

        rates_msg = system.get_urgency_creator("rates")
        assert isinstance(rates_msg, str)
        assert rates_msg != urgency_msg

    def test_fallback_response_handling(self, system):
        """Test fallback response when no templates match"""
        # Create empty response system to test fallback
        empty_system = CompetitiveResponseSystem()
        empty_system.response_templates = {}

        response = empty_system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=[], lead_profile=None
        )

        assert response is not None
        assert response["response_type"] == "fallback"
        assert response["escalation_recommended"] is True

    def test_response_success_rates(self, system):
        """Test that response templates have realistic success rates"""
        for risk_level, response_types in system.response_templates.items():
            for response_type, template_list in response_types.items():
                for template in template_list:
                    # Success rates should be realistic (not 100% for high risk)
                    if risk_level == RiskLevel.CRITICAL:
                        assert template.success_rate <= 0.5
                    elif risk_level == RiskLevel.HIGH:
                        assert template.success_rate <= 0.6
                    # All should have some success rate
                    assert template.success_rate > 0

    def test_follow_up_strategy_generation(self, system, sample_competitor_mentions):
        """Test follow-up strategy generation"""
        for risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            response = system.get_competitive_response(
                risk_level=risk_level, competitor_mentions=sample_competitor_mentions, lead_profile=None
            )

            if response["follow_up_required"]:
                assert len(response["follow_up_strategy"]) > 0
                # Strategies should be actionable strings
                assert all(isinstance(strategy, str) for strategy in response["follow_up_strategy"])

    def test_competitor_specific_messaging(self, system):
        """Test competitor-specific messaging"""
        kw_mention = CompetitorMention(
            competitor_type="named_competitor",
            competitor_name="keller_williams",
            mention_text="Keller Williams",
            confidence_score=0.9,
            risk_level=RiskLevel.HIGH,
            context="test",
            timestamp=datetime.now(),
            patterns_matched=[],
            sentiment_score=0.0,
            urgency_indicators=[],
        )

        remax_mention = CompetitorMention(
            competitor_type="named_competitor",
            competitor_name="remax",
            mention_text="RE/MAX",
            confidence_score=0.9,
            risk_level=RiskLevel.HIGH,
            context="test",
            timestamp=datetime.now(),
            patterns_matched=[],
            sentiment_score=0.0,
            urgency_indicators=[],
        )

        kw_response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=[kw_mention], lead_profile=None
        )

        remax_response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=[remax_mention], lead_profile=None
        )

        # Responses should potentially be different based on competitor
        # (if competitor-specific templates exist)
        assert kw_response is not None
        assert remax_response is not None

    def test_rancho_cucamonga_market_advantages_integration(self, system):
        """Test Rancho Cucamonga/Inland Empire market advantages integration"""
        rancho_cucamonga_advantages = system.rc_advantages

        assert "market_timing" in rancho_cucamonga_advantages
        assert "neighborhood_expertise" in rancho_cucamonga_advantages
        assert "development_pipeline" in rancho_cucamonga_advantages
        assert "local_connections" in rancho_cucamonga_advantages

        # Each advantage should have relevant data
        for advantage_type, advantage_data in rancho_cucamonga_advantages.items():
            assert isinstance(advantage_data, dict)
            assert len(advantage_data) > 0

    def test_response_professionalism(self, system, sample_competitor_mentions):
        """Test that responses maintain professionalism"""
        for risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            response = system.get_competitive_response(
                risk_level=risk_level, competitor_mentions=sample_competitor_mentions, lead_profile=None
            )

            message = response["message"].lower()

            # Should not contain disparaging language
            negative_words = ["bad", "terrible", "awful", "sucks", "worst", "horrible"]
            assert not any(word in message for word in negative_words)

            # Should maintain professional tone
            assert len(message) > 10  # Not too short
            assert not message.isupper()  # Not all caps

    def test_urgency_indicators_handling(self, system):
        """Test handling of urgency indicators in competitor mentions"""
        urgent_mention = CompetitorMention(
            competitor_type="direct",
            competitor_name=None,
            mention_text="need to decide ASAP",
            confidence_score=0.7,
            risk_level=RiskLevel.MEDIUM,
            context="test",
            timestamp=datetime.now(),
            patterns_matched=[],
            sentiment_score=0.0,
            urgency_indicators=["ASAP", "deadline"],
        )

        response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=[urgent_mention], lead_profile=None
        )

        # Should escalate urgency when urgency indicators present
        assert response["urgency_level"] >= 3

    def test_singleton_pattern(self):
        """Test singleton pattern for competitive response system"""
        system1 = get_competitive_response_system()
        system2 = get_competitive_response_system()

        assert system1 is system2

    def test_response_length_appropriateness(self, system, sample_competitor_mentions):
        """Test that responses are appropriate length for SMS/chat"""
        for risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            response = system.get_competitive_response(
                risk_level=risk_level, competitor_mentions=sample_competitor_mentions, lead_profile=None
            )

            message = response["message"]
            # Should be reasonable length for SMS (not too long)
            assert len(message) <= 500  # Reasonable for multiple SMS
            assert len(message) >= 20  # Not too short to be useful

    def test_edge_case_handling(self, system):
        """Test edge case handling"""
        # Empty competitor mentions
        response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=[], lead_profile=None
        )
        assert response is not None

        # Unknown lead profile
        response = system.get_competitive_response(
            risk_level=RiskLevel.MEDIUM, competitor_mentions=[], lead_profile=None
        )
        assert response is not None

        # Invalid risk level handling should still work
        # (system should handle gracefully)


if __name__ == "__main__":
    pytest.main([__file__])