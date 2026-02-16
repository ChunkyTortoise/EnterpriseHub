"""Call and CallTranscript SQLAlchemy models."""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from voice_ai.models import Base


class CallStatus(str, enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"


class CallDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    twilio_call_sid = Column(String(64), unique=True, index=True)
    direction = Column(Enum(CallDirection), nullable=False)
    from_number = Column(String(20))
    to_number = Column(String(20))
    status = Column(Enum(CallStatus), default=CallStatus.INITIATED, index=True)
    bot_type = Column(String(20))  # "lead" | "buyer" | "seller"
    agent_persona_id = Column(UUID(as_uuid=True), nullable=True)
    duration_seconds = Column(Float, default=0)
    recording_url = Column(String(512), nullable=True)
    consent_given = Column(String(10), default="pending")  # "pending" | "yes" | "no"
    sentiment_scores = Column(JSON, default=dict)
    lead_score = Column(Float, nullable=True)
    ghl_contact_id = Column(String(64), nullable=True)
    appointment_booked = Column(Boolean, default=False)

    # Cost tracking
    cost_stt = Column(Float, default=0)
    cost_tts = Column(Float, default=0)
    cost_llm = Column(Float, default=0)
    cost_telephony = Column(Float, default=0)

    # PII detection results
    pii_detected = Column(Boolean, default=False)
    pii_types_found = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    transcripts = relationship("CallTranscript", back_populates="call", lazy="selectin")

    __table_args__ = (
        Index("ix_calls_tenant_created", "tenant_id", "created_at"),
        Index("ix_calls_tenant_status", "tenant_id", "status"),
    )


class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), index=True)
    speaker = Column(String(10), nullable=False)  # "agent" | "caller"
    text = Column(Text, nullable=False)
    text_redacted = Column(Text, nullable=True)
    timestamp_ms = Column(Float, nullable=False)
    confidence = Column(Float, default=1.0)
    is_final = Column(Boolean, default=True)

    call = relationship("Call", back_populates="transcripts")

    __table_args__ = (Index("ix_transcripts_call_timestamp", "call_id", "timestamp_ms"),)
