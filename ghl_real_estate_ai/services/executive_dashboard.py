"""
Executive Dashboard Engine - Enterprise Intelligence
Aggregates multi-tenant performance metrics for Agency Owners and Tenant Admins.

Features:
- Revenue in Pipeline visualization
- Agent Swarm performance tracking
- Multi-tenant data aggregation
- ROI and Yield analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.enterprise_tenant_service import get_enterprise_tenant_service

logger = get_logger(__name__)


class ExecutiveDashboardService:
    """
    Central engine for aggregating and visualizing enterprise-level metrics.
    """

    def __init__(self):
        self.tenant_service = None  # Lazy load

    async def get_agency_overview(self) -> Dict[str, Any]:
        """
        Aggregates metrics across ALL tenants for the Agency Owner (Jorge).
        """
        if not self.tenant_service:
            self.tenant_service = await get_enterprise_tenant_service()

        # 1. Fetch all active tenants
        # In a real system, this queries the database
        tenants = ["tenant_1", "tenant_2", "default_tenant"]

        total_revenue_pipeline = 0.0
        total_leads_processed = 0
        total_conversions = 0
        tenant_breakdown = []

        for tid in tenants:
            stats = await self.get_tenant_summary(tid)
            total_revenue_pipeline += stats["revenue_pipeline"]
            total_leads_processed += stats["leads_processed"]
            total_conversions += stats["conversions"]
            tenant_breakdown.append(
                {
                    "tenant_id": tid,
                    "revenue": stats["revenue_pipeline"],
                    "health": "Healthy" if stats["leads_processed"] > 0 else "Idle",
                }
            )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_revenue_pipeline": round(total_revenue_pipeline, 2),
            "total_leads_processed": total_leads_processed,
            "total_conversions": total_conversions,
            "tenant_count": len(tenants),
            "tenant_breakdown": tenant_breakdown,
        }

    async def get_tenant_summary(self, tenant_id: str) -> Dict[str, Any]:
        """
        Provides a high-level summary for a specific Tenant Admin.
        """
        # Simulated data aggregation from PredictiveLeadScorer and Memory
        return {
            "tenant_id": tenant_id,
            "revenue_pipeline": 450000.00,  # Sum of (LeadValue * ClosingProb)
            "leads_processed": 125,
            "conversions": 12,
            "avg_yield": 0.18,
            "swarm_confidence": 0.88,
            "stalled_leads_count": 15,
        }

    async def get_swarm_performance_report(self, tenant_id: str) -> Dict[str, Any]:
        """
        Detailed breakdown of agent performance for a specific tenant.
        """
        from ghl_real_estate_ai.agents.lead_intelligence_swarm import lead_intelligence_swarm

        status = await lead_intelligence_swarm.get_swarm_status(tenant_id)

        return {
            "tenant_id": tenant_id,
            "agent_stats": status["agent_status"],
            "swarm_agreement_rate": status["swarm_metrics"]["agent_agreement_rate"],
            "avg_processing_time": status["swarm_metrics"]["average_processing_time"],
        }
