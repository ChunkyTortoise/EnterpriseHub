"""
Churn Detection & Recovery Models

This module contains SQLAlchemy models for tracking churn risk assessments,
recovery actions, and recovery outcomes.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Decimal,
    ForeignKey,
    Index,
    Integer,
    JSONB,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ghl_real_estate_ai.models.base import Base


class ChurnRiskAssessment(Base):
    """
    Tracks churn risk assessments for contacts.
    
    Attributes:
        id: Unique identifier
        contact_id: Reference to the contact
        risk_score: Churn risk score (0-100)
        risk_level: Risk level classification (low, medium, high, critical)
        signals: JSON object containing all detection signals and their values
        last_activity: Timestamp of last activity
        days_inactive: Number of days since last activity
        recommended_action: Recommended recovery strategy
        assessed_at: Timestamp when assessment was performed
        created_at: Timestamp when record was created
    """
    
    __tablename__ = "churn_risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    risk_score = Column(Decimal(5, 2), nullable=False)
    risk_level = Column(String(50), nullable=False, index=True)
    signals = Column(JSONB, nullable=False)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    days_inactive = Column(Integer, nullable=False)
    recommended_action = Column(String(100), nullable=True)
    assessed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="churn_assessments")
    recovery_actions = relationship("RecoveryAction", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return (
            f"<ChurnRiskAssessment(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"risk_score={self.risk_score}, "
            f"risk_level={self.risk_level})>"
        )


class RecoveryAction(Base):
    """
    Tracks recovery actions scheduled and executed for at-risk contacts.
    
    Attributes:
        id: Unique identifier
        contact_id: Reference to the contact
        assessment_id: Reference to the churn risk assessment
        strategy: Recovery strategy used
        message_template: Template used for the recovery message
        channel: Channel used (email, sms, etc.)
        scheduled_at: When the action was scheduled to be sent
        sent_at: When the action was actually sent
        delivered_at: When the action was delivered
        status: Status of the action (pending, sent, delivered, failed)
        result: Result of the action
        ghl_message_id: GHL message ID if sent via GHL
        created_at: Timestamp when record was created
    """
    
    __tablename__ = "recovery_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("churn_risk_assessments.id", ondelete="CASCADE"),
        nullable=False
    )
    strategy = Column(String(100), nullable=False)
    message_template = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    result = Column(Text, nullable=True)
    ghl_message_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    contact = relationship("Contact", back_populates="recovery_actions")
    assessment = relationship("ChurnRiskAssessment", back_populates="recovery_actions")
    outcomes = relationship("RecoveryOutcome", back_populates="action", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return (
            f"<RecoveryAction(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"strategy={self.strategy}, "
            f"status={self.status})>"
        )


class RecoveryOutcome(Base):
    """
    Tracks outcomes of recovery actions.
    
    Attributes:
        id: Unique identifier
        recovery_action_id: Reference to the recovery action
        contact_id: Reference to the contact
        outcome: Outcome of the recovery action (recovered, no_response, opted_out, converted)
        response_time_hours: Time in hours it took for the contact to respond
        next_action: Recommended next action
        outcome_at: Timestamp when outcome was recorded
    """
    
    __tablename__ = "recovery_outcomes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    recovery_action_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recovery_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    outcome = Column(String(50), nullable=False, index=True)
    response_time_hours = Column(Decimal(10, 2), nullable=True)
    next_action = Column(String(100), nullable=True)
    outcome_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    action = relationship("RecoveryAction", back_populates="outcomes")
    contact = relationship("Contact", back_populates="recovery_outcomes")
    
    def __repr__(self) -> str:
        return (
            f"<RecoveryOutcome(id={self.id}, "
            f"action_id={self.recovery_action_id}, "
            f"outcome={self.outcome})>"
        )


# Create indexes for better query performance
Index("idx_churn_assessments_contact", ChurnRiskAssessment.contact_id)
Index("idx_churn_assessments_risk", ChurnRiskAssessment.risk_level)
Index("idx_churn_assessments_date", ChurnRiskAssessment.assessed_at.desc())
Index("idx_recovery_actions_contact", RecoveryAction.contact_id)
Index("idx_recovery_actions_status", RecoveryAction.status)
Index("idx_recovery_actions_scheduled", RecoveryAction.scheduled_at)
Index("idx_recovery_outcomes_action", RecoveryOutcome.recovery_action_id)
Index("idx_recovery_outcomes_contact", RecoveryOutcome.contact_id)
Index("idx_recovery_outcomes_outcome", RecoveryOutcome.outcome)
