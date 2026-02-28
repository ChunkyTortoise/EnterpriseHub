"""
Multi-turn smoke tests for buyer and seller bots.
Tests fixes for:
  - buyer bot repeating hot-path tour question on every turn
  - ai_valuation_price showing lead-pricing mock instead of seller's price_expectation
"""
from __future__ import annotations

import asyncio
import pytest
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock


# ── Seller smoke test via _StubConversationManager ─────────────────────────


class _StubMemoryService:
    async def save_context(self, *a: Any, **kw: Any) -> None:
        pass


class _StubConversationManager:
    def __init__(self) -> None:
        self.memory_service = _StubMemoryService()
        self._history: List[Dict[str, str]] = []
        self._seller_data: Dict[str, Any] = {}

    async def get_context(self, contact_id: str, location_id: str | None = None) -> Dict[str, Any]:
        return {
            "contact_id": contact_id,
            "location_id": location_id or "test",
            "conversation_history": list(self._history),
            "seller_preferences": dict(self._seller_data),
            "contact_name": "Test Lead",
            "closing_probability": 0.0,
            "active_ab_test": None,
            "last_ai_message_type": None,
            "is_returning_lead": False,
        }

    async def get_conversation_history(self, *a: Any, **kw: Any) -> List:
        return list(self._history)

    async def update_context(self, contact_id: str, user_message: str, ai_response: str,
                              *a: Any, **kw: Any) -> None:
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": ai_response})
        ed = kw.get("extracted_data")
        if ed and isinstance(ed, dict):
            self._seller_data.update(ed)

    async def extract_seller_data(self, user_message: str, current: Dict, *a: Any, **kw: Any) -> Dict:
        return current


class _StubGHLClient:
    async def apply_actions(self, *a: Any, **kw: Any) -> Dict:
        return {"success": True}

    async def add_tags(self, *a: Any, **kw: Any) -> Dict:
        return {"success": True}

    async def update_contact(self, *a: Any, **kw: Any) -> Dict:
        return {"success": True}


@pytest.mark.asyncio
async def test_seller_valuation_field_uses_price_expectation_not_lead_pricing() -> None:
    """
    _create_seller_actions must write seller's price_expectation to ai_valuation_price,
    not the lead-pricing mock value (which was previously showing as $4.2 or $2.0).
    Tests the exact change made to jorge_seller_engine._create_seller_actions.
    """
    from types import SimpleNamespace
    from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

    cm = _StubConversationManager()
    ghl = _StubGHLClient()
    engine = JorgeSellerEngine(cm, ghl)

    pricing_mock = SimpleNamespace(
        final_price=2.0,  # lead-pricing mock — should NOT appear in ai_valuation_price
        tier="hot",
        expected_roi=12.5,
        justification="test",
    )
    seller_data = {
        "price_expectation": "750,000",
        "motivation": "relocation",
        "timeline": "3 months",
        "property_condition": "Move-in Ready",
    }

    actions = await engine._create_seller_actions(
        contact_id="test",
        location_id="test",
        temperature="hot",
        seller_data=seller_data,
        pricing_result=pricing_mock,
    )

    valuation_actions = [a for a in actions if "valuation" in str(a.get("field", ""))]
    assert valuation_actions, "Expected an ai_valuation_price action"

    val = str(valuation_actions[0]["value"])
    assert "750" in val, (
        f"ai_valuation_price should use seller's price_expectation (750,000), got: {val}"
    )
    assert "2.0" not in val, (
        f"ai_valuation_price must NOT contain lead-pricing mock value 2.0, got: {val}"
    )


@pytest.mark.asyncio
async def test_seller_valuation_field_omitted_when_no_price_expectation() -> None:
    """When seller hasn't given a price yet, ai_valuation_price should not be written."""
    from types import SimpleNamespace
    from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

    cm = _StubConversationManager()
    ghl = _StubGHLClient()
    engine = JorgeSellerEngine(cm, ghl)

    pricing_mock = SimpleNamespace(final_price=2.0, tier="cold", expected_roi=0.0, justification="test")
    seller_data: Dict[str, Any] = {}  # no price_expectation yet

    actions = await engine._create_seller_actions(
        contact_id="test",
        location_id="test",
        temperature="cold",
        seller_data=seller_data,
        pricing_result=pricing_mock,
    )

    valuation_actions = [a for a in actions if "valuation" in str(a.get("field", ""))]
    assert not valuation_actions, (
        f"ai_valuation_price should NOT be written when price_expectation is unknown, got: {valuation_actions}"
    )


@pytest.mark.asyncio
async def test_buyer_multiturn_advances_past_tour_question() -> None:
    """
    Buyer confirms pre-approval and budget (Turn 1) → bot asks tour preference.
    Buyer answers tour preference (Turn 2) → bot must NOT repeat the tour question.
    Buyer gives property preferences (Turn 3) → bot asks about something new.
    """
    from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

    bot = JorgeBuyerBot()
    history: List[Dict[str, str]] = []

    async def run_turn(message: str, buyer_name: str = "Test") -> Dict[str, Any]:
        history.append({"role": "user", "content": message})
        result = await bot.process_buyer_conversation(
            conversation_id="smoke-buyer",
            user_message=message,
            buyer_name=buyer_name,
            conversation_history=list(history),
        )
        response = result.get("response_content", "")
        history.append({"role": "assistant", "content": response})
        return result

    # Turn 1: pre-approved buyer
    r1 = await run_turn("Looking to buy around $600K, I have pre-approval", buyer_name="Jorge")
    resp1 = r1.get("response_content", "")
    assert "mornings or afternoons" in resp1.lower() or "morning" in resp1.lower(), (
        f"Turn 1 should ask about tour preference, got: {resp1}"
    )

    # Turn 2: user answers tour preference
    r2 = await run_turn("mornings work great")
    resp2 = r2.get("response_content", "")
    # Should NOT repeat the same tour question
    assert "mornings or afternoons" not in resp2.lower(), (
        f"Turn 2 should NOT repeat tour question, got: {resp2}"
    )

    # Turn 3: user gives property preferences — bot should ask something different
    r3 = await run_turn("3 bed 2 bath single family in Rancho Cucamonga")
    resp3 = r3.get("response_content", "")
    assert resp3.strip(), "Turn 3 should have a non-empty response"
    assert "mornings or afternoons" not in resp3.lower(), (
        f"Turn 3 should NOT ask tour question again, got: {resp3}"
    )
