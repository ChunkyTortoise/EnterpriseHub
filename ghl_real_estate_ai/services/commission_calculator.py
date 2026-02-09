"""
Commission Calculator Service - Agent 3: Revenue Maximizer
Real-time commission tracking and revenue projection system.

Revenue Impact: Shows Jorge exactly how much $ each automation generates
Features:
- Commission calculation by deal stage
- ROI tracking for each automation feature
- Revenue projections and forecasting
- Deal pipeline value visualization
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class DealStage(Enum):
    """Deal pipeline stages."""

    LEAD = "lead"
    QUALIFIED = "qualified"
    SHOWING = "showing"
    OFFER = "offer"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"
    LOST = "lost"


class CommissionType(Enum):
    """Commission structure types."""

    BUYER_AGENT = "buyer_agent"  # Representing buyer
    SELLER_AGENT = "seller_agent"  # Representing seller
    DUAL_AGENCY = "dual_agency"  # Representing both


class CommissionCalculator:
    """
    Comprehensive commission calculator and revenue tracker for real estate agents.
    Tracks deal value, calculates commissions, and shows automation ROI.
    """

    # Default commission rates (customizable)
    DEFAULT_RATES = {
        CommissionType.BUYER_AGENT: 0.025,  # 2.5%
        CommissionType.SELLER_AGENT: 0.025,  # 2.5%
        CommissionType.DUAL_AGENCY: 0.05,  # 5%
    }

    # Deal stage conversion rates (industry averages)
    CONVERSION_RATES = {
        DealStage.LEAD: 0.05,  # 5% of leads become qualified
        DealStage.QUALIFIED: 0.30,  # 30% of qualified leads go to showings
        DealStage.SHOWING: 0.40,  # 40% of showings result in offers
        DealStage.OFFER: 0.60,  # 60% of offers get under contract
        DealStage.UNDER_CONTRACT: 0.90,  # 90% of contracts close
        DealStage.CLOSED: 1.0,  # 100% - deal is done
    }

    # Automation impact multipliers (how much each feature improves conversion)
    AUTOMATION_MULTIPLIERS = {
        "deal_closer_ai": 1.15,  # 15% improvement in closing rate
        "hot_lead_fastlane": 1.20,  # 20% improvement in lead conversion
        "ai_listing_writer": 1.10,  # 10% more showings from better listings
        "auto_followup": 1.25,  # 25% more leads stay engaged
        "voice_receptionist": 1.30,  # 30% more leads captured
        "market_insights": 1.08,  # 8% better pricing decisions
        "workflow_automation": 1.12,  # 12% time savings = more deals
    }

    def __init__(self, brokerage_split: float = 0.80):
        """
        Initialize Commission Calculator.

        Args:
            brokerage_split: Agent's share of commission (0.80 = 80/20 split)
        """
        self.brokerage_split = brokerage_split
        self.deals = []

    def calculate_commission(
        self,
        property_price: float,
        commission_type: CommissionType,
        custom_rate: Optional[float] = None,
        transaction_costs: float = 0,
    ) -> Dict:
        """
        Calculate commission for a single deal.

        Args:
            property_price: Sale price of property
            commission_type: Type of commission (buyer/seller/dual)
            custom_rate: Optional custom commission rate (overrides defaults)
            transaction_costs: Additional costs to deduct

        Returns:
            Dictionary with commission breakdown
        """
        # Determine commission rate
        rate = custom_rate if custom_rate else self.DEFAULT_RATES[commission_type]

        # Calculate gross commission
        gross_commission = property_price * rate

        # Calculate agent's share after brokerage split
        agent_share = gross_commission * self.brokerage_split

        # Calculate net after transaction costs
        net_commission = agent_share - transaction_costs

        # Calculate brokerage portion
        brokerage_portion = gross_commission - agent_share

        return {
            "property_price": property_price,
            "commission_rate": rate,
            "commission_type": commission_type.value,
            "gross_commission": round(gross_commission, 2),
            "brokerage_split_pct": self.brokerage_split * 100,
            "brokerage_portion": round(brokerage_portion, 2),
            "agent_share_gross": round(agent_share, 2),
            "transaction_costs": round(transaction_costs, 2),
            "net_commission": round(net_commission, 2),
            "effective_rate": round((net_commission / property_price) * 100, 3),
        }

    def track_deal(
        self,
        deal_id: str,
        client_name: str,
        property_price: float,
        commission_type: CommissionType,
        current_stage: DealStage,
        created_date: Optional[datetime] = None,
        custom_rate: Optional[float] = None,
        automation_features: Optional[List[str]] = None,
    ) -> Dict:
        """
        Track a deal through the pipeline.

        Args:
            deal_id: Unique deal identifier
            client_name: Client name
            property_price: Property value
            commission_type: Commission structure
            current_stage: Current pipeline stage
            created_date: When deal was created
            custom_rate: Custom commission rate
            automation_features: List of automation features used

        Returns:
            Deal tracking data with projections
        """
        if created_date is None:
            created_date = datetime.now()

        # Calculate base commission
        commission_data = self.calculate_commission(property_price, commission_type, custom_rate)

        # Calculate probability of closing based on stage
        close_probability = self._calculate_close_probability(current_stage, automation_features or [])

        # Project expected value
        expected_value = commission_data["net_commission"] * close_probability

        # Calculate days in pipeline
        days_in_pipeline = (datetime.now() - created_date).days

        deal = {
            "deal_id": deal_id,
            "client_name": client_name,
            "property_price": property_price,
            "commission_type": commission_type.value,
            "current_stage": current_stage.value,
            "created_date": created_date.isoformat(),
            "days_in_pipeline": days_in_pipeline,
            "commission_data": commission_data,
            "close_probability": round(close_probability * 100, 1),
            "expected_value": round(expected_value, 2),
            "automation_features": automation_features or [],
            "automation_impact": self._calculate_automation_impact(automation_features or []),
            "updated_at": datetime.now().isoformat(),
        }

        # Add or update deal in tracker
        existing_idx = next((i for i, d in enumerate(self.deals) if d["deal_id"] == deal_id), None)
        if existing_idx is not None:
            self.deals[existing_idx] = deal
        else:
            self.deals.append(deal)

        return deal

    def _calculate_close_probability(self, stage: DealStage, automation_features: List[str]) -> float:
        """Calculate probability of deal closing based on stage and automations."""
        base_probability = self.CONVERSION_RATES[stage]

        # Apply automation multipliers
        automation_boost = 1.0
        for feature in automation_features:
            multiplier = self.AUTOMATION_MULTIPLIERS.get(feature, 1.0)
            automation_boost *= multiplier

        # Cap at 95% (never 100% certain)
        return min(base_probability * automation_boost, 0.95)

    def _calculate_automation_impact(self, features: List[str]) -> Dict:
        """Calculate dollar impact of automation features."""
        if not features:
            return {"features_used": 0, "estimated_impact": 0, "roi_multiplier": 1.0}

        # Calculate compound multiplier
        compound_multiplier = 1.0
        for feature in features:
            compound_multiplier *= self.AUTOMATION_MULTIPLIERS.get(feature, 1.0)

        return {
            "features_used": len(features),
            "feature_list": features,
            "roi_multiplier": round(compound_multiplier, 2),
            "improvement_pct": round((compound_multiplier - 1.0) * 100, 1),
        }

    def get_pipeline_summary(self, active_only: bool = True) -> Dict:
        """
        Get summary of entire deal pipeline.

        Args:
            active_only: Only include active deals (exclude closed/lost)

        Returns:
            Pipeline summary with totals and projections
        """
        if active_only:
            deals = [d for d in self.deals if d["current_stage"] not in ["closed", "lost"]]
        else:
            deals = self.deals

        if not deals:
            return {
                "total_deals": 0,
                "total_value": 0,
                "expected_commission": 0,
                "by_stage": {},
                "automation_roi": {},
            }

        # Group by stage
        by_stage = {}
        for stage in DealStage:
            stage_deals = [d for d in deals if d["current_stage"] == stage.value]
            if stage_deals:
                by_stage[stage.value] = {
                    "count": len(stage_deals),
                    "total_property_value": sum(d["property_price"] for d in stage_deals),
                    "expected_commission": sum(d["expected_value"] for d in stage_deals),
                    "close_probability_avg": sum(d["close_probability"] for d in stage_deals) / len(stage_deals),
                }

        # Calculate totals
        total_property_value = sum(d["property_price"] for d in deals)
        total_expected = sum(d["expected_value"] for d in deals)
        total_potential = sum(d["commission_data"]["net_commission"] for d in deals)

        # Calculate automation impact
        automation_roi = self._calculate_pipeline_automation_roi(deals)

        return {
            "total_deals": len(deals),
            "total_property_value": round(total_property_value, 2),
            "total_potential_commission": round(total_potential, 2),
            "total_expected_commission": round(total_expected, 2),
            "weighted_close_rate": round(
                (total_expected / total_potential * 100) if total_potential > 0 else 0,
                1,
            ),
            "by_stage": by_stage,
            "automation_roi": automation_roi,
            "generated_at": datetime.now().isoformat(),
        }

    def _calculate_pipeline_automation_roi(self, deals: List[Dict]) -> Dict:
        """Calculate ROI impact of automations across pipeline."""
        deals_with_automation = [d for d in deals if d["automation_features"]]

        if not deals_with_automation:
            return {
                "deals_using_automation": 0,
                "estimated_revenue_increase": 0,
                "roi_note": "No automation features tracked yet",
            }

        # Calculate expected value with vs without automation
        total_with_automation = sum(d["expected_value"] for d in deals_with_automation)

        # Estimate what it would be without automation (remove multiplier impact)
        total_without = 0
        for deal in deals_with_automation:
            base_probability = self.CONVERSION_RATES[DealStage(deal["current_stage"])]
            base_expected = deal["commission_data"]["net_commission"] * base_probability
            total_without += base_expected

        revenue_increase = total_with_automation - total_without

        # Most common features
        all_features = []
        for deal in deals_with_automation:
            all_features.extend(deal["automation_features"])

        feature_counts = {}
        for feature in all_features:
            feature_counts[feature] = feature_counts.get(feature, 0) + 1

        top_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "deals_using_automation": len(deals_with_automation),
            "estimated_revenue_increase": round(revenue_increase, 2),
            "improvement_pct": round((revenue_increase / total_without * 100) if total_without > 0 else 0, 1),
            "top_features": [{"feature": f, "count": c} for f, c in top_features],
            "roi_note": f"Automation features increasing pipeline value by ${revenue_increase:,.0f}",
        }

    def get_monthly_projections(self, months: int = 12) -> Dict:
        """
        Project monthly commission income.

        Args:
            months: Number of months to project

        Returns:
            Monthly projection data
        """
        active_deals = [d for d in self.deals if d["current_stage"] not in ["closed", "lost"]]

        # Calculate average deal velocity (days to close)
        closed_deals = [d for d in self.deals if d["current_stage"] == "closed"]
        avg_days_to_close = 90  # Default

        if closed_deals:
            avg_days_to_close = sum(d["days_in_pipeline"] for d in closed_deals) / len(closed_deals)

        # Project closings by month
        monthly_projections = []

        for month in range(1, months + 1):
            month_start = datetime.now() + timedelta(days=30 * (month - 1))
            month_end = month_start + timedelta(days=30)

            # Simple projection: distribute expected value across avg close time
            expected_monthly = sum(d["expected_value"] for d in active_deals) / (avg_days_to_close / 30)

            monthly_projections.append(
                {
                    "month": month,
                    "month_name": month_start.strftime("%B %Y"),
                    "projected_commission": round(expected_monthly, 2),
                    "deals_expected": round(len(active_deals) * 0.1, 1),  # Rough estimate
                }
            )

        total_12_month = sum(m["projected_commission"] for m in monthly_projections)

        return {
            "projections": monthly_projections,
            "total_12_month": round(total_12_month, 2),
            "avg_monthly": round(total_12_month / 12, 2),
            "avg_days_to_close": round(avg_days_to_close, 1),
            "assumptions": "Based on current pipeline and historical close rates",
        }

    def get_automation_roi_report(self) -> Dict:
        """
        Generate detailed ROI report for automation features.

        Returns:
            ROI analysis showing value of each automation
        """
        # GHL AI system cost (Jorge's investment)
        system_cost_monthly = 300  # Current price point
        system_cost_annual = system_cost_monthly * 12

        pipeline_summary = self.get_pipeline_summary()
        automation_impact = pipeline_summary["automation_roi"]

        revenue_increase = automation_impact.get("estimated_revenue_increase", 0)

        # Calculate ROI
        if revenue_increase > 0:
            roi_multiplier = revenue_increase / system_cost_annual
            roi_percentage = (revenue_increase - system_cost_annual) / system_cost_annual * 100
        else:
            roi_multiplier = 0
            roi_percentage = 0

        # Break down by feature
        feature_breakdown = []
        if "top_features" in automation_impact:
            for feature_data in automation_impact["top_features"]:
                feature = feature_data["feature"]
                multiplier = self.AUTOMATION_MULTIPLIERS.get(feature, 1.0)

                feature_breakdown.append(
                    {
                        "feature": feature,
                        "improvement_pct": round((multiplier - 1.0) * 100, 1),
                        "deals_using": feature_data["count"],
                        "estimated_value": round(
                            revenue_increase * (feature_data["count"] / automation_impact["deals_using_automation"]),
                            2,
                        ),
                    }
                )

        return {
            "system_cost_annual": system_cost_annual,
            "system_cost_monthly": system_cost_monthly,
            "revenue_increase_annual": round(revenue_increase, 2),
            "net_benefit": round(revenue_increase - system_cost_annual, 2),
            "roi_multiplier": round(roi_multiplier, 1),
            "roi_percentage": round(roi_percentage, 1),
            "payback_period_days": round(
                ((system_cost_annual / revenue_increase * 365) if revenue_increase > 0 else 999),
                0,
            ),
            "feature_breakdown": feature_breakdown,
            "deals_tracked": len(self.deals),
            "deals_with_automation": automation_impact.get("deals_using_automation", 0),
            "summary": f"${revenue_increase:,.0f} annual increase from ${system_cost_annual:,.0f} investment = {roi_percentage:.0f}% ROI",
            "generated_at": datetime.now().isoformat(),
        }


# Convenience functions
def quick_commission(property_price: float, commission_rate: float = 0.025, split: float = 0.80) -> float:
    """
    Quick commission calculation.

    Args:
        property_price: Property sale price
        commission_rate: Commission rate (default 2.5%)
        split: Brokerage split (default 80%)

    Returns:
        Net commission to agent
    """
    calc = CommissionCalculator(brokerage_split=split)
    result = calc.calculate_commission(property_price, CommissionType.BUYER_AGENT, custom_rate=commission_rate)
    return result["net_commission"]


if __name__ == "__main__":
    # Demo usage
    calc = CommissionCalculator(brokerage_split=0.80)

    print("💰 Commission Calculator - Demo\n")

    # Demo deal 1: Hot lead with automation
    deal1 = calc.track_deal(
        deal_id="D001",
        client_name="Sarah Johnson",
        property_price=850000,
        commission_type=CommissionType.BUYER_AGENT,
        current_stage=DealStage.OFFER,
        automation_features=["deal_closer_ai", "hot_lead_fastlane", "auto_followup"],
    )

    print(f"Deal: {deal1['client_name']}")
    print(f"Property: ${deal1['property_price']:,}")
    print(f"Stage: {deal1['current_stage']}")
    print(f"Expected Commission: ${deal1['expected_value']:,}")
    print(f"Close Probability: {deal1['close_probability']}%")
    print(f"Automation Impact: +{deal1['automation_impact']['improvement_pct']}%")
    print()

    # Pipeline summary
    summary = calc.get_pipeline_summary()
    print(f"Pipeline Summary:")
    print(f"Total Deals: {summary['total_deals']}")
    print(f"Expected Commission: ${summary['total_expected_commission']:,}")
    print()

    # ROI Report
    roi = calc.get_automation_roi_report()
    print(f"Automation ROI:")
    print(f"Annual Investment: ${roi['system_cost_annual']:,}")
    print(f"Revenue Increase: ${roi['revenue_increase_annual']:,}")
    print(f"ROI: {roi['roi_percentage']:.0f}%")
