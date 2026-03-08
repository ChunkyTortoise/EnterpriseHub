"""Unit tests for ObjectionHandler.handle_async() with Claude fallback.

Tests the async path: pattern match first (fast), Claude classification on miss.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.agents.sdr.objection_handler import ObjectionHandler, ObjectionResult

pytestmark = pytest.mark.unit


def _mock_llm(content: str) -> MagicMock:
    """Build a mock LLMClient whose agenerate returns the given content."""
    llm = MagicMock()
    response = MagicMock()
    response.content = content
    llm.agenerate = AsyncMock(return_value=response)
    return llm


# ---- fast path: pattern match hits, no Claude call ----


@pytest.mark.asyncio
async def test_handle_async_pattern_match_skips_claude():
    llm = _mock_llm('{"objection_type": "timing"}')
    handler = ObjectionHandler(llm_client=llm)

    result = await handler.handle_async("not interested in anything", contact_id="c1")

    assert result.objection_type == "not_interested"
    assert result.should_opt_out is True
    # LLM should NOT be called — pattern match was sufficient
    llm.agenerate.assert_not_awaited()


# ---- slow path: no pattern match, Claude classifies ----


@pytest.mark.asyncio
async def test_handle_async_calls_claude_when_no_pattern_match():
    """Claude classifies when pattern match misses; llm_client passed as method arg."""
    llm = _mock_llm('{"objection_type": "timing"}')
    handler = ObjectionHandler()  # no constructor llm

    result = await handler.handle_async(
        "we might think about it down the road", contact_id="c2", llm_client=llm
    )

    assert result.objection_type == "timing"
    assert result.strategy == "nurture_pause"
    assert result.should_pause is True
    llm.agenerate.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_async_claude_returns_none_for_neutral():
    llm = _mock_llm('{"objection_type": "none"}')
    handler = ObjectionHandler(llm_client=llm)

    result = await handler.handle_async("thanks for reaching out", contact_id="c3")

    assert result.objection_type is None
    assert result.strategy == "qualify"
    assert result.should_opt_out is False


# ---- error handling ----


@pytest.mark.asyncio
async def test_handle_async_claude_error_returns_no_objection():
    llm = MagicMock()
    llm.agenerate = AsyncMock(side_effect=RuntimeError("LLM down"))
    handler = ObjectionHandler(llm_client=llm)

    result = await handler.handle_async("something ambiguous here", contact_id="c4")

    assert result.objection_type is None
    assert result.strategy == "qualify"


@pytest.mark.asyncio
async def test_handle_async_no_llm_client_returns_no_objection():
    handler = ObjectionHandler(llm_client=None)

    result = await handler.handle_async("something ambiguous here", contact_id="c5")

    assert result.objection_type is None
    assert result.strategy == "qualify"
