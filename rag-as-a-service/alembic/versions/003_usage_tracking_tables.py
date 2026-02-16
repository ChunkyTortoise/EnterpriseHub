"""Usage tracking tables for quota enforcement and billing.

Tracks per-tenant resource consumption (queries, documents, storage) with
time-series granularity for billing reconciliation and analytics.

Revision ID: 003
Revises: 002
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create usage tracking tables in shared schema."""
    # Usage events — append-only log of all resource consumption
    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "event_type",
            sa.String(32),
            nullable=False,
            comment="query, document_upload, document_delete, storage_add, storage_remove",
        ),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        schema="shared",
    )

    # Usage summaries — pre-aggregated monthly totals per tenant
    op.create_table(
        "usage_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "period",
            sa.String(7),
            nullable=False,
            comment="Billing period in YYYY-MM format",
        ),
        sa.Column("queries_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("documents_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("storage_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("overage_queries", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("tenant_id", "period", name="uq_usage_summary_tenant_period"),
        schema="shared",
    )

    # Indexes for efficient lookups
    op.create_index(
        "ix_usage_events_tenant_created",
        "usage_events",
        ["tenant_id", "created_at"],
        schema="shared",
    )
    op.create_index(
        "ix_usage_events_type",
        "usage_events",
        ["event_type"],
        schema="shared",
    )
    op.create_index(
        "ix_usage_summaries_tenant_period",
        "usage_summaries",
        ["tenant_id", "period"],
        schema="shared",
    )


def downgrade() -> None:
    """Drop usage tracking tables."""
    op.drop_table("usage_summaries", schema="shared")
    op.drop_table("usage_events", schema="shared")
