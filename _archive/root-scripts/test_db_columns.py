import pytest

@pytest.mark.integration

import asyncio
import asyncpg
from ghl_real_estate_ai.ghl_utils.config import settings

async def test_db():
    try:
        conn = await asyncpg.connect(settings.database_url)
        print("Connected")
        row = await conn.fetchrow("SELECT * FROM pg_stat_user_tables LIMIT 1")
        if row:
            print(f"Columns: {list(row.keys())}")
        else:
            print("No rows in pg_stat_user_tables")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
