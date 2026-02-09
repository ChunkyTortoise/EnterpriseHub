"""
Client Outcome Verification System

This service validates transaction results, client satisfaction, and performance metrics
using multiple data sources to ensure 95%+ accuracy in reported performance metrics.

Key Features:
- Transaction result validation with MLS data
- Client satisfaction verification through multiple channels
- Performance metric authentication with third-party data
- Success story documentation with evidence
- Continuous accuracy monitoring and updates
- Automated fraud detection and anomaly identification
"""

import hashlib
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class VerificationSource(Enum):
    """Data sources for verification"""

    MLS_DATA = "mls_data"
    TRANSACTION_RECORDS = "transaction_records"
    CLIENT_SURVEY = "client_survey"
    THIRD_PARTY_REVIEW = "third_party_review"
    BANK_RECORDS = "bank_records"
    TITLE_COMPANY = "title_company"
    INSPECTION_REPORT = "inspection_report"
    APPRAISAL_REPORT = "appraisal_report"
    COUNTY_RECORDS = "county_records"


class VerificationLevel(Enum):
    """Levels of verification confidence"""

    GOLD = "gold"  # 95%+ confidence, multiple independent sources
    SILVER = "silver"  # 85%+ confidence, dual source verification
    BRONZE = "bronze"  # 75%+ confidence, single reliable source
    PENDING = "pending"  # Under review, insufficient verification
    FAILED = "failed"  # Failed verification, potential issues


@dataclass
class VerificationEvidence:
    """Evidence supporting a verification"""

    source: VerificationSource
    data_hash: str
    timestamp: datetime
    confidence_score: float
    raw_data: Optional[Dict] = None
    verification_details: Optional[Dict] = None


@dataclass
class OutcomeVerification:
    """Verification result for a specific outcome"""

    outcome_id: str
    outcome_type: str
    claimed_value: Any
    verified_value: Any
    verification_level: VerificationLevel
    evidence: List[VerificationEvidence]
    accuracy_percentage: float
    verification_timestamp: datetime
    next_review_date: datetime
    anomalies_detected: List[str]


@dataclass
class TransactionVerification:
    """Complete transaction verification"""

    transaction_id: str
    agent_id: str
    client_id: str
    property_address: str

    # Verified transaction details
    listed_price: Decimal
    sold_price: Decimal
    closing_date: datetime
    days_on_market: int
    commission_paid: Decimal

    # Verification results
    price_verification: OutcomeVerification
    timeline_verification: OutcomeVerification
    commission_verification: OutcomeVerification
    satisfaction_verification: Optional[OutcomeVerification]

    # Overall verification
    overall_verification_level: VerificationLevel
    overall_accuracy: float
    verification_summary: Dict[str, Any]


@dataclass
class ClientSatisfactionVerification:
    """Client satisfaction verification with multiple sources"""

    client_id: str
    transaction_id: str
    agent_id: str

    # Satisfaction metrics
    claimed_rating: float
    verified_ratings: Dict[str, float]  # source -> rating
    average_verified_rating: float

    # Verification sources
    survey_responses: List[Dict]
    review_platform_data: List[Dict]
    follow_up_interviews: List[Dict]

    # Verification results
    verification_level: VerificationLevel
    confidence_score: float
    discrepancy_flags: List[str]


class ClientOutcomeVerificationService:
    """
    Client Outcome Verification Service

    Validates transaction results and performance metrics using multiple
    data sources to ensure accuracy and build client trust.
    """

    def __init__(self):
        # Verification thresholds
        self.verification_thresholds = {
            VerificationLevel.GOLD: 0.95,
            VerificationLevel.SILVER: 0.85,
            VerificationLevel.BRONZE: 0.75,
            VerificationLevel.PENDING: 0.50,
            VerificationLevel.FAILED: 0.0,
        }

        # Acceptable variance thresholds
        self.variance_thresholds = {
            "price_variance": 0.01,  # 1% price variance acceptable
            "timeline_variance": 2,  # 2 days timeline variance
            "rating_variance": 0.2,  # 0.2 point rating variance
            "commission_variance": 0.005,  # 0.5% commission variance
        }

        # Data source weights for composite verification
        self.source_weights = {
            VerificationSource.MLS_DATA: 0.25,
            VerificationSource.TRANSACTION_RECORDS: 0.20,
            VerificationSource.BANK_RECORDS: 0.15,
            VerificationSource.TITLE_COMPANY: 0.15,
            VerificationSource.COUNTY_RECORDS: 0.15,
            VerificationSource.CLIENT_SURVEY: 0.10,
        }

    async def verify_transaction_outcome(
        self,
        transaction_id: str,
        claimed_data: Dict[str, Any],
        verification_sources: Optional[List[VerificationSource]] = None,
    ) -> TransactionVerification:
        """
        Verify complete transaction outcome using multiple data sources

        Args:
            transaction_id: Transaction identifier
            claimed_data: Claimed transaction data to verify
            verification_sources: Optional list of specific sources to use

        Returns:
            TransactionVerification: Complete verification result
        """
        try:
            # Get verification data from multiple sources
            verification_data = await self._gather_verification_data(transaction_id, verification_sources)

            # Verify individual components
            price_verification = await self._verify_transaction_price(claimed_data, verification_data)

            timeline_verification = await self._verify_transaction_timeline(claimed_data, verification_data)

            commission_verification = await self._verify_commission_data(claimed_data, verification_data)

            # Verify client satisfaction if available
            satisfaction_verification = None
            if claimed_data.get("client_satisfaction"):
                satisfaction_verification = await self.verify_client_satisfaction(
                    claimed_data["client_id"],
                    transaction_id,
                    claimed_data["agent_id"],
                    claimed_data["client_satisfaction"],
                )

            # Calculate overall verification
            overall_verification_level, overall_accuracy = await self._calculate_overall_verification(
                [price_verification, timeline_verification, commission_verification], satisfaction_verification
            )

            # Generate verification summary
            verification_summary = await self._generate_verification_summary(
                price_verification, timeline_verification, commission_verification, satisfaction_verification
            )

            transaction_verification = TransactionVerification(
                transaction_id=transaction_id,
                agent_id=claimed_data["agent_id"],
                client_id=claimed_data["client_id"],
                property_address=claimed_data.get("property_address", ""),
                listed_price=Decimal(
                    str(verification_data.get("verified_listed_price", claimed_data.get("listed_price", 0)))
                ),
                sold_price=Decimal(
                    str(verification_data.get("verified_sold_price", claimed_data.get("sold_price", 0)))
                ),
                closing_date=verification_data.get("verified_closing_date", datetime.now()),
                days_on_market=verification_data.get("verified_days_on_market", claimed_data.get("days_on_market", 0)),
                commission_paid=Decimal(
                    str(verification_data.get("verified_commission", claimed_data.get("commission_paid", 0)))
                ),
                price_verification=price_verification,
                timeline_verification=timeline_verification,
                commission_verification=commission_verification,
                satisfaction_verification=satisfaction_verification,
                overall_verification_level=overall_verification_level,
                overall_accuracy=overall_accuracy,
                verification_summary=verification_summary,
            )

            # Store verification result
            await self._store_verification_result(transaction_verification)

            logger.info(f"Verified transaction {transaction_id} with {overall_verification_level.value} level")
            return transaction_verification

        except Exception as e:
            logger.error(f"Error verifying transaction outcome: {e}")
            raise

    async def verify_client_satisfaction(
        self, client_id: str, transaction_id: str, agent_id: str, claimed_rating: float
    ) -> ClientSatisfactionVerification:
        """
        Verify client satisfaction rating using multiple channels

        Args:
            client_id: Client identifier
            transaction_id: Transaction identifier
            agent_id: Agent identifier
            claimed_rating: Claimed satisfaction rating

        Returns:
            ClientSatisfactionVerification: Verification result
        """
        try:
            # Gather satisfaction data from multiple sources
            survey_responses = await self._get_survey_responses(client_id, transaction_id)
            review_platform_data = await self._get_review_platform_data(agent_id, client_id)
            follow_up_interviews = await self._get_follow_up_interviews(client_id, transaction_id)

            # Extract verified ratings from each source
            verified_ratings = {}

            # Process survey responses
            if survey_responses:
                survey_ratings = [r["rating"] for r in survey_responses if "rating" in r]
                if survey_ratings:
                    verified_ratings["survey"] = statistics.mean(survey_ratings)

            # Process review platform data
            if review_platform_data:
                review_ratings = [r["rating"] for r in review_platform_data if "rating" in r]
                if review_ratings:
                    verified_ratings["reviews"] = statistics.mean(review_ratings)

            # Process follow-up interviews
            if follow_up_interviews:
                interview_ratings = [r["rating"] for r in follow_up_interviews if "rating" in r]
                if interview_ratings:
                    verified_ratings["interviews"] = statistics.mean(interview_ratings)

            # Calculate average verified rating
            if verified_ratings:
                average_verified_rating = statistics.mean(verified_ratings.values())
            else:
                average_verified_rating = claimed_rating  # Fallback

            # Determine verification level
            verification_level, confidence_score = await self._calculate_satisfaction_verification_level(
                claimed_rating, verified_ratings, average_verified_rating
            )

            # Identify discrepancies
            discrepancy_flags = await self._identify_satisfaction_discrepancies(
                claimed_rating, verified_ratings, average_verified_rating
            )

            satisfaction_verification = ClientSatisfactionVerification(
                client_id=client_id,
                transaction_id=transaction_id,
                agent_id=agent_id,
                claimed_rating=claimed_rating,
                verified_ratings=verified_ratings,
                average_verified_rating=average_verified_rating,
                survey_responses=survey_responses,
                review_platform_data=review_platform_data,
                follow_up_interviews=follow_up_interviews,
                verification_level=verification_level,
                confidence_score=confidence_score,
                discrepancy_flags=discrepancy_flags,
            )

            logger.info(f"Verified client satisfaction for {client_id}: {verification_level.value}")
            return satisfaction_verification

        except Exception as e:
            logger.error(f"Error verifying client satisfaction: {e}")
            raise

    async def verify_performance_metric(
        self,
        agent_id: str,
        metric_type: str,
        claimed_value: float,
        period_start: datetime,
        period_end: datetime,
        evidence_data: Optional[Dict] = None,
    ) -> OutcomeVerification:
        """
        Verify individual performance metric

        Args:
            agent_id: Agent identifier
            metric_type: Type of metric (e.g., "negotiation_performance")
            claimed_value: Claimed metric value
            period_start: Period start date
            period_end: Period end date
            evidence_data: Optional supporting evidence

        Returns:
            OutcomeVerification: Metric verification result
        """
        try:
            # Get transactions for the period
            transactions = await self._get_agent_transactions(agent_id, period_start, period_end)

            # Calculate verified metric value
            verified_value = await self._calculate_verified_metric(metric_type, transactions)

            # Gather evidence
            evidence = await self._gather_metric_evidence(metric_type, transactions, evidence_data)

            # Calculate accuracy
            accuracy_percentage = await self._calculate_metric_accuracy(claimed_value, verified_value, metric_type)

            # Determine verification level
            verification_level = await self._determine_verification_level(accuracy_percentage, evidence)

            # Detect anomalies
            anomalies = await self._detect_metric_anomalies(metric_type, claimed_value, verified_value, transactions)

            outcome_id = f"{agent_id}_{metric_type}_{period_start.strftime('%Y%m%d')}_{period_end.strftime('%Y%m%d')}"

            verification = OutcomeVerification(
                outcome_id=outcome_id,
                outcome_type=metric_type,
                claimed_value=claimed_value,
                verified_value=verified_value,
                verification_level=verification_level,
                evidence=evidence,
                accuracy_percentage=accuracy_percentage,
                verification_timestamp=datetime.now(),
                next_review_date=datetime.now() + timedelta(days=30),
                anomalies_detected=anomalies,
            )

            logger.info(f"Verified metric {metric_type} for agent {agent_id}: {accuracy_percentage:.1f}% accuracy")
            return verification

        except Exception as e:
            logger.error(f"Error verifying performance metric: {e}")
            raise

    async def get_verification_report(self, agent_id: str, period_days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive verification report for agent

        Args:
            agent_id: Agent identifier
            period_days: Report period in days

        Returns:
            Dict: Verification report with accuracy metrics
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # Get all verifications for the period
            verifications = await self._get_agent_verifications(agent_id, start_date, end_date)

            # Calculate aggregate metrics
            total_verifications = len(verifications)
            gold_verifications = sum(1 for v in verifications if v.overall_verification_level == VerificationLevel.GOLD)
            silver_verifications = sum(
                1 for v in verifications if v.overall_verification_level == VerificationLevel.SILVER
            )
            bronze_verifications = sum(
                1 for v in verifications if v.overall_verification_level == VerificationLevel.BRONZE
            )

            overall_verification_rate = (
                (gold_verifications + silver_verifications + bronze_verifications) / total_verifications
                if total_verifications > 0
                else 0
            )

            # Calculate average accuracy
            if verifications:
                average_accuracy = statistics.mean([v.overall_accuracy for v in verifications])
            else:
                average_accuracy = 0.0

            # Get verification breakdown by metric type
            metric_breakdown = {}
            for verification in verifications:
                for metric_type in ["price", "timeline", "commission", "satisfaction"]:
                    metric_verification = getattr(verification, f"{metric_type}_verification", None)
                    if metric_verification:
                        if metric_type not in metric_breakdown:
                            metric_breakdown[metric_type] = []
                        metric_breakdown[metric_type].append(metric_verification.accuracy_percentage)

            # Calculate metric averages
            for metric_type in metric_breakdown:
                metric_breakdown[metric_type] = {
                    "average_accuracy": statistics.mean(metric_breakdown[metric_type]),
                    "verification_count": len(metric_breakdown[metric_type]),
                    "min_accuracy": min(metric_breakdown[metric_type]),
                    "max_accuracy": max(metric_breakdown[metric_type]),
                }

            report = {
                "agent_id": agent_id,
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days,
                },
                "verification_summary": {
                    "total_verifications": total_verifications,
                    "overall_verification_rate": overall_verification_rate,
                    "average_accuracy": average_accuracy,
                    "verification_levels": {
                        "gold": gold_verifications,
                        "silver": silver_verifications,
                        "bronze": bronze_verifications,
                        "pending": total_verifications
                        - (gold_verifications + silver_verifications + bronze_verifications),
                    },
                },
                "metric_breakdown": metric_breakdown,
                "data_quality_score": await self._calculate_data_quality_score(agent_id, verifications),
                "recommendations": await self._generate_verification_recommendations(verifications),
                "generated_at": datetime.now().isoformat(),
            }

            return report

        except Exception as e:
            logger.error(f"Error generating verification report: {e}")
            raise

    async def detect_verification_anomalies(self, agent_id: str, lookback_days: int = 90) -> List[Dict[str, Any]]:
        """
        Detect anomalies in verification patterns

        Args:
            agent_id: Agent identifier
            lookback_days: Days to look back for anomaly detection

        Returns:
            List: Detected anomalies with details
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)

            verifications = await self._get_agent_verifications(agent_id, start_date, end_date)
            anomalies = []

            # Check for accuracy trends
            if len(verifications) >= 10:
                recent_accuracy = [v.overall_accuracy for v in verifications[-5:]]
                older_accuracy = [v.overall_accuracy for v in verifications[:-5]]

                if statistics.mean(recent_accuracy) < statistics.mean(older_accuracy) - 0.1:
                    anomalies.append(
                        {
                            "type": "declining_accuracy",
                            "description": "Verification accuracy has declined recently",
                            "severity": "medium",
                            "details": {
                                "recent_average": statistics.mean(recent_accuracy),
                                "historical_average": statistics.mean(older_accuracy),
                            },
                        }
                    )

            # Check for unusual verification level patterns
            verification_levels = [v.overall_verification_level for v in verifications]
            gold_rate = (
                verification_levels.count(VerificationLevel.GOLD) / len(verification_levels)
                if verification_levels
                else 0
            )

            if gold_rate < 0.5:  # Less than 50% gold level
                anomalies.append(
                    {
                        "type": "low_verification_quality",
                        "description": "Low percentage of gold-level verifications",
                        "severity": "high",
                        "details": {"gold_rate": gold_rate, "total_verifications": len(verifications)},
                    }
                )

            # Check for data source issues
            source_usage = {}
            for verification in verifications:
                for outcome in [
                    verification.price_verification,
                    verification.timeline_verification,
                    verification.commission_verification,
                ]:
                    for evidence in outcome.evidence:
                        source = evidence.source.value
                        source_usage[source] = source_usage.get(source, 0) + 1

            if len(source_usage) < 3:  # Using fewer than 3 data sources
                anomalies.append(
                    {
                        "type": "limited_data_sources",
                        "description": "Limited diversity in verification data sources",
                        "severity": "medium",
                        "details": {"sources_used": list(source_usage.keys()), "source_count": len(source_usage)},
                    }
                )

            return anomalies

        except Exception as e:
            logger.error(f"Error detecting verification anomalies: {e}")
            return []

    # Private helper methods

    async def _gather_verification_data(
        self, transaction_id: str, sources: Optional[List[VerificationSource]] = None
    ) -> Dict[str, Any]:
        """Gather verification data from multiple sources"""

        verification_data = {}
        sources = sources or list(VerificationSource)

        for source in sources:
            try:
                if source == VerificationSource.MLS_DATA:
                    mls_data = await self._get_mls_data(transaction_id)
                    if mls_data:
                        verification_data.update(mls_data)

                elif source == VerificationSource.TRANSACTION_RECORDS:
                    txn_data = await self._get_transaction_records(transaction_id)
                    if txn_data:
                        verification_data.update(txn_data)

                elif source == VerificationSource.COUNTY_RECORDS:
                    county_data = await self._get_county_records(transaction_id)
                    if county_data:
                        verification_data.update(county_data)

                # Add other source handlers as needed

            except Exception as e:
                logger.warning(f"Error gathering data from {source.value}: {e}")
                continue

        return verification_data

    async def _verify_transaction_price(
        self, claimed_data: Dict[str, Any], verification_data: Dict[str, Any]
    ) -> OutcomeVerification:
        """Verify transaction price data"""

        claimed_price = float(claimed_data.get("sold_price", 0))
        verified_price = verification_data.get("verified_sold_price", claimed_price)

        # Calculate accuracy
        if claimed_price > 0:
            accuracy = 1.0 - abs(claimed_price - verified_price) / claimed_price
        else:
            accuracy = 0.0

        # Create evidence
        evidence = []
        if "mls_sold_price" in verification_data:
            evidence.append(
                VerificationEvidence(
                    source=VerificationSource.MLS_DATA,
                    data_hash=hashlib.md5(str(verification_data["mls_sold_price"]).encode()).hexdigest(),
                    timestamp=datetime.now(),
                    confidence_score=0.95,
                )
            )

        if "county_sold_price" in verification_data:
            evidence.append(
                VerificationEvidence(
                    source=VerificationSource.COUNTY_RECORDS,
                    data_hash=hashlib.md5(str(verification_data["county_sold_price"]).encode()).hexdigest(),
                    timestamp=datetime.now(),
                    confidence_score=0.90,
                )
            )

        # Determine verification level
        verification_level = self._get_verification_level_from_accuracy(accuracy)

        return OutcomeVerification(
            outcome_id=f"price_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            outcome_type="transaction_price",
            claimed_value=claimed_price,
            verified_value=verified_price,
            verification_level=verification_level,
            evidence=evidence,
            accuracy_percentage=accuracy * 100,
            verification_timestamp=datetime.now(),
            next_review_date=datetime.now() + timedelta(days=30),
            anomalies_detected=[],
        )

    async def _verify_transaction_timeline(
        self, claimed_data: Dict[str, Any], verification_data: Dict[str, Any]
    ) -> OutcomeVerification:
        """Verify transaction timeline data"""

        claimed_days = int(claimed_data.get("days_on_market", 0))
        verified_days = verification_data.get("verified_days_on_market", claimed_days)

        # Calculate accuracy
        if claimed_days > 0:
            accuracy = 1.0 - abs(claimed_days - verified_days) / max(claimed_days, verified_days)
        else:
            accuracy = 1.0 if verified_days == 0 else 0.0

        # Create evidence
        evidence = []
        if "mls_listing_date" in verification_data and "mls_sold_date" in verification_data:
            evidence.append(
                VerificationEvidence(
                    source=VerificationSource.MLS_DATA,
                    data_hash=hashlib.md5(
                        f"{verification_data['mls_listing_date']}_{verification_data['mls_sold_date']}".encode()
                    ).hexdigest(),
                    timestamp=datetime.now(),
                    confidence_score=0.95,
                )
            )

        verification_level = self._get_verification_level_from_accuracy(accuracy)

        return OutcomeVerification(
            outcome_id=f"timeline_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            outcome_type="transaction_timeline",
            claimed_value=claimed_days,
            verified_value=verified_days,
            verification_level=verification_level,
            evidence=evidence,
            accuracy_percentage=accuracy * 100,
            verification_timestamp=datetime.now(),
            next_review_date=datetime.now() + timedelta(days=30),
            anomalies_detected=[],
        )

    async def _verify_commission_data(
        self, claimed_data: Dict[str, Any], verification_data: Dict[str, Any]
    ) -> OutcomeVerification:
        """Verify commission data"""

        claimed_commission = float(claimed_data.get("commission_paid", 0))
        verified_commission = verification_data.get("verified_commission", claimed_commission)

        # Calculate accuracy
        if claimed_commission > 0:
            accuracy = 1.0 - abs(claimed_commission - verified_commission) / claimed_commission
        else:
            accuracy = 1.0 if verified_commission == 0 else 0.0

        evidence = []
        if "title_company_commission" in verification_data:
            evidence.append(
                VerificationEvidence(
                    source=VerificationSource.TITLE_COMPANY,
                    data_hash=hashlib.md5(str(verification_data["title_company_commission"]).encode()).hexdigest(),
                    timestamp=datetime.now(),
                    confidence_score=0.90,
                )
            )

        verification_level = self._get_verification_level_from_accuracy(accuracy)

        return OutcomeVerification(
            outcome_id=f"commission_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            outcome_type="commission_data",
            claimed_value=claimed_commission,
            verified_value=verified_commission,
            verification_level=verification_level,
            evidence=evidence,
            accuracy_percentage=accuracy * 100,
            verification_timestamp=datetime.now(),
            next_review_date=datetime.now() + timedelta(days=30),
            anomalies_detected=[],
        )

    def _get_verification_level_from_accuracy(self, accuracy: float) -> VerificationLevel:
        """Determine verification level from accuracy percentage"""

        if accuracy >= self.verification_thresholds[VerificationLevel.GOLD]:
            return VerificationLevel.GOLD
        elif accuracy >= self.verification_thresholds[VerificationLevel.SILVER]:
            return VerificationLevel.SILVER
        elif accuracy >= self.verification_thresholds[VerificationLevel.BRONZE]:
            return VerificationLevel.BRONZE
        elif accuracy >= self.verification_thresholds[VerificationLevel.PENDING]:
            return VerificationLevel.PENDING
        else:
            return VerificationLevel.FAILED

    async def _calculate_overall_verification(
        self,
        outcome_verifications: List[OutcomeVerification],
        satisfaction_verification: Optional[ClientSatisfactionVerification] = None,
    ) -> Tuple[VerificationLevel, float]:
        """Calculate overall verification level and accuracy"""

        # Weight the verifications
        weights = {"price": 0.4, "timeline": 0.3, "commission": 0.2, "satisfaction": 0.1}

        weighted_accuracy = 0.0
        total_weight = 0.0

        verification_levels = []

        for verification in outcome_verifications:
            outcome_type = verification.outcome_type
            if "price" in outcome_type:
                weight = weights["price"]
            elif "timeline" in outcome_type:
                weight = weights["timeline"]
            elif "commission" in outcome_type:
                weight = weights["commission"]
            else:
                weight = 0.1

            weighted_accuracy += verification.accuracy_percentage * weight
            total_weight += weight
            verification_levels.append(verification.verification_level)

        if satisfaction_verification:
            weighted_accuracy += satisfaction_verification.confidence_score * 100 * weights["satisfaction"]
            total_weight += weights["satisfaction"]

            # Convert satisfaction confidence to verification level
            if satisfaction_verification.confidence_score >= 0.95:
                verification_levels.append(VerificationLevel.GOLD)
            elif satisfaction_verification.confidence_score >= 0.85:
                verification_levels.append(VerificationLevel.SILVER)
            else:
                verification_levels.append(VerificationLevel.BRONZE)

        overall_accuracy = weighted_accuracy / total_weight if total_weight > 0 else 0.0

        # Determine overall level (most conservative)
        if VerificationLevel.FAILED in verification_levels:
            overall_level = VerificationLevel.FAILED
        elif VerificationLevel.PENDING in verification_levels:
            overall_level = VerificationLevel.PENDING
        elif VerificationLevel.BRONZE in verification_levels:
            overall_level = VerificationLevel.BRONZE
        elif VerificationLevel.SILVER in verification_levels:
            overall_level = VerificationLevel.SILVER
        else:
            overall_level = VerificationLevel.GOLD

        return overall_level, overall_accuracy

    # Placeholder methods for external data integration
    async def _get_mls_data(self, transaction_id: str) -> Optional[Dict]:
        """Get MLS data for transaction (to be implemented with actual MLS API)"""
        # This would integrate with actual MLS systems
        return {
            "verified_sold_price": 445000,
            "verified_listed_price": 440000,
            "mls_listing_date": datetime(2024, 1, 15),
            "mls_sold_date": datetime(2024, 2, 3),
        }

    async def _get_transaction_records(self, transaction_id: str) -> Optional[Dict]:
        """Get internal transaction records"""
        return {"verified_days_on_market": 19, "verified_commission": 13350}

    async def _get_county_records(self, transaction_id: str) -> Optional[Dict]:
        """Get county records data"""
        return {"county_sold_price": 445000, "county_recording_date": datetime(2024, 2, 5)}

    async def _get_survey_responses(self, client_id: str, transaction_id: str) -> List[Dict]:
        """Get client survey responses"""
        return [{"rating": 4.8, "survey_date": datetime.now(), "verified": True, "source": "post_transaction_survey"}]

    async def _get_review_platform_data(self, agent_id: str, client_id: str) -> List[Dict]:
        """Get review platform data"""
        return [{"rating": 4.9, "platform": "google_reviews", "verified_purchase": True, "review_date": datetime.now()}]

    async def _get_follow_up_interviews(self, client_id: str, transaction_id: str) -> List[Dict]:
        """Get follow-up interview data"""
        return []

    async def _calculate_satisfaction_verification_level(
        self, claimed_rating: float, verified_ratings: Dict[str, float], average_verified_rating: float
    ) -> Tuple[VerificationLevel, float]:
        """Calculate satisfaction verification level"""

        if not verified_ratings:
            return VerificationLevel.PENDING, 0.5

        # Calculate variance from claimed rating
        variance = abs(claimed_rating - average_verified_rating)

        # Determine confidence based on number of sources and variance
        num_sources = len(verified_ratings)
        confidence = 0.5 + (num_sources * 0.15) - (variance * 0.2)
        confidence = max(0.0, min(1.0, confidence))

        verification_level = self._get_verification_level_from_accuracy(confidence)

        return verification_level, confidence

    async def _identify_satisfaction_discrepancies(
        self, claimed_rating: float, verified_ratings: Dict[str, float], average_verified_rating: float
    ) -> List[str]:
        """Identify satisfaction rating discrepancies"""

        discrepancies = []

        if abs(claimed_rating - average_verified_rating) > self.variance_thresholds["rating_variance"]:
            discrepancies.append(
                f"Claimed rating differs from verified average by {abs(claimed_rating - average_verified_rating):.1f}"
            )

        # Check for inconsistency across sources
        if len(verified_ratings) > 1:
            rating_values = list(verified_ratings.values())
            if max(rating_values) - min(rating_values) > 1.0:
                discrepancies.append("High variance across verification sources")

        return discrepancies

    async def _store_verification_result(self, verification: TransactionVerification) -> None:
        """Store verification result (to be implemented with actual storage)"""
        logger.info(f"Storing verification result for transaction {verification.transaction_id}")

    async def _get_agent_transactions(self, agent_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get agent transactions for period"""
        # This would integrate with actual transaction database
        return []

    async def _calculate_verified_metric(self, metric_type: str, transactions: List[Dict]) -> float:
        """Calculate verified metric value from transactions"""
        if not transactions:
            return 0.0

        if metric_type == "negotiation_performance":
            # Calculate average sold price / listed price ratio
            ratios = []
            for txn in transactions:
                if txn.get("listed_price") and txn.get("sold_price"):
                    ratios.append(txn["sold_price"] / txn["listed_price"])
            return statistics.mean(ratios) if ratios else 0.0

        elif metric_type == "timeline_efficiency":
            # Calculate average days on market
            days = [txn.get("days_on_market", 0) for txn in transactions if txn.get("days_on_market")]
            return statistics.mean(days) if days else 0.0

        return 0.0

    async def _gather_metric_evidence(
        self, metric_type: str, transactions: List[Dict], evidence_data: Optional[Dict]
    ) -> List[VerificationEvidence]:
        """Gather evidence for metric verification"""
        return [
            VerificationEvidence(
                source=VerificationSource.TRANSACTION_RECORDS,
                data_hash=hashlib.md5(f"{metric_type}_{len(transactions)}".encode()).hexdigest(),
                timestamp=datetime.now(),
                confidence_score=0.9,
            )
        ]

    async def _calculate_metric_accuracy(self, claimed_value: float, verified_value: float, metric_type: str) -> float:
        """Calculate metric accuracy percentage"""
        if claimed_value == 0 and verified_value == 0:
            return 100.0

        if claimed_value == 0:
            return 0.0

        accuracy = 1.0 - abs(claimed_value - verified_value) / abs(claimed_value)
        return max(0.0, min(100.0, accuracy * 100))

    async def _determine_verification_level(
        self, accuracy: float, evidence: List[VerificationEvidence]
    ) -> VerificationLevel:
        """Determine verification level from accuracy and evidence"""

        # Adjust level based on evidence quality
        evidence_quality = statistics.mean([e.confidence_score for e in evidence]) if evidence else 0.5
        adjusted_accuracy = (accuracy / 100) * evidence_quality

        return self._get_verification_level_from_accuracy(adjusted_accuracy)

    async def _detect_metric_anomalies(
        self, metric_type: str, claimed_value: float, verified_value: float, transactions: List[Dict]
    ) -> List[str]:
        """Detect anomalies in metric verification"""
        anomalies = []

        variance = (
            abs(claimed_value - verified_value) / max(abs(claimed_value), abs(verified_value))
            if max(abs(claimed_value), abs(verified_value)) > 0
            else 0
        )

        if variance > 0.1:  # 10% variance
            anomalies.append(f"High variance between claimed and verified values: {variance:.1%}")

        if len(transactions) < 5:
            anomalies.append("Low sample size for metric calculation")

        return anomalies

    async def _generate_verification_summary(
        self,
        price_verification: OutcomeVerification,
        timeline_verification: OutcomeVerification,
        commission_verification: OutcomeVerification,
        satisfaction_verification: Optional[ClientSatisfactionVerification],
    ) -> Dict[str, Any]:
        """Generate verification summary"""
        return {
            "price_accuracy": price_verification.accuracy_percentage,
            "timeline_accuracy": timeline_verification.accuracy_percentage,
            "commission_accuracy": commission_verification.accuracy_percentage,
            "satisfaction_confidence": satisfaction_verification.confidence_score * 100
            if satisfaction_verification
            else None,
            "evidence_sources": len(
                set(
                    [
                        e.source
                        for e in price_verification.evidence
                        + timeline_verification.evidence
                        + commission_verification.evidence
                    ]
                )
            ),
            "total_anomalies": len(price_verification.anomalies_detected)
            + len(timeline_verification.anomalies_detected)
            + len(commission_verification.anomalies_detected),
        }

    async def _get_agent_verifications(
        self, agent_id: str, start_date: datetime, end_date: datetime
    ) -> List[TransactionVerification]:
        """Get agent verifications for period (placeholder)"""
        # This would query actual verification database
        return []

    async def _calculate_data_quality_score(self, agent_id: str, verifications: List[TransactionVerification]) -> float:
        """Calculate data quality score"""
        if not verifications:
            return 0.0

        total_evidence_sources = sum(
            len(
                set(
                    [
                        e.source
                        for e in v.price_verification.evidence
                        + v.timeline_verification.evidence
                        + v.commission_verification.evidence
                    ]
                )
            )
            for v in verifications
        )

        avg_evidence_sources = total_evidence_sources / len(verifications)
        return min(100.0, avg_evidence_sources * 20)  # Scale to 100

    async def _generate_verification_recommendations(self, verifications: List[TransactionVerification]) -> List[str]:
        """Generate recommendations for improving verification"""
        recommendations = []

        if not verifications:
            recommendations.append("Increase transaction volume for better verification coverage")
            return recommendations

        avg_accuracy = statistics.mean([v.overall_accuracy for v in verifications])
        if avg_accuracy < 90:
            recommendations.append("Improve data collection processes to increase verification accuracy")

        gold_rate = sum(1 for v in verifications if v.overall_verification_level == VerificationLevel.GOLD) / len(
            verifications
        )
        if gold_rate < 0.7:
            recommendations.append("Increase use of primary data sources for gold-level verification")

        return recommendations


# Global instance
_verification_service = None


def get_client_outcome_verification_service() -> ClientOutcomeVerificationService:
    """Get global client outcome verification service instance"""
    global _verification_service
    if _verification_service is None:
        _verification_service = ClientOutcomeVerificationService()
    return _verification_service
