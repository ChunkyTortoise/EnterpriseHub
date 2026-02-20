"""
Scheduler Startup Service - Initializes and starts Lead Sequence Scheduler

Integrates with FastAPI app lifecycle to ensure scheduler is running.
Provides health check endpoints and manual trigger capabilities.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.lead_sequence_scheduler import LeadSequenceScheduler, get_lead_scheduler

logger = get_logger(__name__)


class SchedulerStartupService:
    """
    Manages Lead Sequence Scheduler lifecycle

    Ensures scheduler starts with FastAPI app and provides
    health monitoring and manual trigger capabilities.
    """

    def __init__(self):
        self.scheduler: Optional[LeadSequenceScheduler] = None
        self.started_at: Optional[datetime] = None
        self.health_status: str = "not_started"
        self.last_error: Optional[str] = None

    async def initialize_scheduler(self) -> bool:
        """
        Initialize and start the Lead Sequence Scheduler

        This should be called during FastAPI app startup.
        """
        try:
            logger.info("Initializing Lead Sequence Scheduler...")

            # Get scheduler instance
            self.scheduler = get_lead_scheduler()

            if not self.scheduler or not self.scheduler.enabled:
                error_msg = "Lead Sequence Scheduler is not enabled (missing dependencies or configuration)"
                logger.error(error_msg)
                self.health_status = "disabled"
                self.last_error = error_msg
                return False

            # Start the scheduler
            success = await self.scheduler.start()

            if success:
                self.started_at = datetime.now()
                self.health_status = "healthy"
                self.last_error = None
                logger.info("✅ Lead Sequence Scheduler started successfully")

                # Register daily digest job (7am PT)
                try:
                    import os

                    from ghl_real_estate_ai.services.jorge.digest_service import DigestService
                    _digest = DigestService()
                    await _digest.schedule_daily_digest(
                        self.scheduler.scheduler,
                        recipient_email=os.getenv("JORGE_DIGEST_EMAIL", "realtorjorgesalas@gmail.com"),
                    )
                    logger.info("✅ Daily digest job registered (7am PT)")
                except Exception as _digest_err:
                    logger.warning(f"Daily digest registration failed (non-fatal): {_digest_err}")

                return True
            else:
                error_msg = "Failed to start Lead Sequence Scheduler"
                logger.error(error_msg)
                self.health_status = "failed"
                self.last_error = error_msg
                return False

        except Exception as e:
            error_msg = f"Exception initializing scheduler: {str(e)}"
            logger.error(error_msg)
            self.health_status = "error"
            self.last_error = error_msg
            return False

    async def shutdown_scheduler(self):
        """
        Gracefully shutdown the scheduler

        This should be called during FastAPI app shutdown.
        """
        try:
            if self.scheduler and hasattr(self.scheduler, "scheduler") and self.scheduler.scheduler.running:
                logger.info("Shutting down Lead Sequence Scheduler...")
                self.scheduler.scheduler.shutdown(wait=True)
                self.health_status = "stopped"
                logger.info("✅ Lead Sequence Scheduler shut down successfully")

        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status of the scheduler

        Returns comprehensive health information for monitoring.
        """
        try:
            # Basic status info
            status_info = {
                "status": self.health_status,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "last_error": self.last_error,
                "scheduler_enabled": self.scheduler.enabled if self.scheduler else False,
            }

            # Add scheduler-specific details if available
            if self.scheduler and hasattr(self.scheduler, "scheduler"):
                scheduler = self.scheduler.scheduler
                status_info.update(
                    {
                        "scheduler_running": scheduler.running if hasattr(scheduler, "running") else False,
                        "job_count": len(scheduler.get_jobs()) if hasattr(scheduler, "get_jobs") else 0,
                        "scheduler_state": str(scheduler.state) if hasattr(scheduler, "state") else "unknown",
                    }
                )

                # Get active jobs info
                if hasattr(scheduler, "get_jobs"):
                    try:
                        jobs = scheduler.get_jobs()
                        job_info = []
                        for job in jobs[:10]:  # Limit to first 10 jobs
                            job_info.append(
                                {
                                    "id": job.id,
                                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                                    "function": job.func.__name__ if hasattr(job.func, "__name__") else str(job.func),
                                }
                            )
                        status_info["active_jobs"] = job_info
                    except Exception as e:
                        logger.error(f"Error getting job details: {e}")
                        status_info["job_details_error"] = str(e)

            return status_info

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {"status": "error", "error": str(e), "scheduler_enabled": False}

    async def trigger_manual_test(self, lead_id: str = "test-lead-1") -> Dict[str, Any]:
        """
        Manually trigger a test sequence for validation

        Useful for testing the scheduler without waiting for scheduled times.
        """
        try:
            if not self.scheduler or not self.scheduler.enabled:
                return {"success": False, "error": "Scheduler not available or not enabled"}

            logger.info(f"Triggering manual test sequence for lead {lead_id}")

            # Create a test sequence
            from ghl_real_estate_ai.services.lead_sequence_state_service import SequenceDay

            result = await self.scheduler.schedule_sequence_start(
                lead_id=lead_id,
                sequence_day=SequenceDay.DAY_3,
                delay_minutes=0,  # Immediate execution
            )

            if result:
                logger.info(f"Successfully triggered test sequence for lead {lead_id}")
                return {
                    "success": True,
                    "message": f"Test sequence triggered for lead {lead_id}",
                    "lead_id": lead_id,
                    "triggered_at": datetime.now().isoformat(),
                }
            else:
                error_msg = f"Failed to trigger test sequence for lead {lead_id}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Exception triggering manual test: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def get_scheduler_metrics(self) -> Dict[str, Any]:
        """
        Get detailed scheduler performance metrics

        Provides insights into scheduler operation for monitoring.
        """
        try:
            if not self.scheduler or not hasattr(self.scheduler, "scheduler"):
                return {"error": "Scheduler not available"}

            scheduler = self.scheduler.scheduler

            # Basic metrics
            metrics = {
                "uptime_seconds": (datetime.now() - self.started_at).total_seconds() if self.started_at else 0,
                "status": self.health_status,
                "total_jobs": 0,
                "pending_jobs": 0,
                "next_job_time": None,
                "job_types": {},
            }

            # Job analysis
            if hasattr(scheduler, "get_jobs"):
                jobs = scheduler.get_jobs()
                metrics["total_jobs"] = len(jobs)

                # Count job types and find next execution
                job_type_counts = {}
                next_run_time = None

                for job in jobs:
                    # Extract job type from job ID pattern
                    job_type = "unknown"
                    if "sms" in job.id:
                        job_type = "sms"
                    elif "call" in job.id:
                        job_type = "call"
                    elif "email" in job.id:
                        job_type = "email"

                    job_type_counts[job_type] = job_type_counts.get(job_type, 0) + 1

                    # Track next run time
                    if job.next_run_time:
                        if not next_run_time or job.next_run_time < next_run_time:
                            next_run_time = job.next_run_time

                metrics["job_types"] = job_type_counts
                metrics["next_job_time"] = next_run_time.isoformat() if next_run_time else None
                metrics["pending_jobs"] = sum(job_type_counts.values())

            return metrics

        except Exception as e:
            logger.error(f"Error getting scheduler metrics: {e}")
            return {"error": str(e)}

    async def restart_scheduler(self) -> Dict[str, Any]:
        """
        Restart the scheduler (useful for recovery from errors)

        Performs graceful shutdown and restart.
        """
        try:
            logger.info("Restarting Lead Sequence Scheduler...")

            # Shutdown current scheduler
            await self.shutdown_scheduler()

            # Wait a moment
            await asyncio.sleep(2)

            # Reinitialize
            success = await self.initialize_scheduler()

            if success:
                return {
                    "success": True,
                    "message": "Scheduler restarted successfully",
                    "restarted_at": datetime.now().isoformat(),
                }
            else:
                return {"success": False, "error": self.last_error or "Unknown error during restart"}

        except Exception as e:
            error_msg = f"Exception during scheduler restart: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def is_healthy(self) -> bool:
        """Quick health check for load balancers"""
        return self.health_status == "healthy"


# Singleton instance
_scheduler_startup_service = None


def get_scheduler_startup_service() -> SchedulerStartupService:
    """Get singleton SchedulerStartupService instance"""
    global _scheduler_startup_service
    if _scheduler_startup_service is None:
        _scheduler_startup_service = SchedulerStartupService()
    return _scheduler_startup_service


# Convenience functions for FastAPI integration
async def initialize_lead_scheduler() -> bool:
    """Initialize the lead scheduler (for FastAPI startup)"""
    service = get_scheduler_startup_service()
    return await service.initialize_scheduler()


async def shutdown_lead_scheduler():
    """Shutdown the lead scheduler (for FastAPI shutdown)"""
    service = get_scheduler_startup_service()
    await service.shutdown_scheduler()


def get_lead_scheduler_health() -> Dict[str, Any]:
    """Get scheduler health status (for health check endpoint)"""
    service = get_scheduler_startup_service()
    return service.get_health_status()
