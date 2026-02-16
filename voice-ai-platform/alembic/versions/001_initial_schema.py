"""Initial schema — calls, call_transcripts, agent_personas.

Revision ID: 001
Revises:
Create Date: 2026-02-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Calls table
    op.create_table(
        "calls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("twilio_call_sid", sa.String(64), unique=True),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("from_number", sa.String(20)),
        sa.Column("to_number", sa.String(20)),
        sa.Column("status", sa.String(20), server_default="initiated"),
        sa.Column("bot_type", sa.String(20)),
        sa.Column("agent_persona_id", UUID(as_uuid=True), nullable=True),
        sa.Column("duration_seconds", sa.Float, server_default="0"),
        sa.Column("recording_url", sa.String(512), nullable=True),
        sa.Column("consent_given", sa.String(10), server_default="pending"),
        sa.Column("sentiment_scores", JSON, server_default="{}"),
        sa.Column("lead_score", sa.Float, nullable=True),
        sa.Column("ghl_contact_id", sa.String(64), nullable=True),
        sa.Column("appointment_booked", sa.Boolean, server_default="false"),
        sa.Column("cost_stt", sa.Float, server_default="0"),
        sa.Column("cost_tts", sa.Float, server_default="0"),
        sa.Column("cost_llm", sa.Float, server_default="0"),
        sa.Column("cost_telephony", sa.Float, server_default="0"),
        sa.Column("pii_detected", sa.Boolean, server_default="false"),
        sa.Column("pii_types_found", JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_calls_tenant_id", "calls", ["tenant_id"])
    op.create_index("ix_calls_twilio_call_sid", "calls", ["twilio_call_sid"])
    op.create_index("ix_calls_status", "calls", ["status"])
    op.create_index("ix_calls_tenant_created", "calls", ["tenant_id", "created_at"])
    op.create_index("ix_calls_tenant_status", "calls", ["tenant_id", "status"])

    # Call transcripts table
    op.create_table(
        "call_transcripts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            UUID(as_uuid=True),
            sa.ForeignKey("calls.id", ondelete="CASCADE"),
        ),
        sa.Column("speaker", sa.String(10), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("text_redacted", sa.Text, nullable=True),
        sa.Column("timestamp_ms", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("is_final", sa.Boolean, server_default="true"),
    )
    op.create_index("ix_transcripts_call_id", "call_transcripts", ["call_id"])
    op.create_index(
        "ix_transcripts_call_timestamp",
        "call_transcripts",
        ["call_id", "timestamp_ms"],
    )

    # Agent personas table
    op.create_table(
        "agent_personas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("bot_type", sa.String(20), nullable=False),
        sa.Column("voice_id", sa.String(64)),
        sa.Column("language", sa.String(10), server_default="en"),
        sa.Column("system_prompt_override", sa.Text, nullable=True),
        sa.Column("greeting_message", sa.String(512), nullable=True),
        sa.Column("transfer_number", sa.String(20), nullable=True),
        sa.Column("settings", JSON, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_personas_tenant_id", "agent_personas", ["tenant_id"])
    op.create_index(
        "ix_personas_tenant_active", "agent_personas", ["tenant_id", "is_active"]
    )


def downgrade() -> None:
    op.drop_table("call_transcripts")
    op.drop_table("calls")
    op.drop_table("agent_personas")
