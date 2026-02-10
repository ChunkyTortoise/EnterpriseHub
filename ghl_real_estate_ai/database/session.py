import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from ghl_real_estate_ai.ghl_utils.config import settings


def _resolve_database_url() -> str | None:
    database_url = os.getenv('DATABASE_URL') or settings.database_url
    if not database_url:
        return None
    if database_url.startswith('postgresql://'):
        return database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return database_url


_DATABASE_URL = _resolve_database_url()
_engine = create_async_engine(_DATABASE_URL, pool_pre_ping=True) if _DATABASE_URL else None
_SessionLocal = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession) if _engine else None


@asynccontextmanager
async def get_async_session():
    if not _SessionLocal:
        raise RuntimeError('DATABASE_URL not configured for async SQLAlchemy session')
    async with _SessionLocal() as session:
        yield session
