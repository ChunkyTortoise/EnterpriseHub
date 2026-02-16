"""Initial schema - shared and tenant models

Revision ID: 001
Revises:
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create shared schema tables."""
    # Create shared schema
    op.execute("CREATE SCHEMA IF NOT EXISTS shared")

    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(256), nullable=False),
        sa.Column('slug', sa.String(128), unique=True, nullable=False),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='trial'),
        sa.Column('tier', sa.String(20), nullable=False, server_default='starter'),
        sa.Column('stripe_customer_id', sa.String(256), nullable=True),
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='shared'
    )

    # API Keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('key_prefix', sa.String(8), nullable=False),
        sa.Column('hashed_key', sa.String(64), unique=True, nullable=False),
        sa.Column('scopes', postgresql.JSONB, nullable=False, server_default='["read", "write"]'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='shared'
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('stripe_subscription_id', sa.String(256), nullable=True),
        sa.Column('plan', sa.String(20), nullable=False, server_default='starter'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='shared'
    )

    # Audit Logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', sa.String(256), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('resource_type', sa.String(64), nullable=False),
        sa.Column('resource_id', sa.String(256), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='shared'
    )

    # Team Members table
    op.create_table(
        'team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('invited_by', sa.String(256), nullable=True),
        sa.Column('accepted', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        schema='shared'
    )

    # Create indexes
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True, schema='shared')
    op.create_index('ix_api_keys_hashed', 'api_keys', ['hashed_key'], unique=True, schema='shared')
    op.create_index('ix_audit_logs_created', 'audit_logs', ['created_at'], schema='shared')


def downgrade() -> None:
    """Drop shared schema tables."""
    op.drop_table('team_members', schema='shared')
    op.drop_table('audit_logs', schema='shared')
    op.drop_table('subscriptions', schema='shared')
    op.drop_table('api_keys', schema='shared')
    op.drop_table('tenants', schema='shared')
    op.execute("DROP SCHEMA IF EXISTS shared CASCADE")
