"""
Supply Chain Event Coordinator

This module handles integration with the central EventBus for the Supply Chain Engine.
Part of the Supply Chain Intelligence Engine.
"""

import logging
from typing import Dict, Any

from ..core.event_bus import EventBus, EventType, EventPriority

logger = logging.getLogger(__name__)

class SupplyChainEventCoordinator:
    """
    Coordinates supply chain events with the central event bus.
    """

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def publish_disruption_prediction(self, vulnerability: Any):
        """
        Publish a predicted supply chain disruption event.
        """
        await self.event_bus.publish(
            event_type=EventType.SUPPLY_CHAIN_DISRUPTION_PREDICTED,
            data={
                "supplier_id": vulnerability.supplier_id,
                "severity": vulnerability.severity.value,
                "probability": vulnerability.probability,
                "financial_exposure": float(vulnerability.financial_exposure),
                "predicted_date": vulnerability.predicted_impact_date.isoformat()
            },
            source_system="supply_chain_engine",
            priority=EventPriority.CRITICAL if vulnerability.severity.name == "CRITICAL" else EventPriority.HIGH
        )
        logger.info(f"Published disruption prediction for {vulnerability.supplier_id}")

    async def publish_procurement_opportunity(self, opportunity: Any):
        """
        Publish an identified procurement savings opportunity.
        """
        await self.event_bus.publish(
            event_type=EventType.PROCUREMENT_OPPORTUNITY_IDENTIFIED,
            data={
                "opportunity_id": opportunity.opportunity_id,
                "category": opportunity.item_category,
                "potential_savings": float(opportunity.potential_savings),
                "strategy": opportunity.strategy
            },
            source_system="supply_chain_engine",
            priority=EventPriority.MEDIUM
        )

    async def publish_response_plan(self, plan_id: str, actions: Dict[str, Any]):
        """
        Publish a coordinated response plan.
        """
        await self.event_bus.publish(
            event_type=EventType.SUPPLY_CHAIN_RESPONSE_COORDINATED,
            data={
                "plan_id": plan_id,
                "actions": actions,
                "timestamp": str(actions.get("created_at"))
            },
            source_system="supply_chain_engine",
            priority=EventPriority.HIGH
        )
