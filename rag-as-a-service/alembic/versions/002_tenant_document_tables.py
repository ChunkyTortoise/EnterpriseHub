"""Tenant-scoped document tables with pgvector embeddings.

Creates a template tenant schema with collections, documents, chunks (with
vector column), and query_logs tables. At runtime, new tenant schemas are
created by cloning this template via schema_manager.

Revision ID: 002
Revises: 001
Create Date: 2026-02-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TEMPLATE_SCHEMA = "tenant_template"


def upgrade() -> None:
    """Create template tenant schema with document/chunk/collection tables."""
    # Ensure pgvector extension exists (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create template schema for tenant provisioning
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {TEMPLATE_SCHEMA}")

    # Collections table
    op.create_table(
        "collections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("document_count", sa.Integer, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        schema=TEMPLATE_SCHEMA,
    )

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "collection_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{TEMPLATE_SCHEMA}.collections.id"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("chunk_count", sa.Integer, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column("storage_key", sa.String(1024), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        schema=TEMPLATE_SCHEMA,
    )

    # Chunks table with vector embedding column
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{TEMPLATE_SCHEMA}.documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        schema=TEMPLATE_SCHEMA,
    )

    # Add vector column for embeddings (1536 dimensions for OpenAI text-embedding-3-small)
    op.execute(
        f"ALTER TABLE {TEMPLATE_SCHEMA}.chunks "
        f"ADD COLUMN embedding vector(1536)"
    )

    # Query logs
    op.create_table(
        "query_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("answer_text", sa.Text, nullable=True),
        sa.Column("source_chunks", sa.Integer, server_default="0"),
        sa.Column("latency_ms", sa.Integer, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        schema=TEMPLATE_SCHEMA,
    )

    # Indexes for performance
    op.create_index(
        "ix_documents_collection",
        "documents",
        ["collection_id"],
        schema=TEMPLATE_SCHEMA,
    )
    op.create_index(
        "ix_chunks_document",
        "chunks",
        ["document_id"],
        schema=TEMPLATE_SCHEMA,
    )
    op.create_index(
        "ix_query_logs_created",
        "query_logs",
        ["created_at"],
        schema=TEMPLATE_SCHEMA,
    )

    # HNSW index for vector similarity search
    op.execute(
        f"CREATE INDEX ix_chunks_embedding ON {TEMPLATE_SCHEMA}.chunks "
        f"USING hnsw (embedding vector_cosine_ops) "
        f"WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    """Drop template tenant schema."""
    op.execute(f"DROP SCHEMA IF EXISTS {TEMPLATE_SCHEMA} CASCADE")
