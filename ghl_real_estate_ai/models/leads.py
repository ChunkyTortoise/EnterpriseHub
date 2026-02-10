import uuid
from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base


class Lead(Base):
    __tablename__ = 'leads'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ghl_lead_id = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    source = Column(String, nullable=True)
    lead_score = Column(Integer, default=0)
    qualification_stage = Column(String, default='unqualified')
    engagement_score = Column(Integer, default=0)
    converted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
