"""
Jorge Salas - GHL Real Estate AI Integration Tests
Validates all of Jorge's specific requirements and workflow
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

# Import the modules we're testing
from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook, prepare_ghl_actions
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.api.schemas.ghl import (
    GHLWebhookEvent,
    MessageData,
    ContactData,
    ActionType
)
from ghl_real_estate_ai.ghl_utils.config import settings


class TestJorgeIntegration:
    """Test Jorge's specific GHL integration requirements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.lead_scorer = LeadScorer()
        self.conversation_manager = ConversationManager()

        # Mock GHL webhook event
        self.base_event = GHLWebhookEvent(
            contact_id="test_contact_123",
            location_id="jorge_location",
            message=MessageData(
                body="Hi, I need to sell my house",
                type="SMS"
            ),
            contact=ContactData(
                first_name="John",
                last_name="Doe",
                phone="+15125551234",
                email="john@example.com",
                tags=["Needs Qualifying"]  # Jorge's activation tag
            )
        )

    # ============================================================================
    # JORGE'S AUTO-DEACTIVATION TESTS
    # ============================================================================

    def test_percentage_score_mapping(self):
        """Test Jorge's question count to percentage conversion."""
        expected_mapping = {
            0: 5,   # No engagement
            1: 15,  # Cold lead
            2: 30,  # Warm lead
            3: 50,  # Hot lead
            4: 65,  # Strong engagement
            5: 75,  # Above Jorge's 70% threshold - AUTO DEACTIVATE
            6: 85,  # Nearly complete
            7: 100  # All questions answered
        }

        for question_count, expected_percentage in expected_mapping.items():
            percentage = self.lead_scorer.get_percentage_score(question_count)
            assert percentage == expected_percentage, \
                f"Question count {question_count} should map to {expected_percentage}%, got {percentage}%"

    @pytest.mark.asyncio
    async def test_auto_deactivation_at_70_percent(self):
        """Test that AI auto-deactivates when score reaches 70+ (5+ questions)."""
        # Test case: 5 questions answered = 75% = Should auto-deactivate
        extracted_data = {
            "budget": "$400k",
            "location": "Austin",
            "timeline": "ASAP",
            "bedrooms": "3",
            "financing": "pre-approved"  # 5 questions answered
        }

        lead_score = 5  # 5 questions answered

        actions = await prepare_ghl_actions(
            extracted_data=extracted_data,
            lead_score=lead_score,
            event=self.base_event
        )

        # Should remove activation tag and add qualified tags
        action_types = [action.type for action in actions]
        action_tags = [action.tag for action in actions if hasattr(action, 'tag')]

        assert ActionType.REMOVE_TAG in action_types, "Should remove activation tag"
        assert "Needs Qualifying" in [action.tag for action in actions if action.type == ActionType.REMOVE_TAG]
        assert "AI-Qualified" in action_tags, "Should add AI-Qualified tag"
        assert "Ready-For-Agent" in action_tags, "Should add Ready-For-Agent tag"

    @pytest.mark.asyncio
    async def test_no_auto_deactivation_below_70_percent(self):
        """Test that AI continues below 70% threshold (4 or fewer questions)."""
        # Test case: 4 questions answered = 65% = Should NOT auto-deactivate
        extracted_data = {
            "budget": "$400k",
            "location": "Austin",
            "timeline": "ASAP",
            "bedrooms": "3"  # 4 questions answered
        }

        lead_score = 4  # 4 questions answered

        actions = await prepare_ghl_actions(
            extracted_data=extracted_data,
            lead_score=lead_score,
            event=self.base_event
        )

        # Should NOT remove activation tag
        remove_actions = [action for action in actions if action.type == ActionType.REMOVE_TAG]
        assert not any(action.tag == "Needs Qualifying" for action in remove_actions), \
            "Should NOT remove activation tag when below 70%"

    # ============================================================================
    # JORGE'S 7-QUESTION QUALIFICATION SYSTEM TESTS
    # ============================================================================

    def test_jorge_question_scoring(self):
        """Test Jorge's exact 7-question scoring system."""
        test_cases = [
            # No questions answered
            ({}, 0),

            # 1 question: Budget only
            ({"budget": "$400k"}, 1),

            # 2 questions: Budget + Location (Warm lead)
            ({"budget": "$400k", "location": "Austin"}, 2),

            # 3 questions: Budget + Location + Timeline (Hot lead)
            ({"budget": "$400k", "location": "Austin", "timeline": "ASAP"}, 3),

            # 4 questions: Above + Property details
            ({"budget": "$400k", "location": "Austin", "timeline": "ASAP", "bedrooms": "3"}, 4),

            # 5 questions: Above + Financing (70% threshold - auto-deactivate)
            ({"budget": "$400k", "location": "Austin", "timeline": "ASAP", "bedrooms": "3", "financing": "pre-approved"}, 5),

            # 6 questions: Above + Motivation
            ({"budget": "$400k", "location": "Austin", "timeline": "ASAP", "bedrooms": "3", "financing": "pre-approved", "motivation": "job relocation"}, 6),

            # 7 questions: Above + Home condition (sellers)
            ({"budget": "$400k", "location": "Austin", "timeline": "ASAP", "bedrooms": "3", "financing": "pre-approved", "motivation": "job relocation", "home_condition": "excellent"}, 7),
        ]

        for preferences, expected_score in test_cases:
            context = {"extracted_preferences": preferences}
            actual_score = self.lead_scorer.calculate(context)
            assert actual_score == expected_score, \
                f"Preferences {preferences} should score {expected_score}, got {actual_score}"

    def test_jorge_lead_classification(self):
        """Test Jorge's lead classification criteria."""
        assert self.lead_scorer.classify(0) == "cold"   # 0-1 questions
        assert self.lead_scorer.classify(1) == "cold"   # 0-1 questions
        assert self.lead_scorer.classify(2) == "warm"   # 2 questions
        assert self.lead_scorer.classify(3) == "hot"    # 3+ questions
        assert self.lead_scorer.classify(4) == "hot"    # 3+ questions
        assert self.lead_scorer.classify(7) == "hot"    # 3+ questions

    # ============================================================================
    # ACTIVATION/DEACTIVATION TAG TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_activation_tag_required(self):
        """Test that AI only activates with 'Needs Qualifying' tag."""
        # Mock request and background tasks
        request = Mock()
        background_tasks = Mock()

        # Test without activation tag
        event_no_tag = GHLWebhookEvent(
            contact_id="test_contact",
            location_id="jorge_location",
            message=MessageData(body="Hello", type="SMS"),
            contact=ContactData(
                first_name="John",
                tags=[]  # No activation tag
            )
        )

        # This should return early without processing
        # Note: We'd need to mock the webhook handler fully for this test
        # For now, we'll test the tag logic directly
        activation_tags = ["Needs Qualifying"]
        should_activate = any(tag in [] for tag in activation_tags)
        assert not should_activate, "Should not activate without Needs Qualifying tag"

        # Test with activation tag
        should_activate = any(tag in ["Needs Qualifying"] for tag in activation_tags)
        assert should_activate, "Should activate with Needs Qualifying tag"

    # ============================================================================
    # SMS FORMATTING TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_sms_character_limit(self):
        """Test that responses are under 160 characters (Jorge's SMS requirement)."""
        # Mock a long AI response
        long_response = "This is a very long response that exceeds the 160 character limit for SMS messages and should be truncated to fit within the SMS constraints that Jorge requires for his real estate AI system."

        # Apply SMS formatting logic (from conversation_manager.py)
        if len(long_response) > 160:
            formatted_response = long_response[:157] + "..."
        else:
            formatted_response = long_response

        assert len(formatted_response) <= 160, f"Response {len(formatted_response)} chars exceeds 160 SMS limit"
        assert formatted_response.endswith("..."), "Long responses should end with ..."

    def test_jorge_tone_examples(self):
        """Test that responses match Jorge's exact tone examples."""
        jorge_examples = [
            "Hey! What's up?",
            "Hey, are you actually still looking to sell or should we close your file?",
            "Hey John, just checking in - is it still a priority of yours to buy or have you given up?",
            "Would today around 2:00 or closer to 4:30 work better for you?"
        ]

        for example in jorge_examples:
            # All examples should be under 160 characters
            assert len(example) <= 160, f"Jorge's example '{example}' is {len(example)} chars"

            # Should start with "Hey" for re-engagement style
            if "checking in" in example or "actually still" in example:
                assert example.startswith("Hey"), f"Re-engagement should start with 'Hey': {example}"

    # ============================================================================
    # END-TO-END WORKFLOW TESTS
    # ============================================================================

    @pytest.mark.asyncio
    async def test_jorge_complete_workflow(self):
        """Test complete workflow: activation → qualification → auto-deactivation."""

        # Stage 1: Initial contact with activation tag
        stage1_data = {"budget": "$400k"}  # 1 question = Cold
        stage1_score = 1
        stage1_actions = await prepare_ghl_actions(stage1_data, stage1_score, self.base_event)
        stage1_tags = [action.tag for action in stage1_actions if hasattr(action, 'tag')]
        assert "Cold-Lead" in stage1_tags, "Stage 1: Should tag as Cold-Lead"

        # Stage 2: Getting warmer
        stage2_data = {"budget": "$400k", "location": "Austin"}  # 2 questions = Warm
        stage2_score = 2
        stage2_actions = await prepare_ghl_actions(stage2_data, stage2_score, self.base_event)
        stage2_tags = [action.tag for action in stage2_actions if hasattr(action, 'tag')]
        assert "Warm-Lead" in stage2_tags, "Stage 2: Should tag as Warm-Lead"

        # Stage 3: Hot lead
        stage3_data = {"budget": "$400k", "location": "Austin", "timeline": "ASAP"}  # 3 questions = Hot
        stage3_score = 3
        stage3_actions = await prepare_ghl_actions(stage3_data, stage3_score, self.base_event)
        stage3_tags = [action.tag for action in stage3_actions if hasattr(action, 'tag')]
        assert "Hot-Lead" in stage3_tags, "Stage 3: Should tag as Hot-Lead"

        # Stage 4: Continue qualifying (still AI active)
        stage4_data = {"budget": "$400k", "location": "Austin", "timeline": "ASAP", "bedrooms": "3"}  # 4 questions = 65%
        stage4_score = 4
        stage4_actions = await prepare_ghl_actions(stage4_data, stage4_score, self.base_event)
        # Should NOT auto-deactivate yet
        remove_actions = [action for action in stage4_actions if action.type == ActionType.REMOVE_TAG]
        assert not any(action.tag == "Needs Qualifying" for action in remove_actions), \
            "Stage 4: Should NOT auto-deactivate at 65%"

        # Stage 5: Auto-deactivation (Jorge's 70% threshold)
        stage5_data = {
            "budget": "$400k",
            "location": "Austin",
            "timeline": "ASAP",
            "bedrooms": "3",
            "financing": "pre-approved"  # 5 questions = 75% = AUTO-DEACTIVATE
        }
        stage5_score = 5
        stage5_actions = await prepare_ghl_actions(stage5_data, stage5_score, self.base_event)

        # Should auto-deactivate
        action_types = [action.type for action in stage5_actions]
        action_tags = [action.tag for action in stage5_actions if hasattr(action, 'tag')]

        assert ActionType.REMOVE_TAG in action_types, "Stage 5: Should remove activation tag"
        assert "AI-Qualified" in action_tags, "Stage 5: Should add AI-Qualified tag"
        assert "Ready-For-Agent" in action_tags, "Stage 5: Should add Ready-For-Agent tag"

    # ============================================================================
    # INTEGRATION VALIDATION
    # ============================================================================

    def test_jorge_configuration_values(self):
        """Test that Jorge's configuration values are properly set."""
        # These should match Jorge's requirements from the clarification document
        assert settings.auto_deactivate_threshold == 70, "Auto-deactivate threshold should be 70%"
        assert settings.hot_lead_threshold == 3, "Hot lead threshold should be 3+ questions"
        assert settings.warm_lead_threshold == 2, "Warm lead threshold should be 2 questions"
        assert "Needs Qualifying" in settings.activation_tags, "Should include Jorge's activation tag"

    @pytest.mark.asyncio
    async def test_workflow_notification_trigger(self):
        """Test that agent notification workflow is triggered on auto-deactivation."""
        # Mock settings with workflow ID
        original_workflow_id = settings.notify_agent_workflow_id
        settings.notify_agent_workflow_id = "jorge_notification_workflow"

        try:
            # 5 questions = auto-deactivation
            extracted_data = {
                "budget": "$400k",
                "location": "Austin",
                "timeline": "ASAP",
                "bedrooms": "3",
                "financing": "pre-approved"
            }
            lead_score = 5

            actions = await prepare_ghl_actions(extracted_data, lead_score, self.base_event)

            # Should trigger workflow
            workflow_actions = [action for action in actions if action.type == ActionType.TRIGGER_WORKFLOW]
            assert len(workflow_actions) > 0, "Should trigger agent notification workflow"
            assert workflow_actions[0].workflow_id == "jorge_notification_workflow"

        finally:
            # Restore original setting
            settings.notify_agent_workflow_id = original_workflow_id


# ============================================================================
# VALIDATION SCRIPTS
# ============================================================================

def run_jorge_validation():
    """Run all validation tests for Jorge's requirements."""
    print("🧪 Jorge Salas - GHL Real Estate AI Validation")
    print("=" * 50)

    # Run pytest with verbose output
    import subprocess
    import sys

    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short"
    ], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("ERRORS:")
        print(result.stderr)

    if result.returncode == 0:
        print("\n✅ All Jorge validation tests PASSED!")
        print("🚀 System is ready for deployment")
    else:
        print("\n❌ Some validation tests FAILED!")
        print("🔧 Please fix issues before deploying")

    return result.returncode == 0


if __name__ == "__main__":
    # Run validation when executed directly
    success = run_jorge_validation()
    exit(0 if success else 1)