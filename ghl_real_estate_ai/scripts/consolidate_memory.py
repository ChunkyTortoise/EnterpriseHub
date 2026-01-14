"""
Nightly Memory Consolidation Script ("The Dream Cycle").
Reference: AGENT_MEMORY_STRATEGY.md Section 5.

This script should be scheduled to run nightly (e.g., via cron).
It performs:
1. Conflict Resolution
2. Insight Generation
3. Pruning
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ghl_real_estate_ai.agent_system.memory.manager import memory_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Nightly Memory Consolidation...")
    
    if not memory_manager.enabled:
        logger.warning("Graphiti memory is not enabled. Aborting consolidation.")
        return

    try:
        await memory_manager.consolidate_memory()
        logger.info("Memory consolidation complete.")
    except Exception as e:
        logger.error(f"Memory consolidation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
