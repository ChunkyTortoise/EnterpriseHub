"""
Conversation State Management for Streamlit.
"""

import sys
from pathlib import Path
from typing import Dict, List

import streamlit as st

# Add project root to sys.path to import ghl_real_estate_ai.services
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))


def init_conversation_state():
    """Initialize session state for conversation."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = {}

    if "lead_score" not in st.session_state:
        st.session_state.lead_score = 0

    if "tags" not in st.session_state:
        st.session_state.tags = []


def add_message(role: str, content: str):
    """Add message to conversation history."""
    st.session_state.messages.append({"role": role, "content": content})


def update_extracted_data(data: Dict):
    """Update extracted preferences."""
    st.session_state.extracted_data.update(data)


def calculate_lead_score() -> int:
    """Calculate lead score from extracted data."""
    # Use the actual lead scorer
    from ghl_real_estate_ai.services.lead_scorer import LeadScorer

    scorer = LeadScorer()
    context = {
        "extracted_preferences": st.session_state.extracted_data,
        "conversation_history": st.session_state.messages,
    }

    score = scorer.calculate(context)
    st.session_state.lead_score = score

    # Update tags based on score
    update_tags(score, st.session_state.extracted_data)

    return score


def update_tags(score: int, preferences: Dict):
    """Update tags based on score and preferences."""
    tags = []

    # Lead temperature tag
    if score >= 70:
        tags.append("Hot-Lead")
    elif score >= 40:
        tags.append("Warm-Lead")
    else:
        tags.append("Cold-Lead")

    # Budget tags
    budget = preferences.get("budget")
    if budget:
        if budget < 300000:
            tags.append("Budget-Under-300k")
        elif budget <= 500000:
            tags.append("Budget-300k-500k")
        else:
            tags.append("Budget-500k-Plus")

    # Financing tags
    if preferences.get("financing"):
        tags.append("Pre-Approved")

    # Timeline tags
    if preferences.get("timeline") == "ASAP":
        tags.append("Timeline-Urgent")

    # Location tags
    location = preferences.get("location")
    if location:
        tags.append(f"Location-{location.replace(' ', '-')}")

    st.session_state.tags = tags
