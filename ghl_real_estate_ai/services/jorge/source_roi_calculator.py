"""
Lead Source ROI Calculator

Calculates ROI metrics for lead sources including conversion rates, deal values,
cost per qualified lead, and ROI. Generates optimization recommendations based
on performance data.

Usage:
    calculator = SourceROICalculator()
    roi_data = await calculator.calculate_source_roi(source_name="Facebook Ads", cost=5000)
    recommendations = await calculator.get_optimization_recommendations()
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.jorge.source_tracker import SourceTracker, get_source_tracker

logger = get_logger(__name__)


class SourceROICalculator:
    """Calculates ROI and performance metrics for lead sources.

    Analyzes source performance, calculates cost efficiency, and generates
    actionable optimization recommendations for budget allocation.
    """

    def __init__(
        self,
        source_tracker: Optional[SourceTracker] = None,
        db_service: Optional[Any] = None,
    ):
        """Initialize ROI calculator.

        Args:
            source_tracker: Source tracker instance (creates one if None)
            db_service: Optional database service for cost data persistence
        """
        self._source_tracker = source_tracker or get_source_tracker(db_service)
        self._db_service = db_service
        self._initialized = True
        logger.info("SourceROICalculator initialized")

    async def calculate_source_roi(
        self,
        source_name: str,
        cost: Optional[float] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Calculate ROI metrics for a specific source.

        Args:
            source_name: Lead source name
            cost: Marketing cost for this source (optional, can be from DB)
            days: Time window in days

        Returns:
            Dict containing:
                - source_name: Source name
                - cost: Total marketing cost
                - revenue: Total revenue generated
                - roi: Return on investment (%)
                - roi_ratio: Revenue / cost ratio
                - cost_per_lead: Cost / total contacts
                - cost_per_qualified_lead: Cost / qualified leads
                - cost_per_close: Cost / closed deals
                - conversion_rate: Overall conversion rate (%)
                - avg_deal_value: Average deal value
                - profit: Revenue - cost
        """
        # Get source metrics
        metrics = await self._source_tracker.get_source_metrics(
            source_name=source_name,
            days=days,
        )

        if not metrics:
            logger.warning(f"No metrics found for source: {source_name}")
            return self._empty_roi_data(source_name)

        # Get cost data (from param or DB)
        if cost is None:
            cost = await self._get_source_cost(source_name, days)

        total_contacts = metrics.get("total_contacts", 0)
        qualified_leads = metrics.get("qualified_leads", 0)
        closed_deals = metrics.get("closed_deals", 0)
        revenue = metrics.get("total_revenue", 0.0)
        avg_deal_value = metrics.get("avg_deal_value", 0.0)
        conversion_rate = metrics.get("conversion_rate", 0.0)

        # Calculate ROI metrics
        roi = 0.0
        roi_ratio = 0.0
        profit = revenue - cost

        if cost > 0:
            roi = ((revenue - cost) / cost) * 100
            roi_ratio = revenue / cost

        cost_per_lead = cost / total_contacts if total_contacts > 0 else 0.0
        cost_per_qualified_lead = cost / qualified_leads if qualified_leads > 0 else 0.0
        cost_per_close = cost / closed_deals if closed_deals > 0 else 0.0

        return {
            "source_name": source_name,
            "cost": round(cost, 2),
            "revenue": round(revenue, 2),
            "roi": round(roi, 2),
            "roi_ratio": round(roi_ratio, 2),
            "cost_per_lead": round(cost_per_lead, 2),
            "cost_per_qualified_lead": round(cost_per_qualified_lead, 2),
            "cost_per_close": round(cost_per_close, 2),
            "conversion_rate": conversion_rate,
            "avg_deal_value": round(avg_deal_value, 2),
            "profit": round(profit, 2),
            "total_contacts": total_contacts,
            "qualified_leads": qualified_leads,
            "closed_deals": closed_deals,
        }

    async def get_all_source_roi(
        self,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Calculate ROI for all sources.

        Args:
            days: Time window in days

        Returns:
            List of ROI data for each source
        """
        # Get all source metrics
        all_metrics = await self._source_tracker.get_source_metrics(days=days)

        if not all_metrics or "sources" not in all_metrics:
            logger.warning("No source metrics available")
            return []

        results = []
        for source_data in all_metrics["sources"]:
            source_name = source_data["source_name"]
            cost = await self._get_source_cost(source_name, days)

            roi_data = await self.calculate_source_roi(
                source_name=source_name,
                cost=cost,
                days=days,
            )
            results.append(roi_data)

        return results

    async def get_optimization_recommendations(
        self,
        days: int = 30,
        budget_shift_percent: float = 20.0,
    ) -> Dict[str, Any]:
        """Generate budget optimization recommendations.

        Args:
            days: Time window for analysis
            budget_shift_percent: Percentage of budget to recommend shifting

        Returns:
            Dict containing:
                - top_performers: Sources to increase budget
                - underperformers: Sources to decrease budget
                - recommendations: List of actionable recommendations
                - projected_impact: Estimated revenue impact
        """
        all_roi = await self.get_all_source_roi(days=days)

        if not all_roi:
            return {
                "top_performers": [],
                "underperformers": [],
                "recommendations": ["Insufficient data for recommendations"],
                "projected_impact": 0.0,
            }

        # Sort by ROI
        sorted_by_roi = sorted(all_roi, key=lambda x: x["roi"], reverse=True)

        # Identify top and bottom performers
        num_sources = len(sorted_by_roi)
        top_cutoff = max(1, num_sources // 3)  # Top 33%
        bottom_cutoff = max(1, num_sources // 3)  # Bottom 33%

        top_performers = sorted_by_roi[:top_cutoff]
        underperformers = sorted_by_roi[-bottom_cutoff:]

        # Generate recommendations
        recommendations = []
        total_budget = sum(s["cost"] for s in all_roi)
        shift_amount = total_budget * (budget_shift_percent / 100)

        # Recommendation 1: Shift budget from underperformers to top performers
        if underperformers and top_performers:
            worst_source = underperformers[-1]
            best_source = top_performers[0]

            recommendations.append(
                f"Shift ${shift_amount:,.0f} ({budget_shift_percent}%) from "
                f"{worst_source['source_name']} (ROI: {worst_source['roi']:.1f}%) "
                f"to {best_source['source_name']} (ROI: {best_source['roi']:.1f}%)"
            )

        # Recommendation 2: Focus on high-conversion sources
        high_conversion = [s for s in all_roi if s["conversion_rate"] > 10.0]
        if high_conversion:
            best_conv = max(high_conversion, key=lambda x: x["conversion_rate"])
            recommendations.append(
                f"Increase investment in {best_conv['source_name']} "
                f"(conversion rate: {best_conv['conversion_rate']:.1f}%)"
            )

        # Recommendation 3: Eliminate or reduce negative ROI sources
        negative_roi = [s for s in all_roi if s["roi"] < 0]
        if negative_roi:
            for source in negative_roi:
                recommendations.append(
                    f"Consider pausing {source['source_name']} "
                    f"(ROI: {source['roi']:.1f}%, losing ${abs(source['profit']):,.0f})"
                )

        # Recommendation 4: Optimize cost per qualified lead
        if all_roi:
            avg_cpl = sum(s["cost_per_qualified_lead"] for s in all_roi) / len(all_roi)
            low_cost_sources = [s for s in all_roi if s["cost_per_qualified_lead"] < avg_cpl and s["cost_per_qualified_lead"] > 0]

            if low_cost_sources:
                best_cost = min(low_cost_sources, key=lambda x: x["cost_per_qualified_lead"])
                recommendations.append(
                    f"Scale {best_cost['source_name']} - lowest cost per qualified lead "
                    f"(${best_cost['cost_per_qualified_lead']:.0f} vs ${avg_cpl:.0f} average)"
                )

        # Calculate projected impact
        projected_impact = 0.0
        if top_performers and underperformers:
            best_roi_ratio = top_performers[0]["roi_ratio"]
            projected_impact = shift_amount * best_roi_ratio - shift_amount

        return {
            "top_performers": top_performers,
            "underperformers": underperformers,
            "recommendations": recommendations,
            "projected_impact": round(projected_impact, 2),
            "total_budget": round(total_budget, 2),
            "recommended_shift": round(shift_amount, 2),
        }

    async def compare_sources(
        self,
        source_a: str,
        source_b: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Compare two sources side-by-side.

        Args:
            source_a: First source name
            source_b: Second source name
            days: Time window in days

        Returns:
            Comparison data with winner determination
        """
        roi_a = await self.calculate_source_roi(source_a, days=days)
        roi_b = await self.calculate_source_roi(source_b, days=days)

        # Determine winner across metrics
        winners = {
            "roi": source_a if roi_a["roi"] > roi_b["roi"] else source_b,
            "conversion_rate": source_a if roi_a["conversion_rate"] > roi_b["conversion_rate"] else source_b,
            "cost_per_qualified_lead": source_a if roi_a["cost_per_qualified_lead"] < roi_b["cost_per_qualified_lead"] else source_b,
            "avg_deal_value": source_a if roi_a["avg_deal_value"] > roi_b["avg_deal_value"] else source_b,
        }

        return {
            "source_a": roi_a,
            "source_b": roi_b,
            "winners": winners,
            "recommendation": self._generate_comparison_recommendation(roi_a, roi_b),
        }

    def _generate_comparison_recommendation(
        self,
        roi_a: Dict[str, Any],
        roi_b: Dict[str, Any],
    ) -> str:
        """Generate recommendation from source comparison.

        Args:
            roi_a: ROI data for source A
            roi_b: ROI data for source B

        Returns:
            Recommendation string
        """
        source_a = roi_a["source_name"]
        source_b = roi_b["source_name"]

        # Compare overall performance
        score_a = (
            (roi_a["roi"] / 100 if roi_a["roi"] > 0 else -1) +
            (roi_a["conversion_rate"] / 10) -
            (roi_a["cost_per_qualified_lead"] / 1000)
        )

        score_b = (
            (roi_b["roi"] / 100 if roi_b["roi"] > 0 else -1) +
            (roi_b["conversion_rate"] / 10) -
            (roi_b["cost_per_qualified_lead"] / 1000)
        )

        winner = source_a if score_a > score_b else source_b
        loser = source_b if score_a > score_b else source_a

        return f"Prioritize {winner} over {loser} for better ROI and efficiency"

    async def _get_source_cost(self, source_name: str, days: int) -> float:
        """Get marketing cost for a source from database.

        Args:
            source_name: Source name
            days: Time window in days

        Returns:
            Total cost (defaults to 0 if not available)
        """
        if not self._db_service:
            return 0.0

        try:
            since_date = datetime.now() - timedelta(days=days)

            result = await self._db_service.fetchrow(
                """
                SELECT SUM(cost) as total_cost
                FROM lead_source_costs
                WHERE source_name = $1 AND date >= $2
                """,
                source_name,
                since_date,
            )

            return float(result["total_cost"]) if result and result["total_cost"] else 0.0

        except Exception as e:
            logger.warning(f"Could not fetch cost for {source_name}: {e}")
            return 0.0

    def _empty_roi_data(self, source_name: str) -> Dict[str, Any]:
        """Return empty ROI data structure.

        Args:
            source_name: Source name

        Returns:
            Empty ROI data dict
        """
        return {
            "source_name": source_name,
            "cost": 0.0,
            "revenue": 0.0,
            "roi": 0.0,
            "roi_ratio": 0.0,
            "cost_per_lead": 0.0,
            "cost_per_qualified_lead": 0.0,
            "cost_per_close": 0.0,
            "conversion_rate": 0.0,
            "avg_deal_value": 0.0,
            "profit": 0.0,
            "total_contacts": 0,
            "qualified_leads": 0,
            "closed_deals": 0,
        }


# Singleton instance
_instance: Optional[SourceROICalculator] = None


def get_roi_calculator(
    source_tracker: Optional[SourceTracker] = None,
    db_service: Optional[Any] = None,
) -> SourceROICalculator:
    """Get or create singleton SourceROICalculator instance.

    Args:
        source_tracker: Optional source tracker instance
        db_service: Optional database service

    Returns:
        SourceROICalculator instance
    """
    global _instance
    if _instance is None:
        _instance = SourceROICalculator(
            source_tracker=source_tracker,
            db_service=db_service,
        )
    return _instance
