from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

"""
Tests for the industry-agnostic bot configuration layer.

Covers:
- YAML loading for all 4 industry configs
- default_real_estate() factory method
- Invalid YAML error handling
- Missing required field validation
- Personality template rendering (Jinja2)
- Intent markers loaded correctly
- Scoring weights validation
- Market config validation
- Handoff patterns are valid regex
- Bot constructors accept industry_config parameter
"""

import re
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.config.industry_config import (
    BotPersonality,
    HandoffConfig,
    IndustryConfig,
    IntentConfig,
    IntentMarkers,
    MarketConfig,
    QuestionConfig,
)

# ── Paths to bundled YAML configs ─────────────────────────────────────────────

INDUSTRIES_DIR = Path(__file__).resolve().parent.parent / "ghl_real_estate_ai" / "config" / "industries"
RANCHO_YAML = INDUSTRIES_DIR / "real_estate_rancho.yaml"
DALLAS_YAML = INDUSTRIES_DIR / "real_estate_dallas.yaml"
DENTAL_YAML = INDUSTRIES_DIR / "dental_practice.yaml"
HVAC_YAML = INDUSTRIES_DIR / "hvac_services.yaml"


# ═══════════════════════════════════════════════════════════════════════════════
# 1. YAML Loading — All 4 Configs
# ═══════════════════════════════════════════════════════════════════════════════


class TestYAMLLoading:
    """Verify all bundled YAML files load without errors."""

    def test_load_rancho_yaml(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert cfg.industry == "real_estate"
        assert cfg.market.name == "Rancho Cucamonga"
        assert cfg.market.state == "CA"

    def test_load_dallas_yaml(self):
        cfg = IndustryConfig.from_yaml(DALLAS_YAML)
        assert cfg.industry == "real_estate"
        assert cfg.market.name == "Dallas-Fort Worth Metroplex"
        assert cfg.market.state == "TX"

    def test_load_dental_yaml(self):
        cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        assert cfg.industry == "dental_practice"
        assert cfg.personality.name == "Mia"
        assert cfg.personality.role == "Dental Care Coordinator"

    def test_load_hvac_yaml(self):
        cfg = IndustryConfig.from_yaml(HVAC_YAML)
        assert cfg.industry == "hvac_services"
        assert cfg.personality.name == "Alex"
        assert cfg.personality.role == "HVAC Service Coordinator"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. default_real_estate() Factory
# ═══════════════════════════════════════════════════════════════════════════════


class TestDefaultFactory:
    """Verify the default_real_estate() class method."""

    def test_default_real_estate_returns_config(self):
        cfg = IndustryConfig.default_real_estate()
        assert isinstance(cfg, IndustryConfig)
        assert cfg.industry == "real_estate"

    def test_default_real_estate_has_personality(self):
        cfg = IndustryConfig.default_real_estate()
        assert cfg.personality.name == "Jorge Salas"
        assert "HELPFUL" in cfg.personality.approach

    def test_default_real_estate_fallback_when_yaml_missing(self):
        """When YAML file is missing, should fall back to minimal in-memory config."""
        with patch.object(Path, "exists", return_value=False):
            cfg = IndustryConfig.default_real_estate()
            assert cfg.industry == "real_estate"
            assert cfg.personality.name == "Jorge Salas"
            assert len(cfg.intents.motivation.high) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Invalid YAML Error Handling
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Verify proper error handling for invalid inputs."""

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError, match="Industry config not found"):
            IndustryConfig.from_yaml("/nonexistent/path/config.yaml")

    def test_invalid_yaml_syntax_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: [broken: {")
            f.flush()
            with pytest.raises(ValueError, match="Invalid YAML"):
                IndustryConfig.from_yaml(f.name)

    def test_non_mapping_yaml_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- just\n- a\n- list\n")
            f.flush()
            with pytest.raises(ValueError, match="Expected a YAML mapping"):
                IndustryConfig.from_yaml(f.name)

    def test_missing_industry_field_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("market:\n  name: Test\n")
            f.flush()
            with pytest.raises(ValueError, match="Missing required field 'industry'"):
                IndustryConfig.from_yaml(f.name)

    def test_invalid_regex_in_handoff_patterns_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("industry: test\nhandoff:\n  buyer_intent_patterns:\n    - '[invalid regex'\n")
            f.flush()
            with pytest.raises(ValueError, match="Invalid handoff regex"):
                IndustryConfig.from_yaml(f.name)

    def test_invalid_regex_in_intent_buyer_patterns_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("industry: test\nintents:\n  buyer_patterns:\n    - '(unclosed group'\n")
            f.flush()
            with pytest.raises(ValueError, match="Invalid regex pattern"):
                IndustryConfig.from_yaml(f.name)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Personality Template Rendering (Jinja2)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPersonalityTemplateRendering:
    """Verify Jinja2 template rendering for system prompts."""

    def test_render_rancho_system_prompt(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        rendered = cfg.personality.render_system_prompt(
            context={
                "name": cfg.personality.name,
                "approach": cfg.personality.approach,
                "core_values": cfg.personality.core_values,
                "lead_name": "John Smith",
                "tone_mode": "empathetic",
            }
        )
        assert "Jorge Salas" in rendered
        assert "John Smith" in rendered
        assert "empathetic" in rendered

    def test_render_empty_template_returns_empty(self):
        personality = BotPersonality(name="Test", role="Tester", approach="Direct")
        assert personality.render_system_prompt() == ""

    def test_render_dental_prompt(self):
        cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        rendered = cfg.personality.render_system_prompt(
            context={
                "name": "Mia",
                "approach": cfg.personality.approach,
                "core_values": cfg.personality.core_values,
                "lead_name": "Jane Doe",
                "concern_type": "toothache",
            }
        )
        assert "Mia" in rendered
        assert "toothache" in rendered


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Intent Markers Loaded Correctly
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntentMarkers:
    """Verify intent markers are extracted from source files accurately."""

    def test_rancho_motivation_markers(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert "need to sell fast" in cfg.intents.motivation.high
        assert "divorce" in cfg.intents.motivation.high
        assert "thinking about it" in cfg.intents.motivation.medium
        assert "just browsing" in cfg.intents.motivation.low

    def test_rancho_timeline_markers(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert "asap" in cfg.intents.timeline.high
        assert "soon" in cfg.intents.timeline.medium
        assert "eventually" in cfg.intents.timeline.low

    def test_dental_has_appropriate_motivation(self):
        cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        assert "toothache" in cfg.intents.motivation.high
        assert "cleaning due" in cfg.intents.motivation.medium

    def test_hvac_has_appropriate_motivation(self):
        cfg = IndustryConfig.from_yaml(HVAC_YAML)
        assert "no AC" in cfg.intents.motivation.high
        assert "maintenance" in cfg.intents.motivation.low


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Scoring Weights Validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestScoringWeights:
    """Verify scoring weights are valid and sum to 1.0."""

    def test_rancho_weights_sum_to_one(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        total = sum(cfg.intents.scoring_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_dallas_weights_sum_to_one(self):
        cfg = IndustryConfig.from_yaml(DALLAS_YAML)
        total = sum(cfg.intents.scoring_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_dental_weights_sum_to_one(self):
        cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        total = sum(cfg.intents.scoring_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_hvac_weights_sum_to_one(self):
        cfg = IndustryConfig.from_yaml(HVAC_YAML)
        total = sum(cfg.intents.scoring_weights.values())
        assert abs(total - 1.0) < 0.01

    def test_rancho_has_frs_weights(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert cfg.intents.scoring_weights["motivation"] == 0.35
        assert cfg.intents.scoring_weights["timeline"] == 0.30
        assert cfg.intents.scoring_weights["condition"] == 0.20
        assert cfg.intents.scoring_weights["price"] == 0.15


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Market Config Validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestMarketConfig:
    """Verify market configurations are complete and accurate."""

    def test_rancho_service_areas(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert "Rancho Cucamonga" in cfg.market.service_areas
        assert "Alta Loma" in cfg.market.service_areas

    def test_dallas_service_areas(self):
        cfg = IndustryConfig.from_yaml(DALLAS_YAML)
        assert "Dallas" in cfg.market.service_areas
        assert "Plano" in cfg.market.service_areas
        assert "Frisco" in cfg.market.service_areas

    def test_rancho_has_neighborhoods(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert len(cfg.market.neighborhoods) >= 5
        names = [n["name"] for n in cfg.market.neighborhoods]
        assert "Alta Loma" in names

    def test_rancho_has_price_ranges(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert "entry_level" in cfg.market.price_ranges
        assert "luxury" in cfg.market.price_ranges

    def test_dallas_price_range_matches_source(self):
        cfg = IndustryConfig.from_yaml(DALLAS_YAML)
        assert cfg.market.price_ranges["entry_level"]["min"] == 200000
        assert cfg.market.price_ranges["luxury"]["max"] == 800000


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Handoff Patterns — Valid Regex
# ═══════════════════════════════════════════════════════════════════════════════


class TestHandoffPatterns:
    """Verify all handoff patterns compile as valid regex and match expected text."""

    def test_rancho_buyer_patterns_compile(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        for pattern in cfg.handoff.buyer_intent_patterns:
            compiled = re.compile(pattern)
            assert compiled is not None

    def test_rancho_seller_patterns_compile(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        for pattern in cfg.handoff.seller_intent_patterns:
            compiled = re.compile(pattern)
            assert compiled is not None

    def test_buyer_pattern_matches_expected_text(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        text = "I want to buy a house in Rancho Cucamonga"
        matched = any(re.search(p, text, re.IGNORECASE) for p in cfg.handoff.buyer_intent_patterns)
        assert matched, "Expected buyer intent patterns to match 'I want to buy a house'"

    def test_seller_pattern_matches_expected_text(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        text = "I need to sell my home before the end of the month"
        matched = any(re.search(p, text, re.IGNORECASE) for p in cfg.handoff.seller_intent_patterns)
        assert matched, "Expected seller intent patterns to match 'need to sell'"

    def test_rancho_handoff_thresholds(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert cfg.handoff.thresholds["default"] == 0.7
        assert cfg.handoff.rate_limits["per_hour"] == 3
        assert cfg.handoff.rate_limits["per_day"] == 10
        assert cfg.handoff.circular_prevention_window == 1800


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Bot Constructors Accept industry_config
# ═══════════════════════════════════════════════════════════════════════════════


class TestBotConstructorWiring:
    """Verify bot constructors accept and store industry_config parameter.

    These tests use inspect to verify the signature without instantiating
    the bots (which pull in heavy service dependencies).
    """

    def test_seller_bot_signature_has_industry_config(self):
        """JorgeSellerBot.__init__ should accept industry_config kwarg."""
        import inspect

        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

        sig = inspect.signature(JorgeSellerBot.__init__)
        assert "industry_config" in sig.parameters
        param = sig.parameters["industry_config"]
        assert param.default is None

    def test_buyer_bot_signature_has_industry_config(self):
        """JorgeBuyerBot.__init__ should accept industry_config kwarg."""
        import inspect

        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

        sig = inspect.signature(JorgeBuyerBot.__init__)
        assert "industry_config" in sig.parameters
        param = sig.parameters["industry_config"]
        assert param.default is None

    def test_lead_bot_signature_has_industry_config(self):
        """LeadBotWorkflow.__init__ should accept industry_config kwarg."""
        import inspect

        from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

        sig = inspect.signature(LeadBotWorkflow.__init__)
        assert "industry_config" in sig.parameters
        param = sig.parameters["industry_config"]
        assert param.default is None

    def test_seller_bot_stores_industry_config(self):
        """JorgeSellerBot should store industry_config when instantiated."""
        from unittest.mock import MagicMock, patch

        custom_cfg = IndustryConfig.from_yaml(DENTAL_YAML)

        # Mock the heavy dependencies to allow instantiation
        with (
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.SellerIntentDecoder"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.CMAGenerator"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_market_intelligence"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.PerformanceTracker"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.BotMetricsCollector"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.AlertingService"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.ABTestingService"),
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(industry_config=custom_cfg)
            assert bot.industry_config is custom_cfg
            assert bot.industry_config.industry == "dental_practice"

    def test_buyer_bot_stores_industry_config(self):
        """JorgeBuyerBot should store industry_config when instantiated."""
        from unittest.mock import MagicMock, patch

        custom_cfg = IndustryConfig.from_yaml(HVAC_YAML)

        with (
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerIntentDecoder"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLClient"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_ml_analytics_engine", return_value=None),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ABTestingService"),
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(industry_config=custom_cfg)
            assert bot.industry_config is custom_cfg
            assert bot.industry_config.industry == "hvac_services"

    def test_lead_bot_stores_industry_config(self):
        """LeadBotWorkflow should store industry_config when instantiated."""
        from unittest.mock import MagicMock, patch

        custom_cfg = IndustryConfig.from_yaml(DALLAS_YAML)

        with (
            patch("ghl_real_estate_ai.agents.lead_bot.LeadIntentDecoder"),
            patch("ghl_real_estate_ai.agents.lead_bot.RetellClient"),
            patch("ghl_real_estate_ai.agents.lead_bot.CMAGenerator"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_ghost_followup_engine"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_sequence_service"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_lead_scheduler"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_national_market_intelligence", create=True),
            patch(
                "ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence",
                return_value=MagicMock(),
            ),
            patch("ghl_real_estate_ai.agents.lead_bot.PerformanceTracker"),
            patch("ghl_real_estate_ai.agents.lead_bot.BotMetricsCollector"),
            patch("ghl_real_estate_ai.agents.lead_bot.AlertingService"),
            patch("ghl_real_estate_ai.agents.lead_bot.ABTestingService"),
        ):
            from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

            bot = LeadBotWorkflow(industry_config=custom_cfg)
            assert bot.industry_config is custom_cfg
            assert bot.industry_config.market.state == "TX"


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Questions and Business Rules
# ═══════════════════════════════════════════════════════════════════════════════


class TestQuestionsAndBusinessRules:
    """Verify questions and business rules are loaded from YAML."""

    def test_rancho_has_four_core_questions(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert len(cfg.questions.questions) == 4

    def test_rancho_has_accelerators(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert len(cfg.questions.accelerators) >= 2

    def test_rancho_business_rules(self):
        cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        assert cfg.business_rules["commission_standard"] == 0.06
        assert cfg.business_rules["sms_max_length"] == 160


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Behavior Wiring — IndustryConfig actually changes bot behavior
# ═══════════════════════════════════════════════════════════════════════════════


class TestIndustryConfigBehaviorWiring:
    """Verify that IndustryConfig actually changes decoder, bot, and handoff behavior.

    These tests ensure the config-first wiring is live — not just accepted and stored.
    """

    # ── Decoder Tests ────────────────────────────────────────────────────

    def test_dental_decoder_uses_dental_motivation_markers(self):
        """Dental config: 'toothache' should be high motivation, NOT RE markers."""
        from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        decoder = LeadIntentDecoder(industry_config=dental_cfg)

        assert "toothache" in decoder.high_intent_motivation
        assert "need to sell fast" not in decoder.high_intent_motivation

    def test_hvac_decoder_uses_hvac_motivation_markers(self):
        """HVAC config: 'no AC' should be high motivation."""
        from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

        hvac_cfg = IndustryConfig.from_yaml(HVAC_YAML)
        decoder = LeadIntentDecoder(industry_config=hvac_cfg)

        assert "no AC" in decoder.high_intent_motivation
        assert "no heat" in decoder.high_intent_motivation

    def test_default_decoder_uses_real_estate_markers(self):
        """No config: decoder still uses original RE markers."""
        from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

        decoder = LeadIntentDecoder()
        assert "need to sell fast" in decoder.high_intent_motivation
        assert "divorce" in decoder.high_intent_motivation

    def test_dental_scoring_weights_differ_from_re(self):
        """Dental motivation weight (0.40) differs from RE (0.35)."""
        from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        decoder = LeadIntentDecoder(industry_config=dental_cfg)
        # Verify the config weights are loaded (used in analyze_lead)
        assert dental_cfg.intents.scoring_weights["motivation"] == 0.40
        assert dental_cfg.intents.scoring_weights["motivation"] != 0.35  # RE default

    def test_dental_temperature_thresholds_differ(self):
        """Dental hot threshold (70) differs from RE default (75)."""
        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        assert dental_cfg.intents.temperature_thresholds["hot"] == 70
        assert dental_cfg.intents.temperature_thresholds["warm"] == 45

    def test_buyer_decoder_no_re_patterns_for_dental(self):
        """Dental config has empty buyer/seller patterns — decoder falls back to defaults."""
        from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        # Dental has no buyer_patterns in YAML, so decoder should use RE defaults
        assert dental_cfg.intents.buyer_patterns == []
        decoder = LeadIntentDecoder(industry_config=dental_cfg)
        # Falls back to RE defaults since config list is empty
        assert len(decoder.buyer_markers) > 0

    def test_seller_intent_decoder_with_dental_uses_dental_motivation(self):
        """SellerIntentDecoder with dental config uses dental motivation markers."""
        from ghl_real_estate_ai.agents.seller_intent_decoder import SellerIntentDecoder

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        decoder = SellerIntentDecoder(industry_config=dental_cfg)

        # Dental motivation.high = [toothache, pain, broken tooth, ...]
        assert "toothache" in decoder.high_motivation
        assert "must sell" not in decoder.high_motivation

    def test_buyer_intent_decoder_with_hvac_uses_hvac_urgency(self):
        """BuyerIntentDecoder with HVAC config uses HVAC timeline for urgency."""
        from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder

        hvac_cfg = IndustryConfig.from_yaml(HVAC_YAML)
        decoder = BuyerIntentDecoder(industry_config=hvac_cfg)

        # HVAC timeline.high includes "it's 100 degrees", "freezing"
        assert "today" in decoder.immediate_urgency
        assert "it's 100 degrees" in decoder.immediate_urgency

    # ── Bot Tests ────────────────────────────────────────────────────────

    def test_seller_bot_passes_config_to_decoders(self):
        """JorgeSellerBot should pass industry_config to its decoders."""
        from unittest.mock import patch

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)

        with (
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.CMAGenerator"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_market_intelligence"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.PerformanceTracker"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.BotMetricsCollector"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.AlertingService"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.ABTestingService"),
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(industry_config=dental_cfg)
            # Verify decoder got the config
            assert "toothache" in bot.intent_decoder.high_intent_motivation
            assert "toothache" in bot.seller_intent_decoder.high_motivation

    def test_buyer_bot_passes_config_to_decoder(self):
        """JorgeBuyerBot should pass industry_config to BuyerIntentDecoder."""
        from unittest.mock import patch

        hvac_cfg = IndustryConfig.from_yaml(HVAC_YAML)

        with (
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLClient"),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_ml_analytics_engine", return_value=None),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ABTestingService"),
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(industry_config=hvac_cfg)
            # HVAC timeline.high includes "today", "right now", etc.
            assert "today" in bot.intent_decoder.immediate_urgency

    def test_lead_bot_passes_config_to_decoder(self):
        """LeadBotWorkflow should pass industry_config to LeadIntentDecoder."""
        from unittest.mock import MagicMock, patch

        dallas_cfg = IndustryConfig.from_yaml(DALLAS_YAML)

        with (
            patch("ghl_real_estate_ai.agents.lead_bot.RetellClient"),
            patch("ghl_real_estate_ai.agents.lead_bot.CMAGenerator"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_ghost_followup_engine"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_event_publisher"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_sequence_service"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_lead_scheduler"),
            patch("ghl_real_estate_ai.agents.lead_bot.get_national_market_intelligence", create=True),
            patch(
                "ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence",
                return_value=MagicMock(),
            ),
            patch("ghl_real_estate_ai.agents.lead_bot.PerformanceTracker"),
            patch("ghl_real_estate_ai.agents.lead_bot.BotMetricsCollector"),
            patch("ghl_real_estate_ai.agents.lead_bot.AlertingService"),
            patch("ghl_real_estate_ai.agents.lead_bot.ABTestingService"),
        ):
            from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

            bot = LeadBotWorkflow(industry_config=dallas_cfg)
            # Dallas RE config has same markers as rancho
            assert "need to sell fast" in bot.intent_decoder.high_intent_motivation

    def test_adaptive_question_engine_with_dental_questions(self):
        """AdaptiveQuestionEngine with dental config uses dental questions."""
        from ghl_real_estate_ai.agents.jorge_seller_bot import AdaptiveQuestionEngine

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        engine = AdaptiveQuestionEngine(questions_config=dental_cfg.questions)

        # Dental questions include "pain or discomfort"
        assert any("pain or discomfort" in q for q in engine.jorge_core_questions)
        # Should NOT have RE questions
        assert not any("timeline for selling" in q for q in engine.jorge_core_questions)

    def test_adaptive_question_engine_default_questions(self):
        """AdaptiveQuestionEngine with no config uses RE defaults."""
        from ghl_real_estate_ai.agents.jorge_seller_bot import AdaptiveQuestionEngine

        engine = AdaptiveQuestionEngine()
        assert any("timeline for selling" in q for q in engine.jorge_core_questions)

    # ── Handoff Tests ────────────────────────────────────────────────────

    def test_handoff_service_dental_threshold(self):
        """Dental config: default threshold 0.6 not 0.7."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        service = JorgeHandoffService(industry_config=dental_cfg)

        # Dental default threshold is 0.6 applied to all routes
        for key in service._thresholds:
            assert service._thresholds[key] == 0.6

    def test_handoff_service_dental_empty_patterns(self):
        """Dental config: empty buyer/seller intent patterns."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        service = JorgeHandoffService(industry_config=dental_cfg)

        # Dental has empty buyer/seller patterns, so falls back to class defaults
        assert len(service._buyer_intent_patterns) > 0  # Falls back
        assert service._buyer_intent_patterns == list(JorgeHandoffService.BUYER_INTENT_PATTERNS)

    def test_handoff_service_default_uses_re_patterns(self):
        """Default service (no config): still uses RE patterns."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        service = JorgeHandoffService()
        assert service._buyer_intent_patterns == list(JorgeHandoffService.BUYER_INTENT_PATTERNS)
        assert service._seller_intent_patterns == list(JorgeHandoffService.SELLER_INTENT_PATTERNS)

    def test_handoff_classmethod_wrapper_works(self):
        """Backward-compatible classmethod wrapper returns signals."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        history = [{"content": "I want to buy a house"}]
        signals = JorgeHandoffService.extract_intent_signals_from_history_cls(history)
        assert "buyer_intent" in signals
        assert signals["buyer_intent"] > 0

    def test_handoff_instance_method_uses_config_patterns(self):
        """Instance method uses config patterns when provided."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        rancho_cfg = IndustryConfig.from_yaml(RANCHO_YAML)
        service = JorgeHandoffService(industry_config=rancho_cfg)

        history = [{"content": "I want to buy a house in Rancho Cucamonga"}]
        signals = service.extract_intent_signals_from_history(history)
        assert "buyer_intent" in signals

    def test_handoff_config_thresholds_map_correctly(self):
        """Config thresholds are applied to the tuple-keyed dict."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        dental_cfg = IndustryConfig.from_yaml(DENTAL_YAML)
        service = JorgeHandoffService(industry_config=dental_cfg)

        # All routes should have 0.6 from dental default
        assert service._thresholds[("lead", "buyer")] == 0.6
        assert service._thresholds[("lead", "seller")] == 0.6
        assert service._thresholds[("buyer", "seller")] == 0.6
        assert service._thresholds[("seller", "buyer")] == 0.6
