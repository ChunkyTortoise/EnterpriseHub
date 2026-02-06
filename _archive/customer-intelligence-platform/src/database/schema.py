"""
Database Schema Management for Customer Intelligence Platform.

Handles database initialization, migrations, and row-level security setup.
"""

import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text
from .models import Base, RLS_MODELS
import os

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/customer_intelligence"
)

async def create_database_engine(url: Optional[str] = None) -> AsyncEngine:
    """Create async database engine with optimized settings."""
    db_url = url or DATABASE_URL

    engine = create_async_engine(
        db_url,
        pool_size=10,                    # Connection pool size
        max_overflow=20,                 # Additional connections
        pool_pre_ping=True,              # Validate connections
        pool_recycle=3600,               # Recycle connections every hour
        echo=os.getenv("DEBUG") == "true"  # SQL logging in debug mode
    )

    return engine

async def create_tables(engine: AsyncEngine) -> None:
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

async def setup_row_level_security(engine: AsyncEngine) -> None:
    """Set up row-level security policies for multi-tenancy."""
    try:
        async with engine.begin() as conn:
            logger.info("Setting up row-level security...")

            # Enable RLS for tenant-isolated tables
            for model in RLS_MODELS:
                table_name = model.__tablename__

                # Enable row-level security
                await conn.execute(text(f"""
                    ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;
                """))

                # Create tenant isolation policy
                await conn.execute(text(f"""
                    DROP POLICY IF EXISTS tenant_isolation ON {table_name};
                    CREATE POLICY tenant_isolation ON {table_name}
                    USING (tenant_id = (current_setting('app.current_tenant'))::uuid);
                """))

                logger.info(f"RLS enabled for table: {table_name}")

            # Create tenant context function
            await conn.execute(text("""
                CREATE OR REPLACE FUNCTION set_current_tenant(tenant_uuid uuid)
                RETURNS void AS $$
                BEGIN
                    PERFORM set_config('app.current_tenant', tenant_uuid::text, false);
                END;
                $$ LANGUAGE plpgsql;
            """))

            logger.info("Row-level security setup completed")
    except Exception as e:
        logger.error(f"Failed to setup RLS: {e}")
        raise

async def create_indexes(engine: AsyncEngine) -> None:
    """Create additional performance indexes."""
    try:
        async with engine.begin() as conn:
            logger.info("Creating performance indexes...")

            # Additional composite indexes for common queries
            indexes = [
                # Customer analytics
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_tenant_status_created
                   ON customers(tenant_id, status, created_at);""",

                # Score analytics
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scores_tenant_type_created
                   ON customer_scores(tenant_id, score_type, created_at DESC);""",

                # Conversation search
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_tenant_customer_timestamp
                   ON conversation_messages(tenant_id, customer_id, timestamp DESC);""",

                # Knowledge base search (text search)
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_knowledge_content_search
                   ON knowledge_documents USING gin(to_tsvector('english', content));""",

                # Audit log partitioning prep
                """CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_tenant_timestamp_desc
                   ON audit_logs(tenant_id, timestamp DESC);"""
            ]

            for index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql.split('IF NOT EXISTS')[1].split('ON')[0].strip()}")
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")

            logger.info("Performance indexes created")
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")
        raise

async def init_sample_tenant(engine: AsyncEngine) -> str:
    """Initialize a sample tenant for development/demo."""
    try:
        from .models import Tenant, TenantUser
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker
        import uuid

        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Check if default tenant exists
            result = await session.execute(text("SELECT id FROM tenants WHERE slug = 'default'"))
            existing_tenant = result.fetchone()

            if existing_tenant:
                logger.info("Default tenant already exists")
                return str(existing_tenant[0])

            # Create default tenant
            tenant_id = uuid.uuid4()
            tenant = Tenant(
                id=tenant_id,
                name="Default Organization",
                slug="default",
                subscription_tier="professional",
                settings={
                    "features": {
                        "advanced_ai": True,
                        "real_time_analytics": True,
                        "crm_integrations": True
                    },
                    "ui_theme": "dark",
                    "default_department": "General"
                }
            )

            # Create admin user
            admin_user = TenantUser(
                tenant_id=tenant_id,
                user_email="admin@example.com",
                role="admin"
            )

            session.add(tenant)
            session.add(admin_user)
            await session.commit()

            logger.info(f"Sample tenant created: {tenant_id}")
            return str(tenant_id)
    except Exception as e:
        logger.error(f"Failed to create sample tenant: {e}")
        raise

async def migrate_sample_data(engine: AsyncEngine, tenant_id: str) -> None:
    """Migrate sample data from MockDatabase to PostgreSQL."""
    try:
        from .models import Customer, CustomerScore, CustomerStatus, ScoreType
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker
        import uuid
        from datetime import datetime

        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            # Set tenant context
            await session.execute(text(f"SELECT set_current_tenant('{tenant_id}')"))

            # Sample customers (same as MockDatabase)
            sample_customers_data = [
                {
                    "name": "Acme Corporation",
                    "email": "contact@acme.com",
                    "company": "Acme Corp",
                    "industry": "Technology",
                    "department": "Sales",
                    "status": CustomerStatus.QUALIFIED
                },
                {
                    "name": "TechStart Inc",
                    "email": "hello@techstart.com",
                    "company": "TechStart Inc",
                    "industry": "Software",
                    "department": "Marketing",
                    "status": CustomerStatus.HOT
                },
                {
                    "name": "Global Solutions",
                    "email": "info@globalsol.com",
                    "company": "Global Solutions Ltd",
                    "industry": "Consulting",
                    "department": "Customer Success",
                    "status": CustomerStatus.NEW
                }
            ]

            for customer_data in sample_customers_data:
                customer_id = uuid.uuid4()
                customer = Customer(
                    id=customer_id,
                    tenant_id=uuid.UUID(tenant_id),
                    **customer_data
                )
                session.add(customer)

                # Add sample score
                score = CustomerScore(
                    customer_id=customer_id,
                    tenant_id=uuid.UUID(tenant_id),
                    score_type=ScoreType.LEAD_SCORING,
                    score=0.7 + (hash(str(customer_id)) % 30) / 100,
                    confidence=0.8 + (hash(str(customer_id)) % 20) / 100,
                    model_version="v1.0",
                    features={"engagement": 0.8, "company_size": 0.6}
                )
                session.add(score)

            await session.commit()
            logger.info("Sample data migrated to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to migrate sample data: {e}")
        raise

async def init_database(engine: Optional[AsyncEngine] = None) -> str:
    """
    Initialize the complete database with schema, security, and sample data.
    Returns the default tenant ID.
    """
    if engine is None:
        engine = await create_database_engine()

    try:
        logger.info("Starting database initialization...")

        # 1. Create tables
        await create_tables(engine)

        # 2. Set up row-level security
        await setup_row_level_security(engine)

        # 3. Create performance indexes
        await create_indexes(engine)

        # 4. Initialize sample tenant
        tenant_id = await init_sample_tenant(engine)

        # 5. Migrate sample data
        await migrate_sample_data(engine, tenant_id)

        logger.info("Database initialization completed successfully")
        return tenant_id

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def health_check_database(engine: AsyncEngine) -> dict:
    """Perform database health check."""
    try:
        async with engine.begin() as conn:
            # Test basic connectivity
            result = await conn.execute(text("SELECT 1 as health_check"))
            health_result = result.fetchone()

            # Check tenant count
            result = await conn.execute(text("SELECT COUNT(*) FROM tenants"))
            tenant_count = result.fetchone()[0]

            # Check customer count
            result = await conn.execute(text("SELECT COUNT(*) FROM customers"))
            customer_count = result.fetchone()[0]

            return {
                "status": "healthy",
                "connection": "ok" if health_result else "failed",
                "tenant_count": tenant_count,
                "customer_count": customer_count,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    # CLI for database initialization
    asyncio.run(init_database())
    print("Database initialization completed!")