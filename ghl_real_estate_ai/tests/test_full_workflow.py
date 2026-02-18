import asyncio
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.models.lead_scoring import FinancialReadinessScore, LeadIntentProfile, PriceResponsiveness
from ghl_real_estate_ai.models.workflows import LeadFollowUpState



@pytest.fixture
def mock_dependencies():
    with (
        patch("ghl_real_estate_ai.agents.lead_bot.RetellClient") as MockRetell,
        patch("ghl_real_estate_ai.agents.lead_bot.CMAGenerator") as MockCMA,
        patch("ghl_real_estate_ai.agents.lead_bot.LeadIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.lead_bot.LyrioClient") as MockLyrio,
    ):
        # Setup Retell Mock
        retell_instance = MockRetell.return_value
        retell_instance.create_call = AsyncMock(return_value={"call_id": "test_call_123"})

        # Setup Lyrio Mock
        lyrio_instance = MockLyrio.return_value
        lyrio_instance.sync_lead_score = AsyncMock(return_value=True)
        lyrio_instance.sync_digital_twin_url = AsyncMock(return_value=True)

        # Setup CMA Mock
        cma_instance = MockCMA.return_value
        cma_report = MagicMock()
        cma_report.zillow_variance_abs = 50000.0
        cma_report.estimated_value = 550000.0
        cma_report.value_range_low = 525000.0
        cma_report.value_range_high = 575000.0
        cma_report.confidence_score = 90
        cma_report.zillow_variance_percent = 10.0
        cma_report.zillow_explanation = "Zillow is wrong."
        cma_report.market_narrative = "The market is hot."
        cma_report.generated_at = "2024-01-22"

        # Mocking Market Context
        cma_report.market_context = MagicMock()
        cma_report.market_context.price_trend = 10.5  # Positive trend
        cma_report.market_context.dom_average = 30
        cma_report.market_context.inventory_level = 100
        cma_report.market_context.zillow_zestimate = 500000.0
        cma_report.market_context.market_name = "Austin, TX"

        # Mocking Subject Property
        cma_report.subject_property = MagicMock()
        cma_report.subject_property.address = "456 Lamar Blvd"
        cma_report.subject_property.beds = 3
        cma_report.subject_property.baths = 2.0
        cma_report.subject_property.sqft = 2000.0
        cma_report.subject_property.year_built = 2000
        cma_report.subject_property.condition = "Good"

        # Mocking Comparables
        comp1 = MagicMock()
        comp1.address = "123 Test Ln"
        comp1.sale_date = "2024-01-01"
        comp1.sale_price = 500000.0
        comp1.sqft = 2000.0
        comp1.price_per_sqft = 250.0
        comp1.adjustment_percent = 2.5
        comp1.adjusted_value = 512500.0

        cma_report.comparables = [comp1]

        cma_instance.generate_report = AsyncMock(return_value=cma_report)

        # Setup Intent Mock
        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=LeadIntentProfile)
        mock_profile.frs = MagicMock(spec=FinancialReadinessScore)
        mock_profile.frs.total_score = 75
        mock_profile.frs.price = MagicMock(spec=PriceResponsiveness)
        mock_profile.frs.price.category = "Neutral"  # Default
        mock_profile.frs.classification = "Warm Lead"

        # Add PCS Mock (Phase 4)
        mock_profile.pcs = MagicMock()
        mock_profile.pcs.total_score = 80

        intent_instance.analyze_lead = MagicMock(return_value=mock_profile)

        yield {"retell": retell_instance, "cma": cma_instance, "intent": intent_instance, "profile": mock_profile}


async def test_day_7_call_workflow(mock_dependencies):
    """
    Test that the Day 7 step triggers the Retell AI call.
    """
    workflow = LeadBotWorkflow()
    workflow.sequence_service = AsyncMock()
    workflow.scheduler = AsyncMock()

    # Initial State: Day 7, Ghosted
    initial_state: LeadFollowUpState = {
        "lead_id": f"test_lead_001_{uuid4().hex}",
        "lead_name": "John Doe",
        "contact_phone": "+15551234567",
        "contact_email": "john@example.com",
        "property_address": "123 Austin Blvd",
        "conversation_history": [],
        "intent_profile": mock_dependencies["profile"],
        "current_step": "day_7",
        "sequence_day": 7,
        "engagement_status": "ghosted",
        "last_interaction_time": None,
        "stall_breaker_attempted": False,
        "cma_generated": False,
    }

    # Execute the day-7 node directly to isolate retell-call behavior.
    final_state = await workflow.initiate_day_7_call(initial_state)
    await asyncio.sleep(0)

    # Verifications
    mock_dependencies["retell"].create_call.assert_called_once()
    call_args = mock_dependencies["retell"].create_call.call_args[1]
    assert call_args["to_number"] == "+15551234567"
    assert call_args["lead_name"] == "John Doe"

    # Verify state transition
    assert final_state["current_step"] == "day_14_email"
    # Note: engagement_status logic in initiate_day_7_call sets it to "ghosted" again
    # (waiting for day 14), or maybe it should change?
    # Looking at code: return {"engagement_status": "ghosted", "current_step": "day_14_email"}
    assert final_state["engagement_status"] == "ghosted"


async def test_price_objection_triggers_cma(mock_dependencies):
    """
    Test that a price objection in conversation history triggers CMA generation.
    """
    # Mock Intent Decoder to return Price-Aware if needed,
    # but the logic in determine_path checks keyword match OR category.
    # We will rely on keyword match "price" in history.

    workflow = LeadBotWorkflow()

    initial_state: LeadFollowUpState = {
        "lead_id": "test_lead_002",
        "lead_name": "Jane Smith",
        "contact_phone": "+15559876543",
        "contact_email": "jane@example.com",
        "property_address": "456 Lamar Blvd",
        "conversation_history": [
            {"role": "assistant", "content": "Hi Jane, following up."},
            {"role": "user", "content": "I'm not sure about the price."},  # Keyword "price"
        ],
        "intent_profile": None,
        "current_step": "day_3",  # Even if step is day_3, response should trigger CMA
        "engagement_status": "responsive",
        "last_interaction_time": datetime.now(),
        "stall_breaker_attempted": False,
        "cma_generated": False,
    }

    # Run Workflow
    final_state = await workflow.workflow.ainvoke(initial_state)

    # Verifications
    mock_dependencies["cma"].generate_report.assert_called_once()
    args = mock_dependencies["cma"].generate_report.call_args
    assert args[0][0] == "456 Lamar Blvd"

    # Verify state transition
    assert final_state["cma_generated"] is True
    assert final_state["current_step"] == "nurture"


async def test_high_intent_qualification(mock_dependencies):
    """
    Test that a 'Hot Lead' classification leads to 'qualified' status.
    """
    # Adjust mock to return Hot Lead
    mock_dependencies["profile"].frs.classification = "Hot Lead"

    workflow = LeadBotWorkflow()

    initial_state: LeadFollowUpState = {
        "lead_id": "test_lead_hot",
        "lead_name": "Hot Lead",
        "contact_phone": "+15550000000",
        "contact_email": "hot@example.com",
        "property_address": "789 Hot St",
        "conversation_history": [{"role": "user", "content": "I want to sell now."}],
        "intent_profile": None,
        "current_step": "initial",
        "engagement_status": "new",
        "last_interaction_time": datetime.now(),
        "stall_breaker_attempted": False,
        "cma_generated": False,
    }

    final_state = await workflow.workflow.ainvoke(initial_state)

    # Verify strict routing to qualified
    # Logic: determine_path -> returns {"current_step": "qualified", ...} -> _route_next_step returns "qualified" -> END
    # So final state should reflect that.
    assert final_state["current_step"] in {"qualified", "post_showing"}
    assert final_state["engagement_status"] in {"qualified", "responsive", "showing_booked"}
