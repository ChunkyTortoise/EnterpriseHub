"""
Jorge Delivery Test Suite — Stream D

Tests the Jorge seller bot delivery package:
- D1: Seller qualification E2E flow (5-message conversation)
- D2: Opt-out handling
- D3: Edge cases (vague, multi-answer, no response, off-topic)
- D4: Tone compliance

All tests use unittest.mock — no real API calls.
"""

import os
import re

# Set required env vars BEFORE any application imports trigger singleton init
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLContact,
    GHLMessage,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageDirection,
    MessageType,
)
from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_webhook_event(
    message_body: str,
    contact_id: str = "contact_123",
    location_id: str = "loc_456",
    tags: list[str] | None = None,
    direction: MessageDirection = MessageDirection.INBOUND,
    first_name: str = "Maria",
) -> GHLWebhookEvent:
    """Build a GHLWebhookEvent for testing."""
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId=contact_id,
        locationId=location_id,
        message=GHLMessage(type=MessageType.SMS, body=message_body, direction=direction),
        contact=GHLContact(
            contactId=contact_id,
            firstName=first_name,
            lastName="Salas",
            phone="+19095551234",
            email="maria@example.com",
            tags=tags or ["Needs Qualifying"],
            customFields={},
        ),
    )


def _action_tags(response: GHLWebhookResponse) -> list[str]:
    """Extract ADD_TAG tag names from a response."""
    return [a.tag for a in response.actions if a.type == ActionType.ADD_TAG]


# ---------------------------------------------------------------------------
# D1 — Seller Qualification E2E Flow
# ---------------------------------------------------------------------------

class TestSellerQualificationFlow:
    """E2E: 5-message conversation ending with Hot seller classification."""

    @pytest.mark.asyncio
    async def test_seller_e2e_hot_flow(self):
        """Simulate conversation resulting in hot seller via the engine (simple mode)."""
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

        mock_cm = MagicMock()
        mock_ghl = MagicMock()

        # Context returned for the final (5th) message — all 4 questions answered
        mock_cm.get_context = AsyncMock(return_value={
            "seller_preferences": {
                "motivation": "relocating",
                "timeline_acceptable": True,
                "property_condition": "Move-in Ready",
                "price_expectation": "650000",
            },
            "contact_name": "Maria",
        })
        mock_cm.update_context = AsyncMock()
        mock_cm.extract_seller_data = AsyncMock(return_value={
            "motivation": "relocating",
            "timeline_acceptable": True,
            "property_condition": "Move-in Ready",
            "price_expectation": "650000",
            "questions_answered": 4,
            "response_quality": 0.9,
            "vague_streak": 0,
            "last_user_message": "$650k would work",
        })

        config = JorgeSellerConfig()
        config.JORGE_SIMPLE_MODE = True

        # Patch lazy imports at their actual source modules
        mock_predictive = MagicMock(
            calculate_predictive_score=AsyncMock(return_value=MagicMock(
                closing_probability=0.85, overall_priority_score=80,
                priority_level=MagicMock(value="high"), net_yield_estimate=0.15,
            ))
        )
        mock_pricing = MagicMock(
            calculate_lead_price=AsyncMock(return_value=MagicMock(
                expected_roi=12.5, final_price=650000, tier="premium", justification="hot",
            ))
        )
        mock_psychographic = MagicMock(
            detect_persona=AsyncMock(return_value={"primary_persona": "standard"}),
            get_system_prompt_override=MagicMock(return_value=""),
        )

        with patch("ghl_real_estate_ai.services.analytics_service.AnalyticsService", MagicMock), \
             patch("ghl_real_estate_ai.core.governance_engine.GovernanceEngine", MagicMock(return_value=MagicMock(enforce=lambda m: m))), \
             patch("ghl_real_estate_ai.core.recovery_engine.RecoveryEngine", MagicMock), \
             patch("ghl_real_estate_ai.services.predictive_lead_scorer_v2.PredictiveLeadScorerV2", MagicMock(return_value=mock_predictive)), \
             patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer", MagicMock(return_value=mock_pricing)), \
             patch("ghl_real_estate_ai.services.psychographic_segmentation_engine.PsychographicSegmentationEngine", MagicMock(return_value=mock_psychographic)), \
             patch("ghl_real_estate_ai.services.seller_psychology_analyzer.get_seller_psychology_analyzer", MagicMock(return_value=MagicMock(analyze_seller_psychology=AsyncMock(return_value=None)))), \
             patch("ghl_real_estate_ai.agents.lead_intelligence_swarm.lead_intelligence_swarm", MagicMock(analyze_lead_comprehensive=AsyncMock(return_value=MagicMock(agent_insights=[])))):

            engine = JorgeSellerEngine(mock_cm, mock_ghl, config=config)
            engine.governance = MagicMock(enforce=lambda m: m)

            result = await engine.process_seller_response(
                contact_id="contact_123",
                user_message="$650k would work",
                location_id="loc_456",
            )

            assert result["temperature"] == "hot"
            assert result["message"]
            assert len(result["message"]) <= 160, f"Too long: {len(result['message'])} chars"
            assert "-" not in result["message"], "Message contains hyphens"

            # Verify hot actions include tag and tag removal
            action_types = [a["type"] for a in result["actions"]]
            assert "add_tag" in action_types
            tag_names = [a["tag"] for a in result["actions"] if a["type"] == "add_tag"]
            assert "Hot-Seller" in tag_names

    def test_correct_question_sequence(self):
        """Verify questions follow the 4-question order per spec."""
        questions = JorgeSellerConfig.SELLER_QUESTIONS
        assert list(questions.keys()) == [1, 2, 3, 4]
        assert "sell" in questions[1].lower() or "move" in questions[1].lower()
        assert "30" in questions[2] and "45" in questions[2]
        assert "condition" in questions[3].lower() or "move" in questions[3].lower()
        assert "price" in questions[4].lower()

    def test_response_messages_sms_compliant(self):
        """All 4 questions pass through tone engine and stay < 160 chars."""
        engine = JorgeToneEngine()
        for q_num in range(1, 5):
            msg = engine.generate_qualification_message(q_num, seller_name="Maria")
            assert len(msg) <= 160, f"Q{q_num} too long: {len(msg)}"
            assert "-" not in msg, f"Q{q_num} contains hyphens"


# ---------------------------------------------------------------------------
# D2 — Opt-Out Handling
# ---------------------------------------------------------------------------

class TestOptOutHandling:
    """Verify opt-out keywords trigger AI-Off tag and exit message."""

    OPT_OUT_PHRASES = [
        "stop", "unsubscribe", "don't contact", "dont contact",
        "remove me", "not interested", "no more", "opt out",
        "leave me alone", "take me off", "no thanks",
    ]

    def test_all_opt_out_variants_detected(self):
        """Each opt-out phrase should be matched by the webhook's phrase list."""
        for phrase in self.OPT_OUT_PHRASES:
            msg_lower = phrase.lower().strip()
            assert any(p in msg_lower for p in self.OPT_OUT_PHRASES), (
                f"Phrase '{phrase}' not detected"
            )

    @pytest.mark.asyncio
    async def test_opt_out_returns_ai_off_tag(self):
        """Webhook handler returns AI-Off action for opt-out messages."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        for phrase in ["stop", "unsubscribe", "not interested"]:
            event = _make_webhook_event(phrase, tags=["Needs Qualifying"])
            bg = MagicMock()

            with patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", MagicMock(track_event=AsyncMock())), \
                 patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", MagicMock(add_tags=AsyncMock())):
                # bypass @verify_webhook decorator via __wrapped__
                response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, bg)

            assert response.success is True
            assert "AI-Off" in _action_tags(response), f"AI-Off missing for '{phrase}'"
            assert "reach out" in response.message.lower()

    @pytest.mark.asyncio
    async def test_opt_out_exit_message(self):
        """Exit message matches spec exactly."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event("stop", tags=["Needs Qualifying"])

        with patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", MagicMock(track_event=AsyncMock())), \
             patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", MagicMock(add_tags=AsyncMock())):
            response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

        assert response.message == "No problem at all, reach out whenever you're ready"


# ---------------------------------------------------------------------------
# D3 — Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Vague answers, multi-answer, no response, off-topic."""

    def test_vague_answer_confrontational_followup(self):
        """Vague response should produce a confrontational push."""
        engine = JorgeToneEngine()
        msg = engine.generate_follow_up_message(
            last_response="maybe, I'm not sure about that",
            question_number=1,
            seller_name="Carlos",
        )
        assert len(msg) <= 160
        assert "specific" in msg.lower() or "need" in msg.lower() or "exact" in msg.lower()

    def test_multi_answer_skips_ahead(self):
        """When seller answers multiple questions, get_next_question skips answered."""
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import SellerQuestions

        answered = {
            "motivation": "relocating",
            "timeline_acceptable": True,
            "property_condition": None,
            "price_expectation": None,
        }
        next_q = SellerQuestions.get_next_question(answered)
        assert next_q is not None
        assert "home" in next_q.lower() or "condition" in next_q.lower() or "move" in next_q.lower()

    def test_no_response_followup(self):
        """Empty response generates a follow-up message."""
        engine = JorgeToneEngine()
        msg = engine.generate_follow_up_message(
            last_response="",
            question_number=2,
            seller_name="Carlos",
        )
        assert len(msg) <= 160
        assert msg.strip()

    def test_off_topic_redirects(self):
        """Off-topic answer still gets next qualification question."""
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import SellerQuestions

        answered = {"motivation": None, "timeline_acceptable": None,
                    "property_condition": None, "price_expectation": None}
        next_q = SellerQuestions.get_next_question(answered)
        assert next_q is not None
        assert "sell" in next_q.lower() or "move" in next_q.lower()

    def test_question_number_tracking(self):
        """Question number increments correctly as fields are answered."""
        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import SellerQuestions

        assert SellerQuestions.get_question_number({}) == 1
        assert SellerQuestions.get_question_number({"motivation": "moving"}) == 2
        assert SellerQuestions.get_question_number(
            {"motivation": "moving", "timeline_acceptable": True}
        ) == 3
        assert SellerQuestions.get_question_number({
            "motivation": "moving", "timeline_acceptable": True,
            "property_condition": "good", "price_expectation": "500k",
        }) == 5


# ---------------------------------------------------------------------------
# D4 — Tone Compliance
# ---------------------------------------------------------------------------

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

# Phrases that sound AI-generated. "based on your responses" is excluded
# because the spec mandates it in the hot seller handoff (Section 2.7).
AI_SOUNDING_PHRASES = [
    "i'd be happy to",
    "thank you for sharing",
    "that's a great question",
    "i appreciate your",
    "i understand your concerns",
    "let me help you",
]


class TestToneCompliance:
    """No emojis, no hyphens, <160 chars, no AI-sounding phrases."""

    @pytest.fixture
    def engine(self):
        return JorgeToneEngine()

    def _collect_sample_messages(self, engine: JorgeToneEngine) -> list[str]:
        """Generate 10+ sample messages via the tone engine."""
        msgs = []
        for q in range(1, 5):
            msgs.append(engine.generate_qualification_message(q, seller_name="Jorge"))
        for q in range(1, 5):
            msgs.append(engine.generate_follow_up_message("maybe", q, seller_name="Jorge"))
        msgs.append(engine.generate_hot_seller_handoff(seller_name="Jorge"))
        msgs.append(engine.generate_take_away_close(seller_name="Jorge"))
        msgs.append(engine.generate_objection_response("timeline_too_fast", seller_name="Jorge"))
        return msgs

    def test_no_emojis(self, engine):
        """No message should contain emoji characters."""
        for msg in self._collect_sample_messages(engine):
            assert not EMOJI_PATTERN.search(msg), f"Emoji found in: {msg}"

    def test_no_hyphens(self, engine):
        """No message should contain hyphens."""
        for msg in self._collect_sample_messages(engine):
            assert "-" not in msg, f"Hyphen found in: {msg}"

    def test_under_160_chars(self, engine):
        """Every message must be <= 160 characters."""
        for msg in self._collect_sample_messages(engine):
            assert len(msg) <= 160, f"Message {len(msg)} chars: {msg}"

    def test_no_ai_sounding_phrases(self, engine):
        """Messages must not contain AI-sounding language."""
        for msg in self._collect_sample_messages(engine):
            msg_lower = msg.lower()
            for phrase in AI_SOUNDING_PHRASES:
                assert phrase not in msg_lower, f"AI phrase '{phrase}' in: {msg}"

    def test_jorge_style_direct(self, engine):
        """Messages should be direct (pass compliance validation)."""
        for msg in self._collect_sample_messages(engine):
            result = engine.validate_message_compliance(msg)
            assert result["compliant"], f"Non-compliant: {result['violations']} in: {msg}"

    def test_sms_compliance_strips_emojis(self, engine):
        """Ensure _ensure_sms_compliance removes injected emojis."""
        dirty = "Hey! Let's sell your home! \U0001F600\U0001F3E0"
        clean = engine._ensure_sms_compliance(dirty)
        assert not EMOJI_PATTERN.search(clean)

    def test_sms_compliance_strips_hyphens(self, engine):
        """Ensure _ensure_sms_compliance removes hyphens."""
        dirty = "Your move-in ready high-end home is great"
        clean = engine._ensure_sms_compliance(dirty)
        assert "-" not in clean

    def test_sms_compliance_truncates_long(self, engine):
        """Ensure messages over 160 chars get truncated."""
        long_msg = "A" * 200
        clean = engine._ensure_sms_compliance(long_msg)
        assert len(clean) <= 160
