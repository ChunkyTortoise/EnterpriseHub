"""
A/B Testing Database Schema for Jorge Bots

SQLAlchemy models for persistent A/B testing with PostgreSQL.
Provides experiment definitions, variant configurations, user assignments,
and conversion metrics tracking.

Features:
- Experiment management with traffic allocation
- Variant configuration with weights
- User-to-variant assignment tracking
- Conversion event metrics per variant
- Statistical significance analysis
"""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import (
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


class ExperimentStatus(PyEnum):
    """Experiment lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ABExperiment(Base):
    """
    A/B experiment definition.

    Represents a single A/B test with multiple variants for testing
    different bot response strategies.
    """

    __tablename__ = "ab_experiments"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    # Experiment configuration
    hypothesis = Column(Text)  # What we're testing
    target_bot = Column(String(50))  # Which bot this applies to
    metric_type = Column(String(50), nullable=False)  # conversion, engagement, response_rate
    minimum_sample_size = Column(Integer, default=100)

    # Status and dates
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Traffic allocation (default split)
    default_traffic_split = Column(JSONB, default={"A": 0.5, "B": 0.5})

    # Results
    winner_variant = Column(String(50))
    statistical_significance = Column(Float)  # p-value or confidence level

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(100))

    # Relationships
    variants = relationship("ABVariant", back_populates="experiment", cascade="all, delete-orphan")
    assignments = relationship("ABAssignment", back_populates="experiment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_experiment_name", "experiment_name", unique=True),
        Index("idx_experiment_status", "status"),
        Index("idx_experiment_target_bot", "target_bot"),
        Index("idx_experiment_created_at", "created_at"),
    )


class ABVariant(Base):
    """
    A/B test variant configuration.

    Defines a specific variant within an experiment with its own
    response template, weight, and performance metrics.
    """

    __tablename__ = "ab_variants"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_experiments.id"), nullable=False)

    # Variant configuration
    variant_name = Column(String(50), nullable=False)  # A, B, C, etc.
    variant_label = Column(String(200))  # Human-readable label
    description = Column(Text)

    # Response/template configuration
    response_template = Column(Text)  # The bot response template for this variant
    system_prompt = Column(Text)  # Modified system prompt for this variant
    config_overrides = Column(JSONB)  # Any config changes for this variant

    # Traffic allocation
    traffic_weight = Column(Float, default=0.5)  # Traffic percentage (0.0 - 1.0)

    # Performance metrics (aggregated)
    impressions = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    total_value = Column(Float, default=0.0)  # Sum of conversion values

    # Statistical data
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)

    # Status
    is_control = Column(Boolean, default=False)  # Control variant for comparison

    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    experiment = relationship("ABExperiment", back_populates="variants")
    metrics = relationship("ABMetric", back_populates="variant", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("experiment_id", "variant_name", name="uq_experiment_variant"),
        Index("idx_variant_experiment", "experiment_id"),
        Index("idx_variant_name", "variant_name"),
        CheckConstraint("traffic_weight >= 0 AND traffic_weight <= 1", name="chk_weight_range"),
        CheckConstraint("conversion_rate >= 0 AND conversion_rate <= 1", name="chk_conversion_rate"),
    )


class ABAssignment(Base):
    """
    User-to-variant assignment tracking.

    Records which variant each user/contact was assigned to for
    ensuring consistent experiences across sessions.
    """

    __tablename__ = "ab_assignments"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_experiments.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("ab_variants.id"), nullable=False)

    # User/contact identification
    user_id = Column(String(255), nullable=False)  # GHL contact ID
    session_id = Column(String(255))  # Session identifier

    # Assignment details
    assigned_at = Column(DateTime, default=func.now())
    bucket_value = Column(Float)  # Hash bucket value for deterministic assignment

    # Status
    has_converted = Column(Boolean, default=False)
    converted_at = Column(DateTime)

    # Metadata
    metadata = Column(JSONB)  # Additional context (user agent, etc.)

    # Relationships
    experiment = relationship("ABExperiment", back_populates="assignments")
    variant = relationship("ABVariant")

    __table_args__ = (
        UniqueConstraint("experiment_id", "user_id", name="uq_experiment_user"),
        Index("idx_assignment_experiment", "experiment_id"),
        Index("idx_assignment_user", "user_id"),
        Index("idx_assignment_converted", "has_converted"),
    )


class ABMetric(Base):
    """
    Conversion metrics per variant.

    Records individual conversion events for detailed analytics
    and statistical analysis.
    """

    __tablename__ = "ab_metrics"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("ab_experiments.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("ab_variants.id"), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("ab_assignments.id"), nullable=False)

    # Metric details
    event_type = Column(String(50), nullable=False)  # conversion, engagement, handoff, appointment
    event_value = Column(Float, default=1.0)  # Numeric value for the event

    # Event metadata
    event_data = Column(JSONB)  # Additional event context
    event_timestamp = Column(DateTime, default=func.now())

    # Source tracking
    source = Column(String(100))  # Which bot/trigger recorded this
    session_context = Column(JSONB)  # Conversation context at time of event

    # Metadata
    created_at = Column(DateTime, default=func.now())

    # Relationships
    experiment = relationship("ABExperiment")
    variant = relationship("ABVariant", back_populates="metrics")
    assignment = relationship("ABAssignment")

    __table_args__ = (
        Index("idx_metric_experiment", "experiment_id"),
        Index("idx_metric_variant", "variant_id"),
        Index("idx_metric_event_type", "event_type"),
        Index("idx_metric_timestamp", "event_timestamp"),
    )


# ============================================================================
# Database Migration Helper
# ============================================================================


def get_create_tables_sql() -> str:
    """
    Generate SQL statements to create A/B testing tables.

    Returns:
        SQL CREATE TABLE statements with indexes and constraints.
    """
    return """
    -- A/B Testing Tables
    
    CREATE TYPE experiment_status AS ENUM ('draft', 'active', 'paused', 'completed', 'archived');
    
    CREATE TABLE ab_experiments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        hypothesis TEXT,
        target_bot VARCHAR(50),
        metric_type VARCHAR(50) NOT NULL,
        minimum_sample_size INTEGER DEFAULT 100,
        status experiment_status DEFAULT 'draft',
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        default_traffic_split JSONB DEFAULT '{\"A\": 0.5, \"B\": 0.5}',
        winner_variant VARCHAR(50),
        statistical_significance FLOAT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        created_by VARCHAR(100)
    );
    
    CREATE INDEX idx_experiment_name ON ab_experiments(experiment_name);
    CREATE INDEX idx_experiment_status ON ab_experiments(status);
    CREATE INDEX idx_experiment_target_bot ON ab_experiments(target_bot);
    CREATE INDEX idx_experiment_created_at ON ab_experiments(created_at);
    
    CREATE TABLE ab_variants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_id UUID NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
        variant_name VARCHAR(50) NOT NULL,
        variant_label VARCHAR(200),
        description TEXT,
        response_template TEXT,
        system_prompt TEXT,
        config_overrides JSONB,
        traffic_weight FLOAT DEFAULT 0.5,
        impressions INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        conversion_rate FLOAT DEFAULT 0.0,
        total_value FLOAT DEFAULT 0.0,
        confidence_interval_lower FLOAT,
        confidence_interval_upper FLOAT,
        is_control BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        CONSTRAINT uq_experiment_variant UNIQUE (experiment_id, variant_name),
        CONSTRAINT chk_weight_range CHECK (traffic_weight >= 0 AND traffic_weight <= 1),
        CONSTRAINT chk_conversion_rate CHECK (conversion_rate >= 0 AND conversion_rate <= 1)
    );
    
    CREATE INDEX idx_variant_experiment ON ab_variants(experiment_id);
    CREATE INDEX idx_variant_name ON ab_variants(variant_name);
    
    CREATE TABLE ab_assignments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_id UUID NOT NULL REFERENCES ab_experiments(id),
        variant_id UUID NOT NULL REFERENCES ab_variants(id),
        user_id VARCHAR(255) NOT NULL,
        session_id VARCHAR(255),
        assigned_at TIMESTAMP DEFAULT NOW(),
        bucket_value FLOAT,
        has_converted BOOLEAN DEFAULT FALSE,
        converted_at TIMESTAMP,
        metadata JSONB,
        CONSTRAINT uq_experiment_user UNIQUE (experiment_id, user_id)
    );
    
    CREATE INDEX idx_assignment_experiment ON ab_assignments(experiment_id);
    CREATE INDEX idx_assignment_user ON ab_assignments(user_id);
    CREATE INDEX idx_assignment_converted ON ab_assignments(has_converted);
    
    CREATE TABLE ab_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_id UUID NOT NULL REFERENCES ab_experiments(id),
        variant_id UUID NOT NULL REFERENCES ab_variants(id),
        assignment_id UUID NOT NULL REFERENCES ab_assignments(id),
        event_type VARCHAR(50) NOT NULL,
        event_value FLOAT DEFAULT 1.0,
        event_data JSONB,
        event_timestamp TIMESTAMP DEFAULT NOW(),
        source VARCHAR(100),
        session_context JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    CREATE INDEX idx_metric_experiment ON ab_metrics(experiment_id);
    CREATE INDEX idx_metric_variant ON ab_metrics(variant_id);
    CREATE INDEX idx_metric_event_type ON ab_metrics(event_type);
    CREATE INDEX idx_metric_timestamp ON ab_metrics(event_timestamp);
    """
