import pytest
pytestmark = pytest.mark.integration

"""Tests for warm handoff card generator.

Covers card generation, formatting, serialization, priority mapping,
fact extraction, and recommended approach logic.
"""

import os

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pytest

from ghl_real_estate_ai.services.jorge.handoff_card_generator import (

@pytest.mark.unit
    HandoffCard,
    HandoffCardGenerator,
    get_handoff_card_generator,
)


# ---------------------------------------------------------------------------
# Helpers — lightweight stub for EnrichedHandoffContext
# ---------------------------------------------------------------------------


@dataclass
class FakeEnrichedContext:
    """Mimics EnrichedHandoffContext for testing without importing the service."""

    source_qualification_score: float = 0.0
    source_temperature: str = "cold"
    budget_range: Optional[Dict[str, Any]] = None
    property_address: Optional[str] = None
    cma_summary: Optional[Dict[str, Any]] = None
    conversation_summary: str = ""
    key_insights: Dict[str, Any] = field(default_factory=dict)
    urgency_level: str = "browsing"


SAMPLE_HISTORY = [
    {"role": "user", "content": "Hi, I want to buy a home in Rancho Cucamonga"},
    {"role": "assistant", "content": "Great! What is your budget range?"},
    {"role": "user", "content": "My budget is around $500k, pre-approved already"},
    {
        "role": "assistant",
        "content": (
            "Excellent! Are you looking to move soon or within a few months? "
            "Do you have a preferred neighborhood?"
        ),
    },
]


# ---------------------------------------------------------------------------
# Test: Card generation with complete enriched context
# ---------------------------------------------------------------------------


class TestCardGenerationWithEnrichedContext:
    def test_populates_all_fields_from_enriched_context(self):
        gen = HandoffCardGenerator()
        ctx = FakeEnrichedContext(
            source_qualification_score=0.85,
            source_temperature="hot",
            budget_range={"min": 400000, "max": 600000},
            conversation_summary="Buyer interested in 3BR homes near Victoria Gardens.",
            key_insights={"preferred_area": "Victoria Gardens", "beds": "3+"},
            urgency_level="30_days",
        )

        card = gen.generate_card(
            source_bot="lead",
            target_bot="buyer",
            contact_id="ct_123",
            reason="buyer_intent_detected",
            confidence=0.92,
            enriched_context=ctx,
            contact_name="Maria Lopez",
        )

        assert card.source_bot == "lead"
        assert card.target_bot == "buyer"
        assert card.qualification_score == 0.85
        assert card.temperature == "hot"
        assert card.budget_range == {"min": 400000, "max": 600000}
        assert card.timeline == "30_days"
        assert card.contact_name == "Maria Lopez"
        assert "Victoria Gardens" in card.conversation_summary
        assert any("preferred_area" in f for f in card.key_facts)


# ---------------------------------------------------------------------------
# Test: Card generation without enriched context (conversation only)
# ---------------------------------------------------------------------------


class TestCardGenerationConversationOnly:
    def test_extracts_summary_and_facts_from_history(self):
        gen = HandoffCardGenerator()

        card = gen.generate_card(
            source_bot="lead",
            target_bot="buyer",
            contact_id="ct_456",
            reason="buyer_intent_detected",
            confidence=0.75,
            conversation_history=SAMPLE_HISTORY,
        )

        assert card.conversation_summary != ""
        assert "4 messages exchanged" in card.conversation_summary
        assert len(card.key_facts) > 0
        assert card.qualification_score == 0.0  # No enriched context
        assert card.temperature == "unknown"


# ---------------------------------------------------------------------------
# Test: Card generation with empty/minimal inputs
# ---------------------------------------------------------------------------


class TestCardGenerationMinimal:
    def test_minimal_card_has_required_fields(self):
        gen = HandoffCardGenerator()

        card = gen.generate_card(
            source_bot="seller",
            target_bot="human",
            contact_id="ct_789",
            reason="escalation",
            confidence=0.5,
        )

        assert card.source_bot == "seller"
        assert card.target_bot == "human"
        assert card.contact_id == "ct_789"
        assert card.handoff_reason == "escalation"
        assert card.confidence == 0.5
        assert card.key_facts == []
        assert card.unanswered_questions == []
        assert card.recommended_approach != ""  # always generated


# ---------------------------------------------------------------------------
# Test: GHL note formatting
# ---------------------------------------------------------------------------


class TestGHLNoteFormatting:
    def test_note_includes_all_sections(self):
        card = HandoffCard(
            source_bot="lead",
            target_bot="buyer",
            handoff_reason="buyer_intent_detected",
            confidence=0.88,
            contact_id="ct_100",
            conversation_summary="Active buyer conversation.",
            key_facts=["Budget mention: $500k", "Timeline mention: ASAP"],
            unanswered_questions=["Do you have a preferred neighborhood?"],
            qualification_score=0.72,
            temperature="warm",
            budget_range={"min": 400000, "max": 600000},
            timeline="30_days",
            recommended_approach="Contact is engaged and responsive. Well-qualified.",
            priority_level="high",
        )

        note = card.to_ghl_note()

        assert "Lead -> Buyer" in note
        assert "buyer_intent_detected" in note
        assert "88%" in note
        assert "HIGH" in note
        assert "Active buyer conversation." in note
        assert "Budget mention: $500k" in note
        assert "Timeline mention: ASAP" in note
        assert "Do you have a preferred neighborhood?" in note
        assert "72%" in note
        assert "warm" in note
        assert "$400,000" in note
        assert "$600,000" in note
        assert "30_days" in note
        assert "Recommended Approach" in note

    def test_note_omits_empty_sections(self):
        card = HandoffCard(
            source_bot="seller",
            target_bot="human",
            handoff_reason="escalation",
            confidence=0.5,
            contact_id="ct_200",
        )

        note = card.to_ghl_note()

        assert "Key Facts:" not in note
        assert "Open Questions:" not in note
        assert "Budget:" not in note


# ---------------------------------------------------------------------------
# Test: to_dict() serialization
# ---------------------------------------------------------------------------


class TestSerialization:
    def test_to_dict_roundtrip(self):
        gen = HandoffCardGenerator()
        ctx = FakeEnrichedContext(
            source_qualification_score=0.6,
            source_temperature="warm",
            budget_range={"min": 300000, "max": 500000},
        )
        card = gen.generate_card(
            source_bot="lead",
            target_bot="seller",
            contact_id="ct_300",
            reason="seller_intent_detected",
            confidence=0.82,
            enriched_context=ctx,
            conversation_history=SAMPLE_HISTORY,
        )

        d = card.to_dict()

        assert d["source_bot"] == "lead"
        assert d["target_bot"] == "seller"
        assert d["confidence"] == 0.82
        assert d["contact_id"] == "ct_300"
        assert isinstance(d["key_facts"], list)
        assert isinstance(d["unanswered_questions"], list)
        assert isinstance(d["budget_range"], dict)
        assert d["created_at"]  # non-empty timestamp string

    def test_to_dict_contains_all_keys(self):
        card = HandoffCard(
            source_bot="a",
            target_bot="b",
            handoff_reason="r",
            confidence=0.5,
            contact_id="c",
        )
        d = card.to_dict()
        expected_keys = {
            "source_bot",
            "target_bot",
            "handoff_reason",
            "confidence",
            "contact_id",
            "contact_name",
            "conversation_summary",
            "key_facts",
            "unanswered_questions",
            "qualification_score",
            "temperature",
            "budget_range",
            "timeline",
            "recommended_approach",
            "priority_level",
            "created_at",
            "metadata",
        }
        assert set(d.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Test: Priority determination
# ---------------------------------------------------------------------------


class TestPriorityDetermination:
    @pytest.mark.parametrize(
        "confidence,expected",
        [
            (0.95, "urgent"),
            (0.90, "urgent"),
            (0.85, "high"),
            (0.80, "high"),
            (0.70, "normal"),
            (0.60, "normal"),
            (0.50, "low"),
            (0.30, "low"),
            (0.0, "low"),
        ],
    )
    def test_confidence_to_priority_mapping(self, confidence, expected):
        gen = HandoffCardGenerator()
        assert gen._determine_priority(confidence) == expected


# ---------------------------------------------------------------------------
# Test: Key facts extraction
# ---------------------------------------------------------------------------


class TestKeyFactsExtraction:
    def test_extracts_budget_mentions(self):
        gen = HandoffCardGenerator()
        history = [
            {"role": "user", "content": "My budget is $450,000"},
            {"role": "assistant", "content": "Got it!"},
        ]
        facts = gen._extract_key_facts(history)
        assert len(facts) == 1
        assert "Budget mention" in facts[0]

    def test_extracts_timeline_mentions(self):
        gen = HandoffCardGenerator()
        history = [
            {"role": "user", "content": "We need to move within 2 months"},
            {"role": "assistant", "content": "Understood."},
        ]
        facts = gen._extract_key_facts(history)
        assert len(facts) == 1
        assert "Timeline mention" in facts[0]

    def test_caps_at_five_facts(self):
        gen = HandoffCardGenerator()
        history = [
            {"role": "user", "content": f"Budget is ${i * 100}k, ready soon"}
            for i in range(10)
        ]
        facts = gen._extract_key_facts(history)
        assert len(facts) <= 5

    def test_ignores_assistant_messages(self):
        gen = HandoffCardGenerator()
        history = [
            {"role": "assistant", "content": "What is your budget?"},
        ]
        facts = gen._extract_key_facts(history)
        assert facts == []


# ---------------------------------------------------------------------------
# Test: Unanswered questions extraction
# ---------------------------------------------------------------------------


class TestUnansweredQuestions:
    def test_extracts_questions_from_last_assistant_msg(self):
        gen = HandoffCardGenerator()
        history = [
            {"role": "user", "content": "I want to sell."},
            {
                "role": "assistant",
                "content": "How long have you owned the property? What improvements have you made?",
            },
        ]
        questions = gen._extract_unanswered_questions(history)
        assert len(questions) == 2
        assert all(q.endswith("?") for q in questions)

    def test_caps_at_three_questions(self):
        gen = HandoffCardGenerator()
        long_qs = "First question? Second question? Third question? Fourth question? Fifth?"
        history = [{"role": "assistant", "content": long_qs}]
        questions = gen._extract_unanswered_questions(history)
        assert len(questions) <= 3

    def test_returns_empty_when_no_assistant_msgs(self):
        gen = HandoffCardGenerator()
        history = [{"role": "user", "content": "Hello"}]
        questions = gen._extract_unanswered_questions(history)
        assert questions == []


# ---------------------------------------------------------------------------
# Test: Recommended approach generation
# ---------------------------------------------------------------------------


class TestRecommendedApproach:
    def test_hot_well_qualified(self):
        gen = HandoffCardGenerator()
        card = HandoffCard(
            source_bot="lead",
            target_bot="buyer",
            handoff_reason="buyer_intent",
            confidence=0.9,
            contact_id="c1",
            temperature="hot",
            qualification_score=0.8,
        )
        approach = gen._generate_approach(card)
        assert "engaged" in approach.lower()
        assert "well-qualified" in approach.lower()

    def test_cold_low_qualification(self):
        gen = HandoffCardGenerator()
        card = HandoffCard(
            source_bot="lead",
            target_bot="seller",
            handoff_reason="seller_intent",
            confidence=0.6,
            contact_id="c2",
            temperature="cold",
            qualification_score=0.2,
        )
        approach = gen._generate_approach(card)
        assert "re-engagement" in approach.lower()
        assert "rapport" in approach.lower()

    def test_includes_open_questions_note(self):
        gen = HandoffCardGenerator()
        card = HandoffCard(
            source_bot="lead",
            target_bot="buyer",
            handoff_reason="buyer_intent",
            confidence=0.7,
            contact_id="c3",
            unanswered_questions=["What neighborhood?", "When move?"],
        )
        approach = gen._generate_approach(card)
        assert "2 open question" in approach.lower()

    def test_default_approach_when_unknown(self):
        gen = HandoffCardGenerator()
        card = HandoffCard(
            source_bot="lead",
            target_bot="buyer",
            handoff_reason="intent",
            confidence=0.7,
            contact_id="c4",
            temperature="unknown",
            qualification_score=0.0,
        )
        approach = gen._generate_approach(card)
        assert "rapport" in approach.lower()


# ---------------------------------------------------------------------------
# Test: Singleton accessor
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_handoff_card_generator_returns_same_instance(self):
        g1 = get_handoff_card_generator()
        g2 = get_handoff_card_generator()
        assert g1 is g2
        assert isinstance(g1, HandoffCardGenerator)