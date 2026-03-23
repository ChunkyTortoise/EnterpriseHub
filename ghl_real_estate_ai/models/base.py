"""
Base SQLAlchemy model and shared mixins.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


def utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime. Use instead of datetime.utcnow()."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Adds created_at and updated_at columns to any SQLAlchemy model.

    Usage:
        class MyModel(TimestampMixin, Base):
            __tablename__ = "my_table"
            ...
    """

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=True)
