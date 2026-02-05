import asyncio
import os
from dotenv import load_dotenv
from src.core.memory.supermemory_handler import SupermemoryHandler

async def test_supermemory():
    # Load env vars
    load_dotenv()
    
    print("Initializing SupermemoryHandler...")
    handler = SupermemoryHandler()
    
    if not handler.client:
        print("Error: Supermemory client not initialized. Check your SUPERMEMORY_API_KEY.")
        return

    print("\n1. Testing add_memory...")
    content = "SuperMemory Python SDK integration is successfully implemented in EnterpriseHub."
    metadata = {"source": "unit_test", "version": "1.0"}
    add_response = await handler.add_memory(content=content, metadata=metadata)
    print(f"Add Response: {add_response}")

    print("\n2. Testing search_memories...")
    query = "What do we know about SuperMemory integration?"
    search_results = await handler.search_memories(query=query)
    print(f"Search Results: {search_results}")

    print("\n3. Testing get_user_profile...")
    profile = await handler.get_user_profile()
    print(f"Profile: {profile}")

    print("\nVerification complete!")

if __name__ == "__main__":
    asyncio.run(test_supermemory())
