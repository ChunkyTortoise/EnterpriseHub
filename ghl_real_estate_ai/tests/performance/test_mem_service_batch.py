import asyncio
import json
import os
import shutil
import time
from pathlib import Path

from ghl_real_estate_ai.services.memory_service import MemoryService


async def benchmark():
    # Setup test data
    test_dir = Path("data/memory/test_location")
    test_dir.mkdir(parents=True, exist_ok=True)

    num_leads = 50
    contact_ids = [f"contact_{i}" for i in range(num_leads)]

    for cid in contact_ids:
        with open(test_dir / f"{cid}.json", "w") as f:
            json.dump(
                {
                    "contact_id": cid,
                    "location_id": "test_location",
                    "conversation_history": [{"role": "user", "content": "hello"}],
                    "updated_at": "2026-01-01T00:00:00",
                },
                f,
            )

    memory_service = MemoryService(storage_type="file")

    print(f"Benchmarking {num_leads} leads contexts...")

    # 1. Individual fetching (Serial)
    start_time = time.time()
    for cid in contact_ids:
        await memory_service.get_context(cid, "test_location")
    serial_time = time.time() - start_time
    print(f"Serial fetch: {serial_time:.4f}s")

    # 2. Individual fetching (Parallel/Gather - Old way)
    start_time = time.time()
    await asyncio.gather(*[memory_service.get_context(cid, "test_location") for cid in contact_ids])
    parallel_time = time.time() - start_time
    print(f"Parallel fetch: {parallel_time:.4f}s")

    # 3. Batch fetching (New way)
    start_time = time.time()
    await memory_service.get_context_batch(contact_ids, "test_location")
    batch_time = time.time() - start_time
    print(f"Batch fetch: {batch_time:.4f}s")

    print(f"\nImprovement over Parallel: {(1 - batch_time / parallel_time) * 100:.2f}%")

    # Cleanup
    shutil.rmtree("data/memory/test_location")


if __name__ == "__main__":
    asyncio.run(benchmark())
