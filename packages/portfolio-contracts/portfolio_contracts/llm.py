"""LLM provider contracts — shared across all portfolio products."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    OPENROUTER = "openrouter"
    MOCK = "mock"


class TokenUsage(BaseModel):
    """Token consumption for a single LLM call."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class CostEstimate(BaseModel):
    """Cost breakdown for a single LLM call."""

    input_cost: float = 0.0
    output_cost: float = 0.0
    currency: str = "USD"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_cost(self) -> float:
        return self.input_cost + self.output_cost


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str
    provider: LLMProvider
    model: str
    usage: TokenUsage | None = None
    cost: CostEstimate | None = None
    finish_reason: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    elapsed_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
