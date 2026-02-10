"""Background task for periodic abandonment detection and recovery.

Runs every 4 hours to scan for abandoned leads and trigger recovery sequences.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global task handle
_background_task: Optional[asyncio.Task] = None
_is_running = False


async def abandonment_detection_loop(
    ghl_client,
    db_pool,
    interval_seconds: int = 4 * 3600,  # 4 hours
) -> None:
    """Periodic loop for abandonment detection and recovery.

    Args:
        ghl_client: EnhancedGHLClient for GHL API access
        db_pool: asyncpg connection pool for database access
        interval_seconds: Loop interval (default: 4 hours)
    """
    global _is_running

    from ghl_real_estate_ai.services.jorge.abandonment_detector import (
        get_abandonment_detector,
    )
    from ghl_real_estate_ai.services.jorge.recovery_orchestrator import (
        get_recovery_orchestrator,
    )

    detector = get_abandonment_detector(ghl_client=ghl_client, db_pool=db_pool)
    orchestrator = get_recovery_orchestrator(ghl_client=ghl_client)

    logger.info(
        f"Abandonment detection loop started (interval: {interval_seconds}s = {interval_seconds/3600:.1f}h)"
    )
    _is_running = True

    while _is_running:
        try:
            logger.info("Starting abandonment detection scan...")

            # Get all locations from environment or tenant service
            # For now, use primary location from settings
            from ghl_real_estate_ai.ghl_utils.config import settings

            location_id = settings.ghl_location_id

            if not location_id:
                logger.warning("No location_id configured, skipping detection")
                await asyncio.sleep(interval_seconds)
                continue

            # Detect abandoned contacts
            abandoned_contacts = await detector.detect_abandoned_contacts(
                location_id=location_id,
                max_contacts=100,
            )

            logger.info(f"Found {len(abandoned_contacts)} abandoned contacts")

            if abandoned_contacts:
                # Orchestrate recovery
                summary = await orchestrator.orchestrate_recovery(abandoned_contacts)

                logger.info(
                    f"Recovery batch complete: "
                    f"{summary['successful']}/{summary['total_attempted']} successful"
                )

                # Mark recovery attempts in database
                for contact in abandoned_contacts:
                    if any(
                        c["contact_id"] == contact.contact_id
                        and c["status"] == "success"
                        for c in summary.get("contacts_processed", [])
                    ):
                        await detector.mark_recovery_attempted(
                            contact.contact_id, contact.current_stage
                        )

            else:
                logger.info("No abandoned contacts found in this scan")

        except Exception as exc:
            logger.error(f"Abandonment detection loop error: {exc}", exc_info=True)
            # Continue running despite errors

        # Wait for next interval
        logger.info(f"Sleeping for {interval_seconds}s until next scan...")
        await asyncio.sleep(interval_seconds)

    logger.info("Abandonment detection loop stopped")


async def start_abandonment_background_task(
    ghl_client, db_pool, interval_seconds: int = 4 * 3600
) -> bool:
    """Start the abandonment detection background task.

    Args:
        ghl_client: EnhancedGHLClient instance
        db_pool: asyncpg connection pool
        interval_seconds: Loop interval (default: 4 hours)

    Returns:
        True if started successfully, False otherwise
    """
    global _background_task, _is_running

    if _background_task and not _background_task.done():
        logger.warning("Abandonment background task already running")
        return True

    try:
        _is_running = True
        _background_task = asyncio.create_task(
            abandonment_detection_loop(ghl_client, db_pool, interval_seconds)
        )
        logger.info("✅ Abandonment detection background task started")
        return True
    except Exception as exc:
        logger.error(f"Failed to start abandonment background task: {exc}")
        _is_running = False
        return False


async def stop_abandonment_background_task() -> None:
    """Stop the abandonment detection background task."""
    global _background_task, _is_running

    if not _background_task or _background_task.done():
        logger.warning("No abandonment background task running")
        return

    logger.info("Stopping abandonment detection background task...")
    _is_running = False

    # Wait for task to finish gracefully (with timeout)
    try:
        await asyncio.wait_for(_background_task, timeout=10.0)
    except asyncio.TimeoutError:
        logger.warning("Abandonment task did not stop gracefully, cancelling...")
        _background_task.cancel()
        try:
            await _background_task
        except asyncio.CancelledError:
            pass

    logger.info("Abandonment detection background task stopped")


def is_abandonment_task_running() -> bool:
    """Check if abandonment background task is running."""
    return _is_running and _background_task is not None and not _background_task.done()
