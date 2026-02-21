"""Shared schema models — Tenant, APIKey, Subscription (public schema)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Tenant(Base):
    """Tenant record in the shared/public schema."""

    __tablename__ = "tenants"
    __table_args__ = {"schema": "shared"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="trial")
    tier: Mapped[str] = mapped_column(String(20), default="starter")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class APIKey(Base):
    """API key for tenant authentication."""

    __tablename__ = "api_keys"
    __table_args__ = {"schema": "shared"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    hashed_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    scopes: Mapped[list] = mapped_column(JSONB, default=lambda: ["read", "write"])
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Subscription(Base):
    """Subscription record linking tenant to Stripe."""

    __tablename__ = "subscriptions"
    __table_args__ = {"schema": "shared"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    plan: Mapped[str] = mapped_column(String(20), default="starter")
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AuditLog(Base):
    """Immutable audit trail."""

    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "shared"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class TeamMember(Base):
    """Team member within a tenant."""

    __tablename__ = "team_members"
    __table_args__ = {"schema": "shared"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member")  # admin, member, viewer
    invited_by: Mapped[str | None] = mapped_column(String(256), nullable=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
