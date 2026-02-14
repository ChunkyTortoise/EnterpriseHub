"""
Sentiment Analysis Models

This module contains SQLAlchemy models for tracking sentiment analysis
across conversations and escalation events.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
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


class ConversationSentiment(Base):
    """
    Tracks sentiment analysis for individual messages in a conversation.
    
    Attributes:
        id: Unique identifier
        conversation_id: Reference to the conversation
        message_index: Position of message in conversation
        sentiment: Detected sentiment type (positive, neutral, anxious, etc.)
        confidence: Confidence score (0.0-1.0)
        intensity: Intensity of the sentiment (0.0-1.0)
        key_phrases: JSON array of key phrases that influenced sentiment
        escalation_level: Escalation level triggered (none, monitor, human_handoff, critical)
        created_at: Timestamp when sentiment was analyzed
    """
    
    __tablename__ = "conversation_sentiments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    message_index = Column(Integer, nullable=False)
    sentiment = Column(String(50), nullable=False, index=True)
    confidence = Column(Decimal(3, 2), nullable=False)
    intensity = Column(Decimal(3, 2), default=0.5)
    key_phrases = Column(JSONB, default=list)
    escalation_level = Column(String(50), default="none", index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="sentiments")
    
    def __repr__(self) -> str:
        return (
            f"<ConversationSentiment(id={self.id}, "
            f"sentiment={self.sentiment}, "
            f"confidence={self.confidence})>"
        )


class SentimentEscalation(Base):
    """
    Tracks sentiment escalation events that require human intervention.
    
    Attributes:
        id: Unique identifier
        conversation_id: Reference to the conversation
        contact_id: Reference to the contact
        escalation_level: Level of escalation (monitor, human_handoff, critical)
        sentiment: Sentiment that triggered escalation
        intensity: Intensity of the sentiment
        reason: Detailed reason for escalation
        resolved: Whether the escalation has been resolved
        resolved_at: Timestamp when escalation was resolved
        resolved_by: Who resolved the escalation (agent name or system)
        created_at: Timestamp when escalation was triggered
    """
    
    __tablename__ = "sentiment_escalations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    contact_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    escalation_level = Column(String(50), nullable=False, index=True)
    sentiment = Column(String(50), nullable=False)
    intensity = Column(Decimal(3, 2), nullable=False)
    reason = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="escalations")
    contact = relationship("Contact", back_populates="sentiment_escalations")
    
    def __repr__(self) -> str:
        return (
            f"<SentimentEscalation(id={self.id}, "
            f"level={self.escalation_level}, "
            f"sentiment={self.sentiment}, "
            f"resolved={self.resolved})>"
        )


# Create indexes for better query performance
Index("idx_conversation_sentiments_conversation", ConversationSentiment.conversation_id)
Index("idx_conversation_sentiments_sentiment", ConversationSentiment.sentiment)
Index("idx_conversation_sentiments_escalation", ConversationSentiment.escalation_level)
Index("idx_sentiment_escalations_contact", SentimentEscalation.contact_id)
Index("idx_sentiment_escalations_level", SentimentEscalation.escalation_level)
