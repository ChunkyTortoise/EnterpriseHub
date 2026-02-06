"""
SQLAlchemy Database Models for Customer Intelligence Platform.

Production-ready database models with multi-tenant support.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, DateTime, Text, Float, Integer,
    JSON, ARRAY, ForeignKey, Index, Boolean, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

Base = declarative_base()

# Enums (same as in utils/database_service.py)
class CustomerStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    HOT = "hot"
    CONVERTED = "converted"
    LOST = "lost"
    SILENT = "silent"

class ScoreType(str, Enum):
    LEAD_SCORING = "lead_scoring"
    ENGAGEMENT = "engagement_prediction"
    CHURN = "churn_prediction"
    LTV = "customer_ltv"

class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Multi-tenant base class
class TenantMixin:
    """Mixin for multi-tenant support."""
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Database Models
class Customer(Base, TenantMixin, TimestampMixin):
    """Customer table with multi-tenant support."""
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    department = Column(String(100), default="General", nullable=False)
    status = Column(SQLEnum(CustomerStatus), default=CustomerStatus.NEW, nullable=False)
    last_interaction_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    tags = Column(ARRAY(String), default=list, nullable=False)

    # Relationships
    scores = relationship("CustomerScore", back_populates="customer", cascade="all, delete-orphan")
    conversations = relationship("ConversationMessage", back_populates="customer", cascade="all, delete-orphan")

    # Multi-tenant indexes
    __table_args__ = (
        Index("idx_customers_tenant_status", "tenant_id", "status"),
        Index("idx_customers_tenant_department", "tenant_id", "department"),
        Index("idx_customers_tenant_email", "tenant_id", "email"),
    )

class CustomerScore(Base, TenantMixin):
    """Customer score table with multi-tenant support."""
    __tablename__ = "customer_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    score_type = Column(SQLEnum(ScoreType), nullable=False)
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    features = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="scores")

    # Multi-tenant indexes
    __table_args__ = (
        Index("idx_scores_tenant_customer", "tenant_id", "customer_id"),
        Index("idx_scores_tenant_type", "tenant_id", "score_type"),
        Index("idx_scores_tenant_created", "tenant_id", "created_at"),
    )

class ConversationMessage(Base, TenantMixin):
    """Conversation message table with multi-tenant support."""
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(ConversationRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSON, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="conversations")

    # Multi-tenant indexes
    __table_args__ = (
        Index("idx_messages_tenant_conversation", "tenant_id", "conversation_id"),
        Index("idx_messages_tenant_customer", "tenant_id", "customer_id"),
        Index("idx_messages_tenant_timestamp", "tenant_id", "timestamp"),
    )

class KnowledgeDocument(Base, TenantMixin, TimestampMixin):
    """Knowledge base document table with multi-tenant support."""
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), default=list, nullable=False)
    metadata = Column(JSON, nullable=True)

    # Multi-tenant indexes
    __table_args__ = (
        Index("idx_knowledge_tenant_type", "tenant_id", "document_type"),
        Index("idx_knowledge_tenant_department", "tenant_id", "department"),
    )

class Tenant(Base, TimestampMixin):
    """Tenant configuration table for multi-tenancy."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    settings = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    subscription_tier = Column(String(50), default="starter", nullable=False)
    api_rate_limit = Column(Integer, default=1000, nullable=False)  # requests per hour

    # Security and compliance
    data_retention_days = Column(Integer, default=365, nullable=False)
    encryption_enabled = Column(Boolean, default=True, nullable=False)
    audit_logging_enabled = Column(Boolean, default=True, nullable=False)

class TenantUser(Base, TimestampMixin):
    """Tenant user access control."""
    __tablename__ = "tenant_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # admin, user, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    # Unique constraint
    __table_args__ = (
        Index("idx_tenant_users_unique", "tenant_id", "user_email", unique=True),
    )

class AuditLog(Base):
    """Audit log for compliance and security."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes for compliance queries
    __table_args__ = (
        Index("idx_audit_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_audit_tenant_user", "tenant_id", "user_email"),
        Index("idx_audit_tenant_action", "tenant_id", "action"),
    )

# Model metadata for row-level security
RLS_MODELS = [Customer, CustomerScore, ConversationMessage, KnowledgeDocument]