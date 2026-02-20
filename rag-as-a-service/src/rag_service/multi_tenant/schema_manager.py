"""Schema manager — create/migrate/delete tenant PostgreSQL schemas."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manage per-tenant PostgreSQL schemas."""

    TENANT_TABLES_SQL = [
        # Collections table
        """
        CREATE TABLE IF NOT EXISTS {schema}.collections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            description TEXT,
            document_count INT DEFAULT 0,
            metadata JSONB DEFAULT '{{}}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
        # Documents table
        """
        CREATE TABLE IF NOT EXISTS {schema}.documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            collection_id UUID REFERENCES {schema}.collections(id),
            filename TEXT NOT NULL,
            content_type TEXT NOT NULL,
            size_bytes BIGINT NOT NULL,
            chunk_count INT DEFAULT 0,
            metadata JSONB DEFAULT '{{}}',
            storage_key TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
        # Chunks table with vector column
        """
        CREATE TABLE IF NOT EXISTS {schema}.chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES {schema}.documents(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            chunk_index INT NOT NULL,
            metadata JSONB DEFAULT '{{}}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
        # Query logs
        """
        CREATE TABLE IF NOT EXISTS {schema}.query_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            collection_id UUID,
            query_text TEXT NOT NULL,
            answer_text TEXT,
            source_chunks INT DEFAULT 0,
            latency_ms INT DEFAULT 0,
            metadata JSONB DEFAULT '{{}}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
    ]

    VECTOR_COLUMN_SQL = """
        ALTER TABLE {schema}.chunks
        ADD COLUMN IF NOT EXISTS embedding vector(1536)
    """

    VECTOR_INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS idx_{schema_safe}_chunks_embedding
        ON {schema}.chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """

    def __init__(self, engine=None):
        self.engine = engine

    async def create_tenant_schema(self, slug: str) -> str:
        """Create a new tenant schema with all required tables."""
        schema = f"tenant_{slug}"
        schema_safe = slug.replace("-", "_")

        if self.engine:
            async with self.engine.begin() as conn:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

                for sql_template in self.TENANT_TABLES_SQL:
                    sql = sql_template.format(schema=schema)
                    await conn.execute(sql)

                # Add vector column (requires pgvector extension)
                try:
                    await conn.execute(self.VECTOR_COLUMN_SQL.format(schema=schema))
                    await conn.execute(
                        self.VECTOR_INDEX_SQL.format(schema=schema, schema_safe=schema_safe)
                    )
                except Exception:
                    logger.warning("pgvector not available, skipping vector column for %s", schema)

        logger.info("Created tenant schema: %s", schema)
        return schema

    async def run_migrations(self, schema: str) -> None:
        """Run pending migrations on a tenant schema."""
        if self.engine:
            async with self.engine.begin() as conn:
                for sql_template in self.TENANT_TABLES_SQL:
                    sql = sql_template.format(schema=schema)
                    await conn.execute(sql)

        logger.info("Migrations applied for schema: %s", schema)

    async def delete_tenant_schema(self, slug: str) -> None:
        """Drop a tenant schema and all its data. IRREVERSIBLE."""
        schema = f"tenant_{slug}"

        if self.engine:
            async with self.engine.begin() as conn:
                await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")

        logger.info("Deleted tenant schema: %s", schema)

    async def list_tenant_schemas(self) -> list[str]:
        """List all tenant schemas."""
        if self.engine:
            async with self.engine.begin() as conn:
                result = await conn.execute(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name LIKE 'tenant_%' ORDER BY schema_name"
                )
                return [row[0] for row in result.fetchall()]
        return []
