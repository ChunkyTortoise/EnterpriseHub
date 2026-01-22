
import asyncio
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add project root to path
sys.path.append(os.getcwd())

# Force SQLite
import ghl_real_estate_ai.compliance_platform.database.database as db_mod
db_mod.DATABASE_URL = "sqlite+aiosqlite:///./raw_test.db"

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from ghl_real_estate_ai.compliance_platform.database.models import DBModelRegistration, Base

async def test_insert():
    print("Testing RAW SQLAlchemy Insert...")
    engine = create_async_engine(db_mod.DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        print("Creating record...")
        new_model = DBModelRegistration(
            name="Raw Test",
            version="1.0",
            description="Testing environment",
            model_type="test",
            provider="internal",
            deployment_location="local",
            intended_use="testing"
        )
        session.add(new_model)
        print("Attempting flush (this is where it usually hangs)...")
        try:
            async with asyncio.timeout(10):
                await session.flush()
            print("FLUSH SUCCESSFUL!")
            await session.commit()
            print("COMMIT SUCCESSFUL!")
        except Exception as e:
            print(f"FAILED: {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_insert())
