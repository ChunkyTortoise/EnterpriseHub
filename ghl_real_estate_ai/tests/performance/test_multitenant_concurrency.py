"""
Multi-Tenant Concurrency and Isolation Test
===========================================

Verifies that the system maintains strict tenant isolation under high concurrent load.
Ensures no data leakage between different location_ids.
"""

import asyncio
import random
import time
import uuid
from typing import Any, Dict, List

import pytest
import pytest_asyncio

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.memory_service import MemoryService


@pytest.mark.asyncio
class TestMultiTenantConcurrency:
    """Test suite for multi-tenant isolation under load."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_teardown(self):
        """Setup and teardown test environment."""
        self.memory_service = MemoryService(storage_type="redis")
        self.num_tenants = 20
        self.requests_per_tenant = 50
        self.tenants = [f"loc_concurrent_{i}_{uuid.uuid4().hex[:8]}" for i in range(self.num_tenants)]

        yield

        # Cleanup test data
        for tenant_id in self.tenants:
            for i in range(self.requests_per_tenant):
                contact_id = f"contact_{i}"
                await self.memory_service.clear_context(contact_id, location_id=tenant_id)
        # Also clear the shared contact used in cross-tenant test
        await self.memory_service.clear_context("shared_contact_id", location_id=self.tenants[0])
        await self.memory_service.clear_context("shared_contact_id", location_id=self.tenants[1])

    async def simulate_tenant_load(self, tenant_id: str, tenant_index: int):
        """Simulate concurrent requests for a single tenant."""
        leaks_detected = 0

        for i in range(self.requests_per_tenant):
            contact_id = f"contact_{i}"
            secret_value = f"secret_data_{tenant_index}_{i}_{uuid.uuid4().hex[:8]}"

            # 1. Save context
            await self.memory_service.save_context(
                contact_id, {"secret": secret_value, "tenant_index": tenant_index}, location_id=tenant_id
            )

            # Small random sleep to increase interleaving
            await asyncio.sleep(random.uniform(0.001, 0.01))

            # 2. Retrieve context and verify
            retrieved = await self.memory_service.get_context(contact_id, location_id=tenant_id)

            if retrieved.get("secret") != secret_value:
                print(f"LEAK DETECTED! Tenant {tenant_id} expected {secret_value}, got {retrieved.get('secret')}")
                leaks_detected += 1

            if retrieved.get("location_id") != tenant_id:
                print(f"TENANT MISMATCH! Expected {tenant_id}, got {retrieved.get('location_id')}")
                leaks_detected += 1

        return leaks_detected

    @pytest.mark.performance
    async def test_concurrent_isolation(self):
        """
        Run concurrent operations for multiple tenants and verify isolation.

        This test creates 20 tenants and performs 50 requests per tenant concurrently.
        Total operations: 1000 save/get pairs.
        """
        print(f"\n🚀 Starting Multi-Tenant Concurrency Test with {self.num_tenants} tenants...")
        start_time = time.time()

        tasks = []
        for i, tenant_id in enumerate(self.tenants):
            tasks.append(self.simulate_tenant_load(tenant_id, i))

        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time
        total_leaks = sum(results)

        print(f"📊 Completed in {duration:.2f}s")
        print(f"📉 Total leaks detected: {total_leaks}")

        assert total_leaks == 0, f"Detected {total_leaks} data leaks between tenants!"

    @pytest.mark.performance
    async def test_cross_tenant_access_denial(self):
        """Verify that explicitly accessing another tenant's data fails."""
        tenant_a = self.tenants[0]
        tenant_b = self.tenants[1]
        contact_id = "shared_contact_id"

        # Save data for Tenant A
        await self.memory_service.save_context(contact_id, {"data": "Tenant A Secret"}, location_id=tenant_a)

        # Attempt to access from Tenant B's scope
        # In our implementation, get_context(contact_id, location_id=tenant_b)
        # should not return tenant_a's data.
        context_b = await self.memory_service.get_context(contact_id, location_id=tenant_b)

        assert "Tenant A Secret" not in str(context_b)
        assert context_b.get("location_id") == tenant_b


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add project root to sys.path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    pytest.main([__file__, "-v"])
