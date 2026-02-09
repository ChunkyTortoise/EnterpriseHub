"""
Service Manager - Centralized management of background services.

Provides utilities for starting and managing background services like the lead sequence scheduler.
"""

import asyncio

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


async def initialize_services():
    """Initialize all background services."""
    try:
        # Initialize lead sequence scheduler
        from ghl_real_estate_ai.services.lead_sequence_scheduler import start_lead_scheduler

        scheduler_started = await start_lead_scheduler()
        if scheduler_started:
            logger.info("✅ Lead sequence scheduler started successfully")
        else:
            logger.warning("⚠️ Lead sequence scheduler failed to start")

        return scheduler_started

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        return False


async def shutdown_services():
    """Gracefully shutdown all background services."""
    try:
        from ghl_real_estate_ai.services.lead_sequence_scheduler import stop_lead_scheduler

        await stop_lead_scheduler()
        logger.info("✅ All services shutdown gracefully")

    except Exception as e:
        logger.error(f"❌ Error during services shutdown: {e}")


if __name__ == "__main__":
    # Allow running this module directly for testing
    async def main():
        print("Starting services...")
        success = await initialize_services()

        if success:
            print("Services started successfully. Press Ctrl+C to stop.")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping services...")
                await shutdown_services()
                print("Services stopped.")
        else:
            print("Failed to start services.")

    asyncio.run(main())
