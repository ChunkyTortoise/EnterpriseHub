"""
Industry-Agnostic Bot Personality ABC + Registry

Defines the behavioral contract for industry-specific bot personalities.
Implementations provide intent signals, qualification questions, temperature
thresholds, handoff triggers, and system prompts for a given industry.

Note: This ABC defines the *behavioral* contract. The static config dataclass
``config.industry_config.BotPersonality`` stores raw persona data (name, role,
tone instructions). Implementations of this ABC may consume that dataclass
internally.

Author: Claude Code Assistant
Created: 2026-02-09
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# ── Supporting Dataclasses ────────────────────────────────────────────────────


@dataclass
class QualificationQuestion:
    """A single qualification question for lead/contact scoring."""

    text: str
    category: str  # e.g. "timeline", "budget", "motivation", "urgency"
    priority: int = 0  # higher = asked earlier
    follow_ups: list[str] = field(default_factory=list)


@dataclass
class HandoffTrigger:
    """Defines when to hand off a conversation to a different bot type."""

    target_bot: str  # e.g. "buyer", "seller", "specialist", "cosmetic"
    confidence_threshold: float = 0.7
    trigger_phrases: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class IntentMarkerSet:
    """Graduated keyword lists for scoring a single intent dimension."""

    high: list[str] = field(default_factory=list)
    medium: list[str] = field(default_factory=list)
    low: list[str] = field(default_factory=list)

    def score(self, text: str, base: float = 25.0) -> float:
        """Score text against this marker set.

        Returns a 0-100 score using weighted keyword matching.
        """
        text_lower = text.lower()
        score = base
        high_matches = sum(1 for m in self.high if m.lower() in text_lower)
        score += min(high_matches * 25, 50)
        medium_matches = sum(1 for m in self.medium if m.lower() in text_lower)
        score += min(medium_matches * 15, 30)
        low_matches = sum(1 for m in self.low if m.lower() in text_lower)
        score -= min(low_matches * 15, 30)
        return max(0.0, min(100.0, score))


@dataclass
class TemperatureThresholds:
    """Thresholds for classifying lead temperature from a 0-100 score."""

    hot: float = 75.0
    warm: float = 50.0
    lukewarm: float = 25.0

    def classify(self, score: float) -> str:
        """Classify a numeric score into a temperature label."""
        if score >= self.hot:
            return "hot"
        elif score >= self.warm:
            return "warm"
        elif score >= self.lukewarm:
            return "lukewarm"
        else:
            return "cold"


@dataclass
class ScoringWeights:
    """Named weights for multi-dimension intent scoring.

    Keys are dimension names (e.g. "motivation", "timeline"), values are
    floats that should sum to 1.0.
    """

    weights: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.weights:
            total = sum(self.weights.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Scoring weights must sum to 1.0, got {total:.3f}")

    def compute(self, scores: dict[str, float]) -> float:
        """Compute weighted overall score from per-dimension scores."""
        total = 0.0
        for dim, weight in self.weights.items():
            total += scores.get(dim, 0.0) * weight
        return max(0.0, min(100.0, total))


# ── BotPersonality ABC ───────────────────────────────────────────────────────


class BotPersonality(ABC):
    """Industry-agnostic bot personality contract.

    Subclass this ABC to define a complete personality for a specific
    industry and bot type (e.g. real estate lead bot, dental qualifier).
    Register implementations via ``BotPersonalityRegistry.register()``.
    """

    def __init__(self, industry: str, bot_type: str, tone: str = "consultative") -> None:
        self.industry = industry
        self.bot_type = bot_type
        self.tone = tone

    @abstractmethod
    def get_qualification_questions(self) -> list[QualificationQuestion]:
        """Return ordered qualification questions for this personality."""

    @abstractmethod
    def get_intent_signals(self) -> dict[str, IntentMarkerSet]:
        """Return intent marker sets keyed by dimension name.

        Example keys: "motivation", "timeline", "urgency", "budget".
        """

    @abstractmethod
    def get_temperature_thresholds(self) -> TemperatureThresholds:
        """Return temperature classification thresholds."""

    @abstractmethod
    def get_handoff_triggers(self) -> list[HandoffTrigger]:
        """Return handoff trigger definitions for cross-bot routing."""

    @abstractmethod
    def get_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        """Render the system prompt for this personality.

        Args:
            context: Optional template variables (lead_name, tone_mode, etc.).
        """

    @abstractmethod
    def get_scoring_weights(self) -> ScoringWeights:
        """Return dimension weights for overall score calculation."""

    @abstractmethod
    def get_tone_instructions(self) -> dict[str, str]:
        """Return tone instructions keyed by tone name.

        Example: {"consultative": "Be helpful...", "direct": "Get to the point..."}
        """

    @abstractmethod
    def get_journey_stages(self) -> list[str]:
        """Return ordered list of customer journey stages.

        Example: ["qualification", "evaluation", "decision", "closed"]
        """

    @abstractmethod
    def get_stall_responses(self) -> dict[str, list[str]]:
        """Return stall-type-specific response templates.

        Keys are stall types (e.g. "thinking", "competitor", "price"),
        values are lists of response options to rotate through.
        """

    # ── Concrete helper methods ──────────────────────────────────────────

    def classify_temperature(self, score: float) -> str:
        """Classify a lead score into a temperature label."""
        return self.get_temperature_thresholds().classify(score)

    def compute_overall_score(self, dimension_scores: dict[str, float]) -> float:
        """Compute the weighted overall lead score."""
        return self.get_scoring_weights().compute(dimension_scores)

    def determine_next_step(self, dimension_scores: dict[str, float]) -> str:
        """Suggest the next qualification step based on weakest dimension.

        Returns the dimension name with the lowest score, indicating
        where to focus the next question.
        """
        if not dimension_scores:
            return "qualification"
        weakest = min(dimension_scores, key=lambda k: dimension_scores[k])
        return weakest

    def match_handoff(self, text: str) -> HandoffTrigger | None:
        """Check if text matches any handoff trigger phrases.

        Returns the first matching HandoffTrigger, or None.
        """
        text_lower = text.lower()
        for trigger in self.get_handoff_triggers():
            for phrase in trigger.trigger_phrases:
                if phrase.lower() in text_lower:
                    return trigger
        return None


# ── Registry ─────────────────────────────────────────────────────────────────


class BotPersonalityRegistry:
    """Registry for industry-specific personality implementations.

    Usage::

        @BotPersonalityRegistry.register("real_estate", "lead")
        class RealEstateLeadPersonality(BotPersonality):
            ...

        # Lookup
        cls = BotPersonalityRegistry.get("real_estate", "lead")
        personality = cls(industry="real_estate", bot_type="lead")
    """

    _registry: dict[tuple[str, str], type[BotPersonality]] = {}

    @classmethod
    def register(cls, industry: str, bot_type: str = "*") -> type[BotPersonality] | Any:
        """Register a personality class, usable as a decorator.

        Args:
            industry: Industry identifier (e.g. "real_estate", "dental").
            bot_type: Bot type (e.g. "lead", "buyer", "seller").
                      Use "*" for a fallback that matches any bot type.
        """

        def decorator(personality_cls: type[BotPersonality]) -> type[BotPersonality]:
            cls._registry[(industry, bot_type)] = personality_cls
            return personality_cls

        return decorator

    @classmethod
    def get(cls, industry: str, bot_type: str) -> type[BotPersonality]:
        """Look up a registered personality class.

        Tries exact match first, then falls back to wildcard bot_type.

        Raises:
            KeyError: If no personality is registered for the given combination.
        """
        key = (industry, bot_type)
        if key in cls._registry:
            return cls._registry[key]
        wildcard = (industry, "*")
        if wildcard in cls._registry:
            return cls._registry[wildcard]
        raise KeyError(
            f"No personality registered for industry={industry!r}, "
            f"bot_type={bot_type!r}. "
            f"Available: {cls.list_registered()}"
        )

    @classmethod
    def list_industries(cls) -> list[str]:
        """Return unique industry names with registered personalities."""
        return sorted({k[0] for k in cls._registry})

    @classmethod
    def list_registered(cls) -> list[tuple[str, str]]:
        """Return all registered (industry, bot_type) pairs."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Remove all registrations (primarily for testing)."""
        cls._registry.clear()
