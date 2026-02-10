import pytest

@pytest.mark.integration

import asyncio
from ghl_real_estate_ai.database.connection_manager import DatabaseConnectionManager
from ghl_real_estate_ai.ghl_utils.config import settings

async def test_conn_mgr():
    print(f"Testing DatabaseConnectionManager with URL: {settings.database_url}")
    mgr = DatabaseConnectionManager(settings.database_url)
    try:
        await mgr.initialize()
        print("✅ DatabaseConnectionManager initialized successfully")
        health = await mgr.health_check()
        print(f"Health: {health}")
        await mgr.close()
    except Exception as e:
        print(f"❌ DatabaseConnectionManager failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn_mgr())
