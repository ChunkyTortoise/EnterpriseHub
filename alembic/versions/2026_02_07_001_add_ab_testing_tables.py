"""Add A/B testing tables

Revision ID: 001
Revises: 
Create Date: 2026-02-07 09:23:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM type for experiment status
    experiment_status_enum = postgresql.ENUM(
        'draft', 'active', 'paused', 'completed', 'archived',
        name='experiment_status',
        create_type=True
    )
    experiment_status_enum.create(op.get_bind())
    
    # Create ab_experiments table
    op.create_table(
        'ab_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('experiment_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('hypothesis', sa.Text(), nullable=True),
        sa.Column('target_bot', sa.String(50), nullable=True),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('minimum_sample_size', sa.Integer(), nullable=True, server_default='100'),
        sa.Column('status', experiment_status_enum, nullable=True, server_default='draft'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('default_traffic_split', postgresql.JSONB(), nullable=True, server_default=sa.text('\'{"A": 0.5, "B": 0.5}\'::jsonb')),
        sa.Column('winner_variant', sa.String(50), nullable=True),
        sa.Column('statistical_significance', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.UniqueConstraint('experiment_name', name='uq_experiment_name'),
    )
    
    # Create indexes for ab_experiments
    op.create_index('idx_experiment_name', 'ab_experiments', ['experiment_name'], unique=True)
    op.create_index('idx_experiment_status', 'ab_experiments', ['status'], unique=False)
    op.create_index('idx_experiment_target_bot', 'ab_experiments', ['target_bot'], unique=False)
    op.create_index('idx_experiment_created_at', 'ab_experiments', ['created_at'], unique=False)
    
    # Create ab_variants table
    op.create_table(
        'ab_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_name', sa.String(50), nullable=False),
        sa.Column('variant_label', sa.String(200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('response_template', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('config_overrides', postgresql.JSONB(), nullable=True),
        sa.Column('traffic_weight', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('impressions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('conversions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('conversion_rate', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_value', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=True),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=True),
        sa.Column('is_control', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_experiments.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('experiment_id', 'variant_name', name='uq_experiment_variant'),
        sa.CheckConstraint('traffic_weight >= 0 AND traffic_weight <= 1', name='chk_weight_range'),
        sa.CheckConstraint('conversion_rate >= 0 AND conversion_rate <= 1', name='chk_conversion_rate'),
    )
    
    # Create indexes for ab_variants
    op.create_index('idx_variant_experiment', 'ab_variants', ['experiment_id'], unique=False)
    op.create_index('idx_variant_name', 'ab_variants', ['variant_name'], unique=False)
    
    # Create ab_assignments table
    op.create_table(
        'ab_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('bucket_value', sa.Float(), nullable=True),
        sa.Column('has_converted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_experiments.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['ab_variants.id']),
        sa.UniqueConstraint('experiment_id', 'user_id', name='uq_experiment_user'),
    )
    
    # Create indexes for ab_assignments
    op.create_index('idx_assignment_experiment', 'ab_assignments', ['experiment_id'], unique=False)
    op.create_index('idx_assignment_user', 'ab_assignments', ['user_id'], unique=False)
    op.create_index('idx_assignment_converted', 'ab_assignments', ['has_converted'], unique=False)
    
    # Create ab_metrics table
    op.create_table(
        'ab_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_value', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('session_context', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_experiments.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['ab_variants.id']),
        sa.ForeignKeyConstraint(['assignment_id'], ['ab_assignments.id']),
    )
    
    # Create indexes for ab_metrics
    op.create_index('idx_metric_experiment', 'ab_metrics', ['experiment_id'], unique=False)
    op.create_index('idx_metric_variant', 'ab_metrics', ['variant_id'], unique=False)
    op.create_index('idx_metric_event_type', 'ab_metrics', ['event_type'], unique=False)
    op.create_index('idx_metric_timestamp', 'ab_metrics', ['event_timestamp'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation (due to foreign keys)
    op.drop_index('idx_metric_timestamp', 'ab_metrics')
    op.drop_index('idx_metric_event_type', 'ab_metrics')
    op.drop_index('idx_metric_variant', 'ab_metrics')
    op.drop_index('idx_metric_experiment', 'ab_metrics')
    op.drop_table('ab_metrics')
    
    op.drop_index('idx_assignment_converted', 'ab_assignments')
    op.drop_index('idx_assignment_user', 'ab_assignments')
    op.drop_index('idx_assignment_experiment', 'ab_assignments')
    op.drop_table('ab_assignments')
    
    op.drop_index('idx_variant_name', 'ab_variants')
    op.drop_index('idx_variant_experiment', 'ab_variants')
    op.drop_table('ab_variants')
    
    op.drop_index('idx_experiment_created_at', 'ab_experiments')
    op.drop_index('idx_experiment_target_bot', 'ab_experiments')
    op.drop_index('idx_experiment_status', 'ab_experiments')
    op.drop_index('idx_experiment_name', 'ab_experiments')
    op.drop_table('ab_experiments')
    
    # Drop ENUM type
    experiment_status_enum = postgresql.ENUM(
        'draft', 'active', 'paused', 'completed', 'archived',
        name='experiment_status',
        create_type=False
    )
    experiment_status_enum.drop(op.get_bind())
