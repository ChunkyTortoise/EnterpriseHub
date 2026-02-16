"""Telemetry and metrics models."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class EventType(str, Enum):
    AGENT_START = "agent.start"
    AGENT_END = "agent.end"
    AGENT_ERROR = "agent.error"
    LLM_CALL = "llm.call"
    TOOL_CALL = "tool.call"
    TOKEN_USAGE = "token.usage"


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    agent_id = Column(String(256), nullable=False, index=True)
    trace_id = Column(String(256), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration_ms = Column(Float, nullable=True)
    model = Column(String(128), nullable=True)
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)
    error_type = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_agent_events_tenant_ts", "tenant_id", "timestamp"),
    )


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_id = Column(String(256), nullable=False)
    metric_name = Column(String(128), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    window_seconds = Column(Integer, nullable=False, default=300)

    __table_args__ = (
        Index("ix_metric_snapshots_lookup", "tenant_id", "agent_id", "metric_name", "timestamp"),
    )
