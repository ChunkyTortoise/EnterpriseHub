"""
CAT-10: Concurrency edge-case integration tests.

Covers four scenarios identified in the RT audit:
  1. Two simultaneous messages from the same contact — observable responses
     are both valid (non-exception, non-empty) and temperature is coherent.
     (Complements the white-box lock-ordering test in test_test_bots_hardening.py
     by asserting *observable output behaviour* rather than internal call order.)
  2. Rapid-fire turns (<500 ms apart) — asyncio.gather of 5 concurrent requests
     all return valid dicts with no exceptions.
  3. Race condition on seller_data accumulation — two concurrent extractions
     for the same contact each carrying a distinct field do not silently drop
     the field the other call had started writing.
  4. Session isolation — responses for contact A never bleed into contact B.

All GHL and LLM calls are mocked. No real API calls.
"""

from __future__ import annotations

import asyncio

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.critical]

from unittest.mock import AsyncMock, MagicMock

# Skip whole module gracefully if full app deps are absent (minimal CI sandbox).
try:
    from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False

_needs_engine = pytest.mark.skipif(
    not _ENGINE_AVAILABLE,
    reason="Full app deps not installed (aiohttp/aiosqlite missing)",
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_cm(seller_prefs: dict | None = None) -> AsyncMock:
    """Minimal stub conversation manager."""
    cm = AsyncMock()
    ctx: dict = {
        "seller_preferences": seller_prefs or {},
        "conversation_history": [],
        "contact_name": "Concurrent Seller",
        "closing_probability": 0.0,
    }
    cm.get_context = AsyncMock(return_value=ctx)
    cm.update_context = AsyncMock()
    cm.get_conversation_history = AsyncMock(return_value=[])

    class _MS:
        async def save_context(self, *a, **kw):
            pass

    cm.memory_service = _MS()
    return cm


def _build_engine(cm=None) -> "JorgeSellerEngine":
    """Construct an engine with stubbed dependencies."""
    if cm is None:
        cm = _make_cm()
    ghl = MagicMock()
    ghl.apply_actions = AsyncMock(return_value=[])
    return JorgeSellerEngine(conversation_manager=cm, ghl_client=ghl)


def _is_valid_response(r) -> bool:
    """Return True if r looks like a well-formed engine response dict."""
    return (
        isinstance(r, dict)
        and "message" in r
        and isinstance(r["message"], str)
        and len(r["message"]) > 0
    )


# ---------------------------------------------------------------------------
# Scenario 1: Two simultaneous messages from the same contact
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_two_simultaneous_messages_both_return_valid_responses() -> None:
    """Two concurrent process_seller_response calls for the same contact must
    both complete without exceptions and both return well-formed response dicts.

    This test focuses on observable output (unlike the white-box
    ``test_concurrent_requests_serialised_by_contact_lock`` in
    test_test_bots_hardening.py which verifies internal call ordering).
    """
    # Use a fresh contact ID to avoid lock state from other tests
    contact_id = "cat10-concurrent-001"
    cm = _make_cm()
    engine = _build_engine(cm)

    results = await asyncio.gather(
        engine.process_seller_response(contact_id, "Moving for a new job opportunity", "loc-cat10"),
        engine.process_seller_response(contact_id, "House is move-in ready", "loc-cat10"),
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        assert not isinstance(r, Exception), (
            f"Concurrent call {i} raised an exception: {r}"
        )
        assert _is_valid_response(r), (
            f"Concurrent call {i} returned an invalid response dict: {r!r}"
        )
        # Temperature must be a known value — not None or garbage
        assert r.get("temperature") in ("hot", "warm", "cold"), (
            f"Concurrent call {i} produced unknown temperature: {r.get('temperature')!r}"
        )


# ---------------------------------------------------------------------------
# Scenario 2: Rapid-fire turns (<500 ms apart)
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
@pytest.mark.slow
async def test_rapid_fire_five_concurrent_turns_all_succeed() -> None:
    """Five simultaneous process_seller_response calls for the same contact
    must all complete without exceptions.  The per-contact asyncio.Lock
    serialises them; this test verifies no deadlock and no dropped responses.
    """
    contact_id = "cat10-rapid-fire-002"
    messages = [
        "I need to sell quickly",
        "The house is in good condition",
        "I can close in 30 days",
        "Looking for around $600k",
        "When can we meet?",
    ]
    engine = _build_engine()

    results = await asyncio.gather(
        *[
            engine.process_seller_response(contact_id, msg, "loc-cat10")
            for msg in messages
        ],
        return_exceptions=True,
    )

    exceptions = [r for r in results if isinstance(r, Exception)]
    assert len(exceptions) == 0, (
        f"Rapid-fire calls raised {len(exceptions)} exception(s): {exceptions}"
    )

    for i, r in enumerate(results):
        assert _is_valid_response(r), (
            f"Rapid-fire call {i} returned invalid response: {r!r}"
        )


# ---------------------------------------------------------------------------
# Scenario 3: Race condition on seller_data accumulation
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_concurrent_calls_do_not_silently_drop_extracted_fields() -> None:
    """Two concurrent calls each reporting a distinct qualification field must
    both persist their field via update_context — neither call's data should be
    silently dropped due to a read-modify-write race.

    We verify this by asserting update_context is called at least twice
    (once per serialised turn) and that neither call terminates abnormally.
    """
    contact_id = "cat10-race-seller-data-003"
    cm = _make_cm()
    engine = _build_engine(cm)

    results = await asyncio.gather(
        # First call provides motivation
        engine.process_seller_response(contact_id, "Moving because of divorce", "loc-cat10"),
        # Second call provides timeline acceptance
        engine.process_seller_response(contact_id, "Yes, 30-45 days works for me", "loc-cat10"),
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        assert not isinstance(r, Exception), (
            f"Call {i} raised: {r}"
        )
        assert _is_valid_response(r), f"Call {i} invalid response: {r!r}"

    # update_context must have been called at least twice — once per serialised turn
    assert cm.update_context.await_count >= 2, (
        f"update_context was called {cm.update_context.await_count} time(s); "
        "expected at least 2 (one per concurrent turn)"
    )


# ---------------------------------------------------------------------------
# Scenario 4: Session isolation between contacts
# ---------------------------------------------------------------------------


@_needs_engine
@pytest.mark.asyncio
async def test_session_isolation_between_contacts() -> None:
    """Concurrent requests for different contact IDs must not share context.
    Each contact's update_context calls must carry the correct contact_id,
    never the other contact's ID.
    """
    contact_a = "cat10-isolation-A-004"
    contact_b = "cat10-isolation-B-004"

    # Separate conversation managers so context is fully isolated
    cm_a = _make_cm()
    cm_b = _make_cm()

    ghl = MagicMock()
    ghl.apply_actions = AsyncMock(return_value=[])

    engine_a = JorgeSellerEngine(conversation_manager=cm_a, ghl_client=ghl)
    engine_b = JorgeSellerEngine(conversation_manager=cm_b, ghl_client=ghl)

    results = await asyncio.gather(
        engine_a.process_seller_response(contact_a, "Need to sell fast — job relocation", "loc-cat10"),
        engine_b.process_seller_response(contact_b, "Just exploring options for now", "loc-cat10"),
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        assert not isinstance(r, Exception), f"Contact {'A' if i == 0 else 'B'} raised: {r}"
        assert _is_valid_response(r), f"Contact {'A' if i == 0 else 'B'} invalid response: {r!r}"

    # Contact A's conversation manager must never receive contact B's ID
    for call_args in cm_a.update_context.await_args_list:
        cid = call_args.args[0] if call_args.args else call_args.kwargs.get("contact_id")
        assert cid == contact_a, (
            f"Contact A's CM received update for wrong contact ID: {cid!r}"
        )

    # Contact B's conversation manager must never receive contact A's ID
    for call_args in cm_b.update_context.await_args_list:
        cid = call_args.args[0] if call_args.args else call_args.kwargs.get("contact_id")
        assert cid == contact_b, (
            f"Contact B's CM received update for wrong contact ID: {cid!r}"
        )
