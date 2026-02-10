"""
Data package for Streamlit portfolio showcase
Contains services catalog and case studies data
"""

from ghl_real_estate_ai.streamlit_demo.data.services_data import (
    SERVICES,
    CATEGORIES,
    INDUSTRIES,
    DIFFERENTIATORS,
)
from ghl_real_estate_ai.streamlit_demo.data.case_studies_data import CASE_STUDIES

__all__ = [
    "SERVICES",
    "CATEGORIES",
    "INDUSTRIES",
    "DIFFERENTIATORS",
    "CASE_STUDIES",
]
