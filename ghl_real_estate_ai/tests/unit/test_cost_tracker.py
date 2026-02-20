"""Unit tests for the API cost tracker service."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.core.llm_client import LLMProvider, LLMResponse
from ghl_real_estate_ai.services.jorge.cost_tracker import (
    CostTracker,
    _calculate_cost,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(
    input_tokens=None,
    output_tokens=None,
    cache_creation_input_tokens=None,
    cache_read_input_tokens=None,
    model="claude-3-5-sonnet",
) -> LLMResponse:
    return LLMResponse(
        content="test",
        provider=LLMProvider.CLAUDE,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
        cache_read_input_tokens=cache_read_input_tokens,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_cost_calculation_input_only():
    """Input-only cost: 1M tokens * $3.00/MTok = $3.00."""
    cost = _calculate_cost(input_tokens=1_000_000, output_tokens=0, cache_read_tokens=0)
    assert cost == pytest.approx(3.00)


@pytest.mark.unit
def test_cost_calculation_with_cache_read():
    """Cache read at $0.30/MTok blended with regular input and output."""
    cost = _calculate_cost(
        input_tokens=500_000,
        output_tokens=100_000,
        cache_read_tokens=200_000,
    )
    expected = (
        500_000 * 3.00 / 1_000_000   # $1.50
        + 100_000 * 15.00 / 1_000_000  # $1.50
        + 200_000 * 0.30 / 1_000_000   # $0.06
    )
    assert cost == pytest.approx(expected)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_record_usage_inserts_row():
    """record_usage should call execute_command with correct SQL and params."""
    mock_db = MagicMock()
    mock_db.execute_command = AsyncMock(return_value="INSERT 0 1")

    tracker = CostTracker()
    resp = _make_response(input_tokens=1000, output_tokens=200)

    with patch(
        "ghl_real_estate_ai.services.jorge.cost_tracker.get_db_manager",
        return_value=mock_db,
    ):
        await tracker.record_usage("conv-1", "contact-1", "seller", resp)

    mock_db.execute_command.assert_called_once()
    call_args = mock_db.execute_command.call_args
    # Positional args after SQL: conversation_id, contact_id, bot_type, model,
    # input_tokens, output_tokens, cache_creation, cache_read, cost
    assert call_args[0][1] == "conv-1"
    assert call_args[0][2] == "contact-1"
    assert call_args[0][3] == "seller"
    assert call_args[0][5] == 1000  # input_tokens
    assert call_args[0][6] == 200   # output_tokens


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_month_total_aggregates():
    """get_month_total should return aggregated dict from DB row."""
    mock_row = {
        "input_tokens": 50000,
        "output_tokens": 12000,
        "cost_usd": 0.33,
        "call_count": 15,
    }
    mock_db = MagicMock()
    mock_db.execute_fetchrow = AsyncMock(return_value=mock_row)

    tracker = CostTracker()

    with patch(
        "ghl_real_estate_ai.services.jorge.cost_tracker.get_db_manager",
        return_value=mock_db,
    ):
        result = await tracker.get_month_total(2026, 2)

    assert result["input_tokens"] == 50000
    assert result["output_tokens"] == 12000
    assert result["cost_usd"] == pytest.approx(0.33)
    assert result["call_count"] == 15


@pytest.mark.unit
@pytest.mark.asyncio
async def test_zero_tokens_no_crash():
    """LLMResponse with all None tokens should not crash record_usage."""
    mock_db = MagicMock()
    mock_db.execute_command = AsyncMock(return_value="INSERT 0 1")

    tracker = CostTracker()
    resp = _make_response()  # all token fields None

    with patch(
        "ghl_real_estate_ai.services.jorge.cost_tracker.get_db_manager",
        return_value=mock_db,
    ):
        # Should not raise
        await tracker.record_usage("conv-x", None, "lead", resp)

    mock_db.execute_command.assert_called_once()
    call_args = mock_db.execute_command.call_args
    # input_tokens and output_tokens should be 0 (None -> 0)
    assert call_args[0][5] == 0
    assert call_args[0][6] == 0
    # estimated_cost_usd should be 0.0
    assert call_args[0][9] == pytest.approx(0.0)
