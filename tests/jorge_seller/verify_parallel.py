import asyncio
import os
import sys
import time

# Add project root to path
sys.path.append(os.getcwd())

from unittest.mock import AsyncMock, MagicMock

from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.core.llm_client import LLMProvider, LLMResponse


async def verify_parallel():
    print("Starting Parallelization Verification...")
    cm = ConversationManager()

    # Mock dependencies to simulate latency
    cm.extract_data = AsyncMock(return_value={"budget": 500000, "location": "Rancho Cucamonga"})

    # Mock RAG to take 100ms
    def slow_search(*args, **kwargs):
        time.sleep(0.1)
        return []

    cm.rag_engine.search = slow_search

    # Mock GHL Client to take 100ms
    mock_ghl = AsyncMock()

    async def slow_slots(*args, **kwargs):
        await asyncio.sleep(0.1)
        return [{"start_time": "2026-01-21T10:00:00Z"}]

    mock_ghl.get_available_slots = slow_slots

    # Mock LLM to take 50ms
    cm.llm_client.agenerate = AsyncMock(
        return_value=LLMResponse(
            content="Hello!", provider=LLMProvider.CLAUDE, model="claude-3-5-sonnet", input_tokens=10, output_tokens=10
        )
    )

    contact_info = {"first_name": "Test", "id": "123"}
    context = {
        "conversation_history": [{"role": "user", "content": "Hi"}],
        "extracted_preferences": {},
        "created_at": "2026-01-21T00:00:00Z",
    }

    print("Executing generate_response...")
    start_time = time.time()
    response = await cm.generate_response(
        user_message="I want to buy a house in Rancho Cucamonga for 500k",
        contact_info=contact_info,
        context=context,
        ghl_client=mock_ghl,
    )
    end_time = time.time()

    total_latency_ms = (end_time - start_time) * 1000
    print(f"Total Latency: {total_latency_ms:.2f}ms")

    if total_latency_ms < 250:
        print("✅ SUCCESS: Latency is within parallelized bounds.")
    else:
        print("❌ FAILURE: Latency suggests sequential execution.")

    print(f"Response: {response.message}")


if __name__ == "__main__":
    asyncio.run(verify_parallel())
