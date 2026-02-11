"""
GHL Workflow Models

This module contains SQLAlchemy models for tracking GHL workflow operations,
pipeline stage history, and bot appointments.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ghl_real_estate_ai.models.base import Base


class GHLWorkflowOperation(Base):
    """
    Tracks all GHL workflow operations for audit trail and debugging.
    
    This table logs every operation performed against the GoHighLevel CRM,
    including tag operations, pipeline updates, and appointment creation.
    
    Attributes:
        id: Unique identifier
        contact_id: Reference to the contact
        operation_type: Type of operation ('tag', 'pipeline', 'appointment')
        operation_data: JSON data containing operation details
        status: Operation status ('pending', 'success', 'failed')
        error_message: Error message if operation failed
        ghl_operation_id: ID returned by GHL API
        created_at: Timestamp when operation was created
        completed_at: Timestamp when operation completed
    """
    
    __tablename__ = "ghl_workflow_operations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    operation_type = Column(String(50), nullable=False, index=True)
    operation_data = Column(JSONB, nullable=False)
    status = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    ghl_operation_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="ghl_operations")
    
    def __repr__(self) -> str:
        return (
            f"<GHLWorkflowOperation(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"operation_type={self.operation_type}, "
            f"status={self.status})>"
        )


class PipelineStageHistory(Base):
    """
    Tracks pipeline stage transitions for lead progression analysis.
    
    This table maintains a history of all pipeline stage changes, enabling
    analysis of lead flow through the sales funnel and identification of
    bottlenecks.
    
    Attributes:
        id: Unique identifier
        contact_id: Reference to the contact
        from_stage: Previous pipeline stage
        to_stage: New pipeline stage
        reason: Reason for the stage transition
        score_at_transition: Composite score at time of transition
        transitioned_at: Timestamp when transition occurred
    """
    
    __tablename__ = "pipeline_stage_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    from_stage = Column(String(50), nullable=True)
    to_stage = Column(String(50), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    score_at_transition = Column(String(50), nullable=True)
    transitioned_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="pipeline_history")
    
    def __repr__(self) -> str:
        return (
            f"<PipelineStageHistory(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"from_stage={self.from_stage}, "
            f"to_stage={self.to_stage})>"
        )


class BotAppointment(Base):
    """
    Tracks appointments created by bots and synced to GHL.
    
    This table maintains records of all appointments booked through bot
    conversations, including their status and outcomes.
    
    Attributes:
        id: Unique identifier
        contact_id: Reference to the contact
        ghl_appointment_id: ID returned by GHL calendar API
        title: Appointment title
        start_time: Appointment start time
        end_time: Appointment end time
        calendar_id: GHL calendar ID
        location: Physical or virtual location
        notes: Additional notes
        status: Appointment status ('scheduled', 'completed', 'cancelled', 'no_show')
        created_at: Timestamp when appointment was created
        updated_at: Timestamp when appointment was last updated
    """
    
    __tablename__ = "bot_appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ghl_appointment_id = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    calendar_id = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="scheduled", index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="bot_appointments")
    
    def __repr__(self) -> str:
        return (
            f"<BotAppointment(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"title={self.title}, "
            f"start_time={self.start_time}, "
            f"status={self.status})>"
        )


# Create indexes for better query performance
Index("idx_ghl_operations_contact", GHLWorkflowOperation.contact_id)
Index("idx_ghl_operations_type", GHLWorkflowOperation.operation_type)
Index("idx_ghl_operations_status", GHLWorkflowOperation.status)

Index("idx_pipeline_history_contact", PipelineStageHistory.contact_id)
Index("idx_pipeline_history_stage", PipelineStageHistory.to_stage)
Index("idx_pipeline_history_date", PipelineStageHistory.transitioned_at.desc())

Index("idx_bot_appointments_contact", BotAppointment.contact_id)
Index("idx_bot_appointments_status", BotAppointment.status)
Index("idx_bot_appointments_time", BotAppointment.start_time)
