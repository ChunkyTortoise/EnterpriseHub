"""
Industry-Agnostic Bot Configuration Layer

Provides dataclass-based configuration that decouples domain knowledge
(intent markers, personality, market data, handoff rules) from bot logic.
Configs can be loaded from YAML files, enabling the same bot framework
to serve real estate, dental, HVAC, or any service industry.

Author: Claude Code Assistant
Created: 2026-02-08
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)

# Jinja2 is optional — only needed for template rendering
try:
    from jinja2 import Template as Jinja2Template

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


# ── Leaf Dataclasses ──────────────────────────────────────────────────────────


@dataclass
class BotPersonality:
    """Bot persona: name, role, communication style, and prompt template."""

    name: str
    role: str
    approach: str
    core_values: List[str] = field(default_factory=list)
    system_prompt_template: str = ""
    tone_instructions: Dict[str, str] = field(default_factory=dict)
    phrases: Dict[str, List[str]] = field(default_factory=dict)

    def render_system_prompt(self, context: Dict[str, Any] | None = None) -> str:
        """Render the system prompt template with Jinja2 context variables.

        Args:
            context: Template variables (e.g. lead_name, tone_mode).

        Returns:
            Rendered prompt string.

        Raises:
            RuntimeError: If Jinja2 is not installed.
        """
        if not self.system_prompt_template:
            return ""
        if not JINJA2_AVAILABLE:
            raise RuntimeError("Jinja2 is required for template rendering: pip install Jinja2")
        template = Jinja2Template(self.system_prompt_template)
        return template.render(**(context or {}))


@dataclass
class IntentMarkers:
    """Graduated intent signal lists (high / medium / low confidence)."""

    high: List[str] = field(default_factory=list)
    medium: List[str] = field(default_factory=list)
    low: List[str] = field(default_factory=list)


@dataclass
class IntentConfig:
    """Full intent-detection configuration: markers, patterns, weights, thresholds."""

    motivation: IntentMarkers = field(default_factory=IntentMarkers)
    timeline: IntentMarkers = field(default_factory=IntentMarkers)
    condition: IntentMarkers = field(default_factory=IntentMarkers)
    price: IntentMarkers = field(default_factory=IntentMarkers)
    buyer_patterns: List[str] = field(default_factory=list)
    seller_patterns: List[str] = field(default_factory=list)
    scoring_weights: Dict[str, float] = field(default_factory=dict)
    temperature_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class MarketConfig:
    """Geographic / regulatory market definition."""

    name: str = ""
    state: str = ""
    regulatory_authority: str = ""
    neighborhoods: List[Dict[str, Any]] = field(default_factory=list)
    price_ranges: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    service_areas: List[str] = field(default_factory=list)
    compliance_notes: List[str] = field(default_factory=list)


@dataclass
class QuestionConfig:
    """Qualification question sets, follow-ups, and accelerators."""

    questions: List[Dict[str, Any]] = field(default_factory=list)
    follow_ups: Dict[str, List[str]] = field(default_factory=dict)
    accelerators: List[str] = field(default_factory=list)


@dataclass
class HandoffConfig:
    """Cross-bot handoff rules: thresholds, rate limits, intent patterns."""

    thresholds: Dict[str, float] = field(default_factory=dict)
    rate_limits: Dict[str, int] = field(default_factory=dict)
    circular_prevention_window: int = 1800  # seconds (default 30 min)
    buyer_intent_patterns: List[str] = field(default_factory=list)
    seller_intent_patterns: List[str] = field(default_factory=list)


# ── Root Config ───────────────────────────────────────────────────────────────


@dataclass
class IndustryConfig:
    """
    Top-level industry configuration container.

    Aggregates personality, intent detection, market data, qualification
    questions, handoff rules, and arbitrary business rules for a single
    industry + market combination.
    """

    industry: str = ""
    market: MarketConfig = field(default_factory=MarketConfig)
    personality: BotPersonality = field(default_factory=lambda: BotPersonality(name="", role="", approach=""))
    intents: IntentConfig = field(default_factory=IntentConfig)
    questions: QuestionConfig = field(default_factory=QuestionConfig)
    handoff: HandoffConfig = field(default_factory=HandoffConfig)
    business_rules: Dict[str, Any] = field(default_factory=dict)

    # ── Factory Methods ───────────────────────────────────────────────────

    @classmethod
    def from_yaml(cls, path: str | Path) -> IndustryConfig:
        """Load an IndustryConfig from a YAML file.

        Args:
            path: Filesystem path to a YAML config file.

        Returns:
            Populated IndustryConfig instance.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValueError: If the YAML is invalid or missing required fields.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Industry config not found: {path}")

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ValueError(f"Expected a YAML mapping at top level in {path}")

        return cls._from_dict(raw, source=str(path))

    @classmethod
    def default_real_estate(cls) -> IndustryConfig:
        """Return the bundled Rancho Cucamonga real-estate config.

        Falls back to a minimal in-memory default if the YAML file is
        missing (e.g. in minimal test environments).
        """
        yaml_path = Path(__file__).parent / "industries" / "real_estate_rancho.yaml"
        if yaml_path.exists():
            return cls.from_yaml(yaml_path)
        logger.warning("Bundled real_estate_rancho.yaml not found; using minimal defaults")
        return cls._minimal_real_estate()

    # ── Internal Helpers ──────────────────────────────────────────────────

    @classmethod
    def _from_dict(cls, data: Dict[str, Any], source: str = "<dict>") -> IndustryConfig:
        """Hydrate an IndustryConfig from a parsed dictionary."""
        # Required top-level field
        industry = data.get("industry", "")
        if not industry:
            raise ValueError(f"Missing required field 'industry' in {source}")

        # Market
        mkt = data.get("market", {})
        market = MarketConfig(
            name=mkt.get("name", ""),
            state=mkt.get("state", ""),
            regulatory_authority=mkt.get("regulatory_authority", ""),
            neighborhoods=mkt.get("neighborhoods", []),
            price_ranges=mkt.get("price_ranges", {}),
            service_areas=mkt.get("service_areas", []),
            compliance_notes=mkt.get("compliance_notes", []),
        )

        # Personality
        pers = data.get("personality", {})
        personality = BotPersonality(
            name=pers.get("name", ""),
            role=pers.get("role", ""),
            approach=pers.get("approach", ""),
            core_values=pers.get("core_values", []),
            system_prompt_template=pers.get("system_prompt_template", ""),
            tone_instructions=pers.get("tone_instructions", {}),
            phrases=pers.get("phrases", {}),
        )

        # Intents
        intents_raw = data.get("intents", {})
        intents = IntentConfig(
            motivation=cls._parse_markers(intents_raw.get("motivation", {})),
            timeline=cls._parse_markers(intents_raw.get("timeline", {})),
            condition=cls._parse_markers(intents_raw.get("condition", {})),
            price=cls._parse_markers(intents_raw.get("price", {})),
            buyer_patterns=intents_raw.get("buyer_patterns", []),
            seller_patterns=intents_raw.get("seller_patterns", []),
            scoring_weights=intents_raw.get("scoring_weights", {}),
            temperature_thresholds=intents_raw.get("temperature_thresholds", {}),
        )

        # Validate scoring weights sum (if provided)
        weights = intents.scoring_weights
        if weights:
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                logger.warning("Scoring weights sum to %.3f (expected 1.0) in %s", total, source)

        # Validate handoff patterns are valid regex
        for pattern in intents.buyer_patterns + intents.seller_patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"Invalid regex pattern '{pattern}' in {source}: {exc}") from exc

        # Questions
        qs = data.get("questions", {})
        questions = QuestionConfig(
            questions=qs.get("questions", []),
            follow_ups=qs.get("follow_ups", {}),
            accelerators=qs.get("accelerators", []),
        )

        # Handoff
        ho = data.get("handoff", {})
        buyer_hp = ho.get("buyer_intent_patterns", [])
        seller_hp = ho.get("seller_intent_patterns", [])
        # Validate handoff regex patterns
        for pattern in buyer_hp + seller_hp:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ValueError(f"Invalid handoff regex '{pattern}' in {source}: {exc}") from exc

        handoff = HandoffConfig(
            thresholds=ho.get("thresholds", {}),
            rate_limits=ho.get("rate_limits", {}),
            circular_prevention_window=ho.get("circular_prevention_window", 1800),
            buyer_intent_patterns=buyer_hp,
            seller_intent_patterns=seller_hp,
        )

        # Business rules (arbitrary key-value)
        business_rules = data.get("business_rules", {})

        return cls(
            industry=industry,
            market=market,
            personality=personality,
            intents=intents,
            questions=questions,
            handoff=handoff,
            business_rules=business_rules,
        )

    @classmethod
    def _parse_markers(cls, raw: Dict[str, Any]) -> IntentMarkers:
        """Parse an IntentMarkers section from a dict."""
        return IntentMarkers(
            high=raw.get("high", []),
            medium=raw.get("medium", []),
            low=raw.get("low", []),
        )

    @classmethod
    def _minimal_real_estate(cls) -> IndustryConfig:
        """In-memory fallback for real-estate config."""
        return cls(
            industry="real_estate",
            market=MarketConfig(
                name="Rancho Cucamonga",
                state="CA",
                regulatory_authority="California Department of Real Estate",
                service_areas=["Rancho Cucamonga", "Alta Loma", "Etiwanda"],
            ),
            personality=BotPersonality(
                name="Jorge Salas",
                role="Real Estate Professional",
                approach="HELPFUL, CONSULTATIVE, and RELATIONSHIP-FOCUSED",
                core_values=[
                    "Put the seller's success first",
                    "Build trust through expertise and care",
                    "Provide valuable insights and education",
                    "Be patient and understanding",
                    "Focus on long-term relationships",
                ],
            ),
            intents=IntentConfig(
                motivation=IntentMarkers(
                    high=["need to sell fast", "relocating in 30 days", "behind on payments"],
                    medium=["thinking about it", "might sell next year"],
                    low=["just browsing", "not sure"],
                ),
                scoring_weights={
                    "motivation": 0.35,
                    "timeline": 0.30,
                    "condition": 0.20,
                    "price": 0.15,
                },
                temperature_thresholds={"hot": 75, "warm": 50, "lukewarm": 25},
            ),
            handoff=HandoffConfig(
                thresholds={"default": 0.7},
                rate_limits={"per_hour": 3, "per_day": 10},
                circular_prevention_window=1800,
            ),
        )
