"""Add SDR tables for prospect enrollment, outreach sequences, touches, and objection logs.

Revision ID: 2026_03_04_014
Revises: 2026_03_03_013
Create Date: 2026-03-04 02:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_03_04_014"
down_revision = "2026_03_03_013"
branch_labels = None
depends_on = None


def upgrade():
    # -- sdr_prospects --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sdr_prospects (
            id TEXT PRIMARY KEY,
            contact_id VARCHAR(64) NOT NULL,
            location_id VARCHAR(64) NOT NULL,
            source VARCHAR(32) NOT NULL,
            lead_type VARCHAR(16) NOT NULL DEFAULT 'unknown',
            frs_score DOUBLE PRECISION,
            pcs_score DOUBLE PRECISION,
            enrolled_at TIMESTAMPTZ NOT NULL,
            last_scored_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_sdr_prospect_contact_location UNIQUE (contact_id, location_id)
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_prospects_contact_id
        ON sdr_prospects (contact_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_prospects_location_id
        ON sdr_prospects (location_id)
        """
    )

    # -- sdr_outreach_sequences --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sdr_outreach_sequences (
            id TEXT PRIMARY KEY,
            prospect_id TEXT NOT NULL REFERENCES sdr_prospects(id),
            contact_id VARCHAR(64) NOT NULL,
            location_id VARCHAR(64) NOT NULL,
            current_step VARCHAR(32) NOT NULL,
            ab_variant VARCHAR(32),
            next_touch_at TIMESTAMPTZ,
            enrolled_at TIMESTAMPTZ NOT NULL,
            reply_count INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_outreach_sequences_contact_id
        ON sdr_outreach_sequences (contact_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_outreach_sequences_location_id
        ON sdr_outreach_sequences (location_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_outreach_sequences_next_touch_at
        ON sdr_outreach_sequences (next_touch_at)
        """
    )

    # -- sdr_outreach_touches --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sdr_outreach_touches (
            id TEXT PRIMARY KEY,
            sequence_id TEXT NOT NULL REFERENCES sdr_outreach_sequences(id),
            contact_id VARCHAR(64) NOT NULL,
            step VARCHAR(32) NOT NULL,
            channel VARCHAR(16) NOT NULL,
            message_body TEXT,
            sent_at TIMESTAMPTZ NOT NULL,
            replied_at TIMESTAMPTZ,
            reply_body TEXT
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_outreach_touches_contact_id
        ON sdr_outreach_touches (contact_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_outreach_touches_sent_at
        ON sdr_outreach_touches (sent_at)
        """
    )

    # -- sdr_objection_logs --
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sdr_objection_logs (
            id TEXT PRIMARY KEY,
            contact_id VARCHAR(64) NOT NULL,
            objection_type VARCHAR(64) NOT NULL,
            raw_message TEXT NOT NULL,
            rebuttal_used TEXT,
            outcome VARCHAR(32),
            logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sdr_objection_logs_contact_id
        ON sdr_objection_logs (contact_id)
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_sdr_objection_logs_contact_id")
    op.execute("DROP TABLE IF EXISTS sdr_objection_logs")

    op.execute("DROP INDEX IF EXISTS idx_sdr_outreach_touches_sent_at")
    op.execute("DROP INDEX IF EXISTS idx_sdr_outreach_touches_contact_id")
    op.execute("DROP TABLE IF EXISTS sdr_outreach_touches")

    op.execute("DROP INDEX IF EXISTS idx_sdr_outreach_sequences_next_touch_at")
    op.execute("DROP INDEX IF EXISTS idx_sdr_outreach_sequences_location_id")
    op.execute("DROP INDEX IF EXISTS idx_sdr_outreach_sequences_contact_id")
    op.execute("DROP TABLE IF EXISTS sdr_outreach_sequences")

    op.execute("DROP INDEX IF EXISTS idx_sdr_prospects_location_id")
    op.execute("DROP INDEX IF EXISTS idx_sdr_prospects_contact_id")
    op.execute("DROP TABLE IF EXISTS sdr_prospects")
