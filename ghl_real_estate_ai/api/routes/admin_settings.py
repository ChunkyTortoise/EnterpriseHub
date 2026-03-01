"""Admin API for bot tone, question, and phrase editing.

Endpoints consumed by the Lyrio dashboard (pages/bot_tone.py):
  GET  /admin/settings              - fetch all bot settings
  PUT  /admin/settings/{bot}        - partial update for seller or buyer
  DELETE /api/jorge-{bot}/{contact_id}/state - reset a contact's conversation
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.jorge.bot_settings_store import (
    get_all_settings,
    update_bot_settings,
)

logger = get_logger(__name__)

router = APIRouter(tags=["Bot Admin"])

_VALID_BOTS = {"seller", "buyer"}


class BotSettingsUpdate(BaseModel):
    system_prompt: Optional[str] = None
    jorge_phrases: Optional[list[str]] = None
    questions: Optional[dict[str, str]] = None


@router.get("/admin/settings")
async def get_settings() -> dict[str, Any]:
    """Return current tone/question/phrase settings for all bots."""
    return get_all_settings()


@router.put("/admin/settings/{bot}")
async def update_settings(bot: str, body: BotSettingsUpdate) -> dict[str, Any]:
    """Partial update for seller or buyer bot settings. Returns updated settings."""
    if bot not in _VALID_BOTS:
        raise HTTPException(status_code=400, detail=f"bot must be one of {sorted(_VALID_BOTS)}")
    partial = body.model_dump(exclude_none=True)
    if not partial:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    return update_bot_settings(bot, partial)


@router.delete("/api/jorge-{bot}/{contact_id}/state")
async def reset_contact_state(bot: str, contact_id: str) -> dict[str, Any]:
    """Clear a contact's conversation state so the bot starts fresh from Q1."""
    if bot not in _VALID_BOTS:
        raise HTTPException(status_code=400, detail=f"bot must be one of {sorted(_VALID_BOTS)}")

    cleared: list[str] = []

    # 1. Clear Redis conversation sessions via ConversationSessionManager
    try:
        from ghl_real_estate_ai.services.conversation_session_manager import get_session_manager

        session_manager = get_session_manager()
        conversation_ids = await session_manager.get_lead_conversations(contact_id)
        for cid in conversation_ids:
            await session_manager.delete_session(cid)
            cleared.append(f"session:{cid}")
        if conversation_ids:
            cleared.append(f"lead-index:{contact_id}")
    except Exception as exc:
        logger.warning(f"Redis session clear failed for contact {contact_id}: {exc}")

    # 2. Clear in-memory test sessions (from /test/ smoke-test endpoints)
    try:
        from ghl_real_estate_ai.api.routes.test_bots import _sessions

        if contact_id in _sessions:
            del _sessions[contact_id]
            cleared.append("test-session")
    except Exception as exc:
        logger.warning(f"Test session clear failed for contact {contact_id}: {exc}")

    logger.info(f"Cleared {bot} bot state for contact {contact_id}: {cleared}")
    return {
        "status": "cleared",
        "contact_id": contact_id,
        "bot": bot,
        "cleared": cleared,
    }
