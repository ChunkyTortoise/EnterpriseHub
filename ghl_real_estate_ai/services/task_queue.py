"""Redis RQ-backed task queue for reliable async operations."""

import asyncio
import json
import time
from typing import Any, Callable, Optional

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

RETRY_DELAYS = [1, 5, 30, 300]  # 1s, 5s, 30s, 5min
DLQ_KEY = "lyrio:dlq"


class TaskQueue:
    """Enqueue background tasks via Redis RQ with sync fallback."""

    def __init__(self, redis_url: Optional[str] = None):
        self._redis = None
        self._available = False
        try:
            import redis

            url = redis_url or getattr(settings, "redis_url", None)
            if url:
                self._redis = redis.from_url(url, decode_responses=True, socket_timeout=2.0)
                self._redis.ping()
                self._available = True
        except Exception as exc:
            logger.warning("TaskQueue: Redis unavailable (%s), tasks will run synchronously", exc)
            self._redis = None
            self._available = False

    async def enqueue(self, func: Callable, *args: Any, **kwargs: Any) -> str:
        """Enqueue a task. Returns job_id or runs sync if Redis unavailable."""
        if not self._available:
            logger.warning("Redis unavailable, running task synchronously")
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
            return "sync"

        try:
            from rq import Queue, Retry

            q = Queue("lyrio-tasks", connection=self._redis)
            job = q.enqueue(
                func,
                *args,
                **kwargs,
                retry=Retry(max=4, interval=RETRY_DELAYS),
            )
            return job.id
        except ImportError:
            logger.warning("rq not installed, running task synchronously")
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
            return "sync-no-rq"
        except Exception as e:
            logger.error("Failed to enqueue task: %s", e)
            return "error"

    def get_dlq_jobs(self) -> dict:
        """Get dead letter queue stats."""
        if not self._redis:
            return {"count": 0, "jobs": []}
        try:
            count = self._redis.llen(DLQ_KEY)
            raw = self._redis.lrange(DLQ_KEY, 0, 9)
            jobs = [json.loads(j) for j in raw]
            return {"count": count, "jobs": jobs}
        except Exception:
            return {"count": 0, "jobs": []}


task_queue = TaskQueue()
