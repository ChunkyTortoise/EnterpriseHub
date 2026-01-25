
import asyncio
import asyncpg
from ghl_real_estate_ai.ghl_utils.config import settings

async def test_db():
    print(f"Testing DB connection to {settings.database_url}")
    try:
        conn = await asyncpg.connect(settings.database_url)
        print("✅ Database connection successful")
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {version}")
        await conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
