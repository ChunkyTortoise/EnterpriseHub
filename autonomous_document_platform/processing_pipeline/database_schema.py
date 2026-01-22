"""
Database Schema for Processing Pipeline

PostgreSQL schema design for enterprise document processing with
full audit trail, version control, and compliance tracking.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, Text, JSON,
    ForeignKey, Index, Table, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

Base = declarative_base()

# Enums for type safety
class ProcessingStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    QUALITY_REVIEW = "quality_review"
    HUMAN_REVIEW = "human_review"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReviewPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class QueueType(Enum):
    CRITICAL = "critical"
    PROCESSING = "processing"
    QUALITY = "quality"
    REVIEW = "review"
    EXPORT = "export"

class AuditEventType(Enum):
    DOCUMENT_UPLOADED = "document_uploaded"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    QUALITY_CHECK = "quality_check"
    REVIEW_ASSIGNED = "review_assigned"
    REVIEW_COMPLETED = "review_completed"
    VERSION_CREATED = "version_created"
    DOCUMENT_EXPORTED = "document_exported"
    ERROR_OCCURRED = "error_occurred"

# Association table for document relationships
document_relationships = Table(
    'document_relationships',
    Base.metadata,
    Column('parent_id', String, ForeignKey('document_versions.id')),
    Column('child_id', String, ForeignKey('document_versions.id')),
    Column('relationship_type', String),  # 'revision', 'merge', 'split'
    Column('created_at', DateTime, default=func.now())
)

class BatchJob(Base):
    """
    Batch processing jobs for bulk document operations.
    Tracks overall progress and performance metrics.
    """
    __tablename__ = 'batch_jobs'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    # Progress tracking
    total_documents = Column(Integer, default=0)
    completed_documents = Column(Integer, default=0)
    failed_documents = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Performance metrics
    average_processing_time = Column(Float)  # seconds
    throughput_docs_per_hour = Column(Float)
    queue_wait_time = Column(Float)  # average wait time in queue
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # SLA tracking
    target_completion_time = Column(DateTime)
    sla_met = Column(Boolean, default=True)
    
    # Resource utilization
    peak_memory_mb = Column(Float)
    total_cpu_seconds = Column(Float)
    
    # Relationships
    documents = relationship("DocumentVersion", back_populates="batch_job")
    
    __table_args__ = (
        Index('idx_batch_status', 'status'),
        Index('idx_batch_created', 'created_at'),
    )

class DocumentVersion(Base):
    """
    Immutable document versions with full processing lineage.
    Each processing stage creates a new version for audit compliance.
    """
    __tablename__ = 'document_versions'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, nullable=False)  # Logical document ID (multiple versions)
    version_number = Column(Integer, default=1)
    
    # Document metadata
    original_filename = Column(String(500))
    content_type = Column(String(100))
    file_size_bytes = Column(Integer)
    content_hash = Column(String(64))  # SHA-256 for change detection
    
    # Processing status
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    queue_type = Column(SQLEnum(QueueType))
    
    # Processing results (JSON storage for flexibility)
    parsing_results = Column(JSON)  # IntelligentParser output
    legal_analysis = Column(JSON)   # LegalAnalyzer output
    citations = Column(JSON)        # CitationTracker output
    risk_assessment = Column(JSON)  # RiskExtractor output
    
    # Quality metrics
    parsing_confidence = Column(Float)
    legal_confidence = Column(Float)
    risk_confidence = Column(Float)
    citation_completeness = Column(Float)
    overall_confidence = Column(Float)
    
    # Business metadata
    client_id = Column(String(100))
    matter_id = Column(String(100))
    document_type = Column(String(100))
    priority_score = Column(Float, default=0.5)
    
    # Processing timing
    queue_entered_at = Column(DateTime)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    total_processing_time = Column(Float)  # seconds
    
    # Batch tracking
    batch_job_id = Column(String, ForeignKey('batch_jobs.id'))
    batch_job = relationship("BatchJob", back_populates="documents")
    
    # Version relationships
    parent_versions = relationship(
        "DocumentVersion",
        secondary=document_relationships,
        primaryjoin=id == document_relationships.c.child_id,
        secondaryjoin=id == document_relationships.c.parent_id,
        back_populates="child_versions"
    )
    child_versions = relationship(
        "DocumentVersion",
        secondary=document_relationships,
        primaryjoin=id == document_relationships.c.parent_id,
        secondaryjoin=id == document_relationships.c.child_id,
        back_populates="parent_versions"
    )
    
    # Audit trail
    audit_entries = relationship("AuditTrail", back_populates="document_version")
    
    __table_args__ = (
        UniqueConstraint('document_id', 'version_number', name='uq_document_version'),
        Index('idx_doc_status', 'processing_status'),
        Index('idx_doc_confidence', 'overall_confidence'),
        Index('idx_doc_created', 'queue_entered_at'),
        Index('idx_doc_hash', 'content_hash'),
    )

class QualityMetrics(Base):
    """
    Multi-dimensional quality assessment for processed documents.
    Tracks confidence scores and validation results.
    """
    __tablename__ = 'quality_metrics'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_version_id = Column(String, ForeignKey('document_versions.id'), nullable=False)
    
    # Confidence dimensions (0.0 - 1.0)
    parsing_confidence = Column(Float, nullable=False)
    entity_extraction_confidence = Column(Float, nullable=False)
    clause_identification_confidence = Column(Float, nullable=False)
    risk_assessment_confidence = Column(Float, nullable=False)
    citation_accuracy_confidence = Column(Float, nullable=False)
    
    # Composite scores
    overall_confidence = Column(Float, nullable=False)
    business_rule_compliance_score = Column(Float, default=1.0)
    
    # Validation flags
    requires_human_review = Column(Boolean, default=False)
    validation_flags = Column(JSON)  # List of issues found
    
    # Business rules validation
    contract_type_confidence = Column(Float)
    key_dates_extracted = Column(Boolean, default=False)
    financial_terms_identified = Column(Boolean, default=False)
    parties_identified = Column(Boolean, default=False)
    governing_law_identified = Column(Boolean, default=False)
    
    # Quality thresholds (configurable per client)
    minimum_confidence_threshold = Column(Float, default=0.8)
    review_threshold = Column(Float, default=0.7)
    auto_approval_threshold = Column(Float, default=0.95)
    
    # Assessment details
    assessment_method = Column(String(100))  # 'automated', 'hybrid', 'manual'
    assessment_duration = Column(Float)  # seconds
    assessed_at = Column(DateTime, default=func.now())
    assessed_by = Column(String(100))  # User ID or 'system'
    
    # Performance benchmarking
    compared_to_baseline = Column(Boolean, default=False)
    performance_percentile = Column(Float)  # 0.0-1.0
    
    __table_args__ = (
        Index('idx_quality_confidence', 'overall_confidence'),
        Index('idx_quality_review_required', 'requires_human_review'),
        Index('idx_quality_assessed', 'assessed_at'),
    )

class ReviewAssignment(Base):
    """
    Human review queue with priority-based assignment and SLA tracking.
    Manages escalation and load balancing across reviewers.
    """
    __tablename__ = 'review_assignments'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_version_id = Column(String, ForeignKey('document_versions.id'), nullable=False)
    
    # Assignment details
    assigned_reviewer_id = Column(String(100))  # User ID
    reviewer_role = Column(String(50))  # 'paralegal', 'associate', 'partner'
    priority = Column(SQLEnum(ReviewPriority), default=ReviewPriority.MEDIUM)
    
    # Review status
    status = Column(String(50), default='assigned')  # 'assigned', 'in_progress', 'completed', 'escalated'
    review_type = Column(String(50))  # 'quality_check', 'full_review', 'spot_check'
    
    # SLA tracking
    assigned_at = Column(DateTime, default=func.now())
    due_date = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    sla_met = Column(Boolean, default=True)
    
    # Escalation management
    escalation_count = Column(Integer, default=0)
    escalated_at = Column(DateTime)
    escalated_to_role = Column(String(50))
    escalation_reason = Column(Text)
    
    # Review results
    approved = Column(Boolean)
    rejection_reason = Column(Text)
    reviewer_confidence = Column(Float)  # Reviewer's confidence in their assessment
    review_notes = Column(Text)
    
    # Time tracking
    estimated_duration_hours = Column(Float)
    actual_duration_hours = Column(Float)
    complexity_rating = Column(Integer)  # 1-5 scale
    
    # Quality feedback
    ai_accuracy_rating = Column(Float)  # How accurate was the AI processing?
    false_positive_flags = Column(JSON)  # AI flagged incorrectly
    false_negative_flags = Column(JSON)  # AI missed issues
    
    __table_args__ = (
        Index('idx_review_status', 'status'),
        Index('idx_review_priority', 'priority'),
        Index('idx_review_due_date', 'due_date'),
        Index('idx_review_assigned', 'assigned_reviewer_id'),
    )

class AuditTrail(Base):
    """
    Comprehensive audit trail for compliance and debugging.
    Tracks all document processing events with full context.
    """
    __tablename__ = 'audit_trail'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event identification
    event_type = Column(SQLEnum(AuditEventType), nullable=False)
    event_category = Column(String(50))  # 'processing', 'security', 'user_action'
    event_severity = Column(String(20), default='info')  # 'info', 'warning', 'error', 'critical'
    
    # Context
    document_version_id = Column(String, ForeignKey('document_versions.id'))
    document_version = relationship("DocumentVersion", back_populates="audit_entries")
    batch_job_id = Column(String, ForeignKey('batch_jobs.id'))
    
    # User/system context
    user_id = Column(String(100))
    user_role = Column(String(50))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    session_id = Column(String(100))
    
    # Event details
    event_description = Column(Text, nullable=False)
    event_data = Column(JSON)  # Structured event details
    before_state = Column(JSON)  # State before change
    after_state = Column(JSON)   # State after change
    
    # Processing context
    processing_stage = Column(String(50))  # Which pipeline stage
    worker_id = Column(String(100))        # Celery worker ID
    task_id = Column(String(100))          # Celery task ID
    error_details = Column(JSON)           # Error stack trace if applicable
    
    # Performance tracking
    duration_ms = Column(Integer)
    memory_usage_mb = Column(Float)
    cpu_usage_percent = Column(Float)
    
    # Compliance fields
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    timezone = Column(String(50), default='UTC')
    compliance_category = Column(String(50))  # 'GDPR', 'SOX', 'HIPAA'
    retention_period_days = Column(Integer, default=2555)  # 7 years default
    
    # Data lineage
    correlation_id = Column(String(100))  # Track related events
    parent_event_id = Column(String, ForeignKey('audit_trail.id'))
    children = relationship("AuditTrail", remote_side=[id])
    
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_document', 'document_version_id'),
        Index('idx_audit_correlation', 'correlation_id'),
    )

class ProcessingQueue(Base):
    """
    Queue status tracking for real-time monitoring and load balancing.
    Tracks queue depth, processing rates, and performance metrics.
    """
    __tablename__ = 'processing_queues'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    queue_name = Column(SQLEnum(QueueType), nullable=False, unique=True)
    
    # Queue metrics
    current_depth = Column(Integer, default=0)
    max_depth_24h = Column(Integer, default=0)
    average_depth_24h = Column(Float, default=0.0)
    
    # Processing metrics
    documents_processed_24h = Column(Integer, default=0)
    average_processing_time_24h = Column(Float, default=0.0)
    error_rate_24h = Column(Float, default=0.0)
    
    # Worker metrics
    active_workers = Column(Integer, default=0)
    max_workers = Column(Integer, default=10)
    worker_utilization_percent = Column(Float, default=0.0)
    
    # SLA tracking
    sla_target_seconds = Column(Float, nullable=False)
    sla_breaches_24h = Column(Integer, default=0)
    sla_compliance_rate_24h = Column(Float, default=1.0)
    
    # Status
    is_healthy = Column(Boolean, default=True)
    last_health_check = Column(DateTime, default=func.now())
    health_check_message = Column(Text)
    
    # Performance tuning
    auto_scaling_enabled = Column(Boolean, default=True)
    priority_boost_enabled = Column(Boolean, default=False)
    
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_queue_health', 'is_healthy'),
        Index('idx_queue_updated', 'updated_at'),
    )

# Database initialization and migration functions
def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)

def get_table_names():
    """Get list of all table names for migrations."""
    return [table.name for table in Base.metadata.sorted_tables]

# Query helpers for common operations
class DatabaseQueries:
    """Common database queries for the processing pipeline."""
    
    @staticmethod
    def get_pending_documents(session, queue_type: QueueType = None, limit: int = 100):
        """Get pending documents for processing."""
        query = session.query(DocumentVersion).filter(
            DocumentVersion.processing_status == ProcessingStatus.PENDING
        )
        if queue_type:
            query = query.filter(DocumentVersion.queue_type == queue_type)
        return query.limit(limit).all()
    
    @staticmethod
    def get_documents_requiring_review(session, priority: ReviewPriority = None):
        """Get documents that require human review."""
        query = session.query(DocumentVersion).filter(
            DocumentVersion.processing_status == ProcessingStatus.HUMAN_REVIEW
        )
        if priority:
            query = query.join(ReviewAssignment).filter(
                ReviewAssignment.priority == priority
            )
        return query.all()
    
    @staticmethod
    def get_batch_status(session, batch_id: str):
        """Get comprehensive batch processing status."""
        return session.query(BatchJob).filter(BatchJob.id == batch_id).first()
    
    @staticmethod
    def get_queue_health(session):
        """Get health status of all processing queues."""
        return session.query(ProcessingQueue).all()