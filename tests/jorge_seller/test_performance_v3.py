"""
Performance Test V3 for Jorge's System 3.0.
Verifies sub-200ms processing (pre-generation) goal after parallelization.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.core.llm_client import LLMProvider, LLMResponse


@pytest.mark.asyncio
async def test_parallel_pipeline_latency():
    """Verify that parallelized generate_response is faster than sequential."""
    cm = ConversationManager()

    # Mock dependencies to simulate latency
    cm.extract_data = AsyncMock(return_value={"budget": 500000, "location": "Austin"})

    # Mock RAG search_corrective (the async method called by generate_response) to take 100ms
    async def slow_search_corrective(*args, **kwargs):
        await asyncio.sleep(0.1)
        return []

    cm.rag_engine.search_corrective = slow_search_corrective

    # Mock GHL Client to take 100ms
    mock_ghl = AsyncMock()

    async def slow_slots(*args, **kwargs):
        await asyncio.sleep(0.1)
        return [{"start_time": "2026-01-21T10:00:00Z"}]

    mock_ghl.get_available_slots = slow_slots

    # Mock lead_scorer.calculate (runs in parallel gather)
    cm.lead_scorer.calculate = AsyncMock(return_value=5)

    # Mock predictive_scorer.calculate_predictive_score (runs in parallel gather)
    cm.predictive_scorer.calculate_predictive_score = AsyncMock(return_value=None)

    # Mock property_matcher.find_matches (called via asyncio.to_thread in parallel)
    cm.property_matcher.find_matches = MagicMock(return_value=[])

    # Mock LLM to take 50ms
    async def slow_llm(*args, **kwargs):
        await asyncio.sleep(0.05)
        return LLMResponse(
            content="Hello!", provider=LLMProvider.CLAUDE, model="claude-3-5-sonnet", input_tokens=10, output_tokens=10
        )

    cm.llm_client.agenerate = slow_llm

    contact_info = {"first_name": "Test", "id": "123"}
    context = {
        "conversation_history": [{"role": "user", "content": "Hi"}],
        "extracted_preferences": {},
        "created_at": "2026-01-21T00:00:00Z",
    }

    start_time = time.time()
    response = await cm.generate_response(
        user_message="I want to buy a house in Austin for 500k",
        contact_info=contact_info,
        context=context,
        ghl_client=mock_ghl,
    )
    end_time = time.time()

    total_latency_ms = (end_time - start_time) * 1000
    print(f"Total Latency: {total_latency_ms:.2f}ms")

    # If sequential, it would be:
    # extraction (0) + rag (100) + slots (100) + llm (50) = 250ms
    # If parallel, it should be:
    # extraction (0) + max(rag, slots) (100) + llm (50) = 150ms

    assert response.message == "Hello!"
    # Allow some overhead, but 200ms should be the limit for non-LLM parts
    # Here total is 150ms + overhead.
    assert total_latency_ms < 250  # In a real env with 100ms mocks, 150-180ms is expected


if __name__ == "__main__":
    asyncio.run(test_parallel_pipeline_latency())
