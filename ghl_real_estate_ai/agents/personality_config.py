"""
YAML-Backed Personality Configuration

Pydantic schema for loading bot personality definitions from YAML files.
Creates concrete BotPersonality implementations from declarative config,
enabling non-code personality customization.

Author: Claude Code Assistant
Created: 2026-02-09
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from ghl_real_estate_ai.agents.bot_personality import (
    BotPersonality,
    BotPersonalityRegistry,
    HandoffTrigger,
    IntentMarkerSet,
    QualificationQuestion,
    ScoringWeights,
    TemperatureThresholds,
)

# ── Pydantic Sub-Schemas ─────────────────────────────────────────────────────


class IntentMarkerConfig(BaseModel):
    """YAML schema for graduated intent markers."""

    high: list[str] = Field(default_factory=list)
    medium: list[str] = Field(default_factory=list)
    low: list[str] = Field(default_factory=list)

    def to_marker_set(self) -> IntentMarkerSet:
        return IntentMarkerSet(high=self.high, medium=self.medium, low=self.low)


class QualificationQuestionConfig(BaseModel):
    """YAML schema for a single qualification question."""

    text: str
    category: str
    priority: int = 0
    follow_ups: list[str] = Field(default_factory=list)

    def to_question(self) -> QualificationQuestion:
        return QualificationQuestion(
            text=self.text,
            category=self.category,
            priority=self.priority,
            follow_ups=self.follow_ups,
        )


class HandoffTriggerConfig(BaseModel):
    """YAML schema for a handoff trigger definition."""

    target_bot: str
    confidence_threshold: float = 0.7
    trigger_phrases: list[str] = Field(default_factory=list)
    description: str = ""

    def to_trigger(self) -> HandoffTrigger:
        return HandoffTrigger(
            target_bot=self.target_bot,
            confidence_threshold=self.confidence_threshold,
            trigger_phrases=self.trigger_phrases,
            description=self.description,
        )


class TemperatureConfig(BaseModel):
    """YAML schema for temperature thresholds."""

    hot: float = 75.0
    warm: float = 50.0
    lukewarm: float = 25.0

    def to_thresholds(self) -> TemperatureThresholds:
        return TemperatureThresholds(
            hot=self.hot, warm=self.warm, lukewarm=self.lukewarm
        )


# ── Root Personality Config ──────────────────────────────────────────────────


class PersonalityConfig(BaseModel):
    """Pydantic schema for a complete YAML personality definition.

    Example YAML::

        industry: real_estate
        bot_type: lead
        tone: consultative
        name: Jorge Salas
        role: Real Estate Professional
        system_prompt_template: |
          You are {name}, a {role}. ...
        qualification_questions:
          - text: "What's your timeline?"
            category: timeline
            priority: 1
        intent_signals:
          motivation:
            high: ["must sell", "relocating"]
            medium: ["thinking about it"]
            low: ["just curious"]
        temperature_thresholds:
          hot: 75
          warm: 50
          lukewarm: 25
        scoring_weights:
          motivation: 0.35
          timeline: 0.30
          condition: 0.20
          price: 0.15
        handoff_triggers:
          - target_bot: buyer
            confidence_threshold: 0.7
            trigger_phrases: ["want to buy", "pre-approval"]
    """

    industry: str
    bot_type: str = "lead"
    tone: str = "consultative"
    name: str = ""
    role: str = ""
    approach: str = ""
    core_values: list[str] = Field(default_factory=list)
    system_prompt_template: str = ""
    qualification_questions: list[QualificationQuestionConfig] = Field(
        default_factory=list
    )
    intent_signals: dict[str, IntentMarkerConfig] = Field(default_factory=dict)
    temperature_thresholds: TemperatureConfig = Field(
        default_factory=TemperatureConfig
    )
    scoring_weights: dict[str, float] = Field(default_factory=dict)
    handoff_triggers: list[HandoffTriggerConfig] = Field(default_factory=list)
    tone_instructions: dict[str, str] = Field(default_factory=dict)
    journey_stages: list[str] = Field(default_factory=list)
    stall_responses: dict[str, list[str]] = Field(default_factory=dict)

    @field_validator("scoring_weights")
    @classmethod
    def validate_weights_sum(cls, v: dict[str, float]) -> dict[str, float]:
        if v:
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(
                    f"scoring_weights must sum to 1.0, got {total:.3f}"
                )
        return v

    @classmethod
    def from_yaml(cls, path: str | Path) -> PersonalityConfig:
        """Load a PersonalityConfig from a YAML file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the YAML is invalid or fails validation.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Personality config not found: {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Expected YAML mapping in {path}")

        return cls(**raw)

    def to_personality(self) -> YAMLBotPersonality:
        """Build a concrete BotPersonality from this config."""
        return YAMLBotPersonality(
            industry=self.industry,
            bot_type=self.bot_type,
            tone=self.tone,
            config=self,
        )

    def register(self) -> type[BotPersonality]:
        """Create, register, and return the personality class.

        Registers a factory-backed personality under
        (industry, bot_type) in the global registry.
        """
        self.to_personality()

        # Create a thin wrapper class for registry storage
        config_ref = self

        class _ConfigBackedPersonality(YAMLBotPersonality):
            def __init__(self, **kwargs: Any) -> None:
                super().__init__(
                    industry=config_ref.industry,
                    bot_type=config_ref.bot_type,
                    tone=config_ref.tone,
                    config=config_ref,
                )

        _ConfigBackedPersonality.__name__ = (
            f"{self.industry.title()}{self.bot_type.title()}Personality"
        )
        _ConfigBackedPersonality.__qualname__ = _ConfigBackedPersonality.__name__

        BotPersonalityRegistry.register(self.industry, self.bot_type)(
            _ConfigBackedPersonality
        )
        return _ConfigBackedPersonality


# ── YAML-Backed BotPersonality Implementation ────────────────────────────────


class YAMLBotPersonality(BotPersonality):
    """Concrete BotPersonality backed by a PersonalityConfig (from YAML)."""

    def __init__(
        self,
        industry: str,
        bot_type: str,
        tone: str,
        config: PersonalityConfig,
    ) -> None:
        super().__init__(industry=industry, bot_type=bot_type, tone=tone)
        self._config = config

    def get_qualification_questions(self) -> list[QualificationQuestion]:
        return [q.to_question() for q in self._config.qualification_questions]

    def get_intent_signals(self) -> dict[str, IntentMarkerSet]:
        return {k: v.to_marker_set() for k, v in self._config.intent_signals.items()}

    def get_temperature_thresholds(self) -> TemperatureThresholds:
        return self._config.temperature_thresholds.to_thresholds()

    def get_handoff_triggers(self) -> list[HandoffTrigger]:
        return [t.to_trigger() for t in self._config.handoff_triggers]

    def get_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        template = self._config.system_prompt_template
        if not template:
            return ""
        ctx = {
            "name": self._config.name,
            "role": self._config.role,
            "approach": self._config.approach,
            "tone": self.tone,
            **(context or {}),
        }
        return template.format(**ctx)

    def get_scoring_weights(self) -> ScoringWeights:
        return ScoringWeights(weights=dict(self._config.scoring_weights))

    def get_tone_instructions(self) -> dict[str, str]:
        return dict(self._config.tone_instructions)

    def get_journey_stages(self) -> list[str]:
        return list(self._config.journey_stages)

    def get_stall_responses(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._config.stall_responses.items()}
