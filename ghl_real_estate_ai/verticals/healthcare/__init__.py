"""
Healthcare Real Estate Vertical

Specialized platform for healthcare real estate professionals including:
- Medical practices and clinics
- Hospitals and health systems
- Senior living facilities
- Urgent care centers
- Dental and specialty practices

Key Features:
- HIPAA compliance framework
- Medical facility-specific property analysis
- Healthcare market intelligence
- Regulatory compliance automation
- Medical practice valuation models
"""

from .healthcare_analytics import HealthcareAnalytics
from .healthcare_compliance import HealthcareCompliance
from .medical_facility_matcher import MedicalFacilityMatcher
from .medical_property_analyzer import MedicalPropertyAnalyzer

__all__ = ["MedicalPropertyAnalyzer", "HealthcareCompliance", "MedicalFacilityMatcher", "HealthcareAnalytics"]

# Healthcare vertical configuration
HEALTHCARE_CONFIG = {
    "industry": "healthcare",
    "target_revenue": 39_000_000,  # $39M ARR
    "compliance_frameworks": ["HIPAA", "ADA", "OSHA", "Joint Commission"],
    "property_types": [
        "medical_office",
        "hospital",
        "senior_living",
        "urgent_care",
        "dental_practice",
        "specialty_clinic",
        "rehabilitation_center",
        "diagnostic_center",
    ],
    "key_metrics": [
        "beds_per_1000_population",
        "physician_density",
        "aging_population_index",
        "medicare_reimbursement_rates",
        "medical_facility_occupancy",
        "healthcare_market_growth",
    ],
}
