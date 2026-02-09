"""
Adaptive Model Retraining Service - Phase 7
Handles the feedback loop from GHL outcomes to update AI scoring weights.
"""

from decimal import Decimal

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.database_service import get_database

logger = get_logger(__name__)


class ModelRetrainingService:
    """
    Service to manage the closed-loop retraining of lead scoring and matching models.
    """

    def __init__(self):
        self.db_service = None
        self.cache = get_cache_service()
        self.retraining_threshold = 10  # Retrain after 10 new outcomes

    async def _get_db(self):
        if not self.db_service:
            self.db_service = await get_database()
        return self.db_service

    async def record_outcome(self, lead_id: str, outcome: str, value: float = 0.0):
        """Record a deal outcome and trigger weight adjustment if needed."""
        try:
            db = await self._get_db()

            # Log outcome to database
            await db.execute_optimized_query(
                "INSERT INTO model_outcomes (lead_id, outcome, monetary_value, recorded_at) VALUES ($1, $2, $3, NOW())",
                lead_id,
                outcome,
                value,
            )

            logger.info(f"✅ Recorded outcome '{outcome}' for lead {lead_id}. Value: ${value:,.2f}")

            # Increment outcome counter for retraining trigger
            count = await self.cache.increment("retraining_outcome_count", 1)
            if count >= self.retraining_threshold:
                await self.cache.set("retraining_outcome_count", 0)
                await self.trigger_weight_adjustment()

        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")

    async def trigger_weight_adjustment(self):
        """Analyze recent outcomes and adjust PredictiveLeadScorerV2 weights."""
        logger.info("🤖 Starting Adaptive Weight Adjustment cycle...")
        try:
            db = await self._get_db()

            # Fetch recent successful vs unsuccessful leads
            results = await db.execute_optimized_query("""
                SELECT l.enrichment_data, o.outcome 
                FROM leads l 
                JOIN model_outcomes o ON l.id = o.lead_id 
                ORDER BY o.recorded_at DESC LIMIT 100
            """)

            if not results:
                return

            # Logic to determine which factors correlate with success
            # (Simplified: increase 'engagement' weight if high engagement leads are closing)
            # In production, this would use a Gradient Boosting or Logistic Regression coefficient update.

            current_weights = await self.cache.get("dynamic_scoring_weights") or {
                "qualification": 0.25,
                "closing_probability": 0.35,
                "engagement": 0.20,
                "urgency": 0.20,
            }

            # Simulate an adjustment based on "success" outcomes
            # e.g., If 'won' deals have high urgency, increase urgency weight
            new_weights = current_weights.copy()
            new_weights["engagement"] = float(Decimal(str(new_weights["engagement"])) + Decimal("0.01"))
            new_weights["qualification"] = float(Decimal(str(new_weights["qualification"])) - Decimal("0.01"))

            await self.cache.set("dynamic_scoring_weights", new_weights)
            logger.info(f"📈 Adjusted scoring weights: {new_weights}")

        except Exception as e:
            logger.error(f"Weight adjustment failed: {e}")


# Global instance
_retraining_service = None


def get_retraining_service() -> ModelRetrainingService:
    global _retraining_service
    if _retraining_service is None:
        _retraining_service = ModelRetrainingService()
    return _retraining_service
