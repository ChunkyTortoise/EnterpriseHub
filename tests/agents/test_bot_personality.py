from __future__ import annotations
import pytest
pytestmark = pytest.mark.integration

"""Tests for WS1: Bot Personality ABC, Registry, YAML Config, and Implementations."""

import textwrap
from pathlib import Path

import pytest

from ghl_real_estate_ai.agents.bot_personality import (
    BotPersonality,
    BotPersonalityRegistry,
    HandoffTrigger,
    IntentMarkerSet,
    QualificationQuestion,
    ScoringWeights,
    TemperatureThresholds,
)
from ghl_real_estate_ai.agents.personalities.dental import (  # noqa: F401
    DentalLeadPersonality,
)

# Import to trigger @register decorators
from ghl_real_estate_ai.agents.personalities.real_estate import (  # noqa: F401
    RealEstateBuyerPersonality,
    RealEstateLeadPersonality,
    RealEstateSellerPersonality,
)
from ghl_real_estate_ai.agents.personality_config import (

    PersonalityConfig,
    YAMLBotPersonality,
)

# ── ABC Contract Tests ───────────────────────────────────────────────────────


class TestBotPersonalityABC:
    """Verify the ABC contract is enforced."""

    def test_cannot_instantiate_abc(self) -> None:
        with pytest.raises(TypeError):
            BotPersonality(industry="test", bot_type="test")  # type: ignore[abstract]

    def test_abstract_methods_required(self) -> None:
        class IncompletePers(BotPersonality):
            pass

        with pytest.raises(TypeError):
            IncompletePers(industry="test", bot_type="test")

    def test_concrete_subclass_works(self) -> None:
        lead = RealEstateLeadPersonality()
        assert isinstance(lead, BotPersonality)
        assert lead.industry == "real_estate"
        assert lead.bot_type == "lead"


# ── Registry Tests ───────────────────────────────────────────────────────────


class TestBotPersonalityRegistry:
    def test_list_industries(self) -> None:
        industries = BotPersonalityRegistry.list_industries()
        assert "real_estate" in industries
        assert "dental" in industries

    def test_list_registered(self) -> None:
        registered = BotPersonalityRegistry.list_registered()
        assert ("real_estate", "lead") in registered
        assert ("real_estate", "buyer") in registered
        assert ("real_estate", "seller") in registered
        assert ("dental", "lead") in registered

    def test_get_exact_match(self) -> None:
        cls = BotPersonalityRegistry.get("real_estate", "lead")
        assert cls is RealEstateLeadPersonality

    def test_get_buyer(self) -> None:
        cls = BotPersonalityRegistry.get("real_estate", "buyer")
        assert cls is RealEstateBuyerPersonality

    def test_get_seller(self) -> None:
        cls = BotPersonalityRegistry.get("real_estate", "seller")
        assert cls is RealEstateSellerPersonality

    def test_get_dental(self) -> None:
        cls = BotPersonalityRegistry.get("dental", "lead")
        assert cls is DentalLeadPersonality

    def test_get_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="hvac"):
            BotPersonalityRegistry.get("hvac", "lead")

    def test_wildcard_fallback(self) -> None:
        # Register a wildcard
        @BotPersonalityRegistry.register("test_wild", "*")
        class WildPersonality(RealEstateLeadPersonality):
            pass

        # Should fall back to wildcard
        cls = BotPersonalityRegistry.get("test_wild", "anything")
        assert cls is WildPersonality

        # Cleanup
        del BotPersonalityRegistry._registry[("test_wild", "*")]


# ── IntentMarkerSet Tests ────────────────────────────────────────────────────


class TestIntentMarkerSet:
    def test_score_high_match(self) -> None:
        markers = IntentMarkerSet(
            high=["must sell"], medium=["thinking"], low=["just curious"]
        )
        score = markers.score("I must sell my house")
        assert score > 40

    def test_score_low_match_reduces(self) -> None:
        markers = IntentMarkerSet(high=[], medium=[], low=["just curious"])
        score = markers.score("I'm just curious about prices")
        assert score < 25

    def test_score_no_match_returns_base(self) -> None:
        markers = IntentMarkerSet(high=["xyz"], medium=["abc"], low=["def"])
        score = markers.score("nothing matches here")
        assert score == 25.0

    def test_score_clamped_to_0_100(self) -> None:
        markers = IntentMarkerSet(
            high=[], medium=[], low=["a", "b", "c", "d", "e"]
        )
        score = markers.score("a b c d e")
        assert score >= 0.0
        assert score <= 100.0


# ── TemperatureThresholds Tests ──────────────────────────────────────────────


class TestTemperatureThresholds:
    def test_hot(self) -> None:
        t = TemperatureThresholds(hot=75, warm=50, lukewarm=25)
        assert t.classify(80) == "hot"

    def test_warm(self) -> None:
        t = TemperatureThresholds(hot=75, warm=50, lukewarm=25)
        assert t.classify(60) == "warm"

    def test_lukewarm(self) -> None:
        t = TemperatureThresholds(hot=75, warm=50, lukewarm=25)
        assert t.classify(30) == "lukewarm"

    def test_cold(self) -> None:
        t = TemperatureThresholds(hot=75, warm=50, lukewarm=25)
        assert t.classify(10) == "cold"

    def test_boundary_hot(self) -> None:
        t = TemperatureThresholds(hot=75, warm=50, lukewarm=25)
        assert t.classify(75) == "hot"

    def test_boundary_warm(self) -> None:
        t = TemperatureThresholds(hot=75, warm=50, lukewarm=25)
        assert t.classify(50) == "warm"


# ── ScoringWeights Tests ─────────────────────────────────────────────────────


class TestScoringWeights:
    def test_valid_weights(self) -> None:
        sw = ScoringWeights(weights={"a": 0.5, "b": 0.5})
        assert sw.compute({"a": 80, "b": 60}) == 70.0

    def test_invalid_weights_raises(self) -> None:
        with pytest.raises(ValueError, match="sum to 1.0"):
            ScoringWeights(weights={"a": 0.5, "b": 0.3})

    def test_compute_missing_dim_defaults_zero(self) -> None:
        sw = ScoringWeights(weights={"a": 0.5, "b": 0.5})
        result = sw.compute({"a": 80})
        assert result == 40.0

    def test_compute_clamped(self) -> None:
        sw = ScoringWeights(weights={"a": 1.0})
        assert sw.compute({"a": 150}) == 100.0

    def test_empty_weights_ok(self) -> None:
        sw = ScoringWeights(weights={})
        assert sw.compute({"a": 80}) == 0.0


# ── Real Estate Personality Tests ────────────────────────────────────────────


class TestRealEstatePersonality:
    def setup_method(self) -> None:
        self.lead = RealEstateLeadPersonality()
        self.buyer = RealEstateBuyerPersonality()
        self.seller = RealEstateSellerPersonality()

    def test_lead_questions(self) -> None:
        qs = self.lead.get_qualification_questions()
        assert len(qs) >= 3
        categories = {q.category for q in qs}
        assert "timeline" in categories
        assert "motivation" in categories

    def test_lead_intent_signals(self) -> None:
        signals = self.lead.get_intent_signals()
        assert "motivation" in signals
        assert "timeline" in signals
        assert len(signals["motivation"].high) > 0

    def test_lead_temperature_classify(self) -> None:
        assert self.lead.classify_temperature(80) == "hot"
        assert self.lead.classify_temperature(40) == "lukewarm"
        assert self.lead.classify_temperature(10) == "cold"

    def test_lead_handoff_triggers(self) -> None:
        triggers = self.lead.get_handoff_triggers()
        targets = {t.target_bot for t in triggers}
        assert "buyer" in targets
        assert "seller" in targets

    def test_lead_handoff_match_buyer(self) -> None:
        trigger = self.lead.match_handoff("I want to buy a home")
        assert trigger is not None
        assert trigger.target_bot == "buyer"

    def test_lead_handoff_match_seller(self) -> None:
        trigger = self.lead.match_handoff("I want to sell my house")
        assert trigger is not None
        assert trigger.target_bot == "seller"

    def test_lead_no_handoff_match(self) -> None:
        assert self.lead.match_handoff("hello there") is None

    def test_lead_system_prompt(self) -> None:
        prompt = self.lead.get_system_prompt({"lead_name": "Alice"})
        assert "Jorge Salas" in prompt
        assert "Alice" in prompt

    def test_lead_scoring(self) -> None:
        scores = {
            "motivation": 80, "timeline": 60, "condition": 50,
            "price": 50, "valuation": 40, "prep_readiness": 30,
        }
        overall = self.lead.compute_overall_score(scores)
        assert 40 < overall < 80

    def test_buyer_journey_stages(self) -> None:
        stages = self.buyer.get_journey_stages()
        assert "discovery" in stages
        assert "closed" in stages

    def test_seller_stall_responses(self) -> None:
        stalls = self.seller.get_stall_responses()
        assert "zestimate" in stalls
        assert len(stalls["zestimate"]) > 0

    def test_seller_tone_instructions(self) -> None:
        tones = self.seller.get_tone_instructions()
        assert "consultative" in tones

    def test_determine_next_step(self) -> None:
        scores = {"motivation": 80, "timeline": 30, "price": 60}
        step = self.lead.determine_next_step(scores)
        assert step == "timeline"  # lowest


# ── Dental Personality Tests ─────────────────────────────────────────────────


class TestDentalPersonality:
    def setup_method(self) -> None:
        self.dental = DentalLeadPersonality()

    def test_dental_questions(self) -> None:
        qs = self.dental.get_qualification_questions()
        assert len(qs) >= 3
        categories = {q.category for q in qs}
        assert "procedure" in categories
        assert "insurance" in categories

    def test_dental_intent_signals(self) -> None:
        signals = self.dental.get_intent_signals()
        assert "urgency" in signals
        assert "procedure_value" in signals
        assert "emergency" in signals["urgency"].high

    def test_dental_temperature(self) -> None:
        assert self.dental.classify_temperature(80) == "hot"
        assert self.dental.classify_temperature(50) == "warm"
        assert self.dental.classify_temperature(10) == "cold"

    def test_dental_handoff_cosmetic(self) -> None:
        trigger = self.dental.match_handoff("I want veneers")
        assert trigger is not None
        assert trigger.target_bot == "cosmetic"

    def test_dental_handoff_orthodontic(self) -> None:
        trigger = self.dental.match_handoff("I need braces for my teeth")
        assert trigger is not None
        assert trigger.target_bot == "orthodontic"

    def test_dental_handoff_emergency(self) -> None:
        trigger = self.dental.match_handoff("I have an emergency toothache")
        assert trigger is not None
        assert trigger.target_bot == "emergency"

    def test_dental_system_prompt(self) -> None:
        prompt = self.dental.get_system_prompt({"patient_name": "Bob"})
        assert "Bob" in prompt
        assert "dental" in prompt.lower()

    def test_dental_scoring(self) -> None:
        scores = {
            "urgency": 90, "procedure_value": 70,
            "insurance_status": 60, "motivation": 50,
        }
        overall = self.dental.compute_overall_score(scores)
        assert 50 < overall < 90

    def test_dental_stall_anxiety(self) -> None:
        stalls = self.dental.get_stall_responses()
        assert "dental_anxiety" in stalls

    def test_dental_journey_stages(self) -> None:
        stages = self.dental.get_journey_stages()
        assert "initial_inquiry" in stages
        assert "scheduling" in stages


# ── YAML Config Tests ────────────────────────────────────────────────────────


class TestPersonalityConfig:
    def test_from_dict(self) -> None:
        config = PersonalityConfig(
            industry="test",
            bot_type="lead",
            tone="friendly",
            name="TestBot",
            role="Tester",
            scoring_weights={"a": 0.5, "b": 0.5},
        )
        assert config.industry == "test"
        assert config.name == "TestBot"

    def test_invalid_weights_rejected(self) -> None:
        with pytest.raises(ValueError, match="sum to 1.0"):
            PersonalityConfig(
                industry="test",
                scoring_weights={"a": 0.5, "b": 0.3},
            )

    def test_to_personality(self) -> None:
        config = PersonalityConfig(
            industry="yaml_test",
            bot_type="lead",
            tone="consultative",
            name="YAMLBot",
            role="Assistant",
            system_prompt_template="Hello {name}, you are a {role}.",
            qualification_questions=[
                {"text": "What do you need?", "category": "need", "priority": 1}
            ],
            scoring_weights={"need": 0.5, "budget": 0.5},
            temperature_thresholds={"hot": 80, "warm": 50, "lukewarm": 20},
            journey_stages=["start", "middle", "end"],
        )
        personality = config.to_personality()
        assert isinstance(personality, YAMLBotPersonality)
        assert isinstance(personality, BotPersonality)
        assert personality.industry == "yaml_test"

        # Check methods
        qs = personality.get_qualification_questions()
        assert len(qs) == 1
        assert qs[0].category == "need"

        prompt = personality.get_system_prompt()
        assert "YAMLBot" in prompt
        assert "Assistant" in prompt

        assert personality.classify_temperature(85) == "hot"
        assert personality.classify_temperature(30) == "lukewarm"

    def test_from_yaml_file(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            industry: hvac
            bot_type: lead
            tone: friendly
            name: CoolBot
            role: HVAC Assistant
            system_prompt_template: "You are {name}."
            qualification_questions:
              - text: "What type of service?"
                category: service
                priority: 2
              - text: "Home or business?"
                category: location
                priority: 1
            intent_signals:
              urgency:
                high: ["no AC", "emergency", "broken"]
                medium: ["not cooling well"]
                low: ["tune-up", "maintenance"]
            temperature_thresholds:
              hot: 70
              warm: 40
              lukewarm: 20
            scoring_weights:
              urgency: 1.0
            handoff_triggers:
              - target_bot: commercial
                confidence_threshold: 0.7
                trigger_phrases: ["office building", "commercial"]
            journey_stages:
              - inquiry
              - assessment
              - scheduling
              - service
        """)
        yaml_file = tmp_path / "hvac.yaml"
        yaml_file.write_text(yaml_content)

        config = PersonalityConfig.from_yaml(yaml_file)
        assert config.industry == "hvac"
        assert config.name == "CoolBot"
        assert len(config.qualification_questions) == 2

        personality = config.to_personality()
        assert personality.classify_temperature(75) == "hot"
        signals = personality.get_intent_signals()
        assert "urgency" in signals
        assert "no AC" in signals["urgency"].high

        triggers = personality.get_handoff_triggers()
        assert len(triggers) == 1
        assert triggers[0].target_bot == "commercial"

    def test_from_yaml_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            PersonalityConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_register_config(self) -> None:
        config = PersonalityConfig(
            industry="test_register",
            bot_type="lead",
            scoring_weights={"a": 1.0},
        )
        cls = config.register()

        # Verify it's in the registry
        looked_up = BotPersonalityRegistry.get("test_register", "lead")
        assert looked_up is cls

        # Cleanup
        del BotPersonalityRegistry._registry[("test_register", "lead")]