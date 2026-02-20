"""Add composite lead scores table

Revision ID: 2026_02_10_010
Revises: 2026_02_10_009
Create Date: 2026-02-10 16:50:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '2026_02_10_010'
down_revision = '2026_02_10_009'
branch_labels = None
depends_on = None


def upgrade():
    # Create composite_lead_scores table
    op.create_table(
        'composite_lead_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('contact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.Column('confidence_level', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('confidence_interval_lower', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('confidence_interval_upper', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('frs_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('pcs_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('sentiment_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('engagement_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('data_completeness', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('conversation_depth', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('scoring_weights', postgresql.JSONB(), server_default='{}'),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes for composite_lead_scores
    op.create_index('idx_composite_scores_contact', 'composite_lead_scores', ['contact_id'])
    op.create_index('idx_composite_scores_classification', 'composite_lead_scores', ['classification'])
    op.create_index('idx_composite_scores_score', 'composite_lead_scores', ['total_score'])
    op.create_index('idx_composite_scores_calculated', 'composite_lead_scores', ['calculated_at'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_composite_scores_calculated', table_name='composite_lead_scores')
    op.drop_index('idx_composite_scores_score', table_name='composite_lead_scores')
    op.drop_index('idx_composite_scores_classification', table_name='composite_lead_scores')
    op.drop_index('idx_composite_scores_contact', table_name='composite_lead_scores')
    
    # Drop table
    op.drop_table('composite_lead_scores')
