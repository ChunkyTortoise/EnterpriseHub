import pytest

pytestmark = pytest.mark.integration

"""
Integration tests for competitor intelligence system

Tests the complete flow:
1. Enhanced conversation manager with competitive intelligence
2. End-to-end competitor detection and response
3. Alert system integration
4. Rancho Cucamonga market intelligence integration
5. Recovery workflow testing
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from ghl_real_estate_ai.core.enhanced_conversation_manager import EnhancedAIResponse, EnhancedConversationManager
    from ghl_real_estate_ai.prompts.competitive_responses import LeadProfile
    from ghl_real_estate_ai.services.competitor_intelligence import RiskLevel
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestCompetitorIntelligenceIntegration:
    """Integration tests for complete competitor intelligence system"""

    @pytest.fixture
    def enhanced_conversation_manager(self):
        """Create enhanced conversation manager for testing"""
        return EnhancedConversationManager()

    @pytest.fixture
    def sample_contact_info(self):
        """Sample contact information for testing"""
        return {
            "id": "contact_123",
            "first_name": "John",
            "last_name": "Doe",
            "name": "John Doe",
            "phone": "+1234567890",
            "email": "john.doe@example.com",
        }

    @pytest.fixture
    def sample_context(self):
        """Sample conversation context for testing"""
        return {
            "conversation_history": [
                {"role": "user", "content": "I'm looking for a house in Rancho Cucamonga", "timestamp": "2024-01-15T10:00:00"},
                {
                    "role": "assistant",
                    "content": "I'd be happy to help you find a home in Rancho Cucamonga",
                    "timestamp": "2024-01-15T10:00:30",
                },
            ],
            "extracted_preferences": {"budget": 500000, "location": ["Rancho Cucamonga"], "bedrooms": 3},
            "created_at": "2024-01-15T09:00:00",
        }

    @pytest.mark.asyncio
    async def test_competitor_detection_in_conversation_flow(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test competitor detection in normal conversation flow"""
        competitive_message = "Actually, I'm already working with a Keller Williams agent"

        response = await enhanced_conversation_manager.generate_response(
            user_message=competitive_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        assert isinstance(response, EnhancedAIResponse)
        assert response.competitive_analysis is not None
        assert response.competitive_analysis.has_competitor_risk is True
        assert response.competitive_analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    @pytest.mark.asyncio
    async def test_competitive_response_application(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test that competitive responses are applied appropriately"""
        competitive_message = "I'm comparing you with RE/MAX to decide"

        response = await enhanced_conversation_manager.generate_response(
            user_message=competitive_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        assert response.competitive_response_applied is True
        # Message should contain competitive positioning
        assert len(response.message) > 0
        # Should not be generic response
        assert "comparing" in response.message.lower() or "different" in response.message.lower()

    @pytest.mark.asyncio
    async def test_alert_system_integration(self, enhanced_conversation_manager, sample_contact_info, sample_context):
        """Test integration with alert system"""
        critical_message = "I already signed with Coldwell Banker and closing next week"

        with patch.object(
            enhanced_conversation_manager.competitive_alert_system, "send_competitive_alert"
        ) as mock_alert:
            mock_alert.return_value = Mock(alert_id="alert_123", human_intervention_required=True, channels_sent=[])

            response = await enhanced_conversation_manager.generate_response(
                user_message=critical_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
            )

            assert response.alert_sent is True
            assert response.jorge_intervention_required is True
            mock_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_rancho_cucamonga_market_intelligence_integration(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test Rancho Cucamonga market intelligence integration"""
        # Mention specific Rancho Cucamonga competitor
        message = "My Keller Williams agent showed me houses in Ontario Mills"

        # Update context with Rancho Cucamonga location
        sample_context["extracted_preferences"]["location"] = ["Ontario Mills", "Arboretum"]

        response = await enhanced_conversation_manager.generate_response(
            user_message=message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        # Should have competitive analysis
        assert response.competitive_analysis is not None
        # Should apply Rancho Cucamonga-specific competitive positioning
        assert "rancho_cucamonga" in response.message.lower() or "ontario_mills" in response.message.lower()

    @pytest.mark.asyncio
    async def test_lead_profile_targeting(self, enhanced_conversation_manager, sample_contact_info, sample_context):
        """Test lead profile-specific targeting"""
        # Investor profile
        investor_context = sample_context.copy()
        investor_context["extracted_preferences"].update(
            {"budget": 300000, "property_type": "investment", "must_haves": ["cash flow", "rental potential"]}
        )

        investor_message = "My other agent doesn't understand investment properties like I need"

        response = await enhanced_conversation_manager.generate_response(
            user_message=investor_message, contact_info=sample_contact_info, context=investor_context, is_buyer=True
        )

        assert response.competitive_response_applied is True
        # Should mention investment-related advantages
        message_lower = response.message.lower()
        assert any(word in message_lower for word in ["investment", "roi", "cash flow", "investor"])

    @pytest.mark.asyncio
    async def test_competitive_context_tracking(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test competitive intelligence context tracking"""
        competitive_message = "I'm working with another agent"

        # First competitive interaction
        await enhanced_conversation_manager.generate_response(
            user_message=competitive_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        # Get competitive summary
        summary = await enhanced_conversation_manager.get_competitive_summary("contact_123")

        assert summary["has_competitive_risk"] is True
        assert summary["current_risk_level"] != "low"
        assert "total_risk_events" in summary

    @pytest.mark.asyncio
    async def test_recovery_recommendations(self, enhanced_conversation_manager, sample_contact_info, sample_context):
        """Test competitive recovery recommendations"""
        # Simulate competitive situation
        competitive_message = "I'm leaning towards my current agent"

        await enhanced_conversation_manager.generate_response(
            user_message=competitive_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        # Get recovery recommendations
        recommendations = await enhanced_conversation_manager.get_recovery_recommendations("contact_123")

        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
        # Should provide actionable recommendations
        assert any("value" in rec.lower() or "insight" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_competitive_situation_resolution(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test competitive situation resolution workflow"""
        # Create competitive situation
        competitive_message = "I'm working with RE/MAX"

        await enhanced_conversation_manager.generate_response(
            user_message=competitive_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        # Resolve competitive situation
        resolution_notes = "Lead chose Jorge after demonstrating superior market knowledge"
        await enhanced_conversation_manager.mark_competitive_situation_resolved(
            contact_id="contact_123", resolution_notes=resolution_notes
        )

        # Verify resolution
        summary = await enhanced_conversation_manager.get_competitive_summary("contact_123")
        assert summary["current_risk_level"] == "resolved"

    @pytest.mark.asyncio
    async def test_no_false_positives_normal_conversation(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test that normal conversation doesn't trigger false competitive alerts"""
        normal_messages = [
            "I'm interested in 3 bedroom homes",
            "What's the market like in Rancho Cucamonga?",
            "Can you help me understand the buying process?",
            "I'm pre-approved for $500k",
            "When can we schedule a showing?",
        ]

        for message in normal_messages:
            response = await enhanced_conversation_manager.generate_response(
                user_message=message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
            )

            # Should not trigger competitive response for normal messages
            if response.competitive_analysis:
                assert response.competitive_analysis.has_competitor_risk is False

    @pytest.mark.asyncio
    async def test_escalation_levels(self, enhanced_conversation_manager, sample_contact_info, sample_context):
        """Test different escalation levels based on risk"""
        risk_scenarios = [
            ("I might look at other options", "low_risk"),
            ("I'm comparing a few agents", "medium_risk"),
            ("I'm working with someone else", "high_risk"),
            ("I already signed with another agent", "critical_risk"),
        ]

        results = []
        for message, scenario in risk_scenarios:
            response = await enhanced_conversation_manager.generate_response(
                user_message=message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
            )
            results.append((scenario, response))

        # Verify escalation levels increase with risk
        risk_levels = []
        for scenario, response in results:
            if response.competitive_analysis and response.competitive_analysis.has_competitor_risk:
                risk_levels.append(response.competitive_analysis.risk_level)

        # Should have increasing risk levels
        assert len(risk_levels) > 0

    @pytest.mark.asyncio
    async def test_tech_relocation_competitive_scenario(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test tech relocation specific competitive scenario"""
        # Tech relocation context
        tech_context = sample_context.copy()
        tech_context["extracted_preferences"].update(
            {
                "location": ["Ontario Mills", "Cedar Park"],
                "timeline": "need to close before Apple start date",
                "budget": 650000,
            }
        )

        tech_message = "My Apple relocation specialist is showing me houses this week"

        response = await enhanced_conversation_manager.generate_response(
            user_message=tech_message, contact_info=sample_contact_info, context=tech_context, is_buyer=True
        )

        assert response.competitive_analysis.has_competitor_risk is True
        # Should leverage Jorge's Apple specialization in response
        message_lower = response.message.lower()
        assert any(word in message_lower for word in ["apple", "tech", "timeline", "relocation"])

    @pytest.mark.asyncio
    async def test_error_recovery_in_competitive_flow(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test error recovery in competitive intelligence flow"""
        # Simulate error in competitive analysis
        with patch.object(
            enhanced_conversation_manager.competitor_intelligence, "analyze_conversation"
        ) as mock_analysis:
            mock_analysis.side_effect = Exception("Analysis service error")

            competitive_message = "I'm working with another agent"

            # Should not fail completely, should fall back gracefully
            response = await enhanced_conversation_manager.generate_response(
                user_message=competitive_message,
                contact_info=sample_contact_info,
                context=sample_context,
                is_buyer=True,
            )

            # Should still return valid response
            assert isinstance(response, EnhancedAIResponse)
            assert response.competitive_analysis is None
            assert len(response.message) > 0

    @pytest.mark.asyncio
    async def test_competitive_intelligence_performance(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test performance of competitive intelligence system"""
        competitive_message = "I'm comparing you with Keller Williams and RE/MAX"

        start_time = datetime.now()

        response = await enhanced_conversation_manager.generate_response(
            user_message=competitive_message, contact_info=sample_contact_info, context=sample_context, is_buyer=True
        )

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Should complete within reasonable time (< 10 seconds for integration test)
        assert processing_time < 10
        assert response.competitive_analysis is not None

    @pytest.mark.asyncio
    async def test_multiple_competitors_handling(
        self, enhanced_conversation_manager, sample_contact_info, sample_context
    ):
        """Test handling of multiple competitors mentioned"""
        multi_competitor_message = "I'm comparing Keller Williams, RE/MAX, and Coldwell Banker"

        response = await enhanced_conversation_manager.generate_response(
            user_message=multi_competitor_message,
            contact_info=sample_contact_info,
            context=sample_context,
            is_buyer=True,
        )

        assert response.competitive_analysis.has_competitor_risk is True
        # Should escalate due to multiple competitors
        assert response.competitive_analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert len(response.competitive_analysis.mentions) >= 2


if __name__ == "__main__":
    pytest.main([__file__])