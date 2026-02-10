import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), nullable=True)
    conversation_type = Column(String, default='sandbox')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
