"""
Lead Scoring v2 Models

This module contains SQLAlchemy models for tracking composite lead scores
that combine FRS, PCS, sentiment, and engagement metrics.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSONB,
    Column,
    DateTime,
    Decimal,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ghl_real_estate_ai.models.base import Base


class CompositeLeadScore(Base):
    """
    Tracks composite lead scores combining multiple signals.

    The composite score is calculated as:
    (FRS x 0.40) + (PCS x 0.35) + (Sentiment x 0.15) + (Engagement x 0.10)

    Attributes:
        id: Unique identifier
        contact_id: Reference to the contact
        total_score: Composite score (0-100)
        classification: Lead classification (hot, warm, lukewarm, cold, unqualified)
        confidence_level: Confidence in the score (0-100)
        confidence_interval_lower: Lower bound of confidence interval
        confidence_interval_upper: Upper bound of confidence interval
        frs_score: Financial Readiness Score (0-100)
        pcs_score: Psychological Commitment Score (0-100)
        sentiment_score: Normalized sentiment score (0-100)
        engagement_score: Engagement velocity score (0-100)
        data_completeness: Percentage of required fields populated (0-100)
        conversation_depth: Conversation depth score (0-100)
        scoring_weights: JSON object with custom weights used
        calculated_at: Timestamp when score was calculated
        created_at: Timestamp when record was created
    """

    __tablename__ = "composite_lead_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True)
    total_score = Column(Decimal(5, 2), nullable=False, index=True)
    classification = Column(String(50), nullable=False, index=True)
    confidence_level = Column(Decimal(5, 2), nullable=False)
    confidence_interval_lower = Column(Decimal(5, 2), nullable=False)
    confidence_interval_upper = Column(Decimal(5, 2), nullable=False)
    frs_score = Column(Decimal(5, 2), nullable=False)
    pcs_score = Column(Decimal(5, 2), nullable=False)
    sentiment_score = Column(Decimal(5, 2), nullable=False)
    engagement_score = Column(Decimal(5, 2), nullable=False)
    data_completeness = Column(Decimal(5, 2), nullable=False)
    conversation_depth = Column(Decimal(5, 2), nullable=False)
    scoring_weights = Column(JSONB, default=dict)
    calculated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    contact = relationship("Contact", back_populates="composite_scores")

    def __repr__(self) -> str:
        return (
            f"<CompositeLeadScore(id={self.id}, "
            f"contact_id={self.contact_id}, "
            f"total_score={self.total_score}, "
            f"classification={self.classification})>"
        )


# Create indexes for better query performance
Index("idx_composite_scores_contact", CompositeLeadScore.contact_id)
Index("idx_composite_scores_classification", CompositeLeadScore.classification)
Index("idx_composite_scores_score", CompositeLeadScore.total_score)
Index("idx_composite_scores_calculated", CompositeLeadScore.calculated_at.desc())
