"""Add revenue reporting tables for outcome events and weekly pilot KPIs.

Revision ID: 2026_03_03_013
Revises: 2026_02_10_012
Create Date: 2026-03-03 01:20:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_03_013"
down_revision = "2026_02_10_012"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS outcome_events (
            event_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            lead_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_value DOUBLE PRECISION,
            timestamp TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pilot_kpi_records (
            tenant_id TEXT NOT NULL,
            week_start DATE NOT NULL,
            leads_received INTEGER NOT NULL,
            qualified_leads INTEGER NOT NULL,
            response_sla_pct DOUBLE PRECISION NOT NULL,
            appointments_booked INTEGER NOT NULL,
            cost_per_qualified_lead DOUBLE PRECISION NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (tenant_id, week_start)
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_outcome_events_tenant_ts_desc
        ON outcome_events (tenant_id, timestamp DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pilot_kpi_records_tenant_week_desc
        ON pilot_kpi_records (tenant_id, week_start DESC)
        """
    )


def downgrade():
    op.drop_index("idx_pilot_kpi_records_tenant_week_desc", table_name="pilot_kpi_records")
    op.drop_index("idx_outcome_events_tenant_ts_desc", table_name="outcome_events")
    op.drop_table("pilot_kpi_records")
    op.drop_table("outcome_events")
