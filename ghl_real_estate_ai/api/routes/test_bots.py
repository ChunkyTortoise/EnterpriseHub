"""
/test/seller and /test/buyer â smoke-test endpoints for Jorge bots.

Run multi-turn bot conversations without real GHL contacts, database
connections, or Redis. All state lives in-process per contact_id.
Side-effects (tags, workflows) are captured and returned rather than
being applied to GHL.

Usage (Swagger):  GET /docs  â Bot Testing section
Usage (curl):
  curl -X POST https://<host>/test/seller \
       -H 'Content-Type: application/json' \
       -d '{"message": "I want to sell my house"}'
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ghl_real_estate_ai.api.routes.inbound_compliance import (
    check_inbound_compliance as _check_inbound_compliance,
    sanitise_message as _sanitise_message,
)

router = APIRouter(prefix="/test", tags=["Bot Testing"])

# ââ In-memory session store (cleared on restart) ââââââââââââââââââââââââââââââ
_sessions: Dict[str, Dict[str, Any]] = {}


def _get_session(contact_id: str, location_id: str = "test") -> Dict[str, Any]:
    if contact_id not in _sessions:
        _sessions[contact_id] = {
            "contact_id": contact_id,
            "location_id": location_id,
            "history": [],
            "seller_data": {},
            "turn": 0,
        }
    return _sessions[contact_id]


# ââ Stub ConversationManager ââââââââââââââââââââââââââââââââââââââââââââââââââ

class _StubMemoryService:
    async def save_context(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        pass


class _StubConversationManager:
    """Minimal in-memory ConversationManager for smoke testing.

    Only implements the methods that JorgeSellerEngine actually calls:
      - get_context()
      - update_context()
      - memory_service.save_context()
      - extract_seller_data()   (delegates to real LLM if API key is set)
    """

    def __init__(self) -> None:
        self.memory_service = _StubMemoryService()

    async def get_context(self, contact_id: str, location_id: Optional[str] = None) -> Dict[str, Any]:
        sess = _get_session(contact_id, location_id or "test")
        # Return a plain dict â JorgeSellerEngine.process_seller_response() calls
        # context.get("seller_preferences", {}) and expects a dict, not a Pydantic model.
        return {
            "contact_id": contact_id,
            "location_id": location_id or "test",
            "conversation_history": list(sess["history"]),
            "seller_preferences": dict(sess.get("seller_data", {})),
            "contact_name": "Test Lead",
            "closing_probability": 0.0,
            "active_ab_test": None,
            "last_ai_message_type": None,
            "is_returning_lead": False,
        }

    async def get_conversation_history(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        return _get_session(contact_id, location_id or "test")["history"]

    async def update_context(
        self,
        contact_id: str,
        user_message: str,
        ai_response: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        sess = _get_session(contact_id)
        sess["history"].append({"role": "user", "content": user_message})
        sess["history"].append({"role": "assistant", "content": ai_response})
        sess["turn"] = sess.get("turn", 0) + 1
        # Persist extracted seller data and temperature so the next turn's
        # get_context() returns the accumulated qualification answers.
        extracted_data = kwargs.get("extracted_data")
        if extracted_data and isinstance(extracted_data, dict):
            sess.setdefault("seller_data", {}).update(extracted_data)
        seller_temp = kwargs.get("seller_temperature")
        if seller_temp:
            sess["seller_temperature"] = seller_temp

    async def extract_seller_data(
        self,
        user_message: str,
        current_seller_data: Dict[str, Any],
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Return current data unchanged â the engine will call the real LLM
        # for extraction as part of process_seller_response.
        return current_seller_data


# ââ Stub GHL Client âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

class _StubGHLClient:
    """Records all GHL side-effects without hitting the API."""

    def __init__(self) -> None:
        self._applied_actions: List[Any] = []

    async def apply_actions(self, contact_id: str, actions: list) -> Dict[str, Any]:
        self._applied_actions.extend(actions)
        return {"success": True, "applied": len(actions)}

    async def add_tags(self, contact_id: str, tags: list) -> Dict[str, Any]:
        return {"success": True}

    async def update_contact(self, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": True}


# ââ Request / Response models âââââââââââââââââââââââââââââââââââââââââââââââââ

class TestSellerRequest(BaseModel):
    message: str
    contact_id: str = "test-seller"
    location_id: str = "test"
    reset: bool = False  # True â wipe session and start fresh


class TestBuyerRequest(BaseModel):
    message: str
    contact_id: str = "test-buyer"
    buyer_name: str = "Test Lead"
    reset: bool = False


class TestBotResponse(BaseModel):
    contact_id: str
    turn: int
    response: str
    actions: List[Dict[str, Any]] = []
    extracted_data: Dict[str, Any] = {}
    temperature: Optional[str] = None
    session_history: List[Dict[str, str]] = []


# ââ POST /test/seller âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.post(
    "/seller",
    response_model=TestBotResponse,
    summary="Smoke-test Seller bot (no GHL / DB required)",
)
async def test_seller(req: TestSellerRequest) -> TestBotResponse:
    """Run one turn of the Seller bot without a real GHL contact.

    - Session history persists in-process per `contact_id`.
    - All GHL side-effects (tags, workflow triggers) are captured and returned.
    - Set `reset: true` to clear the session and start fresh.
    """
    if req.reset:
        _sessions.pop(req.contact_id, None)

    # ── Compliance pre-screen (before engine) ────────────────────────────────
    intercepted, intercept_response, intercept_actions = _check_inbound_compliance(req.message)
    if intercepted:
        sess = _get_session(req.contact_id, req.location_id)
        sess["history"].append({"role": "user", "content": req.message})
        sess["history"].append({"role": "assistant", "content": intercept_response})
        sess["turn"] = sess.get("turn", 0) + 1
        return TestBotResponse(
            contact_id=req.contact_id,
            turn=sess["turn"],
            response=intercept_response,
            actions=intercept_actions,
            extracted_data=sess.get("seller_data", {}),
            temperature=sess.get("seller_temperature", "cold"),
            session_history=sess["history"],
        )

    # Sanitise message to prevent JSON/structured-data injection
    safe_message = _sanitise_message(req.message)

    sess = _get_session(req.contact_id, req.location_id)

    stub_cm = _StubConversationManager()
    stub_ghl = _StubGHLClient()

    from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

    engine = JorgeSellerEngine(stub_cm, stub_ghl)
    result = await engine.process_seller_response(
        contact_id=req.contact_id,
        user_message=safe_message,
        location_id=req.location_id,
        tenant_config=None,
    )

    response_text = result.get("response") or result.get("message") or ""
    actions = result.get("actions") or []
    seller_data = result.get("seller_data") or {}
    temperature = result.get("temperature") or result.get("seller_temperature")

    # Sync history into session (engine may have called stub_cm.update_context
    # already; use the stub's accumulated history as the source of truth).
    sess["history"] = stub_cm.__dict__.get("_history", sess["history"])

    # Fallback: manually append if update_context wasn't called
    existing_turns = len(sess["history"])
    if not any(m.get("content") == req.message for m in sess["history"] if m.get("role") == "user"):
        sess["history"].append({"role": "user", "content": req.message})
    if response_text and not any(m.get("content") == response_text for m in sess["history"] if m.get("role") == "assistant"):
        sess["history"].append({"role": "assistant", "content": response_text})

    sess["turn"] = sess.get("turn", 0) + 1
    if seller_data:
        sess["seller_data"].update(seller_data)

    return TestBotResponse(
        contact_id=req.contact_id,
        turn=sess["turn"],
        response=response_text,
        actions=actions,
        extracted_data=sess.get("seller_data", {}),
        temperature=temperature,
        session_history=sess["history"],
    )


# ââ POST /test/buyer ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

@router.post(
    "/buyer",
    response_model=TestBotResponse,
    summary="Smoke-test Buyer bot (no GHL / DB required)",
)
async def test_buyer(req: TestBuyerRequest) -> TestBotResponse:
    """Run one turn of the Buyer bot without a real GHL contact.

    - Session history persists in-process per `contact_id`.
    - Set `reset: true` to clear the session and start fresh.
    """
    if req.reset:
        _sessions.pop(req.contact_id, None)

    # ── Compliance pre-screen (before engine) ────────────────────────────────
    intercepted, intercept_response, intercept_actions = _check_inbound_compliance(req.message)
    if intercepted:
        sess = _get_session(req.contact_id)
        sess["history"].append({"role": "user", "content": req.message})
        sess["history"].append({"role": "assistant", "content": intercept_response})
        sess["turn"] = sess.get("turn", 0) + 1
        return TestBotResponse(
            contact_id=req.contact_id,
            turn=sess["turn"],
            response=intercept_response,
            actions=intercept_actions,
            extracted_data={},
            temperature="cold",
            session_history=sess["history"],
        )

    safe_message = _sanitise_message(req.message)
    sess = _get_session(req.contact_id)

    # Build history including this new user message
    history = list(sess["history"])
    history.append({"role": "user", "content": safe_message})

    try:
        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
        buyer_bot = JorgeBuyerBot()
        result = await buyer_bot.process_buyer_conversation(
            conversation_id=req.contact_id,
            user_message=safe_message,
            buyer_name=req.buyer_name,
            conversation_history=history,
        )
    except BaseException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Buyer engine unavailable in this environment: {type(exc).__name__}: {exc}",
        ) from exc

    response_text = inject_disclosure(result.get("response_content") or result.get("response") or "", sess.get("turn", 0))
    buyer_temp = result.get("buyer_temperature")
    actions = result.get("actions") or []

    sess["history"].append({"role": "user", "content": safe_message})
    if response_text:
        sess["history"].append({"role": "assistant", "content": response_text})
    sess["turn"] = sess.get("turn", 0) + 1

    # The buyer bot result uses different keys than the seller bot.
    # Pull the available qualification fields into a structured dict.
    buyer_extracted: Dict[str, Any] = {}
    for _key in ("budget_range", "current_qualification_step", "financial_readiness",
                 "urgency_score", "buying_motivation_score"):
        _val = result.get(_key)
        if _val is not None:
            buyer_extracted[_key] = _val

    return TestBotResponse(
        contact_id=req.contact_id,
        turn=sess["turn"],
        response=response_text,
        actions=actions,
        extracted_data=buyer_extracted,
        temperature=buyer_temp,
        session_history=sess["history"],
    )


# ââ Session management helpers ââââââââââââââââââââââââââââââââââââââââââââââââ

@router.delete(
    "/session/{contact_id}",
    summary="Clear test session for a contact_id",
)
async def clear_test_session(contact_id: str) -> Dict[str, str]:
    """Wipe in-memory test session for a contact_id."""
    _sessions.pop(contact_id, None)
    return {"deleted": contact_id}


@router.get("/sessions", summary="List active test sessions")
async def list_test_sessions() -> Dict[str, Any]:
    """Show all active in-memory test sessions (turn count + history length)."""
    return {
        "count": len(_sessions),
        "sessions": {
            cid: {
                "turn": s.get("turn", 0),
                "history_len": len(s.get("history", [])),
            }
            for cid, s in _sessions.items()
        },
    }
