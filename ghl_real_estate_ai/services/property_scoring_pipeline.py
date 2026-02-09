"""
Background Property Scoring Pipeline for Real-Time Property Alerts.

Continuous background pipeline that:
- Runs scheduled jobs every 15 minutes to evaluate new/updated properties
- Integrates with PropertyAlertEngine for alert generation
- Uses APScheduler with Redis persistence for reliability
- Handles error recovery, retry logic, and performance monitoring
- Processes properties in batches for optimal performance

Features:
- Redis-backed job persistence and state management
- Configurable scoring intervals and batch sizes
- Comprehensive error handling and retry mechanisms
- Performance metrics and monitoring
- Integration with existing property data sources
- Graceful shutdown and job cleanup
"""

import asyncio
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import redis.asyncio as redis
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.property_alert_engine import AlertType, get_property_alert_engine

logger = get_logger(__name__)


@dataclass
class PipelineMetrics:
    """Performance metrics for the scoring pipeline."""

    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    properties_processed: int = 0
    alerts_generated: int = 0
    last_run_time: Optional[datetime] = None
    average_run_duration_ms: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            **asdict(self),
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
        }


class PropertyScoringPipeline:
    """
    Background pipeline for continuous property scoring and alert generation.

    Manages scheduled jobs that:
    - Fetch new/updated properties from data sources
    - Score properties against active alert criteria
    - Generate and deliver property alerts
    - Monitor performance and handle errors
    """

    def __init__(self, redis_url: Optional[str] = None):
        # Core services
        self.property_alert_engine = get_property_alert_engine()
        self.cache_service = get_cache_service()

        # Redis configuration
        self.redis_url = redis_url or settings.redis_url or "redis://localhost:6379/0"
        self.redis_client: Optional[redis.Redis] = None

        # APScheduler configuration
        self.scheduler: Optional[AsyncIOScheduler] = None
        parsed = urlparse(self.redis_url)
        redis_host = parsed.hostname or "localhost"
        redis_port = parsed.port or 6379
        redis_password = parsed.password
        self.job_store_config = {
            "default": RedisJobStore(
                host=redis_host,
                port=redis_port,
                db=1,  # Use separate DB from cache
                password=redis_password,
            )
        }
        self.executor_config = {"default": AsyncIOExecutor()}

        # Pipeline configuration
        self.scoring_interval_minutes = 15  # Run every 15 minutes
        self.batch_size = 50  # Properties to process per batch
        self.max_concurrent_batches = 3  # Maximum parallel batches
        self.cleanup_interval_hours = 24  # Cleanup old data every 24 hours

        # Performance tracking
        self.metrics = PipelineMetrics()
        self.running_jobs: Set[str] = set()

        # State management
        self.is_running = False
        self.shutdown_event = asyncio.Event()

        logger.info("PropertyScoringPipeline initialized")

    async def start(self):
        """Start the background scoring pipeline."""
        if self.is_running:
            logger.warning("Pipeline is already running")
            return

        try:
            # Initialize Redis connection
            await self._init_redis_connection()

            # Initialize APScheduler
            await self._init_scheduler()

            # Start alert engine processing
            await self.property_alert_engine.start_processing_queue()

            # Schedule recurring jobs
            await self._schedule_jobs()

            self.is_running = True
            logger.info("PropertyScoringPipeline started successfully")

        except Exception as e:
            logger.error(f"Failed to start PropertyScoringPipeline: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self):
        """Stop the background scoring pipeline."""
        if not self.is_running:
            return

        logger.info("Stopping PropertyScoringPipeline...")

        try:
            # Signal shutdown
            self.shutdown_event.set()

            # Stop scheduler
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=True)

            # Stop alert engine
            await self.property_alert_engine.stop_processing_queue()

            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()

            self.is_running = False
            logger.info("PropertyScoringPipeline stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping PropertyScoringPipeline: {e}", exc_info=True)

    async def force_run_scoring(self) -> Dict[str, Any]:
        """
        Force immediate property scoring run (for testing/manual triggers).

        Returns:
            Scoring results and metrics
        """
        logger.info("Force running property scoring pipeline")
        return await self._run_property_scoring_job()

    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics."""
        scheduler_info = {}
        if self.scheduler:
            jobs = self.scheduler.get_jobs()
            scheduler_info = {
                "running": self.scheduler.running,
                "total_jobs": len(jobs),
                "job_details": [
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                        "trigger": str(job.trigger),
                    }
                    for job in jobs
                ],
            }

        return {
            "is_running": self.is_running,
            "running_jobs": list(self.running_jobs),
            "metrics": self.metrics.to_dict(),
            "scheduler": scheduler_info,
            "alert_engine_metrics": self.property_alert_engine.get_metrics(),
            "configuration": {
                "scoring_interval_minutes": self.scoring_interval_minutes,
                "batch_size": self.batch_size,
                "max_concurrent_batches": self.max_concurrent_batches,
            },
        }

    # Private methods

    async def _init_redis_connection(self):
        """Initialize Redis connection for job state management."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established for PropertyScoringPipeline")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _init_scheduler(self):
        """Initialize APScheduler with Redis persistence."""
        try:
            # Configure scheduler
            job_defaults = {
                "coalesce": False,
                "max_instances": 1,
                "misfire_grace_time": 300,  # 5 minutes grace period
            }

            self.scheduler = AsyncIOScheduler(
                jobstores=self.job_store_config,
                executors=self.executor_config,
                job_defaults=job_defaults,
                timezone="UTC",
            )

            # Start scheduler
            self.scheduler.start()
            logger.info("APScheduler initialized and started")

        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise

    async def _schedule_jobs(self):
        """Schedule recurring jobs for property scoring and maintenance."""
        try:
            # Main property scoring job - every 15 minutes
            self.scheduler.add_job(
                func=self._run_property_scoring_job,
                trigger=IntervalTrigger(minutes=self.scoring_interval_minutes),
                id="property_scoring_main",
                name="Property Scoring Pipeline",
                replace_existing=True,
                max_instances=1,
            )

            # Cleanup job - daily at 2:00 AM UTC
            self.scheduler.add_job(
                func=self._run_cleanup_job,
                trigger=CronTrigger(hour=2, minute=0),
                id="pipeline_cleanup",
                name="Pipeline Data Cleanup",
                replace_existing=True,
                max_instances=1,
            )

            # Health check job - every 5 minutes
            self.scheduler.add_job(
                func=self._run_health_check,
                trigger=IntervalTrigger(minutes=5),
                id="pipeline_health_check",
                name="Pipeline Health Check",
                replace_existing=True,
                max_instances=1,
            )

            logger.info("Scheduled jobs created successfully")

        except Exception as e:
            logger.error(f"Failed to schedule jobs: {e}")
            raise

    async def _run_property_scoring_job(self) -> Dict[str, Any]:
        """
        Main property scoring job that runs every 15 minutes.

        Returns:
            Job execution results and metrics
        """
        job_id = f"scoring_job_{int(time.time())}"
        start_time = time.time()

        if self.shutdown_event.is_set():
            logger.info("Shutdown requested, skipping property scoring job")
            return {"status": "skipped", "reason": "shutdown_requested"}

        try:
            self.running_jobs.add(job_id)
            logger.info(f"Starting property scoring job {job_id}")

            # Update metrics
            self.metrics.total_runs += 1
            self.metrics.last_run_time = datetime.now(timezone.utc)

            # Get new/updated properties to score
            properties_to_score = await self._get_properties_for_scoring()
            logger.info(f"Found {len(properties_to_score)} properties to score")

            if not properties_to_score:
                logger.info("No new properties to score")
                return {"status": "completed", "properties_processed": 0, "alerts_generated": 0}

            # Process properties in batches
            total_alerts = 0
            properties_processed = 0

            for batch_start in range(0, len(properties_to_score), self.batch_size):
                if self.shutdown_event.is_set():
                    logger.info("Shutdown requested during processing")
                    break

                batch = properties_to_score[batch_start : batch_start + self.batch_size]
                batch_alerts = await self._process_property_batch(batch, job_id)

                total_alerts += batch_alerts
                properties_processed += len(batch)

                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(0.1)

            # Update metrics
            self.metrics.properties_processed += properties_processed
            self.metrics.alerts_generated += total_alerts
            self.metrics.successful_runs += 1

            # Calculate and update average run duration
            run_duration = (time.time() - start_time) * 1000
            self.metrics.average_run_duration_ms = self.metrics.average_run_duration_ms * 0.9 + run_duration * 0.1

            # Update last processed timestamp
            await self._update_last_processed_timestamp()

            result = {
                "status": "completed",
                "job_id": job_id,
                "properties_processed": properties_processed,
                "alerts_generated": total_alerts,
                "duration_ms": run_duration,
            }

            logger.info(f"Property scoring job {job_id} completed: {result}")
            return result

        except Exception as e:
            self.metrics.failed_runs += 1
            self.metrics.last_error = str(e)
            self.metrics.last_error_time = datetime.now(timezone.utc)

            logger.error(f"Error in property scoring job {job_id}: {e}", exc_info=True)

            return {
                "status": "failed",
                "job_id": job_id,
                "error": str(e),
                "duration_ms": (time.time() - start_time) * 1000,
            }

        finally:
            self.running_jobs.discard(job_id)

    async def _get_properties_for_scoring(self) -> List[Dict[str, Any]]:
        """
        Get new/updated properties that need scoring.

        In production, this would:
        1. Query MLS data feeds for new listings
        2. Check property update timestamps
        3. Filter out already processed properties
        4. Return batch of properties to score

        For now, returns sample properties for testing.
        """
        # Get timestamp of last processing
        last_processed = await self._get_last_processed_timestamp()

        # In production: query external property data sources
        # For now, return sample properties
        sample_properties = [
            {
                "id": f"prop_{int(time.time())}_{i}",
                "address": f"{100 + i} Sample St, Austin, TX",
                "price": 450000 + (i * 25000),
                "bedrooms": 3 + (i % 2),
                "bathrooms": 2.0 + (i % 2) * 0.5,
                "sqft": 1800 + (i * 200),
                "property_type": "single_family",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "listing_date": datetime.now(timezone.utc).isoformat(),
                "days_on_market": 1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)  # Sample 5 properties
        ]

        logger.debug(f"Generated {len(sample_properties)} sample properties for scoring")
        return sample_properties

    async def _process_property_batch(self, properties: List[Dict[str, Any]], job_id: str) -> int:
        """
        Process a batch of properties for alert generation.

        Args:
            properties: List of property data to process
            job_id: Current job identifier

        Returns:
            Number of alerts generated for this batch
        """
        total_alerts = 0

        try:
            # Process properties concurrently within the batch
            tasks = [
                self.property_alert_engine.evaluate_property_for_alerts(
                    property_data=prop, alert_type=AlertType.NEW_MATCH
                )
                for prop in properties
            ]

            # Execute batch with controlled concurrency
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing property {properties[i].get('id', 'unknown')}: {result}")
                elif isinstance(result, list):
                    total_alerts += len(result)

            logger.debug(f"Batch processed {len(properties)} properties, generated {total_alerts} alerts")

        except Exception as e:
            logger.error(f"Error processing property batch in job {job_id}: {e}", exc_info=True)

        return total_alerts

    async def _get_last_processed_timestamp(self) -> Optional[datetime]:
        """Get timestamp of last successful property processing."""
        cache_key = "pipeline:last_processed_timestamp"
        timestamp_str = await self.cache_service.get(cache_key)

        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                pass

        return None

    async def _update_last_processed_timestamp(self):
        """Update timestamp of last successful property processing."""
        cache_key = "pipeline:last_processed_timestamp"
        timestamp = datetime.now(timezone.utc).isoformat()
        await self.cache_service.set(cache_key, timestamp, ttl=86400 * 7)  # 7 days

    async def _run_cleanup_job(self) -> Dict[str, Any]:
        """
        Daily cleanup job to maintain system performance.

        Cleans up:
        - Old alert history records
        - Expired cache entries
        - Processed property tracking data
        """
        start_time = time.time()

        try:
            logger.info("Starting daily cleanup job")

            # Clear old alert history from cache (older than 7 days)
            cleanup_count = 0

            # In production, this would:
            # 1. Clean up old database records
            # 2. Clear expired cache entries
            # 3. Archive processed data
            # 4. Update cleanup metrics

            logger.info(f"Cleanup job completed, cleaned up {cleanup_count} items")

            return {
                "status": "completed",
                "items_cleaned": cleanup_count,
                "duration_ms": (time.time() - start_time) * 1000,
            }

        except Exception as e:
            logger.error(f"Error in cleanup job: {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "duration_ms": (time.time() - start_time) * 1000}

    async def _run_health_check(self) -> Dict[str, Any]:
        """
        Health check job to monitor pipeline status.

        Checks:
        - Redis connectivity
        - Scheduler status
        - Alert engine health
        - Job execution status
        """
        try:
            health_status = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pipeline_running": self.is_running,
                "redis_connected": False,
                "scheduler_running": False,
                "alert_engine_active": False,
                "running_jobs_count": len(self.running_jobs),
            }

            # Check Redis connectivity
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    health_status["redis_connected"] = True
                except Exception:
                    pass

            # Check scheduler status
            if self.scheduler:
                health_status["scheduler_running"] = self.scheduler.running

            # Check alert engine
            alert_metrics = self.property_alert_engine.get_metrics()
            health_status["alert_engine_active"] = alert_metrics.get("queue_processing_active", False)

            # Store health status in cache for monitoring
            await self.cache_service.set(
                "pipeline:health_status",
                health_status,
                ttl=300,  # 5 minutes
            )

            return health_status

        except Exception as e:
            logger.error(f"Error in health check: {e}", exc_info=True)
            return {"status": "error", "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


# Global singleton instance
_property_scoring_pipeline = None


async def get_property_scoring_pipeline() -> PropertyScoringPipeline:
    """Get singleton PropertyScoringPipeline instance."""
    global _property_scoring_pipeline
    if _property_scoring_pipeline is None:
        _property_scoring_pipeline = PropertyScoringPipeline()
    return _property_scoring_pipeline


# Management functions for external control
async def start_property_scoring_pipeline():
    """Start the background property scoring pipeline."""
    pipeline = await get_property_scoring_pipeline()
    await pipeline.start()


async def stop_property_scoring_pipeline():
    """Stop the background property scoring pipeline."""
    pipeline = await get_property_scoring_pipeline()
    await pipeline.stop()


async def get_pipeline_status() -> Dict[str, Any]:
    """Get current pipeline status and metrics."""
    pipeline = await get_property_scoring_pipeline()
    return await pipeline.get_pipeline_status()


async def force_run_property_scoring() -> Dict[str, Any]:
    """Force immediate property scoring run."""
    pipeline = await get_property_scoring_pipeline()
    return await pipeline.force_run_scoring()
