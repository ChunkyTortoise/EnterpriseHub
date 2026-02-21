"""
Lead Source ROI Background Task

Periodically updates source metrics aggregation table for dashboard display.
Runs as a background task in the FastAPI app lifecycle.

Usage:
    task_started = await start_source_roi_background_task(db_pool, interval_seconds=86400)
    # ... later ...
    await stop_source_roi_background_task()
"""

import asyncio
from typing import Any, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.jorge.source_tracker import SourceTracker

logger = get_logger(__name__)

# Global task handle
_source_roi_task: Optional[asyncio.Task] = None
_task_running = False


async def _source_roi_update_loop(
    source_tracker: SourceTracker,
    interval_seconds: int,
) -> None:
    """Background loop to update source ROI metrics.

    Args:
        source_tracker: SourceTracker instance
        interval_seconds: Update interval in seconds
    """
    global _task_running

    logger.info(f"Source ROI update loop started (interval: {interval_seconds}s)")

    while _task_running:
        try:
            logger.debug("Updating source ROI metrics...")

            # Update aggregated metrics table
            await source_tracker.update_source_metrics_table()

            logger.info("✅ Source ROI metrics updated successfully")

        except asyncio.CancelledError:
            logger.info("Source ROI update loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error updating source ROI metrics: {e}", exc_info=True)

        # Wait for next interval
        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("Source ROI update loop sleep cancelled")
            break


async def start_source_roi_background_task(
    db_pool: Optional[Any] = None,
    interval_seconds: int = 86400,  # Default: once per day
) -> bool:
    """Start the source ROI background task.

    Args:
        db_pool: Database connection pool
        interval_seconds: Update interval (default: 86400 = 24 hours)

    Returns:
        True if task started successfully, False otherwise
    """
    global _source_roi_task, _task_running

    if _task_running:
        logger.warning("Source ROI background task already running")
        return True

    if not db_pool:
        logger.warning("No database pool provided - source ROI tracking disabled")
        return False

    try:
        # Create mock DB service wrapper
        class DBServiceWrapper:
            """Wrapper to adapt db_pool to service interface."""

            def __init__(self, pool):
                self._pool = pool

            async def execute(self, query: str, *args):
                """Execute query."""
                async with self._pool.acquire() as conn:
                    return await conn.execute(query, *args)

            async def fetch(self, query: str, *args):
                """Fetch multiple rows."""
                async with self._pool.acquire() as conn:
                    return await conn.fetch(query, *args)

            async def fetchrow(self, query: str, *args):
                """Fetch single row."""
                async with self._pool.acquire() as conn:
                    return await conn.fetchrow(query, *args)

        db_service = DBServiceWrapper(db_pool)

        # Initialize source tracker
        source_tracker = SourceTracker(db_service=db_service)

        # Start background task
        _task_running = True
        _source_roi_task = asyncio.create_task(_source_roi_update_loop(source_tracker, interval_seconds))

        logger.info(f"✅ Source ROI background task started (interval: {interval_seconds}s)")
        return True

    except Exception as e:
        logger.error(f"Failed to start source ROI background task: {e}", exc_info=True)
        _task_running = False
        return False


async def stop_source_roi_background_task() -> None:
    """Stop the source ROI background task."""
    global _source_roi_task, _task_running

    if not _task_running:
        logger.debug("Source ROI background task not running")
        return

    logger.info("Stopping source ROI background task...")
    _task_running = False

    if _source_roi_task and not _source_roi_task.done():
        _source_roi_task.cancel()

        try:
            await _source_roi_task
        except asyncio.CancelledError:
            logger.info("Source ROI background task cancelled successfully")
        except Exception as e:
            logger.warning(f"Error stopping source ROI task: {e}")

    _source_roi_task = None
    logger.info("Source ROI background task stopped")
