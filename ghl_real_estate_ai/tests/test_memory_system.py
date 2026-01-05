import asyncio
import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Set dummy env vars for Pydantic Settings validation
os.environ["ANTHROPIC_API_KEY"] = "sk-test-key"
os.environ["GHL_API_KEY"] = "ghl-test-key"
os.environ["GHL_LOCATION_ID"] = "loc-test-123"

import sys
sys.path.append(os.path.join(os.getcwd(), "ghl-real-estate-ai"))

from ghl_real_estate_ai.core.conversation_manager import ConversationManager, AIResponse
from ghl_real_estate_ai.services.memory_service import MemoryService

@pytest.mark.asyncio
async def test_memory_persistence():
    print("🚀 Testing Memory Persistence...")
    
    # 1. Setup clean test environment
    test_contact_id = "test_contact_123"
    memory_dir = Path("data/memory")
    if memory_dir.exists():
        shutil.rmtree(memory_dir)
    
    # 2. Initialize ConversationManager
    # Mock LLMClient to avoid API calls
    cm = ConversationManager()
    cm.llm_client = AsyncMock()
    cm.llm_client.agenerate.return_value = MagicMock(
        content="Hello! I remember you.",
        provider="claude",
        model="test-model"
    )
    
    # Mock RAG engine to avoid search issues
    cm.rag_engine = MagicMock()
    cm.rag_engine.search.return_value = []
    
    # 3. First interaction
    print("--- Turn 1 ---")
    user_msg_1 = "Hi, my name is John and I'm looking for a 3-bedroom house in Austin."
    
    # We need to mock extract_data too or it will try to call LLM
    cm.extract_data = AsyncMock(return_value={
        "bedrooms": 3,
        "location": "Austin"
    })
    
    response = await cm.generate_response(
        user_message=user_msg_1,
        contact_info={"first_name": "John"},
        context=await cm.get_context(test_contact_id)
    )
    
    await cm.update_context(
        contact_id=test_contact_id,
        user_message=user_msg_1,
        ai_response=response.message,
        extracted_data=response.extracted_data
    )
    
    # 4. Verify file exists
    file_path = memory_dir / f"{test_contact_id}.json"
    assert file_path.exists(), "Memory file was not created!"
    print(f"✅ Memory file created: {file_path}")
    
    # 5. Simulate new session (re-initialize cm)
    print("--- Simulating New Session ---")
    cm2 = ConversationManager()
    cm2.llm_client = AsyncMock()
    cm2.llm_client.agenerate.return_value = MagicMock(
        content="I see you're still looking for that house in Austin!",
        provider="claude",
        model="test-model"
    )
    cm2.rag_engine = MagicMock()
    cm2.rag_engine.search.return_value = []
    cm2.extract_data = AsyncMock(return_value={})
    
    # 6. Get context in new session
    context = await cm2.get_context(test_contact_id)
    assert len(context["conversation_history"]) == 2, f"History lost! Found {len(context['conversation_history'])} messages."
    assert context["extracted_preferences"]["bedrooms"] == 3, "Preferences lost!"
    print("✅ History and preferences successfully reloaded from file.")
    
    # 7. Second interaction
    user_msg_2 = "Actually, my budget is $500,000."
    
    response2 = await cm2.generate_response(
        user_message=user_msg_2,
        contact_info={"first_name": "John"},
        context=context
    )
    
    # Check if history was passed to LLMClient
    called_history = cm2.llm_client.agenerate.call_args.kwargs.get("history")
    assert len(called_history) == 2, f"History not passed to LLM! Passed {len(called_history)} messages."
    assert called_history[0]["content"] == user_msg_1, "First user message missing from history."
    print("✅ Full history passed to LLM Client.")
    
    await cm2.update_context(
        contact_id=test_contact_id,
        user_message=user_msg_2,
        ai_response=response2.message,
        extracted_data={"budget": 500000}
    )
    
    # 8. Final verification
    context_final = await cm2.get_context(test_contact_id)
    assert len(context_final["conversation_history"]) == 4, "Final history length incorrect."
    assert context_final["extracted_preferences"]["budget"] == 500000, "New preference not saved."
    print("✅ Memory system fully functional!")

if __name__ == "__main__":
    asyncio.run(test_memory_persistence())
