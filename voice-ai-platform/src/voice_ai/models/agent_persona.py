"""AgentPersona SQLAlchemy model."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID

from voice_ai.models import Base


class AgentPersona(Base):
    __tablename__ = "agent_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    bot_type = Column(String(20), nullable=False)  # "lead" | "buyer" | "seller"
    voice_id = Column(String(64))  # ElevenLabs voice ID
    language = Column(String(10), default="en")
    system_prompt_override = Column(Text, nullable=True)
    greeting_message = Column(String(512), nullable=True)
    transfer_number = Column(String(20), nullable=True)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_personas_tenant_active", "tenant_id", "is_active"),)
