"""
Billing SQLAlchemy Models

ORM models for subscription management, customer tracking,
usage recording, and billing event audit trail.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ghl_real_estate_ai.models.base import Base, utcnow


class Subscription(Base):
    """
    Subscription record per GHL location.

    Tracks Stripe subscription lifecycle, tier configuration,
    and usage counters for overage billing.
    """

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String(128), nullable=False, unique=True, index=True)
    stripe_subscription_id = Column(String(128), nullable=True, unique=True, index=True)
    stripe_customer_id = Column(String(128), nullable=True, index=True)
    tier = Column(String(64), nullable=False, default="starter")
    status = Column(String(64), nullable=False, default="trialing", index=True)
    usage_allowance = Column(Integer, nullable=False, default=500)
    usage_current = Column(Integer, nullable=False, default=0)
    overage_rate = Column(Numeric(10, 4), nullable=False, default="0.50")
    base_price = Column(Numeric(10, 2), nullable=False, default="297.00")
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    currency = Column(String(8), nullable=False, default="usd")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True)

    usage_records = relationship("UsageRecord", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, location_id={self.location_id!r}, tier={self.tier!r}, status={self.status!r})>"


class StripeCustomer(Base):
    """
    Maps GHL location IDs to Stripe customer IDs.

    Prevents duplicate customer creation and enables
    customer lookup by location.
    """

    __tablename__ = "stripe_customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String(128), nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String(128), nullable=False, unique=True, index=True)
    email = Column(String(256), nullable=True)
    name = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<StripeCustomer(id={self.id}, location_id={self.location_id!r}, "
            f"stripe_customer_id={self.stripe_customer_id!r})>"
        )


class UsageRecord(Base):
    """
    Per-lead usage record for billing and audit purposes.

    Links each processed lead to its subscription and Stripe
    usage record for overage billing reconciliation.
    """

    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_usage_record_id = Column(String(128), nullable=True)
    lead_id = Column(String(128), nullable=True)
    contact_id = Column(String(128), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    amount = Column(Numeric(10, 4), nullable=True)
    tier = Column(String(64), nullable=True)
    billing_period_start = Column(DateTime(timezone=True), nullable=True)
    billing_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    subscription = relationship("Subscription", back_populates="usage_records")

    def __repr__(self) -> str:
        return f"<UsageRecord(id={self.id}, subscription_id={self.subscription_id}, amount={self.amount})>"


class BillingEvent(Base):
    """
    Immutable audit log of inbound Stripe webhook events.

    Stored after processing for replay, debugging, and
    idempotency enforcement (UNIQUE event_id).
    """

    __tablename__ = "billing_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(128), nullable=False, unique=True, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)
    processing_result = Column(JSONB, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<BillingEvent(id={self.id}, event_id={self.event_id!r}, event_type={self.event_type!r})>"
