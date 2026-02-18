"""Regression tests for buyer response generator API contract fixes."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator


@pytest.mark.asyncio
async def test_generate_buyer_response_uses_analyze_sentiment_api():
    """Regression: response generation should call analyze_sentiment (not analyze_message)."""
    sentiment_result = SimpleNamespace(
        sentiment=SimpleNamespace(value="neutral"),
        confidence=0.88,
        escalation_required=SimpleNamespace(value="none"),
    )

    sentiment_service = MagicMock()
    sentiment_service.analyze_sentiment = AsyncMock(return_value=sentiment_result)
    sentiment_service.get_response_tone_adjustment = MagicMock(return_value={"tone": "professional", "pace": "normal"})

    claude = MagicMock()
    claude.generate_response = AsyncMock(return_value={"content": "I can help you find a good fit."})

    generator = ResponseGenerator(claude=claude, sentiment_service=sentiment_service)

    state = {
        "buyer_id": "buyer_123",
        "conversation_history": [
            {"role": "assistant", "content": "What budget are you targeting?"},
            {"role": "user", "content": "Around 700k and I want to move quickly."},
        ],
        "current_qualification_step": "qualify_budget",
        "financial_readiness_score": 72,
    }

    result = await generator.generate_buyer_response(state)

    sentiment_service.analyze_sentiment.assert_awaited_once_with("Around 700k and I want to move quickly.")
    assert result["response_content"] == "I can help you find a good fit."
