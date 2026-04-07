"""Add prompt_versions and prompt_usage_log tables.

Revision ID: 2026_04_07_016
Revises: 2026_03_20_015
Create Date: 2026-04-07 10:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2026_04_07_016"
down_revision = "2026_03_20_015"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(256) NOT NULL,
            version INTEGER NOT NULL,
            content TEXT NOT NULL,
            model VARCHAR(128) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            CONSTRAINT uq_prompt_versions_name_version UNIQUE (name, version)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_prompt_versions_name ON prompt_versions (name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prompt_usage_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            version_id UUID NOT NULL REFERENCES prompt_versions(id),
            request_id VARCHAR(256) NOT NULL,
            response_quality NUMERIC(5, 4),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_prompt_usage_log_version_id ON prompt_usage_log (version_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS prompt_usage_log")
    op.execute("DROP TABLE IF EXISTS prompt_versions")
