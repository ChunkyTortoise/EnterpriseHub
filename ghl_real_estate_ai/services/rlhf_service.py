"""
RLHF (Reinforcement Learning from Human Feedback) Service
Manages Jorge's explicit feedback (thumbs up/down) for agent responses.
Integrates with LangSmith for trace tracking and weekly retraining.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class RLHFService:
    def __init__(self, feedback_dir: str = "data/rlhf"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback_log.json"

        # Initialize LangSmith environment variables if present
        self.langsmith_enabled = os.getenv("LANGCHAIN_TRACING_V2") == "true"
        if self.langsmith_enabled:
            logger.info("LangSmith integration enabled for RLHF Service.")

    async def record_feedback(
        self,
        trace_id: str,
        rating: int,  # 1 for positive, -1 for negative
        feedback_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Records human feedback for a specific trace or response.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "trace_id": trace_id,
            "rating": rating,
            "feedback_text": feedback_text,
            "context": context or {},
            "status": "pending_retraining",
        }

        # Save to local log
        await self._save_to_log(entry)

        # In production, this would also send to LangSmith
        if self.langsmith_enabled:
            await self._send_to_langsmith(trace_id, rating, feedback_text)

        logger.info(f"Feedback recorded for trace {trace_id}: rating={rating}")
        return {"success": True, "message": "Feedback recorded."}

    async def _save_to_log(self, entry: Dict[str, Any]):
        """Persist feedback to a local JSON line log."""
        try:
            with open(self.feedback_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to save RLHF feedback: {e}")

    async def _send_to_langsmith(self, trace_id: str, rating: int, feedback_text: Optional[str]):
        """Simulates sending feedback to LangSmith."""
        # This would use langsmith.Client().create_feedback()
        logger.info(f"[SIMULATED] Sending feedback to LangSmith for trace {trace_id}")

    def get_feedback_summary(self) -> Dict[str, Any]:
        """Calculates stats for Jorge's weekly review."""
        if not self.feedback_file.exists():
            return {"total_feedback": 0, "positive_rate": 0, "needs_review": 0}

        stats = {"total": 0, "positive": 0, "negative": 0, "pending": 0}

        with open(self.feedback_file, "r") as f:
            for line in f:
                data = json.loads(line)
                stats["total"] += 1
                if data["rating"] > 0:
                    stats["positive"] += 1
                else:
                    stats["negative"] += 1
                if data["status"] == "pending_retraining":
                    stats["pending"] += 1

        return {
            "total_feedback": stats["total"],
            "positive_rate": (stats["positive"] / stats["total"]) if stats["total"] > 0 else 0,
            "needs_review": stats["pending"],
        }

    async def run_weekly_retraining_simulation(self) -> Dict[str, Any]:
        """
        Simulates the weekly model retraining process using the accumulated RLHF data.
        """
        summary = self.get_feedback_summary()
        if summary["total_feedback"] == 0:
            return {"success": False, "message": "No new feedback data for retraining."}

        logger.info(f"🚀 Starting Weekly Retraining Simulation with {summary['total_feedback']} samples.")

        # 1. Extract negative samples for prompt optimization
        # 2. Update model instructions/parameters (simulated)

        # Mark all as 'completed'
        # In a real run, we would read, update, then write back.

        return {
            "success": True,
            "samples_processed": summary["total_feedback"],
            "model_lift_estimate": "+2.5%",
            "timestamp": datetime.now().isoformat(),
        }


_rlhf_service = None


def get_rlhf_service() -> RLHFService:
    global _rlhf_service
    if _rlhf_service is None:
        _rlhf_service = RLHFService()
    return _rlhf_service
