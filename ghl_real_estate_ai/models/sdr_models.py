"""
SDR Agent Module — SQLAlchemy ORM models and Pydantic API schemas.

Four new tables:
- sdr_prospects: one row per contact enrolled in SDR
- sdr_outreach_sequences: current step + scheduling state
- sdr_outreach_touches: every touch sent and replies received
- sdr_objection_logs: objection analytics

PII fields (reply_body, raw_message) are encrypted at the ORM level via Fernet.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from ghl_real_estate_ai.models.base import Base

# ---------------------------------------------------------------------------
# PII encryption helpers
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    key = os.getenv("SDR_FERNET_KEY", "")
    if not key:
        # Fallback for dev/test: generate an ephemeral key (data won't survive restarts)
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_pii(value: Optional[str]) -> Optional[str]:
    """Encrypt a PII string. Returns None if value is None."""
    if value is None:
        return None
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_pii(value: Optional[str]) -> Optional[str]:
    """Decrypt a PII string. Returns None if value is None."""
    if value is None:
        return None
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except Exception:
        return value  # Return raw if decryption fails (e.g., dev plaintext data)


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class SDRProspect(Base):
    """One row per contact enrolled in the SDR system."""

    __tablename__ = "sdr_prospects"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    contact_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # ProspectSource.value
    lead_type: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    frs_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pcs_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_scored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sequences: Mapped[List["SDROutreachSequence"]] = relationship(
        "SDROutreachSequence", back_populates="prospect", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("contact_id", "location_id", name="uq_sdr_prospect_contact_location"),)


class SDROutreachSequence(Base):
    """Current step and scheduling state for each prospect."""

    __tablename__ = "sdr_outreach_sequences"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    prospect_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sdr_prospects.id"), nullable=False
    )
    contact_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    current_step: Mapped[str] = mapped_column(String(32), nullable=False)  # SequenceStep.value
    ab_variant: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    next_touch_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reply_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    prospect: Mapped["SDRProspect"] = relationship("SDRProspect", back_populates="sequences")
    touches: Mapped[List["SDROutreachTouch"]] = relationship(
        "SDROutreachTouch", back_populates="sequence", cascade="all, delete-orphan"
    )


class SDROutreachTouch(Base):
    """Every touch sent to a prospect and any replies received."""

    __tablename__ = "sdr_outreach_touches"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    sequence_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sdr_outreach_sequences.id"), nullable=False
    )
    contact_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    step: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)  # "sms"|"email"|"voicemail"
    message_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    _reply_body_encrypted: Mapped[Optional[str]] = mapped_column(
        "reply_body", Text, nullable=True
    )

    sequence: Mapped["SDROutreachSequence"] = relationship(
        "SDROutreachSequence", back_populates="touches"
    )

    @property
    def reply_body(self) -> Optional[str]:
        return decrypt_pii(self._reply_body_encrypted)

    @reply_body.setter
    def reply_body(self, value: Optional[str]) -> None:
        self._reply_body_encrypted = encrypt_pii(value)


class SDRObjectionLog(Base):
    """Objection analytics — one row per classified objection."""

    __tablename__ = "sdr_objection_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    contact_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    objection_type: Mapped[str] = mapped_column(String(64), nullable=False)
    _raw_message_encrypted: Mapped[str] = mapped_column("raw_message", Text, nullable=False)
    rebuttal_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # "sequence_continued" | "opted_out" | "qualified" | "paused"
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    @property
    def raw_message(self) -> str:
        return decrypt_pii(self._raw_message_encrypted) or ""

    @raw_message.setter
    def raw_message(self, value: str) -> None:
        self._raw_message_encrypted = encrypt_pii(value) or ""


# ---------------------------------------------------------------------------
# Pydantic API schemas
# ---------------------------------------------------------------------------

class SDRWebhookPayload(BaseModel):
    """Payload from GHL webhook triggers."""

    contact_id: str
    location_id: str
    trigger_type: str  # "reply_received" | "touch_due" | "prospect_enrolled" | "opt_out" | "stage_change"
    channel: Optional[str] = None  # "sms" | "email" | "voicemail"
    message_body: Optional[str] = None
    workflow_id: Optional[str] = None
    pipeline_stage_id: Optional[str] = None


class SDREnrollRequest(BaseModel):
    """Request body for manual prospect enrollment."""

    contact_ids: List[str] = Field(..., min_length=1)
    location_id: str
    sources: List[str] = Field(default=["ghl_pipeline"])
    lead_type: str = Field(default="unknown")


class SDRProspectResponse(BaseModel):
    """Response for GET /sdr/prospects/{contact_id}."""

    contact_id: str
    location_id: str
    source: str
    lead_type: str
    frs_score: Optional[float]
    pcs_score: Optional[float]
    enrolled_at: datetime
    current_step: Optional[str] = None
    next_touch_at: Optional[datetime] = None
    reply_count: int = 0


class SDRStatsResponse(BaseModel):
    """Aggregated SDR performance metrics."""

    window: str
    enrolled: int = 0
    touches_sent: int = 0
    replies_received: int = 0
    reply_rate: float = 0.0
    objections_handled: int = 0
    qualified_leads: int = 0
    appointments_booked: int = 0
    cost_per_qualified: Optional[float] = None
    conversion_by_step: Dict[str, int] = Field(default_factory=dict)


class SDRBatchProcessResult(BaseModel):
    """Result of a cadence batch processing run."""

    processed: int = 0
    dispatched: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: Optional[float] = None
