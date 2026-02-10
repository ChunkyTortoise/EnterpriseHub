import pytest

from conversation_manager import ConversationManager
from jorge_engines_optimized import (
    JorgeLeadEngineOptimized,
    JorgeSellerEngineOptimized,
    OptimizedResponse,
)


class DummyGHLClient:
    pass


@pytest.mark.asyncio
async def test_seller_context_update_persists_fields(tmp_path):
    manager = ConversationManager(storage_dir=str(tmp_path))
    engine = JorgeSellerEngineOptimized(manager, DummyGHLClient())

    response = OptimizedResponse(
        message="I can make you an offer today.",
        confidence_score=0.91,
        tone_quality="authentic_jorge",
        business_context={},
    )
    analysis = {
        "motivation_score": 0.8,
        "urgency_score": 0.65,
        "motivation_type": "financial",
    }

    await engine._update_seller_context(
        contact_id="seller-1",
        location_id="loc-1",
        user_message="I need to sell quickly.",
        response=response,
        analysis=analysis,
        questions_answered=1,
    )

    context = await manager.get_context("seller-1", "loc-1")
    assert context["seller_questions_answered"] == 2
    assert context["seller_temperature"] in {"hot", "warm", "cold"}
    assert len(context["conversation_history"]) == 1
    assert context["conversation_history"][0]["user_message"] == "I need to sell quickly."
    assert context["conversation_history"][0]["ai_response"] == "I can make you an offer today."


@pytest.mark.asyncio
async def test_lead_context_update_persists_fields(tmp_path):
    manager = ConversationManager(storage_dir=str(tmp_path))
    engine = JorgeLeadEngineOptimized(manager, DummyGHLClient())

    response = OptimizedResponse(
        message="Great, let's find you the right home.",
        confidence_score=0.87,
        tone_quality="professional_helpful",
        business_context={},
    )
    lead_data = {
        "budget_max": 650000,
        "timeline": "30_days",
        "financing_status": "pre_approved",
        "location": ["Day Creek"],
    }

    await engine._safe_update_context(
        contact_id="lead-1",
        location_id="loc-1",
        user_message="Budget is $650k and pre-approved.",
        response=response,
        lead_data=lead_data,
        lead_score=85.0,
    )

    context = await manager.get_context("lead-1", "loc-1")
    assert context["lead_score"] == 85.0
    assert context["lead_temperature"] == "hot"
    assert context["budget_max"] == 650000
    assert len(context["conversation_history"]) == 1


@pytest.mark.asyncio
async def test_two_turn_seller_conversation_increments_question_count(tmp_path):
    manager = ConversationManager(storage_dir=str(tmp_path))
    engine = JorgeSellerEngineOptimized(manager, DummyGHLClient())

    first = await engine.process_seller_response(
        contact_id="seller-2",
        user_message="Thinking about selling.",
        location_id="loc-2",
    )
    second = await engine.process_seller_response(
        contact_id="seller-2",
        user_message="It needs some repairs and I need to move soon.",
        location_id="loc-2",
    )

    context = await manager.get_context("seller-2", "loc-2")
    assert first["questions_answered"] == 1
    assert second["questions_answered"] == 2
    assert context["seller_questions_answered"] == 2
    assert len(context["conversation_history"]) == 2
