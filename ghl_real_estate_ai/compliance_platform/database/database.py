
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from ghl_real_estate_ai.ghl_utils.config import settings

logger = logging.getLogger(__name__)

# Default to sqlite if no DB URL is provided (for testing/dev)
# In production, settings.database_url should be set
DATABASE_URL = settings.database_url or "sqlite+aiosqlite:///./compliance.db"

# Ensure async driver for postgres
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.log_level == "DEBUG",
    future=True,
    # Pool settings for production
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get DB session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """
    Initialize database tables.
    Use Alembic for production migrations, but this is useful for dev/tests.
    """
    from .models import Base
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Dangerous!
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")
