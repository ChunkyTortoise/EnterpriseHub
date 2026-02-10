"""
Tests for Property Recommendation Integration (Phase 3)
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set dummy env vars
os.environ["ANTHROPIC_API_KEY"] = "sk-test-key"
os.environ["GHL_API_KEY"] = "ghl-test-key"
os.environ["GHL_LOCATION_ID"] = "loc-test-123"

from ghl_real_estate_ai.core.conversation_manager import ConversationManager

@pytest.mark.integration


@pytest.mark.asyncio
async def test_property_recommendation_for_warm_lead():
    """Test that properties are recommended when lead score is 2 or higher."""
    cm = ConversationManager()

    # Mock LLM and RAG
    cm.llm_client.agenerate = AsyncMock(return_value=MagicMock(content="I found some houses for you."))
    cm.rag_engine.search = MagicMock(return_value=[])

    # Warm lead context (score should be 2 because location and budget are provided)
    context = {
        "conversation_history": [
            {"role": "user", "content": "I want a house in Austin"},
            {"role": "assistant", "content": "What is your budget?"},
        ],
        "extracted_preferences": {"location": "Austin", "budget": 500000},
        "created_at": datetime.utcnow().isoformat(),
    }

    # Generate response
    await cm.generate_response(
        user_message="My budget is $500k.", contact_info={"first_name": "Test", "id": "contact_123"}, context=context
    )

    # Verify properties were included in system prompt
    system_prompt = cm.llm_client.agenerate.call_args.kwargs["system_prompt"]
    assert "PROPERTY RECOMMENDATIONS" in system_prompt
    assert "Austin" in system_prompt or "Duval" in system_prompt