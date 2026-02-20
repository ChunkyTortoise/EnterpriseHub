"""Transcript retrieval API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/calls", tags=["transcripts"])


class TranscriptEntry(BaseModel):
    id: str
    speaker: str
    text: str
    timestamp_ms: float
    confidence: float
    is_final: bool


@router.get("/{call_id}/transcript", response_model=list[TranscriptEntry])
async def get_transcript(call_id: str, request: Request) -> list[dict[str, Any]]:
    """Get the full transcript for a call."""
    # MVP: query from DB
    db = request.app.state.db_session
    if db is None:
        return []

    import uuid

    from sqlalchemy import select

    from voice_ai.models.call import CallTranscript

    result = await db.execute(
        select(CallTranscript)
        .where(CallTranscript.call_id == uuid.UUID(call_id))
        .order_by(CallTranscript.timestamp_ms)
    )
    transcripts = result.scalars().all()

    return [
        {
            "id": str(t.id),
            "speaker": t.speaker,
            "text": t.text_redacted or t.text,
            "timestamp_ms": t.timestamp_ms,
            "confidence": t.confidence,
            "is_final": t.is_final,
        }
        for t in transcripts
    ]
