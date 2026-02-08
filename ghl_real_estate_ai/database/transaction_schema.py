"""
Real-Time Transaction Intelligence Database Schema

This module defines the database schema for the Netflix-style transaction tracking system.
Provides complete transaction lifecycle management with real-time progress tracking,
milestone detection, predictive intelligence, and celebration triggers.

Key Features:
- Transaction lifecycle management
- Milestone progress tracking with real-time updates
- Predictive delay detection and health scoring
- Event streaming for real-time dashboard updates
- Celebration triggers for major milestones
- Performance optimized with proper indexing (<50ms queries)
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class TransactionStatus(PyEnum):
    """Transaction status enumeration"""

    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    DELAYED = "delayed"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MilestoneType(PyEnum):
    """Milestone type enumeration"""

    CONTRACT_SIGNED = "contract_signed"
    LOAN_APPLICATION = "loan_application"
    INSPECTION_SCHEDULED = "inspection_scheduled"
    INSPECTION_COMPLETED = "inspection_completed"
    APPRAISAL_ORDERED = "appraisal_ordered"
    APPRAISAL_COMPLETED = "appraisal_completed"
    LOAN_APPROVAL = "loan_approval"
    TITLE_SEARCH = "title_search"
    TITLE_CLEAR = "title_clear"
    FINAL_WALKTHROUGH = "final_walkthrough"
    CLOSING_SCHEDULED = "closing_scheduled"
    CLOSING_COMPLETED = "closing_completed"


class MilestoneStatus(PyEnum):
    """Milestone status enumeration"""

    NOT_STARTED = "not_started"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class EventType(PyEnum):
    """Event type enumeration"""

    MILESTONE_STARTED = "milestone_started"
    MILESTONE_COMPLETED = "milestone_completed"
    MILESTONE_DELAYED = "milestone_delayed"
    PREDICTION_ALERT = "prediction_alert"
    STATUS_CHANGED = "status_changed"
    CELEBRATION_TRIGGERED = "celebration_triggered"
    ACTION_REQUIRED = "action_required"


class RealEstateTransaction(Base):
    """
    Core transaction entity representing a home purchase/sale transaction.

    This is the central table that tracks the overall transaction progress,
    health score, and key metrics for Netflix-style progress visualization.
    """

    __tablename__ = "real_estate_transactions"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(100), unique=True, nullable=False)
    ghl_lead_id = Column(String(255), nullable=False)

    # Property and parties
    property_id = Column(String(255), nullable=False)
    property_address = Column(Text, nullable=False)
    buyer_name = Column(String(200), nullable=False)
    buyer_email = Column(String(255), nullable=False)
    seller_name = Column(String(200))
    agent_name = Column(String(200))

    # Financial details
    purchase_price = Column(Float, nullable=False)
    loan_amount = Column(Float)
    down_payment = Column(Float)
    estimated_closing_costs = Column(Float)

    # Transaction timeline
    contract_date = Column(DateTime, nullable=False)
    expected_closing_date = Column(DateTime, nullable=False)
    actual_closing_date = Column(DateTime)

    # Status and progress
    status = Column(Enum(TransactionStatus), default=TransactionStatus.INITIATED)
    progress_percentage = Column(Float, default=0.0)
    health_score = Column(Integer, default=100)  # 0-100 health score

    # Predictive intelligence
    predicted_closing_date = Column(DateTime)
    delay_risk_score = Column(Float, default=0.0)  # 0-1 probability of delay
    on_track = Column(Boolean, default=True)

    # Performance metrics
    days_since_contract = Column(Integer, default=0)
    days_to_expected_closing = Column(Integer)
    milestones_completed = Column(Integer, default=0)
    total_milestones = Column(Integer, default=12)

    # Client communication
    last_communication_date = Column(DateTime)
    next_update_due = Column(DateTime)
    celebration_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    milestones = relationship("TransactionMilestone", back_populates="transaction")
    events = relationship("TransactionEvent", back_populates="transaction")
    predictions = relationship("TransactionPrediction", back_populates="transaction")
    celebrations = relationship("TransactionCelebration", back_populates="transaction")

    __table_args__ = (
        Index("idx_transaction_ghl_lead", "ghl_lead_id"),
        Index("idx_transaction_status", "status"),
        Index("idx_transaction_progress", "progress_percentage"),
        Index("idx_transaction_health", "health_score"),
        Index("idx_transaction_expected_closing", "expected_closing_date"),
        Index("idx_transaction_delay_risk", "delay_risk_score"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100"),
        CheckConstraint("health_score >= 0 AND health_score <= 100"),
        CheckConstraint("delay_risk_score >= 0 AND delay_risk_score <= 1"),
    )


class TransactionMilestone(Base):
    """
    Individual milestones within a transaction (inspection, appraisal, etc.)

    Tracks detailed progress of each step in the home buying process,
    enabling real-time progress updates and milestone celebrations.
    """

    __tablename__ = "transaction_milestones"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("real_estate_transactions.id"), nullable=False)

    # Milestone details
    milestone_type = Column(Enum(MilestoneType), nullable=False)
    milestone_name = Column(String(200), nullable=False)
    description = Column(Text)
    order_sequence = Column(Integer, nullable=False)

    # Status and progress
    status = Column(Enum(MilestoneStatus), default=MilestoneStatus.NOT_STARTED)
    progress_weight = Column(Float, default=1.0)  # Weight in overall progress calculation

    # Timeline
    target_start_date = Column(DateTime)
    actual_start_date = Column(DateTime)
    target_completion_date = Column(DateTime)
    actual_completion_date = Column(DateTime)

    # Dependencies
    depends_on_milestone_ids = Column(JSONB)  # Array of milestone IDs this depends on
    blocks_milestone_ids = Column(JSONB)  # Array of milestone IDs this blocks

    # Stakeholders
    responsible_party = Column(String(200))  # Who is responsible for this milestone
    contact_info = Column(JSONB)  # Contact information

    # AI insights
    ai_confidence_score = Column(Float)  # AI confidence in timeline prediction
    predicted_completion_date = Column(DateTime)
    delay_probability = Column(Float, default=0.0)

    # Client-facing content
    client_description = Column(Text)  # Client-friendly description
    celebration_message = Column(Text)  # Message shown when completed
    next_steps_description = Column(Text)  # What happens next

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    transaction = relationship("RealEstateTransaction", back_populates="milestones")

    __table_args__ = (
        Index("idx_milestone_transaction", "transaction_id"),
        Index("idx_milestone_type", "milestone_type"),
        Index("idx_milestone_status", "status"),
        Index("idx_milestone_sequence", "transaction_id", "order_sequence"),
        Index("idx_milestone_target_completion", "target_completion_date"),
        CheckConstraint("progress_weight >= 0 AND progress_weight <= 10"),
        CheckConstraint("delay_probability >= 0 AND delay_probability <= 1"),
    )


class TransactionEvent(Base):
    """
    Real-time events in the transaction lifecycle.

    Enables event streaming for live dashboard updates and maintains
    a complete audit trail of all transaction activities.
    """

    __tablename__ = "transaction_events"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("real_estate_transactions.id"), nullable=False)

    # Event details
    event_type = Column(Enum(EventType), nullable=False)
    event_name = Column(String(200), nullable=False)
    description = Column(Text)

    # Event data
    event_data = Column(JSONB)  # Structured event data
    old_values = Column(JSONB)  # Previous values for change events
    new_values = Column(JSONB)  # New values for change events

    # Source and attribution
    source = Column(String(100))  # system, user, api, webhook
    user_id = Column(String(255))  # User who triggered the event
    source_ip = Column(String(45))  # IP address if applicable
    user_agent = Column(Text)  # User agent if applicable

    # Priority and visibility
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    client_visible = Column(Boolean, default=True)  # Should this be shown to client?
    agent_visible = Column(Boolean, default=True)  # Should this be shown to agent?

    # Real-time streaming
    streamed_at = Column(DateTime)  # When this was sent to real-time subscribers
    acknowledgments = Column(JSONB)  # Track which clients have seen this event

    # Metadata
    event_timestamp = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationships
    transaction = relationship("RealEstateTransaction", back_populates="events")

    __table_args__ = (
        Index("idx_event_transaction", "transaction_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_event_timestamp", "event_timestamp"),
        Index("idx_event_priority", "priority"),
        Index("idx_event_client_visible", "client_visible", "event_timestamp"),
    )


class TransactionPrediction(Base):
    """
    AI-powered predictions for transaction outcomes and delays.

    Tracks predictive intelligence for proactive issue resolution
    and client communication about potential delays or concerns.
    """

    __tablename__ = "transaction_predictions"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("real_estate_transactions.id"), nullable=False)

    # Prediction details
    prediction_type = Column(String(100), nullable=False)  # delay, success, risk_factor
    prediction_target = Column(String(200))  # What is being predicted

    # Prediction values
    predicted_value = Column(String(500))  # The predicted outcome
    confidence_score = Column(Float, nullable=False)  # 0-1 confidence level
    probability_distribution = Column(JSONB)  # Full probability distribution

    # Contributing factors
    key_factors = Column(JSONB)  # Top factors influencing prediction
    historical_patterns = Column(JSONB)  # Similar historical cases
    external_factors = Column(JSONB)  # External influences (market, etc.)

    # Risk assessment
    risk_level = Column(String(20))  # low, medium, high, critical
    impact_assessment = Column(Text)  # Description of potential impact
    recommended_actions = Column(JSONB)  # Suggested proactive actions

    # Model information
    model_version = Column(String(50))  # Which model version made this prediction
    model_features = Column(JSONB)  # Feature values used
    prediction_date = Column(DateTime, default=func.now())

    # Validation and feedback
    actual_outcome = Column(String(500))  # What actually happened
    prediction_accuracy = Column(Float)  # How accurate was this prediction
    feedback_provided = Column(Boolean, default=False)  # Was feedback given to improve model

    # Action tracking
    actions_taken = Column(JSONB)  # Actions taken based on this prediction
    outcome_influenced = Column(Boolean)  # Did actions change the outcome

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    transaction = relationship("RealEstateTransaction", back_populates="predictions")

    __table_args__ = (
        Index("idx_prediction_transaction", "transaction_id"),
        Index("idx_prediction_type", "prediction_type"),
        Index("idx_prediction_confidence", "confidence_score"),
        Index("idx_prediction_risk", "risk_level"),
        Index("idx_prediction_date", "prediction_date"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1"),
    )


class TransactionCelebration(Base):
    """
    Milestone celebrations and client engagement events.

    Tracks celebration triggers, client reactions, and engagement
    to maintain excitement throughout the transaction process.
    """

    __tablename__ = "transaction_celebrations"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("real_estate_transactions.id"), nullable=False)

    # Celebration trigger
    trigger_event = Column(String(200), nullable=False)  # What triggered this celebration
    milestone_type = Column(Enum(MilestoneType))  # Associated milestone if applicable
    celebration_type = Column(String(100), nullable=False)  # confetti, modal, email, sms

    # Celebration content
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    emoji = Column(String(20))
    animation_type = Column(String(50))  # confetti, fireworks, pulse

    # Delivery channels
    delivered_via = Column(JSONB)  # Array of delivery channels used
    delivery_status = Column(JSONB)  # Status per channel

    # Client engagement
    client_viewed = Column(Boolean, default=False)
    view_timestamp = Column(DateTime)
    client_reaction = Column(String(50))  # thumbs_up, heart, celebrate, etc.
    reaction_timestamp = Column(DateTime)

    # Celebration metrics
    engagement_duration = Column(Integer)  # How long client engaged (seconds)
    shared_celebration = Column(Boolean, default=False)  # Did client share this
    generated_referral = Column(Boolean, default=False)  # Did this lead to referral

    # A/B testing
    celebration_variant = Column(String(50))  # A/B test variant
    variant_performance = Column(JSONB)  # Performance metrics

    # Metadata
    triggered_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relationships
    transaction = relationship("RealEstateTransaction", back_populates="celebrations")

    __table_args__ = (
        Index("idx_celebration_transaction", "transaction_id"),
        Index("idx_celebration_trigger", "trigger_event"),
        Index("idx_celebration_type", "celebration_type"),
        Index("idx_celebration_triggered", "triggered_at"),
        Index("idx_celebration_engagement", "client_viewed", "engagement_duration"),
    )


# ============================================================================
# Supporting Tables for Enhanced Functionality
# ============================================================================


class TransactionTemplate(Base):
    """
    Templates for different transaction types and their milestone sequences.

    Enables automatic transaction setup with appropriate milestones
    based on transaction type (purchase, refinance, etc.)
    """

    __tablename__ = "transaction_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = Column(String(200), nullable=False, unique=True)
    transaction_type = Column(String(100), nullable=False)

    # Template configuration
    milestone_sequence = Column(JSONB, nullable=False)  # Ordered array of milestone definitions
    typical_duration_days = Column(Integer)  # Expected transaction length
    default_health_weights = Column(JSONB)  # How each milestone affects health score

    # Predictive settings
    risk_factors = Column(JSONB)  # Common risk factors for this type
    success_indicators = Column(JSONB)  # Positive indicators
    benchmark_data = Column(JSONB)  # Historical performance data

    # Active status
    active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_template_type", "transaction_type"),
        Index("idx_template_active", "active"),
    )


class TransactionMetrics(Base):
    """
    Aggregated metrics for transaction performance analysis.

    Supports dashboard analytics and business intelligence
    with pre-calculated metrics for fast dashboard loading.
    """

    __tablename__ = "transaction_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Time period
    metric_date = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly

    # Transaction counts
    transactions_initiated = Column(Integer, default=0)
    transactions_completed = Column(Integer, default=0)
    transactions_cancelled = Column(Integer, default=0)
    transactions_delayed = Column(Integer, default=0)

    # Performance metrics
    avg_completion_days = Column(Float)
    avg_health_score = Column(Float)
    avg_celebration_count = Column(Float)
    client_satisfaction_avg = Column(Float)

    # Milestone performance
    milestone_completion_rates = Column(JSONB)  # Completion rate by milestone type
    milestone_avg_duration = Column(JSONB)  # Average duration by milestone

    # Predictive accuracy
    prediction_accuracy_avg = Column(Float)  # Average accuracy of predictions
    delay_prevention_rate = Column(Float)  # How often we prevent predicted delays

    # Business impact
    total_transaction_value = Column(Float)
    total_commissions = Column(Float)
    referral_generation_rate = Column(Float)

    # Metadata
    calculated_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("idx_metrics_date_period", "metric_date", "period_type"),
        UniqueConstraint("metric_date", "period_type"),
    )


# ============================================================================
# Views for Optimized Queries
# ============================================================================

# This will be created as a SQL view for performance
TRANSACTION_DASHBOARD_VIEW = """
CREATE OR REPLACE VIEW transaction_dashboard_summary AS
SELECT 
    t.id,
    t.transaction_id,
    t.buyer_name,
    t.property_address,
    t.purchase_price,
    t.status,
    t.progress_percentage,
    t.health_score,
    t.expected_closing_date,
    t.delay_risk_score,
    t.days_to_expected_closing,
    t.milestones_completed,
    t.total_milestones,
    t.celebration_count,
    
    -- Current milestone
    (SELECT m.milestone_name 
     FROM transaction_milestones m 
     WHERE m.transaction_id = t.id 
       AND m.status = 'in_progress' 
     ORDER BY m.order_sequence 
     LIMIT 1) as current_milestone,
    
    -- Next milestone
    (SELECT m.milestone_name 
     FROM transaction_milestones m 
     WHERE m.transaction_id = t.id 
       AND m.status = 'not_started' 
     ORDER BY m.order_sequence 
     LIMIT 1) as next_milestone,
    
    -- Recent activity count
    (SELECT COUNT(*) 
     FROM transaction_events e 
     WHERE e.transaction_id = t.id 
       AND e.event_timestamp >= NOW() - INTERVAL '7 days') as recent_activity_count,
    
    -- Risk level
    CASE 
        WHEN t.delay_risk_score >= 0.8 THEN 'critical'
        WHEN t.delay_risk_score >= 0.6 THEN 'high'
        WHEN t.delay_risk_score >= 0.3 THEN 'medium'
        ELSE 'low'
    END as risk_level,
    
    -- Progress status
    CASE 
        WHEN t.progress_percentage >= 90 THEN 'near_completion'
        WHEN t.progress_percentage >= 50 THEN 'mid_progress'
        WHEN t.progress_percentage >= 20 THEN 'early_progress'
        ELSE 'getting_started'
    END as progress_status
    
FROM real_estate_transactions t
WHERE t.status IN ('initiated', 'in_progress', 'delayed')
ORDER BY t.expected_closing_date;
"""

# Performance-optimized materialized view for metrics
TRANSACTION_PERFORMANCE_VIEW = """
CREATE MATERIALIZED VIEW transaction_performance_summary AS
SELECT 
    DATE_TRUNC('week', t.contract_date) as week_start,
    COUNT(*) as transactions_count,
    AVG(t.progress_percentage) as avg_progress,
    AVG(t.health_score) as avg_health_score,
    AVG(CASE WHEN t.actual_closing_date IS NOT NULL 
             THEN EXTRACT(days FROM (t.actual_closing_date - t.contract_date))
             ELSE NULL END) as avg_completion_days,
    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_count,
    SUM(CASE WHEN t.delay_risk_score > 0.5 THEN 1 ELSE 0 END) as at_risk_count,
    AVG(t.celebration_count) as avg_celebrations
FROM real_estate_transactions t
GROUP BY DATE_TRUNC('week', t.contract_date)
ORDER BY week_start DESC;
"""
