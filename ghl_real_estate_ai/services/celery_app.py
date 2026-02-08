"""
Celery Application for Jorge's Real Estate AI Platform

Provides distributed background job processing for horizontal scaling:
- Property scoring and matching
- Lead automation sequences
- Email and SMS processing
- Real-time analytics computation
- Data synchronization tasks
- Scheduled bot operations

Optimized for 10,000+ concurrent users with Redis backend
and distributed worker architecture.
"""

import os

from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Celery configuration
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Create Celery app
app = Celery(
    "jorge_real_estate_ai",
    broker=broker_url,
    backend=result_backend,
    include=[
        "ghl_real_estate_ai.services.celery_tasks.property_tasks",
        "ghl_real_estate_ai.services.celery_tasks.lead_tasks",
        "ghl_real_estate_ai.services.celery_tasks.bot_tasks",
        "ghl_real_estate_ai.services.celery_tasks.analytics_tasks",
        "ghl_real_estate_ai.services.celery_tasks.notification_tasks",
    ],
)

# Celery configuration for horizontal scaling
app.conf.update(
    # Task routing for distributed processing
    task_routes={
        "property.*": {"queue": "property_processing"},
        "lead.*": {"queue": "lead_automation"},
        "bot.*": {"queue": "bot_operations"},
        "analytics.*": {"queue": "analytics_compute"},
        "notification.*": {"queue": "notifications"},
    },
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("property_processing", routing_key="property.#"),
        Queue("lead_automation", routing_key="lead.#"),
        Queue("bot_operations", routing_key="bot.#"),
        Queue("analytics_compute", routing_key="analytics.#"),
        Queue("notifications", routing_key="notification.#"),
        Queue("high_priority", routing_key="urgent.#"),
    ),
    # Performance optimization
    worker_prefetch_multiplier=1,  # Disable prefetching for better load distribution
    task_acks_late=True,  # Acknowledge after task completion
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    task_ignore_result=False,
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
    # Worker settings for scaling
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory management)
    worker_concurrency=4,  # 4 concurrent tasks per worker
    # Beat schedule for periodic tasks
    beat_schedule={
        # Property scoring every 15 minutes
        "property-scoring": {
            "task": "property.score_new_properties",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "property_processing"},
        },
        # Lead sequence automation (hourly)
        "lead-automation": {
            "task": "lead.process_sequence_automation",
            "schedule": crontab(minute=0),
            "options": {"queue": "lead_automation"},
        },
        # Jorge bot health checks (every 5 minutes)
        "bot-health-check": {
            "task": "bot.health_check_all_bots",
            "schedule": crontab(minute="*/5"),
            "options": {"queue": "bot_operations"},
        },
        # Analytics computation (every 30 minutes)
        "analytics-computation": {
            "task": "analytics.compute_performance_metrics",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "analytics_compute"},
        },
        # Daily lead scoring model update
        "ml-model-update": {
            "task": "analytics.update_ml_models",
            "schedule": crontab(hour=2, minute=0),  # 2 AM daily
            "options": {"queue": "analytics_compute"},
        },
        # Cleanup old data (weekly)
        "data-cleanup": {
            "task": "analytics.cleanup_old_data",
            "schedule": crontab(hour=1, minute=0, day_of_week=0),  # Sunday 1 AM
            "options": {"queue": "analytics_compute"},
        },
    },
)


# Task retry configuration
class BaseTaskConfig:
    """Base configuration for all Celery tasks"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True


# Apply base configuration to app
app.conf.task_inherit_parent_config = True


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f"Request: {self.request!r}")
    logger.info(f"Celery debug task executed on worker: {self.request.hostname}")
    return {"status": "success", "worker": self.request.hostname}


# Health check task
@app.task(name="celery.health_check")
def health_check():
    """Health check task for monitoring"""
    return {
        "status": "healthy",
        "timestamp": app.now(),
        "broker": app.conf.broker_url,
        "backend": app.conf.result_backend,
    }


# Startup logging
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup logging when Celery starts"""
    logger.info("Jorge's Real Estate AI Celery app configured successfully")
    logger.info(f"Broker: {broker_url}")
    logger.info(f"Backend: {result_backend}")
    logger.info("Scheduled tasks:")
    for name, task_info in app.conf.beat_schedule.items():
        logger.info(f"  - {name}: {task_info['task']} ({task_info['schedule']})")


# Worker initialization
@app.signals.worker_ready.connect
def worker_ready(sender=None, **kwargs):
    """Called when worker is ready to receive tasks"""
    logger.info(f"Celery worker ready: {sender.hostname}")


# Task success logging
@app.signals.task_success.connect
def task_success(sender=None, **kwargs):
    """Log successful task completion"""
    logger.debug(f"Task {sender.name} completed successfully")


# Task failure logging
@app.signals.task_failure.connect
def task_failure(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Log task failures for monitoring"""
    logger.error(f"Task {sender.name} ({task_id}) failed: {exception}")


# Export the app
if __name__ == "__main__":
    app.start()
