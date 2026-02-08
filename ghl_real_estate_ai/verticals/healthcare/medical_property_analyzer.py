"""
Medical Property Analyzer

AI-powered analysis engine for healthcare real estate properties.
Provides specialized insights for medical practices, hospitals, and healthcare facilities.

Key Features:
- Medical facility suitability scoring
- Healthcare market analysis
- Patient accessibility evaluation
- Regulatory compliance assessment
- Healthcare-specific ROI calculations
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...core.llm_client import LLMClient
from ...services.cache_service import CacheService

logger = logging.getLogger(__name__)


@dataclass
class HealthcareProperty:
    """Healthcare-specific property data structure."""

    property_id: str
    address: str
    square_footage: int
    property_type: str  # medical_office, hospital, clinic, etc.
    parking_spaces: int
    ada_compliant: bool
    medical_gas_systems: bool
    backup_power: bool
    laboratory_space: bool
    imaging_capability: bool
    surgery_suites: int
    patient_rooms: int
    waiting_area_sqft: int
    proximity_to_hospital: float  # miles
    public_transit_score: int  # 1-10
    demographics: Dict[str, Any]


@dataclass
class HealthcareAnalysis:
    """Healthcare property analysis results."""

    overall_score: float  # 0-100
    facility_suitability: float
    market_opportunity: float
    patient_accessibility: float
    regulatory_compliance: float
    financial_viability: float
    recommendations: List[str]
    risk_factors: List[str]
    target_specialties: List[str]
    estimated_revenue_potential: int


class MedicalPropertyAnalyzer:
    """
    Advanced AI analyzer for healthcare real estate properties.

    Leverages Claude AI for sophisticated healthcare market intelligence
    and property suitability assessment for medical practices.
    """

    def __init__(self):
        self.llm_client = LLMClient()
        self.cache = CacheService()

        # Healthcare-specific analysis weights
        self.analysis_weights = {
            "facility_suitability": 0.25,
            "market_opportunity": 0.25,
            "patient_accessibility": 0.20,
            "regulatory_compliance": 0.15,
            "financial_viability": 0.15,
        }

        # Medical specialty requirements
        self.specialty_requirements = {
            "primary_care": {
                "min_sqft": 2000,
                "exam_rooms": 6,
                "parking_ratio": 4.5,
                "imaging_required": False,
                "lab_required": True,
            },
            "cardiology": {
                "min_sqft": 3500,
                "exam_rooms": 8,
                "parking_ratio": 5.0,
                "imaging_required": True,
                "lab_required": True,
                "stress_test_capability": True,
            },
            "orthopedics": {
                "min_sqft": 4000,
                "exam_rooms": 10,
                "parking_ratio": 6.0,
                "imaging_required": True,
                "lab_required": False,
                "physical_therapy_space": True,
            },
            "urgent_care": {
                "min_sqft": 2500,
                "exam_rooms": 8,
                "parking_ratio": 8.0,
                "imaging_required": True,
                "lab_required": True,
                "24_7_access": True,
            },
        }

    async def analyze_healthcare_property(
        self, property_data: HealthcareProperty, target_specialties: Optional[List[str]] = None
    ) -> HealthcareAnalysis:
        """
        Perform comprehensive healthcare property analysis.

        Args:
            property_data: Healthcare property information
            target_specialties: Specific medical specialties to analyze for

        Returns:
            Detailed healthcare analysis results
        """
        try:
            # Check cache first
            cache_key = f"healthcare_analysis:{property_data.property_id}:{hash(str(target_specialties))}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                return HealthcareAnalysis(**cached_result)

            logger.info(f"Analyzing healthcare property: {property_data.property_id}")

            # Perform parallel analysis components
            analysis_tasks = [
                self._analyze_facility_suitability(property_data, target_specialties),
                self._analyze_market_opportunity(property_data),
                self._analyze_patient_accessibility(property_data),
                self._analyze_regulatory_compliance(property_data),
                self._analyze_financial_viability(property_data, target_specialties),
            ]

            results = await asyncio.gather(*analysis_tasks)

            facility_score, facility_recommendations = results[0]
            market_score, market_insights = results[1]
            accessibility_score, accessibility_factors = results[2]
            compliance_score, compliance_issues = results[3]
            financial_score, revenue_potential = results[4]

            # Calculate weighted overall score
            overall_score = (
                facility_score * self.analysis_weights["facility_suitability"]
                + market_score * self.analysis_weights["market_opportunity"]
                + accessibility_score * self.analysis_weights["patient_accessibility"]
                + compliance_score * self.analysis_weights["regulatory_compliance"]
                + financial_score * self.analysis_weights["financial_viability"]
            )

            # Generate AI-powered strategic recommendations
            strategic_analysis = await self._generate_strategic_recommendations(
                property_data, overall_score, target_specialties
            )

            analysis_result = HealthcareAnalysis(
                overall_score=overall_score,
                facility_suitability=facility_score,
                market_opportunity=market_score,
                patient_accessibility=accessibility_score,
                regulatory_compliance=compliance_score,
                financial_viability=financial_score,
                recommendations=facility_recommendations + strategic_analysis["recommendations"],
                risk_factors=compliance_issues + strategic_analysis["risks"],
                target_specialties=strategic_analysis["optimal_specialties"],
                estimated_revenue_potential=revenue_potential,
            )

            # Cache results for 24 hours
            await self.cache.set(cache_key, analysis_result.__dict__, ttl=86400)

            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing healthcare property {property_data.property_id}: {e}")
            raise

    async def _analyze_facility_suitability(
        self, property_data: HealthcareProperty, target_specialties: Optional[List[str]]
    ) -> Tuple[float, List[str]]:
        """Analyze physical facility suitability for medical practice."""

        score = 0.0
        recommendations = []

        # Base facility scoring
        if property_data.square_footage >= 2000:
            score += 20
        elif property_data.square_footage >= 1500:
            score += 15
        else:
            recommendations.append("Consider larger space for optimal patient flow")

        # Medical infrastructure scoring
        if property_data.ada_compliant:
            score += 15
        else:
            recommendations.append("ADA compliance modifications required")

        if property_data.medical_gas_systems:
            score += 10

        if property_data.backup_power:
            score += 10

        if property_data.laboratory_space:
            score += 10

        # Parking adequacy
        parking_ratio = property_data.parking_spaces / (property_data.square_footage / 1000)
        if parking_ratio >= 5.0:
            score += 15
        elif parking_ratio >= 3.0:
            score += 10
        else:
            recommendations.append("Additional parking may be needed for patient convenience")

        # Specialty-specific requirements
        if target_specialties:
            specialty_score = 0
            for specialty in target_specialties:
                if specialty in self.specialty_requirements:
                    req = self.specialty_requirements[specialty]
                    if property_data.square_footage >= req["min_sqft"]:
                        specialty_score += 5
                    if property_data.patient_rooms >= req["exam_rooms"]:
                        specialty_score += 5
            score += min(specialty_score, 20)

        return min(score, 100.0), recommendations

    async def _analyze_market_opportunity(self, property_data: HealthcareProperty) -> Tuple[float, Dict]:
        """Analyze healthcare market opportunity in the area."""

        # Use Claude AI for sophisticated market analysis
        market_prompt = f"""
        Analyze the healthcare market opportunity for this property location:
        
        Address: {property_data.address}
        Demographics: {json.dumps(property_data.demographics, indent=2)}
        Property Type: {property_data.property_type}
        Hospital Proximity: {property_data.proximity_to_hospital} miles
        
        Provide analysis on:
        1. Demographics suitability for healthcare services (age, income, insurance coverage)
        2. Competition density and market saturation
        3. Growth projections for healthcare services in this area
        4. Specialty opportunities based on demographics
        5. Market opportunity score (0-100)
        
        Format response as JSON with keys: score, insights, growth_factors, competition_level
        """

        try:
            market_analysis = await self.llm_client.generate_response(market_prompt, max_tokens=1000)

            # Parse Claude's response
            analysis_data = json.loads(market_analysis)
            return analysis_data.get("score", 75.0), analysis_data

        except Exception as e:
            logger.warning(f"Market analysis error: {e}")
            # Fallback scoring
            base_score = 70.0
            if property_data.demographics.get("median_age", 35) > 45:
                base_score += 10  # Older populations use more healthcare
            if property_data.demographics.get("median_income", 50000) > 75000:
                base_score += 10  # Higher income = better insurance

            return base_score, {"insights": ["Fallback analysis used"]}

    async def _analyze_patient_accessibility(self, property_data: HealthcareProperty) -> Tuple[float, List[str]]:
        """Analyze patient accessibility and convenience factors."""

        score = 0.0
        factors = []

        # Public transit accessibility
        if property_data.public_transit_score >= 8:
            score += 25
            factors.append("Excellent public transit access")
        elif property_data.public_transit_score >= 6:
            score += 20
            factors.append("Good public transit access")
        elif property_data.public_transit_score >= 4:
            score += 15
            factors.append("Moderate public transit access")
        else:
            factors.append("Limited public transit - patients may need private transport")

        # Hospital proximity (important for referrals and emergencies)
        if property_data.proximity_to_hospital <= 1.0:
            score += 25
            factors.append("Excellent hospital proximity for referrals")
        elif property_data.proximity_to_hospital <= 3.0:
            score += 20
            factors.append("Good hospital proximity")
        elif property_data.proximity_to_hospital <= 5.0:
            score += 15
            factors.append("Moderate hospital proximity")
        else:
            factors.append("Remote from hospitals - may affect referral patterns")

        # Parking convenience
        parking_per_1000sqft = property_data.parking_spaces / (property_data.square_footage / 1000)
        if parking_per_1000sqft >= 5:
            score += 25
            factors.append("Excellent parking availability")
        elif parking_per_1000sqft >= 3:
            score += 20
            factors.append("Adequate parking")
        else:
            score += 10
            factors.append("Limited parking may inconvenience patients")

        # ADA accessibility
        if property_data.ada_compliant:
            score += 25
            factors.append("Full ADA compliance ensures patient accessibility")
        else:
            factors.append("ADA compliance needed for patient accessibility")

        return min(score, 100.0), factors

    async def _analyze_regulatory_compliance(self, property_data: HealthcareProperty) -> Tuple[float, List[str]]:
        """Analyze regulatory compliance status and requirements."""

        score = 100.0  # Start with perfect score, deduct for issues
        issues = []

        # ADA Compliance (mandatory)
        if not property_data.ada_compliant:
            score -= 30
            issues.append("ADA compliance modifications required - mandatory for healthcare facilities")

        # Medical gas systems (important for many specialties)
        if not property_data.medical_gas_systems:
            score -= 15
            issues.append("Medical gas systems may be required for certain specialties")

        # Backup power (critical for emergency care)
        if not property_data.backup_power:
            score -= 10
            issues.append("Backup power recommended for patient safety and equipment protection")

        # Imaging radiation compliance (if applicable)
        if property_data.imaging_capability and property_data.square_footage < 3000:
            score -= 20
            issues.append("Imaging facilities require additional radiation safety compliance")

        # Surgery suite regulations (if applicable)
        if property_data.surgery_suites > 0:
            if not property_data.medical_gas_systems:
                score -= 25
                issues.append("Surgery suites require medical gas systems")
            if not property_data.backup_power:
                score -= 15
                issues.append("Surgery suites require backup power systems")

        return max(score, 0.0), issues

    async def _analyze_financial_viability(
        self, property_data: HealthcareProperty, target_specialties: Optional[List[str]]
    ) -> Tuple[float, int]:
        """Analyze financial viability and revenue potential."""

        # Base revenue calculation per square foot by property type
        revenue_per_sqft = {
            "medical_office": 400,
            "urgent_care": 600,
            "specialty_clinic": 500,
            "dental_practice": 450,
            "hospital": 800,
        }

        base_revenue = property_data.square_footage * revenue_per_sqft.get(property_data.property_type, 400)

        # Specialty multipliers
        specialty_multiplier = 1.0
        if target_specialties:
            specialty_multipliers = {
                "cardiology": 1.4,
                "orthopedics": 1.3,
                "dermatology": 1.2,
                "primary_care": 1.0,
                "urgent_care": 1.1,
            }
            for specialty in target_specialties:
                if specialty in specialty_multipliers:
                    specialty_multiplier = max(specialty_multiplier, specialty_multipliers[specialty])

        # Demographics adjustment
        demo_multiplier = 1.0
        if property_data.demographics:
            median_income = property_data.demographics.get("median_income", 50000)
            if median_income > 100000:
                demo_multiplier = 1.3
            elif median_income > 75000:
                demo_multiplier = 1.2
            elif median_income > 50000:
                demo_multiplier = 1.1

        # Location adjustment
        location_multiplier = 1.0
        if property_data.proximity_to_hospital <= 1.0:
            location_multiplier += 0.2
        if property_data.public_transit_score >= 7:
            location_multiplier += 0.1

        estimated_revenue = int(base_revenue * specialty_multiplier * demo_multiplier * location_multiplier)

        # Score based on revenue potential
        if estimated_revenue >= 2000000:  # $2M+
            score = 95.0
        elif estimated_revenue >= 1500000:  # $1.5M+
            score = 85.0
        elif estimated_revenue >= 1000000:  # $1M+
            score = 75.0
        elif estimated_revenue >= 750000:  # $750K+
            score = 65.0
        else:
            score = 50.0

        return score, estimated_revenue

    async def _generate_strategic_recommendations(
        self, property_data: HealthcareProperty, overall_score: float, target_specialties: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate AI-powered strategic recommendations using Claude."""

        strategy_prompt = f"""
        As a healthcare real estate consultant, provide strategic recommendations for this property:
        
        Property Analysis:
        - Overall Score: {overall_score:.1f}/100
        - Square Footage: {property_data.square_footage:,}
        - Property Type: {property_data.property_type}
        - Location: {property_data.address}
        - ADA Compliant: {property_data.ada_compliant}
        - Medical Infrastructure: Gas systems={property_data.medical_gas_systems}, Backup power={property_data.backup_power}
        - Patient Capacity: {property_data.patient_rooms} rooms, {property_data.waiting_area_sqft} sqft waiting
        - Target Specialties: {target_specialties or "Not specified"}
        
        Provide strategic guidance on:
        1. Top 3 medical specialties most suitable for this property
        2. Key recommendations to maximize success
        3. Potential risks and mitigation strategies
        4. Revenue optimization opportunities
        
        Format as JSON with keys: optimal_specialties, recommendations, risks, revenue_strategies
        """

        try:
            strategic_response = await self.llm_client.generate_response(strategy_prompt, max_tokens=1200)

            return json.loads(strategic_response)

        except Exception as e:
            logger.warning(f"Strategic analysis error: {e}")
            # Fallback recommendations
            return {
                "optimal_specialties": target_specialties or ["primary_care"],
                "recommendations": [
                    "Ensure ADA compliance for patient accessibility",
                    "Optimize patient flow design",
                    "Consider specialty-specific infrastructure needs",
                ],
                "risks": ["Market competition", "Regulatory changes"],
                "revenue_strategies": ["Focus on high-value specialties", "Optimize operational efficiency"],
            }

    async def get_specialty_recommendations(self, property_data: HealthcareProperty) -> List[Dict[str, Any]]:
        """Get ranked specialty recommendations for the property."""

        recommendations = []

        for specialty, requirements in self.specialty_requirements.items():
            suitability_score = 0

            # Size suitability
            if property_data.square_footage >= requirements["min_sqft"]:
                suitability_score += 30

            # Room count
            if property_data.patient_rooms >= requirements["exam_rooms"]:
                suitability_score += 25

            # Parking adequacy
            parking_ratio = property_data.parking_spaces / (property_data.square_footage / 1000)
            if parking_ratio >= requirements["parking_ratio"]:
                suitability_score += 20

            # Infrastructure requirements
            if requirements.get("imaging_required") and property_data.imaging_capability:
                suitability_score += 15
            if requirements.get("lab_required") and property_data.laboratory_space:
                suitability_score += 10

            recommendations.append(
                {
                    "specialty": specialty,
                    "suitability_score": suitability_score,
                    "requirements_met": suitability_score >= 60,
                    "missing_requirements": self._get_missing_requirements(property_data, requirements),
                }
            )

        # Sort by suitability score
        recommendations.sort(key=lambda x: x["suitability_score"], reverse=True)

        return recommendations

    def _get_missing_requirements(self, property_data: HealthcareProperty, requirements: Dict[str, Any]) -> List[str]:
        """Identify missing requirements for a specialty."""

        missing = []

        if property_data.square_footage < requirements["min_sqft"]:
            missing.append(f"Minimum {requirements['min_sqft']:,} sqft required")

        if property_data.patient_rooms < requirements["exam_rooms"]:
            missing.append(f"Minimum {requirements['exam_rooms']} exam rooms required")

        if requirements.get("imaging_required") and not property_data.imaging_capability:
            missing.append("Imaging capability required")

        if requirements.get("lab_required") and not property_data.laboratory_space:
            missing.append("Laboratory space required")

        return missing
