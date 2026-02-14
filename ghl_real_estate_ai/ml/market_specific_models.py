#!/usr/bin/env python3
"""
🎯 Market-Specific Conversion Models
===================================

Specialized ML models for different market segments with optimized
conversion prediction algorithms tailored to specific buyer personas.

Market Segments:
- Tech Hub (Rancho Cucamonga, Seattle, San Francisco) - Tech professionals
- Energy Sector (Houston, Dallas) - Oil & gas professionals
- Military Market (San Antonio, Norfolk) - Military personnel
- Luxury Residential (High-end buyers)
- Investment Focused (Real estate investors)
- First-Time Buyers (Entry-level market)

Features:
- Segment-specific feature engineering
- Custom scoring algorithms per market
- Dynamic model selection
- Performance monitoring per segment
- A/B testing framework

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ai_predictive_lead_scoring import LeadScore

logger = get_logger(__name__)


class MarketSegment(Enum):
    """Market segment types"""

    TECH_HUB = "tech_hub"
    ENERGY_SECTOR = "energy_sector"
    MILITARY_MARKET = "military_market"
    LUXURY_RESIDENTIAL = "luxury_residential"
    FIRST_TIME_BUYERS = "first_time_buyers"
    INVESTMENT_FOCUSED = "investment_focused"
    GENERAL_MARKET = "general_market"


@dataclass
class MarketMetrics:
    """Market-specific performance metrics"""

    segment: MarketSegment
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_score: float
    sample_size: int
    last_updated: datetime
    conversion_rate: float
    avg_deal_size: float
    avg_days_to_close: int


@dataclass
class SegmentProfile:
    """Segment characteristics and behavior patterns"""

    segment: MarketSegment
    typical_budget_range: Tuple[int, int]
    common_keywords: List[str]
    decision_timeline: str  # fast/medium/slow
    preferred_communication: List[str]
    key_motivators: List[str]
    common_objections: List[str]
    conversion_probability_boost: float


class BaseMarketModel(ABC):
    """Abstract base class for market-specific models"""

    def __init__(self, segment: MarketSegment):
        self.segment = segment
        self.model_version = "1.0"
        self.last_training_date = None
        self.feature_importance = {}

    @abstractmethod
    def predict(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> LeadScore:
        """Predict lead score for this market segment"""
        pass

    @abstractmethod
    def get_segment_features(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> Dict[str, float]:
        """Extract segment-specific features"""
        pass


class TechHubModel(BaseMarketModel):
    """Model optimized for tech professionals"""

    def __init__(self):
        super().__init__(MarketSegment.TECH_HUB)
        self.tech_companies = [
            "apple",
            "google",
            "microsoft",
            "amazon",
            "meta",
            "tesla",
            "nvidia",
            "salesforce",
            "adobe",
            "uber",
            "airbnb",
        ]
        self.tech_keywords = [
            "engineer",
            "developer",
            "programmer",
            "architect",
            "manager",
            "startup",
            "ipo",
            "stock options",
            "remote work",
            "commute",
        ]

    def get_segment_features(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> Dict[str, float]:
        """Extract tech-specific features"""
        features = {}

        all_text = str(lead_data).lower()
        conversation_text = " ".join([str(msg) for msg in lead_data.get("messages", [])]).lower()

        # Tech company association
        tech_company_mentions = sum(1 for company in self.tech_companies if company in all_text)
        features["tech_company_association"] = min(tech_company_mentions / 3.0, 1.0)

        # Tech role indicators
        tech_role_mentions = sum(1 for keyword in self.tech_keywords if keyword in all_text)
        features["tech_role_indicators"] = min(tech_role_mentions / 5.0, 1.0)

        # Equity/stock options mentions (high income potential)
        equity_indicators = ["stock options", "rsu", "vesting", "equity", "ipo", "shares"]
        features["equity_compensation"] = float(any(indicator in conversation_text for indicator in equity_indicators))

        # Work-from-home setup mentions
        wfh_indicators = ["home office", "work from home", "remote work", "office space"]
        features["wfh_requirements"] = float(any(indicator in conversation_text for indicator in wfh_indicators))

        # Tech hub location preferences
        tech_locations = ["rancho_cucamonga", "seattle", "san francisco", "palo alto", "cupertino"]
        features["tech_location_preference"] = float(any(location in all_text for location in tech_locations))

        # High-speed internet requirements
        internet_indicators = ["fiber", "gigabit", "high speed internet", "bandwidth"]
        features["high_speed_internet_needs"] = float(
            any(indicator in conversation_text for indicator in internet_indicators)
        )

        # Commute optimization focus
        commute_indicators = ["commute", "drive time", "traffic", "transportation", "bart", "metro"]
        features["commute_focus"] = float(any(indicator in conversation_text for indicator in commute_indicators))

        return features

    def predict(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> LeadScore:
        """Tech hub specific prediction logic"""
        # Get segment features
        segment_features = self.get_segment_features(lead_data, behavioral_signals)

        # Tech-specific scoring weights
        tech_score = 0.0

        # High value signals for tech professionals
        tech_score += segment_features.get("tech_company_association", 0) * 15
        tech_score += segment_features.get("tech_role_indicators", 0) * 10
        tech_score += segment_features.get("equity_compensation", 0) * 20
        tech_score += segment_features.get("wfh_requirements", 0) * 8
        tech_score += segment_features.get("tech_location_preference", 0) * 12
        tech_score += segment_features.get("commute_focus", 0) * 10

        # Standard behavioral signals with tech-specific weights
        tech_score += behavioral_signals.get("response_velocity", 0) * 15
        tech_score += behavioral_signals.get("digital_engagement", 0) * 12
        tech_score += behavioral_signals.get("technical_language_usage", 0) * 10
        tech_score += behavioral_signals.get("detail_oriented", 0) * 8

        # Budget considerations (tech professionals often have higher budgets)
        budget = lead_data.get("budget", 0)
        if budget > 800000:  # High budget boost
            tech_score += 15
        elif budget > 600000:
            tech_score += 10

        # Timeline considerations (tech moves are often job-driven = urgent)
        if behavioral_signals.get("relocation_pressure", 0) > 0.5:
            tech_score += 12

        # Final normalization and confidence
        normalized_score = min(tech_score, 100.0)
        confidence = 0.85 if segment_features.get("tech_company_association", 0) > 0.5 else 0.7

        # Assign tier
        tier = "hot" if normalized_score >= 75 else "warm" if normalized_score >= 50 else "cold"

        # Generate recommendations
        recommendations = self._generate_tech_recommendations(segment_features, behavioral_signals)

        return LeadScore(
            lead_id=lead_data.get("lead_id", "unknown"),
            score=normalized_score,
            confidence=confidence,
            tier=tier,
            factors=[
                {
                    "name": "Tech Industry Association",
                    "impact": segment_features.get("tech_company_association", 0) * 15,
                    "value": f"{int(segment_features.get('tech_company_association', 0) * 100)}% tech signals",
                },
                {
                    "name": "Equity Compensation",
                    "impact": segment_features.get("equity_compensation", 0) * 20,
                    "value": "Stock options mentioned"
                    if segment_features.get("equity_compensation", 0) > 0
                    else "Not mentioned",
                },
                {
                    "name": "Digital Engagement",
                    "impact": behavioral_signals.get("digital_engagement", 0) * 12,
                    "value": f"{int(behavioral_signals.get('digital_engagement', 0) * 100)}% engagement",
                },
            ],
            recommendations=recommendations,
            scored_at=datetime.now(),
        )

    def _generate_tech_recommendations(
        self, segment_features: Dict[str, float], behavioral_signals: Dict[str, float]
    ) -> List[str]:
        """Generate tech-specific recommendations"""
        recommendations = []

        if segment_features.get("wfh_requirements", 0) > 0:
            recommendations.append("Highlight home office spaces and fiber internet availability")

        if segment_features.get("commute_focus", 0) > 0:
            recommendations.append("Provide detailed commute analysis to major tech campuses")

        if segment_features.get("equity_compensation", 0) > 0:
            recommendations.append("Discuss property as investment vehicle for equity gains")

        if behavioral_signals.get("digital_engagement", 0) > 0.7:
            recommendations.append("Provide virtual tours and detailed online property data")

        if not recommendations:
            recommendations.append("Focus on tech-friendly amenities and location benefits")

        return recommendations


class EnergySectorModel(BaseMarketModel):
    """Model optimized for energy sector professionals"""

    def __init__(self):
        super().__init__(MarketSegment.ENERGY_SECTOR)
        self.energy_companies = [
            "exxon",
            "chevron",
            "bp",
            "shell",
            "conocophillips",
            "marathon",
            "valero",
            "phillips 66",
            "halliburton",
            "schlumberger",
        ]
        self.energy_keywords = [
            "oil",
            "gas",
            "petroleum",
            "refinery",
            "drilling",
            "pipeline",
            "upstream",
            "downstream",
            "geologist",
            "engineer",
        ]

    def get_segment_features(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> Dict[str, float]:
        """Extract energy sector specific features"""
        features = {}

        all_text = str(lead_data).lower()

        # Energy company association
        energy_company_mentions = sum(1 for company in self.energy_companies if company in all_text)
        features["energy_company_association"] = min(energy_company_mentions / 2.0, 1.0)

        # Industry keywords
        energy_keyword_mentions = sum(1 for keyword in self.energy_keywords if keyword in all_text)
        features["energy_industry_indicators"] = min(energy_keyword_mentions / 4.0, 1.0)

        # Cyclical employment awareness (energy sector volatility)
        stability_indicators = ["stable job", "permanent position", "contract work", "layoffs"]
        features["employment_stability_awareness"] = float(
            any(indicator in all_text for indicator in stability_indicators)
        )

        # Location proximity to energy hubs
        energy_locations = ["houston", "dallas", "midland", "corpus christi", "beaumont"]
        features["energy_hub_proximity"] = float(any(location in all_text for location in energy_locations))

        return features

    def predict(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> LeadScore:
        """Energy sector specific prediction"""
        segment_features = self.get_segment_features(lead_data, behavioral_signals)

        energy_score = 0.0

        # Energy-specific scoring
        energy_score += segment_features.get("energy_company_association", 0) * 18
        energy_score += segment_features.get("energy_industry_indicators", 0) * 12
        energy_score += segment_features.get("energy_hub_proximity", 0) * 10

        # Financial stability considerations
        if behavioral_signals.get("preapproval_mentions", 0) > 0:
            energy_score += 15  # Important for cyclical industry

        # Standard signals with energy-specific weights
        energy_score += behavioral_signals.get("cash_buyer_indicators", 0) * 20  # Common in energy
        energy_score += behavioral_signals.get("budget_specificity", 0) * 12

        # Timeline considerations
        energy_score += behavioral_signals.get("immediate_timeline", 0) * 15

        normalized_score = min(energy_score, 100.0)
        confidence = 0.8 if segment_features.get("energy_company_association", 0) > 0.5 else 0.65

        tier = "hot" if normalized_score >= 75 else "warm" if normalized_score >= 50 else "cold"

        return LeadScore(
            lead_id=lead_data.get("lead_id", "unknown"),
            score=normalized_score,
            confidence=confidence,
            tier=tier,
            factors=[
                {
                    "name": "Energy Industry Connection",
                    "impact": segment_features.get("energy_company_association", 0) * 18,
                    "value": f"{int(segment_features.get('energy_company_association', 0) * 100)}% industry signals",
                },
                {
                    "name": "Cash Buyer Potential",
                    "impact": behavioral_signals.get("cash_buyer_indicators", 0) * 20,
                    "value": "Cash purchase mentioned"
                    if behavioral_signals.get("cash_buyer_indicators", 0) > 0
                    else "Financing likely",
                },
            ],
            recommendations=self._generate_energy_recommendations(segment_features, behavioral_signals),
            scored_at=datetime.now(),
        )

    def _generate_energy_recommendations(
        self, segment_features: Dict[str, float], behavioral_signals: Dict[str, float]
    ) -> List[str]:
        """Generate energy sector recommendations"""
        recommendations = []

        if segment_features.get("energy_hub_proximity", 0) > 0:
            recommendations.append("Emphasize proximity to major energy facilities and infrastructure")

        if behavioral_signals.get("cash_buyer_indicators", 0) > 0:
            recommendations.append("Fast-track process for cash purchase capability")

        recommendations.append("Discuss property as stable asset during industry cycles")
        return recommendations


class MilitaryMarketModel(BaseMarketModel):
    """Model optimized for military personnel and families"""

    def __init__(self):
        super().__init__(MarketSegment.MILITARY_MARKET)
        self.military_keywords = [
            "military",
            "army",
            "navy",
            "air force",
            "marines",
            "coast guard",
            "veteran",
            "active duty",
            "deployment",
            "pcs",
            "base",
            "fort",
        ]

    def get_segment_features(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> Dict[str, float]:
        """Extract military-specific features"""
        features = {}

        all_text = str(lead_data).lower()

        # Military affiliation
        military_mentions = sum(1 for keyword in self.military_keywords if keyword in all_text)
        features["military_affiliation"] = min(military_mentions / 3.0, 1.0)

        # VA loan indicators
        va_indicators = ["va loan", "va mortgage", "va benefit", "veterans affairs"]
        features["va_loan_eligible"] = float(any(indicator in all_text for indicator in va_indicators))

        # PCS (Permanent Change of Station) indicators
        pcs_indicators = ["pcs", "transfer", "new orders", "reassignment", "deployment"]
        features["pcs_timeline"] = float(any(indicator in all_text for indicator in pcs_indicators))

        # Base proximity requirements
        base_indicators = ["base", "fort", "naval station", "air force base"]
        features["base_proximity_needs"] = float(any(indicator in all_text for indicator in base_indicators))

        return features

    def predict(self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float]) -> LeadScore:
        """Military market specific prediction"""
        segment_features = self.get_segment_features(lead_data, behavioral_signals)

        military_score = 0.0

        # Military-specific scoring
        military_score += segment_features.get("military_affiliation", 0) * 20
        military_score += segment_features.get("va_loan_eligible", 0) * 18
        military_score += segment_features.get("pcs_timeline", 0) * 15
        military_score += segment_features.get("base_proximity_needs", 0) * 12

        # Family considerations (military families often prioritize stability)
        if behavioral_signals.get("family_oriented", 0) > 0.5:
            military_score += 10

        # Timeline urgency (PCS moves are date-driven)
        military_score += behavioral_signals.get("immediate_timeline", 0) * 18

        normalized_score = min(military_score, 100.0)
        confidence = 0.9 if segment_features.get("military_affiliation", 0) > 0.5 else 0.6

        tier = "hot" if normalized_score >= 70 else "warm" if normalized_score >= 45 else "cold"

        return LeadScore(
            lead_id=lead_data.get("lead_id", "unknown"),
            score=normalized_score,
            confidence=confidence,
            tier=tier,
            factors=[
                {
                    "name": "Military Affiliation",
                    "impact": segment_features.get("military_affiliation", 0) * 20,
                    "value": f"{int(segment_features.get('military_affiliation', 0) * 100)}% military signals",
                },
                {
                    "name": "VA Loan Eligibility",
                    "impact": segment_features.get("va_loan_eligible", 0) * 18,
                    "value": "VA loan mentioned"
                    if segment_features.get("va_loan_eligible", 0) > 0
                    else "Not mentioned",
                },
            ],
            recommendations=self._generate_military_recommendations(segment_features, behavioral_signals),
            scored_at=datetime.now(),
        )

    def _generate_military_recommendations(
        self, segment_features: Dict[str, float], behavioral_signals: Dict[str, float]
    ) -> List[str]:
        """Generate military-specific recommendations"""
        recommendations = []

        if segment_features.get("va_loan_eligible", 0) > 0:
            recommendations.append("Emphasize VA loan benefits and no down payment options")

        if segment_features.get("pcs_timeline", 0) > 0:
            recommendations.append("Expedite process for PCS timeline requirements")

        if segment_features.get("base_proximity_needs", 0) > 0:
            recommendations.append("Highlight proximity to military installations and amenities")

        recommendations.append("Focus on family-friendly neighborhoods and schools")
        return recommendations


class MarketSpecificModelRouter:
    """Router for market-specific models with performance monitoring"""

    def __init__(self):
        self.models = {
            MarketSegment.TECH_HUB: TechHubModel(),
            MarketSegment.ENERGY_SECTOR: EnergySectorModel(),
            MarketSegment.MILITARY_MARKET: MilitaryMarketModel(),
        }

        # Segment profiles for characterization
        self.segment_profiles = self._initialize_segment_profiles()

        # Performance tracking
        self.performance_metrics = {}
        self._initialize_metrics()

        logger.info(f"MarketSpecificModelRouter initialized with {len(self.models)} specialized models")

    def predict(
        self, lead_data: Dict[str, Any], behavioral_signals: Dict[str, float], market_segment: MarketSegment
    ) -> Optional[LeadScore]:
        """Route prediction to appropriate market-specific model"""
        try:
            if market_segment in self.models:
                model = self.models[market_segment]
                result = model.predict(lead_data, behavioral_signals)

                # Apply segment-specific boost
                profile = self.segment_profiles.get(market_segment)
                if profile and profile.conversion_probability_boost != 1.0:
                    result.score *= profile.conversion_probability_boost
                    result.score = min(result.score, 100.0)

                return result
            else:
                logger.warning(f"No specialized model available for {market_segment}")
                return None

        except Exception as e:
            logger.error(f"Model prediction failed for {market_segment}: {e}")
            return None

    def get_model_version(self, segment: MarketSegment) -> str:
        """Get model version for a segment"""
        if segment in self.models:
            return self.models[segment].model_version
        return "unknown"

    def get_segment_profile(self, segment: MarketSegment) -> Optional[SegmentProfile]:
        """Get segment profile information"""
        return self.segment_profiles.get(segment)

    def get_performance_metrics(self, segment: MarketSegment) -> Optional[MarketMetrics]:
        """Get performance metrics for a segment"""
        return self.performance_metrics.get(segment)

    def _initialize_segment_profiles(self) -> Dict[MarketSegment, SegmentProfile]:
        """Initialize segment profiles"""
        return {
            MarketSegment.TECH_HUB: SegmentProfile(
                segment=MarketSegment.TECH_HUB,
                typical_budget_range=(600000, 1500000),
                common_keywords=["tech", "engineer", "startup", "remote work"],
                decision_timeline="fast",
                preferred_communication=["email", "text", "video"],
                key_motivators=["commute", "home office", "investment potential"],
                common_objections=["market volatility", "overpriced market"],
                conversion_probability_boost=1.15,
            ),
            MarketSegment.ENERGY_SECTOR: SegmentProfile(
                segment=MarketSegment.ENERGY_SECTOR,
                typical_budget_range=(400000, 1000000),
                common_keywords=["oil", "gas", "energy", "petroleum"],
                decision_timeline="medium",
                preferred_communication=["phone", "in-person"],
                key_motivators=["stability", "investment", "location"],
                common_objections=["job security", "market cycles"],
                conversion_probability_boost=1.05,
            ),
            MarketSegment.MILITARY_MARKET: SegmentProfile(
                segment=MarketSegment.MILITARY_MARKET,
                typical_budget_range=(200000, 600000),
                common_keywords=["military", "veteran", "va loan", "base"],
                decision_timeline="fast",
                preferred_communication=["phone", "email"],
                key_motivators=["va benefits", "family", "base proximity"],
                common_objections=["deployment", "transfer timeline"],
                conversion_probability_boost=1.20,
            ),
        }

    def _initialize_metrics(self):
        """Initialize performance metrics tracking"""
        for segment in self.models.keys():
            self.performance_metrics[segment] = MarketMetrics(
                segment=segment,
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                auc_score=0.0,
                sample_size=0,
                last_updated=datetime.now(),
                conversion_rate=0.0,
                avg_deal_size=0.0,
                avg_days_to_close=0,
            )


# Factory function for easy model access
def get_market_specific_model(segment: MarketSegment) -> Optional[BaseMarketModel]:
    """Get a market-specific model instance"""
    router = MarketSpecificModelRouter()
    return router.models.get(segment)


# Example usage
if __name__ == "__main__":
    # Initialize router
    router = MarketSpecificModelRouter()

    # Sample tech hub lead
    tech_lead_data = {
        "lead_id": "tech_123",
        "budget": 750000,
        "location": "Rancho Cucamonga, CA",
        "messages": [
            {"text": "I'm a software engineer at Apple looking for a home with a good home office setup"},
            {"text": "My stock options vest next month, so I can put down 20%"},
        ],
    }

    behavioral_signals = {
        "digital_engagement": 0.9,
        "response_velocity": 0.8,
        "technical_language_usage": 0.7,
        "equity_compensation": 1.0,
    }

    # Predict using tech hub model
    result = router.predict(tech_lead_data, behavioral_signals, MarketSegment.TECH_HUB)

    if result:
        print(f"Tech Hub Lead Score: {result.score:.1f}")
        print(f"Tier: {result.tier}")
        print(f"Confidence: {result.confidence:.2f}")
        print("Recommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")
