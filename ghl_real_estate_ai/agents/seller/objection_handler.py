"""
Objection handling service for Jorge Seller Bot.

Phase 2.2: Handles seller objections with graduated responses.
"""

import hashlib
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.prompts.objection_responses import get_variant_count
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher
from ghl_real_estate_ai.services.jorge.pricing_objection_engine import ResponseGraduation, get_pricing_objection_engine

try:
    from ghl_real_estate_ai.repositories.jorge_metrics_repository import JorgeMetricsRepository
    REPO_AVAILABLE = True
except ImportError:
    REPO_AVAILABLE = False
    JorgeMetricsRepository = None

import os

logger = get_logger(__name__)


class ObjectionHandler:
    """Service for handling seller objections with graduated responses."""

    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        self.event_publisher = event_publisher or get_event_publisher()

    async def handle_objection(self, state: JorgeSellerState) -> Dict[str, Any]:
        """
        Phase 2.2: Handle seller objections with graduated responses.

        Detects objections across 6 categories (pricing, timing, competition,
        trust, authority, value) and provides tailored responses using
        A/B-tested variants.

        Graceful fallback: never blocks workflow if objection handling fails.
        """
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="handle_objection",
        )

        objection_detected = False
        objection_response_text = None
        objection_metadata = {}

        try:
            engine = get_pricing_objection_engine()

            # Get last seller message
            last_msg = ""
            if state.get("conversation_history"):
                for msg in reversed(state["conversation_history"]):
                    if msg.get("role") == "user":
                        last_msg = msg.get("content", "")
                        break

            if not last_msg:
                return {"objection_detected": False}

            # Detect objection
            detection = engine.detect_objection(last_msg)

            if detection.detected and detection.confidence >= 0.7:
                logger.info(
                    f"Objection detected for {state['lead_id']}: "
                    f"{detection.objection_category.value}/{detection.objection_type.value} "
                    f"(confidence: {detection.confidence:.2f})"
                )

                objection_detected = True
                objection_metadata = {
                    "objection_type": detection.objection_type.value,
                    "objection_category": detection.objection_category.value if detection.objection_category else None,
                    "confidence": detection.confidence,
                    "matched_text": detection.matched_text,
                }

                # Get A/B test variant for objection responses
                variant_index = 0
                try:
                    seller_id = state.get("lead_id", "unknown")
                    # Use contact ID hash to deterministically assign variant
                    hash_val = int(hashlib.md5(seller_id.encode()).hexdigest(), 16)

                    # Get current graduation level
                    grad_level_idx = engine.get_graduation_level(seller_id, detection.objection_type)
                    graduation_order = list(ResponseGraduation)
                    graduation_level = graduation_order[min(grad_level_idx, len(graduation_order) - 1)]

                    variant_count = get_variant_count(detection.objection_type, graduation_level)
                    if variant_count > 1:
                        variant_index = hash_val % variant_count
                except Exception as e:
                    logger.warning(f"Failed to assign A/B variant, using default: {e}")

                # Gather market data for template interpolation
                market_data = {}
                cma_report = state.get("cma_report")
                if cma_report:
                    market_data.update({
                        "estimated_value": f"${cma_report.get('estimated_value', 0):,.0f}",
                        "median_price": f"${cma_report.get('estimated_value', 0):,.0f}",
                        "suggested_price": f"${cma_report.get('estimated_value', 0):,.0f}",
                    })

                market_context = state.get("market_data", {})
                if market_context:
                    market_data.update({
                        "avg_days_on_market": str(market_context.get("dom_average", 30)),
                        "market_trend": market_context.get("price_trend", "stable"),
                        "inventory_level": str(market_context.get("inventory_level", 1450)),
                    })

                # Generate objection response
                response = engine.generate_response(
                    detection,
                    contact_id=state["lead_id"],
                    market_data=market_data,
                    variant_index=variant_index,
                )

                if response:
                    objection_response_text = response.response_text
                    objection_metadata.update({
                        "graduation_level": response.graduation_level.value,
                        "response_variant": variant_index,
                        "next_graduation": response.next_graduation.value if response.next_graduation else None,
                    })

                    logger.info(
                        f"Objection response generated: {response.objection_category.value} "
                        f"at {response.graduation_level.value} level (variant {variant_index})"
                    )

                    # Fire-and-forget: Save objection event to database
                    try:
                        dsn = os.getenv("DATABASE_URL")
                        if REPO_AVAILABLE and dsn and JorgeMetricsRepository:
                            repo = JorgeMetricsRepository(dsn)
                            await repo.save_objection_event(
                                contact_id=state["lead_id"],
                                objection_type=detection.objection_type.value,
                                objection_category=response.objection_category.value,
                                confidence=detection.confidence,
                                matched_text=detection.matched_text,
                                graduation_level=response.graduation_level.value,
                                response_variant=variant_index,
                                response_text=objection_response_text,
                                market_data=market_data,
                            )
                    except Exception as db_exc:
                        logger.warning(f"Failed to save objection event (non-blocking): {db_exc}")

                    # Emit objection handling event for monitoring
                    await self.event_publisher.publish_conversation_update(
                        conversation_id=f"jorge_{state['lead_id']}",
                        lead_id=state["lead_id"],
                        stage="objection_handled",
                        message=f"Objection handled: {response.objection_category.value} "
                                f"({response.graduation_level.value} level, variant {variant_index})",
                    )

        except Exception as e:
            logger.warning(f"Objection handling failed for {state['lead_id']} (non-blocking): {e}")
            # Graceful fallback: don't block workflow on objection handling failures

        return {
            "objection_detected": objection_detected,
            "objection_response_text": objection_response_text,
            "objection_metadata": objection_metadata,
        }
