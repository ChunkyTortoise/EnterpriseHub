"""
Celery tasks for freelance job monitoring automation.

Wraps scripts/upwork_job_monitor.py for execution via Celery Beat scheduler.
Falls back gracefully if feedparser/requests aren't installed in the worker env.
"""

import subprocess
import sys
from pathlib import Path

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.celery_app import app

logger = get_logger(__name__)

SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "upwork_job_monitor.py"


@app.task(name="freelance.monitor_upwork_jobs", bind=True, max_retries=2)
def monitor_upwork_jobs(self):
    """Run Upwork job monitor script as a subprocess.

    Uses subprocess to isolate dependencies (feedparser, requests) from the
    main Celery worker environment.
    """
    if not SCRIPT_PATH.exists():
        logger.error(f"Upwork monitor script not found: {SCRIPT_PATH}")
        return {"status": "error", "reason": "script_not_found"}

    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(SCRIPT_PATH.parent.parent),
        )

        if result.returncode != 0:
            logger.warning(f"Upwork monitor exited with code {result.returncode}: {result.stderr[:500]}")

        logger.info(f"Upwork monitor output: {result.stdout[:500]}")
        return {
            "status": "success" if result.returncode == 0 else "warning",
            "returncode": result.returncode,
            "stdout": result.stdout[:1000],
            "stderr": result.stderr[:500],
        }

    except subprocess.TimeoutExpired:
        logger.error("Upwork monitor timed out after 120s")
        return {"status": "error", "reason": "timeout"}
    except Exception as exc:
        logger.error(f"Upwork monitor failed: {exc}")
        raise self.retry(exc=exc, countdown=300)
