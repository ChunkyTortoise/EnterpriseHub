"""
Multi-Tenant Row-Level Security (RLS) for PostgreSQL.

This module provides SQLAlchemy utilities for implementing tenant isolation
using PostgreSQL Row-Level Security policies. Each request sets the tenant
context, and RLS policies automatically filter queries to only return
rows belonging to the current tenant.

Usage:
    1. Enable RLS on tables using the migration template.
    2. Use TenantMixin on all tenant-scoped models.
    3. Use TenantContextManager or set_tenant_context() in request middleware.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TenantMixin:
    """
    SQLAlchemy mixin for tenant-scoped models.
    
    Adds tenant_id column and ensures proper indexing for RLS.
    All models that should be tenant-isolated should inherit from this.
    
    Example:
        from sqlalchemy import Column, String
        from sqlalchemy.ext.declarative import declarative_base
        
        Base = declarative_base()
        
        class User(Base, TenantMixin):
            __tablename__ = "users"
            email = Column(String, unique=True)
            name = Column(String)
    """
    
    # These should be defined in the actual model
    # tenant_id = Column(UUID, nullable=False, index=True)
    # created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = {
        # Enable RLS on this table
        # Actual RLS policies are created via migration
    }


async def set_tenant_context(
    session: AsyncSession,
    tenant_id: UUID,
) -> None:
    """
    Set the tenant context for the current database session.
    
    This sets the PostgreSQL session variable `app.current_tenant_id`
    which RLS policies use to filter rows.
    
    Args:
        session: SQLAlchemy async session.
        tenant_id: UUID of the tenant to set as current context.
        
    Example:
        async with get_session() as session:
            await set_tenant_context(session, tenant_uuid)
            # All queries now filtered to this tenant
            users = await session.execute(select(User))
    """
    await session.execute(
        text("SET app.current_tenant_id = :tenant_id"),
        {"tenant_id": str(tenant_id)}
    )


async def clear_tenant_context(session: AsyncSession) -> None:
    """
    Clear the tenant context from the current database session.
    
    This resets the PostgreSQL session variable, useful for
    super-admin operations that need cross-tenant access.
    
    Args:
        session: SQLAlchemy async session.
    """
    await session.execute(text("RESET app.current_tenant_id"))


class TenantContextManager:
    """
    Async context manager for tenant-scoped database operations.
    
    Automatically sets the tenant context on entry and clears it on exit.
    Use this in FastAPI middleware or dependency injection.
    
    Attributes:
        session: SQLAlchemy async session.
        tenant_id: UUID of the tenant for this context.
        
    Example:
        async with TenantContextManager(session, tenant_uuid) as ctx:
            # All queries within this block are tenant-isolated
            users = await session.execute(select(User))
            # users only contains rows for tenant_uuid
            
        # Context automatically cleared after block
        
    FastAPI Dependency Example:
        @app.get("/users")
        async def list_users(
            session: AsyncSession = Depends(get_session),
            api_key: APIKeyData = Depends(verify_api_key)
        ):
            async with TenantContextManager(session, UUID(api_key.tenant_id)):
                users = await session.execute(select(User))
                return users.scalars().all()
    """
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        """
        Initialize the tenant context manager.
        
        Args:
            session: SQLAlchemy async session.
            tenant_id: UUID of the tenant to isolate queries to.
        """
        self.session = session
        self.tenant_id = tenant_id
    
    async def __aenter__(self) -> "TenantContextManager":
        """Set tenant context on entry."""
        await set_tenant_context(self.session, self.tenant_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Clear tenant context on exit."""
        await clear_tenant_context(self.session)


@asynccontextmanager
async def tenant_context(
    session: AsyncSession,
    tenant_id: UUID,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for tenant-scoped database operations.
    
    Functional alternative to TenantContextManager class.
    
    Args:
        session: SQLAlchemy async session.
        tenant_id: UUID of the tenant for this context.
        
    Yields:
        The session with tenant context set.
        
    Example:
        async with tenant_context(session, tenant_uuid) as session:
            users = await session.execute(select(User))
    """
    await set_tenant_context(session, tenant_id)
    try:
        yield session
    finally:
        await clear_tenant_context(session)


async def get_current_tenant_id(session: AsyncSession) -> Optional[str]:
    """
    Get the current tenant ID from the PostgreSQL session context.
    
    Useful for debugging and verifying RLS is properly configured.
    
    Args:
        session: SQLAlchemy async session.
        
    Returns:
        The current tenant ID as string, or None if not set.
    """
    result = await session.execute(
        text("SELECT current_setting('app.current_tenant_id', true)")
    )
    tenant_id = result.scalar()
    return tenant_id


async def verify_rls_enabled(session: AsyncSession, table_name: str) -> bool:
    """
    Verify that RLS is enabled on a specific table.
    
    Args:
        session: SQLAlchemy async session.
        table_name: Name of the table to check.
        
    Returns:
        True if RLS is enabled on the table.
    """
    result = await session.execute(
        text("""
            SELECT relrowsecurity 
            FROM pg_class 
            WHERE relname = :table_name
        """),
        {"table_name": table_name}
    )
    rls_enabled = result.scalar()
    return rls_enabled is True


async def create_tenant_policy(
    session: AsyncSession,
    table_name: str,
    policy_name: Optional[str] = None,
) -> None:
    """
    Create a tenant isolation RLS policy for a table.
    
    This is a helper for migrations. Prefer using the SQL migration
    template for production deployments.
    
    Args:
        session: SQLAlchemy async session.
        table_name: Name of the table to create policy for.
        policy_name: Optional custom policy name.
    """
    policy_name = policy_name or f"{table_name}_tenant_isolation"
    
    await session.execute(
        text(f"""
            CREATE POLICY {policy_name} ON {table_name}
            USING (tenant_id::text = current_setting('app.current_tenant_id'))
            WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id'))
        """)
    )
    await session.commit()
