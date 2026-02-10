import pytest

@pytest.mark.integration

import asyncio
from falkordb import FalkorDB
from ghl_real_estate_ai.ghl_utils.config import settings

async def test_falkor():
    print("Testing FalkorDB connectivity...")
    try:
        # settings.redis_url might be redis://...
        # FalkorDB constructor expects host, port etc.
        host = "localhost"
        port = 6379
        if settings.redis_url:
            from urllib.parse import urlparse
            url = urlparse(settings.redis_url)
            host = url.hostname or host
            port = url.port or port
            
        db = FalkorDB(host=host, port=port)
        print(f"Connected to Redis at {host}:{port}")
        
        # Check if GRAPH.QUERY exists
        try:
            # We can't easily check for command existence without running it
            # Let's try a simple query
            graph = db.select_graph("test_health")
            await graph.query("RETURN 1")
            print("✅ GRAPH.QUERY is available")
        except Exception as e:
            if "unknown command" in str(e):
                print(f"❌ GRAPH.QUERY is NOT available (module missing): {e}")
            else:
                print(f"❌ Error running GRAPH.QUERY: {e}")
                
    except Exception as e:
        print(f"❌ FalkorDB test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_falkor())
