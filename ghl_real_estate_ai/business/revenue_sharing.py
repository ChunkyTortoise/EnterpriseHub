"""
Jorge's Global Revenue Sharing System - Partnership Financial Management
Automated commission tracking and revenue distribution for global partnerships

This module provides:
- Multi-tier commission calculation for different partner types
- Automated revenue sharing based on performance and volume
- Currency conversion for international partnerships
- Tax and regulatory compliance for cross-border payments
- Real-time financial analytics and reporting
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PartnerType(Enum):
    FRANCHISE = "franchise"
    MLS_PROVIDER = "mls_provider"
    TECHNOLOGY = "technology"
    CRM_PROVIDER = "crm_provider"
    FINANCIAL_SERVICES = "financial_services"
    REGIONAL_DISTRIBUTOR = "regional_distributor"


class RevenueType(Enum):
    SUBSCRIPTION = "subscription"  # Monthly/annual subscription fees
    TRANSACTION = "transaction"  # Per-transaction fees
    COMMISSION = "commission"  # Commission sharing from deals
    LICENSING = "licensing"  # White-label licensing fees
    PERFORMANCE_BONUS = "performance_bonus"  # Performance-based bonuses
    TRAINING = "training"  # Training and certification fees


class PaymentFrequency(Enum):
    REAL_TIME = "real_time"  # Instant payment on transaction
    DAILY = "daily"  # Daily aggregated payments
    WEEKLY = "weekly"  # Weekly payments
    MONTHLY = "monthly"  # Monthly payments
    QUARTERLY = "quarterly"  # Quarterly payments


@dataclass
class CommissionTier:
    """Commission tier based on volume or performance"""

    tier_name: str
    min_threshold: float  # Minimum value to reach this tier
    jorge_percentage: float  # Jorge's share (0.0 to 1.0)
    partner_percentage: float  # Partner's share (0.0 to 1.0)
    performance_bonus: float = 0.0  # Additional bonus for high performance


@dataclass
class RevenueStructure:
    """Complete revenue sharing structure for a partner"""

    partner_id: str
    partner_type: PartnerType
    base_commission_tiers: List[CommissionTier]
    transaction_fees: Dict[str, float] = field(default_factory=dict)
    monthly_minimums: Dict[str, float] = field(default_factory=dict)
    performance_bonuses: Dict[str, float] = field(default_factory=dict)
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    currency: str = "USD"
    tax_rate: float = 0.0  # Applicable tax rate
    effective_date: datetime = field(default_factory=datetime.now)
    expiry_date: Optional[datetime] = None


@dataclass
class RevenueTransaction:
    """Individual revenue transaction record"""

    transaction_id: str
    partner_id: str
    revenue_type: RevenueType
    gross_amount: float  # Original transaction amount
    jorge_amount: float  # Jorge's share
    partner_amount: float  # Partner's share
    currency: str
    exchange_rate: float = 1.0
    usd_equivalent: float = 0.0
    commission_tier: str = "base"
    transaction_date: datetime = field(default_factory=datetime.now)
    deal_id: Optional[str] = None
    agent_id: Optional[str] = None
    property_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PartnerFinancials:
    """Financial summary for a partner"""

    partner_id: str
    period_start: datetime
    period_end: datetime
    gross_revenue: float
    jorge_revenue: float
    partner_revenue: float
    transaction_count: int
    avg_transaction_value: float
    commission_tier_distribution: Dict[str, int]
    currency: str
    tax_amount: float = 0.0
    net_payout: float = 0.0


class GlobalRevenueManager:
    """
    Jorge's Global Revenue Sharing Manager
    Handles automated commission calculation and distribution for global partnerships
    """

    def __init__(self):
        self.revenue_structures: Dict[str, RevenueStructure] = {}
        self.transactions: List[RevenueTransaction] = []
        self.partner_financials: Dict[str, List[PartnerFinancials]] = {}
        self.exchange_rates: Dict[str, float] = {}
        self._initialize_default_structures()

    def _initialize_default_structures(self):
        """Initialize default revenue structures for different partner types"""

        # Franchise Partner Structure (High volume, lower per-transaction)
        franchise_structure = RevenueStructure(
            partner_id="default_franchise",
            partner_type=PartnerType.FRANCHISE,
            base_commission_tiers=[
                CommissionTier("Bronze", 0, 0.30, 0.70, 0.00),  # 30/70 split (Jorge/Partner)
                CommissionTier("Silver", 100000, 0.25, 0.75, 0.02),  # Better terms at $100K
                CommissionTier("Gold", 250000, 0.20, 0.80, 0.05),  # Even better at $250K
                CommissionTier("Platinum", 500000, 0.15, 0.85, 0.10),  # Best terms at $500K+
            ],
            transaction_fees={"setup": 0, "per_transaction": 5.0},
            monthly_minimums={"subscription": 2999.0},
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        self.revenue_structures["default_franchise"] = franchise_structure

        # MLS Provider Structure (Data value-based)
        mls_structure = RevenueStructure(
            partner_id="default_mls",
            partner_type=PartnerType.MLS_PROVIDER,
            base_commission_tiers=[
                CommissionTier("Standard", 0, 0.80, 0.20, 0.00),  # Jorge gets more (data is valuable)
                CommissionTier("Premium", 50000, 0.75, 0.25, 0.02),
                CommissionTier("Enterprise", 100000, 0.70, 0.30, 0.05),
            ],
            transaction_fees={"api_call": 0.01, "data_sync": 0.05},
            monthly_minimums={"data_access": 1500.0},
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        self.revenue_structures["default_mls"] = mls_structure

        # Technology Partner Structure (Integration value-based)
        tech_structure = RevenueStructure(
            partner_id="default_technology",
            partner_type=PartnerType.TECHNOLOGY,
            base_commission_tiers=[
                CommissionTier("Basic", 0, 0.60, 0.40, 0.00),  # 60/40 split
                CommissionTier("Advanced", 25000, 0.55, 0.45, 0.02),
                CommissionTier("Strategic", 75000, 0.50, 0.50, 0.05),
            ],
            transaction_fees={"integration": 100.0, "support": 50.0},
            monthly_minimums={"platform_fee": 500.0},
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        self.revenue_structures["default_technology"] = tech_structure

        # Regional Distributor Structure (Market development)
        distributor_structure = RevenueStructure(
            partner_id="default_distributor",
            partner_type=PartnerType.REGIONAL_DISTRIBUTOR,
            base_commission_tiers=[
                CommissionTier("Territory", 0, 0.50, 0.50, 0.00),  # Equal split for market development
                CommissionTier("Regional", 200000, 0.45, 0.55, 0.03),
                CommissionTier("National", 500000, 0.40, 0.60, 0.08),
            ],
            transaction_fees={"territory_fee": 1000.0},
            monthly_minimums={"market_development": 5000.0},
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        self.revenue_structures["default_distributor"] = distributor_structure

    async def setup_partner_revenue_structure(
        self, partner_id: str, partner_type: PartnerType, custom_structure: Optional[RevenueStructure] = None
    ) -> bool:
        """
        Set up revenue sharing structure for a specific partner
        """
        try:
            if custom_structure:
                # Use provided custom structure
                structure = custom_structure
                structure.partner_id = partner_id
            else:
                # Use default structure for partner type
                default_key = f"default_{partner_type.value}"
                if default_key not in self.revenue_structures:
                    raise ValueError(f"No default structure found for partner type: {partner_type.value}")

                # Clone default structure
                default_structure = self.revenue_structures[default_key]
                structure = RevenueStructure(
                    partner_id=partner_id,
                    partner_type=partner_type,
                    base_commission_tiers=default_structure.base_commission_tiers.copy(),
                    transaction_fees=default_structure.transaction_fees.copy(),
                    monthly_minimums=default_structure.monthly_minimums.copy(),
                    performance_bonuses=default_structure.performance_bonuses.copy(),
                    payment_frequency=default_structure.payment_frequency,
                    currency=default_structure.currency,
                )

            # Store partner-specific structure
            self.revenue_structures[partner_id] = structure

            # Initialize partner financials tracking
            self.partner_financials[partner_id] = []

            logger.info(f"Revenue structure configured for partner: {partner_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to setup revenue structure for partner {partner_id}: {str(e)}")
            return False

    async def calculate_commission_split(
        self,
        partner_id: str,
        gross_amount: float,
        revenue_type: RevenueType,
        deal_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float, str]:
        """
        Calculate commission split between Jorge and partner
        Returns: (jorge_amount, partner_amount, commission_tier)
        """
        try:
            if partner_id not in self.revenue_structures:
                raise ValueError(f"No revenue structure found for partner: {partner_id}")

            structure = self.revenue_structures[partner_id]

            # Get partner's current volume to determine tier
            current_volume = await self._calculate_partner_volume(partner_id)

            # Determine applicable commission tier
            applicable_tier = structure.base_commission_tiers[0]  # Default to first tier
            for tier in reversed(structure.base_commission_tiers):  # Check from highest to lowest
                if current_volume >= tier.min_threshold:
                    applicable_tier = tier
                    break

            # Calculate base split
            jorge_amount = gross_amount * applicable_tier.jorge_percentage
            partner_amount = gross_amount * applicable_tier.partner_percentage

            # Apply performance bonus if applicable
            if applicable_tier.performance_bonus > 0:
                bonus_amount = gross_amount * applicable_tier.performance_bonus
                # Performance bonus comes from Jorge's share
                jorge_amount -= bonus_amount
                partner_amount += bonus_amount

            # Apply transaction fees if applicable
            if revenue_type == RevenueType.TRANSACTION:
                transaction_fee = structure.transaction_fees.get("per_transaction", 0)
                jorge_amount += transaction_fee  # Transaction fees go to Jorge

            # Ensure amounts are properly rounded
            jorge_amount = float(Decimal(str(jorge_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            partner_amount = float(Decimal(str(partner_amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

            logger.info(
                f"Commission calculated for {partner_id}: Jorge=${jorge_amount:.2f}, Partner=${partner_amount:.2f}, Tier={applicable_tier.tier_name}"
            )

            return jorge_amount, partner_amount, applicable_tier.tier_name

        except Exception as e:
            logger.error(f"Failed to calculate commission split for partner {partner_id}: {str(e)}")
            # Default to 50/50 split on error
            jorge_amount = gross_amount * 0.5
            partner_amount = gross_amount * 0.5
            return jorge_amount, partner_amount, "error_default"

    async def _calculate_partner_volume(self, partner_id: str) -> float:
        """Calculate partner's volume for the current period"""
        # Calculate volume over the last 12 months
        cutoff_date = datetime.now() - timedelta(days=365)

        partner_transactions = [
            t for t in self.transactions if t.partner_id == partner_id and t.transaction_date >= cutoff_date
        ]

        total_volume = sum(t.gross_amount for t in partner_transactions)
        return total_volume

    async def process_revenue_transaction(
        self,
        partner_id: str,
        gross_amount: float,
        revenue_type: RevenueType,
        currency: str = "USD",
        deal_metadata: Optional[Dict[str, Any]] = None,
    ) -> RevenueTransaction:
        """
        Process a single revenue transaction and split accordingly
        """
        try:
            # Generate transaction ID
            transaction_id = f"rev_{partner_id}_{int(datetime.now().timestamp())}_{len(self.transactions)}"

            # Calculate commission split
            jorge_amount, partner_amount, tier = await self.calculate_commission_split(
                partner_id, gross_amount, revenue_type, deal_metadata
            )

            # Handle currency conversion if needed
            exchange_rate = 1.0
            usd_equivalent = gross_amount
            if currency != "USD":
                exchange_rate = await self._get_exchange_rate(currency, "USD")
                usd_equivalent = gross_amount * exchange_rate

            # Create transaction record
            transaction = RevenueTransaction(
                transaction_id=transaction_id,
                partner_id=partner_id,
                revenue_type=revenue_type,
                gross_amount=gross_amount,
                jorge_amount=jorge_amount,
                partner_amount=partner_amount,
                currency=currency,
                exchange_rate=exchange_rate,
                usd_equivalent=usd_equivalent,
                commission_tier=tier,
                deal_id=deal_metadata.get("deal_id") if deal_metadata else None,
                agent_id=deal_metadata.get("agent_id") if deal_metadata else None,
                property_id=deal_metadata.get("property_id") if deal_metadata else None,
                metadata=deal_metadata or {},
            )

            # Store transaction
            self.transactions.append(transaction)

            # Update partner financials
            await self._update_partner_financials(partner_id, transaction)

            # Trigger payment processing if real-time
            structure = self.revenue_structures.get(partner_id)
            if structure and structure.payment_frequency == PaymentFrequency.REAL_TIME:
                await self._process_payment(partner_id, transaction)

            logger.info(f"Revenue transaction processed: {transaction_id}")
            return transaction

        except Exception as e:
            logger.error(f"Failed to process revenue transaction: {str(e)}")
            raise

    async def _get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate between currencies"""
        # In production, this would connect to a real exchange rate API
        # Using mock exchange rates for now
        mock_rates = {"USD": 1.0, "CAD": 0.74, "GBP": 1.27, "EUR": 1.09, "AUD": 0.66, "JPY": 0.0067}

        from_rate = mock_rates.get(from_currency, 1.0)
        to_rate = mock_rates.get(to_currency, 1.0)

        return to_rate / from_rate

    async def _update_partner_financials(self, partner_id: str, transaction: RevenueTransaction):
        """Update partner financial summary"""
        # This would update real-time financial tracking
        # For now, we'll just log the update
        logger.info(f"Updated financials for partner {partner_id}: +${transaction.partner_amount:.2f}")

    async def _process_payment(self, partner_id: str, transaction: RevenueTransaction):
        """Process payment to partner (real-time or scheduled)"""
        # This would integrate with payment processing systems
        # For now, we'll just log the payment
        logger.info(
            f"Payment processed for partner {partner_id}: ${transaction.partner_amount:.2f} {transaction.currency}"
        )

    async def generate_partner_financial_report(
        self, partner_id: str, start_date: datetime, end_date: datetime
    ) -> PartnerFinancials:
        """
        Generate comprehensive financial report for partner
        """
        try:
            # Filter transactions for period
            partner_transactions = [
                t
                for t in self.transactions
                if t.partner_id == partner_id and start_date <= t.transaction_date <= end_date
            ]

            if not partner_transactions:
                # Return empty report
                return PartnerFinancials(
                    partner_id=partner_id,
                    period_start=start_date,
                    period_end=end_date,
                    gross_revenue=0.0,
                    jorge_revenue=0.0,
                    partner_revenue=0.0,
                    transaction_count=0,
                    avg_transaction_value=0.0,
                    commission_tier_distribution={},
                    currency="USD",
                )

            # Calculate totals
            gross_revenue = sum(t.gross_amount for t in partner_transactions)
            jorge_revenue = sum(t.jorge_amount for t in partner_transactions)
            partner_revenue = sum(t.partner_amount for t in partner_transactions)
            transaction_count = len(partner_transactions)
            avg_transaction_value = gross_revenue / transaction_count if transaction_count > 0 else 0.0

            # Commission tier distribution
            tier_distribution = {}
            for transaction in partner_transactions:
                tier = transaction.commission_tier
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

            # Get partner currency
            structure = self.revenue_structures.get(partner_id)
            currency = structure.currency if structure else "USD"

            # Calculate tax if applicable
            tax_amount = 0.0
            if structure and structure.tax_rate > 0:
                tax_amount = partner_revenue * structure.tax_rate

            # Calculate net payout
            net_payout = partner_revenue - tax_amount

            financials = PartnerFinancials(
                partner_id=partner_id,
                period_start=start_date,
                period_end=end_date,
                gross_revenue=gross_revenue,
                jorge_revenue=jorge_revenue,
                partner_revenue=partner_revenue,
                transaction_count=transaction_count,
                avg_transaction_value=avg_transaction_value,
                commission_tier_distribution=tier_distribution,
                currency=currency,
                tax_amount=tax_amount,
                net_payout=net_payout,
            )

            return financials

        except Exception as e:
            logger.error(f"Failed to generate financial report for partner {partner_id}: {str(e)}")
            raise

    async def get_global_revenue_summary(self) -> Dict[str, Any]:
        """
        Get global revenue summary across all partners
        """
        try:
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

            # Current month transactions
            current_month_transactions = [t for t in self.transactions if t.transaction_date >= current_month_start]

            # Last month transactions
            last_month_transactions = [
                t for t in self.transactions if last_month_start <= t.transaction_date < current_month_start
            ]

            # Calculate current month metrics
            current_gross = sum(t.gross_amount for t in current_month_transactions)
            current_jorge = sum(t.jorge_amount for t in current_month_transactions)
            current_partner = sum(t.partner_amount for t in current_month_transactions)

            # Calculate last month metrics
            last_gross = sum(t.gross_amount for t in last_month_transactions)
            last_jorge = sum(t.jorge_amount for t in last_month_transactions)
            last_partner = sum(t.partner_amount for t in last_month_transactions)

            # Calculate growth rates
            gross_growth = ((current_gross - last_gross) / last_gross * 100) if last_gross > 0 else 0
            jorge_growth = ((current_jorge - last_jorge) / last_jorge * 100) if last_jorge > 0 else 0
            partner_growth = ((current_partner - last_partner) / last_partner * 100) if last_partner > 0 else 0

            # Partner type breakdown
            partner_type_revenue = {}
            for partner_id, structure in self.revenue_structures.items():
                if partner_id.startswith("default_"):
                    continue

                partner_transactions = [t for t in current_month_transactions if t.partner_id == partner_id]

                partner_total = sum(t.partner_amount for t in partner_transactions)
                partner_type = structure.partner_type.value

                if partner_type not in partner_type_revenue:
                    partner_type_revenue[partner_type] = 0.0
                partner_type_revenue[partner_type] += partner_total

            # Top performing partners
            partner_performance = {}
            for partner_id in self.revenue_structures.keys():
                if partner_id.startswith("default_"):
                    continue

                partner_transactions = [t for t in current_month_transactions if t.partner_id == partner_id]

                partner_revenue = sum(t.partner_amount for t in partner_transactions)
                partner_performance[partner_id] = partner_revenue

            top_partners = sorted(partner_performance.items(), key=lambda x: x[1], reverse=True)[:5]

            summary = {
                "current_month": {
                    "gross_revenue": current_gross,
                    "jorge_revenue": current_jorge,
                    "partner_revenue": current_partner,
                    "transaction_count": len(current_month_transactions),
                },
                "last_month": {
                    "gross_revenue": last_gross,
                    "jorge_revenue": last_jorge,
                    "partner_revenue": last_partner,
                    "transaction_count": len(last_month_transactions),
                },
                "growth_rates": {
                    "gross_revenue": gross_growth,
                    "jorge_revenue": jorge_growth,
                    "partner_revenue": partner_growth,
                },
                "partner_type_breakdown": partner_type_revenue,
                "top_performing_partners": [{"partner_id": pid, "revenue": revenue} for pid, revenue in top_partners],
                "total_partners": len([p for p in self.revenue_structures.keys() if not p.startswith("default_")]),
                "generated_at": datetime.now().isoformat(),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to generate global revenue summary: {str(e)}")
            return {}

    async def calculate_annual_projections(self, partner_id: str) -> Dict[str, Any]:
        """
        Calculate annual revenue projections for partner
        """
        try:
            # Get last 6 months of data
            six_months_ago = datetime.now() - timedelta(days=180)
            recent_transactions = [
                t for t in self.transactions if t.partner_id == partner_id and t.transaction_date >= six_months_ago
            ]

            if len(recent_transactions) < 3:  # Need minimum data
                return {"error": "Insufficient data for projection"}

            # Calculate monthly averages
            monthly_revenue = {}
            for transaction in recent_transactions:
                month_key = transaction.transaction_date.strftime("%Y-%m")
                if month_key not in monthly_revenue:
                    monthly_revenue[month_key] = 0.0
                monthly_revenue[month_key] += transaction.partner_amount

            # Calculate growth trend
            monthly_values = list(monthly_revenue.values())
            if len(monthly_values) >= 2:
                avg_growth = (
                    sum(
                        (monthly_values[i] - monthly_values[i - 1]) / monthly_values[i - 1]
                        for i in range(1, len(monthly_values))
                        if monthly_values[i - 1] > 0
                    )
                    / (len(monthly_values) - 1)
                    if len(monthly_values) > 1
                    else 0
                )
            else:
                avg_growth = 0

            # Project next 12 months
            current_monthly_avg = sum(monthly_values) / len(monthly_values)

            projections = []
            projected_monthly = current_monthly_avg
            for month in range(12):
                projected_monthly *= 1 + avg_growth
                projections.append({"month": month + 1, "projected_revenue": round(projected_monthly, 2)})

            annual_projection = sum(p["projected_revenue"] for p in projections)

            return {
                "partner_id": partner_id,
                "current_monthly_avg": round(current_monthly_avg, 2),
                "projected_growth_rate": round(avg_growth * 100, 2),
                "annual_projection": round(annual_projection, 2),
                "monthly_projections": projections,
                "confidence_score": min(len(monthly_values) / 6, 1.0),  # Based on data availability
            }

        except Exception as e:
            logger.error(f"Failed to calculate projections for partner {partner_id}: {str(e)}")
            return {"error": str(e)}


# Global revenue manager instance
global_revenue_manager = GlobalRevenueManager()
