"""
Corporate Billing Service

Enterprise billing and invoicing system with volume pricing tiers,
corporate contract management, and revenue sharing calculations.
Extends the base billing service for Fortune 500 partnerships.
"""

import asyncio
import calendar
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ghl_real_estate_ai.api.schemas.billing import SubscriptionTier
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.billing_service import BillingService, BillingServiceError
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager

logger = get_logger(__name__)


class CorporateBillingError(Exception):
    """Exception for corporate billing service errors."""

    def __init__(
        self,
        message: str,
        partnership_id: Optional[str] = None,
        contract_id: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.partnership_id = partnership_id
        self.contract_id = contract_id
        self.error_code = error_code
        super().__init__(message)


class VolumeDiscountTier:
    """Volume discount tier configurations for enterprise partnerships."""

    BRONZE = {
        "name": "Bronze Volume",
        "min_monthly_volume": 10,
        "max_monthly_volume": 49,
        "discount_percentage": Decimal("0.05"),  # 5%
        "base_rate": Decimal("150.00"),
        "setup_fee": Decimal("2500.00"),
    }

    SILVER = {
        "name": "Silver Volume",
        "min_monthly_volume": 50,
        "max_monthly_volume": 199,
        "discount_percentage": Decimal("0.15"),  # 15%
        "base_rate": Decimal("125.00"),
        "setup_fee": Decimal("5000.00"),
    }

    GOLD = {
        "name": "Gold Volume",
        "min_monthly_volume": 200,
        "max_monthly_volume": 499,
        "discount_percentage": Decimal("0.25"),  # 25%
        "base_rate": Decimal("100.00"),
        "setup_fee": Decimal("10000.00"),
    }

    PLATINUM = {
        "name": "Platinum Volume",
        "min_monthly_volume": 500,
        "max_monthly_volume": None,  # Unlimited
        "discount_percentage": Decimal("0.40"),  # 40%
        "base_rate": Decimal("75.00"),
        "setup_fee": Decimal("25000.00"),
    }


class CorporateBillingService:
    """
    Enterprise billing service for Fortune 500 corporate partnerships.

    Handles volume pricing, corporate contracts, revenue sharing,
    and enterprise-grade billing workflows.
    """

    def __init__(self):
        """Initialize corporate billing service."""
        self.billing_service = BillingService()
        self.subscription_manager = SubscriptionManager()
        self.cache_service = CacheService()

        # Volume discount tiers
        self.volume_tiers = {
            "bronze": VolumeDiscountTier.BRONZE,
            "silver": VolumeDiscountTier.SILVER,
            "gold": VolumeDiscountTier.GOLD,
            "platinum": VolumeDiscountTier.PLATINUM,
        }

        logger.info("CorporateBillingService initialized successfully")

    # ===================================================================
    # Corporate Contract Management
    # ===================================================================

    async def create_enterprise_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create enterprise contract with volume pricing and custom terms.

        Args:
            contract_data: Contract configuration and pricing terms

        Returns:
            Created contract with pricing structure and billing schedule

        Raises:
            CorporateBillingError: If contract creation fails
        """
        try:
            contract_id = str(uuid4())
            logger.info(
                f"Creating enterprise contract for partnership {contract_data.get('partnership_id')} (ID: {contract_id})"
            )

            # Validate contract data
            required_fields = [
                "partnership_id",
                "expected_monthly_volume",
                "contract_term_months",
                "billing_contact_email",
                "payment_terms",
            ]
            missing_fields = [field for field in required_fields if field not in contract_data]
            if missing_fields:
                raise CorporateBillingError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    contract_id=contract_id,
                    error_code="MISSING_REQUIRED_FIELDS",
                )

            # Determine volume tier based on expected volume
            volume_tier = self._determine_volume_tier(contract_data["expected_monthly_volume"])
            tier_config = self.volume_tiers[volume_tier]

            # Calculate pricing structure
            pricing_structure = await self._calculate_enterprise_pricing(
                contract_data["expected_monthly_volume"], tier_config, contract_data.get("custom_rate_per_transaction")
            )

            # Create contract terms
            contract_start = contract_data.get("start_date", datetime.now(timezone.utc))
            contract_end = contract_start + timedelta(days=contract_data["contract_term_months"] * 30)

            enterprise_contract = {
                "contract_id": contract_id,
                "partnership_id": contract_data["partnership_id"],
                "volume_tier": volume_tier,
                "tier_config": tier_config,
                "pricing_structure": pricing_structure,
                "contract_terms": {
                    "start_date": contract_start,
                    "end_date": contract_end,
                    "term_months": contract_data["contract_term_months"],
                    "auto_renewal": contract_data.get("auto_renewal", True),
                    "payment_terms": contract_data["payment_terms"],  # NET30, NET15, etc.
                    "billing_frequency": contract_data.get("billing_frequency", "monthly"),
                    "currency": contract_data.get("currency", "USD"),
                },
                "billing_contacts": {
                    "primary_email": contract_data["billing_contact_email"],
                    "secondary_email": contract_data.get("secondary_billing_contact"),
                    "accounts_payable_email": contract_data.get("ap_email"),
                },
                "volume_commitments": {
                    "minimum_monthly_volume": contract_data["expected_monthly_volume"],
                    "annual_volume_commitment": contract_data["expected_monthly_volume"] * 12,
                    "volume_shortfall_penalty": contract_data.get("volume_shortfall_penalty", Decimal("0.00")),
                },
                "revenue_sharing": {
                    "revenue_share_percentage": contract_data.get("revenue_share_percentage", Decimal("0.30")),
                    "minimum_revenue_guarantee": contract_data.get("minimum_revenue_guarantee", Decimal("0.00")),
                    "performance_bonus_threshold": contract_data.get("performance_bonus_threshold"),
                },
                "status": "draft",
                "created_at": datetime.now(timezone.utc),
                "total_billed": Decimal("0.00"),
                "total_volume": 0,
                "last_billing_date": None,
            }

            # Generate setup invoice if applicable
            if tier_config["setup_fee"] > 0:
                setup_invoice = await self._create_contract_setup_invoice(contract_id, tier_config["setup_fee"])
                enterprise_contract["setup_invoice"] = setup_invoice

            # Store contract
            await self.cache_service.set(
                f"enterprise_contract:{contract_id}",
                enterprise_contract,
                ttl=86400 * 365,  # 1 year
            )

            # Create billing schedule
            billing_schedule = await self._create_billing_schedule(contract_id, enterprise_contract)
            enterprise_contract["billing_schedule"] = billing_schedule

            logger.info(f"Enterprise contract {contract_id} created successfully")

            return {
                "success": True,
                "contract_id": contract_id,
                "contract": enterprise_contract,
                "estimated_annual_revenue": pricing_structure["estimated_annual_revenue"],
                "next_steps": [
                    "Contract review and approval",
                    "Setup fee payment processing",
                    "Billing integration activation",
                    "Volume tracking initialization",
                ],
            }

        except Exception as e:
            logger.error(f"Failed to create enterprise contract: {e}")
            raise CorporateBillingError(
                f"Contract creation failed: {str(e)}",
                partnership_id=contract_data.get("partnership_id"),
                contract_id=contract_id if "contract_id" in locals() else None,
                error_code="CONTRACT_CREATION_FAILED",
            )

    async def activate_enterprise_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Activate enterprise contract and begin billing cycle.

        Args:
            contract_id: Contract to activate

        Returns:
            Activated contract status and billing information
        """
        try:
            contract = await self.cache_service.get(f"enterprise_contract:{contract_id}")
            if not contract:
                raise CorporateBillingError(
                    f"Contract {contract_id} not found", contract_id=contract_id, error_code="CONTRACT_NOT_FOUND"
                )

            # Update contract status
            contract["status"] = "active"
            contract["activated_at"] = datetime.now(timezone.utc)
            contract["contract_terms"]["actual_start_date"] = datetime.now(timezone.utc)

            # Create enterprise customer in Stripe if needed
            enterprise_customer = await self._create_enterprise_customer(contract)
            contract["stripe_customer_id"] = enterprise_customer.id

            # Setup payment method for enterprise billing
            if contract["contract_terms"]["payment_terms"] in ["NET30", "NET15"]:
                # Setup invoice-based billing
                billing_config = await self._setup_invoice_billing(contract_id, contract)
                contract["billing_config"] = billing_config
            else:
                # Setup automatic billing
                auto_billing_config = await self._setup_automatic_billing(contract_id, contract)
                contract["billing_config"] = auto_billing_config

            # Initialize volume tracking
            volume_tracking = await self._initialize_volume_tracking(contract_id)
            contract["volume_tracking"] = volume_tracking

            # Save activated contract
            await self.cache_service.set(
                f"enterprise_contract:{contract_id}",
                contract,
                ttl=86400 * 365,  # 1 year
            )

            logger.info(f"Enterprise contract {contract_id} activated successfully")

            return {
                "success": True,
                "contract_id": contract_id,
                "status": "active",
                "billing_starts": contract["contract_terms"]["actual_start_date"],
                "stripe_customer_id": enterprise_customer.id,
                "volume_tracking_enabled": True,
            }

        except Exception as e:
            logger.error(f"Failed to activate contract {contract_id}: {e}")
            raise CorporateBillingError(
                f"Contract activation failed: {str(e)}",
                contract_id=contract_id,
                error_code="CONTRACT_ACTIVATION_FAILED",
            )

    # ===================================================================
    # Volume-Based Billing
    # ===================================================================

    async def process_volume_billing(
        self, contract_id: str, billing_period_start: datetime, billing_period_end: datetime
    ) -> Dict[str, Any]:
        """
        Process volume-based billing for enterprise contract.

        Args:
            contract_id: Enterprise contract ID
            billing_period_start: Start of billing period
            billing_period_end: End of billing period

        Returns:
            Billing results with volume calculations and invoice details
        """
        try:
            contract = await self.cache_service.get(f"enterprise_contract:{contract_id}")
            if not contract or contract["status"] != "active":
                raise CorporateBillingError(
                    f"Contract {contract_id} not active", contract_id=contract_id, error_code="CONTRACT_NOT_ACTIVE"
                )

            logger.info(
                f"Processing volume billing for contract {contract_id}, period {billing_period_start.date()} to {billing_period_end.date()}"
            )

            # Get actual volume for billing period
            period_volume = await self._get_period_volume(contract_id, billing_period_start, billing_period_end)

            # Calculate billing amounts
            billing_calculation = await self._calculate_volume_billing(
                contract, period_volume, billing_period_start, billing_period_end
            )

            # Apply contract-specific adjustments
            adjusted_billing = await self._apply_contract_adjustments(contract, billing_calculation, period_volume)

            # Generate enterprise invoice
            enterprise_invoice = await self._create_enterprise_invoice(
                contract_id, adjusted_billing, billing_period_start, billing_period_end
            )

            # Update contract metrics
            await self._update_contract_metrics(contract_id, period_volume, adjusted_billing["total_amount"])

            # Process payment based on contract terms
            payment_result = await self._process_enterprise_payment(contract, enterprise_invoice)

            logger.info(
                f"Volume billing processed for contract {contract_id}: "
                f"{period_volume['total_transactions']} transactions, "
                f"${adjusted_billing['total_amount']} total"
            )

            return {
                "success": True,
                "contract_id": contract_id,
                "billing_period": f"{billing_period_start.date()} to {billing_period_end.date()}",
                "volume_summary": period_volume,
                "billing_calculation": adjusted_billing,
                "invoice": enterprise_invoice,
                "payment_result": payment_result,
            }

        except Exception as e:
            logger.error(f"Volume billing failed for contract {contract_id}: {e}")
            raise CorporateBillingError(
                f"Volume billing processing failed: {str(e)}",
                contract_id=contract_id,
                error_code="VOLUME_BILLING_FAILED",
            )

    async def calculate_revenue_sharing(
        self, contract_id: str, revenue_period_start: datetime, revenue_period_end: datetime
    ) -> Dict[str, Any]:
        """
        Calculate revenue sharing for corporate partnership.

        Args:
            contract_id: Enterprise contract ID
            revenue_period_start: Start of revenue period
            revenue_period_end: End of revenue period

        Returns:
            Revenue sharing calculation with partner payout details
        """
        try:
            contract = await self.cache_service.get(f"enterprise_contract:{contract_id}")
            if not contract:
                raise CorporateBillingError(
                    f"Contract {contract_id} not found", contract_id=contract_id, error_code="CONTRACT_NOT_FOUND"
                )

            logger.info(
                f"Calculating revenue sharing for contract {contract_id}, period {revenue_period_start.date()} to {revenue_period_end.date()}"
            )

            # Get gross revenue for period
            gross_revenue = await self._get_period_gross_revenue(contract_id, revenue_period_start, revenue_period_end)

            # Get all costs and deductions
            cost_breakdown = await self._calculate_revenue_sharing_costs(
                contract_id, gross_revenue, revenue_period_start, revenue_period_end
            )

            # Calculate net revenue for sharing
            net_revenue = gross_revenue["total_revenue"] - cost_breakdown["total_deductions"]

            # Apply revenue sharing percentage
            revenue_share_config = contract["revenue_sharing"]
            share_percentage = revenue_share_config["revenue_share_percentage"]
            partner_share_amount = net_revenue * share_percentage

            # Apply minimum guarantees and performance bonuses
            final_payout = await self._apply_revenue_sharing_adjustments(
                contract, partner_share_amount, gross_revenue, cost_breakdown
            )

            revenue_sharing_result = {
                "contract_id": contract_id,
                "period_start": revenue_period_start,
                "period_end": revenue_period_end,
                "gross_revenue": gross_revenue,
                "cost_breakdown": cost_breakdown,
                "net_revenue": net_revenue,
                "share_percentage": float(share_percentage * 100),
                "calculated_share": partner_share_amount,
                "adjustments_applied": final_payout["adjustments"],
                "final_payout_amount": final_payout["final_amount"],
                "payout_status": "pending_approval",
                "calculated_at": datetime.now(timezone.utc),
            }

            # Store revenue sharing calculation
            await self.cache_service.set(
                f"revenue_sharing:{contract_id}:{revenue_period_start.strftime('%Y%m')}",
                revenue_sharing_result,
                ttl=86400 * 90,  # 90 days
            )

            logger.info(
                f"Revenue sharing calculated for contract {contract_id}: "
                f"${final_payout['final_amount']} payout from ${gross_revenue['total_revenue']} gross revenue"
            )

            return revenue_sharing_result

        except Exception as e:
            logger.error(f"Revenue sharing calculation failed for contract {contract_id}: {e}")
            raise CorporateBillingError(
                f"Revenue sharing calculation failed: {str(e)}",
                contract_id=contract_id,
                error_code="REVENUE_SHARING_CALCULATION_FAILED",
            )

    # ===================================================================
    # Enterprise Reporting & Analytics
    # ===================================================================

    async def generate_enterprise_billing_report(
        self, contract_id: str, report_period_months: int = 12
    ) -> Dict[str, Any]:
        """
        Generate comprehensive billing report for enterprise contract.

        Args:
            contract_id: Enterprise contract ID
            report_period_months: Number of months to include in report

        Returns:
            Detailed billing analysis and metrics
        """
        try:
            contract = await self.cache_service.get(f"enterprise_contract:{contract_id}")
            if not contract:
                raise CorporateBillingError(
                    f"Contract {contract_id} not found", contract_id=contract_id, error_code="CONTRACT_NOT_FOUND"
                )

            report_end = datetime.now(timezone.utc)
            report_start = report_end - timedelta(days=report_period_months * 30)

            logger.info(
                f"Generating enterprise billing report for contract {contract_id}, {report_period_months} months"
            )

            # Get billing summary metrics
            billing_summary = await self._get_contract_billing_summary(contract_id, report_start, report_end)

            # Get volume performance metrics
            volume_performance = await self._analyze_volume_performance(
                contract_id, contract["volume_commitments"], report_start, report_end
            )

            # Get revenue and profitability analysis
            revenue_analysis = await self._analyze_contract_revenue(contract_id, report_start, report_end)

            # Get payment performance metrics
            payment_performance = await self._analyze_payment_performance(contract_id, report_start, report_end)

            # Calculate contract health score
            health_score = await self._calculate_contract_health_score(
                billing_summary, volume_performance, payment_performance
            )

            # Generate recommendations
            recommendations = await self._generate_contract_recommendations(
                contract, billing_summary, volume_performance, revenue_analysis
            )

            enterprise_billing_report = {
                "contract_id": contract_id,
                "partnership_id": contract["partnership_id"],
                "report_period": {"start": report_start, "end": report_end, "months": report_period_months},
                "contract_summary": {
                    "tier": contract["volume_tier"],
                    "status": contract["status"],
                    "contract_value": contract["pricing_structure"]["estimated_annual_revenue"],
                    "days_remaining": (contract["contract_terms"]["end_date"] - datetime.now(timezone.utc)).days,
                },
                "billing_summary": billing_summary,
                "volume_performance": volume_performance,
                "revenue_analysis": revenue_analysis,
                "payment_performance": payment_performance,
                "health_score": health_score,
                "recommendations": recommendations,
                "generated_at": datetime.now(timezone.utc),
            }

            # Cache the report
            await self.cache_service.set(
                f"enterprise_billing_report:{contract_id}",
                enterprise_billing_report,
                ttl=86400,  # 24 hours
            )

            logger.info(f"Enterprise billing report generated for contract {contract_id}")

            return enterprise_billing_report

        except Exception as e:
            logger.error(f"Enterprise billing report generation failed for contract {contract_id}: {e}")
            raise CorporateBillingError(
                f"Billing report generation failed: {str(e)}",
                contract_id=contract_id,
                error_code="BILLING_REPORT_FAILED",
            )

    # ===================================================================
    # Private Helper Methods
    # ===================================================================

    def _determine_volume_tier(self, expected_monthly_volume: int) -> str:
        """Determine volume tier based on expected monthly volume."""
        if expected_monthly_volume >= 500:
            return "platinum"
        elif expected_monthly_volume >= 200:
            return "gold"
        elif expected_monthly_volume >= 50:
            return "silver"
        elif expected_monthly_volume >= 10:
            return "bronze"
        else:
            raise CorporateBillingError(
                f"Expected volume {expected_monthly_volume} below minimum threshold of 10 transactions",
                error_code="VOLUME_BELOW_MINIMUM",
            )

    async def _calculate_enterprise_pricing(
        self, monthly_volume: int, tier_config: Dict[str, Any], custom_rate: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Calculate enterprise pricing structure based on volume and tier."""
        if custom_rate:
            base_rate = custom_rate
        else:
            base_rate = tier_config["base_rate"]

        # Apply volume discount
        discount_percentage = tier_config["discount_percentage"]
        discounted_rate = base_rate * (Decimal("1") - discount_percentage)

        # Calculate annual projections
        annual_transactions = monthly_volume * 12
        annual_transaction_revenue = annual_transactions * discounted_rate
        setup_fee = tier_config["setup_fee"]

        return {
            "volume_tier": tier_config["name"],
            "base_rate_per_transaction": base_rate,
            "volume_discount_percentage": float(discount_percentage * 100),
            "discounted_rate_per_transaction": discounted_rate,
            "expected_monthly_volume": monthly_volume,
            "expected_annual_volume": annual_transactions,
            "setup_fee": setup_fee,
            "estimated_monthly_revenue": monthly_volume * discounted_rate,
            "estimated_annual_revenue": annual_transaction_revenue,
            "total_first_year_revenue": annual_transaction_revenue + setup_fee,
        }

    async def _create_contract_setup_invoice(self, contract_id: str, setup_fee: Decimal) -> Dict[str, Any]:
        """Create setup fee invoice for enterprise contract."""
        invoice_id = str(uuid4())

        setup_invoice = {
            "invoice_id": invoice_id,
            "contract_id": contract_id,
            "type": "setup_fee",
            "amount": setup_fee,
            "description": "Enterprise Contract Setup Fee",
            "status": "pending",
            "due_date": datetime.now(timezone.utc) + timedelta(days=30),
            "created_at": datetime.now(timezone.utc),
        }

        await self.cache_service.set(
            f"enterprise_invoice:{invoice_id}",
            setup_invoice,
            ttl=86400 * 90,  # 90 days
        )

        return setup_invoice

    async def _create_billing_schedule(self, contract_id: str, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create billing schedule for enterprise contract."""
        billing_frequency = contract["contract_terms"]["billing_frequency"]
        contract_start = contract["contract_terms"]["start_date"]
        contract_end = contract["contract_terms"]["end_date"]

        schedule = []
        current_date = contract_start

        while current_date < contract_end:
            if billing_frequency == "monthly":
                next_date = (
                    current_date.replace(month=current_date.month + 1)
                    if current_date.month < 12
                    else current_date.replace(year=current_date.year + 1, month=1)
                )
            elif billing_frequency == "quarterly":
                next_date = current_date + timedelta(days=90)
            else:  # annual
                next_date = current_date.replace(year=current_date.year + 1)

            if next_date > contract_end:
                next_date = contract_end

            schedule.append(
                {
                    "period_start": current_date,
                    "period_end": next_date,
                    "billing_date": next_date + timedelta(days=1),
                    "status": "scheduled",
                }
            )

            current_date = next_date

        return schedule

    async def _create_enterprise_customer(self, contract: Dict[str, Any]) -> Any:
        """Create enterprise customer in Stripe."""
        # Use the existing billing service to create enterprise customer
        customer_data = {
            "email": contract["billing_contacts"]["primary_email"],
            "name": f"Enterprise Contract {contract['contract_id']}",
            "description": f"Enterprise customer for partnership {contract['partnership_id']}",
            "metadata": {
                "contract_id": contract["contract_id"],
                "partnership_id": contract["partnership_id"],
                "volume_tier": contract["volume_tier"],
            },
        }

        # This would use the BillingService to create a Stripe customer
        # For now, return a mock customer object
        return type("Customer", (), {"id": f"cus_enterprise_{contract['contract_id'][:8]}"})()

    async def _setup_invoice_billing(self, contract_id: str, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Setup invoice-based billing for enterprise contract."""
        return {
            "billing_type": "invoice",
            "payment_terms": contract["contract_terms"]["payment_terms"],
            "invoice_delivery": "email",
            "auto_collection": False,
            "late_fee_percentage": Decimal("0.015"),  # 1.5% monthly
        }

    async def _setup_automatic_billing(self, contract_id: str, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Setup automatic billing for enterprise contract."""
        return {
            "billing_type": "automatic",
            "payment_terms": "immediate",
            "auto_collection": True,
            "retry_failed_payments": True,
            "max_retry_attempts": 3,
        }

    async def _initialize_volume_tracking(self, contract_id: str) -> Dict[str, Any]:
        """Initialize volume tracking for enterprise contract."""
        tracking_data = {
            "contract_id": contract_id,
            "current_period_volume": 0,
            "total_contract_volume": 0,
            "last_transaction_date": None,
            "volume_trend_7d": [],
            "volume_trend_30d": [],
            "created_at": datetime.now(timezone.utc),
        }

        await self.cache_service.set(
            f"volume_tracking:{contract_id}",
            tracking_data,
            ttl=86400 * 365,  # 1 year
        )

        return tracking_data

    async def _get_period_volume(
        self, contract_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Get transaction volume for billing period."""
        # This would query actual transaction data
        # For now, return mock data
        return {
            "total_transactions": 125,
            "transaction_breakdown": {"hot_leads": 45, "warm_leads": 55, "cold_leads": 25},
            "average_transaction_value": Decimal("1250.00"),
            "total_transaction_value": Decimal("156250.00"),
            "period_start": period_start,
            "period_end": period_end,
        }

    async def _calculate_volume_billing(
        self, contract: Dict[str, Any], volume_data: Dict[str, Any], period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate volume-based billing for period."""
        pricing = contract["pricing_structure"]
        rate_per_transaction = pricing["discounted_rate_per_transaction"]
        total_transactions = volume_data["total_transactions"]

        # Calculate base billing
        base_amount = Decimal(str(total_transactions)) * rate_per_transaction

        # Calculate any volume bonuses or penalties
        volume_adjustments = await self._calculate_volume_adjustments(contract, total_transactions)

        total_amount = base_amount + volume_adjustments["total_adjustment"]

        return {
            "base_amount": base_amount,
            "total_transactions": total_transactions,
            "rate_per_transaction": rate_per_transaction,
            "volume_adjustments": volume_adjustments,
            "total_amount": total_amount,
            "billing_period": f"{period_start.date()} to {period_end.date()}",
        }

    async def _apply_contract_adjustments(
        self, contract: Dict[str, Any], billing: Dict[str, Any], volume_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply contract-specific billing adjustments."""
        adjusted_billing = billing.copy()

        # Apply minimum volume penalties if applicable
        minimum_volume = contract["volume_commitments"]["minimum_monthly_volume"]
        actual_volume = volume_data["total_transactions"]

        if actual_volume < minimum_volume:
            shortfall_penalty = contract["volume_commitments"]["volume_shortfall_penalty"]
            penalty_amount = (minimum_volume - actual_volume) * shortfall_penalty
            adjusted_billing["volume_shortfall_penalty"] = penalty_amount
            adjusted_billing["total_amount"] += penalty_amount

        return adjusted_billing

    async def _create_enterprise_invoice(
        self, contract_id: str, billing_calculation: Dict[str, Any], period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Create enterprise invoice for billing period."""
        invoice_id = str(uuid4())

        enterprise_invoice = {
            "invoice_id": invoice_id,
            "contract_id": contract_id,
            "type": "volume_billing",
            "period_start": period_start,
            "period_end": period_end,
            "line_items": [
                {
                    "description": f"Volume billing for {billing_calculation['total_transactions']} transactions",
                    "quantity": billing_calculation["total_transactions"],
                    "rate": billing_calculation["rate_per_transaction"],
                    "amount": billing_calculation["base_amount"],
                }
            ],
            "adjustments": billing_calculation.get("volume_adjustments", {}),
            "total_amount": billing_calculation["total_amount"],
            "status": "pending",
            "due_date": datetime.now(timezone.utc) + timedelta(days=30),
            "created_at": datetime.now(timezone.utc),
        }

        # Add any additional fees or adjustments as line items
        if "volume_shortfall_penalty" in billing_calculation:
            enterprise_invoice["line_items"].append(
                {
                    "description": "Volume shortfall penalty",
                    "quantity": 1,
                    "rate": billing_calculation["volume_shortfall_penalty"],
                    "amount": billing_calculation["volume_shortfall_penalty"],
                }
            )

        await self.cache_service.set(
            f"enterprise_invoice:{invoice_id}",
            enterprise_invoice,
            ttl=86400 * 90,  # 90 days
        )

        return enterprise_invoice

    async def _update_contract_metrics(
        self, contract_id: str, volume_data: Dict[str, Any], billed_amount: Decimal
    ) -> None:
        """Update contract volume and billing metrics."""
        contract = await self.cache_service.get(f"enterprise_contract:{contract_id}")
        if contract:
            contract["total_volume"] += volume_data["total_transactions"]
            contract["total_billed"] += billed_amount
            contract["last_billing_date"] = datetime.now(timezone.utc)

            await self.cache_service.set(
                f"enterprise_contract:{contract_id}",
                contract,
                ttl=86400 * 365,  # 1 year
            )

    async def _process_enterprise_payment(self, contract: Dict[str, Any], invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment for enterprise invoice based on contract terms."""
        payment_terms = contract["contract_terms"]["payment_terms"]

        if payment_terms in ["NET30", "NET15"]:
            # Invoice-based payment - send invoice and wait for payment
            return {"payment_method": "invoice", "status": "invoice_sent", "payment_due_date": invoice["due_date"]}
        else:
            # Automatic payment processing
            return {
                "payment_method": "automatic",
                "status": "payment_processed",
                "payment_date": datetime.now(timezone.utc),
            }

    async def _calculate_volume_adjustments(self, contract: Dict[str, Any], actual_volume: int) -> Dict[str, Any]:
        """Calculate volume-based adjustments (bonuses, penalties, etc.)."""
        adjustments = {
            "volume_bonus": Decimal("0.00"),
            "volume_penalty": Decimal("0.00"),
            "total_adjustment": Decimal("0.00"),
            "adjustments_applied": [],
        }

        # Volume bonus for exceeding commitments
        minimum_volume = contract["volume_commitments"]["minimum_monthly_volume"]
        if actual_volume > minimum_volume * 1.2:  # 20% over commitment
            bonus_rate = Decimal("5.00")  # $5 bonus per excess transaction
            excess_transactions = actual_volume - minimum_volume
            volume_bonus = Decimal(str(excess_transactions)) * bonus_rate
            adjustments["volume_bonus"] = volume_bonus
            adjustments["total_adjustment"] += volume_bonus
            adjustments["adjustments_applied"].append(f"Volume bonus: {excess_transactions} excess transactions")

        return adjustments

    async def _get_period_gross_revenue(
        self, contract_id: str, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Get gross revenue for revenue sharing calculation."""
        # This would query actual revenue data
        return {
            "total_revenue": Decimal("250000.00"),
            "revenue_breakdown": {
                "transaction_fees": Decimal("200000.00"),
                "setup_fees": Decimal("25000.00"),
                "additional_services": Decimal("25000.00"),
            },
            "transaction_count": 125,
        }

    async def _calculate_revenue_sharing_costs(
        self, contract_id: str, gross_revenue: Dict[str, Any], period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate costs to deduct from gross revenue for sharing calculation."""
        # Calculate standard cost deductions
        gross_amount = gross_revenue["total_revenue"]

        cost_breakdown = {
            "platform_costs": gross_amount * Decimal("0.15"),  # 15% platform costs
            "payment_processing": gross_amount * Decimal("0.03"),  # 3% payment processing
            "customer_support": gross_amount * Decimal("0.05"),  # 5% customer support
            "technology_costs": gross_amount * Decimal("0.07"),  # 7% technology costs
        }

        cost_breakdown["total_deductions"] = sum(cost_breakdown.values())

        return cost_breakdown

    async def _apply_revenue_sharing_adjustments(
        self,
        contract: Dict[str, Any],
        calculated_share: Decimal,
        gross_revenue: Dict[str, Any],
        cost_breakdown: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply revenue sharing adjustments and guarantees."""
        revenue_config = contract["revenue_sharing"]
        adjustments = []

        final_amount = calculated_share

        # Apply minimum revenue guarantee
        minimum_guarantee = revenue_config.get("minimum_revenue_guarantee", Decimal("0.00"))
        if final_amount < minimum_guarantee:
            adjustment_amount = minimum_guarantee - final_amount
            final_amount = minimum_guarantee
            adjustments.append(f"Minimum guarantee adjustment: +${adjustment_amount}")

        # Apply performance bonus if applicable
        performance_threshold = revenue_config.get("performance_bonus_threshold")
        if performance_threshold and gross_revenue["total_revenue"] > performance_threshold:
            bonus_rate = Decimal("0.05")  # 5% bonus on excess revenue
            excess_revenue = gross_revenue["total_revenue"] - performance_threshold
            performance_bonus = excess_revenue * bonus_rate
            final_amount += performance_bonus
            adjustments.append(f"Performance bonus: +${performance_bonus}")

        return {"final_amount": final_amount, "adjustments": adjustments}

    async def _get_contract_billing_summary(
        self, contract_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get billing summary for contract period."""
        # Mock billing summary - would query actual data
        return {
            "total_invoices": 12,
            "total_billed": Decimal("1500000.00"),
            "total_paid": Decimal("1450000.00"),
            "outstanding_balance": Decimal("50000.00"),
            "average_monthly_billing": Decimal("125000.00"),
            "on_time_payment_rate": 0.95,
        }

    async def _analyze_volume_performance(
        self, contract_id: str, volume_commitments: Dict[str, Any], start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze volume performance against commitments."""
        return {
            "commitment_vs_actual": {
                "committed_annual": volume_commitments["annual_volume_commitment"],
                "actual_annual": 1200,
                "performance_percentage": 110.5,
            },
            "trend_analysis": {"monthly_growth_rate": 0.08, "volume_consistency": 0.92, "peak_month": "March 2025"},
        }

    async def _analyze_contract_revenue(
        self, contract_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze revenue performance for contract."""
        return {
            "total_revenue": Decimal("1500000.00"),
            "revenue_growth": Decimal("0.15"),  # 15% growth
            "profit_margin": Decimal("0.35"),  # 35% profit margin
            "revenue_per_transaction": Decimal("1250.00"),
        }

    async def _analyze_payment_performance(
        self, contract_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Analyze payment performance for contract."""
        return {
            "on_time_payments": 11,
            "late_payments": 1,
            "average_days_to_payment": 18,
            "payment_reliability_score": 0.95,
        }

    async def _calculate_contract_health_score(
        self, billing: Dict[str, Any], volume: Dict[str, Any], payment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall contract health score."""
        # Weighted scoring algorithm
        volume_score = min(100, volume["commitment_vs_actual"]["performance_percentage"])
        payment_score = payment["payment_reliability_score"] * 100
        billing_score = (billing["total_paid"] / billing["total_billed"]) * 100

        overall_score = volume_score * 0.4 + payment_score * 0.4 + billing_score * 0.2

        return {
            "overall_score": round(float(overall_score), 1),
            "volume_score": round(float(volume_score), 1),
            "payment_score": round(float(payment_score), 1),
            "billing_score": round(float(billing_score), 1),
            "health_status": "excellent"
            if overall_score >= 90
            else "good"
            if overall_score >= 80
            else "needs_attention",
        }

    async def _generate_contract_recommendations(
        self, contract: Dict[str, Any], billing: Dict[str, Any], volume: Dict[str, Any], revenue: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for contract optimization."""
        recommendations = []

        # Volume-based recommendations
        performance_pct = volume["commitment_vs_actual"]["performance_percentage"]
        if performance_pct > 120:
            recommendations.append("Consider tier upgrade - consistently exceeding volume commitments")

        if performance_pct < 80:
            recommendations.append("Volume below commitment - review business objectives")

        # Payment recommendations
        if billing["on_time_payment_rate"] < 0.90:
            recommendations.append("Consider payment terms adjustment to improve cash flow")

        # Revenue optimization
        if revenue["profit_margin"] > Decimal("0.40"):
            recommendations.append("High profit margin - opportunity for competitive pricing adjustments")

        return recommendations
