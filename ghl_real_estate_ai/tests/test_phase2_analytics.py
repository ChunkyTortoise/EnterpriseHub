import pytest
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.services.memory_service import MemoryService
import os
import shutil

@pytest.fixture
def analytics_service():
    test_dir = "data/test_analytics"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    service = AnalyticsService(analytics_dir=test_dir)
    yield service
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_analytics_tracking(analytics_service):
    location_id = "test_loc_123"
    await analytics_service.track_event("message_received", location_id, "contact_1", {"msg": "hello"})
    await analytics_service.track_event("lead_scored", location_id, "contact_1", {"score": 80})
    
    events = await analytics_service.get_events(location_id)
    assert len(events) == 2
    assert events[0]["event_type"] == "message_received"
    assert events[1]["data"]["score"] == 80

@pytest.mark.asyncio
async def test_analytics_summary(analytics_service):
    location_id = "test_loc_summary"
    await analytics_service.track_event("message_received", location_id, "c1")
    await analytics_service.track_event("message_sent", location_id, "c1")
    await analytics_service.track_event("lead_scored", location_id, "c1", {"score": 90})
    
    summary = await analytics_service.get_daily_summary(location_id)
    assert summary["total_messages"] == 2
    assert summary["hot_leads"] == 1
    assert summary["avg_lead_score"] == 90.0
    assert summary["active_contacts_count"] == 1

@pytest.mark.asyncio
async def test_enhanced_memory_returning_lead():
    # Mock LLM and RAG before instantiating ConversationManager
    with patch("core.conversation_manager.LLMClient"), \
         patch("core.conversation_manager.RAGEngine"):
        
        manager = ConversationManager()
        memory = MemoryService(storage_type="file")
        contact_id = "returning_contact_789"
        location_id = "loc_returning"
        
        # Mock a previous interaction 2 days ago
        past_date = (datetime.utcnow() - timedelta(days=2)).isoformat()
        context = {
            "contact_id": contact_id,
            "location_id": location_id,
            "conversation_history": [],
            "extracted_preferences": {"budget": 500000},
            "last_interaction_at": past_date,
            "updated_at": past_date,
            "previous_sessions_summary": ""
        }
        await memory.save_context(contact_id, context, location_id=location_id)
        
        # Get context via manager
        retrieved_context = await manager.get_context(contact_id, location_id=location_id)
        
        assert retrieved_context.get("is_returning_lead") is True
        assert retrieved_context.get("hours_since_last_interaction") > 47
        assert retrieved_context["extracted_preferences"]["budget"] == 500000

        # Cleanup
        await memory.clear_context(contact_id)
