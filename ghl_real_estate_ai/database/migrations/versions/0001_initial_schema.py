"""Initial schema — transaction intelligence + A/B testing tables.

Wraps the existing hand-written SQL migrations so that Alembic tracks them
in its version history. Future migrations should use op.create_table() etc.

Revision ID: 0001
Revises:
Create Date: 2026-02-20
"""

import pathlib

from alembic import op

# revision identifiers
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

_MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent


def _read_sql(filename: str) -> str:
    return (_MIGRATIONS_DIR / filename).read_text()


def upgrade() -> None:
    # Transaction intelligence tables (001)
    op.execute(_read_sql("001_create_transaction_intelligence_tables.sql"))

    # A/B testing tables (inline from ab_testing_schema.get_create_tables_sql)
    op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'experiment_status') THEN
            CREATE TYPE experiment_status AS ENUM ('draft', 'active', 'paused', 'completed', 'archived');
        END IF;
    END $$;

    CREATE TABLE IF NOT EXISTS ab_experiments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        hypothesis TEXT,
        target_bot VARCHAR(50),
        metric_type VARCHAR(50) NOT NULL,
        minimum_sample_size INTEGER DEFAULT 100,
        status experiment_status DEFAULT 'draft',
        started_at TIMESTAMP,
        completed_at TIMESTAMP,
        default_traffic_split JSONB DEFAULT '{"A": 0.5, "B": 0.5}',
        winner_variant VARCHAR(50),
        statistical_significance FLOAT,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        created_by VARCHAR(100)
    );

    CREATE INDEX IF NOT EXISTS idx_experiment_name ON ab_experiments(experiment_name);
    CREATE INDEX IF NOT EXISTS idx_experiment_status ON ab_experiments(status);
    CREATE INDEX IF NOT EXISTS idx_experiment_target_bot ON ab_experiments(target_bot);
    CREATE INDEX IF NOT EXISTS idx_experiment_created_at ON ab_experiments(created_at);

    CREATE TABLE IF NOT EXISTS ab_variants (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_id UUID NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
        variant_name VARCHAR(50) NOT NULL,
        variant_label VARCHAR(200),
        description TEXT,
        response_template TEXT,
        system_prompt TEXT,
        config_overrides JSONB,
        traffic_weight FLOAT DEFAULT 0.5,
        impressions INTEGER DEFAULT 0,
        conversions INTEGER DEFAULT 0,
        conversion_rate FLOAT DEFAULT 0.0,
        total_value FLOAT DEFAULT 0.0,
        confidence_interval_lower FLOAT,
        confidence_interval_upper FLOAT,
        is_control BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        CONSTRAINT uq_experiment_variant UNIQUE (experiment_id, variant_name),
        CONSTRAINT chk_weight_range CHECK (traffic_weight >= 0 AND traffic_weight <= 1),
        CONSTRAINT chk_conversion_rate CHECK (conversion_rate >= 0 AND conversion_rate <= 1)
    );

    CREATE INDEX IF NOT EXISTS idx_variant_experiment ON ab_variants(experiment_id);
    CREATE INDEX IF NOT EXISTS idx_variant_name ON ab_variants(variant_name);

    CREATE TABLE IF NOT EXISTS ab_assignments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_id UUID NOT NULL REFERENCES ab_experiments(id),
        variant_id UUID NOT NULL REFERENCES ab_variants(id),
        user_id VARCHAR(255) NOT NULL,
        session_id VARCHAR(255),
        assigned_at TIMESTAMP DEFAULT NOW(),
        bucket_value FLOAT,
        has_converted BOOLEAN DEFAULT FALSE,
        converted_at TIMESTAMP,
        metadata JSONB,
        CONSTRAINT uq_experiment_user UNIQUE (experiment_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_assignment_experiment ON ab_assignments(experiment_id);
    CREATE INDEX IF NOT EXISTS idx_assignment_user ON ab_assignments(user_id);
    CREATE INDEX IF NOT EXISTS idx_assignment_converted ON ab_assignments(has_converted);

    CREATE TABLE IF NOT EXISTS ab_metrics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        experiment_id UUID NOT NULL REFERENCES ab_experiments(id),
        variant_id UUID NOT NULL REFERENCES ab_variants(id),
        assignment_id UUID NOT NULL REFERENCES ab_assignments(id),
        event_type VARCHAR(50) NOT NULL,
        event_value FLOAT DEFAULT 1.0,
        event_data JSONB,
        event_timestamp TIMESTAMP DEFAULT NOW(),
        source VARCHAR(100),
        session_context JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_metric_experiment ON ab_metrics(experiment_id);
    CREATE INDEX IF NOT EXISTS idx_metric_variant ON ab_metrics(variant_id);
    CREATE INDEX IF NOT EXISTS idx_metric_event_type ON ab_metrics(event_type);
    CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON ab_metrics(event_timestamp);
    """)


def downgrade() -> None:
    # A/B testing tables
    op.execute("DROP TABLE IF EXISTS ab_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS ab_assignments CASCADE")
    op.execute("DROP TABLE IF EXISTS ab_variants CASCADE")
    op.execute("DROP TABLE IF EXISTS ab_experiments CASCADE")
    op.execute("DROP TYPE IF EXISTS experiment_status")

    # Transaction intelligence tables
    op.execute("DROP MATERIALIZED VIEW IF EXISTS transaction_performance_summary CASCADE")
    op.execute("DROP VIEW IF EXISTS milestone_timeline_view CASCADE")
    op.execute("DROP VIEW IF EXISTS transaction_dashboard_summary CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction_templates CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction_celebrations CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction_predictions CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction_events CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction_milestones CASCADE")
    op.execute("DROP TABLE IF EXISTS real_estate_transactions CASCADE")
    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS milestone_status")
    op.execute("DROP TYPE IF EXISTS milestone_type")
    op.execute("DROP TYPE IF EXISTS transaction_status")
